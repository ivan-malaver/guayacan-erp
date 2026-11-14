"""Pruebas de aceptación de los casos de uso de turismo.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='TUR-01: por construir')
def test_tur_01_gestionar_alojamientos_planes_turisticos_flujo_principal():
    """TUR-01 · Gestionar alojamientos y planes turísticos"""


@pytest.mark.skip(reason='TUR-02: por construir')
def test_tur_02_reservar_cabana_plan_flujo_principal():
    """TUR-02 · Reservar una cabaña o un plan"""


@pytest.mark.skip(reason='TUR-03: por construir')
def test_tur_03_pagar_anticipadamente_reserva_flujo_principal():
    """TUR-03 · Pagar anticipadamente una reserva"""


@pytest.mark.skip(reason='TUR-04: por construir')
def test_tur_04_hacer_check_in_check_out_flujo_principal():
    """TUR-04 · Hacer check-in y check-out de huéspedes"""


@pytest.mark.skip(reason='TUR-05: por construir')
def test_tur_05_atender_solicitud_grupo_flujo_principal():
    """TUR-05 · Atender la solicitud de un grupo"""


@pytest.mark.skip(reason='TUR-06: por construir')
def test_tur_06_bloquear_fechas_calendario_flujo_principal():
    """TUR-06 · Bloquear fechas del calendario"""
