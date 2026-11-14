"""Modelos del esquema cumplimiento: Normas (granja avícola biosegura, BPA, GLOBALG.A.P.), requisitos, expediente, evidencias, auditorías y acciones correctivas.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «cumplimiento». Django usa estas clases para leer y escribir
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
# Tabla cumplimiento.norma  ·  catálogo compartido entre fincas  ·  API: /api/v1/cumplimiento/normas/
# ==============================================================================================================
class Norma(models.Model):
    """Norma o certificación (granja avícola biosegura ICA 3651/2014, BPA ICA 30021/2017, GLOBALG.A.P. IFA v6). Catálogo compartido."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, unique=True, db_comment='Código, ej. ICA_GAB, ICA_BPA, GLOBALGAP_IFA6')
    nombre = models.CharField(max_length=200, db_comment='Nombre')
    entidad = models.CharField(max_length=80, db_comment='Entidad')
    referencia = models.CharField(max_length=120, db_comment='Norma, ej. Resolución ICA 3651 de 2014')
    obligatoria = models.BooleanField(db_comment='Obligatoria por ley')
    condicion_obligatoria = models.TextField(null=True, blank=True, db_comment='Cuándo aplica, ej. postura o levante desde 200 aves')
    funcion_codigo = models.CharField(max_length=40, null=True, blank=True, db_comment='Función por finca que la enciende; vacío = siempre activa')
    vigencia_certificado_meses = models.SmallIntegerField(null=True, blank=True, db_comment='Duración del certificado')
    url_fuente = models.CharField(max_length=300, null=True, blank=True, db_comment='Texto oficial')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "norma" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."norma'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Norma o certificación (granja avícola biosegura ICA 3651/2014, BPA ICA 30021/2017, GLOBALG.A.P. IFA v6). Catálogo compartido.'


# ==============================================================================================================
# Tabla cumplimiento.requisito  ·  catálogo compartido entre fincas  ·  API: /api/v1/cumplimiento/requisitos/
# ==============================================================================================================
class Requisito(models.Model):
    """Requisito de una norma con el tipo de evidencia y, si aplica, la regla que la revisa sola."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    norma = models.ForeignKey('cumplimiento.Norma', models.DO_NOTHING, db_column='norma_id', related_name='+', db_constraint=False, db_comment='Norma')
    codigo = models.CharField(max_length=30, db_comment='Código')
    descripcion = models.TextField(db_comment='Qué pide')
    tipo_evidencia = models.CharField(max_length=21, choices=[('documento', 'documento'), ('registro', 'registro'), ('certificado_formacion', 'certificado_formacion'), ('analisis', 'analisis'), ('inspeccion', 'inspeccion')], db_comment='Evidencia esperada')
    regla_evidencia = models.CharField(max_length=80, null=True, blank=True, db_comment='Revisión automática, ej. documento:protocolo, competencia:bioseguridad, registro:produccion.registro_bioseguridad')
    vigencia_dias = models.SmallIntegerField(null=True, blank=True, db_comment='Días que vale la evidencia')
    critico = models.BooleanField(db_default=False, db_comment='Sin él no se certifica')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "requisito" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."requisito'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Requisito de una norma con el tipo de evidencia y, si aplica, la regla que la revisa sola.'


# ==============================================================================================================
# Tabla cumplimiento.expediente  ·  por finca (seguridad por filas)  ·  API: /api/v1/cumplimiento/expedientes/
# ==============================================================================================================
class Expediente(models.Model):
    """Expediente de la finca ante una norma (incluye el registro sanitario de predio avícola, RSPA)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    norma = models.ForeignKey('cumplimiento.Norma', models.DO_NOTHING, db_column='norma_id', related_name='+', db_constraint=False, db_comment='Norma')
    estado = models.CharField(max_length=14, choices=[('en_preparacion', 'en_preparacion'), ('solicitado', 'solicitado'), ('certificado', 'certificado'), ('suspendido', 'suspendido'), ('vencido', 'vencido')], db_default='en_preparacion', db_comment='Estado')
    rspa_numero = models.CharField(max_length=40, null=True, blank=True, db_comment='Registro sanitario de predio avícola (RSPA) del ICA, si aplica')
    numero_certificado = models.CharField(max_length=60, null=True, blank=True, db_comment='Número del certificado')
    organismo = models.CharField(max_length=120, null=True, blank=True, db_comment='Entidad u organismo certificador')
    solicitado_en = models.DateField(null=True, blank=True, db_comment='Solicitud')
    certificado_en = models.DateField(null=True, blank=True, db_comment='Certificación')
    vence_en = models.DateField(null=True, blank=True, db_comment='Vencimiento')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "expediente" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."expediente'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Expediente de la finca ante una norma (incluye el registro sanitario de predio avícola, RSPA).'


# ==============================================================================================================
# Tabla cumplimiento.evaluacion_requisito  ·  por finca (seguridad por filas)  ·  API: /api/v1/cumplimiento/evaluaciones-requisito/
# ==============================================================================================================
class EvaluacionRequisito(models.Model):
    """Estado de cada requisito en el expediente. Con evidencia vencida pasa solo a no cumple."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    expediente = models.ForeignKey('cumplimiento.Expediente', models.DO_NOTHING, db_column='expediente_id', related_name='+', db_constraint=False, db_comment='Expediente')
    requisito = models.ForeignKey('cumplimiento.Requisito', models.DO_NOTHING, db_column='requisito_id', related_name='+', db_constraint=False, db_comment='Requisito')
    estado = models.CharField(max_length=10, choices=[('cumple', 'cumple'), ('no_cumple', 'no_cumple'), ('en_proceso', 'en_proceso'), ('no_aplica', 'no_aplica')], db_default='en_proceso', db_comment='Estado')
    origen = models.CharField(max_length=14, choices=[('automatica', 'automatica'), ('autoevaluacion', 'autoevaluacion'), ('auditoria', 'auditoria')], db_default='autoevaluacion', db_comment='Cómo se evaluó')
    evaluado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='evaluado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién')
    evaluado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    vence_en = models.DateField(null=True, blank=True, db_comment='Vencimiento de la evidencia que lo sostiene')
    observacion = models.TextField(null=True, blank=True, db_comment='Nota')
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
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "evaluacion_requisito" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."evaluacion_requisito'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Estado de cada requisito en el expediente. Con evidencia vencida pasa solo a no cumple.'


# ==============================================================================================================
# Tabla cumplimiento.evidencia_requisito  ·  por finca (seguridad por filas)  ·  API: /api/v1/cumplimiento/evidencias-requisito/
# ==============================================================================================================
class EvidenciaRequisito(models.Model):
    """Prueba de un requisito: un documento o un registro del sistema, con su vencimiento."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    evaluacion = models.ForeignKey('cumplimiento.EvaluacionRequisito', models.DO_NOTHING, db_column='evaluacion_id', related_name='+', db_constraint=False, db_comment='Evaluación')
    documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='documento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Documento')
    registro_tabla = models.CharField(max_length=60, null=True, blank=True, db_comment='Tabla del registro')
    registro_id = models.BigIntegerField(null=True, blank=True, db_comment='Id')
    descripcion = models.CharField(max_length=200, db_comment='Qué prueba')
    vence_en = models.DateField(null=True, blank=True, db_comment='Vence')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "evidencia_requisito" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."evidencia_requisito'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Prueba de un requisito: un documento o un registro del sistema, con su vencimiento.'


# ==============================================================================================================
# Tabla cumplimiento.auditoria_externa  ·  por finca (seguridad por filas)  ·  API: /api/v1/cumplimiento/auditorias-externas/
# ==============================================================================================================
class AuditoriaExterna(models.Model):
    """Auditoría interna o externa programada, con aviso previo y resultado."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    expediente = models.ForeignKey('cumplimiento.Expediente', models.DO_NOTHING, db_column='expediente_id', related_name='+', db_constraint=False, db_comment='Expediente')
    tipo = models.CharField(max_length=11, choices=[('interna', 'interna'), ('externa', 'externa'), ('seguimiento', 'seguimiento')], db_comment='Tipo')
    organismo = models.CharField(max_length=120, null=True, blank=True, db_comment='Quién audita')
    fecha_programada = models.DateField(db_comment='Fecha')
    fecha_realizada = models.DateField(null=True, blank=True, db_comment='Realizada')
    resultado = models.CharField(max_length=13, choices=[('pendiente', 'pendiente'), ('aprobada', 'aprobada'), ('con_hallazgos', 'con_hallazgos'), ('rechazada', 'rechazada')], db_default='pendiente', db_comment='Resultado')
    informe_documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='informe_documento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Informe')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "auditoria_externa" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."auditoria_externa'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Auditoría interna o externa programada, con aviso previo y resultado.'


# ==============================================================================================================
# Tabla cumplimiento.no_conformidad  ·  por finca (seguridad por filas)  ·  API: /api/v1/cumplimiento/no-conformidades/
# ==============================================================================================================
class NoConformidad(models.Model):
    """Hallazgo; no se cierra sin acciones verificadas y sin quien verifique."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    expediente = models.ForeignKey('cumplimiento.Expediente', models.DO_NOTHING, db_column='expediente_id', related_name='+', db_constraint=False, db_comment='Expediente')
    auditoria = models.ForeignKey('cumplimiento.AuditoriaExterna', models.DO_NOTHING, db_column='auditoria_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Auditoría que la encontró')
    requisito = models.ForeignKey('cumplimiento.Requisito', models.DO_NOTHING, db_column='requisito_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Requisito')
    descripcion = models.TextField(db_comment='Hallazgo')
    severidad = models.CharField(max_length=7, choices=[('menor', 'menor'), ('mayor', 'mayor'), ('critica', 'critica')], db_comment='Severidad')
    detectada_en = models.DateField(db_comment='Fecha')
    estado = models.CharField(max_length=14, choices=[('abierta', 'abierta'), ('en_tratamiento', 'en_tratamiento'), ('cerrada', 'cerrada')], db_default='abierta', db_comment='Estado')
    verificacion = models.TextField(null=True, blank=True, db_comment='Cómo se verificó el cierre')
    cerrada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='cerrada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la cerró')
    cerrada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "no_conformidad" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."no_conformidad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Hallazgo; no se cierra sin acciones verificadas y sin quien verifique.'


# ==============================================================================================================
# Tabla cumplimiento.accion_correctiva  ·  por finca (seguridad por filas)  ·  API: /api/v1/cumplimiento/acciones-correctivas/
# ==============================================================================================================
class AccionCorrectiva(models.Model):
    """Acción para corregir una no conformidad, con responsable, plazo y verificación; se asigna como tarea."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    no_conformidad = models.ForeignKey('cumplimiento.NoConformidad', models.DO_NOTHING, db_column='no_conformidad_id', related_name='+', db_constraint=False, db_comment='No conformidad')
    descripcion = models.TextField(db_comment='Qué hacer')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, db_comment='Responsable')
    plazo = models.DateField(db_comment='Plazo')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea')
    estado = models.CharField(max_length=10, choices=[('pendiente', 'pendiente'), ('hecha', 'hecha'), ('verificada', 'verificada'), ('ineficaz', 'ineficaz')], db_default='pendiente', db_comment='Estado')
    verificada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='verificada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién verificó')
    verificada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "cumplimiento", tabla "accion_correctiva" (las comillas separan esquema y tabla)
        db_table = 'cumplimiento"."accion_correctiva'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Acción para corregir una no conformidad, con responsable, plazo y verificación; se asigna como tarea.'
