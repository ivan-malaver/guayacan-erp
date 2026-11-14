"""Tareas en segundo plano de Celery.

QUÉ ES CELERY
Un programa aparte («worker») que ejecuta tareas fuera de las peticiones web. «Celery Beat» es el reloj que
las lanza a la hora programada (la agenda está en config/celery.py). Redis es la cola donde se dejan las tareas.

IDEA PRINCIPAL
Las tareas de negocio no tienen lógica en Python: solo llaman funciones de PostgreSQL, que ya están probadas.
Python se encarga de recorrer las fincas y de fijar la sesión de cada una (igual que contexto.py en la web).
"""
import json
import logging

from celery import shared_task
from django.conf import settings
from django.db import connections, transaction

log = logging.getLogger(__name__)
CONEXION = 'default'  # conexión con el usuario de la API (respeta la seguridad por filas)


def _fincas():
    """Ids de todas las fincas. nucleo.predio tiene seguridad por filas, por eso se leen con la conexión admin."""
    with connections['admin'].cursor() as cur:
        cur.execute('select id from nucleo.predio order by id')
        return [f[0] for f in cur.fetchall()]


def _con_contexto(predio_id, sql):
    """Ejecuta una sentencia SQL «como» la finca indicada, en su propia transacción."""
    with transaction.atomic(using=CONEXION), connections[CONEXION].cursor() as cur:
        # Sin usuario ni agente: es el sistema el que actúa
        cur.execute("select set_config('app.predio_id', %s, true), set_config('app.usuario_id', '', true), "
                    "set_config('app.agente_id', '', true)", [str(predio_id) if predio_id else ''])
        cur.execute(sql)
        return cur.fetchall() if cur.description else None


@shared_task(name='guayacan.tareas.por_finca')
def por_finca(sql):
    """Corre una función de la base una vez por cada finca, con la seguridad por filas de esa finca.

    Ejemplo (config/celery.py): por_finca('select comercial.actualizar_mora()')
    """
    for predio in _fincas():
        try:
            _con_contexto(predio, sql)
        except Exception:  # noqa: BLE001  una finca con error no detiene a las demás
            log.exception('Tarea fallida en la finca %s: %s', predio, sql)


@shared_task(name='guayacan.tareas.global_')
def global_(sql):
    """Funciones de mantenimiento que no dependen de una finca (crear particiones, revisar copias)."""
    with transaction.atomic(using='admin'), connections['admin'].cursor() as cur:
        cur.execute(sql)


@shared_task(name='guayacan.tareas.publicar_eventos')
def publicar_eventos(limite=200):
    """Entrega los eventos pendientes del outbox (nucleo.evento_salida) a Redis Streams.

    De ahí los leen MongoDB, el servicio de agentes y las integraciones. Corre cada 10 segundos.
    """
    import redis  # se importa aquí porque solo esta tarea lo usa (viene con celery[redis])

    r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    for predio in _fincas():
        # Una transacción por finca: bloquea los pendientes, los entrega y los marca; si Redis falla, nada cambia
        with transaction.atomic(using=CONEXION), connections[CONEXION].cursor() as cur:
            cur.execute("select set_config('app.predio_id', %s, true)", [str(predio)])
            # FOR UPDATE SKIP LOCKED: si otro worker ya tomó un evento, este lo salta (no se publica dos veces)
            cur.execute("select id, tipo_evento, entidad, entidad_id, carga from nucleo.evento_salida where estado = 'pendiente' "
                        "order by creado_en limit %s for update skip locked", [int(limite)])
            filas = cur.fetchall()
            for id_, tipo, entidad, entidad_id, carga in filas:
                # xadd agrega un mensaje al stream 'guayacan.eventos'
                r.xadd('guayacan.eventos', {'predio_id': predio, 'id': id_, 'tipo': tipo, 'entidad': entidad,
                                            'entidad_id': entidad_id, 'carga': json.dumps(carga)})
            if filas:
                cur.execute("update nucleo.evento_salida set estado = 'publicado', publicado_en = now(), intentos = intentos + 1 "
                            "where id = any(%s)", [[f[0] for f in filas]])
