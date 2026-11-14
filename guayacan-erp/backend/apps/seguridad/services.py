"""Casos de uso del esquema seguridad: una función por caso de uso.

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


def seg_01_iniciar_sesion_doble_factor(*, usuario, **datos):
    """SEG-01 · Iniciar sesión con doble factor

    Actores: Usuario autenticado
    Fase 1
    Tablas: seguridad.intento_acceso, seguridad.sesion_usuario, seguridad.factor_autenticacion
    Reglas en la base: seguridad.registrar_intento(), seguridad.requiere_doble_factor(), seguridad.validar_sesion()
    Endpoints: POST /api/v1/auth/token/; POST /api/v1/auth/doble-factor/verificar/
    Requerimientos: RF-01, RF-03, RQ-35

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SEG-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguridad.registrar_intento(), seguridad.requiere_doble_factor(), seguridad.validar_sesion()
    # 4. publicar('seguridad.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SEG-01: por construir')


def seg_02_inscribir_segundo_factor_recuperar_contrasena(*, usuario, **datos):
    """SEG-02 · Inscribir el segundo factor y recuperar la contraseña

    Actores: Usuario autenticado; secundarios: Correo y SMS
    Fase 1
    Tablas: seguridad.factor_autenticacion
    Reglas en la base: formato y permisos de DRF
    Endpoints: POST /api/v1/auth/doble-factor/inscribir/; POST /api/v1/auth/recuperar/
    Requerimientos: RF-03, RQ-35

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SEG-02:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('seguridad.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SEG-02: por construir')


def seg_03_detectar_bloquear_ataques_acceso(*, usuario, **datos):
    """SEG-03 · Detectar y bloquear ataques de acceso

    Actores: Tareas programadas; secundarios: Vigía de seguridad (IA)
    Fase 1
    Tablas: seguridad.regla_deteccion, seguridad.bloqueo, seguridad.senuelo, seguridad.alerta_seguridad
    Reglas en la base: seguridad.registrar_intento(), seguridad.vigilar_exportaciones(), seguridad.ip_bloqueada(), seguridad.cuenta_bloqueada()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-35

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SEG-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguridad.registrar_intento(), seguridad.vigilar_exportaciones(), seguridad.ip_bloqueada()
    # 4. publicar('seguridad.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SEG-03: por construir')


def seg_04_atender_alerta_incidente_seguridad(*, usuario, **datos):
    """SEG-04 · Atender una alerta o un incidente de seguridad

    Actores: Administrador; secundarios: Vigía de seguridad (IA)
    Fase 1
    Tablas: seguridad.alerta_seguridad, seguridad.incidente
    Reglas en la base: seguridad.proteger_alerta()
    Endpoints: GET /api/v1/seguridad/tablero/
    Requerimientos: RQ-35, RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SEG-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguridad.proteger_alerta()
    # 4. publicar('seguridad.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SEG-04: por construir')


def seg_05_revocar_sesiones_levantar_bloqueos(*, usuario, **datos):
    """SEG-05 · Revocar sesiones y levantar bloqueos

    Actores: Administrador
    Fase 1
    Tablas: seguridad.sesion_usuario, seguridad.bloqueo
    Reglas en la base: seguridad.revocar_sesiones()
    Endpoints: POST /api/v1/seguridad/sesiones/{id}/revocar/; POST /api/v1/seguridad/bloqueos/{id}/levantar/
    Requerimientos: RQ-35

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SEG-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguridad.revocar_sesiones()
    # 4. publicar('seguridad.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SEG-05: por construir')


def seg_06_registrar_corrida_pruebas(*, usuario, **datos):
    """SEG-06 · Registrar una corrida de pruebas

    Actores: Integración continua
    Fase 1
    Tablas: seguridad.ejecucion_prueba
    Reglas en la base: solo inserción
    Endpoints: POST /api/v1/seguridad/ejecuciones-prueba/
    Requerimientos: RNF-11, RQ-35

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SEG-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: solo inserción
    # 4. publicar('seguridad.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SEG-06: por construir')


def seg_07_verificar_copias_seguridad_restauraciones(*, usuario, **datos):
    """SEG-07 · Verificar copias de seguridad y restauraciones

    Actores: Tareas programadas, Administrador
    Fase 1
    Tablas: seguridad.copia_seguridad
    Reglas en la base: seguridad.revisar_copias()
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-06, RNF-05

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para SEG-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguridad.revisar_copias()
    # 4. publicar('seguridad.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('SEG-07: por construir')
