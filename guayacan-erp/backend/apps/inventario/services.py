"""Casos de uso del esquema inventario: una función por caso de uso.

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


def inv_01_gestionar_productos_unidades_bodegas(*, usuario, **datos):
    """INV-01 · Gestionar productos, unidades y bodegas

    Actores: Administrador
    Fase 1
    Tablas: inventario.producto, inventario.unidad_medida, inventario.categoria_producto, inventario.bodega
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-09

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para INV-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('inventario.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('INV-01: por construir')


def inv_02_recibir_lote_bodega_etiquetarlo(*, usuario, **datos):
    """INV-02 · Recibir un lote en bodega y etiquetarlo

    Actores: Operario de campo
    Fase 1
    Tablas: inventario.lote_inventario, inventario.etiqueta, inventario.movimiento_inventario
    Reglas en la base: inventario.estimar_vencimiento(), inventario.entrada_inicial()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-06, RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para INV-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.estimar_vencimiento(), inventario.entrada_inicial()
    # 4. publicar('inventario.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('INV-02: por construir')


def inv_03_escanear_codigo_pesar_bascula(*, usuario, **datos):
    """INV-03 · Escanear un código y pesar con báscula

    Actores: Operario de campo, Vendedor; secundarios: Pasarela IoT local
    Fase 1
    Tablas: inventario.lectura_codigo, inventario.pesaje
    Reglas en la base: peso no estable no vende
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-06, RNF-03

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para INV-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: peso no estable no vende
    # 4. publicar('inventario.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('INV-03: por construir')


def inv_04_registrar_merma_ajuste_traslado(*, usuario, **datos):
    """INV-04 · Registrar merma, ajuste o traslado

    Actores: Operario de campo, Encargado de finca
    Fase 1
    Tablas: inventario.movimiento_inventario
    Reglas en la base: inventario.aplicar_movimiento(), inventario.proteger_cantidades()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para INV-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.aplicar_movimiento(), inventario.proteger_cantidades()
    # 4. publicar('inventario.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('INV-04: por construir')


def inv_05_hacer_conteo_fisico(*, usuario, **datos):
    """INV-05 · Hacer un conteo físico

    Actores: Operario de campo, Encargado de finca
    Fase 1
    Tablas: inventario.conteo_fisico, inventario.conteo_detalle
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para INV-05:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('inventario.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('INV-05: por construir')


def inv_06_vigilar_vencimientos_liquidar(*, usuario, **datos):
    """INV-06 · Vigilar vencimientos y liquidar

    Actores: Tareas programadas, Vendedor; secundarios: Asesor virtual (IA)
    Fase 1
    Tablas: inventario.lote_inventario
    Reglas en la base: inventario.marcar_vencidos(), inventario.v_alertas_vencimiento
    Endpoints: GET /api/v1/inventario/alertas-vencimiento/
    Requerimientos: RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para INV-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.marcar_vencidos(), inventario.v_alertas_vencimiento
    # 4. publicar('inventario.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('INV-06: por construir')


def inv_07_vigilar_cadena_frio_decidir_sobre(*, usuario, **datos):
    """INV-07 · Vigilar la cadena de frío y decidir sobre un lote bloqueado

    Actores: Encargado de finca; secundarios: Pasarela IoT local, Tareas programadas
    Fase 2 · función cadena_frio_finca
    Tablas: inventario.excursion_temperatura, inventario.bloqueo_lote, inventario.vehiculo
    Reglas en la base: inventario.evaluar_excursion(), inventario.aplicar_bloqueo()
    Endpoints: POST /api/v1/inventario/bloqueos-lote/{id}/decidir/
    Requerimientos: RQ-27

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para INV-07:
    # 1. with transaction.atomic():
    # 2. La función «cadena_frio_finca» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: inventario.evaluar_excursion(), inventario.aplicar_bloqueo()
    # 4. publicar('inventario.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('INV-07: por construir')
