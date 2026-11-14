"""Pruebas de aceptación de los casos de uso de proyectos.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='PRY-01: por construir')
def test_pry_01_constituir_proyecto_flujo_principal():
    """PRY-01 · Constituir un proyecto"""


@pytest.mark.skip(reason='PRY-02: por construir')
def test_pry_02_aprobar_proyecto_flujo_principal():
    """PRY-02 · Aprobar un proyecto"""


@pytest.mark.skip(reason='PRY-03: por construir')
def test_pry_03_planificar_alcance_cronograma_flujo_principal():
    """PRY-03 · Planificar el alcance y el cronograma"""


@pytest.mark.skip(reason='PRY-04: por construir')
def test_pry_04_calcular_ruta_critica_flujo_principal():
    """PRY-04 · Calcular la ruta crítica"""


@pytest.mark.skip(reason='PRY-05: por construir')
def test_pry_05_gestionar_interesados_riesgos_flujo_principal():
    """PRY-05 · Gestionar interesados y riesgos"""


@pytest.mark.skip(reason='PRY-06: por construir')
def test_pry_06_registrar_avance_medir_valor_ganado_flujo_principal():
    """PRY-06 · Registrar avance y medir el valor ganado"""


@pytest.mark.skip(reason='PRY-07: por construir')
def test_pry_07_solicitar_decidir_cambio_flujo_principal():
    """PRY-07 · Solicitar y decidir un cambio"""


@pytest.mark.skip(reason='PRY-08: por construir')
def test_pry_08_aceptar_entregables_cerrar_proyecto_flujo_principal():
    """PRY-08 · Aceptar entregables y cerrar el proyecto"""


@pytest.mark.skip(reason='PRY-09: por construir')
def test_pry_09_planear_cerrar_iteracion_flujo_principal():
    """PRY-09 · Planear y cerrar una iteración"""
