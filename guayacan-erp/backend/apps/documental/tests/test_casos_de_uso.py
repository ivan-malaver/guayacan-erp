"""Pruebas de aceptación de los casos de uso de documental.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='DOC-01: por construir')
def test_doc_01_publicar_documento_version_aprobada_flujo_principal():
    """DOC-01 · Publicar un documento con versión aprobada"""


@pytest.mark.skip(reason='DOC-02: por construir')
def test_doc_02_vincular_documentos_vigilar_vencimientos_flujo_principal():
    """DOC-02 · Vincular documentos y vigilar vencimientos"""


@pytest.mark.skip(reason='DOC-03: por construir')
def test_doc_03_consultar_documentos_vigentes_flujo_principal():
    """DOC-03 · Consultar documentos vigentes"""
