"""Casos de uso del esquema produccion: una función por caso de uso.

POR QUÉ UNA CAPA DE SERVICIOS
Las vistas solo reciben y responden. La operación de negocio vive aquí para poder llamarla desde la API,
desde una tarea programada (Celery) o desde una prueba, siempre de la misma manera.

PATRÓN PARA CONSTRUIR CADA FUNCIÓN (ejemplo completo en docs/desarrollo/02_construir_un_caso_de_uso.md)
1. with transaction.atomic():  todo o nada; si algo falla no queda nada a medias.
2. Llamar la función de PostgreSQL que aplica la regla (están listadas en «Reglas en la base»).
   No repita la regla en Python: la base ya la valida y está probada.
3. Si la base rechaza, lanza un error con el mensaje en español; guayacan/errores.py lo convierte en
   una respuesta 422 o 409 para el usuario. No hace falta capturarlo aquí.
4. publicar(...) un evento si otros módulos o los agentes deben enterarse (patrón outbox).
5. Devolver el objeto o los datos que mostrará la respuesta.

Cada función está vacía (NotImplementedError) y su documentación resume la especificación.
Especificación completa: documento técnico (pestaña de casos de uso) y docs/casos-de-uso/."""
# transaction y publicar aún no se usan (las funciones están vacías); «noqa» evita el aviso del revisor
from django.db import connection, transaction  # noqa: F401
from django.db.models import F
from rest_framework.exceptions import ValidationError

from apps.inventario.models import LoteInventario
from guayacan.eventos import publicar  # noqa: F401

from . import models


def pro_01_registrar_ingreso_lote_animales(*, usuario, **datos):
    """PRO-01 · Registrar el ingreso de un lote de animales

    Actores: Encargado de finca, Operario de campo
    Fase 1
    Tablas: produccion.lote_animal, produccion.animal, produccion.especie
    Reglas en la base: cumplimiento.v_granja_biosegura
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-07

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó LoteAnimalSerializer).
    Devuelve el lote creado. Los animales individuales (ovinos, caprinos) se registran después en /animales/.
    """
    # Al ingresar, los animales vivos son los que llegaron
    datos.setdefault('cantidad_actual', datos['cantidad_inicial'])
    with transaction.atomic():
        # La finca (predio_id) la pone la base según la sesión; especie, zona y propósito los validan sus llaves y CHECK
        lote = models.LoteAnimal.objects.create(**datos)
        # La vista no bloquea: avisa si la finca llegó a 200 aves de postura o levante sin certificado ICA
        with connection.cursor() as cur:
            cur.execute('select situacion from cumplimiento.v_granja_biosegura')
            situacion = cur.fetchone()[0]
        publicar('produccion.lote_ingresado', 'produccion.lote_animal', lote.id,
                 {'codigo': lote.codigo, 'especie_id': lote.especie_id, 'proposito': lote.proposito,
                  'cantidad': lote.cantidad_inicial, 'granja_biosegura': situacion})
    return lote


def pro_02_registrar_postura_diaria_clasificar_huevo(*, usuario, **datos):
    """PRO-02 · Registrar la postura diaria y clasificar el huevo

    Actores: Operario de campo; secundarios: Pasarela IoT local
    Fase 1
    Tablas: produccion.registro_postura, produccion.clasificacion_postura, produccion.categoria_huevo
    Reglas en la base: produccion.validar_clasificacion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-06, RF-18

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó RegistroPosturaSerializer).
      clasificacion  lista de {'categoria_huevo', 'cantidad', 'metodo'} contados a mano (o por visión)
      pesos_g        lista de pesos de la báscula; cada uno se convierte en categoría con produccion.clasificar_por_peso()
    Devuelve el registro de postura creado.
    """
    clasificacion = datos.pop('clasificacion', [])
    pesos_g = datos.pop('pesos_g', [])
    # Quien registra es el usuario del token, nunca lo que diga el cliente
    datos.pop('registrado_por', None)
    with transaction.atomic():
        # Lote y día repetidos: la llave única de la base responde 409 (flujo 4a)
        registro = models.RegistroPostura.objects.create(registrado_por=usuario, **datos)
        for c in clasificacion:
            # Al insertar, el disparador produccion.validar_clasificacion() rechaza si la suma supera los buenos (3b)
            # o si el método es visión y la función vision_artificial está apagada (3c)
            models.ClasificacionPostura.objects.create(registro_postura=registro, **c)
        if pesos_g:
            with connection.cursor() as cur:
                # Cuenta los pesos por categoría con los rangos vigentes el día del registro (3a)
                cur.execute('select c.id, count(*) from unnest(%s::numeric[]) p join produccion.categoria_huevo c '
                            'on c.codigo = produccion.clasificar_por_peso(p, %s) and c.vigente_desde = '
                            '(select max(vigente_desde) from produccion.categoria_huevo where vigente_desde <= %s) group by c.id',
                            [pesos_g, registro.fecha, registro.fecha])
                conteo = cur.fetchall()
            if sum(n for _, n in conteo) != len(pesos_g):
                raise ValidationError({'pesos_g': 'Hay pesos sin categoría vigente para esa fecha'})
            for categoria_id, n in conteo:
                models.ClasificacionPostura.objects.create(registro_postura=registro, categoria_huevo_id=categoria_id,
                                                           cantidad=n, metodo='peso_bascula')
        aves = models.LoteAnimal.objects.get(pk=registro.lote_animal_id).cantidad_actual
        # TODO(Volumen 4): revisar la carga del evento cuando el resumen de postura y el chatbot la consuman
        publicar('produccion.postura_registrada', 'produccion.registro_postura', registro.id,
                 {'lote_animal_id': registro.lote_animal_id, 'fecha': registro.fecha,
                  'huevos_recogidos': registro.huevos_recogidos, 'huevos_rotos': registro.huevos_rotos,
                  'postura_por_ave': round(registro.huevos_recogidos / aves, 3) if aves else None})
    return registro


def pro_03_registrar_alimentacion_pesajes_eventos_sanitarios(*, usuario, modelo, **datos):
    """PRO-03 · Registrar alimentación, pesajes y eventos sanitarios

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.registro_alimentacion, produccion.registro_pesaje, produccion.evento_sanitario
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-07, RF-18

    Parámetros: usuario (quien hace la petición), modelo (RegistroAlimentacion, RegistroPesaje o EventoSanitario,
    lo elige la vista según la ruta) y **datos (lo que validó su serializer).
    Devuelve el registro creado.
    """
    # shortcut: sin columnas para periodo de retiro (4a), umbral de mortalidad del lote (4b) ni dosis numérica
    # (salida del medicamento); agregarlas al modelo de datos cuando se definan y completar aquí
    if datos['lote_animal'].estado != 'activo':
        raise ValidationError({'lote_animal': 'El lote está cerrado'})
    with transaction.atomic():
        registro = modelo.objects.create(**datos)
        if modelo is models.RegistroAlimentacion:
            _consumir('produccion.registro_alimentacion', registro, registro.producto_id,
                      round(registro.cantidad_kg / _kilos_por_unidad(registro.producto_id), 2), usuario)
        if modelo is models.EventoSanitario and registro.tipo in ('mortalidad', 'descarte'):
            n = registro.cantidad_afectada
            # Descuenta en la base para que dos registros simultáneos no dejen el lote en negativo
            if not models.LoteAnimal.objects.filter(pk=registro.lote_animal_id, cantidad_actual__gte=n).update(
                    cantidad_actual=F('cantidad_actual') - n):
                raise ValidationError({'cantidad_afectada': 'Supera los animales vivos del lote'})
            if registro.animal_id:
                models.Animal.objects.filter(pk=registro.animal_id).update(
                    estado='muerto' if registro.tipo == 'mortalidad' else 'descartado')
            publicar('produccion.mortalidad_registrada', 'produccion.evento_sanitario', registro.id,
                     {'lote_animal_id': registro.lote_animal_id, 'tipo': registro.tipo, 'cantidad': n,
                      'cantidad_actual': models.LoteAnimal.objects.get(pk=registro.lote_animal_id).cantidad_actual})
    return registro


def _kilos_por_unidad(producto_id):
    """El kardex cuenta en la unidad del producto (p. ej. bulto de 40 kg); la alimentación se registra en kilos."""
    with connection.cursor() as cur:
        cur.execute("select u.factor_base from inventario.producto p join inventario.unidad_medida u on u.id = p.unidad_id "
                    "where p.id = %s and u.unidad_base = 'kg'", [producto_id])
        fila = cur.fetchone()
    if not fila:
        raise ValidationError({'producto': 'El alimento debe medirse en kilos o en una unidad de kilos'})
    return fila[0]


def _consumir(tabla, registro, producto_id, cantidad, usuario):
    """Salida de un insumo por consumo interno, primero lo que vence primero.
    Si no alcanza, el registro queda, la salida no se hace a medias y bodega recibe «Inventario insuficiente»."""
    try:
        with transaction.atomic(), connection.cursor() as cur:
            # Reparte la cantidad entre los lotes disponibles; el disparador del kardex descuenta cada uno
            cur.execute("insert into inventario.movimiento_inventario (lote_inventario_id, tipo, cantidad, costo_unitario, "
                        "documento_tipo, documento_id, usuario_id) "
                        "select id, 'consumo_interno', least(cantidad_disponible, %(c)s - previo), costo_unitario, "
                        "%(tipo)s, %(doc)s, %(u)s from (select l.*, coalesce(sum(l.cantidad_disponible) over "
                        "(order by l.fecha_vencimiento nulls last, l.fecha_produccion, l.id rows between unbounded preceding "
                        "and 1 preceding), 0) previo from inventario.lote_inventario l where l.producto_id = %(p)s "
                        "and l.estado = 'disponible' and l.cantidad_disponible > 0) x where previo < %(c)s returning cantidad",
                        {'c': cantidad, 'tipo': tabla.split('.')[1], 'doc': registro.id, 'u': usuario.id, 'p': producto_id})
            if sum(c for (c,) in cur.fetchall()) < cantidad:
                raise ValidationError('Inventario insuficiente')  # deshace solo las salidas de este bloque
    except ValidationError:
        publicar('inventario.salida_rechazada', tabla, registro.id,
                 {'producto_id': producto_id, 'cantidad': cantidad, 'motivo': 'Inventario insuficiente'})


def pro_04_registrar_eventos_reproductivos_ovinos_caprinos(*, usuario, **datos):
    """PRO-04 · Registrar eventos reproductivos de ovinos y caprinos

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.evento_reproductivo, produccion.animal
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-07

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó EventoReproductivoSerializer).
      crias         en un parto, lista de {'sexo', 'identificador' opcional}: una por cría viva
      lote_destino  en un destete, lote al que pasan las crías activas de la hembra
    Devuelve el evento creado.
    """
    crias = datos.pop('crias', [])
    lote_destino = datos.pop('lote_destino', None)
    hembra, macho, tipo = datos['hembra'], datos.get('macho'), datos['tipo']
    # 1a: la hembra (y el macho de la monta) deben estar vivos en la finca y tener el sexo correcto
    if hembra.sexo != 'hembra' or hembra.estado != 'activo':
        raise ValidationError({'hembra': 'Debe ser una hembra activa'})
    if macho and (macho.sexo != 'macho' or macho.estado != 'activo'):
        raise ValidationError({'macho': 'Debe ser un macho activo'})
    if tipo == 'monta' and not macho:
        raise ValidationError({'macho': 'La monta registra el macho'})
    if tipo == 'parto':
        datos['crias_vivas'] = len(crias)
    if tipo == 'destete' and not lote_destino:
        raise ValidationError({'lote_destino': 'El destete indica el lote al que pasan las crías'})
    with transaction.atomic():
        evento = models.EventoReproductivo.objects.create(**datos)
        if crias:
            if not macho:
                # El padre es el macho de la última monta de la hembra, si la hubo
                monta = models.EventoReproductivo.objects.filter(hembra=hembra, tipo='monta', fecha__lte=evento.fecha) \
                    .order_by('-fecha', '-id').first()
                macho = monta and monta.macho
            for i, c in enumerate(crias, 1):
                models.Animal.objects.create(lote_animal_id=hembra.lote_animal_id, madre=hembra, padre=macho,
                                             fecha_nacimiento=evento.fecha, sexo=c['sexo'],
                                             identificador=c.get('identificador') or f'C{evento.id}-{i}')
            models.LoteAnimal.objects.filter(pk=hembra.lote_animal_id).update(cantidad_actual=F('cantidad_actual') + len(crias))
        if lote_destino:
            # 3a: las crías activas que siguen en el lote de la madre pasan al de destino; cada lote ajusta su cantidad
            n = models.Animal.objects.filter(madre=hembra, estado='activo', lote_animal_id=hembra.lote_animal_id) \
                .update(lote_animal=lote_destino)
            models.LoteAnimal.objects.filter(pk=hembra.lote_animal_id).update(cantidad_actual=F('cantidad_actual') - n)
            models.LoteAnimal.objects.filter(pk=lote_destino.pk).update(cantidad_actual=F('cantidad_actual') + n)
    return evento


def pro_05_registrar_siembra_labores_culturales(*, usuario, modelo, **datos):
    """PRO-05 · Registrar una siembra y sus labores culturales

    Actores: Operario de campo, Encargado de finca
    Fase 1
    Tablas: produccion.siembra, produccion.labor_cultural, produccion.cultivo
    Reglas en la base: ck labor por robot exige misión
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-04, RF-05, RF-07

    Parámetros: usuario (quien hace la petición), modelo (Siembra o LaborCultural, lo elige la vista según la ruta)
    y **datos (lo que validó su serializer). En una labor de tipo «conteo», cantidad son las plantas vivas contadas;
    en las demás, el insumo aplicado en la unidad del producto.
    Devuelve el registro creado.
    """
    # shortcut: sin columna de periodo de carencia del insumo (3b); agregarla al modelo de datos y validar en PRO-06
    if modelo is models.Siembra:
        # Al sembrar, las plantas vivas son las sembradas (o las previstas si aún no se contaron)
        datos.setdefault('plantas_vivas', datos.get('plantas_sembradas') or datos.get('plantas_previstas'))
        return models.Siembra.objects.create(**datos)
    siembra = datos['siembra']
    if siembra.estado in ('planeada', 'perdida', 'finalizada'):
        raise ValidationError({'siembra': f'La siembra está {siembra.estado}'})
    with transaction.atomic():
        # Método robot o dron sin misión: lo rechaza el CHECK de la base (3a)
        labor = models.LaborCultural.objects.create(**datos)
        if labor.tipo == 'conteo':
            if labor.cantidad is None:
                raise ValidationError({'cantidad': 'El conteo registra las plantas vivas'})
            siembra.plantas_vivas = int(labor.cantidad)
            base = siembra.plantas_sembradas or siembra.plantas_previstas
            # shortcut: «muchas plantas muertas» es menos de la mitad viva; pasar a un parámetro por cultivo cuando exista
            if siembra.estado == 'sembrada' and base and siembra.plantas_vivas < base / 2:
                siembra.estado = 'recuperacion'  # 2a (ST16: sembrada -> recuperacion) y se programa la resiembra
                publicar('produccion.siembra_en_recuperacion', 'produccion.siembra', siembra.id,
                         {'zona_id': siembra.zona_id, 'plantas_vivas': siembra.plantas_vivas, 'plantas_base': base})
            siembra.save(update_fields=['plantas_vivas', 'estado'])
        elif labor.producto_id and labor.cantidad:
            _consumir('produccion.labor_cultural', labor, labor.producto_id, labor.cantidad, usuario)
    return labor


def pro_06_registrar_cosecha_destino(*, usuario, **datos):
    """PRO-06 · Registrar una cosecha y su destino

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.cosecha, inventario.lote_inventario
    Reglas en la base: inventario.entrada_inicial(), comercial.registrar_huella()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-06, RF-18

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó CosechaSerializer).
      bodega          destino venta: bodega donde entra el lote de inventario
      costo_unitario  destino venta: costo por unidad del lote (0 si aún no se conoce)
      lote_animal     destino alimento animal: lote que se lo come
    Devuelve la cosecha creada.
    """
    # shortcut: sin columna de periodo de carencia del insumo (1b); agregarla al modelo de datos y validar aquí
    bodega = datos.pop('bodega', None)
    costo_unitario = datos.pop('costo_unitario', 0)
    lote_animal = datos.pop('lote_animal', None)
    siembra, destino = datos['siembra'], datos['destino']
    if siembra.estado in ('planeada', 'perdida', 'finalizada'):
        raise ValidationError({'siembra': f'La siembra está {siembra.estado}'})
    if destino == 'venta' and not bodega:
        raise ValidationError({'bodega': 'Lo que va a venta entra a una bodega'})
    if destino == 'alimento_animal' and not lote_animal:
        raise ValidationError({'lote_animal': 'Indique el lote que recibe el alimento'})
    with transaction.atomic():
        cosecha = models.Cosecha.objects.create(**datos)
        if destino == 'venta':
            # La base registra la entrada en kardex, estima el vencimiento y agrega la huella de trazabilidad
            cosecha.lote_inventario = LoteInventario.objects.create(
                producto_id=cosecha.producto_id, bodega=bodega, origen='produccion', origen_tabla='produccion.cosecha',
                origen_id=cosecha.id, fecha_produccion=cosecha.fecha, cantidad_inicial=cosecha.cantidad,
                costo_unitario=costo_unitario, codigo_lote=f'{cosecha.producto.sku[:12]}-{cosecha.fecha:%Y%m%d}-{cosecha.id}')
            cosecha.save(update_fields=['lote_inventario'])
        elif destino == 'alimento_animal':
            # 1a: no pasa por bodega; queda como alimento propio del lote
            models.RegistroAlimentacion.objects.create(
                lote_animal=lote_animal, fecha=cosecha.fecha, producto_id=cosecha.producto_id, origen='propio',
                cantidad_kg=cosecha.cantidad * _kilos_por_unidad(cosecha.producto_id))
        if siembra.estado in ('sembrada', 'recuperacion'):
            # ST16: la primera cosecha pone la siembra en producción
            models.Siembra.objects.filter(pk=siembra.pk).update(estado='en_produccion')
        publicar('produccion.cosecha_registrada', 'produccion.cosecha', cosecha.id,
                 {'siembra_id': siembra.id, 'producto_id': cosecha.producto_id, 'cantidad': cosecha.cantidad,
                  'destino': destino, 'lote_inventario_id': cosecha.lote_inventario_id})
    return cosecha


def pro_07_registrar_analisis_suelo_recomendacion(*, usuario, **datos):
    """PRO-07 · Registrar un análisis de suelo y su recomendación

    Actores: Encargado de finca; secundarios: Agrónomo (IA)
    Fase 1
    Tablas: produccion.analisis_suelo
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-07:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-07: por construir')


def pro_08_registrar_bioseguridad_e_inocuidad(*, usuario, **datos):
    """PRO-08 · Registrar bioseguridad e inocuidad

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.registro_bioseguridad
    Reglas en la base: cumplimiento.evaluar_expediente()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-08:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: cumplimiento.evaluar_expediente()
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-08: por construir')


def pro_09_producir_abono_lombricultivo_compostera(*, usuario, **datos):
    """PRO-09 · Producir abono en lombricultivo o compostera

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.produccion_abono, inventario.lote_inventario
    Reglas en la base: inventario.entrada_inicial()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-08, RNF-14

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.entrada_inicial()
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-09: por construir')


def pro_10_medir_calidad_agua_estanques(*, usuario, **datos):
    """PRO-10 · Medir la calidad del agua de los estanques

    Actores: Operario de campo; secundarios: Pasarela IoT local
    Fase 1
    Tablas: produccion.calidad_agua_estanque
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-18

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-10:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-10: por construir')
