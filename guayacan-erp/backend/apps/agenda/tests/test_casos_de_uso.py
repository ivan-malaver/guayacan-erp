"""Pruebas de aceptación de los casos de uso de agenda.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import hashlib
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone
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


@pytest.fixture
def porteria(agd):
    """Una visita aprobada para dentro de 10 minutos (con su pase) y un trabajador con carné QR vigente."""
    cliente, visita, _ = agd
    ahora = timezone.now()
    visita = {**visita, 'ingreso_programado': (ahora + timedelta(minutes=10)).isoformat(),
              'salida_programada': (ahora + timedelta(hours=3)).isoformat()}

    def aprobada(**cambios):
        v = _visita(cliente, {**visita, **cambios})
        assert cliente.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'aprobar'}, format='json').status_code == 200
        return v['id'], cliente.post(f"/api/v1/agenda/visitas/{v['id']}/pase/").data['codigo_pase']

    with connection.cursor() as cur:
        cur.execute("insert into terceros.tercero (tipo_persona, tipo_documento, numero_documento, nombres) "
                    "values ('natural', 'CC', 'PRB-0001', 'Operario de prueba') returning id")
        cur.execute("insert into terceros.empleado (tercero_id, cargo, tipo_vinculacion, fecha_ingreso) "
                    "values (%s, 'Operario', 'jornal', '2026-01-01') returning id", [cur.fetchone()[0]])
        empleado_id = cur.fetchone()[0]
        cur.execute("insert into personal.credencial_trabajo (empleado_id, tipo, codigo_hash, emitida_en) values (%s, 'qr', %s, '2026-01-01')",
                    [empleado_id, hashlib.sha256(b'CARNE-PRB-1').hexdigest()])
    return cliente, aprobada, empleado_id


def _acceso(cliente, **datos):
    return cliente.post('/api/v1/agenda/registros-acceso/', {'tipo': 'persona', **datos}, format='json')


def _jornadas(empleado_id):
    with connection.cursor() as cur:
        cur.execute('select metodo_registro, salida is not null from personal.jornada where empleado_id = %s', [empleado_id])
        return cur.fetchall()


def test_agd_04_registrar_entradas_salidas_porteria_flujo_principal(porteria):
    """AGD-04 · El portero escanea el pase: la visita entra (en_sitio) y sale (salio)"""
    cliente, aprobada, _ = porteria
    visita_id, codigo = aprobada()
    r = _acceso(cliente, sentido='entrada', codigo_pase=codigo)
    assert r.status_code == 201, r.data
    assert (r.data['visita'], r.data['metodo']) == (visita_id, 'pase_qr')
    assert cliente.get(f'/api/v1/agenda/visitas/{visita_id}/').data['estado'] == 'en_sitio'
    assert _acceso(cliente, sentido='salida', codigo_pase=codigo).status_code == 201
    assert cliente.get(f'/api/v1/agenda/visitas/{visita_id}/').data['estado'] == 'salio'


def test_agd_04_carne_abre_y_cierra_una_sola_jornada(porteria):
    """El carné abre la jornada al entrar y la cierra al salir; escanear dos veces no crea otra jornada"""
    cliente, _, empleado_id = porteria
    # En la prueba todo corre en una transacción (misma hora): la entrada se registra 8 horas antes
    temprano = (timezone.now() - timedelta(hours=8)).isoformat()
    r = _acceso(cliente, sentido='entrada', codigo_carne='CARNE-PRB-1', ocurrido_en=temprano)
    assert (r.status_code, r.data['empleado'], r.data['metodo']) == (201, empleado_id, 'carne_qr')
    assert _acceso(cliente, sentido='entrada', codigo_carne='CARNE-PRB-1', ocurrido_en=temprano).status_code == 201
    assert _jornadas(empleado_id) == [('qr', False)]
    r = _acceso(cliente, sentido='salida', codigo_carne='CARNE-PRB-1')
    assert r.status_code == 201, r.data
    assert _jornadas(empleado_id) == [('qr', True)]


def test_agd_04_carne_revocado_no_entra(porteria):
    """Un carné revocado no identifica a nadie"""
    cliente, _, _ = porteria
    with connection.cursor() as cur:
        cur.execute('update personal.credencial_trabajo set revocada_en = now() where codigo_hash = %s',
                    [hashlib.sha256(b'CARNE-PRB-1').hexdigest()])
    r = _acceso(cliente, sentido='entrada', codigo_carne='CARNE-PRB-1')
    assert r.status_code == 400
    assert 'codigo_carne' in r.data


def test_agd_04_placa_distinta_responde_422(porteria):
    """3a: la placa no corresponde a la visita programada"""
    cliente, aprobada, _ = porteria
    _, codigo = aprobada(vehiculo_placa='ABC123', vehiculo_tipo='carro')
    r = _acceso(cliente, sentido='entrada', tipo='vehiculo', placa='XYZ999', codigo_pase=codigo)
    assert r.status_code == 422
    assert 'no corresponde' in r.data['detalle']


def test_agd_04_galpon_sin_desinfeccion_responde_422(porteria):
    """3c: al galpón sin desinfección no se entra"""
    cliente, aprobada, _ = porteria
    _, codigo = aprobada(requiere_bioseguridad=True, contacto_aves_reciente=False)
    r = _acceso(cliente, sentido='entrada', codigo_pase=codigo)
    assert r.status_code == 422
    assert 'Bioseguridad' in r.data['detalle']
    assert _acceso(cliente, sentido='entrada', codigo_pase=codigo, desinfeccion=True).status_code == 201


def test_agd_04_salida_sin_entrada_responde_422(porteria):
    """4a: salida de alguien que no entró hoy"""
    cliente, _, empleado_id = porteria
    assert _acceso(cliente, sentido='salida', nombre='Desconocido').status_code == 422
    assert _acceso(cliente, sentido='salida', empleado=empleado_id).status_code == 422


def test_agd_04_correccion_es_un_registro_nuevo(porteria):
    """4b: no se edita; la corrección es un registro nuevo con observación que dice cuál corrige"""
    cliente, _, _ = porteria
    malo = _acceso(cliente, sentido='entrada', tipo='vehiculo', placa='ABC12').data
    assert cliente.patch(f"/api/v1/agenda/registros-acceso/{malo['id']}/", {'placa': 'ABC123'}, format='json').status_code == 405
    assert _acceso(cliente, sentido='entrada', tipo='vehiculo', placa='ABC123', corrige=malo['id']).status_code == 400
    r = _acceso(cliente, sentido='entrada', tipo='vehiculo', placa='ABC123', corrige=malo['id'], observacion='Placa mal digitada')
    assert (r.status_code, r.data['corrige'], r.data['metodo']) == (201, malo['id'], 'lectura_placa')


def test_agd_04_jornada_no_se_crea_por_el_crud(agd):
    """La jornada solo nace en portería: el CRUD de jornadas no acepta POST"""
    cliente, _, _ = agd
    assert cliente.post('/api/v1/personal/jornadas/', {}, format='json').status_code == 405


@pytest.mark.skip(reason='AGD-05: por construir')
def test_agd_05_consultar_quien_esta_finca_flujo_principal():
    """AGD-05 · Consultar quién está en la finca"""


@pytest.mark.skip(reason='AGD-06: por construir')
def test_agd_06_consultar_agenda_dia_flujo_principal():
    """AGD-06 · Consultar la agenda del día"""
