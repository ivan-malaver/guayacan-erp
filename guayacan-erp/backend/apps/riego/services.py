"""Casos de uso del esquema riego: una función por caso de uso.

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


def rie_01_configurar_fuentes_tanques_sistemas_valvulas(*, usuario, **datos):
    """RIE-01 · Configurar fuentes, tanques, sistemas y válvulas

    Actores: Encargado de finca
    Fase 1
    Tablas: riego.fuente_agua, riego.tanque, riego.sistema_riego, riego.valvula
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-25

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RIE-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('riego.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RIE-01: por construir')


def rie_02_registrar_riego_manual(*, usuario, **datos):
    """RIE-02 · Registrar un riego manual

    Actores: Operario de campo
    Fase 1
    Tablas: riego.evento_riego
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-25, RF-19

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RIE-02:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('riego.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RIE-02: por construir')


def rie_03_regar_automaticamente_reglas(*, usuario, **datos):
    """RIE-03 · Regar automáticamente por reglas

    Actores: Pasarela IoT local; secundarios: Estación meteorológica, Encargado de finca
    Fase 4 · función riego_automatico
    Tablas: iot.regla_automatizacion, iot.comando_actuador, riego.evento_riego
    Reglas en la base: regla determinista en la pasarela
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-25

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RIE-03:
    # 1. with transaction.atomic():
    # 2. La función «riego_automatico» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: regla determinista en la pasarela
    # 4. publicar('riego.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RIE-03: por construir')
