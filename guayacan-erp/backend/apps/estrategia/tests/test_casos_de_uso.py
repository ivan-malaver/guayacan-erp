"""Pruebas de aceptación de los casos de uso de estrategia.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='EST-01: por construir')
def test_est_01_mantener_lineas_negocio_matriz_dofa_flujo_principal():
    """EST-01 · Mantener las líneas de negocio y la matriz DOFA"""


@pytest.mark.skip(reason='EST-02: por construir')
def test_est_02_registrar_estudio_mercado_flujo_principal():
    """EST-02 · Registrar un estudio de mercado"""


@pytest.mark.skip(reason='EST-03: por construir')
def test_est_03_proponer_iniciativa_crecimiento_flujo_principal():
    """EST-03 · Proponer una iniciativa de crecimiento"""


@pytest.mark.skip(reason='EST-04: por construir')
def test_est_04_evaluar_financieramente_iniciativa_flujo_principal():
    """EST-04 · Evaluar financieramente una iniciativa"""


@pytest.mark.skip(reason='EST-05: por construir')
def test_est_05_aprobar_iniciativa_flujo_principal():
    """EST-05 · Aprobar una iniciativa"""


@pytest.mark.skip(reason='EST-06: por construir')
def test_est_06_reinvertir_utilidades_linea_flujo_principal():
    """EST-06 · Reinvertir utilidades de una línea"""


@pytest.mark.skip(reason='EST-07: por construir')
def test_est_07_seguir_retorno_iniciativas_flujo_principal():
    """EST-07 · Seguir el retorno de las iniciativas"""


@pytest.mark.skip(reason='EST-08: por construir')
def test_est_08_definir_objetivos_metas_cuadro_mando_flujo_principal():
    """EST-08 · Definir objetivos y metas del cuadro de mando"""
