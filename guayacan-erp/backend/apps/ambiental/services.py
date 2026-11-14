"""Casos de uso del esquema ambiental: una función por caso de uso.

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


def amb_01_registrar_mediciones_ambientales(*, usuario, **datos):
    """AMB-01 · Registrar mediciones ambientales

    Actores: Operario de campo; secundarios: Pasarela IoT local
    Fase 2
    Tablas: ambiental.registro_ambiental
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-19, RNF-14, RQ-44

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AMB-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('ambiental.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AMB-01: por construir')


def amb_02_mantener_factores_emision_fuente(*, usuario, **datos):
    """AMB-02 · Mantener factores de emisión con su fuente

    Actores: Administrador
    Fase 2
    Tablas: ambiental.factor_emision
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-44

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AMB-02:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('ambiental.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AMB-02: por construir')


def amb_03_consultar_indicadores_ambientales_co_estimado(*, usuario, **datos):
    """AMB-03 · Consultar indicadores ambientales y CO₂ estimado

    Actores: Familia, Administrador; secundarios: Gestor de redes (IA)
    Fase 2
    Tablas: ambiental.registro_ambiental
    Reglas en la base: ambiental.v_indicadores
    Endpoints: GET /api/v1/ambiental/indicadores/?mes=
    Requerimientos: RF-19, RNF-13, RQ-44

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AMB-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: ambiental.v_indicadores
    # 4. publicar('ambiental.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AMB-03: por construir')
