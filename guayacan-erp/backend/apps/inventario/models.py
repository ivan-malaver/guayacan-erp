"""Modelos del esquema inventario: Catálogo de productos, bodegas, lotes de inventario y kardex de movimientos.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «inventario». Django usa estas clases para leer y escribir
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
# Tabla inventario.unidad_medida  ·  catálogo compartido entre fincas  ·  API: /api/v1/inventario/unidades-medida/
# ==============================================================================================================
class UnidadMedida(models.Model):
    """Unidades (kg, cubeta, unidad, bulto, litro) y su conversión a la unidad base."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=10, unique=True, db_comment='Código, ej. kg, cub30, und, bul40')
    nombre = models.CharField(max_length=40, db_comment='Nombre')
    unidad_base = models.CharField(max_length=10, null=True, blank=True, db_comment='Unidad a la que se convierte, ej. und o kg')
    factor_base = models.DecimalField(max_digits=12, decimal_places=4, db_default=1, db_comment='Cuántas unidades base contiene (cubeta = 30 und)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "unidad_medida" (las comillas separan esquema y tabla)
        db_table = 'inventario"."unidad_medida'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Unidades (kg, cubeta, unidad, bulto, litro) y su conversión a la unidad base.'


# ==============================================================================================================
# Tabla inventario.categoria_producto  ·  catálogo compartido entre fincas  ·  API: /api/v1/inventario/categorias-producto/
# ==============================================================================================================
class CategoriaProducto(models.Model):
    """Agrupación jerárquica de productos (huevo, carne en pie, granos, insumos, medicamentos)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    padre = models.ForeignKey('inventario.CategoriaProducto', models.DO_NOTHING, db_column='padre_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Categoría superior')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "categoria_producto" (las comillas separan esquema y tabla)
        db_table = 'inventario"."categoria_producto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Agrupación jerárquica de productos (huevo, carne en pie, granos, insumos, medicamentos).'


# ==============================================================================================================
# Tabla inventario.producto  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/productos/
# ==============================================================================================================
class Producto(models.Model):
    """Todo lo que se vende, se compra o se produce: cubeta de huevo, kg de tilapia, bulto de concentrado."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    sku = models.CharField(max_length=30, db_comment='Código interno, ej. HUE-AA-30')
    nombre = models.CharField(max_length=150, db_comment='Nombre comercial')
    descripcion = models.TextField(null=True, blank=True, db_comment='Descripción para el catálogo y para los agentes')
    categoria = models.ForeignKey('inventario.CategoriaProducto', models.DO_NOTHING, db_column='categoria_id', related_name='+', db_constraint=False, db_comment='Categoría')
    unidad = models.ForeignKey('inventario.UnidadMedida', models.DO_NOTHING, db_column='unidad_id', related_name='+', db_constraint=False, db_comment='Unidad de venta o de control')
    tipo = models.CharField(max_length=18, choices=[('producto_terminado', 'producto_terminado'), ('insumo', 'insumo'), ('servicio', 'servicio'), ('activo_menor', 'activo_menor')], db_comment='Naturaleza')
    se_vende = models.BooleanField(db_default=False, db_comment='Aparece en el catálogo')
    se_compra = models.BooleanField(db_default=False, db_comment='Se compra a proveedores')
    se_produce = models.BooleanField(db_default=False, db_comment='Se produce en la finca')
    perecedero = models.BooleanField(db_default=False, db_comment='Tiene vencimiento')
    vida_util_ambiente_dias = models.SmallIntegerField(null=True, blank=True, db_comment='Días que dura a temperatura ambiente (base para estimar el vencimiento)')
    vida_util_refrigerado_dias = models.SmallIntegerField(null=True, blank=True, db_comment='Días que dura refrigerado')
    dias_margen_venta = models.SmallIntegerField(db_default=0, db_comment='Días antes del vencimiento en que se deja de vender (fecha límite de venta)')
    dias_alerta_venta = models.SmallIntegerField(db_default=0, db_comment='Días antes de la fecha límite de venta en que se activa la alerta para venderlo primero')
    metodo_salida = models.CharField(max_length=4, choices=[('fefo', 'fefo'), ('fifo', 'fifo')], db_default='fefo', db_comment='Orden de salida: fefo = primero lo que vence primero; fifo = primero lo que entró primero')
    gtin = models.CharField(max_length=14, null=True, blank=True, db_comment='Código de barras comercial GS1 (EAN-13 o GTIN-14), si la finca lo obtiene; vacío = solo códigos internos')
    pesable = models.BooleanField(db_default=False, db_comment='Se vende o controla por peso leído en báscula (tilapia, cordero en pie)')
    peso_nominal_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, db_comment='Peso esperado por unidad, para validar lo que marca la báscula (ej. cubeta)')
    tolerancia_peso_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Diferencia máxima aceptada contra el peso nominal antes de alertar')
    tarifa_iva = models.DecimalField(max_digits=5, decimal_places=2, db_default=0, db_comment='IVA en %: huevo y carne en pie están excluidos (0)')
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Alerta de reposición')
    activo = models.BooleanField(db_default=True, db_comment='Si se sigue usando')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "producto" (las comillas separan esquema y tabla)
        db_table = 'inventario"."producto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Todo lo que se vende, se compra o se produce: cubeta de huevo, kg de tilapia, bulto de concentrado.'


# ==============================================================================================================
# Tabla inventario.bodega  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/bodegas/
# ==============================================================================================================
class Bodega(models.Model):
    """Lugar físico donde se guarda inventario."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código')
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona del predio')
    refrigerada = models.BooleanField(db_default=False, db_comment='Nevera o cuarto frío; sus lotes usan la vida útil refrigerada')
    sensor_temperatura = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_temperatura_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sensor que vigila la temperatura (cadena de frío)')
    temperatura_min_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, db_comment='Temperatura mínima aceptada en °C')
    temperatura_max_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, db_comment='Temperatura máxima aceptada en °C')
    minutos_tolerancia = models.SmallIntegerField(db_default=30, db_comment='Minutos fuera de rango antes de bloquear los lotes')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "bodega" (las comillas separan esquema y tabla)
        db_table = 'inventario"."bodega'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lugar físico donde se guarda inventario.'


# ==============================================================================================================
# Tabla inventario.lote_inventario  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/lotes-inventario/
# ==============================================================================================================
class LoteInventario(models.Model):
    """Existencia concreta de un producto con fecha, origen y vencimiento. Sus cantidades solo las cambia el kardex (movimiento_inventario); la salida sigue el orden FEFO: primero lo que vence primero."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    bodega = models.ForeignKey('inventario.Bodega', models.DO_NOTHING, db_column='bodega_id', related_name='+', db_constraint=False, db_comment='Bodega')
    codigo_lote = models.CharField(max_length=30, db_comment='Código de trazabilidad, ej. HUE-20261025-GAL01')
    origen = models.CharField(max_length=10, choices=[('produccion', 'produccion'), ('compra', 'compra'), ('ajuste', 'ajuste')], db_comment='De dónde salió')
    origen_tabla = models.CharField(max_length=60, null=True, blank=True, db_comment='Tabla de origen (cosecha, registro_postura, orden_compra_detalle)')
    origen_id = models.BigIntegerField(null=True, blank=True, db_comment='Id en la tabla de origen')
    fecha_produccion = models.DateField(db_comment='Fecha de producción, postura, cosecha o recepción')
    condicion_almacenamiento = models.CharField(max_length=11, choices=[('ambiente', 'ambiente'), ('refrigerado', 'refrigerado')], db_default='ambiente', db_comment='Cómo se guarda; cambia la vida útil usada en la estimación')
    origen_vencimiento = models.CharField(max_length=11, choices=[('estimado', 'estimado'), ('manual', 'manual'), ('laboratorio', 'laboratorio')], db_default='estimado', db_comment='estimado = lo calcula el sistema con la vida útil del producto; manual o laboratorio = lo fija una persona')
    fecha_vencimiento = models.DateField(null=True, blank=True, db_comment='Fecha en que el producto deja de ser apto (calculada si origen_vencimiento = estimado)')
    fecha_limite_venta = models.DateField(null=True, blank=True, db_comment='Último día para venderlo: vencimiento menos los días de margen del producto')
    peso_neto_kg = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, db_comment='Peso total leído en báscula al ingresar, si el producto es pesable')
    cantidad_inicial = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad al crearse (genera automáticamente el movimiento de entrada)')
    cantidad_disponible = models.DecimalField(max_digits=12, decimal_places=2, db_default=0, db_comment='Libre para vender; solo la cambia el kardex')
    cantidad_reservada = models.DecimalField(max_digits=12, decimal_places=2, db_default=0, db_comment='Comprometida en pedidos confirmados; solo la cambia el kardex')
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Costo por unidad')
    estado = models.CharField(max_length=10, choices=[('disponible', 'disponible'), ('agotado', 'agotado'), ('vencido', 'vencido'), ('bloqueado', 'bloqueado')], db_default='disponible', db_comment='Situación: agotado y vencido los pone el sistema; bloqueado lo pone un bloqueo_lote abierto (cadena de frío, sanidad, retiro)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "lote_inventario" (las comillas separan esquema y tabla)
        db_table = 'inventario"."lote_inventario'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Existencia concreta de un producto con fecha, origen y vencimiento. Sus cantidades solo las cambia el kardex (movimiento_inventario); la salida sigue el orden FEFO: primero lo que vence primero.'


# ==============================================================================================================
# Tabla inventario.movimiento_inventario  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/movimientos-inventario/
# ==============================================================================================================
class MovimientoInventario(models.Model):
    """Kardex: cada entrada, salida, ajuste, traslado o merma, con el documento que lo causó."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, db_comment='Lote movido')
    tipo = models.CharField(max_length=16, choices=[('entrada', 'entrada'), ('reserva', 'reserva'), ('liberacion', 'liberacion'), ('salida_venta', 'salida_venta'), ('consumo_interno', 'consumo_interno'), ('merma', 'merma'), ('ajuste_entrada', 'ajuste_entrada'), ('ajuste_salida', 'ajuste_salida'), ('traslado_salida', 'traslado_salida'), ('traslado_entrada', 'traslado_entrada')], db_comment='Tipo de movimiento; define qué cantidad del lote cambia (ver reglas del kardex)')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad (siempre positiva; el tipo da el sentido)')
    causa_merma = models.CharField(max_length=7, choices=[('vencido', 'vencido'), ('roto', 'roto'), ('plaga', 'plaga'), ('calidad', 'calidad'), ('robo', 'robo'), ('otro', 'otro')], null=True, blank=True, db_comment='Por qué se perdió, cuando tipo = merma (alimenta el ajuste de la vida útil estimada)')
    pesaje = models.ForeignKey('inventario.Pesaje', models.DO_NOTHING, db_column='pesaje_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Lectura de báscula que respalda la cantidad, si aplica')
    lectura_codigo = models.ForeignKey('inventario.LecturaCodigo', models.DO_NOTHING, db_column='lectura_codigo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Escaneo de código que originó el movimiento, si aplica')
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Costo usado')
    documento_tipo = models.CharField(max_length=40, db_comment='Documento origen, ej. pedido, cosecha, orden_compra')
    documento_id = models.BigIntegerField(db_comment='Id del documento')
    ocurrido_en = models.DateTimeField(db_default=Now(), db_comment='Momento')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo registró')
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
        # Nombre real en PostgreSQL: esquema "inventario", tabla "movimiento_inventario" (las comillas separan esquema y tabla)
        db_table = 'inventario"."movimiento_inventario'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Kardex: cada entrada, salida, ajuste, traslado o merma, con el documento que lo causó.'


# ==============================================================================================================
# Tabla inventario.etiqueta  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/etiquetas/
# ==============================================================================================================
class Etiqueta(models.Model):
    """Código de barras o QR impreso para un lote. Interno (Code 128 o QR) o GS1-128 si la finca obtiene códigos GS1."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, db_comment='Lote identificado')
    codigo = models.CharField(max_length=80, db_comment='Texto que contiene el código, ej. GY-HUE-20261025-GAL01 o (01)…(10)…(17)…')
    simbologia = models.CharField(max_length=14, choices=[('code128', 'code128'), ('qr', 'qr'), ('gs1_128', 'gs1_128'), ('gs1_datamatrix', 'gs1_datamatrix'), ('ean13', 'ean13')], db_comment='Tipo de código impreso')
    impresora = models.ForeignKey('nucleo.DispositivoCaptura', models.DO_NOTHING, db_column='impresora_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Impresora usada')
    impresa_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se imprimió')
    anulada = models.BooleanField(db_default=False, db_comment='Etiqueta dañada o reemplazada; si se escanea, se rechaza')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "etiqueta" (las comillas separan esquema y tabla)
        db_table = 'inventario"."etiqueta'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Código de barras o QR impreso para un lote. Interno (Code 128 o QR) o GS1-128 si la finca obtiene códigos GS1.'


# ==============================================================================================================
# Tabla inventario.lectura_codigo  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/lecturas-codigo/
# ==============================================================================================================
class LecturaCodigo(models.Model):
    """Cada escaneo de un código: qué se leyó, con qué equipo, para qué y qué resultado tuvo."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo_leido = models.CharField(max_length=120, db_comment='Texto leído')
    simbologia = models.CharField(max_length=20, null=True, blank=True, db_comment='Tipo detectado')
    etiqueta = models.ForeignKey('inventario.Etiqueta', models.DO_NOTHING, db_column='etiqueta_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Etiqueta encontrada, si existe')
    accion = models.CharField(max_length=8, choices=[('consulta', 'consulta'), ('entrada', 'entrada'), ('salida', 'salida'), ('conteo', 'conteo'), ('traslado', 'traslado'), ('despacho', 'despacho')], db_comment='Para qué se escaneó')
    resultado = models.CharField(max_length=11, choices=[('ok', 'ok'), ('desconocido', 'desconocido'), ('anulado', 'anulado'), ('vencido', 'vencido'), ('duplicado', 'duplicado'), ('rechazado', 'rechazado')], db_comment='Resultado de la validación')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, db_comment='Quién escaneó')
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
        # Nombre real en PostgreSQL: esquema "inventario", tabla "lectura_codigo" (las comillas separan esquema y tabla)
        db_table = 'inventario"."lectura_codigo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cada escaneo de un código: qué se leyó, con qué equipo, para qué y qué resultado tuvo.'


# ==============================================================================================================
# Tabla inventario.pesaje  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/pesajes/
# ==============================================================================================================
class Pesaje(models.Model):
    """Lectura de una báscula digital, automática o digitada, con tara y estabilidad."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    peso_bruto_kg = models.DecimalField(max_digits=12, decimal_places=3, db_comment='Peso total en la báscula')
    tara_kg = models.DecimalField(max_digits=12, decimal_places=3, db_default=0, db_comment='Peso del recipiente (canastilla, bulto, nevera)')
    peso_neto_kg = models.DecimalField(max_digits=12, decimal_places=3, db_comment='Bruto menos tara')
    estable = models.BooleanField(db_comment='La báscula indicó lectura estable; si es falso, no se acepta para vender')
    origen = models.CharField(max_length=18, choices=[('bascula_automatica', 'bascula_automatica'), ('digitado', 'digitado')], db_comment='Leído del equipo o escrito a mano (el digitado queda marcado en informes)')
    referencia_tabla = models.CharField(max_length=60, null=True, blank=True, db_comment='Para qué se pesó, ej. cosecha, registro_pesaje, pedido_detalle')
    referencia_id = models.BigIntegerField(null=True, blank=True, db_comment='Id del registro relacionado')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, db_comment='Quién pesó')
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
        # Nombre real en PostgreSQL: esquema "inventario", tabla "pesaje" (las comillas separan esquema y tabla)
        db_table = 'inventario"."pesaje'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lectura de una báscula digital, automática o digitada, con tara y estabilidad.'


# ==============================================================================================================
# Tabla inventario.conteo_fisico  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/conteos/
# ==============================================================================================================
class ConteoFisico(models.Model):
    """Inventario físico de una bodega: se escanea lo que hay y se compara con el sistema."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    bodega = models.ForeignKey('inventario.Bodega', models.DO_NOTHING, db_column='bodega_id', related_name='+', db_constraint=False, db_comment='Bodega contada')
    fecha = models.DateField(db_comment='Día del conteo')
    estado = models.CharField(max_length=8, choices=[('en_curso', 'en_curso'), ('cerrado', 'cerrado'), ('ajustado', 'ajustado')], db_default='en_curso', db_comment='Ajustado = las diferencias ya generaron movimientos de ajuste')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, db_comment='Responsable')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "conteo_fisico" (las comillas separan esquema y tabla)
        db_table = 'inventario"."conteo_fisico'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Inventario físico de una bodega: se escanea lo que hay y se compara con el sistema.'


# ==============================================================================================================
# Tabla inventario.conteo_detalle  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/conteos/{id}/detalles/
# ==============================================================================================================
class ConteoDetalle(models.Model):
    """Resultado del conteo por lote."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    conteo_fisico = models.ForeignKey('inventario.ConteoFisico', models.DO_NOTHING, db_column='conteo_fisico_id', related_name='+', db_constraint=False, db_comment='Conteo')
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, db_comment='Lote contado')
    cantidad_sistema = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Lo que decía el sistema al contar')
    cantidad_contada = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Lo encontrado')
    movimiento_ajuste = models.ForeignKey('inventario.MovimientoInventario', models.DO_NOTHING, db_column='movimiento_ajuste_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ajuste generado por la diferencia')
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
        # Nombre real en PostgreSQL: esquema "inventario", tabla "conteo_detalle" (las comillas separan esquema y tabla)
        db_table = 'inventario"."conteo_detalle'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Resultado del conteo por lote.'


# ==============================================================================================================
# Tabla inventario.vehiculo  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/vehiculos/
# ==============================================================================================================
class Vehiculo(models.Model):
    """Vehículo de entregas (camioneta, motocarro) y su registrador de temperatura."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. CAM-01')
    tipo = models.CharField(max_length=9, choices=[('camioneta', 'camioneta'), ('motocarro', 'motocarro'), ('moto', 'moto'), ('otro', 'otro')], db_comment='Tipo')
    placa = models.CharField(max_length=10, null=True, blank=True, db_comment='Placa')
    capacidad_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_comment='Carga máxima')
    refrigerado = models.BooleanField(db_default=False, db_comment='Tiene nevera o caja térmica')
    sensor_temperatura = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_temperatura_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Registrador de temperatura (guarda sin señal)')
    temperatura_max_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, db_comment='Temperatura máxima aceptada')
    minutos_tolerancia = models.SmallIntegerField(db_default=30, db_comment='Minutos fuera de rango antes de bloquear lo que transporta')
    activo = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "vehiculo" (las comillas separan esquema y tabla)
        db_table = 'inventario"."vehiculo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Vehículo de entregas (camioneta, motocarro) y su registrador de temperatura.'


# ==============================================================================================================
# Tabla inventario.excursion_temperatura  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/excursiones-temperatura/
# ==============================================================================================================
class ExcursionTemperatura(models.Model):
    """Periodo en que una nevera o un vehículo estuvo fuera de su rango de temperatura; si supera la tolerancia, bloquea los lotes perecederos."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    sensor = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_id', related_name='+', db_constraint=False, db_comment='Sensor que la detectó')
    bodega = models.ForeignKey('inventario.Bodega', models.DO_NOTHING, db_column='bodega_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Bodega afectada')
    vehiculo = models.ForeignKey('inventario.Vehiculo', models.DO_NOTHING, db_column='vehiculo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Vehículo afectado')
    inicio = models.DateTimeField(db_comment='Inicio')
    fin = models.DateTimeField(null=True, blank=True, db_comment='Fin; vacío = sigue fuera de rango')
    temperatura_extrema_c = models.DecimalField(max_digits=4, decimal_places=1, db_comment='Peor temperatura registrada')
    minutos_fuera = models.IntegerField(db_default=0, db_comment='Minutos fuera de rango')
    lotes_bloqueados = models.IntegerField(db_default=0, db_comment='Lotes que bloqueó (lo calcula la regla)')
    estado = models.CharField(max_length=7, choices=[('abierta', 'abierta'), ('cerrada', 'cerrada')], db_default='abierta', db_comment='Situación')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "excursion_temperatura" (las comillas separan esquema y tabla)
        db_table = 'inventario"."excursion_temperatura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Periodo en que una nevera o un vehículo estuvo fuera de su rango de temperatura; si supera la tolerancia, bloquea los lotes perecederos.'


# ==============================================================================================================
# Tabla inventario.bloqueo_lote  ·  por finca (seguridad por filas)  ·  API: /api/v1/inventario/bloqueos-lote/
# ==============================================================================================================
class BloqueoLote(models.Model):
    """Bloqueo de un lote y su decisión: lo pone una regla o una persona; liberarlo o descartarlo siempre lo decide una persona."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, db_comment='Lote bloqueado')
    motivo = models.CharField(max_length=11, choices=[('cadena_frio', 'cadena_frio'), ('sanitario', 'sanitario'), ('calidad', 'calidad'), ('retiro', 'retiro')], db_comment='Por qué')
    origen_tabla = models.CharField(max_length=60, null=True, blank=True, db_comment='Qué lo causó, ej. excursion_temperatura, retiro_lote')
    origen_id = models.BigIntegerField(null=True, blank=True, db_comment='Id del origen')
    decision = models.CharField(max_length=10, choices=[('pendiente', 'pendiente'), ('liberado', 'liberado'), ('descartado', 'descartado')], db_default='pendiente', db_comment='Liberado vuelve a disponible; descartado registra la merma')
    decidido_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='decidido_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona que decidió')
    decidido_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    observacion = models.TextField(null=True, blank=True, db_comment='Motivo de la decisión')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "inventario", tabla "bloqueo_lote" (las comillas separan esquema y tabla)
        db_table = 'inventario"."bloqueo_lote'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Bloqueo de un lote y su decisión: lo pone una regla o una persona; liberarlo o descartarlo siempre lo decide una persona.'
