"""Configuración compartida de pytest (las «fixtures» que pueden pedir las pruebas).

Las pruebas que tocan la base usan la base ya cargada con esquema_postgresql.sql y datos_iniciales.sql
(Django no crea ni migra las tablas de negocio). Cada prueba corre dentro de una transacción que se deshace al
final, así una prueba no deja datos que afecten a otra.

Para fijar la finca dentro de una prueba use la fixture `en_finca`:
    def test_algo(en_finca):
        en_finca(predio=1, usuario=1)
"""
import pytest
from django.db import connection


@pytest.fixture(scope='session')
def django_db_setup():
    """Reemplaza la de pytest-django: NO crea una base de pruebas, usa la de DATABASES['default'] (ya cargada)."""


@pytest.fixture
def en_finca(db):
    """Devuelve una función que fija app.predio_id, app.usuario_id y app.agente_id para la transacción de la prueba."""

    def fijar(predio, usuario=None, agente=None):
        with connection.cursor() as cur:
            cur.execute("select set_config('app.predio_id', %s, true), set_config('app.usuario_id', %s, true), "
                        "set_config('app.agente_id', %s, true)",
                        [str(predio), '' if usuario is None else str(usuario), '' if agente is None else str(agente)])

    return fijar
