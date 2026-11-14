"""Pruebas de aceptación de los casos de uso de ia.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='IA-01: por construir')
def test_ia_01_configurar_agente_herramientas_flujo_principal():
    """IA-01 · Configurar un agente y sus herramientas"""


@pytest.mark.skip(reason='IA-02: por construir')
def test_ia_02_resolver_bandeja_aprobaciones_flujo_principal():
    """IA-02 · Resolver la bandeja de aprobaciones"""


@pytest.mark.skip(reason='IA-03: por construir')
def test_ia_03_alimentar_base_conocimiento_flujo_principal():
    """IA-03 · Alimentar la base de conocimiento"""


@pytest.mark.skip(reason='IA-04: por construir')
def test_ia_04_recibir_seguir_recomendaciones_mejora_flujo_principal():
    """IA-04 · Recibir y seguir recomendaciones de mejora"""


@pytest.mark.skip(reason='IA-05: por construir')
def test_ia_05_evaluar_respuestas_agentes_flujo_principal():
    """IA-05 · Evaluar las respuestas de los agentes"""


@pytest.mark.skip(reason='IA-06: por construir')
def test_ia_06_controlar_consumo_costo_ia_flujo_principal():
    """IA-06 · Controlar el consumo y el costo de la IA"""


@pytest.mark.skip(reason='IA-07: por construir')
def test_ia_07_pronosticar_demanda_flujo_principal():
    """IA-07 · Pronosticar la demanda"""


@pytest.mark.skip(reason='IA-08: por construir')
def test_ia_08_diagnosticar_foto_campo_flujo_principal():
    """IA-08 · Diagnosticar una foto de campo"""


@pytest.mark.skip(reason='IA-09: por construir')
def test_ia_09_simular_escenario_registrar_decision_flujo_principal():
    """IA-09 · Simular un escenario y registrar la decisión"""
