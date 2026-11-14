"""Modelos del esquema activos: Hoja de vida de equipos, planes y órdenes de mantenimiento, uso, repuestos y depreciación.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «activos». Django usa estas clases para leer y escribir
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
# Tabla activos.activo  ·  por finca (seguridad por filas)  ·  API: /api/v1/activos/activos/
# ==============================================================================================================
class Activo(models.Model):
    """Hoja de vida de cada equipo de la finca (camioneta, motocultor, guadañas, bombas, paneles, dron, robot)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. ACT-GUA-01')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    tipo = models.CharField(max_length=18, choices=[('vehiculo', 'vehiculo'), ('maquinaria', 'maquinaria'), ('herramienta', 'herramienta'), ('bomba', 'bomba'), ('panel_solar', 'panel_solar'), ('bateria', 'bateria'), ('equipo_electronico', 'equipo_electronico'), ('dron', 'dron'), ('robot', 'robot'), ('infraestructura', 'infraestructura'), ('otro', 'otro')], db_comment='Tipo')
    marca = models.CharField(max_length=60, null=True, blank=True, db_comment='Marca')
    modelo = models.CharField(max_length=60, null=True, blank=True, db_comment='Modelo')
    serie = models.CharField(max_length=60, null=True, blank=True, db_comment='Número de serie')
    fecha_compra = models.DateField(null=True, blank=True, db_comment='Compra')
    valor_compra = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Costo de adquisición')
    valor_residual = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Valor de salvamento')
    vida_util_meses = models.SmallIntegerField(null=True, blank=True, db_comment='Vida útil')
    metodo_depreciacion = models.CharField(max_length=11, choices=[('linea_recta', 'linea_recta'), ('ninguno', 'ninguno')], db_default='linea_recta', db_comment='Método')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ubicación')
    responsable = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Centro de costo que lo usa')
    garantia_hasta = models.DateField(null=True, blank=True, db_comment='Garantía')
    horometro = models.DecimalField(max_digits=10, decimal_places=1, db_default=0, db_comment='Horas de uso acumuladas')
    odometro = models.DecimalField(max_digits=10, decimal_places=1, db_default=0, db_comment='Kilómetros acumulados')
    vehiculo = models.ForeignKey('inventario.Vehiculo', models.DO_NOTHING, db_column='vehiculo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Vehículo de entregas, si es el mismo')
    dispositivo = models.ForeignKey('iot.Dispositivo', models.DO_NOTHING, db_column='dispositivo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Dispositivo IoT, si lo tiene')
    registro_aerocivil = models.CharField(max_length=40, null=True, blank=True, db_comment='Registro del dron ante la Aerocivil (RAC 100)')
    estado = models.CharField(max_length=16, choices=[('operativo', 'operativo'), ('en_mantenimiento', 'en_mantenimiento'), ('danado', 'danado'), ('dado_de_baja', 'dado_de_baja')], db_default='operativo', db_comment='Estado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "activos", tabla "activo" (las comillas separan esquema y tabla)
        db_table = 'activos"."activo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Hoja de vida de cada equipo de la finca (camioneta, motocultor, guadañas, bombas, paneles, dron, robot).'


# ==============================================================================================================
# Tabla activos.plan_mantenimiento  ·  por finca (seguridad por filas)  ·  API: /api/v1/activos/planes-mantenimiento/
# ==============================================================================================================
class PlanMantenimiento(models.Model):
    """Mantenimiento por horas de uso, kilómetros o días (cambio de aceite, afilado, revisión de la bomba)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, db_comment='Equipo')
    nombre = models.CharField(max_length=120, db_comment='Qué se hace')
    tipo = models.CharField(max_length=10, choices=[('preventivo', 'preventivo'), ('predictivo', 'predictivo')], db_default='preventivo', db_comment='Tipo (predictivo cuando hay sensores)')
    frecuencia_tipo = models.CharField(max_length=5, choices=[('horas', 'horas'), ('km', 'km'), ('dias', 'dias')], db_comment='Base de la frecuencia')
    frecuencia_valor = models.DecimalField(max_digits=10, decimal_places=1, db_comment='Cada cuánto')
    ultima_lectura = models.DecimalField(max_digits=10, decimal_places=1, db_default=0, db_comment='Horómetro u odómetro en la última ejecución')
    ultima_fecha = models.DateField(null=True, blank=True, db_comment='Fecha de la última ejecución')
    activo_ref = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "activos", tabla "plan_mantenimiento" (las comillas separan esquema y tabla)
        db_table = 'activos"."plan_mantenimiento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Mantenimiento por horas de uso, kilómetros o días (cambio de aceite, afilado, revisión de la bomba).'


# ==============================================================================================================
# Tabla activos.orden_trabajo  ·  por finca (seguridad por filas)  ·  API: /api/v1/activos/ordenes-trabajo/
# ==============================================================================================================
class OrdenTrabajo(models.Model):
    """Orden de mantenimiento: la crea sola la regla al vencer el plan y se asigna como tarea; descuenta repuestos del inventario."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, db_comment='Equipo')
    plan = models.ForeignKey('activos.PlanMantenimiento', models.DO_NOTHING, db_column='plan_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Plan que la originó')
    tipo = models.CharField(max_length=10, choices=[('preventivo', 'preventivo'), ('correctivo', 'correctivo'), ('predictivo', 'predictivo')], db_comment='Tipo')
    descripcion = models.TextField(db_comment='Qué hacer')
    estado = models.CharField(max_length=9, choices=[('abierta', 'abierta'), ('en_curso', 'en_curso'), ('cerrada', 'cerrada'), ('cancelada', 'cancelada')], db_default='abierta', db_comment='Estado')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea asignada')
    lectura_cierre = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True, db_comment='Horómetro u odómetro al cerrar')
    costo_mano_obra = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Mano de obra')
    costo_repuestos = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Repuestos')
    cerrada_en = models.DateTimeField(null=True, blank=True, db_comment='Cierre')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "activos", tabla "orden_trabajo" (las comillas separan esquema y tabla)
        db_table = 'activos"."orden_trabajo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Orden de mantenimiento: la crea sola la regla al vencer el plan y se asigna como tarea; descuenta repuestos del inventario.'


# ==============================================================================================================
# Tabla activos.repuesto_orden  ·  por finca (seguridad por filas)  ·  API: /api/v1/activos/ordenes-trabajo/{id}/repuestos/
# ==============================================================================================================
class RepuestoOrden(models.Model):
    """Repuesto usado en una orden de trabajo (sale del kardex)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    orden = models.ForeignKey('activos.OrdenTrabajo', models.DO_NOTHING, db_column='orden_id', related_name='+', db_constraint=False, db_comment='Orden')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Repuesto')
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, db_comment='Cantidad')
    movimiento = models.ForeignKey('inventario.MovimientoInventario', models.DO_NOTHING, db_column='movimiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Salida en el kardex')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "activos", tabla "repuesto_orden" (las comillas separan esquema y tabla)
        db_table = 'activos"."repuesto_orden'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Repuesto usado en una orden de trabajo (sale del kardex).'


# ==============================================================================================================
# Tabla activos.uso_activo  ·  por finca (seguridad por filas)  ·  API: /api/v1/activos/usos-activo/
# ==============================================================================================================
class UsoActivo(models.Model):
    """Uso de un equipo: horas, kilómetros y combustible, cargados al centro de costo que lo usó."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, db_comment='Equipo')
    fecha = models.DateField(db_comment='Día')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo usó')
    horas = models.DecimalField(max_digits=6, decimal_places=1, db_default=0, db_comment='Horas')
    km = models.DecimalField(max_digits=8, decimal_places=1, db_default=0, db_comment='Kilómetros')
    combustible_litros = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, db_comment='Combustible')
    costo_combustible = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Costo del combustible')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Centro de costo')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea')
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
        # Nombre real en PostgreSQL: esquema "activos", tabla "uso_activo" (las comillas separan esquema y tabla)
        db_table = 'activos"."uso_activo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Uso de un equipo: horas, kilómetros y combustible, cargados al centro de costo que lo usó.'


# ==============================================================================================================
# Tabla activos.depreciacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/activos/depreciaciones/
# ==============================================================================================================
class Depreciacion(models.Model):
    """Depreciación mensual de cada activo (alimenta la contabilidad y el costo por línea)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, db_comment='Equipo')
    mes = models.DateField(db_comment='Primer día del mes')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Depreciación del mes')
    acumulada = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Depreciación acumulada')
    comprobante = models.ForeignKey('finanzas.Comprobante', models.DO_NOTHING, db_column='comprobante_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Comprobante')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "activos", tabla "depreciacion" (las comillas separan esquema y tabla)
        db_table = 'activos"."depreciacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Depreciación mensual de cada activo (alimenta la contabilidad y el costo por línea).'
