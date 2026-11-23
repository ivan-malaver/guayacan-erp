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
import hashlib
import secrets
from datetime import timedelta

from django.db import Error, connection, transaction  # noqa: F401
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from apps.comercial.models import Factura, Pago
from apps.personal.models import EvidenciaTarea
from apps.terceros.models import Cliente, ConsentimientoDatos, Tercero
from guayacan.db import consultar
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
    plan = datos['bien'].plan
    return _contratar(tipo='compra', precio=plan.precio_compra, modalidad=datos.pop('modalidad_siembra'), **datos)


def _contratar(*, tipo, precio, modalidad, bien, cuota_mensual=None, cobrar=True, **datos):
    """Compra (ADO-02), readopción (ADO-08) o cesión (ADO-14): registra al adoptante con su autorización de datos y
    crea el contrato. Con cobrar, nace pendiente_pago y se pide el cobro; sin cobrar (cesión) nace activo.
    Devuelve (contrato, cobro); cobro es None si no se cobra."""
    if not datos['autoriza_datos']:
        raise ValidationError({'autoriza_datos': 'Sin la autorización de datos (Ley 1581) no se puede registrar al adoptante'})
    plan = bien.plan
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
        # La base exige la función «adopcion», el bien disponible (en readopción o vivo para ceder), la modalidad de siembra
        # y, si siembra un trabajador, la autorización seguimiento_adopcion (adopcion.validar_contrato)
        contrato = models.Contrato.objects.create(
            numero=numero, bien=bien, adoptante=tercero, tipo=tipo, precio=precio,
            cuota_mensual=cuota_mensual or plan.cuota_mensual, modalidad_siembra=modalidad,
            consentimiento=consentimiento, estado='pendiente_pago' if cobrar else 'activo')
        cobro = pasarela().crear_cobro(referencia=f'{contrato.predio_id}:{numero}', valor=contrato.precio,
                                       descripcion=f'Adopción {bien.codigo} ({plan.nombre})') if cobrar else None
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
        if not any(m in datos_del_error(e)[1] for m in ('no está disponible', 'no está en readopción')):
            raise
        # Otro adoptante pagó primero el mismo bien: el contrato se cancela y el dinero se devuelve
        contrato.estado = 'cancelado'
        contrato.save(update_fields=['estado'])
        publicar('adopcion.pago_sin_bien', 'adopcion.contrato', contrato.id,
                 {'numero': numero, 'id_transaccion': id_transaccion, 'valor': valor, 'accion': 'devolver el pago'})
        return contrato
    pago = _facturar_y_cobrar(contrato.adoptante_id, valor, referencia, id_transaccion)
    publicar('adopcion.compra_confirmada', 'adopcion.contrato', contrato.id,
             {'numero': numero, 'tipo': contrato.tipo, 'bien_id': contrato.bien_id, 'factura': f'ADO-{pago.factura.numero}',
              'modalidad_siembra': contrato.modalidad_siembra})
    return contrato


def confirmar_pago(**aviso):
    """Aviso de la pasarela (webhook) ya verificado: la referencia dice si es una compra (ADO-) o una cuota (CUO-).
    Devuelve (documento, estado) para la respuesta."""
    documento = aviso['referencia'].split(':', 1)[1]
    if documento.startswith('CUO-'):
        return documento, ado_05_confirmar_pago_cuota(**aviso).estado
    return documento, ado_02_confirmar_pago(**aviso).estado


def _facturar_y_cobrar(adoptante_id, valor, referencia, id_transaccion):
    """Factura de contado ADO-<consecutivo> y pago confirmado de la pasarela, para una compra o una cuota. Devuelve el pago."""
    cliente = Cliente.objects.get(tercero_id=adoptante_id)
    with connection.cursor() as cur:
        cur.execute("select coalesce(max(numero), 0) + 1 from comercial.factura where prefijo = 'ADO'")
        consecutivo = cur.fetchone()[0]
    # TODO(DIAN): numerar con la resolución de facturación de la finca y enviar la factura electrónica;
    # el IVA de la adopción lo define el contador (hoy 0)
    factura = Factura.objects.create(prefijo='ADO', numero=consecutivo, cliente=cliente, fecha_emision=timezone.now(),
                                     subtotal=valor, iva=0, total=valor, forma_pago='contado')
    # comercial.aplicar_pago() descuenta el pago del saldo de la factura
    return Pago.objects.create(factura=factura, fecha=timezone.now(), valor=valor, medio='pasarela',
                               proveedor_pasarela=pasarela().proveedor, id_transaccion_pasarela=id_transaccion,
                               referencia=referencia, estado='confirmado')


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


def ado_04_sembrar_trabajador_enviar_video(*, usuario, bien_id, **datos):
    """ADO-04 · Sembrar por un trabajador y enviar el video

    Actores: Operario de campo; secundarios: Encargado de finca, Gestor de redes (IA)
    Fase 3 · función adopcion
    Tablas: personal.tarea, personal.evidencia_tarea, adopcion.seguimiento
    Reglas en la base: adopcion.registrar_siembra(), redes.verificar_envio()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/siembra/
    Requerimientos: RQ-45

    Parámetros: usuario (el trabajador que sembró, o el encargado), bien_id y **datos (lo que validó
    SiembraTrabajadorSerializer):
      fecha      día de la siembra (el de la tarea)
      tarea      tarea de siembra (PER-04/05) en la zona del árbol, en curso o terminada
      video_url  video de la siembra (ya subido); obligatorio
    Devuelve el bien sembrado (activo).

    La base hace cumplir el resto: contrato activo, árbol reservado (pagado) y video (adopcion.registrar_siembra);
    la autorización seguimiento_adopcion ya se exigió al crear el contrato (ADO-02); la evidencia solo la deja quien
    ejecuta la tarea (personal.validar_evidencia_tarea, 403). Después el encargado aprueba la tarea (PER-06).
    """
    # TODO(datos personales): si el trabajador sale en el video, la base exige imagen_redes solo para piezas publicadas
    # en redes, no para el video privado al adoptante; revisarlo con la política de datos
    fecha, tarea, video = datos['fecha'], datos['tarea'], datos['video_url']
    with transaction.atomic():
        with connection.cursor() as cur:
            # adopcion.registrar_siembra() no exige la función: se exige aquí (422 si está apagada)
            cur.execute("select nucleo.exigir_funcion('adopcion')")
            cur.execute('select s.zona_id from adopcion.bien b join adopcion.sitio s on s.id = b.sitio_id where b.id = %s', [bien_id])
            zona = cur.fetchone()
        if zona and tarea.zona_id != zona[0]:
            raise ValidationError({'tarea': 'La tarea no es de la zona donde está el árbol'})
        if tarea.fecha != fecha:
            raise ValidationError({'fecha': 'La siembra es el día de la tarea'})
        with connection.cursor() as cur:
            # Árbol reservado a activo, sitio ocupado, seguimiento video_siembra y evento adopcion.sembrado con el video
            # TODO(Volumen 4): el Gestor de redes toma adopcion.sembrado, llama a redes.verificar_envio() (ventana,
            # plantilla y tope del canal) y envía el video al adoptante; luego lo confirma con
            # POST /api/v1/adopcion/seguimientos/{id}/marcar-enviado/ (ado_07_marcar_enviado)
            cur.execute('select adopcion.registrar_siembra(%s, %s, %s, %s)', [bien_id, fecha, tarea.id, video])
            cur.execute("select id from adopcion.seguimiento where bien_id = %s and tipo = 'video_siembra' order by id desc limit 1",
                        [bien_id])
            seguimiento_id = cur.fetchone()[0]
        # El video queda también como evidencia de la tarea, para que el encargado lo vea al aprobarla (PER-06)
        EvidenciaTarea.objects.create(tarea=tarea, tipo='video', archivo_url=video, registro_tabla='adopcion.seguimiento',
                                      registro_id=seguimiento_id)
    return models.Bien.objects.get(pk=bien_id)


def ado_05_cobrar_pagar_cuota_mensual(*, usuario, cuota_id):
    """ADO-05 · Cobrar y pagar la cuota mensual

    Actores: Tareas programadas; secundarios: Adoptante, Pasarela de pagos
    Fase 3 · función adopcion
    Tablas: adopcion.cuota, adopcion.movimiento_saldo, comercial.pago
    Reglas en la base: adopcion.generar_cuotas(), adopcion.compensar_cuotas()
    Endpoints: POST /api/v1/adopcion/cuotas/{id}/pagar/
    Requerimientos: RQ-46

    Parámetros: usuario (vendedor, administrador o agente; el adoptante no necesita cuenta) y cuota_id.
    Devuelve el cobro de la pasarela (enlace de pago) para enviárselo al adoptante. La cuota sigue pendiente hasta que
    la pasarela confirme (ado_05_confirmar_pago_cuota).

    El cobro mensual ya lo hace la base: adopcion.generar_cuotas() crea las cuotas el día 1 (Celery, config/celery.py)
    y adopcion.compensar_cuotas() las paga con el saldo a favor del adoptante.
    """
    with connection.cursor() as cur:
        cur.execute("select nucleo.exigir_funcion('adopcion')")
    cuota = models.Cuota.objects.select_related('contrato').filter(pk=cuota_id).first()
    if not cuota:
        raise NotFound(f'No hay cuota {cuota_id}')
    if cuota.estado != 'pendiente':
        raise ValidationError({'estado': f'La cuota ya está {cuota.estado}'})
    return pasarela().crear_cobro(referencia=f'{cuota.predio_id}:CUO-{cuota.id}', valor=cuota.valor,
                                  descripcion=f'Cuota {cuota.periodo:%Y-%m} de la adopción {cuota.contrato.numero}')


def ado_05_confirmar_pago_cuota(*, referencia, estado, id_transaccion, valor):
    """ADO-05 · Aviso de la pasarela para una cuota, con la firma ya verificada y la finca fijada.

    aprobado:  factura y pago confirmado; la cuota queda pagada.
    rechazado: la cuota sigue pendiente, sin factura.
    Si la cuota ya no está pendiente (la compensó el saldo, se anuló por abandono) o el contrato terminó, no se cobra
    dos veces: se publica adopcion.pago_sin_cuota para devolver el dinero. Un aviso repetido no hace nada.
    Devuelve la cuota.
    """
    cuota_id = int(referencia.split(':', 1)[1].removeprefix('CUO-'))
    cuota = models.Cuota.objects.select_for_update().select_related('contrato').filter(pk=cuota_id).first()
    if cuota and cuota.pago_id and Pago.objects.filter(pk=cuota.pago_id, id_transaccion_pasarela=id_transaccion).exists():
        return cuota  # la pasarela reenvió el aviso del pago que ya se aplicó
    if estado == 'rechazado':
        publicar('adopcion.pago_rechazado', 'adopcion.cuota', cuota_id, {'referencia': referencia, 'id_transaccion': id_transaccion})
        return cuota
    if not cuota or cuota.estado != 'pendiente' or cuota.contrato.estado != 'activo':
        with connection.cursor() as cur:
            cur.execute("select exists (select 1 from nucleo.evento_salida where tipo_evento = 'adopcion.pago_sin_cuota' "
                        "and carga->>'id_transaccion' = %s)", [id_transaccion])
            ya_avisado = cur.fetchone()[0]
        if not ya_avisado:
            publicar('adopcion.pago_sin_cuota', 'adopcion.cuota', cuota_id,
                     {'referencia': referencia, 'id_transaccion': id_transaccion, 'valor': valor,
                      'cuota': cuota and cuota.estado, 'accion': 'devolver el pago'})
        return cuota
    if valor != cuota.valor:
        raise ValidationError({'valor': f'La pasarela cobró {valor} y la cuota vale {cuota.valor}'})
    cuota.pago = _facturar_y_cobrar(cuota.contrato.adoptante_id, valor, referencia, id_transaccion)
    cuota.estado, cuota.pagada_en = 'pagada', timezone.now()
    cuota.save(update_fields=['pago', 'estado', 'pagada_en'])
    publicar('adopcion.cuota_pagada', 'adopcion.cuota', cuota.id,
             {'contrato': cuota.contrato.numero, 'periodo': cuota.periodo, 'factura': f'ADO-{cuota.pago.factura.numero}'})
    return cuota


def ado_06_seguir_mi_arbol_mi_animal(*, contrato):
    """ADO-06 · Seguir mi árbol o mi animal

    Actores: Adoptante; secundarios: Operario de campo
    Fase 3 · función adopcion
    Tablas: adopcion.seguimiento, adopcion.cuota, adopcion.movimiento_saldo
    Reglas en la base: adopcion.saldo()
    Endpoints: GET /api/v1/adopcion/mis-bienes/; GET /api/v1/adopcion/mis-bienes/{id}/seguimiento/
    Requerimientos: RQ-48

    Ficha de un contrato para su adoptante: el bien, su seguimiento (fotos, video de siembra...), las cuotas y el saldo
    a favor. Solo datos de ese contrato. La usan el enlace personal (sin cuenta) y /mis-bienes/ (con cuenta).
    """
    bien = models.Bien.objects.select_related('plan', 'sitio').get(pk=contrato.bien_id)
    with connection.cursor() as cur:
        cur.execute('select adopcion.saldo(%s)', [contrato.adoptante_id])
        saldo = cur.fetchone()[0]
    return {
        'contrato': contrato.numero, 'estado': contrato.estado, 'desde': contrato.fecha,
        'bien': {'id': bien.id, 'codigo': bien.codigo, 'nombre': bien.nombre_dado, 'plan': bien.plan.nombre,
                 'tipo': bien.plan.tipo, 'estado': bien.estado, 'sembrado_en': bien.fecha_inicio,
                 'sitio': bien.sitio and bien.sitio.codigo},
        'seguimiento': list(models.Seguimiento.objects.filter(bien=bien).order_by('-fecha')
                            .values('tipo', 'fecha', 'descripcion', 'evidencia_url')),
        'cuotas': list(models.Cuota.objects.filter(contrato=contrato).order_by('-periodo')
                       .values('periodo', 'valor', 'estado', 'vence_en', 'pagada_en')),
        'saldo_a_favor': saldo,
    }


VIGENCIA_ENLACE = timedelta(days=365)


def _huella(codigo):
    return hashlib.sha256(codigo.encode()).hexdigest()


def ado_06_emitir_enlace(*, usuario, contrato_id):
    """Enlace personal del adoptante para seguir su bien sin crear cuenta. Revoca el anterior del mismo contrato.

    Devuelve {'enlace', 'ruta', 'vence_en'}: la ruta lleva el código, que se muestra una sola vez y no se guarda
    (la base solo tiene su huella). Quien lo pide (vendedor o el agente de WhatsApp) lo envía en ese momento.
    """
    # TODO(Volumen 4): el agente lo pide justo al enviarlo por WhatsApp o correo (si el adoptante lo autorizó);
    # nunca va en el outbox, donde quedaría en claro
    contrato = models.Contrato.objects.filter(pk=contrato_id, estado='activo').first()
    if not contrato:
        raise ValidationError({'contrato': 'Solo un contrato activo tiene enlace para su adoptante'})
    codigo = secrets.token_urlsafe(32)
    with transaction.atomic():
        models.EnlaceAdoptante.objects.filter(contrato=contrato, revocado_en__isnull=True).update(revocado_en=timezone.now())
        enlace = models.EnlaceAdoptante.objects.create(contrato=contrato, token_hash=_huella(codigo),
                                                       vence_en=timezone.now() + VIGENCIA_ENLACE, emitido_por=usuario)
    return {'enlace': enlace.id, 'ruta': f'/api/v1/publico/adopcion/{contrato.predio_id}.{codigo}/', 'vence_en': enlace.vence_en}


def ado_06_revocar_enlace(*, usuario, enlace_id):
    """Revoca un enlace (el adoptante lo perdió, lo compartió...). Ceder o terminar el contrato ya lo invalida solo."""
    if not models.EnlaceAdoptante.objects.filter(pk=enlace_id, revocado_en__isnull=True).update(revocado_en=timezone.now()):
        raise NotFound('No hay un enlace vigente con ese número')


def ado_06_contrato_por_enlace(codigo):
    """El contrato que deja ver el código, con la finca ya fijada. Vencido, revocado, contrato no activo o código falso
    responden igual (404), para no dar pistas a quien prueba códigos."""
    enlace = (models.EnlaceAdoptante.objects.select_for_update().select_related('contrato')
              .filter(token_hash=_huella(codigo), revocado_en__isnull=True, vence_en__gt=timezone.now(),
                      contrato__estado='activo').first())
    if not enlace:
        raise NotFound('El enlace no existe o ya no está vigente')
    enlace.ultimo_uso_en = timezone.now()
    enlace.save(update_fields=['ultimo_uso_en'])
    return enlace.contrato


def ado_07_detectar_abandono_poner_readopcion(*, fecha=None):
    """ADO-07 · Detectar abandono y poner en readopción

    Actores: Tareas programadas; secundarios: Adoptante, Gestor de redes (IA)
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.cuota, adopcion.bien, adopcion.seguimiento
    Reglas en la base: adopcion.marcar_abandono()
    Endpoints: POST /api/v1/adopcion/seguimientos/{id}/marcar-enviado/
    Requerimientos: RQ-46

    Parámetros: fecha (por omisión hoy). Devuelve cuántos contratos terminaron por abandono.
    La corre la tarea diaria (config/celery.py, 'adopcion-abandono'). La base hace todo: un aviso de mora por cada
    cuota que se vence (evento adopcion.aviso_mora) y abandono solo con 3 cuotas vencidas y el aviso de la tercera
    entregado hace 15 días o más (dias_gracia_abandono). Nunca hay abandono sin aviso entregado: el Gestor de redes
    lo confirma con ado_07_marcar_enviado().
    """
    with transaction.atomic(), connection.cursor() as cur:
        # marcar_abandono() ya exige la función «adopcion» (422 si está apagada)
        cur.execute('select adopcion.marcar_abandono(coalesce(%s, current_date))', [fecha])
        return cur.fetchone()[0]


def ado_07_marcar_enviado(*, usuario, seguimiento_id):
    """El canal confirmó que el registro le llegó al adoptante (aviso de mora, video de siembra...).

    Solo esta acción pone enviado_al_adoptante (en el CRUD es de solo lectura): del aviso de mora entregado cuentan
    los días de gracia antes del abandono. Repetirla no cambia nada. Devuelve el seguimiento.
    """
    with connection.cursor() as cur:
        cur.execute("select nucleo.exigir_funcion('adopcion')")
    seguimiento = models.Seguimiento.objects.filter(pk=seguimiento_id).first()
    if not seguimiento:
        raise NotFound(f'No hay seguimiento {seguimiento_id}')
    if not seguimiento.enviado_al_adoptante:
        seguimiento.enviado_al_adoptante = True
        seguimiento.save(update_fields=['enviado_al_adoptante'])
    return seguimiento


def ado_08_readoptar(*, usuario, **datos):
    """ADO-08 · Readoptar

    Actores: Adoptante; secundarios: Pasarela de pagos
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.bien
    Reglas en la base: adopcion.validar_contrato()
    Endpoints: POST /api/v1/adopcion/contratos/readopcion/
    Requerimientos: RQ-46

    Parámetros: usuario (vendedor, administrador o agente; el adoptante no necesita cuenta) y **datos (lo que validó
    ReadopcionSerializer). Devuelve (contrato, cobro), igual que la compra (ADO-02).

    El bien quedó en readopción por abandono (ADO-07) y sigue vivo y sembrado en su sitio: el nuevo contrato es tipo
    readopcion, al precio de readopción del plan y sin siembra. El pago lo confirma el mismo aviso de la pasarela
    (ado_02_confirmar_pago); al activarse, la base pasa el bien a activo y desde el mes siguiente se cobra la cuota.
    """
    # shortcut: un precio_readopcion de 0 (la base lo permite) igual pasa por la pasarela; activar sin cobro si un plan lo usa
    bien = datos['bien']
    if bien.estado != 'en_readopcion':
        raise ValidationError({'bien': f'El bien {bien.codigo} no está en readopción (estado {bien.estado})'})
    return _contratar(tipo='readopcion', precio=bien.plan.precio_readopcion, modalidad='no_aplica', **datos)


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


def ado_11_decidir_madurez_mantener_liquidar(*, usuario, contrato_id, decision):
    """ADO-11 · Decidir en la madurez: mantener o liquidar

    Actores: Adoptante; secundarios: Administrador
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato
    Reglas en la base: adopcion.marcar_madurez(), adopcion.validar_contrato()
    Endpoints: POST /api/v1/adopcion/contratos/{id}/decision/
    Requerimientos: RQ-47

    Parámetros: usuario (la persona que registra lo que decidió el adoptante), contrato_id y decision
    ('mantener' o 'liquidar'). Devuelve el contrato.

    adopcion.marcar_madurez() pasa el bien a maduro el día 1 (config/celery.py). La base exige el bien maduro y que
    decida una persona, no un agente (adopcion.validar_contrato), y anota decidido_en. Mantener: el contrato sigue con
    su cuota. Liquidar: el administrador tala, sacrifica o vende en pie y liquida (ADO-12).
    """
    with transaction.atomic():
        contrato = models.Contrato.objects.select_for_update().filter(pk=contrato_id).first()
        if not contrato:
            raise NotFound(f'No hay contrato {contrato_id}')
        if contrato.estado != 'activo':
            raise ValidationError({'contrato': f'El contrato {contrato.numero} no está activo ({contrato.estado})'})
        contrato.decision_madurez = decision
        contrato.save(update_fields=['decision_madurez'])
        contrato.refresh_from_db(fields=['decidido_en'])
        publicar('adopcion.decision_madurez', 'adopcion.contrato', contrato.id,
                 {'numero': contrato.numero, 'bien_id': contrato.bien_id, 'decision': decision})
    return contrato


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


def ado_13_reponer_bien_muerto_garantia(*, usuario, bien_id, fecha, causa):
    """ADO-13 · Reponer un bien muerto en garantía

    Actores: Encargado de finca; secundarios: Adoptante
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato, adopcion.seguimiento
    Reglas en la base: adopcion.registrar_muerte()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/muerte/
    Requerimientos: RQ-48

    Parámetros: usuario (el encargado; la base exige una persona), bien_id, fecha y causa.
    Devuelve {'bien', 'repuesto', 'contrato', 'estado_contrato'}: repuesto es el bien nuevo o None.

    La base decide (adopcion.registrar_muerte): dentro de la garantía del plan y sin cuotas vencidas se repone gratis
    un bien igual en el mismo sitio y el contrato sigue con él; si no, el contrato termina (terminado_muerte), se anulan
    las cuotas futuras y se libera el sitio. Un bien sin dueño solo libera su sitio. Se avisa al adoptante por el outbox.
    """
    with connection.cursor() as cur:
        # adopcion.registrar_muerte() no exige la función: se exige aquí (422 si está apagada)
        cur.execute("select nucleo.exigir_funcion('adopcion')")
    with transaction.atomic():
        if not models.Bien.objects.filter(pk=bien_id).exists():
            raise NotFound(f'No hay bien {bien_id}')
        contrato = models.Contrato.objects.filter(bien_id=bien_id, estado='activo').first()
        with connection.cursor() as cur:
            cur.execute('select adopcion.registrar_muerte(%s, %s, %s)', [bien_id, fecha, causa])
            repuesto = cur.fetchone()[0]
        if contrato:
            contrato.refresh_from_db(fields=['estado'])
            publicar('adopcion.bien_muerto', 'adopcion.contrato', contrato.id,
                     {'numero': contrato.numero, 'bien_id': bien_id, 'repuesto': repuesto, 'causa': causa,
                      'estado_contrato': contrato.estado})
    return {'bien': bien_id, 'repuesto': repuesto, 'contrato': contrato and contrato.id,
            'estado_contrato': contrato and contrato.estado}


def ado_14_ceder_regalar_adopcion(*, usuario, contrato_id, **datos):
    """ADO-14 · Ceder o regalar la adopción

    Actores: Adoptante
    Fase 3 · función adopcion
    Tablas: adopcion.contrato
    Reglas en la base: adopcion.validar_contrato()
    Endpoints: POST /api/v1/adopcion/contratos/{id}/ceder/
    Requerimientos: RQ-48

    Parámetros: usuario (vendedor, administrador o agente), contrato_id (el contrato que se cede) y **datos (lo que
    validó CesionSerializer: el nuevo adoptante y su autorización de datos). Devuelve el contrato nuevo.

    Es un regalo: el contrato nuevo (tipo cesion) nace activo, sin precio ni cobro, con la misma cuota mensual; la
    base deja el anterior cedido (adopcion.ceder_previo) y exige el bien vivo (adopcion.validar_contrato). Para ceder,
    el contrato debe estar al día; las cuotas que aún no vencen pasan al nuevo dueño. El saldo a favor sigue siendo del
    adoptante anterior, y su enlace personal deja de servir (el contrato ya no está activo).
    """
    # TODO(roles): solo el adoptante decide ceder; cuando haya roles, exigir que lo pida él (o su evidencia)
    with transaction.atomic():
        anterior = models.Contrato.objects.select_for_update().select_related('bien__plan').filter(pk=contrato_id).first()
        if not anterior:
            raise NotFound(f'No hay contrato {contrato_id}')
        if anterior.estado != 'activo':
            raise ValidationError({'contrato': f'El contrato {anterior.numero} no está activo ({anterior.estado})'})
        if models.Cuota.objects.filter(contrato=anterior, estado='pendiente', vence_en__lt=timezone.localdate()).exists():
            raise ValidationError({'contrato': 'Para ceder, el contrato debe estar al día con sus cuotas'})
        contrato, _ = _contratar(tipo='cesion', precio=0, modalidad='no_aplica', bien=anterior.bien,
                                 cuota_mensual=anterior.cuota_mensual, cobrar=False, **datos)
        if contrato.adoptante_id == anterior.adoptante_id:
            raise ValidationError({'adoptante': 'El bien ya es de esa persona'})  # deshace la transacción
        models.Cuota.objects.filter(contrato=anterior, estado='pendiente').update(contrato=contrato)
        publicar('adopcion.cedido', 'adopcion.contrato', contrato.id,
                 {'numero': contrato.numero, 'anterior': anterior.numero, 'bien_id': anterior.bien_id})
    return contrato


def ado_15_consultar_tablero_adopcion():
    """ADO-15 · Consultar el tablero de adopción

    Actores: Familia; secundarios: Administrador
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato, adopcion.cuota
    Reglas en la base: adopcion.v_tablero
    Endpoints: GET /api/v1/adopcion/tablero/
    Requerimientos: RQ-48

    Devuelve una fila por tipo de plan (frutal, ovino...): bienes con dueño, en readopción y disponibles, cuotas del
    mes y costo de cuidado estimado. La vista respeta la seguridad por filas (migración 010): solo la finca de la sesión.
    """
    with connection.cursor() as cur:
        cur.execute("select nucleo.exigir_funcion('adopcion')")
    return consultar('select * from adopcion.v_tablero order by tipo')
