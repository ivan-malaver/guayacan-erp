"""Casos de uso del esquema nucleo: una función por caso de uso.

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


def nuc_01_configurar_finca_zonas_mapa(*, usuario, **datos):
    """NUC-01 · Configurar la finca, sus zonas y el mapa

    Actores: Administrador
    Fase 1
    Tablas: nucleo.predio, nucleo.zona
    Reglas en la base: nucleo.predio_actual()
    Endpoints: GET /api/v1/nucleo/zonas/?formato=geojson
    Requerimientos: RF-04, RF-22, RNF-01

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nucleo.predio_actual()
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-01: por construir')


def nuc_02_gestionar_usuarios_roles_permisos(*, usuario, **datos):
    """NUC-02 · Gestionar usuarios, roles y permisos

    Actores: Administrador
    Fase 1
    Tablas: nucleo.usuario, nucleo.rol, nucleo.permiso, nucleo.usuario_rol, nucleo.rol_permiso
    Reglas en la base: seguridad.vigilar_privilegios(), nucleo.tiene_permiso()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-01, RF-02

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: seguridad.vigilar_privilegios(), nucleo.tiene_permiso()
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-02: por construir')


def nuc_03_administrar_parametros_vigencia(*, usuario, **datos):
    """NUC-03 · Administrar parámetros con vigencia

    Actores: Administrador, Contador
    Fase 1
    Tablas: nucleo.parametro
    Reglas en la base: nucleo.parametro_valor(), nucleo.parametro_texto()
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-01

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nucleo.parametro_valor(), nucleo.parametro_texto()
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-03: por construir')


def nuc_04_encender_apagar_funcion_finca(*, usuario, **datos):
    """NUC-04 · Encender o apagar una función de la finca

    Actores: Administrador
    Fase 1
    Tablas: nucleo.funcionalidad
    Reglas en la base: nucleo.exigir_funcion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-01

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nucleo.exigir_funcion()
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-04: por construir')


def nuc_05_sincronizar_registros_capturados_sin_conexion(*, usuario, **datos):
    """NUC-05 · Sincronizar registros capturados sin conexión

    Actores: Operario de campo, Vendedor
    Fase 1
    Tablas: nucleo.sincronizacion, nucleo.dispositivo_captura
    Reglas en la base: ON CONFLICT (predio_id, id_cliente) DO NOTHING
    Endpoints: POST /api/v1/sincronizacion/lote/
    Requerimientos: RNF-03, RF-12

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: ON CONFLICT (predio_id, id_cliente) DO NOTHING
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-05: por construir')


def nuc_06_consultar_auditoria_cambios(*, usuario, **datos):
    """NUC-06 · Consultar la auditoría de cambios

    Actores: Administrador, Contador, Auditor externo
    Fase 1
    Tablas: nucleo.auditoria
    Reglas en la base: nucleo.auditar()
    Endpoints: GET /api/v1/nucleo/auditoria/?tabla=&registro=
    Requerimientos: RNF-04, RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nucleo.auditar()
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-06: por construir')


def nuc_07_registrar_nota_voz_campo_confirmarla(*, usuario, **datos):
    """NUC-07 · Registrar una nota de voz en campo y confirmarla

    Actores: Operario de campo; secundarios: Orquestador (IA)
    Fase 2 · función notas_voz
    Tablas: nucleo.nota_voz
    Reglas en la base: formato y permisos de DRF
    Endpoints: POST /api/v1/nucleo/notas-voz/{id}/confirmar/
    Requerimientos: RNF-03, RNF-07

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-07:
    # 1. with transaction.atomic():
    # 2. La función «notas_voz» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-07: por construir')


def nuc_08_practicar_finca_aprendizaje(*, usuario, **datos):
    """NUC-08 · Practicar en la finca de aprendizaje

    Actores: Estudiante, Instructor
    Fase 1 · función modo_aprendiz
    Tablas: nucleo.predio, nucleo.funcionalidad
    Reglas en la base: nucleo.predios_del_usuario()
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-11

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-08:
    # 1. with transaction.atomic():
    # 2. La función «modo_aprendiz» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: nucleo.predios_del_usuario()
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-08: por construir')


def nuc_09_publicar_eventos_integracion(*, usuario, **datos):
    """NUC-09 · Publicar los eventos de integración

    Actores: Tareas programadas; secundarios: Correo y SMS
    Fase 1
    Tablas: nucleo.evento_salida
    Reglas en la base: patrón outbox
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-20

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: patrón outbox
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-09: por construir')


def nuc_10_administrar_llaves_api_b2b_webhooks(*, usuario, **datos):
    """NUC-10 · Administrar llaves de API B2B y webhooks

    Actores: Administrador; secundarios: Sistema del cliente B2B
    Fase 3 · función api_b2b
    Tablas: nucleo.llave_api, nucleo.webhook_suscripcion, nucleo.webhook_entrega
    Reglas en la base: nucleo.validar_llave_api(), nucleo.autenticar_llave_api(), nucleo.validar_webhook()
    Endpoints: GET /api/b2b/v1/catalogo/; POST /api/b2b/v1/pedidos/
    Requerimientos: RQ-43

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NUC-10:
    # 1. with transaction.atomic():
    # 2. La función «api_b2b» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: nucleo.validar_llave_api(), nucleo.autenticar_llave_api(), nucleo.validar_webhook()
    # 4. publicar('nucleo.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NUC-10: por construir')
