"""Pruebas de aceptación de los casos de uso de terceros.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='TER-01: por construir')
def test_ter_01_registrar_tercero_persona_empresa_flujo_principal():
    """TER-01 · Registrar un tercero (persona o empresa)"""


@pytest.mark.skip(reason='TER-02: por construir')
def test_ter_02_registrar_revocar_autorizacion_datos_flujo_principal():
    """TER-02 · Registrar y revocar una autorización de datos"""


@pytest.mark.skip(reason='TER-03: por construir')
def test_ter_03_atender_solicitud_titular_datos_flujo_principal():
    """TER-03 · Atender una solicitud del titular de datos"""


@pytest.mark.skip(reason='TER-04: por construir')
def test_ter_04_gestionar_clientes_proveedores_empleados_flujo_principal():
    """TER-04 · Gestionar clientes, proveedores y empleados"""
