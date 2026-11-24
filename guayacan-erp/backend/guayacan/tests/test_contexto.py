"""Pruebas del contexto de finca (guayacan/contexto.py).

Las dos primeras no necesitan base de datos. Las dos últimas (marcadas con @pytest.mark.django_db) sí: necesitan
la base cargada con el esquema y los datos iniciales (la integración continua las corre después de las reglas)."""
from datetime import date

import pytest
from django.conf import settings
from django.db import connection
from django.test import RequestFactory
from django.utils import timezone

from guayacan.contexto import Contexto, _entero, fijar, resolver_contexto


# _entero nunca debe fallar: convierte lo que pueda y devuelve None con valores vacíos o inválidos
def test_entero_tolera_vacios_y_basura():
    assert _entero('7') == 7
    assert _entero('') is None
    assert _entero(None) is None
    assert _entero('x') is None


# Sin token no hay usuario: aunque se envíe X-Predio, no se fija ninguna finca
def test_sin_token_no_hay_contexto():
    ctx = resolver_contexto(RequestFactory().get('/api/v1/nucleo/zonas/', HTTP_X_PREDIO='1'))
    assert ctx.usuario_id is None and ctx.predio_id is None


# fijar() deja la finca y el usuario en la sesión; la base los devuelve con sus funciones *_actual()
@pytest.mark.django_db
def test_fijar_deja_la_finca_en_la_transaccion():
    fijar(Contexto(usuario_id=1, predio_id=1))
    with connection.cursor() as cur:
        cur.execute('select nucleo.predio_actual(), nucleo.usuario_actual(), nucleo.agente_actual()')
        assert cur.fetchone() == (1, 1, None)


# «Hoy» en la base es el día de la finca, no el de UTC: Django abre la conexión en UTC y de 19:00 a medianoche
# current_date ya sería mañana (fechas por defecto, vencimientos y moras corridos un día)
@pytest.mark.django_db
def test_fijar_pone_la_hora_de_la_finca():
    fijar(Contexto(usuario_id=1, predio_id=1))
    with connection.cursor() as cur:
        cur.execute("select current_setting('TimeZone'), current_date, (timestamptz '2026-11-23 23:30-05')::date")
        assert cur.fetchone() == (settings.TIME_ZONE, timezone.localdate(), date(2026, 11, 23))


# Con agente_id fijado, la base rechaza las decisiones que solo puede tomar una persona
@pytest.mark.django_db
def test_un_agente_no_puede_decidir():
    fijar(Contexto(usuario_id=1, predio_id=1, agente_id=1))
    with connection.cursor() as cur, pytest.raises(Exception, match='Un agente de IA no puede'):
        cur.execute("select nucleo.exigir_persona('aprobar precios')")
