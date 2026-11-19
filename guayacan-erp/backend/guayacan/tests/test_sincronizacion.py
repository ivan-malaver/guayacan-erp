"""NUC-05 · Sincronización sin conexión: crear registros y cambiar los que ya existen (iniciar y terminar tareas)."""
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from guayacan.autenticacion import emitir_tokens


@pytest.fixture
def campo(en_finca):
    """Con conexión: el encargado crea una tarea de hoy con un paso. Devuelve el cliente, la tarea y el paso."""
    with connection.cursor() as cur:
        cur.execute('select u.id, f.predio_id from nucleo.usuario u cross join lateral nucleo.predios_del_usuario(u.id) f order by 2, 1 limit 1')
        usuario_id, predio_id = cur.fetchone()
    en_finca(predio=predio_id, usuario=usuario_id)
    cliente = APIClient()
    tokens = emitir_tokens(get_user_model().objects.get(pk=usuario_id), predio_id)
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['acceso']}")
    tarea = cliente.post('/api/v1/personal/tareas/', {'titulo': 'Recoger huevos', 'fecha': timezone.localdate().isoformat(),
                         'prioridad': 'media', 'origen': 'manual', 'estado': 'pendiente'}, format='json').data['id']
    r = cliente.post(f'/api/v1/personal/tareas/{tarea}/pasos/', {'tarea': tarea, 'orden': 1, 'descripcion': 'Desinfectar botas',
                     'hecho': False}, format='json')
    assert r.status_code == 201, r.data
    return cliente, tarea, r.data['id']


def _registro(tabla, hora, datos, id=None):
    r = {'tabla': tabla, 'id_cliente': str(uuid.uuid4()), 'capturado_en': hora.isoformat(), 'datos': datos}
    return {**r, 'operacion': 'actualizar', 'id': id} if id else r


def _sincronizar(cliente, registros):
    r = cliente.post('/api/v1/sincronizacion/lote/', {'registros': registros}, format='json')
    assert r.status_code == 200, r.data
    return r.data['resultados']


def _fila(sql, *params):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def test_iniciar_marcar_y_terminar_sin_conexion(campo):
    """La tarea se creó con conexión; sin señal se inicia, se marca el paso, se deja evidencia y se termina.
    Todo llega desordenado en un lote: se aplica en el orden del campo y con las horas del celular."""
    cliente, tarea, paso = campo
    t1, t2, t3 = (timezone.now() - timedelta(hours=h) for h in (3, 2, 1))
    lote = [
        _registro('personal.tarea', t3, {'estado': 'terminada', 'cantidad': 380}, id=tarea),
        _registro('personal.paso_tarea', t2, {'hecho': True}, id=paso),
        _registro('personal.evidencia_tarea', t2, {'tarea': tarea, 'tipo': 'foto', 'archivo_url': 'https://minio.local/e/1.jpg'}),
        _registro('personal.tarea', t1, {'estado': 'en_curso'}, id=tarea),
    ]
    resultados = _sincronizar(cliente, lote)
    assert [r['estado'] for r in resultados] == ['actualizado', 'actualizado', 'creado', 'actualizado']
    assert _fila('select estado, cantidad, iniciada_en = %s, terminada_en = %s from personal.tarea where id = %s',
                 t1, t3, tarea) == ('terminada', 380, True, True)
    assert _fila('select hecho, hecho_en = %s from personal.paso_tarea where id = %s', t2, paso) == (True, True)
    # Reenviar el mismo lote no repite ni deshace nada
    assert sorted(r['estado'] for r in _sincronizar(cliente, lote)) == ['obsoleto', 'obsoleto', 'obsoleto', 'repetido']
    assert _fila('select estado from personal.tarea where id = %s', tarea) == ('terminada',)


def test_un_cambio_viejo_no_pisa_uno_nuevo(campo):
    """Si el «iniciar» llega en un lote posterior al «terminar», no devuelve la tarea a en curso"""
    cliente, tarea, _ = campo
    ahora = timezone.now()
    assert _sincronizar(cliente, [_registro('personal.tarea', ahora - timedelta(hours=2), {'estado': 'en_curso'}, id=tarea),
                                  _registro('personal.tarea', ahora - timedelta(hours=1), {'estado': 'terminada'}, id=tarea)])
    viejo = _sincronizar(cliente, [_registro('personal.tarea', ahora - timedelta(hours=3), {'estado': 'en_curso'}, id=tarea)])
    assert viejo[0]['estado'] == 'obsoleto'
    assert _fila('select estado from personal.tarea where id = %s', tarea) == ('terminada',)


def test_sin_conexion_solo_se_cambia_lo_del_trabajador(campo):
    """Ni quién aprobó ni los estados del aprobador: solo estado en_curso o terminada, cantidad y pasos"""
    cliente, tarea, _ = campo
    hora = timezone.now() - timedelta(minutes=30)
    r = _sincronizar(cliente, [_registro('personal.tarea', hora, {'aprobado_por': 1}, id=tarea)])[0]
    assert (r['estado'], 'aprobado_por' in r['detalle']) == ('rechazado', True)
    r = _sincronizar(cliente, [_registro('personal.tarea', hora, {'estado': 'aprobada'}, id=tarea)])[0]
    assert r['estado'] == 'rechazado'
    r = _sincronizar(cliente, [_registro('agenda.registro_acceso', hora, {'placa': 'ABC123'}, id=1)])[0]
    assert r['detalle'] == 'Esta tabla no admite cambios sin conexión'


def test_paso_de_tarea_no_iniciada_lo_rechaza_la_base(campo):
    """Migración 004: un paso solo se marca si la tarea está en curso, también sin conexión"""
    cliente, _, paso = campo
    r = _sincronizar(cliente, [_registro('personal.paso_tarea', timezone.now() - timedelta(minutes=5), {'hecho': True}, id=paso)])[0]
    assert r['estado'] == 'rechazado'
    assert 'en curso' in r['detalle']


def test_hora_del_celular_en_el_futuro_se_rechaza(campo):
    """Un reloj en el futuro ganaría siempre «el más reciente»: se rechaza"""
    cliente, tarea, _ = campo
    r = _sincronizar(cliente, [_registro('personal.tarea', timezone.now() + timedelta(hours=2), {'estado': 'en_curso'}, id=tarea)])[0]
    assert (r['estado'], r['detalle']) == ('rechazado', 'La hora del celular está en el futuro')
