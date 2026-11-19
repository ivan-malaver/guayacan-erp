"""Pruebas de aceptación de los casos de uso de agenda.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import hashlib

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

from guayacan.autenticacion import emitir_tokens


@pytest.mark.skip(reason='AGD-01: por construir')
def test_agd_01_configurar_recursos_agendables_flujo_principal():
    """AGD-01 · Configurar recursos agendables"""


@pytest.mark.skip(reason='AGD-02: por construir')
def test_agd_02_agendar_cita_recurso_flujo_principal():
    """AGD-02 · Agendar una cita en un recurso"""


@pytest.fixture
def agd(en_finca):
    """Cliente con token de un usuario de la finca (encargado o administrador) y una visita lista para enviar."""
    with connection.cursor() as cur:
        cur.execute('select u.id, f.predio_id from nucleo.usuario u cross join lateral nucleo.predios_del_usuario(u.id) f order by 2, 1 limit 1')
        usuario_id, predio_id = cur.fetchone()
    en_finca(predio=predio_id, usuario=usuario_id)
    cliente = APIClient()
    tokens = emitir_tokens(get_user_model().objects.get(pk=usuario_id), predio_id)
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['acceso']}")
    visita = {'tipo': 'turista', 'nombre': 'Anna Schmidt', 'motivo': 'Sembrar su aguacate adoptado',
              'ingreso_programado': '2026-12-05T09:00:00-05:00', 'salida_programada': '2026-12-05T12:00:00-05:00'}
    return cliente, visita, usuario_id


def _visita(cliente, visita):
    r = cliente.post('/api/v1/agenda/visitas/', visita, format='json')
    assert r.status_code == 201, r.data
    return r.data


def test_agd_03_programar_aprobar_visita_flujo_principal(agd):
    """AGD-03 · Nace solicitada con el usuario de anfitrión; al aprobarla queda quién aprobó y el pase guarda solo su huella"""
    cliente, visita, usuario_id = agd
    v = _visita(cliente, visita)
    assert (v['estado'], v['anfitrion']) == ('solicitada', usuario_id)
    r = cliente.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'aprobar'}, format='json')
    assert r.status_code == 200, r.data
    assert (r.data['estado'], r.data['aprobada_por']) == ('aprobada', usuario_id)
    r = cliente.post(f"/api/v1/agenda/visitas/{v['id']}/pase/")
    assert r.status_code == 200, r.data
    with connection.cursor() as cur:
        cur.execute('select pase_hash from agenda.visita where id = %s', [v['id']])
        assert cur.fetchone()[0] == hashlib.sha256(r.data['codigo_pase'].encode()).hexdigest()
    assert 'pase_hash' not in cliente.get(f"/api/v1/agenda/visitas/{v['id']}/").data


def test_agd_03_crud_no_aprueba(agd):
    """El estado no se cambia por el CRUD: solo con /aprobar/ y su permiso"""
    cliente, visita, _ = agd
    v = _visita(cliente, {**visita, 'estado': 'aprobada'})
    assert v['estado'] == 'solicitada'
    r = cliente.patch(f"/api/v1/agenda/visitas/{v['id']}/", {'estado': 'aprobada'}, format='json')
    assert r.data['estado'] == 'solicitada'


def test_agd_03_galpon_sin_declaracion_no_se_aprueba(agd):
    """3a: al galpón sin declarar 72 horas sin contacto con otras aves, la base no deja aprobar"""
    cliente, visita, _ = agd
    v = _visita(cliente, {**visita, 'requiere_bioseguridad': True})
    r = cliente.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'aprobar'}, format='json')
    assert r.status_code == 422
    assert 'Bioseguridad' in r.data['detalle']
    v = _visita(cliente, {**visita, 'requiere_bioseguridad': True, 'contacto_aves_reciente': False})
    assert cliente.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'aprobar'}, format='json').status_code == 200


def test_agd_03_rechazo_exige_motivo(agd):
    """3b: rechazo sin motivo no se permite; con motivo queda rechazada y ya no cambia"""
    cliente, visita, _ = agd
    v = _visita(cliente, visita)
    r = cliente.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'rechazar'}, format='json')
    assert r.status_code == 422
    r = cliente.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'rechazar', 'motivo': 'Sin cupo ese día'}, format='json')
    assert (r.status_code, r.data['estado']) == (200, 'rechazada')
    assert cliente.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'aprobar'}, format='json').status_code == 400


def test_agd_03_solo_aprobada_recibe_pase(agd):
    """Paso 4: una visita solicitada no recibe pase"""
    cliente, visita, _ = agd
    v = _visita(cliente, visita)
    r = cliente.post(f"/api/v1/agenda/visitas/{v['id']}/pase/")
    assert r.status_code == 422
    assert 'aprobada' in r.data['detalle']


@pytest.mark.skip(reason='AGD-04: por construir')
def test_agd_04_registrar_entradas_salidas_porteria_flujo_principal():
    """AGD-04 · Registrar entradas y salidas en portería"""


@pytest.mark.skip(reason='AGD-05: por construir')
def test_agd_05_consultar_quien_esta_finca_flujo_principal():
    """AGD-05 · Consultar quién está en la finca"""


@pytest.mark.skip(reason='AGD-06: por construir')
def test_agd_06_consultar_agenda_dia_flujo_principal():
    """AGD-06 · Consultar la agenda del día"""
