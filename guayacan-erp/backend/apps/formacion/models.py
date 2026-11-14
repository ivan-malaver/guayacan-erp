"""Modelos del esquema formacion: Cursos, lecciones, evaluaciones, sesiones presenciales, certificados y habilitaciones que permiten asignar tareas.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «formacion». Django usa estas clases para leer y escribir
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
# Tabla formacion.competencia  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/competencias/
# ==============================================================================================================
class Competencia(models.Model):
    """Habilidad que habilita tareas (registrar vacunas, aplicar insumos, liberar lotes, operar motosierra), con su vigencia."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=40, db_comment='Código, ej. aplicar_vacunas')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    vigencia_meses = models.SmallIntegerField(null=True, blank=True, db_comment='Meses que dura el certificado; vacío = no vence')
    descripcion = models.TextField(null=True, blank=True, db_comment='Qué permite hacer')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "competencia" (las comillas separan esquema y tabla)
        db_table = 'formacion"."competencia'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Habilidad que habilita tareas (registrar vacunas, aplicar insumos, liberar lotes, operar motosierra), con su vigencia.'


# ==============================================================================================================
# Tabla formacion.curso  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/cursos/
# ==============================================================================================================
class Curso(models.Model):
    """Curso virtual, presencial o mixto para operarios o estudiantes; los externos (SENA, FAO, Moodle) se enlazan."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código')
    nombre = models.CharField(max_length=150, db_comment='Nombre')
    descripcion = models.TextField(null=True, blank=True, db_comment='Contenido')
    publico = models.CharField(max_length=11, choices=[('operarios', 'operarios'), ('estudiantes', 'estudiantes'), ('ambos', 'ambos')], db_default='ambos', db_comment='A quién va')
    modalidad = models.CharField(max_length=10, choices=[('virtual', 'virtual'), ('presencial', 'presencial'), ('mixto', 'mixto')], db_comment='Modalidad')
    competencia = models.ForeignKey('formacion.Competencia', models.DO_NOTHING, db_column='competencia_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Habilitación que otorga al aprobar')
    nota_minima = models.DecimalField(max_digits=4, decimal_places=2, db_default=3.5, db_comment='Nota mínima para aprobar (escala 0 a 5)')
    duracion_horas = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, db_comment='Horas')
    origen = models.CharField(max_length=6, choices=[('propio', 'propio'), ('sena', 'sena'), ('fao', 'fao'), ('moodle', 'moodle'), ('otro', 'otro')], db_default='propio', db_comment='De dónde viene')
    url_externa = models.CharField(max_length=300, null=True, blank=True, db_comment='Enlace, si es externo')
    ruta_cargo = models.CharField(max_length=60, null=True, blank=True, db_comment='Ruta de aprendizaje, ej. operario_galpon, vendedor')
    activo = models.BooleanField(db_default=True, db_comment='Publicado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "curso" (las comillas separan esquema y tabla)
        db_table = 'formacion"."curso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Curso virtual, presencial o mixto para operarios o estudiantes; los externos (SENA, FAO, Moodle) se enlazan.'


# ==============================================================================================================
# Tabla formacion.leccion  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/lecciones/
# ==============================================================================================================
class Leccion(models.Model):
    """Lección de un curso (texto, video corto, práctica guiada); se descarga para verla sin señal."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    curso = models.ForeignKey('formacion.Curso', models.DO_NOTHING, db_column='curso_id', related_name='+', db_constraint=False, db_comment='Curso')
    orden = models.SmallIntegerField(db_comment='Orden')
    titulo = models.CharField(max_length=150, db_comment='Título')
    tipo = models.CharField(max_length=17, choices=[('texto', 'texto'), ('video', 'video'), ('practica', 'practica'), ('tutorial_pantalla', 'tutorial_pantalla')], db_comment='Tipo')
    contenido_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Archivo')
    pantalla = models.CharField(max_length=80, null=True, blank=True, db_comment='Pantalla de la app que explica (tutoriales dentro de la app)')
    documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='documento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Protocolo o manual de base')
    descargable = models.BooleanField(db_default=True, db_comment='Se puede ver sin conexión')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "leccion" (las comillas separan esquema y tabla)
        db_table = 'formacion"."leccion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lección de un curso (texto, video corto, práctica guiada); se descarga para verla sin señal.'


# ==============================================================================================================
# Tabla formacion.evaluacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/evaluaciones/
# ==============================================================================================================
class Evaluacion(models.Model):
    """Examen de un curso."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    curso = models.ForeignKey('formacion.Curso', models.DO_NOTHING, db_column='curso_id', related_name='+', db_constraint=False, db_comment='Curso')
    titulo = models.CharField(max_length=150, db_comment='Título')
    intentos_max = models.SmallIntegerField(db_default=3, db_comment='Intentos')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "evaluacion" (las comillas separan esquema y tabla)
        db_table = 'formacion"."evaluacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Examen de un curso.'


# ==============================================================================================================
# Tabla formacion.pregunta  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/preguntas/
# ==============================================================================================================
class Pregunta(models.Model):
    """Pregunta de una evaluación."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    evaluacion = models.ForeignKey('formacion.Evaluacion', models.DO_NOTHING, db_column='evaluacion_id', related_name='+', db_constraint=False, db_comment='Evaluación')
    orden = models.SmallIntegerField(db_comment='Orden')
    enunciado = models.TextField(db_comment='Pregunta')
    tipo = models.CharField(max_length=15, choices=[('unica', 'unica'), ('multiple', 'multiple'), ('verdadero_falso', 'verdadero_falso'), ('practica', 'practica')], db_comment='Tipo')
    opciones = models.JSONField(null=True, blank=True, db_comment='Opciones')
    respuesta_correcta = models.JSONField(null=True, blank=True, db_comment='Respuesta')
    puntos = models.DecimalField(max_digits=4, decimal_places=1, db_default=1, db_comment='Puntos')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "pregunta" (las comillas separan esquema y tabla)
        db_table = 'formacion"."pregunta'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Pregunta de una evaluación.'


# ==============================================================================================================
# Tabla formacion.inscripcion  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/inscripciones/
# ==============================================================================================================
class Inscripcion(models.Model):
    """Persona (operario o estudiante) inscrita en un curso, con su nota."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    curso = models.ForeignKey('formacion.Curso', models.DO_NOTHING, db_column='curso_id', related_name='+', db_constraint=False, db_comment='Curso')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Persona')
    inscrito_en = models.DateField(db_default=sql('current_date'), db_comment='Inscripción')
    estado = models.CharField(max_length=9, choices=[('inscrito', 'inscrito'), ('en_curso', 'en_curso'), ('aprobado', 'aprobado'), ('reprobado', 'reprobado'), ('retirado', 'retirado')], db_default='inscrito', db_comment='Estado')
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, db_comment='Nota final')
    aprobado_en = models.DateField(null=True, blank=True, db_comment='Fecha de aprobación')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "inscripcion" (las comillas separan esquema y tabla)
        db_table = 'formacion"."inscripcion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Persona (operario o estudiante) inscrita en un curso, con su nota.'


# ==============================================================================================================
# Tabla formacion.progreso  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/progresos/
# ==============================================================================================================
class Progreso(models.Model):
    """Lecciones vistas por cada inscrito."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    inscripcion = models.ForeignKey('formacion.Inscripcion', models.DO_NOTHING, db_column='inscripcion_id', related_name='+', db_constraint=False, db_comment='Inscripción')
    leccion = models.ForeignKey('formacion.Leccion', models.DO_NOTHING, db_column='leccion_id', related_name='+', db_constraint=False, db_comment='Lección')
    completada_en = models.DateTimeField(db_comment='Cuándo')
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
        # Nombre real en PostgreSQL: esquema "formacion", tabla "progreso" (las comillas separan esquema y tabla)
        db_table = 'formacion"."progreso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lecciones vistas por cada inscrito.'


# ==============================================================================================================
# Tabla formacion.sesion_presencial  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/sesiones-presencial/
# ==============================================================================================================
class SesionPresencial(models.Model):
    """Sesión dictada por el veterinario, el agrónomo o el encargado; su asistencia cuenta igual que un curso virtual."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    curso = models.ForeignKey('formacion.Curso', models.DO_NOTHING, db_column='curso_id', related_name='+', db_constraint=False, db_comment='Curso')
    instructor = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='instructor_id', related_name='+', db_constraint=False, db_comment='Quién la dicta')
    fecha = models.DateField(db_comment='Día')
    lugar = models.CharField(max_length=120, null=True, blank=True, db_comment='Lugar')
    duracion_horas = models.DecimalField(max_digits=4, decimal_places=1, db_comment='Horas')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "sesion_presencial" (las comillas separan esquema y tabla)
        db_table = 'formacion"."sesion_presencial'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Sesión dictada por el veterinario, el agrónomo o el encargado; su asistencia cuenta igual que un curso virtual.'


# ==============================================================================================================
# Tabla formacion.asistencia  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/asistencias/
# ==============================================================================================================
class Asistencia(models.Model):
    """Asistencia y nota de cada persona en una sesión presencial."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    sesion = models.ForeignKey('formacion.SesionPresencial', models.DO_NOTHING, db_column='sesion_id', related_name='+', db_constraint=False, db_comment='Sesión')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Persona')
    asistio = models.BooleanField(db_comment='Asistió')
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, db_comment='Nota práctica')
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
        # Nombre real en PostgreSQL: esquema "formacion", tabla "asistencia" (las comillas separan esquema y tabla)
        db_table = 'formacion"."asistencia'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Asistencia y nota de cada persona en una sesión presencial.'


# ==============================================================================================================
# Tabla formacion.certificado  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/certificados/
# ==============================================================================================================
class Certificado(models.Model):
    """Certificado interno con fecha, nota y vencimiento; al emitirse crea la habilitación."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Persona')
    competencia = models.ForeignKey('formacion.Competencia', models.DO_NOTHING, db_column='competencia_id', related_name='+', db_constraint=False, db_comment='Competencia')
    inscripcion = models.ForeignKey('formacion.Inscripcion', models.DO_NOTHING, db_column='inscripcion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Curso virtual aprobado')
    sesion = models.ForeignKey('formacion.SesionPresencial', models.DO_NOTHING, db_column='sesion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sesión presencial')
    emitido_en = models.DateField(db_comment='Emisión')
    vence_en = models.DateField(null=True, blank=True, db_comment='Vencimiento')
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, db_comment='Nota')
    codigo_verificacion = models.CharField(max_length=40, db_comment='Código para verificarlo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "certificado" (las comillas separan esquema y tabla)
        db_table = 'formacion"."certificado'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Certificado interno con fecha, nota y vencimiento; al emitirse crea la habilitación.'


# ==============================================================================================================
# Tabla formacion.habilitacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/habilitaciones/
# ==============================================================================================================
class Habilitacion(models.Model):
    """Permiso para hacer una tarea, nacido de un certificado. Al vencer el certificado se retira sola."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Persona')
    competencia = models.ForeignKey('formacion.Competencia', models.DO_NOTHING, db_column='competencia_id', related_name='+', db_constraint=False, db_comment='Competencia')
    certificado = models.ForeignKey('formacion.Certificado', models.DO_NOTHING, db_column='certificado_id', related_name='+', db_constraint=False, db_comment='Certificado que la sustenta')
    desde = models.DateField(db_comment='Desde')
    hasta = models.DateField(null=True, blank=True, db_comment='Hasta')
    activa = models.BooleanField(db_default=True, db_comment='Vigente')
    retirada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se retiró')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "habilitacion" (las comillas separan esquema y tabla)
        db_table = 'formacion"."habilitacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Permiso para hacer una tarea, nacido de un certificado. Al vencer el certificado se retira sola.'


# ==============================================================================================================
# Tabla formacion.necesidad_formacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/necesidades-formacion/
# ==============================================================================================================
class NecesidadFormacion(models.Model):
    """Necesidad de formación detectada (por cargo, por una no conformidad, por un cambio o pedida por la persona)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    origen = models.CharField(max_length=20, choices=[('cargo', 'cargo'), ('no_conformidad', 'no_conformidad'), ('cambio', 'cambio'), ('solicitud', 'solicitud'), ('evaluacion_desempeno', 'evaluacion_desempeno'), ('norma', 'norma')], db_comment='De dónde sale')
    descripcion = models.TextField(db_comment='Qué se necesita aprender')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona, si es individual')
    competencia = models.ForeignKey('formacion.Competencia', models.DO_NOTHING, db_column='competencia_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Competencia')
    curso = models.ForeignKey('formacion.Curso', models.DO_NOTHING, db_column='curso_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Curso que la atiende')
    estado = models.CharField(max_length=11, choices=[('abierta', 'abierta'), ('planificada', 'planificada'), ('atendida', 'atendida'), ('descartada', 'descartada')], db_default='abierta', db_comment='Estado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "necesidad_formacion" (las comillas separan esquema y tabla)
        db_table = 'formacion"."necesidad_formacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Necesidad de formación detectada (por cargo, por una no conformidad, por un cambio o pedida por la persona).'


# ==============================================================================================================
# Tabla formacion.encuesta  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/encuestas/
# ==============================================================================================================
class Encuesta(models.Model):
    """Encuesta de satisfacción y de resultados de un curso o sesión (seguimiento y medición de la formación)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    curso = models.ForeignKey('formacion.Curso', models.DO_NOTHING, db_column='curso_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Curso')
    sesion = models.ForeignKey('formacion.SesionPresencial', models.DO_NOTHING, db_column='sesion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sesión')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién responde (vacío = anónima)')
    satisfaccion = models.SmallIntegerField(db_comment='Satisfacción general 1 a 5')
    utilidad = models.SmallIntegerField(db_comment='Utilidad para el trabajo 1 a 5')
    instructor = models.SmallIntegerField(null=True, blank=True, db_comment='Desempeño del instructor 1 a 5')
    comentario = models.TextField(null=True, blank=True, db_comment='Comentario')
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
        # Nombre real en PostgreSQL: esquema "formacion", tabla "encuesta" (las comillas separan esquema y tabla)
        db_table = 'formacion"."encuesta'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Encuesta de satisfacción y de resultados de un curso o sesión (seguimiento y medición de la formación).'


# ==============================================================================================================
# Tabla formacion.queja_apelacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/formacion/quejas-apelacion/
# ==============================================================================================================
class QuejaApelacion(models.Model):
    """Queja sobre la formación o apelación de una nota o certificado; se responde en plazo y la resuelve alguien distinto del instructor."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=9, choices=[('queja', 'queja'), ('apelacion', 'apelacion')], db_comment='Tipo')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Quién la presenta')
    curso = models.ForeignKey('formacion.Curso', models.DO_NOTHING, db_column='curso_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Curso')
    certificado = models.ForeignKey('formacion.Certificado', models.DO_NOTHING, db_column='certificado_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Certificado apelado')
    descripcion = models.TextField(db_comment='Qué pasó')
    presentada_en = models.DateField(db_default=sql('current_date'), db_comment='Fecha')
    responder_antes = models.DateField(db_comment='Plazo de respuesta')
    estado = models.CharField(max_length=10, choices=[('recibida', 'recibida'), ('en_estudio', 'en_estudio'), ('resuelta', 'resuelta'), ('rechazada', 'rechazada')], db_default='recibida', db_comment='Estado')
    respuesta = models.TextField(null=True, blank=True, db_comment='Respuesta')
    resuelta_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='resuelta_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién resolvió')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "formacion", tabla "queja_apelacion" (las comillas separan esquema y tabla)
        db_table = 'formacion"."queja_apelacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Queja sobre la formación o apelación de una nota o certificado; se responde en plazo y la resuelve alguien distinto del instructor.'
