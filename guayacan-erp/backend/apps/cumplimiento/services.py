"""Casos de uso del esquema cumplimiento: una función por caso de uso.

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


def cum_01_cargar_normas_requisitos(*, usuario, **datos):
    """CUM-01 · Cargar normas y requisitos

    Actores: Administrador
    Fase 1
    Tablas: cumplimiento.norma, cumplimiento.requisito
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CUM-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('cumplimiento.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CUM-01: por construir')


def cum_02_abrir_expediente_cumplimiento(*, usuario, **datos):
    """CUM-02 · Abrir un expediente de cumplimiento

    Actores: Administrador
    Fase 1
    Tablas: cumplimiento.expediente
    Reglas en la base: cumplimiento.validar_expediente()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CUM-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: cumplimiento.validar_expediente()
    # 4. publicar('cumplimiento.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CUM-02: por construir')


def cum_03_evaluar_expediente_contra_evidencia(*, usuario, **datos):
    """CUM-03 · Evaluar el expediente contra su evidencia

    Actores: Tareas programadas
    Fase 1
    Tablas: cumplimiento.evaluacion_requisito
    Reglas en la base: cumplimiento.evaluar_expediente()
    Endpoints: POST /api/v1/cumplimiento/expedientes/{id}/evaluar/
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CUM-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: cumplimiento.evaluar_expediente()
    # 4. publicar('cumplimiento.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CUM-03: por construir')


def cum_04_adjuntar_evidencias_requisito(*, usuario, **datos):
    """CUM-04 · Adjuntar evidencias a un requisito

    Actores: Encargado de finca
    Fase 1
    Tablas: cumplimiento.evidencia_requisito
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CUM-04:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('cumplimiento.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CUM-04: por construir')


def cum_05_registrar_auditoria_externa_no_conformidades(*, usuario, **datos):
    """CUM-05 · Registrar una auditoría externa y sus no conformidades

    Actores: Administrador; secundarios: Auditor externo
    Fase 2
    Tablas: cumplimiento.auditoria_externa, cumplimiento.no_conformidad
    Reglas en la base: formato y permisos de DRF
    Endpoints: GET /api/v1/cumplimiento/expedientes/{id}/paquete-auditor/
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CUM-05:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('cumplimiento.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CUM-05: por construir')


def cum_06_ejecutar_verificar_acciones_correctivas(*, usuario, **datos):
    """CUM-06 · Ejecutar y verificar acciones correctivas

    Actores: Encargado de finca, Administrador
    Fase 2
    Tablas: cumplimiento.accion_correctiva, cumplimiento.no_conformidad, personal.tarea
    Reglas en la base: cumplimiento.verificar_accion(), cumplimiento.cerrar_no_conformidad()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-33, RQ-28

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CUM-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: cumplimiento.verificar_accion(), cumplimiento.cerrar_no_conformidad()
    # 4. publicar('cumplimiento.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CUM-06: por construir')


def cum_07_vigilar_obligacion_granja_avicola_biosegura(*, usuario, **datos):
    """CUM-07 · Vigilar la obligación de granja avícola biosegura

    Actores: Tareas programadas, Administrador
    Fase 1
    Tablas: produccion.lote_animal
    Reglas en la base: cumplimiento.v_granja_biosegura
    Endpoints: GET /api/v1/cumplimiento/granja-biosegura/
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CUM-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: cumplimiento.v_granja_biosegura
    # 4. publicar('cumplimiento.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CUM-07: por construir')
