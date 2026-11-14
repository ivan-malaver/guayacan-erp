"""Pruebas de aceptación de los casos de uso de iot.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='IOT-01: por construir')
def test_iot_01_registrar_dispositivos_sensores_actuadores_flujo_principal():
    """IOT-01 · Registrar dispositivos, sensores y actuadores"""


@pytest.mark.skip(reason='IOT-02: por construir')
def test_iot_02_recibir_lecturas_sensores_flujo_principal():
    """IOT-02 · Recibir lecturas de sensores"""


@pytest.mark.skip(reason='IOT-03: por construir')
def test_iot_03_accionar_actuador_mano_flujo_principal():
    """IOT-03 · Accionar un actuador a mano"""


@pytest.mark.skip(reason='IOT-04: por construir')
def test_iot_04_armar_desarmar_alarma_zonas_flujo_principal():
    """IOT-04 · Armar y desarmar la alarma por zonas"""


@pytest.mark.skip(reason='IOT-05: por construir')
def test_iot_05_atender_evento_seguridad_perimetral_flujo_principal():
    """IOT-05 · Atender un evento de seguridad perimetral"""


@pytest.mark.skip(reason='IOT-06: por construir')
def test_iot_06_gestionar_credenciales_acceso_puertas_flujo_principal():
    """IOT-06 · Gestionar credenciales de acceso a puertas"""


@pytest.mark.skip(reason='IOT-07: por construir')
def test_iot_07_conservar_depurar_clips_camaras_flujo_principal():
    """IOT-07 · Conservar o depurar clips de cámaras"""


@pytest.mark.skip(reason='IOT-08: por construir')
def test_iot_08_planear_ejecutar_mision_dron_robot_flujo_principal():
    """IOT-08 · Planear y ejecutar una misión de dron o robot"""


@pytest.mark.skip(reason='IOT-09: por construir')
def test_iot_09_cortar_cargas_bateria_baja_flujo_principal():
    """IOT-09 · Cortar cargas con batería baja"""
