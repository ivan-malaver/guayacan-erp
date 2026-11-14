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
# transaction y publicar aún no se usan (las funciones están vacías); «noqa» evita el aviso del revisor
from django.db import transaction  # noqa: F401

from guayacan.eventos import publicar  # noqa: F401


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


def vta_03_tomar_confirmar_pedido(*, usuario, **datos):
    """VTA-03 · Tomar y confirmar un pedido

    Actores: Vendedor, Cliente; secundarios: Asesor virtual (IA)
    Fase 1
    Tablas: comercial.pedido, comercial.pedido_detalle, comercial.reserva_lote
    Reglas en la base: inventario.reservar_fefo(), comercial.confirmar_pedido(), inventario.puede_venderse()
    Endpoints: POST /api/v1/comercial/pedidos/{id}/confirmar/
    Requerimientos: RF-10, RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para VTA-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.reservar_fefo(), comercial.confirmar_pedido(), inventario.puede_venderse()
    # 4. publicar('comercial.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('VTA-03: por construir')


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
