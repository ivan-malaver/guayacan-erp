"""Casos de uso del esquema adopcion: una función por caso de uso.

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


def ado_01_configurar_catalogo_sitios(*, usuario, **datos):
    """ADO-01 · Configurar catálogo y sitios

    Actores: Administrador; secundarios: Encargado de finca
    Fase 3 · función adopcion
    Tablas: adopcion.plan, adopcion.sitio, adopcion.bien
    Reglas en la base: nucleo.exigir_funcion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-45

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-01:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: nucleo.exigir_funcion()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-01: por construir')


def ado_02_comprar_arbol_animal(*, usuario, **datos):
    """ADO-02 · Comprar un árbol o un animal

    Actores: Adoptante; secundarios: Pasarela de pagos, Vendedor personalizado (IA)
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.bien, terceros.tercero, terceros.consentimiento_datos, comercial.pago
    Reglas en la base: adopcion.validar_contrato(), comercial.preparar_factura()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-45

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-02:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_contrato(), comercial.preparar_factura()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-02: por construir')


def ado_03_sembrar_persona(*, usuario, **datos):
    """ADO-03 · Sembrar en persona

    Actores: Adoptante; secundarios: Encargado de finca, Portería
    Fase 3 · función adopcion
    Tablas: adopcion.seguimiento, agenda.visita
    Reglas en la base: adopcion.registrar_siembra()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/siembra/
    Requerimientos: RQ-45

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-03:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.registrar_siembra()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-03: por construir')


def ado_04_sembrar_trabajador_enviar_video(*, usuario, **datos):
    """ADO-04 · Sembrar por un trabajador y enviar el video

    Actores: Operario de campo; secundarios: Encargado de finca, Gestor de redes (IA)
    Fase 3 · función adopcion
    Tablas: personal.tarea, personal.evidencia_tarea, adopcion.seguimiento
    Reglas en la base: adopcion.registrar_siembra(), redes.verificar_envio()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/siembra/
    Requerimientos: RQ-45

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-04:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.registrar_siembra(), redes.verificar_envio()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-04: por construir')


def ado_05_cobrar_pagar_cuota_mensual(*, usuario, **datos):
    """ADO-05 · Cobrar y pagar la cuota mensual

    Actores: Tareas programadas; secundarios: Adoptante, Pasarela de pagos
    Fase 3 · función adopcion
    Tablas: adopcion.cuota, adopcion.movimiento_saldo, comercial.pago
    Reglas en la base: adopcion.generar_cuotas(), adopcion.compensar_cuotas()
    Endpoints: POST /api/v1/adopcion/cuotas/{id}/pagar/
    Requerimientos: RQ-46

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-05:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.generar_cuotas(), adopcion.compensar_cuotas()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-05: por construir')


def ado_06_seguir_mi_arbol_mi_animal(*, usuario, **datos):
    """ADO-06 · Seguir mi árbol o mi animal

    Actores: Adoptante; secundarios: Operario de campo
    Fase 3 · función adopcion
    Tablas: adopcion.seguimiento, adopcion.cuota, adopcion.movimiento_saldo
    Reglas en la base: adopcion.saldo()
    Endpoints: GET /api/v1/adopcion/mis-bienes/; GET /api/v1/adopcion/mis-bienes/{id}/seguimiento/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-06:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.saldo()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-06: por construir')


def ado_07_detectar_abandono_poner_readopcion(*, usuario, **datos):
    """ADO-07 · Detectar abandono y poner en readopción

    Actores: Tareas programadas; secundarios: Adoptante, Gestor de redes (IA)
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.cuota, adopcion.bien, adopcion.seguimiento
    Reglas en la base: adopcion.marcar_abandono()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-46

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-07:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.marcar_abandono()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-07: por construir')


def ado_08_readoptar(*, usuario, **datos):
    """ADO-08 · Readoptar

    Actores: Adoptante; secundarios: Pasarela de pagos
    Fase 3 · función adopcion
    Tablas: adopcion.contrato, adopcion.bien
    Reglas en la base: adopcion.validar_contrato()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-46

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-08:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_contrato()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-08: por construir')


def ado_09_registrar_vender_productos_bien(*, usuario, **datos):
    """ADO-09 · Registrar y vender productos del bien

    Actores: Operario de campo; secundarios: Vendedor
    Fase 3 · función adopcion
    Tablas: adopcion.seguimiento, comercial.pedido
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-09:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-09: por construir')


def ado_10_liquidar_productos_5(*, usuario, **datos):
    """ADO-10 · Liquidar productos con el 5 %

    Actores: Administrador; secundarios: Contador
    Fase 3 · función adopcion
    Tablas: adopcion.liquidacion, adopcion.movimiento_saldo
    Reglas en la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    Endpoints: POST /api/v1/adopcion/liquidaciones/{id}/aprobar/; POST /api/v1/adopcion/adoptantes/{id}/pagar-saldo/
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-10:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-10: por construir')


def ado_11_decidir_madurez_mantener_liquidar(*, usuario, **datos):
    """ADO-11 · Decidir en la madurez: mantener o liquidar

    Actores: Adoptante; secundarios: Administrador
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato
    Reglas en la base: adopcion.marcar_madurez(), adopcion.validar_contrato()
    Endpoints: POST /api/v1/adopcion/contratos/{id}/decision/
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-11:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.marcar_madurez(), adopcion.validar_contrato()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-11: por construir')


def ado_12_talar_sacrificar_liquidar(*, usuario, **datos):
    """ADO-12 · Talar o sacrificar y liquidar

    Actores: Administrador; secundarios: Autoridad o planta de beneficio (CAR, ICA, INVIMA)
    Fase 3 · función adopcion
    Tablas: adopcion.liquidacion, documental.documento
    Reglas en la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-47

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-12:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_liquidacion(), adopcion.aplicar_liquidacion()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-12: por construir')


def ado_13_reponer_bien_muerto_garantia(*, usuario, **datos):
    """ADO-13 · Reponer un bien muerto en garantía

    Actores: Encargado de finca; secundarios: Adoptante
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato, adopcion.seguimiento
    Reglas en la base: adopcion.registrar_muerte()
    Endpoints: POST /api/v1/adopcion/bienes/{id}/muerte/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-13:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.registrar_muerte()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-13: por construir')


def ado_14_ceder_regalar_adopcion(*, usuario, **datos):
    """ADO-14 · Ceder o regalar la adopción

    Actores: Adoptante
    Fase 3 · función adopcion
    Tablas: adopcion.contrato
    Reglas en la base: adopcion.validar_contrato()
    Endpoints: POST /api/v1/adopcion/contratos/{id}/ceder/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-14:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.validar_contrato()
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-14: por construir')


def ado_15_consultar_tablero_adopcion(*, usuario, **datos):
    """ADO-15 · Consultar el tablero de adopción

    Actores: Familia; secundarios: Administrador
    Fase 3 · función adopcion
    Tablas: adopcion.bien, adopcion.contrato, adopcion.cuota
    Reglas en la base: adopcion.v_tablero
    Endpoints: GET /api/v1/adopcion/tablero/
    Requerimientos: RQ-48

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para ADO-15:
    # 1. with transaction.atomic():
    # 2. La función «adopcion» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)
    # 3. Llamar a la base: adopcion.v_tablero
    # 4. publicar('adopcion.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('ADO-15: por construir')
