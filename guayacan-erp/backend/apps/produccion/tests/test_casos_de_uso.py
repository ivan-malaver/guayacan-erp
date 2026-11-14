"""Pruebas de aceptación de los casos de uso de produccion.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='PRO-01: por construir')
def test_pro_01_registrar_ingreso_lote_animales_flujo_principal():
    """PRO-01 · Registrar el ingreso de un lote de animales"""


@pytest.mark.skip(reason='PRO-02: por construir')
def test_pro_02_registrar_postura_diaria_clasificar_huevo_flujo_principal():
    """PRO-02 · Registrar la postura diaria y clasificar el huevo"""


@pytest.mark.skip(reason='PRO-03: por construir')
def test_pro_03_registrar_alimentacion_pesajes_eventos_sanitarios_flujo_principal():
    """PRO-03 · Registrar alimentación, pesajes y eventos sanitarios"""


@pytest.mark.skip(reason='PRO-04: por construir')
def test_pro_04_registrar_eventos_reproductivos_ovinos_caprinos_flujo_principal():
    """PRO-04 · Registrar eventos reproductivos de ovinos y caprinos"""


@pytest.mark.skip(reason='PRO-05: por construir')
def test_pro_05_registrar_siembra_labores_culturales_flujo_principal():
    """PRO-05 · Registrar una siembra y sus labores culturales"""


@pytest.mark.skip(reason='PRO-06: por construir')
def test_pro_06_registrar_cosecha_destino_flujo_principal():
    """PRO-06 · Registrar una cosecha y su destino"""


@pytest.mark.skip(reason='PRO-07: por construir')
def test_pro_07_registrar_analisis_suelo_recomendacion_flujo_principal():
    """PRO-07 · Registrar un análisis de suelo y su recomendación"""


@pytest.mark.skip(reason='PRO-08: por construir')
def test_pro_08_registrar_bioseguridad_e_inocuidad_flujo_principal():
    """PRO-08 · Registrar bioseguridad e inocuidad"""


@pytest.mark.skip(reason='PRO-09: por construir')
def test_pro_09_producir_abono_lombricultivo_compostera_flujo_principal():
    """PRO-09 · Producir abono en lombricultivo o compostera"""


@pytest.mark.skip(reason='PRO-10: por construir')
def test_pro_10_medir_calidad_agua_estanques_flujo_principal():
    """PRO-10 · Medir la calidad del agua de los estanques"""
