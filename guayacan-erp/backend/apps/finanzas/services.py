"""Casos de uso del esquema finanzas: una función por caso de uso.

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


def fin_01_configurar_plan_cuentas_centros_costo(*, usuario, **datos):
    """FIN-01 · Configurar el plan de cuentas y los centros de costo

    Actores: Contador
    Fase 1
    Tablas: finanzas.cuenta_contable, finanzas.centro_costo
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-17

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-01: por construir')


def fin_02_contabilizar_comprobante(*, usuario, **datos):
    """FIN-02 · Contabilizar un comprobante

    Actores: Contador; secundarios: Asistente contable (IA)
    Fase 1
    Tablas: finanzas.comprobante, finanzas.movimiento_contable
    Reglas en la base: finanzas.validar_cuadre(), finanzas.proteger_movimiento()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-17, RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.validar_cuadre(), finanzas.proteger_movimiento()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-02: por construir')


def fin_03_anular_comprobante_registrar_nota(*, usuario, **datos):
    """FIN-03 · Anular un comprobante o registrar una nota

    Actores: Contador
    Fase 1
    Tablas: finanzas.comprobante
    Reglas en la base: finanzas.proteger_comprobante()
    Endpoints: CRUD de sus tablas
    Requerimientos: RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-03:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.proteger_comprobante()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-03: por construir')


def fin_04_cerrar_periodo_contable(*, usuario, **datos):
    """FIN-04 · Cerrar el periodo contable

    Actores: Contador; secundarios: Tareas programadas
    Fase 1
    Tablas: finanzas.periodo_contable
    Reglas en la base: formato y permisos de DRF
    Endpoints: POST /api/v1/finanzas/periodos-contable/{id}/cerrar/
    Requerimientos: RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-04:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-04: por construir')


def fin_05_clasificar_costos_distribuirlos_actividades(*, usuario, **datos):
    """FIN-05 · Clasificar costos y distribuirlos por actividades

    Actores: Contador
    Fase 2
    Tablas: finanzas.clasificacion_costo, finanzas.actividad_costo, finanzas.asignacion_costo, finanzas.costo_estandar
    Reglas en la base: finanzas.validar_clasificacion(), finanzas.distribuir_costos()
    Endpoints: CRUD de sus tablas
    Requerimientos: RF-18, RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.validar_clasificacion(), finanzas.distribuir_costos()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-05: por construir')


def fin_06_elaborar_aprobar_presupuesto_maestro(*, usuario, **datos):
    """FIN-06 · Elaborar y aprobar el presupuesto maestro

    Actores: Contador, Familia
    Fase 2
    Tablas: finanzas.presupuesto, finanzas.premisa_presupuesto, finanzas.presupuesto_detalle
    Reglas en la base: finanzas.validar_presupuesto_detalle()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-38, RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.validar_presupuesto_detalle()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-06: por construir')


def fin_07_generar_estados_financieros(*, usuario, **datos):
    """FIN-07 · Generar los estados financieros

    Actores: Contador, Familia
    Fase 2
    Tablas: finanzas.estado_financiero
    Reglas en la base: finanzas.estado_resultados(), finanzas.balance_general(), finanzas.saldo()
    Endpoints: GET /api/v1/finanzas/estado-resultados/?desde=&hasta=&centro=; GET /api/v1/finanzas/balance/?hasta=
    Requerimientos: RF-17, RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-07:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.estado_resultados(), finanzas.balance_general(), finanzas.saldo()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-07: por construir')


def fin_08_calcular_indicadores_consultar_tablero(*, usuario, **datos):
    """FIN-08 · Calcular indicadores y consultar el tablero

    Actores: Familia, Tareas programadas; secundarios: Analista de negocio (IA)
    Fase 2
    Tablas: finanzas.indicador, finanzas.valor_indicador, estrategia.objetivo
    Reglas en la base: finanzas.calcular_indicadores()
    Endpoints: POST /api/v1/finanzas/indicadores/calcular/
    Requerimientos: RF-17, RF-18, RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-08:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.calcular_indicadores()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-08: por construir')


def fin_09_analizar_estados_vertical_horizontal_fuentes(*, usuario, **datos):
    """FIN-09 · Analizar estados: vertical, horizontal, fuentes y usos

    Actores: Contador, Familia; secundarios: Analista de negocio (IA)
    Fase 2
    Tablas: finanzas.cuenta_contable, finanzas.movimiento_contable
    Reglas en la base: finanzas.analisis_vertical_horizontal(), finanzas.fuentes_usos()
    Endpoints: GET /api/v1/finanzas/analisis/?a=&b=; GET /api/v1/finanzas/fuentes-usos/?a=&b=
    Requerimientos: RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-09:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.analisis_vertical_horizontal(), finanzas.fuentes_usos()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-09: por construir')


def fin_10_calcular_punto_equilibrio_palancas(*, usuario, **datos):
    """FIN-10 · Calcular punto de equilibrio y palancas

    Actores: Familia; secundarios: Estratega (IA)
    Fase 2
    Tablas: ninguna propia
    Reglas en la base: finanzas.palancas()
    Endpoints: GET /api/v1/finanzas/palancas/?q=&p=&cv=&cf=&i=
    Requerimientos: RQ-38, RQ-37

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-10:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.palancas()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-10: por construir')


def fin_11_gestionar_anticipos_proveedores(*, usuario, **datos):
    """FIN-11 · Gestionar anticipos a proveedores

    Actores: Contador
    Fase 2
    Tablas: finanzas.anticipo_proveedor, finanzas.aplicacion_anticipo
    Reglas en la base: finanzas.aplicar_anticipo(), finanzas.preparar_anticipo()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-38

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-11:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: finanzas.aplicar_anticipo(), finanzas.preparar_anticipo()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-11: por construir')


def fin_12_emitir_informe_indicadores_para_credito(*, usuario, **datos):
    """FIN-12 · Emitir un informe de indicadores para crédito

    Actores: Familia; secundarios: Sistema del cliente B2B
    Fase 3 · función indicadores_credito
    Tablas: finanzas.reporte_indicadores
    Reglas en la base: finanzas.validar_reporte_indicadores()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-38, RNF-13

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para FIN-12:
    # 1. with transaction.atomic():
    # 2. La función «indicadores_credito» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: finanzas.validar_reporte_indicadores()
    # 4. publicar('finanzas.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('FIN-12: por construir')
