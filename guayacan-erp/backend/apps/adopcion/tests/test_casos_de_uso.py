"""Pruebas de aceptación de los casos de uso de adopcion.

Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip
(«saltar») porque el caso aún no está construido. Al construirlo:
1. Quite la línea @pytest.mark.skip.
2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.
3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""
import hashlib
import json
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.adopcion import services
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


@pytest.fixture
def ado_03(ado_02):
    """El aguacate pagado (ADO-02, reservado) y una función que arma la visita de una persona: registrada,
    aprobada (AGD-03) y, si entra, con su paso por portería (AGD-04)."""
    api, compra, bien_id = ado_02
    c = api.post('/api/v1/adopcion/contratos/compra/', compra, format='json').data
    assert _avisar(c['numero'], c['predio']).data['estado'] == 'activo'
    ahora = timezone.now()

    def visita(tercero_id=c['adoptante'], entra=True):
        v = api.post('/api/v1/agenda/visitas/', {
            'tipo': 'turista', 'nombre': 'Anna Schmidt', 'tercero': tercero_id, 'motivo': 'Sembrar su aguacate',
            'ingreso_programado': (ahora + timedelta(minutes=10)).isoformat(),
            'salida_programada': (ahora + timedelta(hours=3)).isoformat()}, format='json').data
        assert api.post(f"/api/v1/agenda/visitas/{v['id']}/aprobar/", {'decision': 'aprobar'}, format='json').status_code == 200
        if entra:
            codigo = api.post(f"/api/v1/agenda/visitas/{v['id']}/pase/").data['codigo_pase']
            r = api.post('/api/v1/agenda/registros-acceso/', {'sentido': 'entrada', 'tipo': 'persona', 'codigo_pase': codigo}, format='json')
            assert r.status_code == 201, r.data
        return v['id']

    hoy = timezone.localdate(ahora + timedelta(minutes=10)).isoformat()
    return api, bien_id, visita, hoy, c


def test_ado_03_sembrar_persona_flujo_principal(ado_03):
    """ADO-03 · El adoptante entró por portería y sembró: el árbol pasa a activo, el sitio a ocupado y queda el seguimiento"""
    api, bien_id, visita, hoy, c = ado_03
    r = api.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'visita': visita()}, format='json')
    assert r.status_code == 200, r.data
    assert (r.data['estado'], r.data['fecha_inicio']) == ('activo', hoy)
    assert _fila('select s.estado from adopcion.sitio s join adopcion.bien b on b.sitio_id = s.id where b.id = %s', bien_id) == ('ocupado',)
    # Solo el comienzo del texto: la base local tiene las tildes de las funciones originales mal codificadas (TODO carga limpia)
    assert _fila("select tipo, descripcion like 'Sembrado por su %%' from adopcion.seguimiento where bien_id = %s", bien_id) == (
        'siembra', True)
    assert _fila("select count(*) from nucleo.evento_salida where tipo_evento = 'adopcion.sembrado' and entidad_id = %s", bien_id) == (1,)


def test_ado_03_visita_de_otra_persona_no_sirve(ado_03):
    """La visita debe ser del adoptante del árbol"""
    api, bien_id, visita, hoy, _ = ado_03
    with connection.cursor() as cur:
        cur.execute("insert into terceros.tercero (tipo_persona, nombres) values ('natural', 'Otra persona') returning id")
        otro = cur.fetchone()[0]
    r = api.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'visita': visita(tercero_id=otro)}, format='json')
    assert r.status_code == 400
    assert 'adoptante' in str(r.data['visita'])


def test_ado_03_sin_paso_por_porteria_no_siembra(ado_03):
    """Visita aprobada pero sin entrada en portería: no hay prueba de que vino"""
    api, bien_id, visita, hoy, _ = ado_03
    r = api.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'visita': visita(entra=False)}, format='json')
    assert r.status_code == 400
    assert 'no ha entrado' in str(r.data['visita'])
    assert _fila('select estado from adopcion.bien where id = %s', bien_id) == ('reservado',)


def test_ado_03_otro_dia_que_la_visita_no_siembra(ado_03):
    """La siembra en persona es el día de la visita"""
    api, bien_id, visita, _, _ = ado_03
    r = api.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': '2027-01-01', 'visita': visita()}, format='json')
    assert r.status_code == 400
    assert 'fecha' in r.data


def test_ado_03_arbol_sin_pagar_no_se_siembra(ado_02):
    """Sin pago confirmado no hay contrato activo: la base lo rechaza"""
    api, compra, bien_id = ado_02
    api.post('/api/v1/adopcion/contratos/compra/', compra, format='json')  # queda pendiente_pago
    visita = api.post('/api/v1/agenda/visitas/', {'tipo': 'turista', 'nombre': 'Anna Schmidt', 'motivo': 'Sembrar',
                      'ingreso_programado': '2026-12-05T09:00:00-05:00', 'salida_programada': '2026-12-05T12:00:00-05:00'},
                      format='json').data['id']
    r = api.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': '2026-12-05', 'visita': visita}, format='json')
    assert r.status_code == 422
    assert 'contrato activo' in r.data['detalle']


def _trabajador(nombre, predio_id):
    """Un empleado con su propio usuario de operario (sin permisos de encargado). Devuelve (empleado_id, cliente)."""
    with connection.cursor() as cur:
        cur.execute("insert into terceros.tercero (tipo_persona, tipo_documento, numero_documento, nombres) "
                    "values ('natural', 'CC', %s, %s) returning id", [f'PRB-{nombre}', nombre])
        tercero = cur.fetchone()[0]
        cur.execute("insert into terceros.empleado (tercero_id, cargo, tipo_vinculacion, fecha_ingreso) "
                    "values (%s, 'Operario', 'jornal', '2026-01-01') returning id", [tercero])
        empleado = cur.fetchone()[0]
        cur.execute("insert into nucleo.usuario (nombre_completo, correo, contrasena_hash, tercero_id) "
                    "values (%s, %s, 'x', %s) returning id", [nombre, f'prb-{nombre.lower()}@guayacan.local', tercero])
        usuario = cur.fetchone()[0]
        cur.execute("insert into nucleo.usuario_rol (usuario_id, rol_id) select %s, id from nucleo.rol where codigo = 'operario_granja'",
                    [usuario])
    cliente = APIClient()
    tokens = emitir_tokens(get_user_model().objects.get(pk=usuario), predio_id)
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['acceso']}")
    return empleado, cliente


@pytest.fixture
def ado_04(ado_02):
    """El aguacate pagado con siembra por trabajador (ADO-02) y la tarea de siembra de hoy asignada a Ana y ya iniciada."""
    api, compra, bien_id = ado_02
    c = api.post('/api/v1/adopcion/contratos/compra/', {**compra, 'modalidad_siembra': 'trabajador', 'autoriza_seguimiento': True},
                 format='json').data
    assert _avisar(c['numero'], c['predio']).data['estado'] == 'activo'
    zona = _fila('select s.zona_id from adopcion.bien b join adopcion.sitio s on s.id = b.sitio_id where b.id = %s', bien_id)[0]
    ana, cliente_ana = _trabajador('Ana', c['predio'])
    hoy = timezone.localdate().isoformat()

    def tarea(zona_id=zona, iniciar=True):
        t = api.post('/api/v1/personal/tareas/', {'titulo': 'Sembrar aguacate PRB-0001', 'fecha': hoy, 'zona': zona_id,
                     'prioridad': 'alta', 'origen': 'manual', 'estado': 'pendiente'}, format='json').data['id']
        assert api.patch(f'/api/v1/personal/tareas/{t}/', {'empleado': ana}, format='json').status_code == 200
        if iniciar:
            assert cliente_ana.patch(f'/api/v1/personal/tareas/{t}/', {'estado': 'en_curso'}, format='json').status_code == 200
        return t

    video = 'https://minio.local/evidencias/siembra-prb-0001.mp4'
    return cliente_ana, bien_id, tarea, hoy, video, c


def test_ado_04_sembrar_trabajador_enviar_video_flujo_principal(ado_04):
    """ADO-04 · Ana siembra en su tarea y sube el video: el árbol pasa a activo, el video queda en el seguimiento y como
    evidencia de la tarea, y sale adopcion.sembrado con el video para el Gestor de redes"""
    ana, bien_id, tarea, hoy, video, _ = ado_04
    t = tarea()
    r = ana.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'tarea': t, 'video_url': video}, format='json')
    assert r.status_code == 200, r.data
    assert r.data['estado'] == 'activo'
    assert _fila("select tipo, evidencia_url, tarea_id from adopcion.seguimiento where bien_id = %s", bien_id) == ('video_siembra', video, t)
    assert _fila("select tipo, archivo_url, registro_tabla from personal.evidencia_tarea where tarea_id = %s", t) == (
        'video', video, 'adopcion.seguimiento')
    carga = _fila("select carga from nucleo.evento_salida where tipo_evento = 'adopcion.sembrado' and entidad_id = %s", bien_id)[0]
    assert json.loads(carga)['video'] == video


def test_ado_04_sin_video_no_hay_siembra(ado_04):
    """Apéndice A: la siembra por un trabajador exige el video para el adoptante"""
    ana, bien_id, tarea, hoy, _, _ = ado_04
    r = ana.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'tarea': tarea()}, format='json')
    assert r.status_code == 400
    assert 'video_url' in r.data
    assert _fila('select estado from adopcion.bien where id = %s', bien_id) == ('reservado',)


def test_ado_04_trabajador_no_asignado_recibe_403(ado_04):
    """Solo quien ejecuta la tarea deja su evidencia (regla de PER-05 en la base): nada queda a medias"""
    _, bien_id, tarea, hoy, video, c = ado_04
    _, beto = _trabajador('Beto', c['predio'])
    r = beto.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'tarea': tarea(), 'video_url': video}, format='json')
    assert (r.status_code, r.data['codigo']) == (403, 'sin_permiso')
    assert _fila('select estado from adopcion.bien where id = %s', bien_id) == ('reservado',)


def test_ado_04_tarea_sin_iniciar_no_recibe_el_video(ado_04):
    """La tarea debe estar en curso o terminada para recibir la evidencia"""
    ana, bien_id, tarea, hoy, video, _ = ado_04
    r = ana.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'tarea': tarea(iniciar=False), 'video_url': video},
                 format='json')
    assert r.status_code == 422
    assert 'en curso o terminada' in r.data['detalle']
    assert _fila('select estado from adopcion.bien where id = %s', bien_id) == ('reservado',)


def test_ado_04_tarea_de_otra_zona_no_sirve(ado_04):
    """La tarea de siembra es la de la zona donde está el árbol"""
    ana, bien_id, tarea, hoy, video, _ = ado_04
    otra = _fila('select id from nucleo.zona where id <> (select s.zona_id from adopcion.bien b join adopcion.sitio s '
                 'on s.id = b.sitio_id where b.id = %s) order by id limit 1', bien_id)[0]
    r = ana.post(f'/api/v1/adopcion/bienes/{bien_id}/siembra/', {'fecha': hoy, 'tarea': tarea(zona_id=otra), 'video_url': video},
                 format='json')
    assert r.status_code == 400
    assert 'zona' in str(r.data['tarea'])


@pytest.fixture
def ado_05(ado_02):
    """Un contrato activo (ADO-02) con el árbol ya sembrado y su cuota del mes siguiente, creada por
    adopcion.generar_cuotas() (la tarea del día 1)."""
    api, compra, bien_id = ado_02
    c = api.post('/api/v1/adopcion/contratos/compra/', compra, format='json').data
    assert _avisar(c['numero'], c['predio']).data['estado'] == 'activo'
    # Solo un árbol sembrado (vivo) paga cuota: se siembra con la función de la base (ADO-03 ya la prueba por la API)
    _fila('select adopcion.registrar_siembra(%s, current_date) is null', bien_id)
    mes = (timezone.localdate().replace(day=1) + timedelta(days=32)).replace(day=1)
    assert _fila('select adopcion.generar_cuotas(%s)', mes) == (1,)
    cuota = _fila('select id from adopcion.cuota where contrato_id = %s', c['id'])[0]
    return api, cuota, c['predio']


def _cuota(cuota_id):
    return _fila('select estado, pago_id is not null from adopcion.cuota where id = %s', cuota_id)


def _avisos(tipo, entidad_id):
    return _fila('select count(*) from nucleo.evento_salida where tipo_evento = %s and entidad_id = %s', tipo, entidad_id)[0]


def test_ado_05_cobrar_pagar_cuota_mensual_flujo_principal(ado_05):
    """ADO-05 · El vendedor pide el cobro, la pasarela confirma y la cuota queda pagada con su factura"""
    api, cuota, predio = ado_05
    r = api.post(f'/api/v1/adopcion/cuotas/{cuota}/pagar/')
    assert r.status_code == 200, r.data
    assert r.data['cobro']['url_pago'].endswith(f'{predio}:CUO-{cuota}')
    assert _cuota(cuota) == ('pendiente', False)  # hasta que la pasarela confirme
    a = _avisar(f'CUO-{cuota}', predio, valor='25000.00')
    assert (a.status_code, a.data['estado']) == (200, 'pagada'), a.data
    assert _cuota(cuota) == ('pagada', True)
    assert _fila('select f.total, f.saldo, p.estado from adopcion.cuota q join comercial.pago p on p.id = q.pago_id '
                 'join comercial.factura f on f.id = p.factura_id where q.id = %s', cuota) == (25000, 0, 'confirmado')
    assert _avisos('adopcion.cuota_pagada', cuota) == 1


def test_ado_05_pago_rechazado_queda_pendiente(ado_05):
    """Si el pago falla, la cuota sigue pendiente y sin factura"""
    api, cuota, predio = ado_05
    a = _avisar(f'CUO-{cuota}', predio, estado='rechazado', valor='25000.00')
    assert a.status_code == 200
    assert _cuota(cuota) == ('pendiente', False)
    assert _avisos('adopcion.pago_rechazado', cuota) == 1


def test_ado_05_monto_distinto_responde_400(ado_05):
    """C: la pasarela debe cobrar exactamente el valor de la cuota"""
    _, cuota, predio = ado_05
    a = _avisar(f'CUO-{cuota}', predio, valor='20000.00')
    assert a.status_code == 400
    assert _cuota(cuota) == ('pendiente', False)


def test_ado_05_cuota_anulada_no_cobra_dos_veces(ado_05):
    """B: el contrato terminó por abandono y la cuota se anuló mientras se pagaba: se pide devolver el dinero, una vez"""
    _, cuota, predio = ado_05
    _fila("update adopcion.cuota set estado = 'anulada' where id = %s returning id", cuota)
    for _ in range(2):
        a = _avisar(f'CUO-{cuota}', predio, valor='25000.00')
        assert (a.status_code, a.data['estado']) == (200, 'anulada')
    assert _cuota(cuota) == ('anulada', False)
    assert _avisos('adopcion.pago_sin_cuota', cuota) == 1


def test_ado_05_aviso_repetido_no_duplica(ado_05):
    """La pasarela reenvía el aviso: no hay segundo pago ni segunda factura"""
    _, cuota, predio = ado_05
    assert _avisar(f'CUO-{cuota}', predio, valor='25000.00').data['estado'] == 'pagada'
    assert _avisar(f'CUO-{cuota}', predio, valor='25000.00').data['estado'] == 'pagada'
    assert _fila("select count(*) from comercial.pago where referencia = %s", f'{predio}:CUO-{cuota}') == (1,)
    assert _avisos('adopcion.pago_sin_cuota', cuota) == 0


def test_ado_05_cuota_pagada_no_se_cobra_otra_vez(ado_05):
    """No se pide el cobro de una cuota que ya no está pendiente"""
    api, cuota, predio = ado_05
    _avisar(f'CUO-{cuota}', predio, valor='25000.00')
    r = api.post(f'/api/v1/adopcion/cuotas/{cuota}/pagar/')
    assert r.status_code == 400
    assert 'pagada' in str(r.data['estado'])


@pytest.fixture
def ado_06(ado_05):
    """El árbol sembrado con su cuota (ADO-05); el vendedor emite el enlace personal del adoptante."""
    api, cuota, predio = ado_05
    contrato, bien, adoptante = _fila('select c.id, c.bien_id, c.adoptante_id from adopcion.cuota q join adopcion.contrato c '
                                      'on c.id = q.contrato_id where q.id = %s', cuota)
    r = api.post(f'/api/v1/adopcion/contratos/{contrato}/enlace/')
    assert r.status_code == 201, r.data
    return api, r.data, contrato, bien, adoptante


def _abrir(ruta):
    """El adoptante abre su enlace: sin sesión."""
    return APIClient().get(ruta)


def test_ado_06_seguir_mi_arbol_mi_animal_flujo_principal(ado_06):
    """ADO-06 · Con su enlace, sin cuenta, el adoptante ve su árbol, el seguimiento, la cuota y el saldo; la base guarda
    solo la huella del código"""
    _, enlace, _, bien, _ = ado_06
    r = _abrir(enlace['ruta'])
    assert r.status_code == 200, r.data
    assert (r.data['bien']['id'], r.data['bien']['estado']) == (bien, 'activo')
    assert [s['tipo'] for s in r.data['seguimiento']] == ['siembra']
    assert [(c['estado'], c['valor']) for c in r.data['cuotas']] == [('pendiente', 25000)]
    assert r.data['saldo_a_favor'] == 0
    codigo = enlace['ruta'].rstrip('/').rsplit('.', 1)[1]
    assert _fila('select token_hash = %s, ultimo_uso_en is not null from adopcion.enlace_adoptante where id = %s',
                 hashlib.sha256(codigo.encode()).hexdigest(), enlace['enlace']) == (True, True)


def test_ado_06_enlace_revocado_deja_de_servir(ado_06):
    """Se puede revocar: el mismo enlace responde 404"""
    api, enlace, _, _, _ = ado_06
    assert api.post(f"/api/v1/adopcion/enlaces/{enlace['enlace']}/revocar/").status_code == 200
    assert _abrir(enlace['ruta']).status_code == 404


def test_ado_06_un_enlace_nuevo_revoca_el_anterior(ado_06):
    """Emitir otro enlace para el mismo contrato deja sin efecto el anterior"""
    api, viejo, contrato, _, _ = ado_06
    nuevo = api.post(f'/api/v1/adopcion/contratos/{contrato}/enlace/').data
    assert (_abrir(viejo['ruta']).status_code, _abrir(nuevo['ruta']).status_code) == (404, 200)


def test_ado_06_contrato_terminado_o_enlace_vencido_no_sirven(ado_06):
    """Si el contrato deja de estar activo (cedido, liquidado, abandonado) o pasan los 12 meses, el enlace ya no sirve"""
    api, enlace, contrato, _, _ = ado_06
    _fila("update adopcion.enlace_adoptante set vence_en = now() - interval '1 day' where id = %s returning id", enlace['enlace'])
    assert _abrir(enlace['ruta']).status_code == 404
    nuevo = api.post(f'/api/v1/adopcion/contratos/{contrato}/enlace/').data
    _fila("update adopcion.contrato set estado = 'terminado_abandono' where id = %s returning id", contrato)
    assert _abrir(nuevo['ruta']).status_code == 404


def test_ado_06_codigo_falso_responde_404(ado_06):
    """Un código inventado, o mal formado, no muestra nada"""
    _, enlace, _, _, _ = ado_06
    finca = enlace['ruta'].split('/')[-2].split('.')[0]
    assert _abrir(f'/api/v1/publico/adopcion/{finca}.codigo-inventado/').status_code == 404
    assert _abrir('/api/v1/publico/adopcion/sin-finca/').status_code == 404


def test_ado_06_mis_bienes_para_el_adoptante_con_cuenta(ado_06):
    """Quien sí se registró ve sus bienes en /mis-bienes/; otra persona no ve los ajenos"""
    _, _, _, bien, adoptante = ado_06
    predio = _fila('select predio_id from adopcion.bien where id = %s', bien)[0]

    def cliente(tercero, correo):
        usuario = _fila("insert into nucleo.usuario (nombre_completo, correo, contrasena_hash, tercero_id) "
                        "values ('Adoptante de prueba', %s, 'x', %s) returning id", correo, tercero)[0]
        _fila("insert into nucleo.usuario_rol (usuario_id, rol_id) select %s, id from nucleo.rol where codigo = 'cliente' returning id", usuario)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {emitir_tokens(get_user_model().objects.get(pk=usuario), predio)['acceso']}")
        return c

    anna = cliente(adoptante, 'anna-prb@example.com')
    assert [b['bien']['id'] for b in anna.get('/api/v1/adopcion/mis-bienes/').data] == [bien]
    r = anna.get(f'/api/v1/adopcion/mis-bienes/{bien}/seguimiento/')
    assert (r.status_code, r.data['bien']['id']) == (200, bien)
    otro = _fila("insert into terceros.tercero (tipo_persona, nombres) values ('natural', 'Otra persona') returning id")[0]
    ajeno = cliente(otro, 'otra-prb@example.com')
    assert ajeno.get('/api/v1/adopcion/mis-bienes/').data == []
    assert ajeno.get(f'/api/v1/adopcion/mis-bienes/{bien}/seguimiento/').status_code == 404


def test_ado_06_limite_de_60_por_minuto(ado_06):
    """C: la ruta pública acepta 60 peticiones por minuto de una misma dirección"""
    _, enlace, _, _, _ = ado_06
    cache.clear()
    try:
        assert all(_abrir(enlace['ruta']).status_code == 200 for _ in range(60))
        assert _abrir(enlace['ruta']).status_code == 429
    finally:
        cache.clear()  # el contador no debe afectar a otras pruebas


@pytest.fixture
def ado_07(ado_05):
    """El contrato de ADO-05 con tres cuotas (vencen el día 10 de tres meses seguidos) y ninguna pagada."""
    api, cuota, _ = ado_05
    contrato, bien, periodo = _fila('select c.id, c.bien_id, q.periodo from adopcion.cuota q join adopcion.contrato c '
                                    'on c.id = q.contrato_id where q.id = %s', cuota)
    meses = [periodo]
    for _ in range(2):
        meses.append((meses[-1] + timedelta(days=32)).replace(day=1))
        _fila('select adopcion.generar_cuotas(%s)', meses[-1])
    assert _fila('select count(*) from adopcion.cuota where contrato_id = %s', contrato) == (3,)
    return api, contrato, bien, [m.replace(day=11) for m in meses]  # el día siguiente a cada vencimiento


def _abandono(fecha):
    """La tarea diaria corre ese día."""
    return services.ado_07_detectar_abandono_poner_readopcion(fecha=fecha)


def _avisos_mora(bien):
    return [s for s, in _filas("select id from adopcion.seguimiento where bien_id = %s and tipo = 'aviso_mora' order by fecha", bien)]


def _filas(sql, *params):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def test_ado_07_detectar_abandono_poner_readopcion_flujo_principal(ado_07):
    """ADO-07 · Un aviso por cada cuota vencida (no uno por día); con la tercera vencida y su aviso entregado hace 15 días
    el contrato termina por abandono, las cuotas se anulan y el bien pasa a readopción"""
    api, contrato, bien, dias = ado_07
    for n, dia in enumerate(dias, 1):
        assert _abandono(dia) == 0
        assert _abandono(dia + timedelta(days=1)) == 0  # la tarea corre a diario: no repite el aviso
        assert len(_avisos_mora(bien)) == n
    assert _avisos('adopcion.aviso_mora', contrato) == 3
    ultimo = _avisos_mora(bien)[-1]
    r = api.post(f'/api/v1/adopcion/seguimientos/{ultimo}/marcar-enviado/')
    assert (r.status_code, r.data['enviado_al_adoptante']) == (200, True), r.data
    assert _abandono(dias[-1] + timedelta(days=14)) == 0  # aún en los días de gracia
    assert _abandono(dias[-1] + timedelta(days=15)) == 1
    assert _fila('select estado from adopcion.contrato where id = %s', contrato) == ('terminado_abandono',)
    assert _fila('select estado from adopcion.bien where id = %s', bien) == ('en_readopcion',)
    assert _fila("select count(*) from adopcion.cuota where contrato_id = %s and estado <> 'anulada'", contrato) == (0,)
    assert _avisos('adopcion.abandonado', contrato) == 1


def test_ado_07_sin_aviso_entregado_nunca_hay_abandono(ado_07):
    """Nunca sin aviso previo: si el canal no confirma la entrega, el contrato sigue activo aunque pasen meses"""
    _, contrato, _, dias = ado_07
    for dia in dias:
        _abandono(dia)
    assert _abandono(dias[-1] + timedelta(days=90)) == 0
    assert _fila('select estado from adopcion.contrato where id = %s', contrato) == ('activo',)


def test_ado_07_solo_el_aviso_de_la_tercera_cuota_cuenta(ado_07):
    """Entregar los avisos de la primera y segunda cuota no basta: hace falta el de la tercera"""
    api, contrato, bien, dias = ado_07
    for dia in dias:
        _abandono(dia)
    for aviso in _avisos_mora(bien)[:2]:
        assert api.post(f'/api/v1/adopcion/seguimientos/{aviso}/marcar-enviado/').status_code == 200
    assert _abandono(dias[-1] + timedelta(days=30)) == 0
    assert _fila('select estado from adopcion.contrato where id = %s', contrato) == ('activo',)


def test_ado_07_enviado_no_se_cambia_por_el_crud(ado_07):
    """enviado_al_adoptante es de solo lectura en /seguimientos/: nadie adelanta el abandono por ahí"""
    api, _, bien, dias = ado_07
    _abandono(dias[0])
    aviso = _avisos_mora(bien)[0]
    r = api.patch(f'/api/v1/adopcion/seguimientos/{aviso}/', {'enviado_al_adoptante': True}, format='json')
    assert r.status_code == 200, r.data
    assert _fila('select enviado_al_adoptante from adopcion.seguimiento where id = %s', aviso) == (False,)
    assert api.post('/api/v1/adopcion/seguimientos/999999999/marcar-enviado/').status_code == 404


@pytest.fixture
def ado_08(ado_07):
    """El aguacate quedó en readopción por abandono (ADO-07) y un vendedor lo ofrece a otro adoptante."""
    api, contrato, bien, dias = ado_07
    for dia in dias:
        _abandono(dia)
    api.post(f'/api/v1/adopcion/seguimientos/{_avisos_mora(bien)[-1]}/marcar-enviado/')
    assert _abandono(dias[-1] + timedelta(days=15)) == 1
    readopcion = {'bien': bien, 'autoriza_datos': True, 'autoriza_seguimiento': True, 'version_politica': '2026-10',
                  'medio_autorizacion': 'web', 'adoptante': {'tipo_documento': 'CC', 'numero_documento': 'PRB987654',
                                                            'nombres': 'Lucía', 'apellidos': 'Rojas'}}
    return api, readopcion, bien, contrato


def test_ado_08_readoptar_flujo_principal(ado_08):
    """ADO-08 · El contrato nace pendiente al precio de readopción y sin siembra; al pagar se activa, el bien vuelve a
    activo en su mismo sitio (con su fecha de siembra) y el nuevo adoptante paga la cuota desde el mes siguiente"""
    api, readopcion, bien, anterior = ado_08
    sembrado = _fila('select fecha_inicio, sitio_id from adopcion.bien where id = %s', bien)
    r = api.post('/api/v1/adopcion/contratos/readopcion/', readopcion, format='json')
    assert r.status_code == 201, r.data
    c = r.data
    assert (c['tipo'], c['precio'], c['modalidad_siembra'], c['estado']) == ('readopcion', '60000.00', 'no_aplica', 'pendiente_pago')
    assert c['cobro']['url_pago'].endswith(f"{c['predio']}:{c['numero']}")
    assert _fila('select estado from adopcion.bien where id = %s', bien) == ('en_readopcion',)  # hasta que pague
    a = _avisar(c['numero'], c['predio'], valor='60000.00')
    assert (a.status_code, a.data['estado']) == (200, 'activo'), a.data
    assert _fila('select estado, fecha_inicio, sitio_id from adopcion.bien where id = %s', bien) == ('activo', *sembrado)
    assert _fila('select estado from adopcion.contrato where id = %s', anterior) == ('terminado_abandono',)
    assert _fila("select f.total from comercial.pago p join comercial.factura f on f.id = p.factura_id where p.referencia = %s",
                 f"{c['predio']}:{c['numero']}") == (60000,)
    mes = (timezone.localdate().replace(day=1) + timedelta(days=32 * 5)).replace(day=1)
    _fila('select adopcion.generar_cuotas(%s)', mes)
    assert _fila('select count(*), min(valor) from adopcion.cuota where contrato_id = %s', c['id']) == (1, 25000)


def test_ado_08_bien_que_no_esta_en_readopcion_responde_400(ado_05):
    """Solo se readopta un bien en readopción: uno activo con su adoptante no"""
    api, cuota, _ = ado_05
    bien = _fila('select c.bien_id from adopcion.cuota q join adopcion.contrato c on c.id = q.contrato_id where q.id = %s', cuota)[0]
    r = api.post('/api/v1/adopcion/contratos/readopcion/', {
        'bien': bien, 'autoriza_datos': True, 'version_politica': '2026-10', 'medio_autorizacion': 'web',
        'adoptante': {'tipo_documento': 'CC', 'numero_documento': 'PRB987654', 'nombres': 'Lucía'}}, format='json')
    assert r.status_code == 400
    assert 'readopción' in str(r.data['bien'])


def test_ado_08_sin_autorizacion_de_datos_no_registra_nada(ado_08):
    """Ley 1581: sin autorización no hay contrato ni tercero nuevo"""
    api, readopcion, bien, _ = ado_08
    r = api.post('/api/v1/adopcion/contratos/readopcion/', {**readopcion, 'autoriza_datos': False}, format='json')
    assert r.status_code == 400
    assert _fila("select count(*) from adopcion.contrato where bien_id = %s and tipo = 'readopcion'", bien) == (0,)
    assert _fila("select count(*) from terceros.tercero where numero_documento = 'PRB987654'") == (0,)


def test_ado_08_si_otro_paga_primero_se_cancela_y_se_devuelve(ado_08):
    """Dos personas readoptan el mismo bien: gana quien paga primero y al otro se le devuelve el dinero"""
    api, readopcion, bien, _ = ado_08
    primero = api.post('/api/v1/adopcion/contratos/readopcion/', readopcion, format='json').data
    otra = {**readopcion, 'adoptante': {**readopcion['adoptante'], 'numero_documento': 'PRB555555', 'nombres': 'Marta'}}
    segundo = api.post('/api/v1/adopcion/contratos/readopcion/', otra, format='json').data
    assert _avisar(primero['numero'], primero['predio'], valor='60000.00').data['estado'] == 'activo'
    assert _avisar(segundo['numero'], segundo['predio'], valor='60000.00').data['estado'] == 'cancelado'
    assert _avisos('adopcion.pago_sin_bien', segundo['id']) == 1


@pytest.mark.skip(reason='ADO-09: por construir')
def test_ado_09_registrar_vender_productos_bien_flujo_principal():
    """ADO-09 · Registrar y vender productos del bien"""


@pytest.mark.skip(reason='ADO-10: por construir')
def test_ado_10_liquidar_productos_5_flujo_principal():
    """ADO-10 · Liquidar productos con el 5 %"""


@pytest.fixture
def ado_11(ado_05):
    """El aguacate sembrado de ADO-05; madurar(True) corre adopcion.marcar_madurez() pasados sus 48 meses."""
    api, cuota, _ = ado_05
    contrato, bien = _fila('select c.id, c.bien_id from adopcion.cuota q join adopcion.contrato c on c.id = q.contrato_id '
                           'where q.id = %s', cuota)

    def madurar():
        assert _fila("select adopcion.marcar_madurez((current_date + interval '48 months')::date)") == (1,)

    return api, contrato, bien, madurar


def _decidir(api, contrato, decision):
    return api.post(f'/api/v1/adopcion/contratos/{contrato}/decision/', {'decision': decision}, format='json')


def test_ado_11_decidir_madurez_mantener_liquidar_flujo_principal(ado_11):
    """ADO-11 · Con el bien maduro, el dueño decide liquidar: queda anotado con su fecha y se avisa al administrador"""
    api, contrato, bien, madurar = ado_11
    madurar()
    assert _fila('select estado from adopcion.bien where id = %s', bien) == ('maduro',)
    r = _decidir(api, contrato, 'liquidar')
    assert r.status_code == 200, r.data
    assert (r.data['decision_madurez'], r.data['estado'], r.data['decidido_en'] is not None) == ('liquidar', 'activo', True)
    assert _avisos('adopcion.decision_madurez', contrato) == 1


def test_ado_11_mantener_sigue_con_la_cuota(ado_11):
    """Mantener: el contrato sigue activo y el bien sigue pagando su cuota"""
    api, contrato, _, madurar = ado_11
    madurar()
    r = _decidir(api, contrato, 'mantener')
    assert (r.status_code, r.data['decision_madurez'], r.data['estado']) == (200, 'mantener', 'activo')


def test_ado_11_antes_de_la_madurez_responde_422(ado_11):
    """La base no deja decidir sobre un bien que todavía no llega a su madurez"""
    api, contrato, _, _ = ado_11
    r = _decidir(api, contrato, 'liquidar')
    assert r.status_code == 422
    assert _fila('select decision_madurez from adopcion.contrato where id = %s', contrato) == (None,)


def test_ado_11_decision_invalida_o_contrato_terminado(ado_11):
    """Solo mantener o liquidar, y solo sobre un contrato activo"""
    api, contrato, _, madurar = ado_11
    madurar()
    assert _decidir(api, contrato, 'vender').status_code == 400
    _fila("update adopcion.contrato set estado = 'terminado_abandono' where id = %s returning id", contrato)
    r = _decidir(api, contrato, 'liquidar')
    assert r.status_code == 400
    assert 'no está activo' in str(r.data['contrato'])


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
