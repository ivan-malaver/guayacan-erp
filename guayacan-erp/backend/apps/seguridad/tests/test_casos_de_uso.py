"""Pruebas de aceptación de los casos de uso de seguridad.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='SEG-01: por construir')
def test_seg_01_iniciar_sesion_doble_factor_flujo_principal():
    """SEG-01 · Iniciar sesión con doble factor"""


@pytest.mark.skip(reason='SEG-02: por construir')
def test_seg_02_inscribir_segundo_factor_recuperar_contrasena_flujo_principal():
    """SEG-02 · Inscribir el segundo factor y recuperar la contraseña"""


@pytest.mark.skip(reason='SEG-03: por construir')
def test_seg_03_detectar_bloquear_ataques_acceso_flujo_principal():
    """SEG-03 · Detectar y bloquear ataques de acceso"""


@pytest.mark.skip(reason='SEG-04: por construir')
def test_seg_04_atender_alerta_incidente_seguridad_flujo_principal():
    """SEG-04 · Atender una alerta o un incidente de seguridad"""


@pytest.mark.skip(reason='SEG-05: por construir')
def test_seg_05_revocar_sesiones_levantar_bloqueos_flujo_principal():
    """SEG-05 · Revocar sesiones y levantar bloqueos"""


@pytest.mark.skip(reason='SEG-06: por construir')
def test_seg_06_registrar_corrida_pruebas_flujo_principal():
    """SEG-06 · Registrar una corrida de pruebas"""


@pytest.mark.skip(reason='SEG-07: por construir')
def test_seg_07_verificar_copias_seguridad_restauraciones_flujo_principal():
    """SEG-07 · Verificar copias de seguridad y restauraciones"""
