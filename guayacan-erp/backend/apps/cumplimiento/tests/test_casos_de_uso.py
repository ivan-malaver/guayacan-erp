"""Pruebas de aceptación de los casos de uso de cumplimiento.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='CUM-01: por construir')
def test_cum_01_cargar_normas_requisitos_flujo_principal():
    """CUM-01 · Cargar normas y requisitos"""


@pytest.mark.skip(reason='CUM-02: por construir')
def test_cum_02_abrir_expediente_cumplimiento_flujo_principal():
    """CUM-02 · Abrir un expediente de cumplimiento"""


@pytest.mark.skip(reason='CUM-03: por construir')
def test_cum_03_evaluar_expediente_contra_evidencia_flujo_principal():
    """CUM-03 · Evaluar el expediente contra su evidencia"""


@pytest.mark.skip(reason='CUM-04: por construir')
def test_cum_04_adjuntar_evidencias_requisito_flujo_principal():
    """CUM-04 · Adjuntar evidencias a un requisito"""


@pytest.mark.skip(reason='CUM-05: por construir')
def test_cum_05_registrar_auditoria_externa_no_conformidades_flujo_principal():
    """CUM-05 · Registrar una auditoría externa y sus no conformidades"""


@pytest.mark.skip(reason='CUM-06: por construir')
def test_cum_06_ejecutar_verificar_acciones_correctivas_flujo_principal():
    """CUM-06 · Ejecutar y verificar acciones correctivas"""


@pytest.mark.skip(reason='CUM-07: por construir')
def test_cum_07_vigilar_obligacion_granja_avicola_biosegura_flujo_principal():
    """CUM-07 · Vigilar la obligación de granja avícola biosegura"""
