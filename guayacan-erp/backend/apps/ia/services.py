"""Casos de uso del esquema ia: una función por caso de uso.

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


def ia_01_configurar_agente_herramientas(*, usuario, **datos):
    """IA-01 · Configurar un agente y sus herramientas

    Actores: Administrador
    Fase 1
    Tablas: ia.agente, ia.herramienta, ia.agente_herramienta
    Reglas en la base: mínimo privilegio
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: mínimo privilegio
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-01: por construir')


def ia_02_resolver_bandeja_aprobaciones(*, usuario, **datos):
    """IA-02 · Resolver la bandeja de aprobaciones

    Actores: Administrador; secundarios: Analista de mercados (IA), Gestor de redes (IA)
    Fase 1
    Tablas: ia.solicitud_aprobacion
    Reglas en la base: nucleo.exigir_persona()
    Endpoints: POST /api/v1/ia/solicitudes-aprobacion/{id}/aprobar/
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nucleo.exigir_persona()
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-02: por construir')


def ia_03_alimentar_base_conocimiento(*, usuario, **datos):
    """IA-03 · Alimentar la base de conocimiento

    Actores: Administrador
    Fase 1
    Tablas: ia.documento_conocimiento, ia.fragmento_conocimiento
    Reglas en la base: formato y permisos de DRF
    Endpoints: POST /api/v1/ia/documentos-conocimiento/{id}/indexar/; POST /api/v1/ia/buscar/
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-03:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-03: por construir')


def ia_04_recibir_seguir_recomendaciones_mejora(*, usuario, **datos):
    """IA-04 · Recibir y seguir recomendaciones de mejora

    Actores: Administrador, Familia; secundarios: Analista de negocio (IA)
    Fase 1
    Tablas: ia.recomendacion
    Reglas en la base: ciclo PHVA semanal
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: ciclo PHVA semanal
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-04: por construir')


def ia_05_evaluar_respuestas_agentes(*, usuario, **datos):
    """IA-05 · Evaluar las respuestas de los agentes

    Actores: Cliente, Administrador
    Fase 1
    Tablas: ia.evaluacion_respuesta
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-05:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-05: por construir')


def ia_06_controlar_consumo_costo_ia(*, usuario, **datos):
    """IA-06 · Controlar el consumo y el costo de la IA

    Actores: Administrador; secundarios: Tareas programadas
    Fase 1
    Tablas: ia.consumo_ia, ia.agente
    Reglas en la base: límite de costo diario por agente
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23, RNF-12

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: límite de costo diario por agente
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-06: por construir')


def ia_07_pronosticar_demanda(*, usuario, **datos):
    """IA-07 · Pronosticar la demanda

    Actores: Tareas programadas; secundarios: Vendedor
    Fase 3 · función pronostico_demanda
    Tablas: ia.modelo_pronostico, ia.pronostico_demanda
    Reglas en la base: mínimo 12 meses de ventas
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-07:
    # 1. with transaction.atomic():
    # 2. La función «pronostico_demanda» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: mínimo 12 meses de ventas
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-07: por construir')


def ia_08_diagnosticar_foto_campo(*, usuario, **datos):
    """IA-08 · Diagnosticar una foto de campo

    Actores: Operario de campo; secundarios: Agrónomo (IA), Encargado de finca
    Fase 2 · función diagnostico_imagen
    Tablas: ia.diagnostico_imagen
    Reglas en la base: ia.validar_diagnostico()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-08:
    # 1. with transaction.atomic():
    # 2. La función «diagnostico_imagen» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: ia.validar_diagnostico()
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-08: por construir')


def ia_09_simular_escenario_registrar_decision(*, usuario, **datos):
    """IA-09 · Simular un escenario y registrar la decisión

    Actores: Familia; secundarios: Analista de negocio (IA), Estratega (IA)
    Fase 2
    Tablas: ia.escenario, ia.decision
    Reglas en la base: ia.validar_decision()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-23, RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IA-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: ia.validar_decision()
    # 4. publicar('ia.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IA-09: por construir')
