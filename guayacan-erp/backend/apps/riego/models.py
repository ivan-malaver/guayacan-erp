"""Modelos del esquema riego: Fuentes de agua, tanques, sistemas de riego, válvulas y eventos de riego (manual hoy, automático en la fase IoT).

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «riego». Django usa estas clases para leer y escribir
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
# Tabla riego.fuente_agua  ·  por finca (seguridad por filas)  ·  API: /api/v1/riego/fuentes-agua/
# ==============================================================================================================
class FuenteAgua(models.Model):
    """De dónde sale el agua (nacedero, acueducto veredal, lluvia, pozo) y su permiso."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    tipo = models.CharField(max_length=17, choices=[('nacedero', 'nacedero'), ('acueducto_veredal', 'acueducto_veredal'), ('lluvia', 'lluvia'), ('pozo', 'pozo'), ('quebrada', 'quebrada')], db_comment='Tipo de fuente')
    caudal_l_s = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, db_comment='Caudal disponible en litros por segundo')
    requiere_concesion = models.BooleanField(db_default=True, db_comment='Si necesita concesión de la CAR')
    numero_concesion = models.CharField(max_length=40, null=True, blank=True, db_comment='Número de resolución de la CAR; vacío = en trámite')
    concesion_vence = models.DateField(null=True, blank=True, db_comment='Vencimiento de la concesión')
    apta_consumo_humano = models.BooleanField(db_default=False, db_comment='Si el último análisis la declara potable')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "riego", tabla "fuente_agua" (las comillas separan esquema y tabla)
        db_table = 'riego"."fuente_agua'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'De dónde sale el agua (nacedero, acueducto veredal, lluvia, pozo) y su permiso.'


# ==============================================================================================================
# Tabla riego.tanque  ·  por finca (seguridad por filas)  ·  API: /api/v1/riego/tanques/
# ==============================================================================================================
class Tanque(models.Model):
    """Tanques de almacenamiento (hoy: dos de 2.000 litros)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. TQ-01')
    capacidad_litros = models.IntegerField(db_comment='Capacidad')
    fuente_agua = models.ForeignKey('riego.FuenteAgua', models.DO_NOTHING, db_column='fuente_agua_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Fuente que lo llena')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ubicación')
    sensor_nivel = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_nivel_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sensor de nivel (fase IoT)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "riego", tabla "tanque" (las comillas separan esquema y tabla)
        db_table = 'riego"."tanque'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Tanques de almacenamiento (hoy: dos de 2.000 litros).'


# ==============================================================================================================
# Tabla riego.sistema_riego  ·  por finca (seguridad por filas)  ·  API: /api/v1/riego/sistemas-riego/
# ==============================================================================================================
class SistemaRiego(models.Model):
    """Red de riego que cubre una o varias zonas (hoy: manguera con aspersores)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    tipo = models.CharField(max_length=14, choices=[('aspersion', 'aspersion'), ('goteo', 'goteo'), ('microaspersion', 'microaspersion'), ('manual', 'manual')], db_comment='Tecnología')
    tanque = models.ForeignKey('riego.Tanque', models.DO_NOTHING, db_column='tanque_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tanque que lo alimenta')
    caudal_l_min = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, db_comment='Caudal nominal')
    modo_control = models.CharField(max_length=10, choices=[('manual', 'manual'), ('programado', 'programado'), ('automatico', 'automatico')], db_default='manual', db_comment='Cómo se acciona hoy')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "riego", tabla "sistema_riego" (las comillas separan esquema y tabla)
        db_table = 'riego"."sistema_riego'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Red de riego que cubre una o varias zonas (hoy: manguera con aspersores).'


# ==============================================================================================================
# Tabla riego.valvula  ·  por finca (seguridad por filas)  ·  API: /api/v1/riego/valvulas/
# ==============================================================================================================
class Valvula(models.Model):
    """Cada válvula del sistema (hoy manual en cada aspersor; luego electroválvula)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    sistema_riego = models.ForeignKey('riego.SistemaRiego', models.DO_NOTHING, db_column='sistema_riego_id', related_name='+', db_constraint=False, db_comment='Sistema al que pertenece')
    codigo = models.CharField(max_length=20, db_comment='Código, ej. V-03')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Zona que riega')
    tipo = models.CharField(max_length=14, choices=[('manual', 'manual'), ('electrovalvula', 'electrovalvula')], db_default='manual', db_comment='Manual o eléctrica')
    actuador = models.ForeignKey('iot.Actuador', models.DO_NOTHING, db_column='actuador_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Actuador IoT que la abre (fase IoT)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "riego", tabla "valvula" (las comillas separan esquema y tabla)
        db_table = 'riego"."valvula'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cada válvula del sistema (hoy manual en cada aspersor; luego electroválvula).'


# ==============================================================================================================
# Tabla riego.evento_riego  ·  por finca (seguridad por filas)  ·  API: /api/v1/riego/eventos-riego/
# ==============================================================================================================
class EventoRiego(models.Model):
    """Cada riego hecho: cuánto tiempo, cuánta agua y si fue manual o automático."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    valvula = models.ForeignKey('riego.Valvula', models.DO_NOTHING, db_column='valvula_id', related_name='+', db_constraint=False, db_comment='Válvula abierta')
    inicio = models.DateTimeField(db_comment='Apertura')
    fin = models.DateTimeField(null=True, blank=True, db_comment='Cierre')
    litros_estimados = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True, db_comment='Litros aplicados (caudal × tiempo)')
    modo = models.CharField(max_length=10, choices=[('manual', 'manual'), ('programado', 'programado'), ('automatico', 'automatico')], db_comment='Quién lo accionó')
    registrado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='registrado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Operario, si fue manual')
    regla = models.ForeignKey('iot.ReglaAutomatizacion', models.DO_NOTHING, db_column='regla_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Regla que lo disparó, si fue automático')
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
        # Nombre real en PostgreSQL: esquema "riego", tabla "evento_riego" (las comillas separan esquema y tabla)
        db_table = 'riego"."evento_riego'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cada riego hecho: cuánto tiempo, cuánta agua y si fue manual o automático.'
