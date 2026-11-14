"""Modelos del esquema personal: Tareas, plan de labores, cuadrillas, turnos, ausencias (sin diagnósticos), matriz de responsabilidades, equipos asignados, carné QR o NFC y jornada.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «personal». Django usa estas clases para leer y escribir
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
# Tabla personal.cuadrilla  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/cuadrillas/
# ==============================================================================================================
class Cuadrilla(models.Model):
    """Grupo de trabajadores que recibe tareas juntos (ej. cuadrilla de cosecha)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. CUA-COSECHA')
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    lider = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='lider_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Trabajador que coordina la cuadrilla')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "cuadrilla" (las comillas separan esquema y tabla)
        db_table = 'personal"."cuadrilla'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Grupo de trabajadores que recibe tareas juntos (ej. cuadrilla de cosecha).'


# ==============================================================================================================
# Tabla personal.cuadrilla_miembro  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/cuadrillas-miembro/
# ==============================================================================================================
class CuadrillaMiembro(models.Model):
    """Trabajadores de cada cuadrilla, con fechas."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    cuadrilla = models.ForeignKey('personal.Cuadrilla', models.DO_NOTHING, db_column='cuadrilla_id', related_name='+', db_constraint=False, db_comment='Cuadrilla')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    desde = models.DateField(db_comment='Desde')
    hasta = models.DateField(null=True, blank=True, db_comment='Hasta; vacío = sigue')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "cuadrilla_miembro" (las comillas separan esquema y tabla)
        db_table = 'personal"."cuadrilla_miembro'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Trabajadores de cada cuadrilla, con fechas.'


# ==============================================================================================================
# Tabla personal.turno  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/turnos/
# ==============================================================================================================
class Turno(models.Model):
    """Horario de trabajo programado de una persona en un día."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    fecha = models.DateField(db_comment='Día')
    hora_inicio = models.TimeField(db_comment='Hora de entrada')
    hora_fin = models.TimeField(db_comment='Hora de salida')
    tipo = models.CharField(max_length=8, choices=[('diurno', 'diurno'), ('nocturno', 'nocturno'), ('mixto', 'mixto'), ('descanso', 'descanso'), ('festivo', 'festivo')], db_default='diurno', db_comment='Tipo de turno (define recargos)')
    area = models.ForeignKey('personal.AreaResponsabilidad', models.DO_NOTHING, db_column='area_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Área en la que trabaja ese turno')
    cronograma = models.ForeignKey('personal.Cronograma', models.DO_NOTHING, db_column='cronograma_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cronograma del que salió')
    horas = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, db_comment='Horas del turno (las calcula la base; si la salida es menor que la entrada, cruza la medianoche)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "turno" (las comillas separan esquema y tabla)
        db_table = 'personal"."turno'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Horario de trabajo programado de una persona en un día.'


# ==============================================================================================================
# Tabla personal.ausencia  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/ausencias/
# ==============================================================================================================
class Ausencia(models.Model):
    """Vacaciones, permisos, incapacidades y licencias. Guarda solo el tipo y las fechas, nunca el diagnóstico médico."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    tipo = models.CharField(max_length=19, choices=[('vacaciones', 'vacaciones'), ('permiso', 'permiso'), ('incapacidad_general', 'incapacidad_general'), ('incapacidad_laboral', 'incapacidad_laboral'), ('licencia_maternidad', 'licencia_maternidad'), ('licencia_paternidad', 'licencia_paternidad'), ('luto', 'luto'), ('calamidad', 'calamidad'), ('suspension', 'suspension')], db_comment='Tipo')
    desde = models.DateField(db_comment='Primer día')
    hasta = models.DateField(db_comment='Último día')
    remunerada = models.BooleanField(db_default=True, db_comment='Si se paga')
    soporte_documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='soporte_documento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Soporte (sin diagnóstico)')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "ausencia" (las comillas separan esquema y tabla)
        db_table = 'personal"."ausencia'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Vacaciones, permisos, incapacidades y licencias. Guarda solo el tipo y las fechas, nunca el diagnóstico médico.'


# ==============================================================================================================
# Tabla personal.plantilla_tarea  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/plantillas-tarea/
# ==============================================================================================================
class PlantillaTarea(models.Model):
    """Labor que se repite (recoger huevos dos veces al día, revisar bebederos, deshierbe semanal) y genera las tareas del día."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código, ej. REC-HUEVO-AM')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    proceso = models.CharField(max_length=60, db_comment='Proceso al que pertenece (une con la matriz de responsabilidades), ej. postura')
    recurrencia = models.CharField(max_length=7, choices=[('diaria', 'diaria'), ('semanal', 'semanal'), ('mensual', 'mensual'), ('unica', 'unica')], db_comment='Cada cuánto se repite')
    dias_semana = ArrayField(models.SmallIntegerField(), null=True, blank=True, db_comment='Días (1 lunes … 7 domingo) para las semanales')
    hora_limite = models.TimeField(null=True, blank=True, db_comment='Hora máxima para terminarla')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona')
    duracion_estimada_min = models.SmallIntegerField(null=True, blank=True, db_comment='Minutos estimados (estándar para productividad)')
    competencia = models.ForeignKey('formacion.Competencia', models.DO_NOTHING, db_column='competencia_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Habilitación que exige; sin ella no se asigna')
    forma_pago = models.CharField(max_length=7, choices=[('ninguna', 'ninguna'), ('jornal', 'jornal'), ('destajo', 'destajo')], db_default='ninguna', db_comment='Si la tarea aprobada paga jornal o destajo (nunca afecta el salario fijo)')
    valor_unitario = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Valor del jornal o de cada unidad a destajo')
    unidad_destajo = models.CharField(max_length=20, null=True, blank=True, db_comment='Unidad que se paga a destajo, ej. kg, racimo, planta')
    registro_que_crea = models.CharField(max_length=14, choices=[('ninguno', 'ninguno'), ('postura', 'postura'), ('alimentacion', 'alimentacion'), ('labor_cultural', 'labor_cultural'), ('bioseguridad', 'bioseguridad'), ('riego', 'riego'), ('cosecha', 'cosecha')], db_default='ninguno', db_comment='Registro que nace de la tarea aprobada')
    pasos = models.JSONField(null=True, blank=True, db_comment='Lista de chequeo')
    area = models.ForeignKey('personal.AreaResponsabilidad', models.DO_NOTHING, db_column='area_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Área de responsabilidad')
    prioridad = models.CharField(max_length=7, choices=[('baja', 'baja'), ('media', 'media'), ('alta', 'alta'), ('critica', 'critica')], db_default='media', db_comment='Prioridad')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "plantilla_tarea" (las comillas separan esquema y tabla)
        db_table = 'personal"."plantilla_tarea'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Labor que se repite (recoger huevos dos veces al día, revisar bebederos, deshierbe semanal) y genera las tareas del día.'


# ==============================================================================================================
# Tabla personal.tarea  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/tareas/
# ==============================================================================================================
class Tarea(models.Model):
    """Trabajo concreto con responsable, lugar, plazo y evidencia. Solo se asigna a quien está disponible y habilitado; aprobada no se edita."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    plantilla_tarea = models.ForeignKey('personal.PlantillaTarea', models.DO_NOTHING, db_column='plantilla_tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Plantilla de la que salió')
    titulo = models.CharField(max_length=150, db_comment='Qué hay que hacer')
    proceso = models.CharField(max_length=60, null=True, blank=True, db_comment='Proceso')
    fecha = models.DateField(db_comment='Día')
    hora_limite = models.DateTimeField(null=True, blank=True, db_comment='Plazo')
    prioridad = models.CharField(max_length=7, choices=[('baja', 'baja'), ('media', 'media'), ('alta', 'alta'), ('critica', 'critica')], db_default='media', db_comment='Prioridad')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona')
    area = models.ForeignKey('personal.AreaResponsabilidad', models.DO_NOTHING, db_column='area_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Área de responsabilidad (su responsable puede aprobarla)')
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Lote de animales')
    siembra = models.ForeignKey('produccion.Siembra', models.DO_NOTHING, db_column='siembra_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Siembra')
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Equipo que se usa o se mantiene')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    cuadrilla = models.ForeignKey('personal.Cuadrilla', models.DO_NOTHING, db_column='cuadrilla_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cuadrilla responsable')
    origen = models.CharField(max_length=17, choices=[('plan', 'plan'), ('manual', 'manual'), ('agente', 'agente'), ('orden_trabajo', 'orden_trabajo'), ('accion_correctiva', 'accion_correctiva'), ('mision_robot', 'mision_robot'), ('proyecto', 'proyecto'), ('agenda', 'agenda')], db_default='manual', db_comment='De dónde salió')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente que la propuso (no asigna por su cuenta)')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('en_curso', 'en_curso'), ('terminada', 'terminada'), ('aprobada', 'aprobada'), ('devuelta', 'devuelta'), ('cancelada', 'cancelada')], db_default='pendiente', db_comment='Estado')
    iniciada_en = models.DateTimeField(null=True, blank=True, db_comment='Inicio (escaneo del carné)')
    terminada_en = models.DateTimeField(null=True, blank=True, db_comment='Fin')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Cantidad lograda (kg, aves, plantas) para destajo y productividad')
    unidad = models.CharField(max_length=20, null=True, blank=True, db_comment='Unidad de la cantidad')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó o devolvió')
    aprobado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    comentario_revision = models.TextField(null=True, blank=True, db_comment='Comentario al aprobar o devolver')
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
        # Nombre real en PostgreSQL: esquema "personal", tabla "tarea" (las comillas separan esquema y tabla)
        db_table = 'personal"."tarea'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Trabajo concreto con responsable, lugar, plazo y evidencia. Solo se asigna a quien está disponible y habilitado; aprobada no se edita.'


# ==============================================================================================================
# Tabla personal.paso_tarea  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/tareas/{id}/pasos/
# ==============================================================================================================
class PasoTarea(models.Model):
    """Paso de la lista de chequeo de una tarea."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, db_comment='Tarea')
    orden = models.SmallIntegerField(db_comment='Orden')
    descripcion = models.CharField(max_length=200, db_comment='Paso')
    hecho = models.BooleanField(db_default=False, db_comment='Marcado')
    hecho_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
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
        # Nombre real en PostgreSQL: esquema "personal", tabla "paso_tarea" (las comillas separan esquema y tabla)
        db_table = 'personal"."paso_tarea'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Paso de la lista de chequeo de una tarea.'


# ==============================================================================================================
# Tabla personal.evidencia_tarea  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/tareas/{id}/evidencias/
# ==============================================================================================================
class EvidenciaTarea(models.Model):
    """Prueba de una tarea: foto, lectura del carné o del lote, nota de voz o el registro que creó."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, db_comment='Tarea')
    tipo = models.CharField(max_length=11, choices=[('foto', 'foto'), ('lectura_qr', 'lectura_qr'), ('lectura_nfc', 'lectura_nfc'), ('nota_voz', 'nota_voz'), ('documento', 'documento'), ('registro', 'registro')], db_comment='Tipo')
    archivo_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Archivo')
    registro_tabla = models.CharField(max_length=60, null=True, blank=True, db_comment='Tabla del registro creado, ej. produccion.registro_postura')
    registro_id = models.BigIntegerField(null=True, blank=True, db_comment='Id del registro')
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
        # Nombre real en PostgreSQL: esquema "personal", tabla "evidencia_tarea" (las comillas separan esquema y tabla)
        db_table = 'personal"."evidencia_tarea'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Prueba de una tarea: foto, lectura del carné o del lote, nota de voz o el registro que creó.'


# ==============================================================================================================
# Tabla personal.matriz_responsabilidad  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/matrices-responsabilidad/
# ==============================================================================================================
class MatrizResponsabilidad(models.Model):
    """Matriz RACI: para cada proceso, qué rol lo hace, lo aprueba, es consultado o informado."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proceso = models.CharField(max_length=60, db_comment='Proceso, ej. postura, venta, nomina')
    rol = models.ForeignKey('nucleo.Rol', models.DO_NOTHING, db_column='rol_id', related_name='+', db_constraint=False, db_comment='Rol')
    responsabilidad = models.CharField(max_length=11, choices=[('responsable', 'responsable'), ('aprueba', 'aprueba'), ('consultado', 'consultado'), ('informado', 'informado')], db_comment='R, A, C o I')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "matriz_responsabilidad" (las comillas separan esquema y tabla)
        db_table = 'personal"."matriz_responsabilidad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Matriz RACI: para cada proceso, qué rol lo hace, lo aprueba, es consultado o informado.'


# ==============================================================================================================
# Tabla personal.asignacion_equipo  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/asignaciones-equipo/
# ==============================================================================================================
class AsignacionEquipo(models.Model):
    """Quién tiene cada herramienta o equipo, desde cuándo y en qué estado lo recibió y lo devolvió."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, db_comment='Equipo')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    entregado_en = models.DateTimeField(db_comment='Entrega')
    estado_entrega = models.CharField(max_length=7, choices=[('bueno', 'bueno'), ('regular', 'regular'), ('malo', 'malo')], db_comment='Estado al entregar')
    devuelto_en = models.DateTimeField(null=True, blank=True, db_comment='Devolución')
    estado_devolucion = models.CharField(max_length=7, choices=[('bueno', 'bueno'), ('regular', 'regular'), ('malo', 'malo'), ('perdido', 'perdido')], null=True, blank=True, db_comment='Estado al devolver')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "asignacion_equipo" (las comillas separan esquema y tabla)
        db_table = 'personal"."asignacion_equipo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Quién tiene cada herramienta o equipo, desde cuándo y en qué estado lo recibió y lo devolvió.'


# ==============================================================================================================
# Tabla personal.credencial_trabajo  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/credenciales-trabajo/
# ==============================================================================================================
class CredencialTrabajo(models.Model):
    """Carné del trabajador con QR o etiqueta NFC para registrar quién hizo qué, sin biometría."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    tipo = models.CharField(max_length=3, choices=[('qr', 'qr'), ('nfc', 'nfc')], db_comment='Tipo (nunca biométrico)')
    codigo_hash = models.CharField(max_length=64, db_comment='Huella SHA-256 del código impreso o grabado')
    emitida_en = models.DateField(db_comment='Emisión')
    revocada_en = models.DateTimeField(null=True, blank=True, db_comment='Revocación (pérdida o retiro)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "credencial_trabajo" (las comillas separan esquema y tabla)
        db_table = 'personal"."credencial_trabajo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Carné del trabajador con QR o etiqueta NFC para registrar quién hizo qué, sin biometría.'


# ==============================================================================================================
# Tabla personal.jornada  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/jornadas/
# ==============================================================================================================
class Jornada(models.Model):
    """Registro de jornada (entrada, salida, horas y labor) para jornaleros sin tarea asignada ese día."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    fecha = models.DateField(db_comment='Día')
    entrada = models.DateTimeField(db_comment='Entrada')
    salida = models.DateTimeField(null=True, blank=True, db_comment='Salida')
    horas = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, db_comment='Horas trabajadas')
    labor = models.CharField(max_length=150, null=True, blank=True, db_comment='Labor hecha')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona')
    metodo_registro = models.CharField(max_length=6, choices=[('qr', 'qr'), ('nfc', 'nfc'), ('manual', 'manual')], db_comment='Cómo se registró')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    aprobada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
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
        # Nombre real en PostgreSQL: esquema "personal", tabla "jornada" (las comillas separan esquema y tabla)
        db_table = 'personal"."jornada'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Registro de jornada (entrada, salida, horas y labor) para jornaleros sin tarea asignada ese día.'


# ==============================================================================================================
# Tabla personal.area_responsabilidad  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/areas-responsabilidad/
# ==============================================================================================================
class AreaResponsabilidad(models.Model):
    """Área de responsabilidad (galpón, cultivos, turismo y cabañas, bodega y despachos, mantenimiento, vigilancia): agrupa zonas, personas y tareas, con un responsable."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. AR-GALPON')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    descripcion = models.TextField(null=True, blank=True, db_comment='Qué cubre')
    zonas = ArrayField(models.BigIntegerField(), null=True, blank=True, db_comment='Zonas que abarca')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Centro de costo')
    opera_24_7 = models.BooleanField(db_default=False, db_comment='Necesita cobertura las 24 horas, todos los días (vigilancia, galpón)')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "area_responsabilidad" (las comillas separan esquema y tabla)
        db_table = 'personal"."area_responsabilidad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Área de responsabilidad (galpón, cultivos, turismo y cabañas, bodega y despachos, mantenimiento, vigilancia): agrupa zonas, personas y tareas, con un responsable.'


# ==============================================================================================================
# Tabla personal.miembro_area  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/miembros-area/
# ==============================================================================================================
class MiembroArea(models.Model):
    """Personas de cada área, con quién es el responsable (puede aprobar las tareas del área)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    area = models.ForeignKey('personal.AreaResponsabilidad', models.DO_NOTHING, db_column='area_id', related_name='+', db_constraint=False, db_comment='Área')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    es_responsable = models.BooleanField(db_default=False, db_comment='Responsable del área')
    desde = models.DateField(db_comment='Desde')
    hasta = models.DateField(null=True, blank=True, db_comment='Hasta')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "miembro_area" (las comillas separan esquema y tabla)
        db_table = 'personal"."miembro_area'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Personas de cada área, con quién es el responsable (puede aprobar las tareas del área).'


# ==============================================================================================================
# Tabla personal.patron_turno  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/patrones-turno/
# ==============================================================================================================
class PatronTurno(models.Model):
    """Patrón de turnos reutilizable: semanal (se eligen días y horas), cíclico (ej. 2 días, 2 noches, 2 de descanso para 24/7) o flexible (se arma a mano)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. SEM-LV-6-14, CIC-2D2N2L')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    tipo = models.CharField(max_length=8, choices=[('semanal', 'semanal'), ('ciclico', 'ciclico'), ('flexible', 'flexible')], db_comment='Semanal: día 1 = lunes … 7 = domingo; cíclico: día 1 … N del ciclo')
    ciclo_dias = models.SmallIntegerField(db_default=7, db_comment='Días del ciclo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "patron_turno" (las comillas separan esquema y tabla)
        db_table = 'personal"."patron_turno'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Patrón de turnos reutilizable: semanal (se eligen días y horas), cíclico (ej. 2 días, 2 noches, 2 de descanso para 24/7) o flexible (se arma a mano).'


# ==============================================================================================================
# Tabla personal.patron_turno_detalle  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/patrones-turno/{id}/dias/
# ==============================================================================================================
class PatronTurnoDetalle(models.Model):
    """Día del patrón con su horario (puede cruzar la medianoche) o descanso."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    patron = models.ForeignKey('personal.PatronTurno', models.DO_NOTHING, db_column='patron_id', related_name='+', db_constraint=False, db_comment='Patrón')
    dia_ciclo = models.SmallIntegerField(db_comment='Día del ciclo (semanal: 1 lunes … 7 domingo)')
    hora_inicio = models.TimeField(null=True, blank=True, db_comment='Entrada (vacío = descanso)')
    hora_fin = models.TimeField(null=True, blank=True, db_comment='Salida; si es menor o igual a la entrada, termina al día siguiente')
    tipo = models.CharField(max_length=8, choices=[('diurno', 'diurno'), ('nocturno', 'nocturno'), ('mixto', 'mixto'), ('descanso', 'descanso')], db_comment='Tipo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "patron_turno_detalle" (las comillas separan esquema y tabla)
        db_table = 'personal"."patron_turno_detalle'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Día del patrón con su horario (puede cruzar la medianoche) o descanso.'


# ==============================================================================================================
# Tabla personal.cronograma  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/cronogramas/
# ==============================================================================================================
class Cronograma(models.Model):
    """Cronograma de trabajo de un área por un periodo: se genera desde patrones, se ajusta a mano y se publica cuando cumple jornada máxima, descanso semanal y cobertura."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=150, db_comment='Nombre, ej. Galpón · noviembre 2026')
    area = models.ForeignKey('personal.AreaResponsabilidad', models.DO_NOTHING, db_column='area_id', related_name='+', db_constraint=False, db_comment='Área')
    desde = models.DateField(db_comment='Primer día')
    hasta = models.DateField(db_comment='Último día')
    estado = models.CharField(max_length=9, choices=[('borrador', 'borrador'), ('publicado', 'publicado'), ('cerrado', 'cerrado')], db_default='borrador', db_comment='Estado')
    permitir_huecos = models.BooleanField(db_default=False, db_comment='Publicar aunque falte cobertura (queda la advertencia)')
    publicado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='publicado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo publicó')
    publicado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "cronograma" (las comillas separan esquema y tabla)
        db_table = 'personal"."cronograma'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cronograma de trabajo de un área por un periodo: se genera desde patrones, se ajusta a mano y se publica cuando cumple jornada máxima, descanso semanal y cobertura.'


# ==============================================================================================================
# Tabla personal.asignacion_patron  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/asignaciones-patron/
# ==============================================================================================================
class AsignacionPatron(models.Model):
    """Qué patrón sigue cada persona dentro del cronograma (con desfase para rotar entre varias personas)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    cronograma = models.ForeignKey('personal.Cronograma', models.DO_NOTHING, db_column='cronograma_id', related_name='+', db_constraint=False, db_comment='Cronograma')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    patron = models.ForeignKey('personal.PatronTurno', models.DO_NOTHING, db_column='patron_id', related_name='+', db_constraint=False, db_comment='Patrón')
    desfase_dias = models.SmallIntegerField(db_default=0, db_comment='En qué día del ciclo empieza (rotación)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "asignacion_patron" (las comillas separan esquema y tabla)
        db_table = 'personal"."asignacion_patron'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Qué patrón sigue cada persona dentro del cronograma (con desfase para rotar entre varias personas).'


# ==============================================================================================================
# Tabla personal.requerimiento_cobertura  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/requerimientos-cobertura/
# ==============================================================================================================
class RequerimientoCobertura(models.Model):
    """Cuántas personas necesita un área por franja horaria y día (ej. galpón: 1 persona las 24 horas; cabañas: 2 de 8 a 18 los fines de semana)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    area = models.ForeignKey('personal.AreaResponsabilidad', models.DO_NOTHING, db_column='area_id', related_name='+', db_constraint=False, db_comment='Área')
    dia_semana = models.SmallIntegerField(null=True, blank=True, db_comment='1 lunes … 7 domingo; vacío = todos los días')
    hora_inicio = models.TimeField(db_comment='Desde')
    hora_fin = models.TimeField(db_comment='Hasta (24:00 se escribe 23:59:59)')
    personas_min = models.SmallIntegerField(db_comment='Personas mínimas')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "requerimiento_cobertura" (las comillas separan esquema y tabla)
        db_table = 'personal"."requerimiento_cobertura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cuántas personas necesita un área por franja horaria y día (ej. galpón: 1 persona las 24 horas; cabañas: 2 de 8 a 18 los fines de semana).'


# ==============================================================================================================
# Tabla personal.disponibilidad  ·  por finca (seguridad por filas)  ·  API: /api/v1/personal/disponibilidades/
# ==============================================================================================================
class Disponibilidad(models.Model):
    """Días y horas en que cada persona puede o prefiere trabajar (para armar el cronograma flexible)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    dia_semana = models.SmallIntegerField(db_comment='1 lunes … 7 domingo')
    hora_inicio = models.TimeField(db_comment='Desde')
    hora_fin = models.TimeField(db_comment='Hasta')
    preferencia = models.CharField(max_length=13, choices=[('disponible', 'disponible'), ('preferido', 'preferido'), ('no_disponible', 'no_disponible')], db_comment='Preferencia')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "personal", tabla "disponibilidad" (las comillas separan esquema y tabla)
        db_table = 'personal"."disponibilidad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Días y horas en que cada persona puede o prefiere trabajar (para armar el cronograma flexible).'
