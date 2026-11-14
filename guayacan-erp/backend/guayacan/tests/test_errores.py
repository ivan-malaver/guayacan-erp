"""Pruebas de guayacan/errores.py. No necesitan base de datos: se fabrican errores falsos con el mismo formato
que los de psycopg (sqlstate y diag) y se revisa la respuesta HTTP que produce cada uno."""
import pytest
from django.db import DatabaseError

from guayacan.errores import respuesta_de_base


# Imita el objeto diag de psycopg (los detalles que envía PostgreSQL)
class Diag:
    def __init__(self, mensaje, restriccion=None, columna=None):
        self.message_primary, self.constraint_name, self.column_name = mensaje, restriccion, columna


# Imita un error de psycopg con su SQLSTATE
class ErrorPsycopg(Exception):
    def __init__(self, sqlstate, mensaje, **kw):
        super().__init__(mensaje)
        self.sqlstate, self.diag = sqlstate, Diag(mensaje, **kw)


# Django envuelve el error del conector: el original queda en __cause__
def error_django(sqlstate, mensaje, **kw):
    exc = DatabaseError(mensaje)
    exc.__cause__ = ErrorPsycopg(sqlstate, mensaje, **kw)
    return exc


# parametrize repite la misma prueba con cada fila de datos (SQLSTATE, HTTP esperado, código esperado)
@pytest.mark.parametrize(('sqlstate', 'http', 'codigo'), [
    ('P0001', 422, 'regla_negocio'), ('42501', 403, 'sin_permiso'), ('23505', 409, 'duplicado'),
    ('23P01', 409, 'cruce'), ('23514', 422, 'valor_invalido'), ('23503', 422, 'referencia_invalida'),
    ('40001', 503, 'reintentar'), ('XX000', 500, 'error_base'),
])
def test_traduce_sqlstate(sqlstate, http, codigo):
    r = respuesta_de_base(error_django(sqlstate, 'mensaje'))
    assert r.status_code == http
    assert r.data['codigo'] == codigo


# El mensaje en español de la regla llega intacto al usuario
def test_conserva_el_mensaje_de_la_regla():
    r = respuesta_de_base(error_django('P0001', 'Un agente de IA no puede aprobar precios: lo hace una persona'))
    assert r.data['detalle'] == 'Un agente de IA no puede aprobar precios: lo hace una persona'


# En un error 500 no se muestran detalles internos
def test_no_filtra_detalles_en_error_interno():
    r = respuesta_de_base(error_django('XX000', 'detalle interno con datos'))
    assert 'datos' not in r.data['detalle']


# Se informa qué restricción falló (útil para mostrar el cruce de reservas)
def test_informa_la_restriccion_del_cruce():
    r = respuesta_de_base(error_django('23P01', 'conflicting key value', restriccion='ex_reserva_recurso_cruce'))
    assert r.data['restriccion'] == 'ex_reserva_recurso_cruce'
