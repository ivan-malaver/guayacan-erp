"""Pruebas de aceptación de los casos de uso de comercial.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='VTA-01: por construir')
def test_vta_01_gestionar_listas_precios_vigencia_flujo_principal():
    """VTA-01 · Gestionar listas y precios con vigencia"""


@pytest.mark.skip(reason='VTA-02: por construir')
def test_vta_02_proponer_aprobar_cambio_precio_flujo_principal():
    """VTA-02 · Proponer y aprobar un cambio de precio"""


@pytest.mark.skip(reason='VTA-03: por construir')
def test_vta_03_tomar_confirmar_pedido_flujo_principal():
    """VTA-03 · Tomar y confirmar un pedido"""


@pytest.mark.skip(reason='VTA-04: por construir')
def test_vta_04_vender_finca_feria_sin_conexion_flujo_principal():
    """VTA-04 · Vender en la finca o en la feria sin conexión"""


@pytest.mark.skip(reason='VTA-05: por construir')
def test_vta_05_despachar_entregar_pedido_flujo_principal():
    """VTA-05 · Despachar y entregar un pedido"""


@pytest.mark.skip(reason='VTA-06: por construir')
def test_vta_06_facturar_electronicamente_flujo_principal():
    """VTA-06 · Facturar electrónicamente"""


@pytest.mark.skip(reason='VTA-07: por construir')
def test_vta_07_registrar_confirmar_pago_flujo_principal():
    """VTA-07 · Registrar y confirmar un pago"""


@pytest.mark.skip(reason='VTA-08: por construir')
def test_vta_08_vender_credito_controlar_cartera_flujo_principal():
    """VTA-08 · Vender a crédito y controlar la cartera"""


@pytest.mark.skip(reason='VTA-09: por construir')
def test_vta_09_generar_pedidos_recurrentes_flujo_principal():
    """VTA-09 · Generar pedidos recurrentes"""


@pytest.mark.skip(reason='VTA-10: por construir')
def test_vta_10_registrar_permuta_flujo_principal():
    """VTA-10 · Registrar una permuta"""


@pytest.mark.skip(reason='VTA-11: por construir')
def test_vta_11_consultar_trazabilidad_lote_flujo_principal():
    """VTA-11 · Consultar la trazabilidad de un lote"""


@pytest.mark.skip(reason='VTA-12: por construir')
def test_vta_12_retirar_lote_mercado_flujo_principal():
    """VTA-12 · Retirar un lote del mercado"""
