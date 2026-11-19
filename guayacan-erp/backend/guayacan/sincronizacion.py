"""NUC-05 · Sincronización de lo capturado sin conexión:  POST /api/v1/sincronizacion/lote/

PARA QUÉ
En el campo casi no hay señal. La app del celular guarda cada registro (postura, cosecha, tarea...) en el
teléfono y, cuando vuelve la señal, los envía en lotes a esta ruta.

FORMATO DEL CUERPO
    {"registros": [{"tabla": "produccion.registro_postura", "id_cliente": "<uuidv7>",
                    "capturado_en": "2026-10-28T06:10:00-05:00", "datos": {...campos del serializer...}}]}

CAMBIOS A REGISTROS QUE YA EXISTEN (p. ej. iniciar y terminar una tarea sin señal)
    {"tabla": "personal.tarea", "operacion": "actualizar", "id": 15, "id_cliente": "<uuidv7>",
     "capturado_en": "2026-12-05T06:05:00-05:00", "datos": {"estado": "en_curso"}}
Solo se aceptan los campos de ACTUALIZABLES. Gana el cambio capturado más tarde (columna capturado_en), así
reenviar el lote no repite nada y un cambio viejo no pisa uno nuevo. Los registros se aplican en el orden en que se
capturaron, y las reglas de la base (disparadores) valen igual que en la API.

RESPUESTA: por cada registro, en el orden en que se capturaron, uno de estos estados
    creado       se guardó ahora
    repetido     ya se había guardado antes (el celular lo reenvió): no se duplica
    actualizado  el cambio se aplicó
    obsoleto     ya había un cambio igual o más reciente: no se aplica
    rechazado    no cumple una regla; trae el mensaje para que la persona lo corrija

CÓMO EVITA DUPLICADOS (idempotencia)
El celular genera un id_cliente único (UUIDv7) por registro. El INSERT usa
ON CONFLICT (id_cliente) DO NOTHING: si ya existe, no hace nada. Reenviar el mismo lote es inofensivo.

OTRAS PROTECCIONES
- Cada registro va en su propio punto de guardado (transaction.atomic interno): uno rechazado no tumba a los demás.
- Solo se aceptan las tablas de guayacan/captura.py, así esta ruta no sirve para escribir en cualquier tabla.
- Máximo 200 registros por lote.
"""
import importlib
from datetime import timedelta

from django.apps import apps
from django.db import Error as ErrorBase
from django.db import connection, transaction
from django.db.models.expressions import DatabaseDefault
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .captura import TABLAS_CAPTURA
from .errores import datos_del_error

# Cambios que el celular puede hacer sin conexión sobre registros que ya existen: solo lo que hace el trabajador en el
# campo (iniciar y terminar su tarea, la cantidad, marcar pasos). Nunca quién aprobó ni las fechas de control.
# None = cualquier valor que acepte el serializer de la tabla; un conjunto = solo esos valores.
ACTUALIZABLES = {
    'personal.tarea': {'estado': {'en_curso', 'terminada'}, 'cantidad': None},
    'personal.paso_tarea': {'hecho': None},
}
# La hora de un cambio sin conexión es la del celular, no la de la sincronización
HORA_DEL_CAMBIO = {
    ('personal.tarea', 'estado', 'en_curso'): 'iniciada_en',
    ('personal.tarea', 'estado', 'terminada'): 'terminada_en',
    ('personal.paso_tarea', 'hecho', True): 'hecho_en',
}
TOLERANCIA_RELOJ = timedelta(minutes=5)  # un celular algo adelantado se acepta; uno en el futuro no

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


def actualizar_si_es_mas_reciente(tabla, modelo, pk, datos, capturado_en):
    """UPDATE ... WHERE id = pk AND (capturado_en IS NULL OR capturado_en < la hora del celular) RETURNING id.

    Gana el cambio capturado más tarde: reenviar un lote, o que llegue tarde un «iniciar» viejo, no deshace un
    «terminar». Devuelve el id, o None si ya se había aplicado un cambio igual o más reciente.
    """
    campos = {modelo._meta.get_field(c): v for c, v in datos.items()}
    for (t, campo, valor), hora in HORA_DEL_CAMBIO.items():
        if t == tabla and datos.get(campo) == valor:
            campos[modelo._meta.get_field(hora)] = capturado_en
    campos[modelo._meta.get_field('capturado_en')] = capturado_en
    esquema, nombre = modelo._meta.db_table.replace('"."', '.').split('.')
    sql = (f'update {connection.ops.quote_name(esquema)}.{connection.ops.quote_name(nombre)} set '
           + ', '.join(f'{connection.ops.quote_name(f.column)} = %s' for f in campos)
           + ' where id = %s and (capturado_en is null or capturado_en < %s) returning id')
    valores = [f.get_db_prep_save(v, connection) for f, v in campos.items()]
    with connection.cursor() as cur:
        cur.execute(sql, [*valores, pk, capturado_en])
        fila = cur.fetchone()
    return fila[0] if fila else None


class RegistroSerializer(serializers.Serializer):
    """Un registro del lote."""
    tabla = serializers.ChoiceField(choices=sorted(TABLAS_CAPTURA))  # solo tablas de la lista blanca
    id_cliente = serializers.UUIDField()
    capturado_en = serializers.DateTimeField()
    operacion = serializers.ChoiceField(choices=['crear', 'actualizar'], default='crear')
    id = serializers.IntegerField(required=False)  # al actualizar: el id del registro en el servidor
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
        # En el orden en que pasaron en el campo: iniciar, marcar pasos, terminar (sin importar cómo llegaron)
        for r in sorted(lote.validated_data['registros'], key=lambda r: r['capturado_en']):
            base = {'tabla': r['tabla'], 'id_cliente': str(r['id_cliente'])}
            modelo, clase_serializer = _modelo_y_serializer(r['tabla'])
            if r['capturado_en'] > timezone.now() + TOLERANCIA_RELOJ:
                resultados.append({**base, 'estado': 'rechazado', 'detalle': 'La hora del celular está en el futuro'})
                continue
            if r['operacion'] == 'actualizar':
                resultados.append({**base, **self.actualizar(r, modelo, clase_serializer)})
                continue
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

    @staticmethod
    def actualizar(r, modelo, clase_serializer):
        """Un cambio hecho sin conexión sobre un registro existente. Devuelve el estado para la respuesta."""
        permitidos = ACTUALIZABLES.get(r['tabla'])
        if not permitidos:
            return {'estado': 'rechazado', 'detalle': 'Esta tabla no admite cambios sin conexión'}
        if fuera := sorted(set(r['datos']) - set(permitidos)):
            return {'estado': 'rechazado', 'detalle': f'Sin conexión no se puede cambiar: {", ".join(fuera)}'}
        instancia = modelo.objects.filter(pk=r.get('id')).first()  # la seguridad por filas solo deja ver la finca
        if not instancia:
            return {'estado': 'rechazado', 'detalle': 'No existe el registro a cambiar'}
        ser = clase_serializer(instancia, data=r['datos'], partial=True)
        if not ser.is_valid():
            return {'estado': 'rechazado', 'detalle': ser.errors}
        for campo, valores in permitidos.items():
            if valores and campo in ser.validated_data and ser.validated_data[campo] not in valores:
                return {'estado': 'rechazado', 'detalle': f'Sin conexión {campo} solo puede ser: {", ".join(sorted(valores))}'}
        try:
            with transaction.atomic():  # las reglas de la base (disparadores) valen igual que en la API
                cambiado = actualizar_si_es_mas_reciente(r['tabla'], modelo, instancia.pk, ser.validated_data, r['capturado_en'])
        except ErrorBase as exc:
            return {'estado': 'rechazado', 'detalle': datos_del_error(exc)[1]}
        return {'estado': 'actualizado' if cambiado else 'obsoleto', 'id': instancia.pk}
