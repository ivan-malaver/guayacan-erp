"""Pruebas de aceptación de los casos de uso de produccion.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import json
from decimal import Decimal

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


def _evento(entidad_id, tipo='produccion.lote_ingresado'):
    with connection.cursor() as cur:
        cur.execute('select carga from nucleo.evento_salida where tipo_evento = %s and entidad_id = %s', [tipo, entidad_id])
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


@pytest.fixture
def postura(api):
    """Un lote de 100 gallinas ya registrado (PRO-01), el usuario de la sesión, las categorías por código y una postura base."""
    cliente, lote, _ = api
    with connection.cursor() as cur:
        cur.execute('select nucleo.usuario_actual()')
        usuario_id = cur.fetchone()[0]
        cur.execute('select codigo, id from produccion.categoria_huevo')
        categorias = dict(cur.fetchall())
    lote_id = cliente.post('/api/v1/produccion/lotes-animal/', {**lote, 'cantidad_inicial': 100}, format='json').data['id']
    base = {'lote_animal': lote_id, 'fecha': '2026-11-18', 'huevos_recogidos': 100, 'huevos_rotos': 4}
    return cliente, base, usuario_id, categorias


def _clasificacion(registro_id):
    with connection.cursor() as cur:
        cur.execute('select c.codigo, p.cantidad, p.metodo from produccion.clasificacion_postura p '
                    'join produccion.categoria_huevo c on c.id = p.categoria_huevo_id where p.registro_postura_id = %s', [registro_id])
        return {codigo: (cantidad, metodo) for codigo, cantidad, metodo in cur.fetchall()}


def test_pro_02_registrar_postura_diaria_clasificar_huevo_flujo_principal(postura):
    """PRO-02 · Registrar la postura diaria y clasificar el huevo: registro, clasificación manual, quién registró y evento"""
    cliente, base, usuario_id, cat = postura
    r = cliente.post('/api/v1/produccion/registros-postura/', {**base, 'clasificacion': [
        {'categoria_huevo': cat['aaa'], 'cantidad': 50}, {'categoria_huevo': cat['aa'], 'cantidad': 46}]}, format='json')
    assert r.status_code == 201, r.data
    assert r.data['registrado_por'] == usuario_id  # lo puso el servicio con el usuario del token
    assert _clasificacion(r.data['id']) == {'aaa': (50, 'manual'), 'aa': (46, 'manual')}
    assert _evento(r.data['id'], 'produccion.postura_registrada')['postura_por_ave'] == 1.0  # 100 huevos / 100 gallinas


def test_pro_02_ignora_registrado_por_del_cliente(postura):
    """Nadie registra a nombre de otro: el registrado_por que envía el cliente se ignora"""
    cliente, base, usuario_id, _ = postura
    with connection.cursor() as cur:
        cur.execute('select id from nucleo.usuario where id <> %s limit 1', [usuario_id])
        otro = cur.fetchone()
    if not otro:
        pytest.skip('la base de prueba solo tiene un usuario')
    r = cliente.post('/api/v1/produccion/registros-postura/', {**base, 'registrado_por': otro[0]}, format='json')
    assert r.status_code == 201, r.data
    assert r.data['registrado_por'] == usuario_id


def test_pro_02_clasificacion_por_peso_de_bascula(postura):
    """3a: cada peso se convierte en categoría con los rangos vigentes (68 g = AAA)"""
    cliente, base, _, _ = postura
    r = cliente.post('/api/v1/produccion/registros-postura/', {**base, 'pesos_g': [68, 59.9, 80, 68]}, format='json')
    assert r.status_code == 201, r.data
    assert _clasificacion(r.data['id']) == {'aaa': (2, 'peso_bascula'), 'a': (1, 'peso_bascula'), 'jumbo': (1, 'peso_bascula')}


def test_pro_02_clasificacion_mayor_que_los_buenos_no_guarda_nada(postura):
    """3b: «La clasificación suma N huevos y solo hay M buenos»; tampoco queda el registro a medias"""
    cliente, base, _, cat = postura
    r = cliente.post('/api/v1/produccion/registros-postura/', {**base, 'clasificacion': [{'categoria_huevo': cat['aaa'], 'cantidad': 97}]}, format='json')
    assert r.status_code == 422
    assert 'solo hay 96 buenos' in r.data['detalle']
    with connection.cursor() as cur:
        cur.execute('select count(*) from produccion.registro_postura where lote_animal_id = %s', [base['lote_animal']])
        assert cur.fetchone()[0] == 0


def test_pro_02_vision_con_funcion_apagada_responde_422(postura):
    """3c: el método visión espera su equipo («La función vision_artificial no está activa»)"""
    cliente, base, _, cat = postura
    with connection.cursor() as cur:
        cur.execute("select nucleo.funcion_activa('vision_artificial')")
        if cur.fetchone()[0]:
            pytest.skip('la finca de prueba tiene la visión artificial encendida')
    r = cliente.post('/api/v1/produccion/registros-postura/', {**base, 'clasificacion': [
        {'categoria_huevo': cat['aaa'], 'cantidad': 10, 'metodo': 'vision'}]}, format='json')
    assert r.status_code == 422
    assert 'vision_artificial' in r.data['detalle']


def test_pro_02_mismo_lote_y_dia_responde_409(postura):
    """4a: ya hay registro de ese lote y día; se corrige el existente"""
    cliente, base, _, _ = postura
    assert cliente.post('/api/v1/produccion/registros-postura/', base, format='json').status_code == 201
    r = cliente.post('/api/v1/produccion/registros-postura/', base, format='json')
    assert r.status_code == 409
    assert r.data['codigo'] == 'duplicado'


@pytest.fixture
def galpon(api):
    """Un lote de 100 gallinas (PRO-01) y 2 bultos de 40 kg de concentrado en bodega."""
    cliente, lote, _ = api
    lote_id = cliente.post('/api/v1/produccion/lotes-animal/', {**lote, 'cantidad_inicial': 100}, format='json').data['id']
    with connection.cursor() as cur:
        cur.execute("insert into inventario.lote_inventario (producto_id, bodega_id, codigo_lote, origen, fecha_produccion, "
                    "cantidad_inicial, costo_unitario) select p.id, (select min(id) from inventario.bodega), 'PRB-CON-1', "
                    "'compra', '2026-11-01', 2, 120000 from inventario.producto p where p.sku = 'CON-POS' returning id, producto_id")
        inventario_id, concentrado = cur.fetchone()
    return cliente, lote_id, inventario_id, concentrado


def _disponible(inventario_id):
    with connection.cursor() as cur:
        cur.execute('select cantidad_disponible from inventario.lote_inventario where id = %s', [inventario_id])
        return cur.fetchone()[0]


def _vivos(lote_id):
    with connection.cursor() as cur:
        cur.execute('select cantidad_actual from produccion.lote_animal where id = %s', [lote_id])
        return cur.fetchone()[0]


def test_pro_03_registrar_alimentacion_pesajes_eventos_sanitarios_flujo_principal(galpon):
    """PRO-03 · Alimentación: se guarda y sale del kardex en la unidad del producto (20 kg = medio bulto)"""
    cliente, lote_id, inventario_id, concentrado = galpon
    r = cliente.post('/api/v1/produccion/registros-alimentacion/', {'lote_animal': lote_id, 'fecha': '2026-11-18',
                     'producto': concentrado, 'cantidad_kg': 20, 'origen': 'comprado'}, format='json')
    assert r.status_code == 201, r.data
    assert _disponible(inventario_id) == Decimal('1.50')


def test_pro_03_sin_inventario_guarda_el_registro_y_avisa(galpon):
    """5a: no alcanza el alimento; el registro queda, no hay salida a medias y bodega recibe «Inventario insuficiente»"""
    cliente, lote_id, inventario_id, concentrado = galpon
    r = cliente.post('/api/v1/produccion/registros-alimentacion/', {'lote_animal': lote_id, 'fecha': '2026-11-18',
                     'producto': concentrado, 'cantidad_kg': 100, 'origen': 'comprado'}, format='json')
    assert r.status_code == 201, r.data
    assert _disponible(inventario_id) == 2
    assert _evento(r.data['id'], 'inventario.salida_rechazada')['motivo'] == 'Inventario insuficiente'


def test_pro_03_pesaje_de_muestra(galpon):
    """Paso 3: pesaje de una muestra del lote"""
    cliente, lote_id, _, _ = galpon
    r = cliente.post('/api/v1/produccion/registros-pesaje/', {'lote_animal': lote_id, 'fecha': '2026-11-18',
                     'animales_muestreados': 10, 'peso_promedio_kg': 1.85}, format='json')
    assert r.status_code == 201, r.data


def test_pro_03_mortalidad_baja_la_cantidad_del_lote(galpon):
    """Paso 5: si hubo muertes, baja la cantidad actual del lote y avisa al encargado"""
    cliente, lote_id, _, _ = galpon
    r = cliente.post('/api/v1/produccion/eventos-sanitario/', {'lote_animal': lote_id, 'fecha': '2026-11-18',
                     'tipo': 'mortalidad', 'cantidad_afectada': 3, 'causa': 'calor'}, format='json')
    assert r.status_code == 201, r.data
    assert _vivos(lote_id) == 97
    assert _evento(r.data['id'], 'produccion.mortalidad_registrada')['cantidad_actual'] == 97


def test_pro_03_mortalidad_mayor_que_los_vivos_no_guarda_nada(galpon):
    """No mueren más animales de los que hay: no queda el evento ni cambia el lote"""
    cliente, lote_id, _, _ = galpon
    r = cliente.post('/api/v1/produccion/eventos-sanitario/', {'lote_animal': lote_id, 'fecha': '2026-11-18',
                     'tipo': 'mortalidad', 'cantidad_afectada': 101}, format='json')
    assert r.status_code == 400
    assert _vivos(lote_id) == 100
    with connection.cursor() as cur:
        cur.execute('select count(*) from produccion.evento_sanitario where lote_animal_id = %s', [lote_id])
        assert cur.fetchone()[0] == 0


def test_pro_03_lote_cerrado_no_recibe_registros(galpon):
    """Precondición: lote activo"""
    cliente, lote_id, _, _ = galpon
    with connection.cursor() as cur:
        cur.execute("update produccion.lote_animal set estado = 'cerrado', fecha_cierre = '2026-11-18' where id = %s", [lote_id])
    r = cliente.post('/api/v1/produccion/registros-pesaje/', {'lote_animal': lote_id, 'fecha': '2026-11-18',
                     'animales_muestreados': 10, 'peso_promedio_kg': 1.85}, format='json')
    assert r.status_code == 400
    assert 'cerrado' in str(r.data['lote_animal'])


@pytest.fixture
def rebano(api):
    """Un rebaño de ovinos (PRO-01) con una hembra y un macho registrados."""
    cliente, lote, _ = api
    with connection.cursor() as cur:
        cur.execute("select id from produccion.especie where codigo = 'ovino'")
        ovino = cur.fetchone()[0]
    lote_id = cliente.post('/api/v1/produccion/lotes-animal/', {**lote, 'codigo': 'PRB-OV-01', 'especie': ovino,
                           'proposito': 'reproduccion', 'cantidad_inicial': 2}, format='json').data['id']

    def animal(identificador, sexo):
        r = cliente.post('/api/v1/produccion/animales/', {'lote_animal': lote_id, 'identificador': identificador,
                         'sexo': sexo}, format='json')
        assert r.status_code == 201, r.data
        return r.data['id']

    return cliente, lote_id, animal('PRB-OV-H1', 'hembra'), animal('PRB-OV-M1', 'macho')


def _crias(madre_id):
    with connection.cursor() as cur:
        cur.execute('select padre_id, lote_animal_id, sexo from produccion.animal where madre_id = %s order by id', [madre_id])
        return cur.fetchall()


def test_pro_04_registrar_eventos_reproductivos_ovinos_caprinos_flujo_principal(rebano):
    """PRO-04 · Monta y parto: cada cría viva nace como animal con su madre y el padre de la monta"""
    cliente, lote_id, hembra, macho = rebano
    r = cliente.post('/api/v1/produccion/eventos-reproductivo/', {'hembra': hembra, 'macho': macho, 'tipo': 'monta',
                     'fecha': '2026-06-01'}, format='json')
    assert r.status_code == 201, r.data
    r = cliente.post('/api/v1/produccion/eventos-reproductivo/', {'hembra': hembra, 'tipo': 'parto', 'fecha': '2026-11-01',
                     'crias_muertas': 1, 'crias': [{'sexo': 'hembra'}, {'sexo': 'macho'}]}, format='json')
    assert r.status_code == 201, r.data
    assert r.data['crias_vivas'] == 2
    assert _crias(hembra) == [(macho, lote_id, 'hembra'), (macho, lote_id, 'macho')]
    assert _vivos(lote_id) == 4


def test_pro_04_hembra_vendida_no_registra_eventos(rebano):
    """1a: la hembra vendida o muerta no puede tener eventos"""
    cliente, _, hembra, macho = rebano
    with connection.cursor() as cur:
        cur.execute("update produccion.animal set estado = 'vendido' where id = %s", [hembra])
    r = cliente.post('/api/v1/produccion/eventos-reproductivo/', {'hembra': hembra, 'macho': macho, 'tipo': 'monta',
                     'fecha': '2026-06-01'}, format='json')
    assert r.status_code == 400
    assert 'hembra' in r.data


def test_pro_04_monta_exige_macho(rebano):
    """Paso 2: para una monta se registra el macho"""
    cliente, _, hembra, _ = rebano
    r = cliente.post('/api/v1/produccion/eventos-reproductivo/', {'hembra': hembra, 'tipo': 'monta', 'fecha': '2026-06-01'},
                     format='json')
    assert r.status_code == 400
    assert 'macho' in r.data


def test_pro_04_destete_pasa_las_crias_a_otro_lote(rebano):
    """3a: al destetar, las crías pasan a su lote y cada lote ajusta su cantidad"""
    cliente, lote_id, hembra, _ = rebano
    destino = cliente.post('/api/v1/produccion/lotes-animal/', {'codigo': 'PRB-OV-02', 'especie': _especie_del_lote(lote_id),
                           'zona': _zona_del_lote(lote_id), 'proposito': 'cria', 'fecha_ingreso': '2026-11-01',
                           'cantidad_inicial': 0}, format='json').data['id']
    cliente.post('/api/v1/produccion/eventos-reproductivo/', {'hembra': hembra, 'tipo': 'parto', 'fecha': '2026-11-01',
                 'crias': [{'sexo': 'hembra'}]}, format='json')
    r = cliente.post('/api/v1/produccion/eventos-reproductivo/', {'hembra': hembra, 'tipo': 'destete', 'fecha': '2027-01-15',
                     'lote_destino': destino}, format='json')
    assert r.status_code == 201, r.data
    assert [c[1] for c in _crias(hembra)] == [destino]
    assert (_vivos(lote_id), _vivos(destino)) == (2, 1)


def _especie_del_lote(lote_id):
    with connection.cursor() as cur:
        cur.execute('select especie_id from produccion.lote_animal where id = %s', [lote_id])
        return cur.fetchone()[0]


def _zona_del_lote(lote_id):
    with connection.cursor() as cur:
        cur.execute('select zona_id from produccion.lote_animal where id = %s', [lote_id])
        return cur.fetchone()[0]


@pytest.fixture
def cultivo(api):
    """Una siembra de 1.000 plantas de fríjol y 50 kg de cal agrícola en bodega."""
    cliente, lote, _ = api
    with connection.cursor() as cur:
        cur.execute("select id from produccion.cultivo where codigo = 'frijol'")
        frijol = cur.fetchone()[0]
        cur.execute("insert into inventario.lote_inventario (producto_id, bodega_id, codigo_lote, origen, fecha_produccion, "
                    "cantidad_inicial, costo_unitario) select p.id, (select min(id) from inventario.bodega), 'PRB-CAL-1', "
                    "'compra', '2026-11-01', 50, 900 from inventario.producto p where p.sku = 'CAL-AGR' returning id, producto_id")
        inventario_id, cal = cur.fetchone()
    r = cliente.post('/api/v1/produccion/siembras/', {'zona': lote['zona'], 'cultivo': frijol, 'fecha_siembra': '2026-10-01',
                     'plantas_sembradas': 1000}, format='json')
    assert r.status_code == 201, r.data
    return cliente, r.data, inventario_id, cal


def _siembra(siembra_id):
    with connection.cursor() as cur:
        cur.execute('select plantas_vivas, estado from produccion.siembra where id = %s', [siembra_id])
        return cur.fetchone()


def test_pro_05_registrar_siembra_labores_culturales_flujo_principal(cultivo):
    """PRO-05 · La siembra nace con sus plantas vivas y la labor descuenta el insumo del inventario"""
    cliente, siembra, inventario_id, cal = cultivo
    assert (siembra['plantas_vivas'], siembra['estado']) == (1000, 'sembrada')
    r = cliente.post('/api/v1/produccion/labores-cultural/', {'siembra': siembra['id'], 'fecha': '2026-10-15',
                     'tipo': 'encalado', 'producto': cal, 'cantidad': 20, 'jornales': 1}, format='json')
    assert r.status_code == 201, r.data
    assert r.data['metodo'] == 'manual'
    assert _disponible(inventario_id) == 30


def test_pro_05_conteo_con_muchas_muertas_pasa_a_recuperacion(cultivo):
    """2a: el conteo deja menos de la mitad viva; la siembra pasa a recuperación y se avisa para resembrar"""
    cliente, siembra, _, _ = cultivo
    r = cliente.post('/api/v1/produccion/labores-cultural/', {'siembra': siembra['id'], 'fecha': '2026-10-20',
                     'tipo': 'conteo', 'cantidad': 400}, format='json')
    assert r.status_code == 201, r.data
    assert _siembra(siembra['id']) == (400, 'recuperacion')
    assert _evento(siembra['id'], 'produccion.siembra_en_recuperacion')['plantas_vivas'] == 400


def test_pro_05_labor_por_robot_sin_mision_responde_422(cultivo):
    """3a: método robot o dron sin misión; lo rechaza el CHECK de la base"""
    cliente, siembra, _, _ = cultivo
    r = cliente.post('/api/v1/produccion/labores-cultural/', {'siembra': siembra['id'], 'fecha': '2026-10-20',
                     'tipo': 'deshierbe', 'metodo': 'robot'}, format='json')
    assert r.status_code == 422
    assert r.data['codigo'] == 'valor_invalido'


def test_pro_05_siembra_finalizada_no_recibe_labores(cultivo):
    """Una siembra perdida o finalizada ya no recibe labores"""
    cliente, siembra, _, _ = cultivo
    with connection.cursor() as cur:
        cur.execute("update produccion.siembra set estado = 'finalizada' where id = %s", [siembra['id']])
    r = cliente.post('/api/v1/produccion/labores-cultural/', {'siembra': siembra['id'], 'fecha': '2026-10-20',
                     'tipo': 'poda'}, format='json')
    assert r.status_code == 400
    assert 'finalizada' in str(r.data['siembra'])


@pytest.fixture
def cosecha(cultivo):
    """La siembra de fríjol de PRO-05, el producto fríjol y una bodega."""
    cliente, siembra, _, _ = cultivo
    with connection.cursor() as cur:
        cur.execute("select (select id from inventario.producto where sku = 'FRI-KG'), (select min(id) from inventario.bodega)")
        frijol, bodega = cur.fetchone()
    base = {'siembra': siembra['id'], 'fecha': '2026-12-30', 'producto': frijol, 'cantidad': 120}
    return cliente, base, bodega


def test_pro_06_registrar_cosecha_destino_flujo_principal(cosecha):
    """PRO-06 · A venta: entra a bodega como lote con su entrada en kardex y la siembra pasa a producción"""
    cliente, base, bodega = cosecha
    r = cliente.post('/api/v1/produccion/cosechas/', {**base, 'destino': 'venta', 'bodega': bodega}, format='json')
    assert r.status_code == 201, r.data
    with connection.cursor() as cur:
        cur.execute("select l.origen_tabla, l.origen_id, l.cantidad_disponible, (select count(*) from inventario.movimiento_inventario m "
                    "where m.lote_inventario_id = l.id and m.tipo = 'entrada') from inventario.lote_inventario l where l.id = %s",
                    [r.data['lote_inventario']])
        assert cur.fetchone() == ('produccion.cosecha', r.data['id'], 120, 1)
    assert _siembra(base['siembra'])[1] == 'en_produccion'
    assert _evento(r.data['id'], 'produccion.cosecha_registrada')['destino'] == 'venta'


def test_pro_06_venta_sin_bodega_responde_400(cosecha):
    """Paso 2: lo que va a venta elige bodega"""
    cliente, base, _ = cosecha
    r = cliente.post('/api/v1/produccion/cosechas/', {**base, 'destino': 'venta'}, format='json')
    assert r.status_code == 400
    assert 'bodega' in r.data


def test_pro_06_alimento_animal_queda_como_alimentacion_propia(cosecha, api):
    """1a: destino alimento animal; no entra a bodega y queda en el registro de alimentación del lote"""
    cliente, base, _ = cosecha
    _, lote, _ = api
    lote_id = cliente.post('/api/v1/produccion/lotes-animal/', lote, format='json').data['id']
    r = cliente.post('/api/v1/produccion/cosechas/', {**base, 'destino': 'alimento_animal', 'lote_animal': lote_id}, format='json')
    assert r.status_code == 201, r.data
    assert r.data['lote_inventario'] is None
    with connection.cursor() as cur:
        cur.execute('select origen, cantidad_kg from produccion.registro_alimentacion where lote_animal_id = %s', [lote_id])
        assert cur.fetchall() == [('propio', 120)]


def test_pro_06_siembra_perdida_no_cosecha(cosecha):
    """Precondición: la siembra debe estar en producción (o por empezar a producir)"""
    cliente, base, _ = cosecha
    with connection.cursor() as cur:
        cur.execute("update produccion.siembra set estado = 'perdida' where id = %s", [base['siembra']])
    r = cliente.post('/api/v1/produccion/cosechas/', {**base, 'destino': 'perdida'}, format='json')
    assert r.status_code == 400


def _abrir_expediente(norma):
    """La finca de prueba aún no lleva el expediente: se abre aquí (se deshace al final)."""
    with connection.cursor() as cur:
        cur.execute('insert into cumplimiento.expediente (norma_id) select id from cumplimiento.norma where codigo = %s '
                    'on conflict do nothing', [norma])


def _requisito(codigo):
    """Estado del requisito en el expediente de la finca (None si aún no se ha evaluado)."""
    with connection.cursor() as cur:
        cur.execute('select ev.estado from cumplimiento.evaluacion_requisito ev join cumplimiento.requisito q '
                    'on q.id = ev.requisito_id where q.codigo = %s', [codigo])
        return (cur.fetchone() or [None])[0]


def test_pro_07_registrar_analisis_suelo_recomendacion_flujo_principal(api):
    """PRO-07 · Sin recomendación, el análisis avisa al Agrónomo (IA) y cuenta como evidencia BPA-02"""
    cliente, lote, _ = api
    with connection.cursor() as cur:
        cur.execute("select nucleo.funcion_activa('certificacion_bpa')")
        bpa = cur.fetchone()[0]
    if bpa:  # el expediente BPA solo se abre con la función encendida
        _abrir_expediente('ICA_BPA')
    r = cliente.post('/api/v1/produccion/analisis-suelo/', {'zona': lote['zona'], 'fecha_muestreo': '2026-11-10',
                     'laboratorio': 'Agrosavia', 'ph': 5.2, 'materia_organica_pct': 3.1}, format='json')
    assert r.status_code == 201, r.data
    assert _evento(r.data['id'], 'produccion.analisis_suelo_registrado')['ph'] == '5.20'  # el outbox guarda los decimales como texto
    assert _requisito('BPA-02') == ('cumple' if bpa else None)


def test_pro_07_con_recomendacion_del_encargado_no_espera_al_agente(api):
    """2a: el encargado escribe la recomendación; no se pide al agente"""
    cliente, lote, _ = api
    r = cliente.post('/api/v1/produccion/analisis-suelo/', {'zona': lote['zona'], 'fecha_muestreo': '2026-11-10', 'ph': 5.2,
                     'recomendacion': 'Encalar 1 t/ha con cal dolomita'}, format='json')
    assert r.status_code == 201, r.data
    with connection.cursor() as cur:
        cur.execute("select count(*) from nucleo.evento_salida where tipo_evento = 'produccion.analisis_suelo_registrado' "
                    "and entidad_id = %s", [r.data['id']])
        assert cur.fetchone()[0] == 0


def test_pro_08_registrar_bioseguridad_e_inocuidad_flujo_principal(api):
    """PRO-08 · La desinfección queda registrada y el requisito GAB-03 del expediente ICA pasa a cumple"""
    cliente, lote, _ = api
    _abrir_expediente('ICA_GAB')
    r = cliente.post('/api/v1/produccion/registros-bioseguridad/', {'zona': lote['zona'], 'fecha': '2026-11-18',
                     'tipo': 'desinfeccion', 'responsable': 'Operario de turno'}, format='json')
    assert r.status_code == 201, r.data
    assert _requisito('GAB-03') == 'cumple'


def test_pro_08_sin_responsable_responde_400(api):
    """El registro exige responsable (evidencia para el ICA)"""
    cliente, lote, _ = api
    r = cliente.post('/api/v1/produccion/registros-bioseguridad/', {'zona': lote['zona'], 'fecha': '2026-11-18',
                     'tipo': 'limpieza'}, format='json')
    assert r.status_code == 400
    assert 'responsable' in r.data


@pytest.mark.skip(reason='PRO-09: por construir')
def test_pro_09_producir_abono_lombricultivo_compostera_flujo_principal():
    """PRO-09 · Producir abono en lombricultivo o compostera"""


@pytest.mark.skip(reason='PRO-10: por construir')
def test_pro_10_medir_calidad_agua_estanques_flujo_principal():
    """PRO-10 · Medir la calidad del agua de los estanques"""
