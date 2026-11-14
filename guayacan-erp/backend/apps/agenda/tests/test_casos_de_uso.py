"""Pruebas de aceptación de los casos de uso de agenda.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='AGD-01: por construir')
def test_agd_01_configurar_recursos_agendables_flujo_principal():
    """AGD-01 · Configurar recursos agendables"""


@pytest.mark.skip(reason='AGD-02: por construir')
def test_agd_02_agendar_cita_recurso_flujo_principal():
    """AGD-02 · Agendar una cita en un recurso"""


@pytest.mark.skip(reason='AGD-03: por construir')
def test_agd_03_programar_aprobar_visita_flujo_principal():
    """AGD-03 · Programar y aprobar una visita"""


@pytest.mark.skip(reason='AGD-04: por construir')
def test_agd_04_registrar_entradas_salidas_porteria_flujo_principal():
    """AGD-04 · Registrar entradas y salidas en portería"""


@pytest.mark.skip(reason='AGD-05: por construir')
def test_agd_05_consultar_quien_esta_finca_flujo_principal():
    """AGD-05 · Consultar quién está en la finca"""


@pytest.mark.skip(reason='AGD-06: por construir')
def test_agd_06_consultar_agenda_dia_flujo_principal():
    """AGD-06 · Consultar la agenda del día"""
