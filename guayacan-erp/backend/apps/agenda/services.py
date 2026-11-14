"""Casos de uso del esquema agenda: una función por caso de uso.

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


def agd_01_configurar_recursos_agendables(*, usuario, **datos):
    """AGD-01 · Configurar recursos agendables

    Actores: Administrador
    Fase 3
    Tablas: agenda.recurso
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-01: por construir')


def agd_02_agendar_cita_recurso(*, usuario, **datos):
    """AGD-02 · Agendar una cita en un recurso

    Actores: Encargado de finca, Vendedor
    Fase 3
    Tablas: agenda.cita
    Reglas en la base: agenda.preparar_cita(), exclusión GiST sin cruces, agenda.recurso_libre()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.preparar_cita(), exclusión GiST sin cruces, agenda.recurso_libre()
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-02: por construir')


def agd_03_programar_aprobar_visita(*, usuario, **datos):
    """AGD-03 · Programar y aprobar una visita

    Actores: Encargado de finca; secundarios: Visitante o turista, Correo y SMS
    Fase 2
    Tablas: agenda.visita
    Reglas en la base: agenda.validar_visita(), agenda.emitir_pase()
    Endpoints: POST /api/v1/agenda/visitas/{id}/aprobar/; POST /api/v1/agenda/visitas/{id}/pase/
    Requerimientos: RQ-39, RF-16

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.validar_visita(), agenda.emitir_pase()
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-03: por construir')


def agd_04_registrar_entradas_salidas_porteria(*, usuario, **datos):
    """AGD-04 · Registrar entradas y salidas en portería

    Actores: Portería; secundarios: Visitante o turista
    Fase 2
    Tablas: agenda.registro_acceso, personal.jornada
    Reglas en la base: agenda.validar_acceso()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-39, RF-16

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.validar_acceso()
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-04: por construir')


def agd_05_consultar_quien_esta_finca(*, usuario, **datos):
    """AGD-05 · Consultar quién está en la finca

    Actores: Portería, Administrador; secundarios: Pasarela IoT local
    Fase 2
    Tablas: agenda.registro_acceso
    Reglas en la base: agenda.v_en_sitio
    Endpoints: GET /api/v1/agenda/en-sitio/
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.v_en_sitio
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-05: por construir')


def agd_06_consultar_agenda_dia(*, usuario, **datos):
    """AGD-06 · Consultar la agenda del día

    Actores: Encargado de finca, Portería
    Fase 2
    Tablas: agenda.cita, agenda.visita, personal.turno
    Reglas en la base: agenda.v_agenda_dia
    Endpoints: GET /api/v1/agenda/dia/?fecha=
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.v_agenda_dia
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-06: por construir')
