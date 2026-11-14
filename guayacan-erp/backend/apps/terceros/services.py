"""Casos de uso del esquema terceros: una función por caso de uso.

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


def ter_01_registrar_tercero_persona_empresa(*, usuario, **datos):
    """TER-01 · Registrar un tercero (persona o empresa)

    Actores: Vendedor, Contador, Administrador
    Fase 1
    Tablas: terceros.tercero
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-10

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TER-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('terceros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TER-01: por construir')


def ter_02_registrar_revocar_autorizacion_datos(*, usuario, **datos):
    """TER-02 · Registrar y revocar una autorización de datos

    Actores: Cliente, Vendedor
    Fase 1
    Tablas: terceros.consentimiento_datos
    Reglas en la base: crm.consentimiento_vigente(), redes.verificar_envio()
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TER-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: crm.consentimiento_vigente(), redes.verificar_envio()
    # 4. publicar('terceros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TER-02: por construir')


def ter_03_atender_solicitud_titular_datos(*, usuario, **datos):
    """TER-03 · Atender una solicitud del titular de datos

    Actores: Titular de datos; secundarios: Administrador
    Fase 1
    Tablas: terceros.consentimiento_datos, terceros.tercero
    Reglas en la base: formato y permisos de DRF
    Endpoints: GET /api/v1/terceros/{id}/datos-personales/
    Requerimientos: RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TER-03:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('terceros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TER-03: por construir')


def ter_04_gestionar_clientes_proveedores_empleados(*, usuario, **datos):
    """TER-04 · Gestionar clientes, proveedores y empleados

    Actores: Administrador, Contador, Vendedor
    Fase 1
    Tablas: terceros.cliente, terceros.proveedor, terceros.empleado
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-10

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TER-04:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('terceros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TER-04: por construir')
