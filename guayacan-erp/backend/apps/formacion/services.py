"""Casos de uso del esquema formacion: una función por caso de uso.

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


def for_01_disenar_curso_lecciones_evaluacion(*, usuario, **datos):
    """FOR-01 · Diseñar un curso con lecciones y evaluación

    Actores: Instructor; secundarios: Plataforma de cursos
    Fase 2
    Tablas: formacion.curso, formacion.leccion, formacion.evaluacion, formacion.pregunta, formacion.competencia
    Reglas en la base: formacion.validar_curso()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: formacion.validar_curso()
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-01: por construir')


def for_02_tomar_curso_virtual(*, usuario, **datos):
    """FOR-02 · Tomar un curso virtual

    Actores: Estudiante, Operario de campo
    Fase 2
    Tablas: formacion.inscripcion, formacion.progreso
    Reglas en la base: formacion.validar_inscripcion(), formacion.certificar_inscripcion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: formacion.validar_inscripcion(), formacion.certificar_inscripcion()
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-02: por construir')


def for_03_dictar_sesion_presencial_registrar_asistencia(*, usuario, **datos):
    """FOR-03 · Dictar una sesión presencial y registrar asistencia

    Actores: Instructor; secundarios: Estudiante, Operario de campo
    Fase 2
    Tablas: formacion.sesion_presencial, formacion.asistencia
    Reglas en la base: formacion.certificar_sesion()
    Endpoints: POST /api/v1/formacion/sesiones-presenciales/{id}/certificar/
    Requerimientos: RQ-30

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: formacion.certificar_sesion()
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-03: por construir')


def for_04_emitir_certificados_habilitaciones(*, usuario, **datos):
    """FOR-04 · Emitir certificados y habilitaciones

    Actores: Tareas programadas
    Fase 2
    Tablas: formacion.certificado, formacion.habilitacion
    Reglas en la base: formacion.emitir_certificado(), formacion.habilitar_desde_certificado()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: formacion.emitir_certificado(), formacion.habilitar_desde_certificado()
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-04: por construir')


def for_05_retirar_habilitaciones_vencidas(*, usuario, **datos):
    """FOR-05 · Retirar habilitaciones vencidas

    Actores: Tareas programadas
    Fase 2
    Tablas: formacion.habilitacion
    Reglas en la base: formacion.actualizar_habilitaciones()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: formacion.actualizar_habilitaciones()
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-05: por construir')


def for_06_detectar_necesidades_formacion(*, usuario, **datos):
    """FOR-06 · Detectar necesidades de formación

    Actores: Encargado de finca
    Fase 2
    Tablas: formacion.necesidad_formacion
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30, RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-06:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-06: por construir')


def for_07_responder_encuesta_curso(*, usuario, **datos):
    """FOR-07 · Responder la encuesta de un curso

    Actores: Estudiante, Operario de campo
    Fase 2
    Tablas: formacion.encuesta
    Reglas en la base: formacion.v_satisfaccion
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30, RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: formacion.v_satisfaccion
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-07: por construir')


def for_08_presentar_resolver_queja_apelacion(*, usuario, **datos):
    """FOR-08 · Presentar y resolver una queja o apelación

    Actores: Estudiante, Operario de campo; secundarios: Administrador
    Fase 2
    Tablas: formacion.queja_apelacion
    Reglas en la base: formacion.validar_queja()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30, RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-08:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: formacion.validar_queja()
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-08: por construir')


def for_09_preguntar_instructor_virtual(*, usuario, **datos):
    """FOR-09 · Preguntar al Instructor virtual

    Actores: Operario de campo, Estudiante; secundarios: Instructor (IA)
    Fase 2
    Tablas: documental.version_documento, ia.fragmento_conocimiento
    Reglas en la base: documental.documento_para_agente()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-30, RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FOR-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: documental.documento_para_agente()
    # 4. publicar('formacion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FOR-09: por construir')
