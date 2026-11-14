"""Pruebas de aceptación de los casos de uso de inventario.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='INV-01: por construir')
def test_inv_01_gestionar_productos_unidades_bodegas_flujo_principal():
    """INV-01 · Gestionar productos, unidades y bodegas"""


@pytest.mark.skip(reason='INV-02: por construir')
def test_inv_02_recibir_lote_bodega_etiquetarlo_flujo_principal():
    """INV-02 · Recibir un lote en bodega y etiquetarlo"""


@pytest.mark.skip(reason='INV-03: por construir')
def test_inv_03_escanear_codigo_pesar_bascula_flujo_principal():
    """INV-03 · Escanear un código y pesar con báscula"""


@pytest.mark.skip(reason='INV-04: por construir')
def test_inv_04_registrar_merma_ajuste_traslado_flujo_principal():
    """INV-04 · Registrar merma, ajuste o traslado"""


@pytest.mark.skip(reason='INV-05: por construir')
def test_inv_05_hacer_conteo_fisico_flujo_principal():
    """INV-05 · Hacer un conteo físico"""


@pytest.mark.skip(reason='INV-06: por construir')
def test_inv_06_vigilar_vencimientos_liquidar_flujo_principal():
    """INV-06 · Vigilar vencimientos y liquidar"""


@pytest.mark.skip(reason='INV-07: por construir')
def test_inv_07_vigilar_cadena_frio_decidir_sobre_flujo_principal():
    """INV-07 · Vigilar la cadena de frío y decidir sobre un lote bloqueado"""
