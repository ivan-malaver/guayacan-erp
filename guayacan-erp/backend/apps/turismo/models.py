"""Modelos del esquema turismo: Alojamientos, planes turísticos y reservas (fase 3).

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «turismo». Django usa estas clases para leer y escribir
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
# Tabla turismo.alojamiento  ·  por finca (seguridad por filas)  ·  API: /api/v1/turismo/alojamientos/
# ==============================================================================================================
class Alojamiento(models.Model):
    """Cabaña o espacio de hospedaje."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código')
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    capacidad_personas = models.SmallIntegerField(db_comment='Huéspedes máximos')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ubicación')
    tarifa_noche = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Tarifa base por noche')
    activo = models.BooleanField(db_default=True, db_comment='Disponible')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "turismo", tabla "alojamiento" (las comillas separan esquema y tabla)
        db_table = 'turismo"."alojamiento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cabaña o espacio de hospedaje.'


# ==============================================================================================================
# Tabla turismo.plan_turistico  ·  por finca (seguridad por filas)  ·  API: /api/v1/turismo/planes-turistico/
# ==============================================================================================================
class PlanTuristico(models.Model):
    """Experiencia ofrecida (pasadía, recorrido del cacao, ordeño, taller)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    descripcion = models.TextField(db_comment='Qué incluye')
    duracion_horas = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, db_comment='Duración')
    cupo_maximo = models.SmallIntegerField(null=True, blank=True, db_comment='Personas por grupo')
    precio_persona = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio por persona')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "turismo", tabla "plan_turistico" (las comillas separan esquema y tabla)
        db_table = 'turismo"."plan_turistico'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Experiencia ofrecida (pasadía, recorrido del cacao, ordeño, taller).'


# ==============================================================================================================
# Tabla turismo.reserva  ·  por finca (seguridad por filas)  ·  API: /api/v1/turismo/reservas/
# ==============================================================================================================
class Reserva(models.Model):
    """Reserva de alojamiento o plan."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código')
    cliente = models.ForeignKey('terceros.Cliente', models.DO_NOTHING, db_column='cliente_id', related_name='+', db_constraint=False, db_comment='Cliente')
    alojamiento = models.ForeignKey('turismo.Alojamiento', models.DO_NOTHING, db_column='alojamiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Alojamiento')
    plan_turistico = models.ForeignKey('turismo.PlanTuristico', models.DO_NOTHING, db_column='plan_turistico_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Plan')
    fecha_inicio = models.DateField(db_comment='Llegada')
    fecha_fin = models.DateField(db_comment='Salida')
    personas = models.SmallIntegerField(db_comment='Número de personas')
    estado = models.CharField(max_length=10, choices=[('solicitada', 'solicitada'), ('confirmada', 'confirmada'), ('pagada', 'pagada'), ('cumplida', 'cumplida'), ('cancelada', 'cancelada')], db_default='solicitada', db_comment='Situación')
    total = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    valor_deposito = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Anticipo pagado para confirmar')
    checkin_en = models.DateTimeField(null=True, blank=True, db_comment='Llegada real')
    checkout_en = models.DateTimeField(null=True, blank=True, db_comment='Salida real')
    pedido = models.ForeignKey('comercial.Pedido', models.DO_NOTHING, db_column='pedido_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Pedido de cobro asociado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "turismo", tabla "reserva" (las comillas separan esquema y tabla)
        db_table = 'turismo"."reserva'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Reserva de alojamiento o plan.'


# ==============================================================================================================
# Tabla turismo.bloqueo_calendario  ·  por finca (seguridad por filas)  ·  API: /api/v1/turismo/bloqueos-calendario/
# ==============================================================================================================
class BloqueoCalendario(models.Model):
    """Fechas en que un alojamiento o un plan no está disponible (mantenimiento, uso familiar)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    alojamiento = models.ForeignKey('turismo.Alojamiento', models.DO_NOTHING, db_column='alojamiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Alojamiento')
    plan_turistico = models.ForeignKey('turismo.PlanTuristico', models.DO_NOTHING, db_column='plan_turistico_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Plan')
    desde = models.DateField(db_comment='Desde')
    hasta = models.DateField(db_comment='Hasta')
    motivo = models.CharField(max_length=150, db_comment='Motivo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "turismo", tabla "bloqueo_calendario" (las comillas separan esquema y tabla)
        db_table = 'turismo"."bloqueo_calendario'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Fechas en que un alojamiento o un plan no está disponible (mantenimiento, uso familiar).'
