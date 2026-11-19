"""Casos de uso del esquema adopcion: una función por caso de uso.

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
from django.db import Error, connection, transaction  # noqa: F401
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.comercial.models import Factura, Pago
from apps.terceros.models import Cliente, ConsentimientoDatos, Tercero
from guayacan.errores import datos_del_error
from guayacan.eventos import publicar  # noqa: F401
from guayacan.pasarela import pasarela

from . import models


def ado_01_configurar_catalogo_sitios(*, usuario, planes=(), sitios=(), bienes=(), **datos):
    """ADO-01 · Configurar catálogo y sitios

    Actores: Administrador; secundarios: Encargado de finca
    Fase 3 · función adopcion
    Tablas: adopcion.plan, adopcion.sitio, adopcion.bien
    Reglas en la base: nucleo.exigir_funcion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-45

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
      planes, sitios, bienes  listas con los datos validados por PlanSerializer, SitioSerializer y BienSerializer
    Devuelve {'planes': [...], 'sitios': [...], 'bienes': [...]} con los objetos creados.
    """
    # Todo o nada: si un registro falla (código repetido, precio en cero...), no queda ninguno a medias
    with transaction.atomic():
        with connection.cursor() as cur:
            # Los disparadores de plan, sitio y bien no exigen la función (pruebas_adopcion.sql los crea apagada): se exige aquí.
            # Si está apagada, la base lanza P0001 y guayacan/errores.py responde 422 con su mensaje
            cur.execute("select nucleo.exigir_funcion('adopcion')")
        # La finca (predio_id) la pone la base según la sesión; el resto de reglas lo validan los CHECK y llaves de la base.
        # shortcut: un bien solo puede apuntar a planes y sitios ya guardados (los del mismo lote aún no tienen id ante el serializer); enviar bienes en una segunda llamada
        return {
            'planes': [models.Plan.objects.create(**p) for p in planes],
            'sitios': [models.Sitio.objects.create(**s) for s in sitios],
            'bienes': [models.Bien.objects.create(**b) for b in bienes],
        }


def ado_02_comprar_arbol_animal(*, usuario, **datos):
    """ADO-02 · Comprar un árbol o un animal

    Actores: Adoptante; secundarios: Pasarela de pagos, Vendedor personalizado (IA)
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.bien, terceros.tercero, terceros.consentimiento_datos, comercial.pago
    Reglas en la base: adopcion.validar_contrato(), comercial.preparar_factura()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-45

    Parámetros: usuario (vendedor, administrador o agente con sesión en la finca; el adoptante no necesita cuenta)
    y **datos (lo que validó CompraSerializer).
    Devuelve (contrato, cobro): el contrato nace pendiente_pago y el bien sigue disponible hasta que la pasarela
    confirme (ado_02_confirmar_pago). cobro trae el enlace de pago para enviarle al adoptante.
    """
    if not datos['autoriza_datos']:
        raise ValidationError({'autoriza_datos': 'Sin la autorización de datos (Ley 1581) no se puede registrar al adoptante'})
    bien, plan = datos['bien'], datos['bien'].plan
    with transaction.atomic():
        persona = datos['adoptante']
        # Un adoptante que ya compró o es cliente se reconoce por su documento; sus datos no se sobrescriben
        tercero = Tercero.objects.filter(tipo_documento=persona['tipo_documento'],
                                         numero_documento=persona['numero_documento']).first() \
            or Tercero.objects.create(es_cliente=True, **persona)
        Tercero.objects.filter(pk=tercero.pk, es_cliente=False).update(es_cliente=True)
        Cliente.objects.get_or_create(tercero=tercero, defaults={'segmento': 'turista'})
        consentimiento = None
        for finalidad, otorgado in (('atencion_pedidos', True), ('seguimiento_adopcion', datos['autoriza_seguimiento'])):
            if otorgado:
                consentimiento = ConsentimientoDatos.objects.create(
                    tercero=tercero, finalidad=finalidad, version_politica=datos['version_politica'], otorgado=True,
                    medio=datos['medio_autorizacion'], evidencia_url=datos.get('evidencia_url'), otorgado_en=timezone.now())
        with connection.cursor() as cur:
            # shortcut: consecutivo por max+1; dos compras simultáneas chocan en el único (409) y se reintenta
            cur.execute("select coalesce(max(substring(numero from '^ADO-([0-9]+)$')::integer), 0) + 1 from adopcion.contrato")
            numero = f'ADO-{cur.fetchone()[0]}'
        # La base exige la función «adopcion», el bien disponible, la modalidad de siembra y, si siembra un trabajador,
        # la autorización seguimiento_adopcion (adopcion.validar_contrato)
        contrato = models.Contrato.objects.create(
            numero=numero, bien=bien, adoptante=tercero, tipo='compra', precio=plan.precio_compra,
            cuota_mensual=plan.cuota_mensual, modalidad_siembra=datos['modalidad_siembra'],
            consentimiento=consentimiento, estado='pendiente_pago')
        cobro = pasarela().crear_cobro(referencia=f'{contrato.predio_id}:{numero}', valor=contrato.precio,
                                       descripcion=f'Adopción {bien.codigo} ({plan.nombre})')
    return contrato, cobro


def ado_02_confirmar_pago(*, referencia, estado, id_transaccion, valor):
    """ADO-02 · Aviso de la pasarela (webhook), con la firma ya verificada y la finca de la referencia fijada.

    aprobado:  el contrato pasa a activo (la base toma el bien) y se crean la factura y el pago confirmado.
    rechazado: el contrato sigue pendiente_pago, sin factura; se puede reintentar o vence (adopcion.cancelar_pendientes_pago).
    Un aviso repetido no hace nada. Devuelve el contrato.
    """
    numero = referencia.split(':', 1)[1]
    contrato = models.Contrato.objects.select_for_update().filter(numero=numero).first()
    if not contrato:
        raise NotFound(f'No hay contrato {numero}')
    if contrato.estado != 'pendiente_pago':
        return contrato  # la pasarela reenvía avisos: el segundo no cambia nada
    if estado == 'rechazado':
        publicar('adopcion.pago_rechazado', 'adopcion.contrato', contrato.id, {'numero': numero, 'id_transaccion': id_transaccion})
        return contrato
    if valor != contrato.precio:
        raise ValidationError({'valor': f'La pasarela cobró {valor} y el contrato vale {contrato.precio}'})
    try:
        with transaction.atomic():
            contrato.estado = 'activo'
            contrato.save(update_fields=['estado'])  # la base revisa otra vez que el bien siga disponible
    except Error as e:
        if 'no está disponible' not in datos_del_error(e)[1]:
            raise
        # Otro adoptante pagó primero el mismo bien: el contrato se cancela y el dinero se devuelve
        contrato.estado = 'cancelado'
        contrato.save(update_fields=['estado'])
        publicar('adopcion.pago_sin_bien', 'adopcion.contrato', contrato.id,
                 {'numero': numero, 'id_transaccion': id_transaccion, 'valor': valor, 'accion': 'devolver el pago'})
        return contrato
    cliente = Cliente.objects.get(tercero_id=contrato.adoptante_id)
    with connection.cursor() as cur:
        cur.execute("select coalesce(max(numero), 0) + 1 from comercial.factura where prefijo = 'ADO'")
        consecutivo = cur.fetchone()[0]
    # TODO(DIAN): numerar con la resolución de facturación de la finca y enviar la factura electrónica;
    # el IVA de la adopción lo define el contador (hoy 0)
    factura = Factura.objects.create(prefijo='ADO', numero=consecutivo, cliente=cliente, fecha_emision=timezone.now(),
                                     subtotal=contrato.precio, iva=0, total=contrato.precio, forma_pago='contado')
    # comercial.aplicar_pago() descuenta el pago del saldo de la factura
    Pago.objects.create(factura=factura, fecha=timezone.now(), valor=valor, medio='pasarela',
                        proveedor_pasarela=pasarela().proveedor, id_transaccion_pasarela=id_transaccion,
                        referencia=referencia, estado='confirmado')
    publicar('adopcion.compra_confirmada', 'adopcion.contrato', contrato.id,
             {'numero': numero, 'bien_id': contrato.bien_id, 'factura': f'ADO-{consecutivo}',
              'modalidad_siembra': contrato.modalidad_siembra})
    return contrato


def ado_03_sembrar_persona(*, usuario, bien_id, **datos):
    """ADO-03 · Sembrar en persona

    Actores: Adoptante; secundarios: Encargado de finca, Portería
    Fase 3 · función adopcion
    Tablas: adopcion.seguimiento, agenda.visita
    Reglas en la base: adopcion.registrar_siembra()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/siembra/
    Requerimientos: RQ-45

    Parámetros: usuario (encargado u operario), bien_id y **datos (lo que validó SiembraPersonaSerializer):
      fecha   día de la siembra
      visita  visita del adoptante (AGD-03) que pasó por portería (AGD-04): prueba de que sembró en persona
    Devuelve el bien sembrado (activo).
    """
    fecha, visita = datos['fecha'], datos['visita']
    with transaction.atomic():
        with connection.cursor() as cur:
            # adopcion.registrar_siembra() no exige la función: se exige aquí (422 si está apagada)
            cur.execute("select nucleo.exigir_funcion('adopcion')")
        contrato = models.Contrato.objects.filter(bien_id=bien_id, estado='activo').first()
        if contrato:  # sin contrato activo la base responde «El árbol no tiene contrato activo»
            if visita.tercero_id != contrato.adoptante_id:
                raise ValidationError({'visita': 'La visita no es del adoptante del árbol'})
            # en_sitio o salio solo los pone portería (agenda.validar_acceso) sobre una visita aprobada
            if visita.estado not in ('en_sitio', 'salio'):
                raise ValidationError({'visita': f'El adoptante no ha entrado a la finca (visita {visita.estado})'})
            if timezone.localdate(visita.ingreso_programado) != fecha:
                raise ValidationError({'fecha': 'La siembra en persona es el día de la visita'})
        with connection.cursor() as cur:
            # Árbol reservado (pagado) a activo, sitio ocupado, seguimiento y evento adopcion.sembrado
            cur.execute('select adopcion.registrar_siembra(%s, %s)', [bien_id, fecha])
    return models.Bien.objects.get(pk=bien_id)


def ado_04_sembrar_trabajador_enviar_video(*, usuario, **datos):
    """ADO-04 · Sembrar por un trabajador y enviar el video

    Actores: Operario de campo; secundarios: Encargado de finca, Gestor de redes (IA)
    Fase 3 · función adopcion
    Tablas: personal.tarea, personal.evidencia_tarea, adopcion.seguimiento
    Reglas en la base: adopcion.registrar_siembra(), redes.verificar_envio()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/siembra/
    Requerimientos: RQ-45

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-04:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.registrar_siembra(), redes.verificar_envio()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-04: por construir')


def ado_05_cobrar_pagar_cuota_mensual(*, usuario, **datos):
    """ADO-05 · Cobrar y pagar la cuota mensual

    Actores: Tareas programadas; secundarios: Adoptante, Pasarela de pagos
    Fase 3 · función adopcion
    Tablas: adopcion.cuota, adopcion.movimiento_saldo, comercial.pago
    Reglas en la base: adopcion.generar_cuotas(), adopcion.compensar_cuotas()
    Endpoints: POST /api/v1/adopcion/cuotas/{id}/pagar/
    Requerimientos: RQ-46

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-05:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.generar_cuotas(), adopcion.compensar_cuotas()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-05: por construir')


def ado_06_seguir_mi_arbol_mi_animal(*, usuario, **datos):
    """ADO-06 · Seguir mi árbol o mi animal

    Actores: Adoptante; secundarios: Operario de campo
    Fase 3 · función adopcion
    Tablas: adopcion.seguimiento, adopcion.cuota, adopcion.movimiento_saldo
    Reglas en la base: adopcion.saldo()
    Endpoints: GET /api/v1/adopcion/mis-bienes/; GET /api/v1/adopcion/mis-bienes/{id}/seguimiento/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-06:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.saldo()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-06: por construir')


def ado_07_detectar_abandono_poner_readopcion(*, usuario, **datos):
    """ADO-07 · Detectar abandono y poner en readopción

    Actores: Tareas programadas; secundarios: Adoptante, Gestor de redes (IA)
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.cuota, adopcion.bien, adopcion.seguimiento
    Reglas en la base: adopcion.marcar_abandono()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-46

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-07:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.marcar_abandono()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-07: por construir')


def ado_08_readoptar(*, usuario, **datos):
    """ADO-08 · Readoptar

    Actores: Adoptante; secundarios: Pasarela de pagos
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.bien
    Reglas en la base: adopcion.validar_contrato()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-46

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-08:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_contrato()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-08: por construir')


def ado_09_registrar_vender_productos_bien(*, usuario, **datos):
    """ADO-09 · Registrar y vender productos del bien

    Actores: Operario de campo; secundarios: Vendedor
    Fase 3 · función adopcion
    Tablas: adopcion.seguimiento, comercial.pedido
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-09:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-09: por construir')


def ado_10_liquidar_productos_5(*, usuario, **datos):
    """ADO-10 · Liquidar productos con el 5 %

    Actores: Administrador; secundarios: Contador
    Fase 3 · función adopcion
    Tablas: adopcion.liquidacion, adopcion.movimiento_saldo
    Reglas en la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    Endpoints: POST /api/v1/adopcion/liquidaciones/{id}/aprobar/; POST /api/v1/adopcion/adoptantes/{id}/pagar-saldo/
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-10:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-10: por construir')


def ado_11_decidir_madurez_mantener_liquidar(*, usuario, **datos):
    """ADO-11 · Decidir en la madurez: mantener o liquidar

    Actores: Adoptante; secundarios: Administrador
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato
    Reglas en la base: adopcion.marcar_madurez(), adopcion.validar_contrato()
    Endpoints: POST /api/v1/adopcion/contratos/{id}/decision/
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-11:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.marcar_madurez(), adopcion.validar_contrato()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-11: por construir')


def ado_12_talar_sacrificar_liquidar(*, usuario, **datos):
    """ADO-12 · Talar o sacrificar y liquidar

    Actores: Administrador; secundarios: Autoridad o planta de beneficio (CAR, ICA, INVIMA)
    Fase 3 · función adopcion
    Tablas: adopcion.liquidacion, documental.documento
    Reglas en la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-12:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-12: por construir')


def ado_13_reponer_bien_muerto_garantia(*, usuario, **datos):
    """ADO-13 · Reponer un bien muerto en garantía

    Actores: Encargado de finca; secundarios: Adoptante
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato, adopcion.seguimiento
    Reglas en la base: adopcion.registrar_muerte()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/muerte/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-13:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.registrar_muerte()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-13: por construir')


def ado_14_ceder_regalar_adopcion(*, usuario, **datos):
    """ADO-14 · Ceder o regalar la adopción

    Actores: Adoptante
    Fase 3 · función adopcion
    Tablas: adopcion.contrato
    Reglas en la base: adopcion.validar_contrato()
    Endpoints: POST /api/v1/adopcion/contratos/{id}/ceder/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-14:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_contrato()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-14: por construir')


def ado_15_consultar_tablero_adopcion(*, usuario, **datos):
    """ADO-15 · Consultar el tablero de adopción

    Actores: Familia; secundarios: Administrador
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato, adopcion.cuota
    Reglas en la base: adopcion.v_tablero
    Endpoints: GET /api/v1/adopcion/tablero/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-15:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.v_tablero
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-15: por construir')
