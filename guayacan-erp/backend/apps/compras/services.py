"""Casos de uso del esquema compras: una función por caso de uso.

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


def cmp_01_registrar_cotizaciones_precios_mercado(*, usuario, **datos):
    """CMP-01 · Registrar cotizaciones y precios de mercado

    Actores: Administrador; secundarios: Analista de mercados (IA), Fuentes de mercado
    Fase 1
    Tablas: compras.cotizacion_proveedor, compras.precio_mercado
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CMP-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('compras.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CMP-01: por construir')


def cmp_02_crear_aprobar_orden_compra(*, usuario, **datos):
    """CMP-02 · Crear y aprobar una orden de compra

    Actores: Administrador; secundarios: Analista de mercados (IA)
    Fase 1
    Tablas: compras.orden_compra, compras.orden_compra_detalle
    Reglas en la base: formato y permisos de DRF
    Endpoints: POST /api/v1/compras/ordenes-compra/{id}/aprobar/
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CMP-02:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('compras.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CMP-02: por construir')


def cmp_03_recibir_compra_bodega(*, usuario, **datos):
    """CMP-03 · Recibir una compra en bodega

    Actores: Operario de campo
    Fase 1
    Tablas: compras.orden_compra, inventario.lote_inventario
    Reglas en la base: inventario.entrada_inicial()
    Endpoints: POST /api/v1/compras/ordenes-compra/{id}/recibir/
    Requerimientos: RF-06

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CMP-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.entrada_inicial()
    # 4. publicar('compras.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CMP-03: por construir')


def cmp_04_emitir_documento_soporte_electronico(*, usuario, **datos):
    """CMP-04 · Emitir un documento soporte electrónico

    Actores: Contador; secundarios: DIAN
    Fase 1
    Tablas: compras.documento_soporte
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CMP-04:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('compras.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CMP-04: por construir')
