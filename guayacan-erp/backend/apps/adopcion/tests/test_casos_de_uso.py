"""Pruebas de aceptación de los casos de uso de adopcion.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='ADO-01: por construir')
def test_ado_01_configurar_catalogo_sitios_flujo_principal():
    """ADO-01 · Configurar catálogo y sitios"""


@pytest.mark.skip(reason='ADO-02: por construir')
def test_ado_02_comprar_arbol_animal_flujo_principal():
    """ADO-02 · Comprar un árbol o un animal"""


@pytest.mark.skip(reason='ADO-03: por construir')
def test_ado_03_sembrar_persona_flujo_principal():
    """ADO-03 · Sembrar en persona"""


@pytest.mark.skip(reason='ADO-04: por construir')
def test_ado_04_sembrar_trabajador_enviar_video_flujo_principal():
    """ADO-04 · Sembrar por un trabajador y enviar el video"""


@pytest.mark.skip(reason='ADO-05: por construir')
def test_ado_05_cobrar_pagar_cuota_mensual_flujo_principal():
    """ADO-05 · Cobrar y pagar la cuota mensual"""


@pytest.mark.skip(reason='ADO-06: por construir')
def test_ado_06_seguir_mi_arbol_mi_animal_flujo_principal():
    """ADO-06 · Seguir mi árbol o mi animal"""


@pytest.mark.skip(reason='ADO-07: por construir')
def test_ado_07_detectar_abandono_poner_readopcion_flujo_principal():
    """ADO-07 · Detectar abandono y poner en readopción"""


@pytest.mark.skip(reason='ADO-08: por construir')
def test_ado_08_readoptar_flujo_principal():
    """ADO-08 · Readoptar"""


@pytest.mark.skip(reason='ADO-09: por construir')
def test_ado_09_registrar_vender_productos_bien_flujo_principal():
    """ADO-09 · Registrar y vender productos del bien"""


@pytest.mark.skip(reason='ADO-10: por construir')
def test_ado_10_liquidar_productos_5_flujo_principal():
    """ADO-10 · Liquidar productos con el 5 %"""


@pytest.mark.skip(reason='ADO-11: por construir')
def test_ado_11_decidir_madurez_mantener_liquidar_flujo_principal():
    """ADO-11 · Decidir en la madurez: mantener o liquidar"""


@pytest.mark.skip(reason='ADO-12: por construir')
def test_ado_12_talar_sacrificar_liquidar_flujo_principal():
    """ADO-12 · Talar o sacrificar y liquidar"""


@pytest.mark.skip(reason='ADO-13: por construir')
def test_ado_13_reponer_bien_muerto_garantia_flujo_principal():
    """ADO-13 · Reponer un bien muerto en garantía"""


@pytest.mark.skip(reason='ADO-14: por construir')
def test_ado_14_ceder_regalar_adopcion_flujo_principal():
    """ADO-14 · Ceder o regalar la adopción"""


@pytest.mark.skip(reason='ADO-15: por construir')
def test_ado_15_consultar_tablero_adopcion_flujo_principal():
    """ADO-15 · Consultar el tablero de adopción"""
