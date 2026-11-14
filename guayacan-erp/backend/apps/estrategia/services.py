"""Casos de uso del esquema estrategia: una función por caso de uso.

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


def est_01_mantener_lineas_negocio_matriz_dofa(*, usuario, **datos):
    """EST-01 · Mantener las líneas de negocio y la matriz DOFA

    Actores: Familia; secundarios: Estratega (IA)
    Fase 2
    Tablas: estrategia.linea_negocio, estrategia.factor_dofa
    Reglas en la base: estrategia.v_matriz_lineas
    Endpoints: GET /api/v1/estrategia/lineas/
    Requerimientos: RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: estrategia.v_matriz_lineas
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-01: por construir')


def est_02_registrar_estudio_mercado(*, usuario, **datos):
    """EST-02 · Registrar un estudio de mercado

    Actores: Familia; secundarios: Estratega (IA), Fuentes de mercado
    Fase 2
    Tablas: estrategia.estudio_mercado
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-02:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-02: por construir')


def est_03_proponer_iniciativa_crecimiento(*, usuario, **datos):
    """EST-03 · Proponer una iniciativa de crecimiento

    Actores: Familia; secundarios: Estratega (IA)
    Fase 2
    Tablas: estrategia.iniciativa
    Reglas en la base: estrategia.validar_iniciativa()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-37, RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: estrategia.validar_iniciativa()
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-03: por construir')


def est_04_evaluar_financieramente_iniciativa(*, usuario, **datos):
    """EST-04 · Evaluar financieramente una iniciativa

    Actores: Familia; secundarios: Estratega (IA)
    Fase 2
    Tablas: estrategia.evaluacion_proyecto, estrategia.flujo_proyecto
    Reglas en la base: estrategia.evaluar_proyecto(), estrategia.vpn(), estrategia.tir()
    Endpoints: POST /api/v1/estrategia/evaluaciones-proyecto/{id}/calcular/
    Requerimientos: RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: estrategia.evaluar_proyecto(), estrategia.vpn(), estrategia.tir()
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-04: por construir')


def est_05_aprobar_iniciativa(*, usuario, **datos):
    """EST-05 · Aprobar una iniciativa

    Actores: Familia
    Fase 2
    Tablas: estrategia.iniciativa
    Reglas en la base: estrategia.validar_iniciativa()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: estrategia.validar_iniciativa()
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-05: por construir')


def est_06_reinvertir_utilidades_linea(*, usuario, **datos):
    """EST-06 · Reinvertir utilidades de una línea

    Actores: Familia
    Fase 2
    Tablas: estrategia.reinversion
    Reglas en la base: estrategia.validar_reinversion(), estrategia.utilidad_linea()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: estrategia.validar_reinversion(), estrategia.utilidad_linea()
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-06: por construir')


def est_07_seguir_retorno_iniciativas(*, usuario, **datos):
    """EST-07 · Seguir el retorno de las iniciativas

    Actores: Familia; secundarios: Analista de negocio (IA)
    Fase 2
    Tablas: estrategia.seguimiento_iniciativa
    Reglas en la base: estrategia.v_retorno_iniciativas
    Endpoints: GET /api/v1/estrategia/retorno/
    Requerimientos: RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: estrategia.v_retorno_iniciativas
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-07: por construir')


def est_08_definir_objetivos_metas_cuadro_mando(*, usuario, **datos):
    """EST-08 · Definir objetivos y metas del cuadro de mando

    Actores: Familia
    Fase 2
    Tablas: estrategia.objetivo
    Reglas en la base: semáforo de finanzas.calcular_indicadores()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-37, RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para EST-08:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: semáforo de finanzas.calcular_indicadores()
    # 4. publicar('estrategia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('EST-08: por construir')
