"""Casos de uso del esquema personal: una función por caso de uso.

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


def per_01_configurar_areas_responsabilidad_matriz_raci(*, usuario, **datos):
    """PER-01 · Configurar áreas de responsabilidad y matriz RACI

    Actores: Administrador
    Fase 1
    Tablas: personal.area_responsabilidad, personal.miembro_area, personal.matriz_responsabilidad
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-28

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-01: por construir')


def per_02_definir_plan_labores(*, usuario, **datos):
    """PER-02 · Definir el plan de labores

    Actores: Encargado de finca
    Fase 1
    Tablas: personal.plantilla_tarea
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-28

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-02:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-02: por construir')


def per_03_generar_tareas_dia(*, usuario, **datos):
    """PER-03 · Generar las tareas del día

    Actores: Tareas programadas; secundarios: Coordinador (IA)
    Fase 1
    Tablas: personal.tarea, personal.paso_tarea
    Reglas en la base: personal.generar_tareas_del_dia()
    Endpoints: POST /api/v1/personal/tareas/generar-dia/
    Requerimientos: RQ-28

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: personal.generar_tareas_del_dia()
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-03: por construir')


def per_04_asignar_tarea(*, usuario, **datos):
    """PER-04 · Asignar una tarea

    Actores: Encargado de finca; secundarios: Coordinador (IA)
    Fase 1
    Tablas: personal.tarea
    Reglas en la base: personal.validar_tarea(), personal.validar_area_tarea(), personal.empleado_disponible(), formacion.esta_habilitado()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-28, RQ-30

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: personal.validar_tarea(), personal.validar_area_tarea(), personal.empleado_disponible()
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-04: por construir')


def per_05_ejecutar_tarea_evidencia(*, usuario, **datos):
    """PER-05 · Ejecutar una tarea con evidencia

    Actores: Operario de campo
    Fase 1
    Tablas: personal.tarea, personal.paso_tarea, personal.evidencia_tarea
    Reglas en la base: personal.validar_tarea()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-28, RNF-03

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: personal.validar_tarea()
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-05: por construir')


def per_06_aprobar_devolver_tarea(*, usuario, **datos):
    """PER-06 · Aprobar o devolver una tarea

    Actores: Encargado de finca
    Fase 1
    Tablas: personal.tarea
    Reglas en la base: personal.validar_tarea(), personal.es_responsable_area()
    Endpoints: POST /api/v1/personal/tareas/{id}/aprobar/
    Requerimientos: RQ-28, RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: personal.validar_tarea(), personal.es_responsable_area()
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-06: por construir')


def per_07_armar_publicar_cronograma_turnos(*, usuario, **datos):
    """PER-07 · Armar y publicar el cronograma de turnos

    Actores: Encargado de finca; secundarios: Coordinador (IA)
    Fase 2
    Tablas: personal.cronograma, personal.patron_turno, personal.asignacion_patron, personal.requerimiento_cobertura, personal.turno
    Reglas en la base: personal.generar_turnos(), personal.huecos_cobertura(), personal.publicar_cronograma(), personal.validar_turno()
    Endpoints: POST /api/v1/personal/cronogramas/{id}/generar/; GET /api/v1/personal/cronogramas/{id}/huecos/; POST /api/v1/personal/cronogramas/{id}/publicar/
    Requerimientos: RQ-40

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: personal.generar_turnos(), personal.huecos_cobertura(), personal.publicar_cronograma()
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-07: por construir')


def per_08_registrar_disponibilidad_ausencias(*, usuario, **datos):
    """PER-08 · Registrar disponibilidad y ausencias

    Actores: Operario de campo, Encargado de finca
    Fase 2
    Tablas: personal.disponibilidad, personal.ausencia
    Reglas en la base: personal.empleado_disponible()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-40

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-08:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: personal.empleado_disponible()
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-08: por construir')


def per_09_registrar_jornada_carne(*, usuario, **datos):
    """PER-09 · Registrar la jornada con el carné

    Actores: Operario de campo; secundarios: Portería
    Fase 1
    Tablas: personal.jornada, personal.credencial_trabajo
    Reglas en la base: personal.calcular_jornada()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-28, RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: personal.calcular_jornada()
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-09: por construir')


def per_10_organizar_cuadrillas(*, usuario, **datos):
    """PER-10 · Organizar cuadrillas

    Actores: Encargado de finca
    Fase 1
    Tablas: personal.cuadrilla, personal.cuadrilla_miembro
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-28

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PER-10:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('personal.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PER-10: por construir')
