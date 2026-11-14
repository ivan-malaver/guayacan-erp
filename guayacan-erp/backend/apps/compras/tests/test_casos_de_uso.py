"""Pruebas de aceptación de los casos de uso de compras.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='CMP-01: por construir')
def test_cmp_01_registrar_cotizaciones_precios_mercado_flujo_principal():
    """CMP-01 · Registrar cotizaciones y precios de mercado"""


@pytest.mark.skip(reason='CMP-02: por construir')
def test_cmp_02_crear_aprobar_orden_compra_flujo_principal():
    """CMP-02 · Crear y aprobar una orden de compra"""


@pytest.mark.skip(reason='CMP-03: por construir')
def test_cmp_03_recibir_compra_bodega_flujo_principal():
    """CMP-03 · Recibir una compra en bodega"""


@pytest.mark.skip(reason='CMP-04: por construir')
def test_cmp_04_emitir_documento_soporte_electronico_flujo_principal():
    """CMP-04 · Emitir un documento soporte electrónico"""
