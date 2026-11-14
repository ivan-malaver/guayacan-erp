"""Casos de uso del esquema produccion: una función por caso de uso.

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


def pro_01_registrar_ingreso_lote_animales(*, usuario, **datos):
    """PRO-01 · Registrar el ingreso de un lote de animales

    Actores: Encargado de finca, Operario de campo
    Fase 1
    Tablas: produccion.lote_animal, produccion.animal, produccion.especie
    Reglas en la base: cumplimiento.v_granja_biosegura
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-07

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: cumplimiento.v_granja_biosegura
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-01: por construir')


def pro_02_registrar_postura_diaria_clasificar_huevo(*, usuario, **datos):
    """PRO-02 · Registrar la postura diaria y clasificar el huevo

    Actores: Operario de campo; secundarios: Pasarela IoT local
    Fase 1
    Tablas: produccion.registro_postura, produccion.clasificacion_postura, produccion.categoria_huevo
    Reglas en la base: produccion.validar_clasificacion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-06, RF-18

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: produccion.validar_clasificacion()
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-02: por construir')


def pro_03_registrar_alimentacion_pesajes_eventos_sanitarios(*, usuario, **datos):
    """PRO-03 · Registrar alimentación, pesajes y eventos sanitarios

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.registro_alimentacion, produccion.registro_pesaje, produccion.evento_sanitario
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-07, RF-18

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-03:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-03: por construir')


def pro_04_registrar_eventos_reproductivos_ovinos_caprinos(*, usuario, **datos):
    """PRO-04 · Registrar eventos reproductivos de ovinos y caprinos

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.evento_reproductivo, produccion.animal
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-07

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-04:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-04: por construir')


def pro_05_registrar_siembra_labores_culturales(*, usuario, **datos):
    """PRO-05 · Registrar una siembra y sus labores culturales

    Actores: Operario de campo, Encargado de finca
    Fase 1
    Tablas: produccion.siembra, produccion.labor_cultural, produccion.cultivo
    Reglas en la base: ck labor por robot exige misión
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-04, RF-05, RF-07

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: ck labor por robot exige misión
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-05: por construir')


def pro_06_registrar_cosecha_destino(*, usuario, **datos):
    """PRO-06 · Registrar una cosecha y su destino

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.cosecha, inventario.lote_inventario
    Reglas en la base: inventario.entrada_inicial(), comercial.registrar_huella()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-06, RF-18

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.entrada_inicial(), comercial.registrar_huella()
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-06: por construir')


def pro_07_registrar_analisis_suelo_recomendacion(*, usuario, **datos):
    """PRO-07 · Registrar un análisis de suelo y su recomendación

    Actores: Encargado de finca; secundarios: Agrónomo (IA)
    Fase 1
    Tablas: produccion.analisis_suelo
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-04

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-07:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-07: por construir')


def pro_08_registrar_bioseguridad_e_inocuidad(*, usuario, **datos):
    """PRO-08 · Registrar bioseguridad e inocuidad

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.registro_bioseguridad
    Reglas en la base: cumplimiento.evaluar_expediente()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-33

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-08:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: cumplimiento.evaluar_expediente()
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-08: por construir')


def pro_09_producir_abono_lombricultivo_compostera(*, usuario, **datos):
    """PRO-09 · Producir abono en lombricultivo o compostera

    Actores: Operario de campo
    Fase 1
    Tablas: produccion.produccion_abono, inventario.lote_inventario
    Reglas en la base: inventario.entrada_inicial()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-08, RNF-14

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: inventario.entrada_inicial()
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-09: por construir')


def pro_10_medir_calidad_agua_estanques(*, usuario, **datos):
    """PRO-10 · Medir la calidad del agua de los estanques

    Actores: Operario de campo; secundarios: Pasarela IoT local
    Fase 1
    Tablas: produccion.calidad_agua_estanque
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-18

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRO-10:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('produccion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRO-10: por construir')
