"""Modelos del esquema agenda: Recursos agendables (cabañas, salón, vehículos, equipos), calendario sin cruces, visitas programadas e ingresos y salidas de personas y vehículos.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «agenda». Django usa estas clases para leer y escribir
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
# Tabla agenda.recurso  ·  por finca (seguridad por filas)  ·  API: /api/v1/agenda/recursos/
# ==============================================================================================================
class Recurso(models.Model):
    """Lo que se agenda: cabañas, salón, zona de camping, vehículo, equipo, punto de cargue. Cada recurso tiene su calendario sin cruces."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    tipo = models.CharField(max_length=12, choices=[('cabana', 'cabana'), ('salon', 'salon'), ('zona_camping', 'zona_camping'), ('vehiculo', 'vehiculo'), ('equipo', 'equipo'), ('punto_cargue', 'punto_cargue'), ('sala', 'sala'), ('otro', 'otro')], db_comment='Tipo')
    alojamiento = models.ForeignKey('turismo.Alojamiento', models.DO_NOTHING, db_column='alojamiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cabaña de turismo que representa')
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Equipo o vehículo que representa')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ubicación')
    capacidad = models.SmallIntegerField(null=True, blank=True, db_comment='Capacidad')
    minutos_preparacion = models.SmallIntegerField(db_default=0, db_comment='Tiempo de alistamiento o limpieza que se bloquea después de cada uso')
    activo_ref = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "agenda", tabla "recurso" (las comillas separan esquema y tabla)
        db_table = 'agenda"."recurso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lo que se agenda: cabañas, salón, zona de camping, vehículo, equipo, punto de cargue. Cada recurso tiene su calendario sin cruces.'


# ==============================================================================================================
# Tabla agenda.cita  ·  por finca (seguridad por filas)  ·  API: /api/v1/agenda/citas/
# ==============================================================================================================
class Cita(models.Model):
    """Bloque del calendario de un recurso (reserva, limpieza, mantenimiento, uso familiar, entrega). La base impide cruces, contando el alistamiento."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    recurso = models.ForeignKey('agenda.Recurso', models.DO_NOTHING, db_column='recurso_id', related_name='+', db_constraint=False, db_comment='Recurso')
    titulo = models.CharField(max_length=150, db_comment='Título')
    tipo = models.CharField(max_length=17, choices=[('reserva_turistica', 'reserva_turistica'), ('limpieza', 'limpieza'), ('mantenimiento', 'mantenimiento'), ('uso_familiar', 'uso_familiar'), ('bloqueo', 'bloqueo'), ('entrega_proveedor', 'entrega_proveedor'), ('recogida_cliente', 'recogida_cliente'), ('capacitacion', 'capacitacion'), ('auditoria', 'auditoria'), ('reunion', 'reunion'), ('otro', 'otro')], db_comment='Tipo')
    inicio = models.DateTimeField(db_comment='Inicio')
    fin = models.DateTimeField(db_comment='Fin')
    fin_con_preparacion = models.DateTimeField(null=True, blank=True, db_comment='Fin más el alistamiento del recurso (lo calcula la base)')
    estado = models.CharField(max_length=10, choices=[('tentativa', 'tentativa'), ('confirmada', 'confirmada'), ('cumplida', 'cumplida'), ('cancelada', 'cancelada')], db_default='confirmada', db_comment='Estado')
    reserva = models.ForeignKey('turismo.Reserva', models.DO_NOTHING, db_column='reserva_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Reserva de turismo')
    bloqueo = models.ForeignKey('turismo.BloqueoCalendario', models.DO_NOTHING, db_column='bloqueo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Bloqueo del calendario')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea asociada (limpieza, mantenimiento)')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    notas = models.TextField(null=True, blank=True, db_comment='Notas')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "agenda", tabla "cita" (las comillas separan esquema y tabla)
        db_table = 'agenda"."cita'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Bloque del calendario de un recurso (reserva, limpieza, mantenimiento, uso familiar, entrega). La base impide cruces, contando el alistamiento.'


# ==============================================================================================================
# Tabla agenda.visita  ·  por finca (seguridad por filas)  ·  API: /api/v1/agenda/visitas/
# ==============================================================================================================
class Visita(models.Model):
    """Ingreso programado de una persona o un vehículo (proveedor, cliente, turista, técnico, autoridad): se aprueba antes, entrega un pase QR y exige bioseguridad si va al galpón."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=13, choices=[('proveedor', 'proveedor'), ('cliente', 'cliente'), ('turista', 'turista'), ('contratista', 'contratista'), ('tecnico', 'tecnico'), ('autoridad', 'autoridad'), ('visitante', 'visitante'), ('transportador', 'transportador')], db_comment='Tipo de visitante')
    nombre = models.CharField(max_length=150, db_comment='Nombre de la persona o empresa')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tercero, si está registrado')
    personas = models.SmallIntegerField(db_default=1, db_comment='Número de personas')
    vehiculo_placa = models.CharField(max_length=10, null=True, blank=True, db_comment='Placa del vehículo')
    vehiculo_tipo = models.CharField(max_length=9, choices=[('carro', 'carro'), ('camioneta', 'camioneta'), ('camion', 'camion'), ('moto', 'moto'), ('tractor', 'tractor'), ('bicicleta', 'bicicleta')], null=True, blank=True, db_comment='Tipo de vehículo')
    motivo = models.CharField(max_length=200, db_comment='Motivo')
    zona_destino = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_destino_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona a la que va')
    ingreso_programado = models.DateTimeField(db_comment='Hora de llegada')
    salida_programada = models.DateTimeField(db_comment='Hora de salida')
    anfitrion = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='anfitrion_id', related_name='+', db_constraint=False, db_comment='Quién lo recibe')
    requiere_bioseguridad = models.BooleanField(db_default=False, db_comment='Entra a una zona de bioseguridad (galpón)')
    contacto_aves_reciente = models.BooleanField(null=True, blank=True, db_comment='Declaró contacto con otras aves en las últimas horas del parámetro cuarentena_aves_horas')
    pase_hash = models.CharField(max_length=64, null=True, blank=True, db_comment='Huella del código QR del pase')
    estado = models.CharField(max_length=10, choices=[('solicitada', 'solicitada'), ('aprobada', 'aprobada'), ('rechazada', 'rechazada'), ('en_sitio', 'en_sitio'), ('salio', 'salio'), ('no_llego', 'no_llego'), ('cancelada', 'cancelada')], db_default='solicitada', db_comment='Estado')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    motivo_rechazo = models.CharField(max_length=200, null=True, blank=True, db_comment='Motivo del rechazo')
    cita = models.ForeignKey('agenda.Cita', models.DO_NOTHING, db_column='cita_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cita de cargue o descargue, si aplica')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "agenda", tabla "visita" (las comillas separan esquema y tabla)
        db_table = 'agenda"."visita'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Ingreso programado de una persona o un vehículo (proveedor, cliente, turista, técnico, autoridad): se aprueba antes, entrega un pase QR y exige bioseguridad si va al galpón.'


# ==============================================================================================================
# Tabla agenda.registro_acceso  ·  por finca (seguridad por filas)  ·  API: /api/v1/agenda/registros-acceso/
# ==============================================================================================================
class RegistroAcceso(models.Model):
    """Cada entrada o salida real por la portería (persona o vehículo): con pase, carné QR o NFC, a mano o por lectura de placa. Funciona sin internet y alimenta la jornada."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    sentido = models.CharField(max_length=7, choices=[('entrada', 'entrada'), ('salida', 'salida')], db_comment='Entrada o salida')
    tipo = models.CharField(max_length=8, choices=[('persona', 'persona'), ('vehiculo', 'vehiculo')], db_comment='Qué pasa')
    visita = models.ForeignKey('agenda.Visita', models.DO_NOTHING, db_column='visita_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Visita programada')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Trabajador')
    nombre = models.CharField(max_length=150, null=True, blank=True, db_comment='Nombre (si no es visita ni trabajador)')
    placa = models.CharField(max_length=10, null=True, blank=True, db_comment='Placa')
    punto = models.CharField(max_length=40, db_default='porteria', db_comment='Punto de control')
    metodo = models.CharField(max_length=13, choices=[('pase_qr', 'pase_qr'), ('carne_qr', 'carne_qr'), ('carne_nfc', 'carne_nfc'), ('manual', 'manual'), ('lectura_placa', 'lectura_placa')], db_comment='Cómo se identificó')
    desinfeccion = models.BooleanField(db_default=False, db_comment='Pasó por desinfección (personas y vehículos que van al galpón)')
    ocurrido_en = models.DateTimeField(db_default=Now(), db_comment='Momento')
    registrado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='registrado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Portero o encargado')
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
        # Nombre real en PostgreSQL: esquema "agenda", tabla "registro_acceso" (las comillas separan esquema y tabla)
        db_table = 'agenda"."registro_acceso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cada entrada o salida real por la portería (persona o vehículo): con pase, carné QR o NFC, a mano o por lectura de placa. Funciona sin internet y alimenta la jornada.'
