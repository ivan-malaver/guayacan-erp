"""Casos de uso del esquema seguros: una función por caso de uso.

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


def sgr_01_registrar_poliza_bienes_asegurados(*, usuario, **datos):
    """SGR-01 · Registrar una póliza y sus bienes asegurados

    Actores: Administrador; secundarios: Aseguradora
    Fase 2
    Tablas: seguros.poliza, seguros.bien_asegurado
    Reglas en la base: seguros.preparar_poliza()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-34

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SGR-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguros.preparar_poliza()
    # 4. publicar('seguros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SGR-01: por construir')


def sgr_02_avisar_polizas_proximas_vencer(*, usuario, **datos):
    """SGR-02 · Avisar pólizas próximas a vencer

    Actores: Tareas programadas; secundarios: Correo y SMS
    Fase 2
    Tablas: seguros.poliza
    Reglas en la base: seguros.v_por_vencer
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-34

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SGR-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguros.v_por_vencer
    # 4. publicar('seguros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SGR-02: por construir')


def sgr_03_registrar_enviar_aviso_siniestro(*, usuario, **datos):
    """SGR-03 · Registrar y enviar un aviso de siniestro

    Actores: Encargado de finca, Administrador; secundarios: Aseguradora
    Fase 2
    Tablas: seguros.aviso_siniestro
    Reglas en la base: seguros.validar_aviso()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-34

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SGR-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguros.validar_aviso()
    # 4. publicar('seguros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SGR-03: por construir')


def sgr_04_vigilar_indice_poliza_parametrica(*, usuario, **datos):
    """SGR-04 · Vigilar el índice de una póliza paramétrica

    Actores: Tareas programadas; secundarios: Estación meteorológica
    Fase 2 · función seguro_parametrico
    Tablas: seguros.indice_poliza, seguros.aviso_siniestro
    Reglas en la base: seguros.vigilar_indice()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-34, RQ-25

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SGR-04:
    # 1. with transaction.atomic():
    # 2. La función «seguro_parametrico» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: seguros.vigilar_indice()
    # 4. publicar('seguros.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SGR-04: por construir')
