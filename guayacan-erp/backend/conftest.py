"""Configuración compartida de pytest (las «fixtures» que pueden pedir las pruebas).

Las pruebas que tocan la base usan la base ya cargada con esquema_postgresql.sql y datos_iniciales.sql
(Django no crea ni migra las tablas de negocio). Cada prueba corre dentro de una transacción que se deshace al
final, así una prueba no deja datos que afecten a otra.

Para fijar la finca dentro de una prueba use la fixture `en_finca`:
    def test_algo(en_finca):
        en_finca(predio=1, usuario=1)
"""
import pytest

from guayacan.contexto import Contexto
from guayacan.contexto import fijar as fijar_contexto


@pytest.fixture(scope='session')
def django_db_setup():
    """Reemplaza la de pytest-django: NO crea una base de pruebas, usa la de DATABASES['default'] (ya cargada)."""


@pytest.fixture
def en_finca(db):
    """Devuelve una función que fija la finca, el usuario y el agente para la transacción de la prueba (lo mismo que
    hace guayacan.contexto.fijar en cada petición, zona horaria incluida)."""

    def fijar(predio, usuario=None, agente=None):
        fijar_contexto(Contexto(usuario_id=usuario, predio_id=predio, agente_id=agente))

    return fijar
