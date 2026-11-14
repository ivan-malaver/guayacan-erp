"""Pruebas de aceptación de los casos de uso de formacion.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='FOR-01: por construir')
def test_for_01_disenar_curso_lecciones_evaluacion_flujo_principal():
    """FOR-01 · Diseñar un curso con lecciones y evaluación"""


@pytest.mark.skip(reason='FOR-02: por construir')
def test_for_02_tomar_curso_virtual_flujo_principal():
    """FOR-02 · Tomar un curso virtual"""


@pytest.mark.skip(reason='FOR-03: por construir')
def test_for_03_dictar_sesion_presencial_registrar_asistencia_flujo_principal():
    """FOR-03 · Dictar una sesión presencial y registrar asistencia"""


@pytest.mark.skip(reason='FOR-04: por construir')
def test_for_04_emitir_certificados_habilitaciones_flujo_principal():
    """FOR-04 · Emitir certificados y habilitaciones"""


@pytest.mark.skip(reason='FOR-05: por construir')
def test_for_05_retirar_habilitaciones_vencidas_flujo_principal():
    """FOR-05 · Retirar habilitaciones vencidas"""


@pytest.mark.skip(reason='FOR-06: por construir')
def test_for_06_detectar_necesidades_formacion_flujo_principal():
    """FOR-06 · Detectar necesidades de formación"""


@pytest.mark.skip(reason='FOR-07: por construir')
def test_for_07_responder_encuesta_curso_flujo_principal():
    """FOR-07 · Responder la encuesta de un curso"""


@pytest.mark.skip(reason='FOR-08: por construir')
def test_for_08_presentar_resolver_queja_apelacion_flujo_principal():
    """FOR-08 · Presentar y resolver una queja o apelación"""


@pytest.mark.skip(reason='FOR-09: por construir')
def test_for_09_preguntar_instructor_virtual_flujo_principal():
    """FOR-09 · Preguntar al Instructor virtual"""
