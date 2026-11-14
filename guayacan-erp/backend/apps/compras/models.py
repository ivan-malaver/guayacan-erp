"""Modelos del esquema compras: Órdenes de compra, cotizaciones de proveedores y precios de mercado de referencia.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «compras». Django usa estas clases para leer y escribir
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
# Tabla compras.orden_compra  ·  por finca (seguridad por filas)  ·  API: /api/v1/compras/ordenes-compra/
# ==============================================================================================================
class OrdenCompra(models.Model):
    """Compra a un proveedor."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    numero = models.CharField(max_length=20, db_comment='Consecutivo')
    proveedor = models.ForeignKey('terceros.Proveedor', models.DO_NOTHING, db_column='proveedor_id', related_name='+', db_constraint=False, db_comment='Proveedor')
    fecha = models.DateField(db_comment='Fecha')
    estado = models.CharField(max_length=8, choices=[('borrador', 'borrador'), ('aprobada', 'aprobada'), ('recibida', 'recibida'), ('parcial', 'parcial'), ('anulada', 'anulada')], db_default='borrador', db_comment='Situación')
    total = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Total')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "compras", tabla "orden_compra" (las comillas separan esquema y tabla)
        db_table = 'compras"."orden_compra'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Compra a un proveedor.'


# ==============================================================================================================
# Tabla compras.orden_compra_detalle  ·  por finca (seguridad por filas)  ·  API: /api/v1/compras/ordenes-compra/{id}/lineas/
# ==============================================================================================================
class OrdenCompraDetalle(models.Model):
    """Línea de la orden de compra."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    orden_compra = models.ForeignKey('compras.OrdenCompra', models.DO_NOTHING, db_column='orden_compra_id', related_name='+', db_constraint=False, db_comment='Orden')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Insumo')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad pedida')
    cantidad_recibida = models.DecimalField(max_digits=12, decimal_places=2, db_default=0, db_comment='Cantidad recibida')
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio pactado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "compras", tabla "orden_compra_detalle" (las comillas separan esquema y tabla)
        db_table = 'compras"."orden_compra_detalle'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Línea de la orden de compra.'


# ==============================================================================================================
# Tabla compras.cotizacion_proveedor  ·  por finca (seguridad por filas)  ·  API: /api/v1/compras/cotizaciones-proveedor/
# ==============================================================================================================
class CotizacionProveedor(models.Model):
    """Precio ofrecido por un proveedor para un insumo, registrado por una persona o por el agente de mercados."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proveedor = models.ForeignKey('terceros.Proveedor', models.DO_NOTHING, db_column='proveedor_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Proveedor, si está registrado')
    nombre_proveedor = models.CharField(max_length=150, null=True, blank=True, db_comment='Nombre si aún no es tercero')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Insumo')
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio')
    fecha = models.DateField(db_comment='Fecha de la cotización')
    vigente_hasta = models.DateField(null=True, blank=True, db_comment='Validez')
    fuente = models.CharField(max_length=8, choices=[('visita', 'visita'), ('telefono', 'telefono'), ('correo', 'correo'), ('web', 'web'), ('agente', 'agente')], db_comment='Cómo se obtuvo')
    fuente_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Enlace, si es web')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "compras", tabla "cotizacion_proveedor" (las comillas separan esquema y tabla)
        db_table = 'compras"."cotizacion_proveedor'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Precio ofrecido por un proveedor para un insumo, registrado por una persona o por el agente de mercados.'


# ==============================================================================================================
# Tabla compras.precio_mercado  ·  por finca (seguridad por filas)  ·  API: /api/v1/compras/precios-mercado/
# ==============================================================================================================
class PrecioMercado(models.Model):
    """Precio de referencia de un producto en un mercado (SIPSA-DANE, Corabastos, Fenavi), usado por el agente analista."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto comparable')
    mercado = models.CharField(max_length=80, db_comment='Mercado o fuente, ej. Corabastos, SIPSA Girardot')
    fecha = models.DateField(db_comment='Fecha del dato')
    precio_minimo = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Mínimo')
    precio_maximo = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Máximo')
    precio_promedio = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Promedio')
    unidad = models.CharField(max_length=20, db_comment='Unidad del dato, ej. kg, cubeta')
    fuente_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Enlace')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "compras", tabla "precio_mercado" (las comillas separan esquema y tabla)
        db_table = 'compras"."precio_mercado'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Precio de referencia de un producto en un mercado (SIPSA-DANE, Corabastos, Fenavi), usado por el agente analista.'


# ==============================================================================================================
# Tabla compras.documento_soporte  ·  por finca (seguridad por filas)  ·  API: /api/v1/compras/documentos-soporte/
# ==============================================================================================================
class DocumentoSoporte(models.Model):
    """Documento soporte electrónico de la DIAN para compras a quien no factura (campesinos, permutas)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proveedor = models.ForeignKey('terceros.Proveedor', models.DO_NOTHING, db_column='proveedor_id', related_name='+', db_constraint=False, db_comment='Vendedor')
    orden_compra = models.ForeignKey('compras.OrdenCompra', models.DO_NOTHING, db_column='orden_compra_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Orden de compra, si existe')
    prefijo = models.CharField(max_length=6, db_comment='Prefijo autorizado')
    numero = models.IntegerField(db_comment='Número')
    fecha = models.DateField(db_comment='Fecha')
    descripcion = models.TextField(db_comment='Qué se compró')
    total = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    cuds = models.CharField(max_length=96, null=True, blank=True, db_comment='Código único del documento soporte')
    estado_dian = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('aceptado', 'aceptado'), ('rechazado', 'rechazado')], db_default='pendiente', db_comment='Respuesta de la DIAN')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "compras", tabla "documento_soporte" (las comillas separan esquema y tabla)
        db_table = 'compras"."documento_soporte'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Documento soporte electrónico de la DIAN para compras a quien no factura (campesinos, permutas).'
