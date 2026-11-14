"""Pruebas de aceptación de los casos de uso de activos.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='ACT-01: por construir')
def test_act_01_registrar_activo_hoja_vida_flujo_principal():
    """ACT-01 · Registrar un activo con su hoja de vida"""


@pytest.mark.skip(reason='ACT-02: por construir')
def test_act_02_registrar_uso_activo_flujo_principal():
    """ACT-02 · Registrar el uso de un activo"""


@pytest.mark.skip(reason='ACT-03: por construir')
def test_act_03_generar_cerrar_ordenes_mantenimiento_flujo_principal():
    """ACT-03 · Generar y cerrar órdenes de mantenimiento"""


@pytest.mark.skip(reason='ACT-04: por construir')
def test_act_04_depreciar_activos_mes_flujo_principal():
    """ACT-04 · Depreciar los activos del mes"""


@pytest.mark.skip(reason='ACT-05: por construir')
def test_act_05_asignar_equipo_trabajador_flujo_principal():
    """ACT-05 · Asignar un equipo a un trabajador"""
