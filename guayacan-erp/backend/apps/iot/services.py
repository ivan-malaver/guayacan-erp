"""Casos de uso del esquema iot: una función por caso de uso.

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


def iot_01_registrar_dispositivos_sensores_actuadores(*, usuario, **datos):
    """IOT-01 · Registrar dispositivos, sensores y actuadores

    Actores: Administrador; secundarios: Pasarela IoT local
    Fase 4
    Tablas: iot.dispositivo, iot.sensor, iot.actuador
    Reglas en la base: ck modo_falla
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-25, RQ-26

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: ck modo_falla
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-01: por construir')


def iot_02_recibir_lecturas_sensores(*, usuario, **datos):
    """IOT-02 · Recibir lecturas de sensores

    Actores: Pasarela IoT local
    Fase 4
    Tablas: iot.lectura
    Reglas en la base: inventario.evaluar_excursion()
    Endpoints: MQTT finca/<dispositivo>/<sensor>
    Requerimientos: RQ-25

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.evaluar_excursion()
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-02: por construir')


def iot_03_accionar_actuador_mano(*, usuario, **datos):
    """IOT-03 · Accionar un actuador a mano

    Actores: Encargado de finca; secundarios: Pasarela IoT local
    Fase 4
    Tablas: iot.comando_actuador
    Reglas en la base: formato y permisos de DRF
    Endpoints: POST /api/v1/iot/comandos/
    Requerimientos: RQ-25

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-03:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-03: por construir')


def iot_04_armar_desarmar_alarma_zonas(*, usuario, **datos):
    """IOT-04 · Armar y desarmar la alarma por zonas

    Actores: Encargado de finca, Portería; secundarios: Pasarela IoT local
    Fase 4 · función seguridad_perimetral
    Tablas: iot.zona_seguridad, iot.cambio_estado_alarma
    Reglas en la base: iot.cambiar_estado_alarma()
    Endpoints: POST /api/v1/iot/zonas-seguridad/{id}/estado/
    Requerimientos: RQ-26

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-04:
    # 1. with transaction.atomic():
    # 2. La función «seguridad_perimetral» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: iot.cambiar_estado_alarma()
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-04: por construir')


def iot_05_atender_evento_seguridad_perimetral(*, usuario, **datos):
    """IOT-05 · Atender un evento de seguridad perimetral

    Actores: Encargado de finca, Portería; secundarios: Pasarela IoT local, Correo y SMS
    Fase 4 · función seguridad_perimetral
    Tablas: iot.evento_seguridad, iot.clip_video
    Reglas en la base: solo se registra la atención
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-26

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-05:
    # 1. with transaction.atomic():
    # 2. La función «seguridad_perimetral» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: solo se registra la atención
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-05: por construir')


def iot_06_gestionar_credenciales_acceso_puertas(*, usuario, **datos):
    """IOT-06 · Gestionar credenciales de acceso a puertas

    Actores: Administrador; secundarios: Pasarela IoT local
    Fase 4
    Tablas: iot.credencial_acceso, terceros.consentimiento_datos
    Reglas en la base: biometría exige autorización expresa
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-26, RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: biometría exige autorización expresa
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-06: por construir')


def iot_07_conservar_depurar_clips_camaras(*, usuario, **datos):
    """IOT-07 · Conservar o depurar clips de cámaras

    Actores: Tareas programadas, Administrador
    Fase 4 · función camaras
    Tablas: iot.camara, iot.clip_video
    Reglas en la base: iot.depurar_clips()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-26

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-07:
    # 1. with transaction.atomic():
    # 2. La función «camaras» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: iot.depurar_clips()
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-07: por construir')


def iot_08_planear_ejecutar_mision_dron_robot(*, usuario, **datos):
    """IOT-08 · Planear y ejecutar una misión de dron o robot

    Actores: Encargado de finca, Administrador; secundarios: Pasarela IoT local
    Fase 4 · función dron_monitoreo
    Tablas: iot.mision_robot, activos.activo, seguros.poliza
    Reglas en la base: iot.validar_mision()
    Endpoints: POST /api/v1/iot/misiones-robot/{id}/aprobar/
    Requerimientos: RQ-42

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-08:
    # 1. with transaction.atomic():
    # 2. La función «dron_monitoreo» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: iot.validar_mision()
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-08: por construir')


def iot_09_cortar_cargas_bateria_baja(*, usuario, **datos):
    """IOT-09 · Cortar cargas con batería baja

    Actores: Pasarela IoT local
    Fase 4
    Tablas: iot.prioridad_carga
    Reglas en la base: iot.cargas_a_cortar()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-25, RNF-14

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para IOT-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: iot.cargas_a_cortar()
    # 4. publicar('iot.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('IOT-09: por construir')
