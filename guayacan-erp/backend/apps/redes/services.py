"""Casos de uso del esquema redes: una función por caso de uso.

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


def red_01_atender_mensaje_cliente_canal(*, usuario, **datos):
    """RED-01 · Atender el mensaje de un cliente por un canal

    Actores: Cliente; secundarios: Canales de mensajería, Orquestador (IA), Asesor virtual (IA), Vendedor personalizado (IA)
    Fase 1
    Tablas: redes.cuenta_red, ia.regla_conversacion
    Reglas en la base: herramientas MCP de solo lectura y borrador
    Endpoints: POST /canales/whatsapp/webhook
    Requerimientos: RQ-24, RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RED-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: herramientas MCP de solo lectura y borrador
    # 4. publicar('redes.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RED-01: por construir')


def red_02_escalar_conversacion_persona(*, usuario, **datos):
    """RED-02 · Escalar una conversación a una persona

    Actores: Vendedor; secundarios: Orquestador (IA)
    Fase 1
    Tablas: ia.escalamiento
    Reglas en la base: ventana del canal
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-24

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RED-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: ventana del canal
    # 4. publicar('redes.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RED-02: por construir')


def red_03_enviar_mensaje_saliente_dentro_reglas(*, usuario, **datos):
    """RED-03 · Enviar un mensaje saliente dentro de las reglas del canal

    Actores: Vendedor; secundarios: Canales de mensajería, Asesor virtual (IA)
    Fase 1
    Tablas: redes.mensaje_saliente, redes.plantilla_mensaje, redes.politica_canal
    Reglas en la base: redes.verificar_envio()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-20, RQ-24, RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RED-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: redes.verificar_envio()
    # 4. publicar('redes.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RED-03: por construir')


def red_04_proponer_aprobar_publicacion(*, usuario, **datos):
    """RED-04 · Proponer y aprobar una publicación

    Actores: Administrador; secundarios: Gestor de redes (IA), Canales de mensajería
    Fase 2
    Tablas: redes.publicacion
    Reglas en la base: solo una persona aprueba contenido
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-24, RQ-23

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RED-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: solo una persona aprueba contenido
    # 4. publicar('redes.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RED-04: por construir')


def red_05_producir_pieza_audiovisual_autorizacion_imagen(*, usuario, **datos):
    """RED-05 · Producir una pieza audiovisual con autorización de imagen

    Actores: Administrador; secundarios: Gestor de redes (IA)
    Fase 2 · función videos_promocionales
    Tablas: redes.pieza_audiovisual, redes.pieza_persona
    Reglas en la base: redes.validar_pieza()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-24, RNF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RED-05:
    # 1. with transaction.atomic():
    # 2. La función «videos_promocionales» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: redes.validar_pieza()
    # 4. publicar('redes.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RED-05: por construir')


def red_06_mantener_plantillas_politicas_canal(*, usuario, **datos):
    """RED-06 · Mantener plantillas y políticas de canal

    Actores: Administrador; secundarios: Canales de mensajería
    Fase 1
    Tablas: redes.plantilla_mensaje, redes.politica_canal
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-24

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para RED-06:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('redes.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('RED-06: por construir')
