"""Pruebas de aceptación de los casos de uso de nucleo.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='NUC-01: por construir')
def test_nuc_01_configurar_finca_zonas_mapa_flujo_principal():
    """NUC-01 · Configurar la finca, sus zonas y el mapa"""


@pytest.mark.skip(reason='NUC-02: por construir')
def test_nuc_02_gestionar_usuarios_roles_permisos_flujo_principal():
    """NUC-02 · Gestionar usuarios, roles y permisos"""


@pytest.mark.skip(reason='NUC-03: por construir')
def test_nuc_03_administrar_parametros_vigencia_flujo_principal():
    """NUC-03 · Administrar parámetros con vigencia"""


@pytest.mark.skip(reason='NUC-04: por construir')
def test_nuc_04_encender_apagar_funcion_finca_flujo_principal():
    """NUC-04 · Encender o apagar una función de la finca"""


@pytest.mark.skip(reason='NUC-05: por construir')
def test_nuc_05_sincronizar_registros_capturados_sin_conexion_flujo_principal():
    """NUC-05 · Sincronizar registros capturados sin conexión"""


@pytest.mark.skip(reason='NUC-06: por construir')
def test_nuc_06_consultar_auditoria_cambios_flujo_principal():
    """NUC-06 · Consultar la auditoría de cambios"""


@pytest.mark.skip(reason='NUC-07: por construir')
def test_nuc_07_registrar_nota_voz_campo_confirmarla_flujo_principal():
    """NUC-07 · Registrar una nota de voz en campo y confirmarla"""


@pytest.mark.skip(reason='NUC-08: por construir')
def test_nuc_08_practicar_finca_aprendizaje_flujo_principal():
    """NUC-08 · Practicar en la finca de aprendizaje"""


@pytest.mark.skip(reason='NUC-09: por construir')
def test_nuc_09_publicar_eventos_integracion_flujo_principal():
    """NUC-09 · Publicar los eventos de integración"""


@pytest.mark.skip(reason='NUC-10: por construir')
def test_nuc_10_administrar_llaves_api_b2b_webhooks_flujo_principal():
    """NUC-10 · Administrar llaves de API B2B y webhooks"""
