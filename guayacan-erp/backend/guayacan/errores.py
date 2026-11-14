"""Traduce los errores de PostgreSQL a respuestas HTTP con el mensaje en español de la regla de la base.

POR QUÉ
Las reglas de negocio viven en PostgreSQL. Cuando una regla rechaza algo, la base lanza un error con un código
de 5 caracteres (SQLSTATE) y un mensaje en español. Este módulo convierte ese error en una respuesta clara para
el frontend, sin que cada vista tenga que capturarlo. Se registra en settings: REST_FRAMEWORK['EXCEPTION_HANDLER'].

TABLA DE TRADUCCIÓN
| SQLSTATE        | Origen                                  | HTTP |
| P0001           | raise exception de una regla de negocio | 422  |
| 42501           | seguridad por filas o permiso           | 403  |
| 23505           | único repetido                          | 409  |
| 23P01           | exclusión (cruce de reservas o turnos)  | 409  |
| 23514           | restricción CHECK                       | 422  |
| 23503           | llave foránea                           | 422  |
| 23502           | dato obligatorio vacío                  | 422  |
| 40001, 40P01    | serialización o interbloqueo            | 503  |
Cualquier otro código responde 500 sin mostrar detalles internos (y queda en el registro del servidor).
"""
import logging

from django.db import Error as ErrorBase
from rest_framework.response import Response
from rest_framework.views import exception_handler

log = logging.getLogger(__name__)

# SQLSTATE -> (código HTTP, código corto que lee el frontend en core/errores/errores.ts)
TABLA = {
    'P0001': (422, 'regla_negocio'),
    '42501': (403, 'sin_permiso'),
    '23505': (409, 'duplicado'),
    '23P01': (409, 'cruce'),
    '23514': (422, 'valor_invalido'),
    '23503': (422, 'referencia_invalida'),
    '23502': (422, 'dato_obligatorio'),
    '40001': (503, 'reintentar'),
    '40P01': (503, 'reintentar'),
}


def datos_del_error(exc):
    """Saca SQLSTATE, mensaje, restricción y columna del error de psycopg que Django envuelve.

    Django convierte el error del conector (psycopg) en su propio tipo y guarda el original en __cause__.
    El objeto diag del error original trae los detalles que envía PostgreSQL.
    """
    causa = getattr(exc, '__cause__', None) or exc
    estado = getattr(causa, 'sqlstate', None) or getattr(causa, 'pgcode', None)
    diag = getattr(causa, 'diag', None)
    mensaje = getattr(diag, 'message_primary', None) or str(causa).split('\n')[0]
    restriccion = getattr(diag, 'constraint_name', None)  # p. ej. el nombre del índice único violado
    columna = getattr(diag, 'column_name', None)          # p. ej. el campo obligatorio que vino vacío
    return estado, mensaje, restriccion, columna


def respuesta_de_base(exc):
    """Arma la respuesta HTTP para un error de la base."""
    estado, mensaje, restriccion, columna = datos_del_error(exc)
    status, codigo = TABLA.get(estado, (500, 'error_base'))
    # En errores 500 no se muestra el mensaje real: podría revelar datos internos
    cuerpo = {'codigo': codigo, 'detalle': mensaje if status != 500 else 'Error interno de la base de datos'}
    if restriccion:
        cuerpo['restriccion'] = restriccion
    if columna:
        cuerpo['campo'] = columna
    if status == 500:
        log.exception('Error de base sin traducir (SQLSTATE %s)', estado)
    respuesta = Response(cuerpo, status=status)
    if status == 503:
        respuesta['Retry-After'] = '1'  # le indica al cliente que reintente en 1 segundo
    return respuesta


def manejar_error(exc, context):
    """Manejador global de errores de la API: los de la base se traducen; los demás los maneja DRF como siempre."""
    if isinstance(exc, ErrorBase):
        return respuesta_de_base(exc)
    return exception_handler(exc, context)
