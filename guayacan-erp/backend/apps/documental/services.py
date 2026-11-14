"""Casos de uso del esquema documental: una función por caso de uso.

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


def doc_01_publicar_documento_version_aprobada(*, usuario, **datos):
    """DOC-01 · Publicar un documento con versión aprobada

    Actores: Encargado de finca, Administrador
    Fase 1
    Tablas: documental.documento, documental.version_documento
    Reglas en la base: documental.validar_version(), documental.obsoletar_anteriores()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-32

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para DOC-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: documental.validar_version(), documental.obsoletar_anteriores()
    # 4. publicar('documental.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('DOC-01: por construir')


def doc_02_vincular_documentos_vigilar_vencimientos(*, usuario, **datos):
    """DOC-02 · Vincular documentos y vigilar vencimientos

    Actores: Tareas programadas, Encargado de finca
    Fase 1
    Tablas: documental.vinculo_documento, documental.documento
    Reglas en la base: documental.v_vigentes
    Endpoints: GET /api/v1/documental/vigentes/
    Requerimientos: RQ-32, RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para DOC-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: documental.v_vigentes
    # 4. publicar('documental.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('DOC-02: por construir')


def doc_03_consultar_documentos_vigentes(*, usuario, **datos):
    """DOC-03 · Consultar documentos vigentes

    Actores: Usuario autenticado; secundarios: Instructor (IA), Agrónomo (IA)
    Fase 1
    Tablas: documental.version_documento
    Reglas en la base: documental.documento_para_agente()
    Endpoints: GET /api/v1/documental/vigentes/
    Requerimientos: RQ-32, RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para DOC-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: documental.documento_para_agente()
    # 4. publicar('documental.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('DOC-03: por construir')
