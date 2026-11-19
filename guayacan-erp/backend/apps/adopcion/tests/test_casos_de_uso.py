"""Pruebas de aceptación de los casos de uso de adopcion.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

from guayacan.autenticacion import emitir_tokens
from guayacan.pasarela import PasarelaSimulada


@pytest.fixture
def ado_01(en_finca):
    """Cliente con token de un usuario de la finca, ids base y un interruptor para la función «adopcion».
    Todo corre en la transacción de la prueba y se deshace al final."""
    with connection.cursor() as cur:
        cur.execute('select u.id, f.predio_id from nucleo.usuario u cross join lateral nucleo.predios_del_usuario(u.id) f order by 2, 1 limit 1')
        usuario_id, predio_id = cur.fetchone()
    en_finca(predio=predio_id, usuario=usuario_id)
    with connection.cursor() as cur:
        cur.execute("select id from produccion.cultivo where codigo = 'aguacate'")
        cultivo = cur.fetchone()[0]
        cur.execute('select id from nucleo.zona order by id limit 1')
        zona = cur.fetchone()[0]

    def funcion(activa):
        # El apéndice A crea la fila solo en las fincas que existían al cargarlo: se asegura aquí
        with connection.cursor() as cur:
            cur.execute("insert into nucleo.funcionalidad (predio_id, codigo, descripcion, fase, activa) "
                        "values (nucleo.predio_actual(), 'adopcion', 'Adopción de árboles y animales por turistas (apéndice A)', 3, %s) "
                        "on conflict (predio_id, codigo) do update set activa = excluded.activa", [activa])

    cliente = APIClient()
    tokens = emitir_tokens(get_user_model().objects.get(pk=usuario_id), predio_id)
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['acceso']}")
    # garantia_meses, requiere_permiso, activo y estado tienen valor por defecto en la base, pero el serializer generado los exige
    plan = {'codigo': 'PRB-AGU', 'nombre': 'Aguacate (prueba)', 'tipo': 'frutal', 'cultivo': cultivo,
            'precio_compra': '150000', 'precio_readopcion': '60000', 'cuota_mensual': '25000', 'costo_bien': '45000',
            'costo_cuidado_mensual': '9000', 'meses_madurez': 48, 'garantia_meses': 12, 'requiere_permiso': 'ninguno', 'activo': True}
    sitio = {'zona': zona, 'codigo': 'PRB-HS-1', 'tipo': 'hoyo_siembra', 'estado': 'libre'}
    return cliente, funcion, plan, sitio, predio_id


def test_ado_01_configurar_catalogo_sitios_flujo_principal(ado_01):
    """ADO-01 · Configurar catálogo y sitios: con la función encendida se crean plan, sitio y bien en la finca de la sesión"""
    api, funcion, plan, sitio, predio_id = ado_01
    funcion(True)
    r = api.post('/api/v1/adopcion/planes/', plan, format='json')
    assert r.status_code == 201, r.data
    assert r.data['predio'] == predio_id  # la finca la puso la base, no el cliente
    plan_id = r.data['id']
    r = api.post('/api/v1/adopcion/sitios/', sitio, format='json')
    assert r.status_code == 201, r.data
    r = api.post('/api/v1/adopcion/bienes/', {'codigo': 'PRB-0001', 'plan': plan_id, 'sitio': r.data['id'], 'estado': 'disponible'}, format='json')
    assert r.status_code == 201, r.data
    assert r.data['estado'] == 'disponible'


def test_ado_01_funcion_apagada_responde_422(ado_01):
    """Flujo alterno: la función «adopcion» está apagada en la finca"""
    api, funcion, plan, _, _ = ado_01
    funcion(False)
    r = api.post('/api/v1/adopcion/planes/', plan, format='json')
    assert r.status_code == 422
    assert r.data['codigo'] == 'regla_negocio'


def test_ado_01_sitio_con_bien_vivo_responde_409(ado_01):
    """Flujo alterno: un sitio no puede tener dos bienes vivos (índice ux_bien_sitio_vivo de la base)"""
    api, funcion, plan, sitio, _ = ado_01
    funcion(True)
    plan_id = api.post('/api/v1/adopcion/planes/', plan, format='json').data['id']
    sitio_id = api.post('/api/v1/adopcion/sitios/', sitio, format='json').data['id']
    bien = {'plan': plan_id, 'sitio': sitio_id, 'estado': 'disponible'}
    assert api.post('/api/v1/adopcion/bienes/', {**bien, 'codigo': 'PRB-0001'}, format='json').status_code == 201
    r = api.post('/api/v1/adopcion/bienes/', {**bien, 'codigo': 'PRB-0002'}, format='json')
    assert r.status_code == 409
    assert r.data['codigo'] == 'duplicado'


def test_ado_01_precio_cero_responde_422(ado_01):
    """Flujo alterno: el precio de compra debe ser mayor que 0 (CHECK de la base)"""
    api, funcion, plan, _, _ = ado_01
    funcion(True)
    r = api.post('/api/v1/adopcion/planes/', {**plan, 'precio_compra': '0'}, format='json')
    assert r.status_code == 422
    assert r.data['codigo'] == 'valor_invalido'


@pytest.fixture
def ado_02(ado_01):
    """Un aguacate disponible (ADO-01) y la compra que envía el vendedor; el adoptante no tiene cuenta."""
    api, funcion, plan, sitio, predio_id = ado_01
    funcion(True)
    plan_id = api.post('/api/v1/adopcion/planes/', plan, format='json').data['id']
    sitio_id = api.post('/api/v1/adopcion/sitios/', sitio, format='json').data['id']
    bien_id = api.post('/api/v1/adopcion/bienes/', {'codigo': 'PRB-0001', 'plan': plan_id, 'sitio': sitio_id,
                       'estado': 'disponible'}, format='json').data['id']
    compra = {'bien': bien_id, 'modalidad_siembra': 'propia', 'autoriza_datos': True, 'version_politica': '2026-10',
              'medio_autorizacion': 'whatsapp', 'adoptante': {'tipo_documento': 'PAS', 'numero_documento': 'PRB123456',
                                                              'nombres': 'Anna', 'apellidos': 'Schmidt', 'correo': 'anna@example.com'}}
    return api, compra, bien_id


def _avisar(numero, predio_id, estado='aprobado', valor='150000.00', firma=None):
    """La pasarela simulada avisa el resultado del pago (sin sesión, con su firma)."""
    aviso = {'referencia': f'{predio_id}:{numero}', 'estado': estado, 'id_transaccion': f'SIM-{numero}', 'valor': valor}
    return APIClient().post('/api/v1/pagos/webhook/', aviso, format='json',
                            HTTP_X_PASARELA_FIRMA=firma or PasarelaSimulada().firmar(aviso))


def _fila(sql, *params):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def test_ado_02_comprar_arbol_animal_flujo_principal(ado_02):
    """ADO-02 · El contrato nace pendiente de pago con el bien libre; al aprobarse el pago se activa, el árbol queda
    reservado y se crean la factura ADO y el pago confirmado"""
    api, compra, bien_id = ado_02
    r = api.post('/api/v1/adopcion/contratos/compra/', compra, format='json')
    assert r.status_code == 201, r.data
    assert r.data['estado'] == 'pendiente_pago'
    assert r.data['cobro']['url_pago'].endswith(f"{r.data['predio']}:{r.data['numero']}")
    assert _fila('select estado from adopcion.bien where id = %s', bien_id) == ('disponible',)
    assert _fila("select count(*) from terceros.consentimiento_datos where tercero_id = %s and finalidad = 'atencion_pedidos'",
                 r.data['adoptante']) == (1,)
    a = _avisar(r.data['numero'], r.data['predio'])
    assert a.status_code == 200, a.data
    assert a.data['estado'] == 'activo'
    assert _fila('select estado from adopcion.bien where id = %s', bien_id) == ('reservado',)
    assert _fila("select f.total, f.saldo, f.estado_dian, p.estado, p.proveedor_pasarela from comercial.factura f "
                 "join comercial.pago p on p.factura_id = f.id where p.referencia = %s",
                 f"{r.data['predio']}:{r.data['numero']}") == (150000, 0, 'pendiente', 'confirmado', 'simulada')


def test_ado_02_sin_autorizacion_de_datos_no_registra_nada(ado_02):
    """Ley 1581: sin autorización expresa no se crea el tercero ni el contrato"""
    api, compra, _ = ado_02
    r = api.post('/api/v1/adopcion/contratos/compra/', {**compra, 'autoriza_datos': False}, format='json')
    assert r.status_code == 400
    assert _fila("select count(*) from terceros.tercero where numero_documento = 'PRB123456'") == (0,)


def test_ado_02_siembra_por_trabajador_exige_autorizar_seguimiento(ado_02):
    """El video de siembra necesita la autorización seguimiento_adopcion (regla de la base)"""
    api, compra, _ = ado_02
    r = api.post('/api/v1/adopcion/contratos/compra/', {**compra, 'modalidad_siembra': 'trabajador'}, format='json')
    assert r.status_code == 422
    assert 'seguimiento_adopcion' in r.data['detalle']
    r = api.post('/api/v1/adopcion/contratos/compra/', {**compra, 'modalidad_siembra': 'trabajador',
                 'autoriza_seguimiento': True}, format='json')
    assert r.status_code == 201, r.data


def test_ado_02_aviso_con_firma_falsa_responde_403(ado_02):
    """Nadie confirma un pago sin la firma de la pasarela"""
    api, compra, _ = ado_02
    r = api.post('/api/v1/adopcion/contratos/compra/', compra, format='json')
    a = _avisar(r.data['numero'], r.data['predio'], firma='falsa')
    assert a.status_code == 403
    assert _fila('select estado from adopcion.contrato where id = %s', r.data['id']) == ('pendiente_pago',)


def test_ado_02_pago_rechazado_queda_pendiente_sin_factura(ado_02):
    """El intento fallido queda como contrato pendiente_pago, sin factura y con el bien libre"""
    api, compra, bien_id = ado_02
    r = api.post('/api/v1/adopcion/contratos/compra/', compra, format='json')
    a = _avisar(r.data['numero'], r.data['predio'], estado='rechazado')
    assert (a.status_code, a.data['estado']) == (200, 'pendiente_pago')
    assert _fila('select estado from adopcion.bien where id = %s', bien_id) == ('disponible',)
    assert _fila('select count(*) from comercial.pago where referencia = %s', f"{r.data['predio']}:{r.data['numero']}") == (0,)


def test_ado_02_si_otro_pago_primero_se_cancela_y_se_devuelve(ado_02):
    """Dos compras del mismo árbol: gana el primer pago; el segundo cancela su contrato y pide devolver el dinero"""
    api, compra, _ = ado_02
    primero = api.post('/api/v1/adopcion/contratos/compra/', compra, format='json').data
    segundo = api.post('/api/v1/adopcion/contratos/compra/', {**compra, 'adoptante': {
        'tipo_documento': 'PAS', 'numero_documento': 'PRB654321', 'nombres': 'John'}}, format='json').data
    assert _avisar(primero['numero'], primero['predio']).data['estado'] == 'activo'
    a = _avisar(segundo['numero'], segundo['predio'])
    assert (a.status_code, a.data['estado']) == (200, 'cancelado')
    assert _fila("select count(*) from nucleo.evento_salida where tipo_evento = 'adopcion.pago_sin_bien' and entidad_id = %s",
                 segundo['id']) == (1,)


def test_ado_02_aviso_repetido_no_duplica_la_factura(ado_02):
    """La pasarela puede reenviar el aviso: la segunda vez no crea otra factura"""
    api, compra, _ = ado_02
    r = api.post('/api/v1/adopcion/contratos/compra/', compra, format='json')
    assert _avisar(r.data['numero'], r.data['predio']).status_code == 200
    assert _avisar(r.data['numero'], r.data['predio']).status_code == 200
    assert _fila('select count(*) from comercial.pago where referencia = %s', f"{r.data['predio']}:{r.data['numero']}") == (1,)


@pytest.mark.skip(reason='ADO-03: por construir')
def test_ado_03_sembrar_persona_flujo_principal():
    """ADO-03 · Sembrar en persona"""


@pytest.mark.skip(reason='ADO-04: por construir')
def test_ado_04_sembrar_trabajador_enviar_video_flujo_principal():
    """ADO-04 · Sembrar por un trabajador y enviar el video"""


@pytest.mark.skip(reason='ADO-05: por construir')
def test_ado_05_cobrar_pagar_cuota_mensual_flujo_principal():
    """ADO-05 · Cobrar y pagar la cuota mensual"""


@pytest.mark.skip(reason='ADO-06: por construir')
def test_ado_06_seguir_mi_arbol_mi_animal_flujo_principal():
    """ADO-06 · Seguir mi árbol o mi animal"""


@pytest.mark.skip(reason='ADO-07: por construir')
def test_ado_07_detectar_abandono_poner_readopcion_flujo_principal():
    """ADO-07 · Detectar abandono y poner en readopción"""


@pytest.mark.skip(reason='ADO-08: por construir')
def test_ado_08_readoptar_flujo_principal():
    """ADO-08 · Readoptar"""


@pytest.mark.skip(reason='ADO-09: por construir')
def test_ado_09_registrar_vender_productos_bien_flujo_principal():
    """ADO-09 · Registrar y vender productos del bien"""


@pytest.mark.skip(reason='ADO-10: por construir')
def test_ado_10_liquidar_productos_5_flujo_principal():
    """ADO-10 · Liquidar productos con el 5 %"""


@pytest.mark.skip(reason='ADO-11: por construir')
def test_ado_11_decidir_madurez_mantener_liquidar_flujo_principal():
    """ADO-11 · Decidir en la madurez: mantener o liquidar"""


@pytest.mark.skip(reason='ADO-12: por construir')
def test_ado_12_talar_sacrificar_liquidar_flujo_principal():
    """ADO-12 · Talar o sacrificar y liquidar"""


@pytest.mark.skip(reason='ADO-13: por construir')
def test_ado_13_reponer_bien_muerto_garantia_flujo_principal():
    """ADO-13 · Reponer un bien muerto en garantía"""


@pytest.mark.skip(reason='ADO-14: por construir')
def test_ado_14_ceder_regalar_adopcion_flujo_principal():
    """ADO-14 · Ceder o regalar la adopción"""


@pytest.mark.skip(reason='ADO-15: por construir')
def test_ado_15_consultar_tablero_adopcion_flujo_principal():
    """ADO-15 · Consultar el tablero de adopción"""
