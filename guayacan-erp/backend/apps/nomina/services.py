"""Casos de uso del esquema nomina: una función por caso de uso.

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


def nom_01_configurar_conceptos_tarifas_nomina(*, usuario, **datos):
    """NOM-01 · Configurar conceptos y tarifas de nómina

    Actores: Contador
    Fase 2
    Tablas: nomina.concepto_nomina, nucleo.parametro
    Reglas en la base: nomina.concepto()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NOM-01:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nomina.concepto()
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-01: por construir')


def nom_02_preparar_prenomina(*, usuario, **datos):
    """NOM-02 · Preparar la prenómina

    Actores: Contador, Encargado de finca
    Fase 2
    Tablas: nomina.periodo_nomina, nomina.novedad
    Reglas en la base: nomina.preparar_prenomina(), nomina.validar_novedad()
    Endpoints: POST /api/v1/nomina/periodos/{id}/prenomina/
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # TODO(Nómina): nomina.preparar_prenomina() solo paga jornal y destajo de tareas con empleado_id; una tarea de
    # cuadrilla aprobada no le paga a nadie. Debe pagarle a cada miembro vigente ese día (personal.cuadrilla_miembro).
    # TODO(Nómina): aprobar jornadas (POST /api/v1/personal/jornadas/{id}/aprobar/, rotulada PER-06)
    # Por construir. Pasos sugeridos para NOM-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nomina.preparar_prenomina(), nomina.validar_novedad()
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-02: por construir')


def nom_03_registrar_novedades_manuales(*, usuario, **datos):
    """NOM-03 · Registrar novedades manuales

    Actores: Contador
    Fase 2
    Tablas: nomina.novedad
    Reglas en la base: nomina.validar_novedad(), nomina.proteger_detalle_periodo()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NOM-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nomina.validar_novedad(), nomina.proteger_detalle_periodo()
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-03: por construir')


def nom_04_liquidar_nomina(*, usuario, **datos):
    """NOM-04 · Liquidar la nómina

    Actores: Contador
    Fase 2
    Tablas: nomina.liquidacion, nomina.liquidacion_detalle, nomina.provision_prestacion
    Reglas en la base: nomina.liquidar()
    Endpoints: POST /api/v1/nomina/periodos/{id}/liquidar/
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NOM-04:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nomina.liquidar()
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-04: por construir')


def nom_05_cerrar_periodo_nomina(*, usuario, **datos):
    """NOM-05 · Cerrar el periodo de nómina

    Actores: Familia, Contador
    Fase 2
    Tablas: nomina.periodo_nomina, finanzas.comprobante
    Reglas en la base: nomina.proteger_periodo()
    Endpoints: POST /api/v1/nomina/periodos/{id}/cerrar/
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NOM-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nomina.proteger_periodo()
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-05: por construir')


def nom_06_preparar_aprobar_pagos_nomina(*, usuario, **datos):
    """NOM-06 · Preparar y aprobar los pagos de nómina

    Actores: Contador, Familia
    Fase 2
    Tablas: nomina.pago_nomina
    Reglas en la base: nomina.validar_pago(), nomina.marcar_pagada()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NOM-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: nomina.validar_pago(), nomina.marcar_pagada()
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-06: por construir')


def nom_07_generar_pila_exportar_contador(*, usuario, **datos):
    """NOM-07 · Generar la PILA y exportar al contador

    Actores: Contador
    Fase 2
    Tablas: nomina.planilla_pila, nomina.exportacion_nomina
    Reglas en la base: formato y permisos de DRF
    Endpoints: GET /api/v1/nomina/periodos/{id}/pila/; GET /api/v1/nomina/periodos/{id}/exportar/?formato=
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NOM-07:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-07: por construir')


def nom_08_transmitir_nomina_electronica(*, usuario, **datos):
    """NOM-08 · Transmitir la nómina electrónica

    Actores: Contador; secundarios: DIAN
    Fase 2 · función nomina_electronica
    Tablas: nomina.documento_nomina_electronica
    Reglas en la base: nomina.validar_documento_electronico()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-29

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para NOM-08:
    # 1. with transaction.atomic():
    # 2. La función «nomina_electronica» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: nomina.validar_documento_electronico()
    # 4. publicar('nomina.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('NOM-08: por construir')
