"""Pruebas de aceptación de los casos de uso de personal.

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


@pytest.mark.skip(reason='PER-01: por construir')
def test_per_01_configurar_areas_responsabilidad_matriz_raci_flujo_principal():
    """PER-01 · Configurar áreas de responsabilidad y matriz RACI"""


@pytest.mark.skip(reason='PER-02: por construir')
def test_per_02_definir_plan_labores_flujo_principal():
    """PER-02 · Definir el plan de labores"""


@pytest.mark.skip(reason='PER-03: por construir')
def test_per_03_generar_tareas_dia_flujo_principal():
    """PER-03 · Generar las tareas del día"""


def _sql(consulta, *params):
    with connection.cursor() as cur:
        cur.execute(consulta, params)
        return cur.fetchone() if cur.description else None


@pytest.fixture
def per(en_finca):
    """Encargado con token, un área con Ana (miembro) y Beto (fuera del área), y una tarea del área para el 5 de diciembre."""
    usuario_id, predio_id = _sql('select u.id, f.predio_id from nucleo.usuario u cross join lateral nucleo.predios_del_usuario(u.id) f order by 2, 1 limit 1')
    en_finca(predio=predio_id, usuario=usuario_id)

    def empleado(nombre):
        tercero = _sql("insert into terceros.tercero (tipo_persona, tipo_documento, numero_documento, nombres) "
                       "values ('natural', 'CC', %s, %s) returning id", f'PRB-{nombre}', nombre)[0]
        return _sql("insert into terceros.empleado (tercero_id, cargo, tipo_vinculacion, fecha_ingreso) "
                    "values (%s, 'Operario', 'jornal', '2026-01-01') returning id", tercero)[0]

    ana, beto = empleado('Ana'), empleado('Beto')
    area = _sql("insert into personal.area_responsabilidad (codigo, nombre) values ('PRB-AVI', 'Avícola de prueba') returning id")[0]
    _sql("insert into personal.miembro_area (area_id, empleado_id, desde) values (%s, %s, '2026-01-01')", area, ana)
    cliente = APIClient()
    tokens = emitir_tokens(get_user_model().objects.get(pk=usuario_id), predio_id)
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['acceso']}")
    r = cliente.post('/api/v1/personal/tareas/', {'titulo': 'Recoger huevos galpón 1', 'fecha': '2026-12-05', 'area': area,
                     'prioridad': 'media', 'origen': 'manual', 'estado': 'pendiente'}, format='json')
    assert r.status_code == 201, r.data
    return cliente, r.data['id'], ana, beto


def _asignar(cliente, tarea_id, **datos):
    return cliente.patch(f'/api/v1/personal/tareas/{tarea_id}/', datos, format='json')


def _cuadrilla(*miembros):
    cuadrilla = _sql("insert into personal.cuadrilla (codigo, nombre) values ('PRB-C1', 'Cuadrilla de prueba') returning id")[0]
    for m in miembros:
        _sql("insert into personal.cuadrilla_miembro (cuadrilla_id, empleado_id, desde) values (%s, %s, '2026-01-01')", cuadrilla, m)
    return cuadrilla


def test_per_04_asignar_tarea_flujo_principal(per):
    """PER-04 · El encargado asigna a una persona del área disponible; la base lo acepta y sale el aviso para la PWA"""
    cliente, tarea, ana, _ = per
    r = _asignar(cliente, tarea, empleado=ana)
    assert (r.status_code, r.data['empleado']) == (200, ana)
    carga = _sql("select carga from nucleo.evento_salida where tipo_evento = 'personal.tarea_asignada' and entidad_id = %s", tarea)[0]
    assert json.loads(carga)['empleado_id'] == ana


def test_per_04_trabajador_de_vacaciones_no_disponible(per):
    """3b: de vacaciones (o en día de descanso) no está disponible"""
    cliente, tarea, ana, _ = per
    _sql("insert into personal.ausencia (empleado_id, tipo, desde, hasta) values (%s, 'vacaciones', '2026-12-01', '2026-12-10')", ana)
    r = _asignar(cliente, tarea, empleado=ana)
    assert r.status_code == 422
    assert 'disponible' in r.data['detalle']


def test_per_04_fuera_del_area_responde_422(per):
    """3c: no es del área de responsabilidad de la tarea"""
    cliente, tarea, _, beto = per
    r = _asignar(cliente, tarea, empleado=beto)
    assert r.status_code == 422
    assert 'de responsabilidad' in r.data['detalle']  # sin tildes: la base local tiene las originales mal codificadas


def test_per_04_sin_habilitacion_responde_422(per):
    """3a: la plantilla exige un curso que el trabajador no tiene"""
    cliente, tarea, ana, _ = per
    competencia = _sql("insert into formacion.competencia (codigo, nombre) values ('PRB-BIO', 'Bioseguridad') returning id")[0]
    plantilla = _sql("insert into personal.plantilla_tarea (codigo, nombre, proceso, recurrencia, competencia_id) "
                     "values ('PRB-HUE', 'Recoger huevos', 'avicola', 'diaria', %s) returning id", competencia)[0]
    assert _asignar(cliente, tarea, plantilla_tarea=plantilla).status_code == 200
    r = _asignar(cliente, tarea, empleado=ana)
    assert r.status_code == 422
    assert 'habilitado' in r.data['detalle']


def test_per_04_persona_y_cuadrilla_a_la_vez_no(per):
    """2a: persona y cuadrilla a la vez no se permite (CHECK)"""
    cliente, tarea, ana, _ = per
    r = _asignar(cliente, tarea, empleado=ana, cuadrilla=_cuadrilla(ana))
    assert (r.status_code, r.data['codigo']) == (422, 'valor_invalido')


def test_per_04_cuadrilla_revisa_cada_miembro(per):
    """Migración 003: la cuadrilla cumple disponibilidad y área miembro por miembro"""
    cliente, tarea, ana, beto = per
    cuadrilla = _cuadrilla(ana, beto)
    r = _asignar(cliente, tarea, cuadrilla=cuadrilla)
    assert r.status_code == 422
    assert f'{beto} de la cuadrilla no pertenece' in r.data['detalle']
    _sql("update personal.cuadrilla_miembro set hasta = '2026-11-30' where empleado_id = %s", beto)
    _sql("insert into personal.ausencia (empleado_id, tipo, desde, hasta) values (%s, 'permiso', '2026-12-05', '2026-12-05')", ana)
    r = _asignar(cliente, tarea, cuadrilla=cuadrilla)
    assert r.status_code == 422
    assert f'{ana} de la cuadrilla no est' in r.data['detalle']


def test_per_04_no_se_aprueba_por_el_crud(per):
    """Hueco cerrado: el PATCH no pone estado aprobada ni elige quién aprobó"""
    cliente, tarea, _, _ = per
    r = _asignar(cliente, tarea, estado='aprobada')
    assert r.status_code == 400
    assert 'aprobar' in str(r.data['estado'])
    r = _asignar(cliente, tarea, aprobado_por=1, iniciada_en='2026-12-05T06:00:00-05:00')
    assert (r.status_code, r.data['aprobado_por'], r.data['iniciada_en']) == (200, None, None)


def test_per_04_candidatos_del_area_disponibles(per):
    """Paso 1: los candidatos son los del área, disponibles y habilitados ese día"""
    cliente, tarea, ana, beto = per
    r = cliente.get(f'/api/v1/personal/tareas/{tarea}/candidatos/')
    assert r.status_code == 200
    ids = [c['empleado'] for c in r.data]
    assert ana in ids and beto not in ids
    _sql("insert into personal.ausencia (empleado_id, tipo, desde, hasta) values (%s, 'vacaciones', '2026-12-01', '2026-12-10')", ana)
    assert ana not in [c['empleado'] for c in cliente.get(f'/api/v1/personal/tareas/{tarea}/candidatos/').data]


def _cliente_de(empleado_id, rol='operario_granja'):
    """El trabajador inicia sesión con su propio usuario (por defecto operario: sin permiso para asignar ni aprobar)."""
    tercero, predio = _sql('select tercero_id, predio_id from terceros.empleado where id = %s', empleado_id)
    usuario = _sql("insert into nucleo.usuario (nombre_completo, correo, contrasena_hash, tercero_id) "
                   "values ('Trabajador de prueba', %s, 'x', %s) returning id", f'prb{empleado_id}{rol}@guayacan.local', tercero)[0]
    _sql("insert into nucleo.usuario_rol (usuario_id, rol_id) select %s, id from nucleo.rol where codigo = %s", usuario, rol)
    cliente = APIClient()
    tokens = emitir_tokens(get_user_model().objects.get(pk=usuario), predio)
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['acceso']}")
    return cliente


@pytest.fixture
def ejecucion(per):
    """La tarea de PER-04 asignada a Ana, con un paso; Ana y Beto (no asignado) con su propia sesión."""
    encargado, tarea, ana, beto = per
    assert _asignar(encargado, tarea, empleado=ana).status_code == 200
    r = encargado.post(f'/api/v1/personal/tareas/{tarea}/pasos/', {'tarea': tarea, 'orden': 1, 'descripcion': 'Desinfectar botas'},
                       format='json')
    assert r.status_code == 201, r.data
    return tarea, r.data['id'], _cliente_de(ana), _cliente_de(beto)


def test_per_05_ejecutar_tarea_evidencia_flujo_principal(ejecucion):
    """PER-05 · Ana inicia, marca el paso con una novedad, deja el video y termina con la cantidad; sale el aviso al aprobador"""
    tarea, paso, ana, _ = ejecucion
    r = _asignar(ana, tarea, estado='en_curso')
    assert (r.status_code, r.data['estado'], r.data['iniciada_en'] is not None) == (200, 'en_curso', True), r.data
    r = ana.patch(f'/api/v1/personal/tareas/{tarea}/pasos/{paso}/', {'hecho': True, 'observacion': 'Sin cal en el pediluvio'}, format='json')
    assert (r.status_code, r.data['hecho'], r.data['hecho_en'] is not None) == (200, True, True), r.data
    r = ana.post(f'/api/v1/personal/tareas/{tarea}/evidencias/', {'tarea': tarea, 'tipo': 'video',
                 'archivo_url': 'https://minio.local/evidencias/siembra.mp4'}, format='json')
    assert r.status_code == 201, r.data
    r = _asignar(ana, tarea, estado='terminada', cantidad=380)
    assert (r.status_code, r.data['estado'], r.data['terminada_en'] is not None) == (200, 'terminada', True), r.data
    carga = _sql("select carga from nucleo.evento_salida where tipo_evento = 'personal.tarea_terminada' and entidad_id = %s", tarea)[0]
    assert json.loads(carga)['cantidad'] == 380


def test_per_05_trabajador_no_asignado_recibe_403(ejecucion):
    """Quién ejecuta: Beto no está asignado; iniciar la tarea responde 403 y la tarea sigue pendiente"""
    tarea, _, _, beto = ejecucion
    r = _asignar(beto, tarea, estado='en_curso')
    assert (r.status_code, r.data['codigo']) == (403, 'sin_permiso')
    assert _sql('select estado from personal.tarea where id = %s', tarea) == ('pendiente',)


def test_per_05_no_asignado_tampoco_sin_conexion(ejecucion):
    """La regla está en la base: por la sincronización sin conexión Beto tampoco la inicia"""
    tarea, _, _, beto = ejecucion
    r = beto.post('/api/v1/sincronizacion/lote/', {'registros': [{
        'tabla': 'personal.tarea', 'operacion': 'actualizar', 'id': tarea, 'id_cliente': '0193a1b2-0000-7000-8000-000000000001',
        'capturado_en': '2026-11-19T06:00:00-05:00', 'datos': {'estado': 'en_curso'}}]}, format='json')
    assert r.data['resultados'][0]['estado'] == 'rechazado'
    assert 'Solo el trabajador asignado' in r.data['resultados'][0]['detalle']


def test_per_05_evidencia_solo_en_tarea_iniciada(ejecucion):
    """Una tarea pendiente todavía no recibe evidencias"""
    tarea, _, ana, _ = ejecucion
    r = ana.post(f'/api/v1/personal/tareas/{tarea}/evidencias/', {'tarea': tarea, 'tipo': 'foto',
                 'archivo_url': 'https://minio.local/evidencias/1.jpg'}, format='json')
    assert r.status_code == 422
    assert 'en curso o terminada' in r.data['detalle']


def test_per_05_miembro_de_la_cuadrilla_la_ejecuta(per):
    """La tarea asignada a una cuadrilla la inicia cualquiera de sus miembros"""
    encargado, tarea, ana, _ = per
    assert _asignar(encargado, tarea, cuadrilla=_cuadrilla(ana)).status_code == 200
    assert _asignar(_cliente_de(ana), tarea, estado='en_curso').status_code == 200


@pytest.fixture
def revision(per):
    """La tarea asignada a Ana y terminada por ella misma, lista para que el encargado la revise."""
    encargado, tarea, ana, beto = per
    assert _asignar(encargado, tarea, empleado=ana).status_code == 200
    cliente_ana = _cliente_de(ana)
    assert _asignar(cliente_ana, tarea, estado='en_curso').status_code == 200
    assert _asignar(cliente_ana, tarea, estado='terminada', cantidad=380).status_code == 200
    return encargado, tarea, ana, beto, cliente_ana


def _revisar(cliente, tarea, accion, **datos):
    return cliente.post(f'/api/v1/personal/tareas/{tarea}/{accion}/', datos, format='json')


def _aviso(tipo, tarea):
    fila = _sql('select carga from nucleo.evento_salida where tipo_evento = %s and entidad_id = %s', tipo, tarea)
    return json.loads(fila[0]) if fila else None


def test_per_06_aprobar_devolver_tarea_flujo_principal(revision):
    """PER-06 · El encargado aprueba: queda quién y cuándo, sale el aviso al trabajador y la tarea ya no se edita"""
    encargado, tarea, ana, _, _ = revision
    r = _revisar(encargado, tarea, 'aprobar')
    assert (r.status_code, r.data['estado'], r.data['aprobado_por'] is not None, r.data['aprobado_en'] is not None) == (
        200, 'aprobada', True, True), r.data
    assert _aviso('personal.tarea_aprobada', tarea)['empleado_id'] == ana
    r = _asignar(encargado, tarea, cantidad=400)
    assert r.status_code == 422
    assert 'no se edita' in r.data['detalle']


def test_per_06_devolver_exige_motivo_y_el_trabajador_la_retoma(revision):
    """2a: devolver sin motivo no se permite; con motivo queda devuelta, avisa y el trabajador la retoma en curso"""
    encargado, tarea, _, _, cliente_ana = revision
    assert _revisar(encargado, tarea, 'devolver').status_code == 400
    r = _revisar(encargado, tarea, 'devolver', motivo='Faltan los huevos del nido 4')
    assert (r.status_code, r.data['estado'], r.data['comentario_revision']) == (200, 'devuelta', 'Faltan los huevos del nido 4')
    assert _aviso('personal.tarea_devuelta', tarea)['motivo'] == 'Faltan los huevos del nido 4'
    assert _asignar(cliente_ana, tarea, estado='en_curso').status_code == 200


def test_per_06_sin_permiso_responde_403(revision):
    """2c: un operario sin permiso ni responsabilidad del área no aprueba"""
    _, tarea, _, beto, _ = revision
    r = _revisar(_cliente_de(beto), tarea, 'aprobar')
    assert (r.status_code, r.data['codigo']) == (403, 'sin_permiso')
    assert _sql('select estado from personal.tarea where id = %s', tarea) == ('terminada',)


def test_per_06_nadie_aprueba_su_propia_tarea(revision):
    """2b: aunque Ana tenga el rol de encargada, no aprueba la tarea que ella ejecutó (403)"""
    _, tarea, ana, _, _ = revision
    r = _revisar(_cliente_de(ana, rol='encargado_finca'), tarea, 'aprobar')
    assert (r.status_code, r.data['detalle']) == (403, 'Nadie aprueba su propia tarea')


def test_per_06_la_cuadrilla_tampoco_se_aprueba(per):
    """Migración 006: un miembro de la cuadrilla asignada no aprueba la tarea de su cuadrilla"""
    encargado, tarea, ana, beto = per
    _sql('insert into personal.miembro_area (area_id, empleado_id, desde) select area_id, %s, %s from personal.tarea where id = %s',
         beto, '2026-01-01', tarea)
    assert _asignar(encargado, tarea, cuadrilla=_cuadrilla(ana, beto)).status_code == 200
    cliente_ana = _cliente_de(ana)
    assert _asignar(cliente_ana, tarea, estado='en_curso').status_code == 200
    assert _asignar(cliente_ana, tarea, estado='terminada').status_code == 200
    r = _revisar(_cliente_de(beto, rol='encargado_finca'), tarea, 'aprobar')
    assert (r.status_code, r.data['detalle']) == (403, 'Nadie aprueba su propia tarea')


def test_per_06_solo_se_revisa_una_tarea_terminada(per):
    """Una tarea pendiente todavía no se aprueba"""
    encargado, tarea, _, _ = per
    r = _revisar(encargado, tarea, 'aprobar')
    assert r.status_code == 422
    assert 'terminada' in r.data['detalle']


@pytest.mark.skip(reason='PER-07: por construir')
def test_per_07_armar_publicar_cronograma_turnos_flujo_principal():
    """PER-07 · Armar y publicar el cronograma de turnos"""


@pytest.mark.skip(reason='PER-08: por construir')
def test_per_08_registrar_disponibilidad_ausencias_flujo_principal():
    """PER-08 · Registrar disponibilidad y ausencias"""


@pytest.mark.skip(reason='PER-09: por construir')
def test_per_09_registrar_jornada_carne_flujo_principal():
    """PER-09 · Registrar la jornada con el carné"""


@pytest.mark.skip(reason='PER-10: por construir')
def test_per_10_organizar_cuadrillas_flujo_principal():
    """PER-10 · Organizar cuadrillas"""
