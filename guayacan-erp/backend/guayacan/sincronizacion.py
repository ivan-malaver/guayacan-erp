"""NUC-05 · Sincronización de lo capturado sin conexión:  POST /api/v1/sincronizacion/lote/

PARA QUÉ
En el campo casi no hay señal. La app del celular guarda cada registro (postura, cosecha, tarea...) en el
teléfono y, cuando vuelve la señal, los envía en lotes a esta ruta.

FORMATO DEL CUERPO
    {"registros": [{"tabla": "produccion.registro_postura", "id_cliente": "<uuidv7>",
                    "capturado_en": "2026-10-28T06:10:00-05:00", "datos": {...campos del serializer...}}]}

RESPUESTA: por cada registro, uno de tres estados
    creado      se guardó ahora
    repetido    ya se había guardado antes (el celular lo reenvió): no se duplica
    rechazado   no cumple una regla; trae el mensaje para que la persona lo corrija

CÓMO EVITA DUPLICADOS (idempotencia)
El celular genera un id_cliente único (UUIDv7) por registro. El INSERT usa
ON CONFLICT (id_cliente) DO NOTHING: si ya existe, no hace nada. Reenviar el mismo lote es inofensivo.

OTRAS PROTECCIONES
- Cada registro va en su propio punto de guardado (transaction.atomic interno): uno rechazado no tumba a los demás.
- Solo se aceptan las tablas de guayacan/captura.py, así esta ruta no sirve para escribir en cualquier tabla.
- Máximo 200 registros por lote.
"""
import importlib

from django.apps import apps
from django.db import Error as ErrorBase
from django.db import connection, transaction
from django.db.models.expressions import DatabaseDefault
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .captura import TABLAS_CAPTURA
from .errores import datos_del_error

MAXIMO_LOTE = 200  # registros por petición


def _camel(s):
    """'registro_postura' -> 'RegistroPostura' (así se llaman las clases de los modelos)."""
    return ''.join(p.capitalize() for p in s.split('_'))


def _modelo_y_serializer(tabla):
    """De 'produccion.registro_postura' obtiene la clase del modelo y la de su serializer."""
    esquema, nombre = tabla.split('.')
    modelo = apps.get_model(esquema, _camel(nombre))
    modulo = importlib.import_module(f'apps.{esquema}.serializers')
    return modelo, getattr(modulo, f'{_camel(nombre)}Serializer')


def insertar_idempotente(modelo, datos_validos, id_cliente, capturado_en):
    """INSERT ... ON CONFLICT (id_cliente) DO NOTHING RETURNING id.

    Devuelve el id nuevo, o None si el registro ya existía. Se arma el SQL a mano porque el ORM de Django no
    ofrece «insertar o ignorar» devolviendo el id.
    """
    objeto = modelo(**datos_validos, id_cliente=id_cliente, capturado_en=capturado_en)
    columnas, valores = [], []
    for campo in modelo._meta.concrete_fields:
        if campo.primary_key or getattr(campo, 'generated', False):
            continue  # el id y las columnas calculadas las pone la base
        valor = getattr(objeto, campo.attname)
        if isinstance(valor, DatabaseDefault):
            continue  # que la base ponga su valor por defecto (finca, fechas, estados)
        columnas.append(connection.ops.quote_name(campo.column))       # nombre de columna entre comillas
        valores.append(campo.get_db_prep_save(valor, connection))      # valor convertido al formato de la base
    tabla = modelo._meta.db_table.replace('"."', '.')
    esquema, nombre = tabla.split('.')
    sql = (f'insert into {connection.ops.quote_name(esquema)}.{connection.ops.quote_name(nombre)} ({", ".join(columnas)}) '
           f'values ({", ".join(["%s"] * len(valores))}) on conflict (id_cliente) do nothing returning id')
    with connection.cursor() as cur:
        cur.execute(sql, valores)  # los valores van como parámetros, nunca pegados al texto
        fila = cur.fetchone()
    return fila[0] if fila else None


class RegistroSerializer(serializers.Serializer):
    """Un registro del lote."""
    tabla = serializers.ChoiceField(choices=sorted(TABLAS_CAPTURA))  # solo tablas de la lista blanca
    id_cliente = serializers.UUIDField()
    capturado_en = serializers.DateTimeField()
    datos = serializers.DictField()  # se validan después con el serializer propio de la tabla


class LoteSerializer(serializers.Serializer):
    """El lote completo: entre 1 y 200 registros."""
    registros = RegistroSerializer(many=True, allow_empty=False, max_length=MAXIMO_LOTE)


class SincronizarLote(APIView):
    """Recibe el lote y responde el estado de cada registro (siempre 200; el detalle va por registro)."""

    def post(self, request):
        lote = LoteSerializer(data=request.data)
        lote.is_valid(raise_exception=True)
        resultados = []
        for r in lote.validated_data['registros']:
            base = {'tabla': r['tabla'], 'id_cliente': str(r['id_cliente'])}
            modelo, clase_serializer = _modelo_y_serializer(r['tabla'])
            ser = clase_serializer(data=r['datos'])
            if not ser.is_valid():
                # Datos mal formados (falta un campo, tipo equivocado): se rechaza solo este registro
                resultados.append({**base, 'estado': 'rechazado', 'detalle': ser.errors})
                continue
            try:
                with transaction.atomic():  # punto de guardado: si este falla, los anteriores siguen guardados
                    nuevo = insertar_idempotente(modelo, ser.validated_data, r['id_cliente'], r['capturado_en'])
                resultados.append({**base, 'estado': 'creado' if nuevo else 'repetido', 'id': nuevo})
            except ErrorBase as exc:
                # Una regla de la base lo rechazó: se devuelve su mensaje en español
                _, mensaje, _, _ = datos_del_error(exc)
                resultados.append({**base, 'estado': 'rechazado', 'detalle': mensaje})
        return Response({'resultados': resultados}, status=status.HTTP_200_OK)
