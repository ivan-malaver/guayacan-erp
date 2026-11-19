"""Pruebas de aceptación de los casos de uso de produccion.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import json

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

from guayacan.autenticacion import emitir_tokens


@pytest.fixture
def api(en_finca):
    """Cliente con token de un usuario de la finca y un lote de gallinas listo para enviar.
    Todo corre en la transacción de la prueba y se deshace al final."""
    with connection.cursor() as cur:
        cur.execute('select u.id, f.predio_id from nucleo.usuario u cross join lateral nucleo.predios_del_usuario(u.id) f order by 2, 1 limit 1')
        usuario_id, predio_id = cur.fetchone()
    en_finca(predio=predio_id, usuario=usuario_id)
    with connection.cursor() as cur:
        cur.execute("select id from produccion.especie where codigo = 'gallina'")
        gallina = cur.fetchone()[0]
        cur.execute('select id from nucleo.zona order by id limit 1')
        zona = cur.fetchone()[0]
    cliente = APIClient()
    tokens = emitir_tokens(get_user_model().objects.get(pk=usuario_id), predio_id)
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['acceso']}")
    lote = {'codigo': 'PRB-AV-01', 'especie': gallina, 'zona': zona, 'proposito': 'postura',
            'fecha_ingreso': '2026-11-01', 'cantidad_inicial': 50}
    return cliente, lote, predio_id


def _evento(lote_id):
    with connection.cursor() as cur:
        cur.execute("select carga from nucleo.evento_salida where tipo_evento = 'produccion.lote_ingresado' and entidad_id = %s", [lote_id])
        # Django deja el jsonb como texto en los cursores crudos
        return json.loads(cur.fetchone()[0])


def test_pro_01_registrar_ingreso_lote_animales_flujo_principal(api):
    """PRO-01 · Registrar el ingreso de un lote de animales: queda activo, con cantidad actual = inicial y avisa por el outbox"""
    cliente, lote, predio_id = api
    r = cliente.post('/api/v1/produccion/lotes-animal/', lote, format='json')
    assert r.status_code == 201, r.data
    assert r.data['predio'] == predio_id  # la finca la puso la base, no el cliente
    assert r.data['estado'] == 'activo'
    assert r.data['cantidad_actual'] == 50
    assert _evento(r.data['id'])['cantidad'] == 50


def test_pro_01_alerta_granja_biosegura_desde_200_aves(api):
    """Paso 4: con 200 aves de postura o más sin certificado ICA, el evento lleva la alerta de granja biosegura"""
    cliente, lote, _ = api
    with connection.cursor() as cur:
        cur.execute("select x.estado from cumplimiento.expediente x join cumplimiento.norma n on n.id = x.norma_id where n.codigo = 'ICA_GAB'")
        if (cur.fetchone() or [''])[0] == 'certificado':
            pytest.skip('la finca de prueba ya tiene el certificado ICA')
    r = cliente.post('/api/v1/produccion/lotes-animal/', {**lote, 'cantidad_inicial': 250}, format='json')
    assert r.status_code == 201, r.data
    assert _evento(r.data['id'])['granja_biosegura'].startswith('alerta')


def test_pro_01_especie_inexistente_no_crea_lote(api):
    """Flujo alterno: la especie debe estar en el catálogo (precondición)"""
    cliente, lote, _ = api
    r = cliente.post('/api/v1/produccion/lotes-animal/', {**lote, 'especie': 999999}, format='json')
    assert r.status_code in (400, 409, 422)


@pytest.mark.skip(reason='PRO-02: por construir')
def test_pro_02_registrar_postura_diaria_clasificar_huevo_flujo_principal():
    """PRO-02 · Registrar la postura diaria y clasificar el huevo"""


@pytest.mark.skip(reason='PRO-03: por construir')
def test_pro_03_registrar_alimentacion_pesajes_eventos_sanitarios_flujo_principal():
    """PRO-03 · Registrar alimentación, pesajes y eventos sanitarios"""


@pytest.mark.skip(reason='PRO-04: por construir')
def test_pro_04_registrar_eventos_reproductivos_ovinos_caprinos_flujo_principal():
    """PRO-04 · Registrar eventos reproductivos de ovinos y caprinos"""


@pytest.mark.skip(reason='PRO-05: por construir')
def test_pro_05_registrar_siembra_labores_culturales_flujo_principal():
    """PRO-05 · Registrar una siembra y sus labores culturales"""


@pytest.mark.skip(reason='PRO-06: por construir')
def test_pro_06_registrar_cosecha_destino_flujo_principal():
    """PRO-06 · Registrar una cosecha y su destino"""


@pytest.mark.skip(reason='PRO-07: por construir')
def test_pro_07_registrar_analisis_suelo_recomendacion_flujo_principal():
    """PRO-07 · Registrar un análisis de suelo y su recomendación"""


@pytest.mark.skip(reason='PRO-08: por construir')
def test_pro_08_registrar_bioseguridad_e_inocuidad_flujo_principal():
    """PRO-08 · Registrar bioseguridad e inocuidad"""


@pytest.mark.skip(reason='PRO-09: por construir')
def test_pro_09_producir_abono_lombricultivo_compostera_flujo_principal():
    """PRO-09 · Producir abono en lombricultivo o compostera"""


@pytest.mark.skip(reason='PRO-10: por construir')
def test_pro_10_medir_calidad_agua_estanques_flujo_principal():
    """PRO-10 · Medir la calidad del agua de los estanques"""
