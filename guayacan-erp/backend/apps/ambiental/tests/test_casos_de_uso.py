"""Pruebas de aceptación de los casos de uso de ambiental.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='AMB-01: por construir')
def test_amb_01_registrar_mediciones_ambientales_flujo_principal():
    """AMB-01 · Registrar mediciones ambientales"""


@pytest.mark.skip(reason='AMB-02: por construir')
def test_amb_02_mantener_factores_emision_fuente_flujo_principal():
    """AMB-02 · Mantener factores de emisión con su fuente"""


@pytest.mark.skip(reason='AMB-03: por construir')
def test_amb_03_consultar_indicadores_ambientales_co_estimado_flujo_principal():
    """AMB-03 · Consultar indicadores ambientales y CO₂ estimado"""
