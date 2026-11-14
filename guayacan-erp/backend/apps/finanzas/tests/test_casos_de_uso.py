"""Pruebas de aceptación de los casos de uso de finanzas.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='FIN-01: por construir')
def test_fin_01_configurar_plan_cuentas_centros_costo_flujo_principal():
    """FIN-01 · Configurar el plan de cuentas y los centros de costo"""


@pytest.mark.skip(reason='FIN-02: por construir')
def test_fin_02_contabilizar_comprobante_flujo_principal():
    """FIN-02 · Contabilizar un comprobante"""


@pytest.mark.skip(reason='FIN-03: por construir')
def test_fin_03_anular_comprobante_registrar_nota_flujo_principal():
    """FIN-03 · Anular un comprobante o registrar una nota"""


@pytest.mark.skip(reason='FIN-04: por construir')
def test_fin_04_cerrar_periodo_contable_flujo_principal():
    """FIN-04 · Cerrar el periodo contable"""


@pytest.mark.skip(reason='FIN-05: por construir')
def test_fin_05_clasificar_costos_distribuirlos_actividades_flujo_principal():
    """FIN-05 · Clasificar costos y distribuirlos por actividades"""


@pytest.mark.skip(reason='FIN-06: por construir')
def test_fin_06_elaborar_aprobar_presupuesto_maestro_flujo_principal():
    """FIN-06 · Elaborar y aprobar el presupuesto maestro"""


@pytest.mark.skip(reason='FIN-07: por construir')
def test_fin_07_generar_estados_financieros_flujo_principal():
    """FIN-07 · Generar los estados financieros"""


@pytest.mark.skip(reason='FIN-08: por construir')
def test_fin_08_calcular_indicadores_consultar_tablero_flujo_principal():
    """FIN-08 · Calcular indicadores y consultar el tablero"""


@pytest.mark.skip(reason='FIN-09: por construir')
def test_fin_09_analizar_estados_vertical_horizontal_fuentes_flujo_principal():
    """FIN-09 · Analizar estados: vertical, horizontal, fuentes y usos"""


@pytest.mark.skip(reason='FIN-10: por construir')
def test_fin_10_calcular_punto_equilibrio_palancas_flujo_principal():
    """FIN-10 · Calcular punto de equilibrio y palancas"""


@pytest.mark.skip(reason='FIN-11: por construir')
def test_fin_11_gestionar_anticipos_proveedores_flujo_principal():
    """FIN-11 · Gestionar anticipos a proveedores"""


@pytest.mark.skip(reason='FIN-12: por construir')
def test_fin_12_emitir_informe_indicadores_para_credito_flujo_principal():
    """FIN-12 · Emitir un informe de indicadores para crédito"""
