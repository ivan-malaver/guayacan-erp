"""Pruebas de aceptación de los casos de uso de crm.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='CRM-01: por construir')
def test_crm_01_capturar_posible_cliente_autorizacion_flujo_principal():
    """CRM-01 · Capturar un posible cliente con autorización"""


@pytest.mark.skip(reason='CRM-02: por construir')
def test_crm_02_gestionar_segmentos_campanas_flujo_principal():
    """CRM-02 · Gestionar segmentos y campañas"""


@pytest.mark.skip(reason='CRM-03: por construir')
def test_crm_03_registrar_interacciones_avanzar_embudo_flujo_principal():
    """CRM-03 · Registrar interacciones y avanzar el embudo"""


@pytest.mark.skip(reason='CRM-04: por construir')
def test_crm_04_calificar_prospectos_flujo_principal():
    """CRM-04 · Calificar los prospectos"""


@pytest.mark.skip(reason='CRM-05: por construir')
def test_crm_05_convertir_prospecto_cliente_flujo_principal():
    """CRM-05 · Convertir un prospecto en cliente"""


@pytest.mark.skip(reason='CRM-06: por construir')
def test_crm_06_gestionar_oportunidades_proyectar_ventas_flujo_principal():
    """CRM-06 · Gestionar oportunidades y proyectar ventas"""
