"""Modelos del esquema ambiental: Mediciones ambientales (energía solar, biogás, compost, agua) y factores de emisión con su fuente.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «ambiental». Django usa estas clases para leer y escribir
filas sin escribir SQL a mano: models.<Clase>.objects.filter(...), .create(...), etc.

CÓMO SE CREÓ
Lo generó docs/uml/fuentes/gen_apps.py a partir de specs/modelo-datos/generador/modelo.py (y modelo_apendice_a.py).
No lo edite a mano: si cambia una tabla, cambie el modelo y vuelva a generar.

POR QUÉ managed = False
La base de datos la crea specs/modelo-datos/esquema_postgresql.sql (y apendice_a_adopcion.sql), con sus reglas,
seguridad por filas y auditoría. Django solo la usa; nunca crea, altera ni borra estas tablas (no hay migraciones).

CÓMO LEER UN CAMPO
  models.CharField(max_length=20)      texto corto de máximo 20 caracteres (varchar)
  models.TextField()                   texto largo (text)
  models.DecimalField(14, 2)           número con decimales exactos, p. ej. dinero (numeric)
  models.DateField / DateTimeField     fecha / fecha y hora con zona horaria (date / timestamptz)
  models.BooleanField                  sí o no (boolean)
  models.ForeignKey('app.Clase', ...)  llave foránea: el valor es el id de una fila de otra tabla
  choices=[...]                        lista cerrada de valores; la base los valida con un CHECK
  null=True, blank=True                el dato puede quedar vacío
  db_default=...                       valor que pone la base si no se envía (Django no lo manda en el INSERT)
  db_comment='...'                     significado del dato (queda como comentario en PostgreSQL)
Opciones de las llaves foráneas:
  models.DO_NOTHING      Django no borra en cascada: la base decide (y en este sistema casi nada se borra)
  db_constraint=False    la llave real ya existe en la base (a veces compuesta con predio_id); Django no la recrea
  related_name='+'       no se crea el acceso inverso desde la otra tabla (evita choques de nombres entre 26 apps)
"""
# ArrayField, Now, VectorField, Geometria y sql se importan siempre porque algunos esquemas los usan;
# «noqa: F401» le dice al revisor de estilo (ruff) que no avise si en este esquema en particular no se usan.
from django.contrib.postgres.fields import ArrayField  # noqa: F401  (listas de PostgreSQL, p. ej. text[])
from django.db import models
from django.db.models.functions import Now  # noqa: F401  (fecha y hora actual calculada por la base)
from pgvector.django import VectorField  # noqa: F401  (vectores para búsquedas semánticas de la IA)

from guayacan.db import Geometria, sql  # noqa: F401  (columnas de mapas sin GeoDjango y valores calculados por SQL)


# ==============================================================================================================
# Tabla ambiental.factor_emision  ·  catálogo compartido entre fincas  ·  API: /api/v1/ambiental/factores-emision/
# ==============================================================================================================
class FactorEmision(models.Model):
    """Factor para convertir una medición en CO₂ equivalente, con su fuente; sin fuente no se publica ninguna cifra."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    magnitud = models.CharField(max_length=40, db_comment='Magnitud, ej. kwh_solar')
    factor_kgco2e = models.DecimalField(max_digits=12, decimal_places=6, db_comment='kg de CO₂ equivalente evitados por unidad')
    fuente = models.CharField(max_length=300, db_comment='Documento oficial del que sale el factor')
    vigente_desde = models.DateField(db_comment='Desde')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ambiental", tabla "factor_emision" (las comillas separan esquema y tabla)
        db_table = 'ambiental"."factor_emision'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Factor para convertir una medición en CO₂ equivalente, con su fuente; sin fuente no se publica ninguna cifra.'


# ==============================================================================================================
# Tabla ambiental.registro_ambiental  ·  por finca (seguridad por filas)  ·  API: /api/v1/ambiental/registros-ambiental/
# ==============================================================================================================
class RegistroAmbiental(models.Model):
    """Medición ambiental de la finca (energía solar, biogás, compost, humus, agua)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    magnitud = models.CharField(max_length=23, choices=[('kwh_solar', 'kwh_solar'), ('m3_biogas', 'm3_biogas'), ('kg_compost', 'kg_compost'), ('kg_humus', 'kg_humus'), ('litros_agua_reutilizada', 'litros_agua_reutilizada'), ('litros_agua_consumida', 'litros_agua_consumida')], db_comment='Qué se midió')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad')
    fecha = models.DateField(db_comment='Día')
    origen = models.CharField(max_length=6, choices=[('sensor', 'sensor'), ('manual', 'manual')], db_comment='Cómo se obtuvo')
    sensor = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sensor, si aplica')
    # Captura sin conexión: el celular genera id_cliente (UUIDv7); si el mismo registro llega dos veces,
    # la base lo detecta por este campo único y no lo duplica (ver guayacan/sincronizacion.py)
    id_cliente = models.UUIDField(null=True, blank=True, unique=True, db_comment='UUIDv7 del celular (sincronización idempotente)')
    capturado_en = models.DateTimeField(null=True, blank=True, db_comment='Momento de la captura en el dispositivo')
    dispositivo_captura = models.ForeignKey('nucleo.DispositivoCaptura', models.DO_NOTHING, db_column='dispositivo_captura_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Dispositivo con que se capturó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ambiental", tabla "registro_ambiental" (las comillas separan esquema y tabla)
        db_table = 'ambiental"."registro_ambiental'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Medición ambiental de la finca (energía solar, biogás, compost, humus, agua).'
