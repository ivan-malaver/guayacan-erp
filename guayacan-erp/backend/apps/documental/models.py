"""Modelos del esquema documental: Documentos con versiones, aprobación, vencimiento y vínculos; los agentes solo leen la versión aprobada y vigente.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «documental». Django usa estas clases para leer y escribir
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
# Tabla documental.documento  ·  por finca (seguridad por filas)  ·  API: /api/v1/documental/documentos/
# ==============================================================================================================
class Documento(models.Model):
    """Papel que la finca no puede perder: permisos, registros ICA, RUT, contratos, protocolos, manuales, evidencias. Con datos personales sigue la Ley 1581."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código, ej. PRT-BIO-01')
    titulo = models.CharField(max_length=200, db_comment='Título')
    tipo = models.CharField(max_length=21, choices=[('permiso', 'permiso'), ('registro', 'registro'), ('contrato', 'contrato'), ('protocolo', 'protocolo'), ('manual', 'manual'), ('ficha_tecnica', 'ficha_tecnica'), ('evidencia', 'evidencia'), ('acta', 'acta'), ('resultado_laboratorio', 'resultado_laboratorio'), ('poliza', 'poliza'), ('certificado', 'certificado'), ('plan', 'plan'), ('otro', 'otro')], db_comment='Tipo')
    entidad_emisora = models.CharField(max_length=120, null=True, blank=True, db_comment='Quién lo expide, ej. ICA, CAR, DIAN')
    numero = models.CharField(max_length=60, null=True, blank=True, db_comment='Número oficial')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    nivel_acceso = models.CharField(max_length=11, choices=[('finca', 'finca'), ('rol', 'rol'), ('restringido', 'restringido')], db_default='finca', db_comment='Quién lo ve')
    rol = models.ForeignKey('nucleo.Rol', models.DO_NOTHING, db_column='rol_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Rol que lo ve, si es por rol')
    contiene_datos_personales = models.BooleanField(db_default=False, db_comment='Tiene datos personales (Ley 1581)')
    finalidad = models.TextField(null=True, blank=True, db_comment='Para qué se guarda')
    conservar_hasta = models.DateField(null=True, blank=True, db_comment='Hasta cuándo se conserva')
    uso_agentes = models.BooleanField(db_default=False, db_comment='Lo pueden leer los agentes (solo la versión aprobada y vigente)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "documental", tabla "documento" (las comillas separan esquema y tabla)
        db_table = 'documental"."documento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Papel que la finca no puede perder: permisos, registros ICA, RUT, contratos, protocolos, manuales, evidencias. Con datos personales sigue la Ley 1581.'


# ==============================================================================================================
# Tabla documental.version_documento  ·  por finca (seguridad por filas)  ·  API: /api/v1/documental/documentos/{id}/versiones/
# ==============================================================================================================
class VersionDocumento(models.Model):
    """Versión de un documento con su archivo, huella, aprobación y vigencia; solo una aprobada vigente a la vez."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='documento_id', related_name='+', db_constraint=False, db_comment='Documento')
    version = models.SmallIntegerField(db_comment='Número de versión')
    archivo_url = models.CharField(max_length=300, db_comment='Archivo en el almacén de objetos')
    hash_sha256 = models.CharField(max_length=64, db_comment='Huella del archivo')
    estado = models.CharField(max_length=11, choices=[('borrador', 'borrador'), ('en_revision', 'en_revision'), ('aprobada', 'aprobada'), ('obsoleta', 'obsoleta')], db_default='borrador', db_comment='Estado')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    aprobada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    vigente_desde = models.DateField(null=True, blank=True, db_comment='Desde')
    vence_en = models.DateField(null=True, blank=True, db_comment='Vencimiento (permisos, registros, pólizas)')
    avisar_dias = models.SmallIntegerField(db_default=30, db_comment='Días de aviso antes de vencer')
    cambios = models.TextField(null=True, blank=True, db_comment='Qué cambió')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "documental", tabla "version_documento" (las comillas separan esquema y tabla)
        db_table = 'documental"."version_documento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Versión de un documento con su archivo, huella, aprobación y vigencia; solo una aprobada vigente a la vez.'


# ==============================================================================================================
# Tabla documental.vinculo_documento  ·  por finca (seguridad por filas)  ·  API: /api/v1/documental/vinculos-documento/
# ==============================================================================================================
class VinculoDocumento(models.Model):
    """Une un documento con cualquier registro (un lote, una póliza, un activo, una no conformidad)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='documento_id', related_name='+', db_constraint=False, db_comment='Documento')
    registro_tabla = models.CharField(max_length=60, db_comment='Tabla')
    registro_id = models.BigIntegerField(db_comment='Id')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "documental", tabla "vinculo_documento" (las comillas separan esquema y tabla)
        db_table = 'documental"."vinculo_documento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Une un documento con cualquier registro (un lote, una póliza, un activo, una no conformidad).'
