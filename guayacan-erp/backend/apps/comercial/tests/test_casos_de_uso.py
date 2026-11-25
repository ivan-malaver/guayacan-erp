"""Pruebas de aceptación de los casos de uso de comercial.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

from guayacan.autenticacion import emitir_tokens


@pytest.mark.skip(reason='VTA-01: por construir')
def test_vta_01_gestionar_listas_precios_vigencia_flujo_principal():
    """VTA-01 · Gestionar listas y precios con vigencia"""


@pytest.mark.skip(reason='VTA-02: por construir')
def test_vta_02_proponer_aprobar_cambio_precio_flujo_principal():
    """VTA-02 · Proponer y aprobar un cambio de precio"""


def _fila(sql, *params):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _api(rol, correo, predio):
    """Cliente de API de una persona nueva con ese rol en la finca."""
    usuario = _fila("insert into nucleo.usuario (nombre_completo, correo, contrasena_hash) values ('Prueba VTA-03', %s, 'x') "
                    "returning id", correo)[0]
    _fila("insert into nucleo.usuario_rol (usuario_id, rol_id) select %s, id from nucleo.rol where codigo = %s returning id", usuario, rol)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {emitir_tokens(get_user_model().objects.get(pk=usuario), predio)['acceso']}")
    return c


@pytest.fixture
def vta_03(en_finca):
    """Un vendedor, un cliente sin lista propia (usa PUBLICO) y 90 huevos HUE-AA-30 en dos lotes: 50 que vencen en 7
    días y 40 que vencen en 20. Fechas relativas a hoy, para que la prueba no caduque."""
    usuario_id, predio_id = _fila('select u.id, f.predio_id from nucleo.usuario u cross join lateral nucleo.predios_del_usuario(u.id) f '
                                  'order by 2, 1 limit 1')
    en_finca(predio=predio_id, usuario=usuario_id)
    producto, precio = _fila("select p.id, pp.precio_unitario from inventario.producto p join comercial.precio_producto pp "
                             "on pp.producto_id = p.id and pp.vigente_hasta is null join comercial.lista_precios l "
                             "on l.id = pp.lista_precios_id and l.codigo = 'PUBLICO' where p.sku = 'HUE-AA-30'")
    if _fila('select count(*) from inventario.lote_inventario l where l.producto_id = %s and inventario.puede_venderse(l)', producto)[0]:
        pytest.skip('La base local ya tiene huevos vendibles: el orden FEFO esperado no sería el de esta prueba')
    tercero = _fila("insert into terceros.tercero (tipo_persona, nombres, es_cliente) values ('natural', 'Cliente VTA-03', true) returning id")[0]
    cliente = _fila("insert into terceros.cliente (tercero_id, segmento) values (%s, 'tienda') returning id", tercero)[0]
    lotes = {}
    for codigo, edad, cantidad in (('PRB-HUE-A', 14, 50), ('PRB-HUE-B', 1, 40)):
        lotes[codigo] = _fila("insert into inventario.lote_inventario (producto_id, bodega_id, codigo_lote, origen, fecha_produccion, "
                              "cantidad_inicial, costo_unitario) values (%s, (select min(id) from inventario.bodega), %s, 'produccion', "
                              "current_date - %s, %s, 300) returning id", producto, codigo, edad, cantidad)[0]
    vendedor = _api('vendedor', 'vendedor-vta03@prueba.local', predio_id)
    pedido = vendedor.post('/api/v1/comercial/pedidos/', {'cliente': cliente, 'canal': 'whatsapp', 'numero': 'X-1', 'total': 1},
                           format='json')
    assert pedido.status_code == 201, pedido.data
    return vendedor, pedido.data, producto, precio, lotes, predio_id


def _linea(api, pedido, producto, cantidad):
    return api.post(f"/api/v1/comercial/pedidos/{pedido['id']}/lineas/", {'producto': producto, 'cantidad': cantidad}, format='json')


def _confirmar(api, pedido):
    return api.post(f"/api/v1/comercial/pedidos/{pedido['id']}/confirmar/")


def _reservas(pedido_id):
    with connection.cursor() as cur:
        cur.execute('select l.codigo_lote, r.cantidad, r.estado from comercial.reserva_lote r join comercial.pedido_detalle d '
                    'on d.id = r.pedido_detalle_id join inventario.lote_inventario l on l.id = r.lote_inventario_id '
                    'where d.pedido_id = %s order by r.id', [pedido_id])
        return [(c, int(q), e) for c, q, e in cur.fetchall()]


def test_vta_03_tomar_confirmar_pedido_flujo_principal(vta_03):
    """VTA-03 · Tomar y confirmar un pedido: nace en borrador como PED-<id> (el número y el total enviados se ignoran),
    la línea toma el precio vigente y al confirmar reserva por FEFO (50 del lote que vence antes y 10 del siguiente),
    congela el total y avisa por el outbox"""
    vendedor, pedido, producto, precio, _, _ = vta_03
    assert (pedido['numero'], pedido['estado'], Decimal(pedido['total'])) == (f"PED-{pedido['id']}", 'borrador', 0)
    linea = _linea(vendedor, pedido, producto, 60)
    assert linea.status_code == 201, linea.data
    assert Decimal(linea.data['precio_unitario']) == precio
    assert Decimal(linea.data['total_linea']) == 60 * precio
    r = _confirmar(vendedor, pedido)
    assert r.status_code == 200, r.data
    assert r.data['estado'] == 'confirmado'
    assert Decimal(r.data['total']) == 60 * precio
    assert _reservas(pedido['id']) == [('PRB-HUE-A', 50, 'reservada'), ('PRB-HUE-B', 10, 'reservada')]
    assert _fila("select count(*) from nucleo.evento_salida where tipo_evento = 'pedido.confirmado' and entidad_id = %s", pedido['id'])[0] == 1


def test_vta_03_inventario_insuficiente_no_deja_reservas(vta_03):
    """4a: con 90 vendibles no se confirman 100; el pedido sigue en borrador y no queda ninguna reserva a medias"""
    vendedor, pedido, producto, _, _, _ = vta_03
    _linea(vendedor, pedido, producto, 100)
    r = _confirmar(vendedor, pedido)
    assert (r.status_code, r.data['codigo']) == (422, 'regla_negocio')
    assert 'Inventario insuficiente' in r.data['detalle'] and 'faltan 10' in r.data['detalle']
    assert _reservas(pedido['id']) == []
    assert vendedor.get(f"/api/v1/comercial/pedidos/{pedido['id']}/").data['estado'] == 'borrador'


def test_vta_03_precio_cambiado_se_actualiza_editando_la_linea(vta_03):
    """4b: si el precio cambió después de tomar la línea, la base pide actualizarla; al editarla toma el precio nuevo"""
    vendedor, pedido, producto, precio, _, _ = vta_03
    linea = _linea(vendedor, pedido, producto, 10).data
    _fila("update comercial.precio_producto set vigente_hasta = now() where producto_id = %s and vigente_hasta is null "
          "returning id", producto)
    _fila("insert into comercial.precio_producto (lista_precios_id, producto_id, precio_unitario, vigente_desde, aprobado_por) "
          "select id, %s, %s, now(), nucleo.usuario_actual() from comercial.lista_precios where codigo = 'PUBLICO' returning id", producto, precio + 500)
    r = _confirmar(vendedor, pedido)
    assert r.status_code == 422 and 'antes de confirmar' in r.data['detalle']  # sin tildes: la base local las tiene dañadas
    e = vendedor.patch(f"/api/v1/comercial/pedidos/{pedido['id']}/lineas/{linea['id']}/", {'cantidad': 10}, format='json')
    assert e.status_code == 200, e.data
    assert Decimal(e.data['precio_unitario']) == precio + 500
    assert _confirmar(vendedor, pedido).status_code == 200


def test_vta_03_pedido_confirmado_no_se_cambia_ni_se_reconfirma(vta_03):
    """4c: confirmado, no se confirma otra vez ni se le agregan líneas ni se cambian sus datos"""
    vendedor, pedido, producto, _, _, _ = vta_03
    _linea(vendedor, pedido, producto, 5)
    assert _confirmar(vendedor, pedido).status_code == 200
    r = _confirmar(vendedor, pedido)
    assert r.status_code == 422 and 'no se puede confirmar' in r.data['detalle']
    assert _linea(vendedor, pedido, producto, 5).status_code == 400
    assert vendedor.patch(f"/api/v1/comercial/pedidos/{pedido['id']}/", {'canal': 'web'}, format='json').status_code == 400


def test_vta_03_cancelar_antes_de_despachar_libera_reservas(vta_03):
    """5a: al cancelar un pedido confirmado se liberan las reservas y el lote vuelve a tener sus 50 disponibles"""
    vendedor, pedido, producto, _, lotes, _ = vta_03
    _linea(vendedor, pedido, producto, 60)
    _confirmar(vendedor, pedido)
    r = vendedor.post(f"/api/v1/comercial/pedidos/{pedido['id']}/cancelar/")
    assert r.status_code == 200, r.data
    assert r.data['estado'] == 'cancelado'
    assert _reservas(pedido['id']) == [('PRB-HUE-A', 50, 'liberada'), ('PRB-HUE-B', 10, 'liberada')]
    assert _fila('select cantidad_disponible from inventario.lote_inventario where id = %s', lotes['PRB-HUE-A'])[0] == 50


def test_vta_03_sin_permiso_no_confirma(vta_03):
    """Confirmar y cancelar exigen comercial.confirmar_pedido (vendedor o administrador): el rol cliente recibe 403"""
    vendedor, pedido, producto, _, _, predio = vta_03
    _linea(vendedor, pedido, producto, 5)
    otro = _api('cliente', 'cliente-vta03@prueba.local', predio)
    assert _confirmar(otro, pedido).status_code == 403
    assert otro.post(f"/api/v1/comercial/pedidos/{pedido['id']}/cancelar/").status_code == 403


@pytest.mark.skip(reason='VTA-04: por construir')
def test_vta_04_vender_finca_feria_sin_conexion_flujo_principal():
    """VTA-04 · Vender en la finca o en la feria sin conexión"""


@pytest.mark.skip(reason='VTA-05: por construir')
def test_vta_05_despachar_entregar_pedido_flujo_principal():
    """VTA-05 · Despachar y entregar un pedido"""


@pytest.mark.skip(reason='VTA-06: por construir')
def test_vta_06_facturar_electronicamente_flujo_principal():
    """VTA-06 · Facturar electrónicamente"""


@pytest.mark.skip(reason='VTA-07: por construir')
def test_vta_07_registrar_confirmar_pago_flujo_principal():
    """VTA-07 · Registrar y confirmar un pago"""


@pytest.mark.skip(reason='VTA-08: por construir')
def test_vta_08_vender_credito_controlar_cartera_flujo_principal():
    """VTA-08 · Vender a crédito y controlar la cartera"""


@pytest.mark.skip(reason='VTA-09: por construir')
def test_vta_09_generar_pedidos_recurrentes_flujo_principal():
    """VTA-09 · Generar pedidos recurrentes"""


@pytest.mark.skip(reason='VTA-10: por construir')
def test_vta_10_registrar_permuta_flujo_principal():
    """VTA-10 · Registrar una permuta"""


@pytest.mark.skip(reason='VTA-11: por construir')
def test_vta_11_consultar_trazabilidad_lote_flujo_principal():
    """VTA-11 · Consultar la trazabilidad de un lote"""


@pytest.mark.skip(reason='VTA-12: por construir')
def test_vta_12_retirar_lote_mercado_flujo_principal():
    """VTA-12 · Retirar un lote del mercado"""
