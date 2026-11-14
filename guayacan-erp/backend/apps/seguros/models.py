"""Modelos del esquema seguros: Pólizas, bienes asegurados, índices de seguros paramétricos y avisos de siniestro con evidencia.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «seguros». Django usa estas clases para leer y escribir
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
# Tabla seguros.poliza  ·  por finca (seguridad por filas)  ·  API: /api/v1/seguros/polizas/
# ==============================================================================================================
class Poliza(models.Model):
    """Póliza (cultivo, animales, equipos, responsabilidad civil del dron, paramétrico) con vigencia, prima, suma asegurada e incentivo de Finagro."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    numero = models.CharField(max_length=40, db_comment='Número')
    aseguradora = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='aseguradora_id', related_name='+', db_constraint=False, db_comment='Aseguradora')
    corredor = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='corredor_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Corredor')
    tipo = models.CharField(max_length=21, choices=[('cultivo', 'cultivo'), ('animales', 'animales'), ('equipos', 'equipos'), ('vehiculo', 'vehiculo'), ('responsabilidad_civil', 'responsabilidad_civil'), ('dron', 'dron'), ('parametrico', 'parametrico'), ('vida', 'vida'), ('otro', 'otro')], db_comment='Tipo')
    desde = models.DateField(db_comment='Inicio')
    hasta = models.DateField(db_comment='Fin')
    prima = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Prima total')
    incentivo_pct = models.DecimalField(max_digits=5, decimal_places=2, db_default=0, db_comment='Porcentaje de la prima subsidiado (Incentivo al Seguro Agropecuario)')
    valor_subsidiado = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Valor subsidiado')
    suma_asegurada = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Suma asegurada')
    deducible = models.CharField(max_length=120, null=True, blank=True, db_comment='Deducible')
    estado = models.CharField(max_length=10, choices=[('en_tramite', 'en_tramite'), ('vigente', 'vigente'), ('vencida', 'vencida'), ('cancelada', 'cancelada')], db_default='en_tramite', db_comment='Estado')
    avisar_dias = models.SmallIntegerField(db_default=30, db_comment='Aviso antes de vencer')
    documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='documento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Póliza firmada')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguros", tabla "poliza" (las comillas separan esquema y tabla)
        db_table = 'seguros"."poliza'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Póliza (cultivo, animales, equipos, responsabilidad civil del dron, paramétrico) con vigencia, prima, suma asegurada e incentivo de Finagro.'


# ==============================================================================================================
# Tabla seguros.bien_asegurado  ·  por finca (seguridad por filas)  ·  API: /api/v1/seguros/bienes-asegurados/
# ==============================================================================================================
class BienAsegurado(models.Model):
    """Lo que cubre la póliza: un activo, una siembra, un lote de animales o una zona."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    poliza = models.ForeignKey('seguros.Poliza', models.DO_NOTHING, db_column='poliza_id', related_name='+', db_constraint=False, db_comment='Póliza')
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Equipo')
    siembra = models.ForeignKey('produccion.Siembra', models.DO_NOTHING, db_column='siembra_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Siembra')
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Lote')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona')
    descripcion = models.CharField(max_length=200, db_comment='Descripción')
    valor_asegurado = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguros", tabla "bien_asegurado" (las comillas separan esquema y tabla)
        db_table = 'seguros"."bien_asegurado'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lo que cubre la póliza: un activo, una siembra, un lote de animales o una zona.'


# ==============================================================================================================
# Tabla seguros.indice_poliza  ·  por finca (seguridad por filas)  ·  API: /api/v1/seguros/indices-poliza/
# ==============================================================================================================
class IndicePoliza(models.Model):
    """Regla del índice de un seguro paramétrico; la decide la aseguradora con su fuente, no los sensores de la finca."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    poliza = models.ForeignKey('seguros.Poliza', models.DO_NOTHING, db_column='poliza_id', related_name='+', db_constraint=False, db_comment='Póliza')
    variable = models.CharField(max_length=13, choices=[('lluvia_mm', 'lluvia_mm'), ('temperatura_c', 'temperatura_c'), ('dias_secos', 'dias_secos'), ('viento_kmh', 'viento_kmh'), ('otro', 'otro')], db_comment='Variable')
    fuente_oficial = models.CharField(max_length=150, db_comment='Fuente que usa la aseguradora, ej. satélite CHIRPS')
    comparador = models.CharField(max_length=5, choices=[('mayor', 'mayor'), ('menor', 'menor')], db_comment='Se cumple si el valor es mayor o menor que el umbral')
    umbral = models.DecimalField(max_digits=10, decimal_places=2, db_comment='Umbral')
    ventana_dias = models.SmallIntegerField(db_comment='Días acumulados')
    sensor = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sensor propio con que se compara')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguros", tabla "indice_poliza" (las comillas separan esquema y tabla)
        db_table = 'seguros"."indice_poliza'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Regla del índice de un seguro paramétrico; la decide la aseguradora con su fuente, no los sensores de la finca.'


# ==============================================================================================================
# Tabla seguros.aviso_siniestro  ·  por finca (seguridad por filas)  ·  API: /api/v1/seguros/avisos-siniestro/
# ==============================================================================================================
class AvisoSiniestro(models.Model):
    """Aviso de posible siniestro con la serie de datos como evidencia. No hay reclamación automática: una persona lo revisa y lo envía."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    poliza = models.ForeignKey('seguros.Poliza', models.DO_NOTHING, db_column='poliza_id', related_name='+', db_constraint=False, db_comment='Póliza')
    indice = models.ForeignKey('seguros.IndicePoliza', models.DO_NOTHING, db_column='indice_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Índice, si es paramétrico')
    detectado_en = models.DateTimeField(db_comment='Cuándo')
    descripcion = models.TextField(db_comment='Qué pasó')
    serie_datos = models.JSONField(null=True, blank=True, db_comment='Datos usados como evidencia')
    estado = models.CharField(max_length=10, choices=[('borrador', 'borrador'), ('revisado', 'revisado'), ('enviado', 'enviado'), ('pagado', 'pagado'), ('rechazado', 'rechazado'), ('descartado', 'descartado')], db_default='borrador', db_comment='Estado')
    revisado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='revisado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo revisó')
    enviado_en = models.DateTimeField(null=True, blank=True, db_comment='Envío al corredor')
    valor_reclamado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Reclamado')
    valor_pagado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Pagado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguros", tabla "aviso_siniestro" (las comillas separan esquema y tabla)
        db_table = 'seguros"."aviso_siniestro'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Aviso de posible siniestro con la serie de datos como evidencia. No hay reclamación automática: una persona lo revisa y lo envía.'
