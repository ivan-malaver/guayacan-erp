"""Pruebas de aceptación de los casos de uso de nomina.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='NOM-01: por construir')
def test_nom_01_configurar_conceptos_tarifas_nomina_flujo_principal():
    """NOM-01 · Configurar conceptos y tarifas de nómina"""


@pytest.mark.skip(reason='NOM-02: por construir')
def test_nom_02_preparar_prenomina_flujo_principal():
    """NOM-02 · Preparar la prenómina"""


@pytest.mark.skip(reason='NOM-03: por construir')
def test_nom_03_registrar_novedades_manuales_flujo_principal():
    """NOM-03 · Registrar novedades manuales"""


@pytest.mark.skip(reason='NOM-04: por construir')
def test_nom_04_liquidar_nomina_flujo_principal():
    """NOM-04 · Liquidar la nómina"""


@pytest.mark.skip(reason='NOM-05: por construir')
def test_nom_05_cerrar_periodo_nomina_flujo_principal():
    """NOM-05 · Cerrar el periodo de nómina"""


@pytest.mark.skip(reason='NOM-06: por construir')
def test_nom_06_preparar_aprobar_pagos_nomina_flujo_principal():
    """NOM-06 · Preparar y aprobar los pagos de nómina"""


@pytest.mark.skip(reason='NOM-07: por construir')
def test_nom_07_generar_pila_exportar_contador_flujo_principal():
    """NOM-07 · Generar la PILA y exportar al contador"""


@pytest.mark.skip(reason='NOM-08: por construir')
def test_nom_08_transmitir_nomina_electronica_flujo_principal():
    """NOM-08 · Transmitir la nómina electrónica"""
