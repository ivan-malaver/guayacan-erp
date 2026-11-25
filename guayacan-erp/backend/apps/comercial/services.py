"""Casos de uso del esquema comercial: una función por caso de uso.

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
# publicar aún no se usa (las funciones están vacías); «noqa» evita el aviso del revisor
import uuid

from django.db import connection, transaction
from rest_framework.exceptions import NotFound, ValidationError

from guayacan.eventos import publicar  # noqa: F401

from . import models


def vta_01_gestionar_listas_precios_vigencia(*, usuario, **datos):
    """VTA-01 · Gestionar listas y precios con vigencia

    Actores: Administrador
    Fase 1
    Tablas: comercial.lista_precios, comercial.precio_producto
    Reglas en la base: precio nunca se edita: se cierra y se crea
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-09

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: precio nunca se edita: se cierra y se crea
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-01: por construir')


def vta_02_proponer_aprobar_cambio_precio(*, usuario, **datos):
    """VTA-02 · Proponer y aprobar un cambio de precio

    Actores: Administrador; secundarios: Analista de mercados (IA)
    Fase 1
    Tablas: comercial.propuesta_precio, ia.solicitud_aprobacion
    Reglas en la base: comercial.aplicar_propuesta_precio()
    Endpoints: POST /api/v1/comercial/propuestas-precio/{id}/aprobar/
    Requerimientos: RF-09, RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: comercial.aplicar_propuesta_precio()
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-02: por construir')


def crear_pedido(*, usuario, **datos):
    """VTA-03 paso 1 · El pedido nace en borrador con número PED-<id> (único por finca, sin secuencia aparte)."""
    with transaction.atomic():
        pedido = models.Pedido.objects.create(numero=uuid.uuid4().hex[:20], **datos)  # provisional: el id aún no existe
        pedido.numero = f'PED-{pedido.pk}'
        pedido.save(update_fields=['numero'])
        pedido.refresh_from_db()
    return pedido


def _en_borrador(pedido_id):
    """El pedido bloqueado para cambiarlo; solo en borrador se tocan sus datos y sus líneas (4c)."""
    pedido = models.Pedido.objects.select_for_update().filter(pk=pedido_id).first()
    if not pedido:
        raise NotFound(f'No hay pedido {pedido_id}')
    if pedido.estado != 'borrador':
        raise ValidationError({'estado': f'El pedido {pedido.numero} está {pedido.estado}: ya no se puede cambiar'})
    return pedido


def actualizar_pedido(*, usuario, pedido_id, **datos):
    """VTA-03 · Cambiar cliente, canal o entrega mientras el pedido está en borrador."""
    with transaction.atomic():
        pedido = _en_borrador(pedido_id)
        for campo, valor in datos.items():
            setattr(pedido, campo, valor)
        pedido.save()
        pedido.refresh_from_db()
    return pedido


def guardar_linea(*, usuario, pedido_id, linea=None, **datos):
    """VTA-03 pasos 1-2 · Crea o cambia una línea con el precio vigente de la lista del cliente (o PUBLICO).

    El usuario envía producto, cantidad y descuento; precio, IVA del producto y total los pone esta función. Al editar
    la línea se vuelve a tomar el precio vigente: así se resuelve el 4b («actualícelo antes de confirmar»).
    """
    with transaction.atomic():
        pedido = _en_borrador(pedido_id)
        linea = linea or models.PedidoDetalle(pedido=pedido)
        for campo, valor in datos.items():
            setattr(linea, campo, valor)
        lista = pedido.cliente.lista_precios_id or models.ListaPrecios.objects.filter(codigo='PUBLICO').values_list('id', flat=True).first()
        precio = models.PrecioProducto.objects.filter(producto=linea.producto, lista_precios_id=lista, vigente_hasta__isnull=True).first()
        if not precio:
            raise ValidationError({'producto': f'{linea.producto.nombre} no tiene precio vigente en la lista del cliente'})
        linea.precio_producto = precio
        linea.precio_unitario = precio.precio_unitario
        linea.tarifa_iva = linea.producto.tarifa_iva
        linea.total_linea = linea.cantidad * precio.precio_unitario - linea.descuento
        linea.save()
        linea.refresh_from_db()
    return linea


def vta_03_tomar_confirmar_pedido(*, usuario, pedido_id):
    """VTA-03 · Tomar y confirmar un pedido

    Actores: Vendedor, Cliente; secundarios: Asesor virtual (IA)
    Fase 1
    Tablas: comercial.pedido, comercial.pedido_detalle, comercial.reserva_lote
    Reglas en la base: inventario.reservar_fefo(), comercial.confirmar_pedido(), inventario.puede_venderse()
    Endpoints: POST /api/v1/comercial/pedidos/{id}/confirmar/ (el borrador y sus líneas son el CRUD)
    Requerimientos: RF-10, RQ-27

    La base valida estado (4c), crédito, precio vigente (4b) e inventario (4a, sin reservas a medias), reserva por
    FEFO, congela los totales y publica pedido.confirmado; quien avisa al cliente por su canal escucha ese evento.
    Devuelve el pedido confirmado.
    """
    with transaction.atomic():
        if not models.Pedido.objects.filter(pk=pedido_id).exists():
            raise NotFound(f'No hay pedido {pedido_id}')
        with connection.cursor() as cur:
            cur.execute('select comercial.confirmar_pedido(%s)', [pedido_id])
    return models.Pedido.objects.get(pk=pedido_id)


def cancelar_pedido(*, usuario, pedido_id):
    """VTA-03 5a · Cancelar antes de despachar: comercial.cancelar_pedido() libera las reservas; después de despachar
    la base lo rechaza (solo hay devolución). Devuelve el pedido cancelado."""
    with transaction.atomic():
        if not models.Pedido.objects.filter(pk=pedido_id).exists():
            raise NotFound(f'No hay pedido {pedido_id}')
        with connection.cursor() as cur:
            cur.execute('select comercial.cancelar_pedido(%s)', [pedido_id])
    return models.Pedido.objects.get(pk=pedido_id)


def vta_04_vender_finca_feria_sin_conexion(*, usuario, **datos):
    """VTA-04 · Vender en la finca o en la feria sin conexión

    Actores: Vendedor
    Fase 2
    Tablas: comercial.pedido, comercial.pago
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-12, RNF-03

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-04:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-04: por construir')


def vta_05_despachar_entregar_pedido(*, usuario, **datos):
    """VTA-05 · Despachar y entregar un pedido

    Actores: Operario de campo, Vendedor; secundarios: Pasarela IoT local
    Fase 1
    Tablas: comercial.entrega, comercial.reserva_lote, inventario.movimiento_inventario
    Reglas en la base: comercial.despachar_pedido()
    Endpoints: POST /api/v1/comercial/pedidos/{id}/despachar/
    Requerimientos: RF-10, RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: comercial.despachar_pedido()
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-05: por construir')


def vta_06_facturar_electronicamente(*, usuario, **datos):
    """VTA-06 · Facturar electrónicamente

    Actores: Tareas programadas; secundarios: DIAN
    Fase 1
    Tablas: comercial.factura
    Reglas en la base: comercial.preparar_factura(), regla fija, no IA
    Endpoints: POST /api/v1/comercial/pedidos/{id}/facturar/
    Requerimientos: RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: comercial.preparar_factura(), regla fija, no IA
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-06: por construir')


def vta_07_registrar_confirmar_pago(*, usuario, **datos):
    """VTA-07 · Registrar y confirmar un pago

    Actores: Vendedor, Contador; secundarios: Pasarela de pagos
    Fase 1
    Tablas: comercial.pago
    Reglas en la base: comercial.aplicar_pago(), un agente no confirma pagos
    Endpoints: POST /api/v1/comercial/pagos/{id}/confirmar/; POST /api/v1/pagos/webhook/
    Requerimientos: RF-21

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: comercial.aplicar_pago(), un agente no confirma pagos
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-07: por construir')


def vta_08_vender_credito_controlar_cartera(*, usuario, **datos):
    """VTA-08 · Vender a crédito y controlar la cartera

    Actores: Contador, Vendedor; secundarios: Correo y SMS
    Fase 2 · función venta_credito
    Tablas: comercial.factura, terceros.cliente
    Reglas en la base: comercial.confirmar_pedido(), comercial.actualizar_mora(), comercial.v_cartera
    Endpoints: GET /api/v1/comercial/cartera/
    Requerimientos: RF-11

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-08:
    # 1. with transaction.atomic():
    # 2. La función «venta_credito» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: comercial.confirmar_pedido(), comercial.actualizar_mora(), comercial.v_cartera
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-08: por construir')


def vta_09_generar_pedidos_recurrentes(*, usuario, **datos):
    """VTA-09 · Generar pedidos recurrentes

    Actores: Tareas programadas, Vendedor
    Fase 2 · función pedidos_recurrentes
    Tablas: comercial.pedido_recurrente, comercial.pedido_recurrente_detalle
    Reglas en la base: comercial.generar_pedidos_recurrentes()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-10

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-09:
    # 1. with transaction.atomic():
    # 2. La función «pedidos_recurrentes» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: comercial.generar_pedidos_recurrentes()
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-09: por construir')


def vta_10_registrar_permuta(*, usuario, **datos):
    """VTA-10 · Registrar una permuta

    Actores: Contador; secundarios: DIAN
    Fase 2 · función permuta
    Tablas: comercial.permuta, compras.documento_soporte, comercial.factura
    Reglas en la base: comercial.aplicar_permuta()
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-10:
    # 1. with transaction.atomic():
    # 2. La función «permuta» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: comercial.aplicar_permuta()
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-10: por construir')


def vta_11_consultar_trazabilidad_lote(*, usuario, **datos):
    """VTA-11 · Consultar la trazabilidad de un lote

    Actores: Cliente, Administrador
    Fase 1
    Tablas: comercial.huella_trazabilidad
    Reglas en la base: comercial.v_trazabilidad_lote, comercial.verificar_cadena_huellas()
    Endpoints: GET /api/v1/publico/trazabilidad/{codigo}/
    Requerimientos: RF-06

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-11:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: comercial.v_trazabilidad_lote, comercial.verificar_cadena_huellas()
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-11: por construir')


def vta_12_retirar_lote_mercado(*, usuario, **datos):
    """VTA-12 · Retirar un lote del mercado

    Actores: Administrador; secundarios: Correo y SMS, Canales de mensajería
    Fase 1
    Tablas: comercial.retiro_lote, comercial.retiro_aviso, inventario.bloqueo_lote
    Reglas en la base: comercial.abrir_retiro()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-06, RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-12:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: comercial.abrir_retiro()
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-12: por construir')
