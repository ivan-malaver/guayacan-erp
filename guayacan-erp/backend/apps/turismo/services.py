"""Casos de uso del esquema turismo: una función por caso de uso.

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


def tur_01_gestionar_alojamientos_planes_turisticos(*, usuario, **datos):
    """TUR-01 · Gestionar alojamientos y planes turísticos

    Actores: Administrador
    Fase 3
    Tablas: turismo.alojamiento, turismo.plan_turistico, agenda.recurso
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TUR-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('turismo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TUR-01: por construir')


def tur_02_reservar_cabana_plan(*, usuario, **datos):
    """TUR-02 · Reservar una cabaña o un plan

    Actores: Cliente, Vendedor; secundarios: Guía virtual (IA)
    Fase 3
    Tablas: turismo.reserva, agenda.cita
    Reglas en la base: turismo.validar_reserva(), turismo.sincronizar_agenda()
    Endpoints: GET /api/v1/agenda/recursos/{id}/disponible/
    Requerimientos: RF-13, RF-14, RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TUR-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: turismo.validar_reserva(), turismo.sincronizar_agenda()
    # 4. publicar('turismo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TUR-02: por construir')


def tur_03_pagar_anticipadamente_reserva(*, usuario, **datos):
    """TUR-03 · Pagar anticipadamente una reserva

    Actores: Cliente; secundarios: Pasarela de pagos
    Fase 3
    Tablas: turismo.reserva, comercial.pago
    Reglas en la base: formato y permisos de DRF
    Endpoints: POST /api/v1/pagos/webhook/
    Requerimientos: RF-14, RF-21

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TUR-03:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('turismo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TUR-03: por construir')


def tur_04_hacer_check_in_check_out(*, usuario, **datos):
    """TUR-04 · Hacer check-in y check-out de huéspedes

    Actores: Portería, Vendedor; secundarios: Visitante o turista
    Fase 3
    Tablas: turismo.reserva, terceros.consentimiento_datos, personal.tarea
    Reglas en la base: turismo.sincronizar_agenda()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-16, RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TUR-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: turismo.sincronizar_agenda()
    # 4. publicar('turismo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TUR-04: por construir')


def tur_05_atender_solicitud_grupo(*, usuario, **datos):
    """TUR-05 · Atender la solicitud de un grupo

    Actores: Operador turístico o institución; secundarios: Vendedor
    Fase 3
    Tablas: turismo.reserva, turismo.plan_turistico, agenda.visita
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-15

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TUR-05:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('turismo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TUR-05: por construir')


def tur_06_bloquear_fechas_calendario(*, usuario, **datos):
    """TUR-06 · Bloquear fechas del calendario

    Actores: Administrador
    Fase 3
    Tablas: turismo.bloqueo_calendario, agenda.cita
    Reglas en la base: turismo.sincronizar_bloqueo()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para TUR-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: turismo.sincronizar_bloqueo()
    # 4. publicar('turismo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('TUR-06: por construir')
