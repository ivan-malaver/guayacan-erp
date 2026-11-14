"""Casos de uso del esquema activos: una función por caso de uso.

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


def act_01_registrar_activo_hoja_vida(*, usuario, **datos):
    """ACT-01 · Registrar un activo con su hoja de vida

    Actores: Administrador
    Fase 2
    Tablas: activos.activo, activos.plan_mantenimiento
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-31

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ACT-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('activos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ACT-01: por construir')


def act_02_registrar_uso_activo(*, usuario, **datos):
    """ACT-02 · Registrar el uso de un activo

    Actores: Operario de campo; secundarios: Pasarela IoT local
    Fase 2
    Tablas: activos.uso_activo
    Reglas en la base: activos.sumar_uso()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-31

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ACT-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: activos.sumar_uso()
    # 4. publicar('activos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ACT-02: por construir')


def act_03_generar_cerrar_ordenes_mantenimiento(*, usuario, **datos):
    """ACT-03 · Generar y cerrar órdenes de mantenimiento

    Actores: Tareas programadas, Encargado de finca, Operario de campo
    Fase 2
    Tablas: activos.orden_trabajo, activos.repuesto_orden, personal.tarea
    Reglas en la base: activos.generar_ordenes_trabajo(), activos.cerrar_orden()
    Endpoints: POST /api/v1/activos/ordenes-trabajo/generar/
    Requerimientos: RQ-31

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ACT-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: activos.generar_ordenes_trabajo(), activos.cerrar_orden()
    # 4. publicar('activos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ACT-03: por construir')


def act_04_depreciar_activos_mes(*, usuario, **datos):
    """ACT-04 · Depreciar los activos del mes

    Actores: Tareas programadas, Contador
    Fase 2
    Tablas: activos.depreciacion
    Reglas en la base: activos.depreciar_mes()
    Endpoints: POST /api/v1/activos/depreciar/?mes=
    Requerimientos: RQ-31, RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ACT-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: activos.depreciar_mes()
    # 4. publicar('activos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ACT-04: por construir')


def act_05_asignar_equipo_trabajador(*, usuario, **datos):
    """ACT-05 · Asignar un equipo a un trabajador

    Actores: Encargado de finca
    Fase 2
    Tablas: personal.asignacion_equipo
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-31, RQ-28

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ACT-05:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('activos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ACT-05: por construir')
