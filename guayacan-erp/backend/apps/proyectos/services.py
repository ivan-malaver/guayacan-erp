"""Casos de uso del esquema proyectos: una función por caso de uso.

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


def pry_01_constituir_proyecto(*, usuario, **datos):
    """PRY-01 · Constituir un proyecto

    Actores: Director de proyecto; secundarios: Asistente de proyectos (IA)
    Fase 2
    Tablas: proyectos.proyecto, documental.documento
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-01: por construir')


def pry_02_aprobar_proyecto(*, usuario, **datos):
    """PRY-02 · Aprobar un proyecto

    Actores: Patrocinador
    Fase 2
    Tablas: proyectos.proyecto, proyectos.linea_base
    Reglas en la base: proyectos.validar_proyecto(), proyectos.linea_base_inicial()
    Endpoints: POST /api/v1/proyectos/proyectos/{id}/aprobar/
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: proyectos.validar_proyecto(), proyectos.linea_base_inicial()
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-02: por construir')


def pry_03_planificar_alcance_cronograma(*, usuario, **datos):
    """PRY-03 · Planificar el alcance y el cronograma

    Actores: Director de proyecto; secundarios: Asistente de proyectos (IA)
    Fase 2
    Tablas: proyectos.elemento_edt, proyectos.actividad, proyectos.dependencia
    Reglas en la base: proyectos.validar_dependencia()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: proyectos.validar_dependencia()
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-03: por construir')


def pry_04_calcular_ruta_critica(*, usuario, **datos):
    """PRY-04 · Calcular la ruta crítica

    Actores: Director de proyecto
    Fase 2
    Tablas: proyectos.actividad
    Reglas en la base: proyectos.calcular_ruta_critica()
    Endpoints: POST /api/v1/proyectos/proyectos/{id}/ruta-critica/
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: proyectos.calcular_ruta_critica()
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-04: por construir')


def pry_05_gestionar_interesados_riesgos(*, usuario, **datos):
    """PRY-05 · Gestionar interesados y riesgos

    Actores: Director de proyecto; secundarios: Asistente de proyectos (IA)
    Fase 2
    Tablas: proyectos.interesado, proyectos.riesgo, proyectos.registro
    Reglas en la base: proyectos.clasificar_interesado()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: proyectos.clasificar_interesado()
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-05: por construir')


def pry_06_registrar_avance_medir_valor_ganado(*, usuario, **datos):
    """PRY-06 · Registrar avance y medir el valor ganado

    Actores: Director de proyecto; secundarios: Tareas programadas
    Fase 2
    Tablas: proyectos.actividad, proyectos.medicion_valor_ganado
    Reglas en la base: proyectos.avance_actividad(), proyectos.calcular_valor_ganado()
    Endpoints: POST /api/v1/proyectos/proyectos/{id}/valor-ganado/?corte=; GET /api/v1/proyectos/tablero/
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: proyectos.avance_actividad(), proyectos.calcular_valor_ganado()
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-06: por construir')


def pry_07_solicitar_decidir_cambio(*, usuario, **datos):
    """PRY-07 · Solicitar y decidir un cambio

    Actores: Director de proyecto, Patrocinador
    Fase 2
    Tablas: proyectos.solicitud_cambio, proyectos.linea_base
    Reglas en la base: proyectos.decidir_cambio(), proyectos.nueva_linea_base()
    Endpoints: POST /api/v1/proyectos/solicitudes-cambio/{id}/decidir/
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: proyectos.decidir_cambio(), proyectos.nueva_linea_base()
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-07: por construir')


def pry_08_aceptar_entregables_cerrar_proyecto(*, usuario, **datos):
    """PRY-08 · Aceptar entregables y cerrar el proyecto

    Actores: Patrocinador, Director de proyecto
    Fase 2
    Tablas: proyectos.elemento_edt, proyectos.registro, proyectos.proyecto
    Reglas en la base: proyectos.aceptar_entregable(), proyectos.validar_proyecto()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-08:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: proyectos.aceptar_entregable(), proyectos.validar_proyecto()
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-08: por construir')


def pry_09_planear_cerrar_iteracion(*, usuario, **datos):
    """PRY-09 · Planear y cerrar una iteración

    Actores: Director de proyecto
    Fase 2
    Tablas: proyectos.iteracion, proyectos.actividad
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-41

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para PRY-09:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('proyectos.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('PRY-09: por construir')
