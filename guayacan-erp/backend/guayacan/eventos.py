"""Publicación de eventos con el patrón «outbox» (bandeja de salida).

PROBLEMA QUE RESUELVE
Cuando se confirma un pedido, otros procesos deben enterarse (el agente de WhatsApp, las integraciones). Si se
avisara directamente y luego la transacción fallara, se habría anunciado algo que no ocurrió.

SOLUCIÓN
El hecho de negocio y su evento se guardan juntos, en la misma transacción, en la tabla nucleo.evento_salida.
Después, la tarea de Celery guayacan.tareas.publicar_eventos los entrega a Redis Streams, de donde los leen
MongoDB, el servicio de agentes y las integraciones. Si la transacción falla, el evento tampoco existe.
"""
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection


def publicar(tipo_evento, entidad, entidad_id, carga):
    """Escribe un evento en nucleo.evento_salida. Llamarla dentro de la transacción del caso de uso.

    tipo_evento  qué pasó, en minúscula con punto, p. ej. 'pedido.confirmado'
    entidad      tabla del registro, p. ej. 'comercial.pedido'
    entidad_id   id del registro
    carga        diccionario con los datos útiles para quien escuche el evento

    Ejemplo: publicar('pedido.confirmado', 'comercial.pedido', pedido.id, {'total': str(pedido.total)})
    Devuelve el id del evento creado.
    """
    with connection.cursor() as cur:
        # DjangoJSONEncoder sabe convertir fechas y decimales a JSON
        cur.execute('insert into nucleo.evento_salida (tipo_evento, entidad, entidad_id, carga) values (%s, %s, %s, %s) returning id',
                    [tipo_evento, entidad, entidad_id, json.dumps(carga, cls=DjangoJSONEncoder)])
        return cur.fetchone()[0]
