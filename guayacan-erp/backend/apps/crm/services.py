"""Casos de uso del esquema crm: una función por caso de uso.

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


def crm_01_capturar_posible_cliente_autorizacion(*, usuario, **datos):
    """CRM-01 · Capturar un posible cliente con autorización

    Actores: Posible cliente, Vendedor
    Fase 2
    Tablas: crm.formulario_captura, crm.prospecto, terceros.consentimiento_datos
    Reglas en la base: crm.validar_prospecto()
    Endpoints: POST /api/v1/crm/captura/{formulario}/
    Requerimientos: RQ-36, RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CRM-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: crm.validar_prospecto()
    # 4. publicar('crm.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CRM-01: por construir')


def crm_02_gestionar_segmentos_campanas(*, usuario, **datos):
    """CRM-02 · Gestionar segmentos y campañas

    Actores: Vendedor, Administrador
    Fase 2
    Tablas: crm.segmento, crm.campana
    Reglas en la base: crm.v_campanas
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-36

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CRM-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: crm.v_campanas
    # 4. publicar('crm.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CRM-02: por construir')


def crm_03_registrar_interacciones_avanzar_embudo(*, usuario, **datos):
    """CRM-03 · Registrar interacciones y avanzar el embudo

    Actores: Vendedor; secundarios: Canales de mensajería
    Fase 2
    Tablas: crm.interaccion, crm.prospecto, crm.contacto_empresa
    Reglas en la base: crm.validar_interaccion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-36

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CRM-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: crm.validar_interaccion()
    # 4. publicar('crm.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CRM-03: por construir')


def crm_04_calificar_prospectos(*, usuario, **datos):
    """CRM-04 · Calificar los prospectos

    Actores: Tareas programadas, Vendedor
    Fase 2
    Tablas: crm.prospecto
    Reglas en la base: crm.calificar()
    Endpoints: POST /api/v1/crm/prospectos/{id}/calificar/
    Requerimientos: RQ-36

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CRM-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: crm.calificar()
    # 4. publicar('crm.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CRM-04: por construir')


def crm_05_convertir_prospecto_cliente(*, usuario, **datos):
    """CRM-05 · Convertir un prospecto en cliente

    Actores: Vendedor
    Fase 2
    Tablas: crm.prospecto, terceros.tercero, terceros.cliente
    Reglas en la base: crm.convertir_prospecto()
    Endpoints: POST /api/v1/crm/prospectos/{id}/convertir/
    Requerimientos: RQ-36

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CRM-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: crm.convertir_prospecto()
    # 4. publicar('crm.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CRM-05: por construir')


def crm_06_gestionar_oportunidades_proyectar_ventas(*, usuario, **datos):
    """CRM-06 · Gestionar oportunidades y proyectar ventas

    Actores: Vendedor, Familia
    Fase 2
    Tablas: crm.oportunidad
    Reglas en la base: crm.v_embudo, crm.v_proyeccion_ventas
    Endpoints: GET /api/v1/crm/embudo/
    Requerimientos: RQ-36, RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para CRM-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: crm.v_embudo, crm.v_proyeccion_ventas
    # 4. publicar('crm.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('CRM-06: por construir')
