"""Pruebas de aceptación de los casos de uso de riego.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='RIE-01: por construir')
def test_rie_01_configurar_fuentes_tanques_sistemas_valvulas_flujo_principal():
    """RIE-01 · Configurar fuentes, tanques, sistemas y válvulas"""


@pytest.mark.skip(reason='RIE-02: por construir')
def test_rie_02_registrar_riego_manual_flujo_principal():
    """RIE-02 · Registrar un riego manual"""


@pytest.mark.skip(reason='RIE-03: por construir')
def test_rie_03_regar_automaticamente_reglas_flujo_principal():
    """RIE-03 · Regar automáticamente por reglas"""
