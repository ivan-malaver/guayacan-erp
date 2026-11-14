"""Modelos del esquema adopcion: Adopción de árboles y animales: catálogo, sitios, bienes, contratos de compra y cuidado, cuotas, seguimiento, liquidaciones y saldo del adoptante.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «adopcion». Django usa estas clases para leer y escribir
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
# Tabla adopcion.plan  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/planes/
# ==============================================================================================================
class Plan(models.Model):
    """Catálogo de lo que se puede adoptar, con precio de compra y de readopción, cuota mensual, costos estimados (para el margen), meses de madurez, garantía y permiso que exige su liquidación."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código del plan (ej. FRU-CACAO)')
    nombre = models.CharField(max_length=120, db_comment='Nombre comercial del plan')
    tipo = models.CharField(max_length=9, choices=[('frutal', 'frutal'), ('maderable', 'maderable'), ('ovino', 'ovino'), ('caprino', 'caprino'), ('ave', 'ave')], db_comment='Grupo de especie')
    cultivo = models.ForeignKey('produccion.Cultivo', models.DO_NOTHING, db_column='cultivo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cultivo, si es frutal o maderable')
    especie = models.ForeignKey('produccion.Especie', models.DO_NOTHING, db_column='especie_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Especie animal, si es ovino, caprino o ave')
    precio_compra = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio de compra (incluye el bien, la siembra o instalación y el primer mes de cuidado)')
    precio_readopcion = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio para un nuevo adoptante de un bien abandonado')
    cuota_mensual = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Cuota mensual de cuidado que se ofrece')
    costo_bien = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Costo estimado del bien para la finca (plántula o animal, siembra)')
    costo_cuidado_mensual = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Costo estimado del cuidado mensual (insumos y mano de obra)')
    meses_madurez = models.SmallIntegerField(db_comment='Meses hasta la madurez (producción, tala o sacrificio)')
    garantia_meses = models.SmallIntegerField(db_default=12, db_comment='Meses de garantía de reposición si el bien muere')
    requiere_permiso = models.CharField(max_length=16, choices=[('ninguno', 'ninguno'), ('tala_car', 'tala_car'), ('remision_ica', 'remision_ica'), ('planta_beneficio', 'planta_beneficio')], db_default='ninguno', db_comment='Soporte legal que exige la liquidación final')
    descripcion = models.TextField(null=True, blank=True, db_comment='Descripción para el sitio público')
    activo = models.BooleanField(db_default=True, db_comment='Se ofrece a la venta')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "plan" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."plan'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Catálogo de lo que se puede adoptar, con precio de compra y de readopción, cuota mensual, costos estimados (para el margen), meses de madurez, garantía y permiso que exige su liquidación.'


# ==============================================================================================================
# Tabla adopcion.sitio  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/sitios/
# ==============================================================================================================
class Sitio(models.Model):
    """Lugar asignado por la administración: hoyo de siembra en un lote o cupo en corral o galpón, con coordenadas."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Zona o lote de la finca')
    codigo = models.CharField(max_length=20, db_comment='Código del sitio (letrero en campo)')
    tipo = models.CharField(max_length=12, choices=[('hoyo_siembra', 'hoyo_siembra'), ('corral', 'corral'), ('galpon', 'galpon')], db_comment='Clase de sitio')
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_comment='Latitud del sitio')
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_comment='Longitud del sitio')
    estado = models.CharField(max_length=12, choices=[('libre', 'libre'), ('reservado', 'reservado'), ('ocupado', 'ocupado'), ('inhabilitado', 'inhabilitado')], db_default='libre', db_comment='Disponibilidad del sitio')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "sitio" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."sitio'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lugar asignado por la administración: hoyo de siembra en un lote o cupo en corral o galpón, con coordenadas.'


# ==============================================================================================================
# Tabla adopcion.bien  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/bienes/
# ==============================================================================================================
class Bien(models.Model):
    """El árbol o el animal concreto que se vende, con su código, sitio, estado de vida y el bien al que reemplaza si fue repuesto en garantía."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código del bien (va en el letrero y el QR)')
    plan = models.ForeignKey('adopcion.Plan', models.DO_NOTHING, db_column='plan_id', related_name='+', db_constraint=False, db_comment='Plan al que pertenece')
    sitio = models.ForeignKey('adopcion.Sitio', models.DO_NOTHING, db_column='sitio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sitio donde está')
    animal = models.ForeignKey('produccion.Animal', models.DO_NOTHING, db_column='animal_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Animal registrado en producción, si es animal')
    fecha_inicio = models.DateField(null=True, blank=True, db_comment='Fecha de siembra o de inicio del cuidado')
    estado = models.CharField(max_length=13, choices=[('disponible', 'disponible'), ('reservado', 'reservado'), ('activo', 'activo'), ('en_readopcion', 'en_readopcion'), ('maduro', 'maduro'), ('liquidado', 'liquidado'), ('muerto', 'muerto')], db_default='disponible', db_comment='Estado de vida y de venta del bien')
    nombre_dado = models.CharField(max_length=60, null=True, blank=True, db_comment='Nombre que le da el adoptante')
    reemplaza = models.ForeignKey('adopcion.Bien', models.DO_NOTHING, db_column='reemplaza_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Bien muerto al que repone en garantía')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "bien" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."bien'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'El árbol o el animal concreto que se vende, con su código, sitio, estado de vida y el bien al que reemplaza si fue repuesto en garantía.'


# ==============================================================================================================
# Tabla adopcion.contrato  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/contratos/
# ==============================================================================================================
class Contrato(models.Model):
    """Compraventa del bien más servicio de cuidado mensual. Un bien vivo tiene a lo sumo un contrato activo; guarda la modalidad de siembra y la decisión en la madurez."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    numero = models.CharField(max_length=20, db_comment='Número del contrato')
    bien = models.ForeignKey('adopcion.Bien', models.DO_NOTHING, db_column='bien_id', related_name='+', db_constraint=False, db_comment='Bien vendido')
    adoptante = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='adoptante_id', related_name='+', db_constraint=False, db_comment='Adoptante (tercero)')
    tipo = models.CharField(max_length=10, choices=[('compra', 'compra'), ('readopcion', 'readopcion'), ('cesion', 'cesion')], db_comment='Origen del contrato')
    fecha = models.DateField(db_default=sql('CURRENT_DATE'), db_comment='Fecha del contrato')
    precio = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio pagado')
    cuota_mensual = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Cuota mensual pactada (no cambia si cambia el plan)')
    modalidad_siembra = models.CharField(max_length=10, choices=[('propia', 'propia'), ('trabajador', 'trabajador'), ('no_aplica', 'no_aplica')], db_default='no_aplica', db_comment='Quién siembra el árbol')
    consentimiento = models.ForeignKey('terceros.ConsentimientoDatos', models.DO_NOTHING, db_column='consentimiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Autorización de datos con finalidad seguimiento_adopcion')
    estado = models.CharField(max_length=21, choices=[('activo', 'activo'), ('terminado_abandono', 'terminado_abandono'), ('terminado_liquidacion', 'terminado_liquidacion'), ('cedido', 'cedido'), ('terminado_muerte', 'terminado_muerte')], db_default='activo', db_comment='Estado del contrato')
    decision_madurez = models.CharField(max_length=8, choices=[('mantener', 'mantener'), ('liquidar', 'liquidar')], null=True, blank=True, db_comment='Decisión del dueño en la madurez')
    decidido_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se registró la decisión')
    terminado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo terminó el contrato')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "contrato" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."contrato'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Compraventa del bien más servicio de cuidado mensual. Un bien vivo tiene a lo sumo un contrato activo; guarda la modalidad de siembra y la decisión en la madurez.'


# ==============================================================================================================
# Tabla adopcion.cuota  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/cuotas/
# ==============================================================================================================
class Cuota(models.Model):
    """Cuota mensual de cuidado; vence el día 10, se paga por la pasarela o se compensa con el saldo a favor del adoptante."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    contrato = models.ForeignKey('adopcion.Contrato', models.DO_NOTHING, db_column='contrato_id', related_name='+', db_constraint=False, db_comment='Contrato al que pertenece')
    periodo = models.DateField(db_comment='Mes cobrado (primer día del mes)')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor de la cuota')
    vence_en = models.DateField(db_comment='Fecha de vencimiento (día 10)')
    estado = models.CharField(max_length=10, choices=[('pendiente', 'pendiente'), ('pagada', 'pagada'), ('compensada', 'compensada'), ('anulada', 'anulada')], db_default='pendiente', db_comment='Estado de la cuota')
    pago = models.ForeignKey('comercial.Pago', models.DO_NOTHING, db_column='pago_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Pago que la canceló')
    pagada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se pagó o compensó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "cuota" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."cuota'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cuota mensual de cuidado; vence el día 10, se paga por la pasarela o se compensa con el saldo a favor del adoptante.'


# ==============================================================================================================
# Tabla adopcion.seguimiento  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/seguimientos/
# ==============================================================================================================
class Seguimiento(models.Model):
    """Bitácora que ve el adoptante: siembra, video, fotos, visitas, sanidad, mediciones, muerte, reposición y avisos de mora. Se captura sin conexión."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    bien = models.ForeignKey('adopcion.Bien', models.DO_NOTHING, db_column='bien_id', related_name='+', db_constraint=False, db_comment='Bien seguido')
    tipo = models.CharField(max_length=13, choices=[('siembra', 'siembra'), ('video_siembra', 'video_siembra'), ('foto', 'foto'), ('visita', 'visita'), ('sanidad', 'sanidad'), ('medicion', 'medicion'), ('muerte', 'muerte'), ('reposicion', 'reposicion'), ('aviso_mora', 'aviso_mora')], db_comment='Clase de registro')
    fecha = models.DateTimeField(db_default=Now(), db_comment='Fecha y hora del registro')
    descripcion = models.TextField(null=True, blank=True, db_comment='Descripción')
    evidencia_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Foto o video en el almacén de objetos')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea de campo que lo originó')
    enviado_al_adoptante = models.BooleanField(db_default=False, db_comment='Ya se envió al adoptante')
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
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "seguimiento" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."seguimiento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Bitácora que ve el adoptante: siembra, video, fotos, visitas, sanidad, mediciones, muerte, reposición y avisos de mora. Se captura sin conexión.'


# ==============================================================================================================
# Tabla adopcion.liquidacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/liquidaciones/
# ==============================================================================================================
class Liquidacion(models.Model):
    """Venta de productos o liquidación final (tala, sacrificio, venta en pie): ingresos menos gastos = utilidad neta; la finca cobra el % de administración solo si hay utilidad."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    contrato = models.ForeignKey('adopcion.Contrato', models.DO_NOTHING, db_column='contrato_id', related_name='+', db_constraint=False, db_comment='Contrato liquidado')
    tipo = models.CharField(max_length=12, choices=[('productos', 'productos'), ('tala', 'tala'), ('sacrificio', 'sacrificio'), ('venta_en_pie', 'venta_en_pie')], db_comment='Clase de liquidación')
    periodo_desde = models.DateField(null=True, blank=True, db_comment='Inicio del periodo liquidado (productos)')
    periodo_hasta = models.DateField(null=True, blank=True, db_comment='Fin del periodo liquidado (productos)')
    ingresos = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Ingresos de la venta')
    gastos = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Gastos directos atribuibles')
    utilidad_neta = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Ingresos menos gastos (la calcula la base)')
    comision_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Porcentaje de administración vigente (parámetro comision_adopcion_pct)')
    comision = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Comisión de la finca: % de la utilidad positiva')
    abono_adoptante = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Lo que se abona al adoptante')
    soporte_documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='soporte_documento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Permiso de tala, remisión ICA o acta de beneficio')
    estado = models.CharField(max_length=8, choices=[('borrador', 'borrador'), ('aprobada', 'aprobada'), ('anulada', 'anulada')], db_default='borrador', db_comment='Estado de la liquidación')
    aprobada_por = models.BigIntegerField(null=True, blank=True, db_comment='Persona que la aprobó')
    aprobada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se aprobó')
    detalle = models.JSONField(db_default=sql("'[]'::jsonb"), db_comment='Líneas de ingresos y gastos (JSON)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "liquidacion" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."liquidacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Venta de productos o liquidación final (tala, sacrificio, venta en pie): ingresos menos gastos = utilidad neta; la finca cobra el % de administración solo si hay utilidad.'


# ==============================================================================================================
# Tabla adopcion.movimiento_saldo  ·  por finca (seguridad por filas)  ·  API: /api/v1/adopcion/movimientos-saldo/
# ==============================================================================================================
class MovimientoSaldo(models.Model):
    """Cuenta del adoptante, solo inserción: abonos de liquidaciones, cuotas compensadas y pagos al adoptante. No genera intereses ni se invierte."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    adoptante = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='adoptante_id', related_name='+', db_constraint=False, db_comment='Adoptante dueño del saldo')
    tipo = models.CharField(max_length=18, choices=[('abono_liquidacion', 'abono_liquidacion'), ('compensacion_cuota', 'compensacion_cuota'), ('pago_al_adoptante', 'pago_al_adoptante')], db_comment='Clase de movimiento')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor (siempre positivo; el tipo da el signo)')
    liquidacion = models.ForeignKey('adopcion.Liquidacion', models.DO_NOTHING, db_column='liquidacion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Liquidación que lo originó')
    cuota = models.ForeignKey('adopcion.Cuota', models.DO_NOTHING, db_column='cuota_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cuota compensada')
    referencia = models.CharField(max_length=80, null=True, blank=True, db_comment='Referencia del pago al adoptante')
    fecha = models.DateTimeField(db_default=Now(), db_comment='Fecha y hora del movimiento')
    creado_en = models.DateTimeField(db_default=Now(), db_comment='Fecha y hora de creación del registro')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "adopcion", tabla "movimiento_saldo" (las comillas separan esquema y tabla)
        db_table = 'adopcion"."movimiento_saldo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cuenta del adoptante, solo inserción: abonos de liquidaciones, cuotas compensadas y pagos al adoptante. No genera intereses ni se invierte.'
