"""Pruebas de aceptación de los casos de uso de personal.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='PER-01: por construir')
def test_per_01_configurar_areas_responsabilidad_matriz_raci_flujo_principal():
    """PER-01 · Configurar áreas de responsabilidad y matriz RACI"""


@pytest.mark.skip(reason='PER-02: por construir')
def test_per_02_definir_plan_labores_flujo_principal():
    """PER-02 · Definir el plan de labores"""


@pytest.mark.skip(reason='PER-03: por construir')
def test_per_03_generar_tareas_dia_flujo_principal():
    """PER-03 · Generar las tareas del día"""


@pytest.mark.skip(reason='PER-04: por construir')
def test_per_04_asignar_tarea_flujo_principal():
    """PER-04 · Asignar una tarea"""


@pytest.mark.skip(reason='PER-05: por construir')
def test_per_05_ejecutar_tarea_evidencia_flujo_principal():
    """PER-05 · Ejecutar una tarea con evidencia"""


@pytest.mark.skip(reason='PER-06: por construir')
def test_per_06_aprobar_devolver_tarea_flujo_principal():
    """PER-06 · Aprobar o devolver una tarea"""


@pytest.mark.skip(reason='PER-07: por construir')
def test_per_07_armar_publicar_cronograma_turnos_flujo_principal():
    """PER-07 · Armar y publicar el cronograma de turnos"""


@pytest.mark.skip(reason='PER-08: por construir')
def test_per_08_registrar_disponibilidad_ausencias_flujo_principal():
    """PER-08 · Registrar disponibilidad y ausencias"""


@pytest.mark.skip(reason='PER-09: por construir')
def test_per_09_registrar_jornada_carne_flujo_principal():
    """PER-09 · Registrar la jornada con el carné"""


@pytest.mark.skip(reason='PER-10: por construir')
def test_per_10_organizar_cuadrillas_flujo_principal():
    """PER-10 · Organizar cuadrillas"""
