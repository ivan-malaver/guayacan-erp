"""Pruebas de aceptación de los casos de uso de redes.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest


@pytest.mark.skip(reason='RED-01: por construir')
def test_red_01_atender_mensaje_cliente_canal_flujo_principal():
    """RED-01 · Atender el mensaje de un cliente por un canal"""


@pytest.mark.skip(reason='RED-02: por construir')
def test_red_02_escalar_conversacion_persona_flujo_principal():
    """RED-02 · Escalar una conversación a una persona"""


@pytest.mark.skip(reason='RED-03: por construir')
def test_red_03_enviar_mensaje_saliente_dentro_reglas_flujo_principal():
    """RED-03 · Enviar un mensaje saliente dentro de las reglas del canal"""


@pytest.mark.skip(reason='RED-04: por construir')
def test_red_04_proponer_aprobar_publicacion_flujo_principal():
    """RED-04 · Proponer y aprobar una publicación"""


@pytest.mark.skip(reason='RED-05: por construir')
def test_red_05_producir_pieza_audiovisual_autorizacion_imagen_flujo_principal():
    """RED-05 · Producir una pieza audiovisual con autorización de imagen"""


@pytest.mark.skip(reason='RED-06: por construir')
def test_red_06_mantener_plantillas_politicas_canal_flujo_principal():
    """RED-06 · Mantener plantillas y políticas de canal"""
