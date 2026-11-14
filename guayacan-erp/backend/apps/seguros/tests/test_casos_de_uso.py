"""Pruebas de aceptación de los casos de uso de seguros.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='SGR-01: por construir')
def test_sgr_01_registrar_poliza_bienes_asegurados_flujo_principal():
    """SGR-01 · Registrar una póliza y sus bienes asegurados"""


@pytest.mark.skip(reason='SGR-02: por construir')
def test_sgr_02_avisar_polizas_proximas_vencer_flujo_principal():
    """SGR-02 · Avisar pólizas próximas a vencer"""


@pytest.mark.skip(reason='SGR-03: por construir')
def test_sgr_03_registrar_enviar_aviso_siniestro_flujo_principal():
    """SGR-03 · Registrar y enviar un aviso de siniestro"""


@pytest.mark.skip(reason='SGR-04: por construir')
def test_sgr_04_vigilar_indice_poliza_parametrica_flujo_principal():
    """SGR-04 · Vigilar el índice de una póliza paramétrica"""
