"""Modelos del esquema comercial: Precios con vigencia, propuestas de precio, pedidos, facturas, pagos y entregas.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «comercial». Django usa estas clases para leer y escribir
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
# Tabla comercial.lista_precios  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/listas-precios/
# ==============================================================================================================
class ListaPrecios(models.Model):
    """Lista de precios por canal o tipo de cliente (público, tiendas, restaurantes, mayoristas)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. PUBLICO, TIENDAS')
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "lista_precios" (las comillas separan esquema y tabla)
        db_table = 'comercial"."lista_precios'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Lista de precios por canal o tipo de cliente (público, tiendas, restaurantes, mayoristas).'


# ==============================================================================================================
# Tabla comercial.precio_producto  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/precios-producto/
# ==============================================================================================================
class PrecioProducto(models.Model):
    """Precio de un producto en una lista, con vigencia. Nunca se edita un precio: se cierra el vigente y se crea uno nuevo, así el historial queda completo."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lista_precios = models.ForeignKey('comercial.ListaPrecios', models.DO_NOTHING, db_column='lista_precios_id', related_name='+', db_constraint=False, db_comment='Lista')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio por unidad de venta')
    incluye_iva = models.BooleanField(db_default=True, db_comment='Si el precio ya incluye IVA')
    vigente_desde = models.DateTimeField(db_comment='Desde cuándo aplica')
    vigente_hasta = models.DateTimeField(null=True, blank=True, db_comment='Hasta cuándo; vacío = vigente')
    propuesta_precio = models.ForeignKey('comercial.PropuestaPrecio', models.DO_NOTHING, db_column='propuesta_precio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Propuesta que lo originó, si vino de un agente')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, db_comment='Administrador que lo autorizó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "precio_producto" (las comillas separan esquema y tabla)
        db_table = 'comercial"."precio_producto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Precio de un producto en una lista, con vigencia. Nunca se edita un precio: se cierra el vigente y se crea uno nuevo, así el historial queda completo.'


# ==============================================================================================================
# Tabla comercial.propuesta_precio  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/propuestas-precio/
# ==============================================================================================================
class PropuestaPrecio(models.Model):
    """Cambio de precio sugerido por el agente analista de mercados. Solo se aplica cuando el administrador lo aprueba."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    lista_precios = models.ForeignKey('comercial.ListaPrecios', models.DO_NOTHING, db_column='lista_precios_id', related_name='+', db_constraint=False, db_comment='Lista afectada')
    precio_actual = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio vigente al proponer')
    precio_propuesto = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio sugerido')
    variacion_pct = models.DecimalField(max_digits=6, decimal_places=2, db_comment='Variación porcentual')
    justificacion = models.TextField(db_comment='Razones en lenguaje claro')
    evidencia = models.JSONField(db_comment='Fuentes consultadas (SIPSA, competidores, costos) con fecha y enlace')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente que la generó')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('aprobada', 'aprobada'), ('rechazada', 'rechazada'), ('vencida', 'vencida'), ('aplicada', 'aplicada')], db_default='pendiente', db_comment='Situación')
    vence_en = models.DateTimeField(db_comment='Si nadie la revisa antes, queda vencida')
    revisado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='revisado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Administrador que decidió')
    revisado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo decidió')
    comentario_revision = models.TextField(null=True, blank=True, db_comment='Motivo de la decisión')
    aplicada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo entró en vigencia')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "propuesta_precio" (las comillas separan esquema y tabla)
        db_table = 'comercial"."propuesta_precio'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cambio de precio sugerido por el agente analista de mercados. Solo se aplica cuando el administrador lo aprueba.'


# ==============================================================================================================
# Tabla comercial.pedido  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/pedidos/
# ==============================================================================================================
class Pedido(models.Model):
    """Solicitud de compra de un cliente por cualquier canal; puede crearla una persona o un agente."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    numero = models.CharField(max_length=20, db_comment='Consecutivo, ej. PED-000123')
    cliente = models.ForeignKey('terceros.Cliente', models.DO_NOTHING, db_column='cliente_id', related_name='+', db_constraint=False, db_comment='Cliente')
    canal = models.CharField(max_length=17, choices=[('whatsapp', 'whatsapp'), ('web', 'web'), ('redes', 'redes'), ('telefono', 'telefono'), ('finca', 'finca'), ('mercado_campesino', 'mercado_campesino')], db_comment='Canal')
    estado = models.CharField(max_length=14, choices=[('borrador', 'borrador'), ('confirmado', 'confirmado'), ('en_preparacion', 'en_preparacion'), ('despachado', 'despachado'), ('entregado', 'entregado'), ('cancelado', 'cancelado')], db_default='borrador', db_comment='Situación')
    forma_pago = models.CharField(max_length=7, choices=[('contado', 'contado'), ('credito', 'credito')], db_default='contado', db_comment='Crédito exige la función venta_credito activa, cliente sin mora y cupo disponible')
    pedido_recurrente = models.ForeignKey('comercial.PedidoRecurrente', models.DO_NOTHING, db_column='pedido_recurrente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Pedido recurrente que lo generó, si aplica')
    fecha_entrega_programada = models.DateField(null=True, blank=True, db_comment='Día de entrega acordado')
    direccion_entrega = models.CharField(max_length=200, null=True, blank=True, db_comment='Dirección de entrega')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Suma de líneas sin impuestos')
    descuento = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Descuentos')
    impuestos = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='IVA')
    valor_domicilio = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Cobro de entrega')
    total = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Total a pagar')
    conversacion_ref = models.CharField(max_length=24, null=True, blank=True, db_comment='Id de la conversación en MongoDB que originó el pedido')
    creado_por_agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='creado_por_agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente que lo tomó, si aplica')
    vendedor = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='vendedor_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona responsable')
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
        # Nombre real en PostgreSQL: esquema "comercial", tabla "pedido" (las comillas separan esquema y tabla)
        db_table = 'comercial"."pedido'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Solicitud de compra de un cliente por cualquier canal; puede crearla una persona o un agente.'


# ==============================================================================================================
# Tabla comercial.pedido_detalle  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/pedidos/{id}/lineas/
# ==============================================================================================================
class PedidoDetalle(models.Model):
    """Línea del pedido. El precio queda congelado al confirmar: un cambio de precio posterior no la afecta."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    pedido = models.ForeignKey('comercial.Pedido', models.DO_NOTHING, db_column='pedido_id', related_name='+', db_constraint=False, db_comment='Pedido')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad (los lotes reservados quedan en comercial.reserva_lote)')
    precio_producto = models.ForeignKey('comercial.PrecioProducto', models.DO_NOTHING, db_column='precio_producto_id', related_name='+', db_constraint=False, db_comment='Precio vigente usado')
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Precio copiado (congelado) al confirmar')
    descuento = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Descuento de la línea')
    tarifa_iva = models.DecimalField(max_digits=5, decimal_places=2, db_default=0, db_comment='IVA aplicado')
    total_linea = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Total de la línea')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "pedido_detalle" (las comillas separan esquema y tabla)
        db_table = 'comercial"."pedido_detalle'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Línea del pedido. El precio queda congelado al confirmar: un cambio de precio posterior no la afecta.'


# ==============================================================================================================
# Tabla comercial.factura  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/facturas/
# ==============================================================================================================
class Factura(models.Model):
    """Factura electrónica (o documento equivalente) generada por regla fija, no por la IA, y validada por la DIAN."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    prefijo = models.CharField(max_length=6, db_comment='Prefijo autorizado por la DIAN')
    numero = models.IntegerField(db_comment='Número dentro del rango autorizado')
    pedido = models.ForeignKey('comercial.Pedido', models.DO_NOTHING, db_column='pedido_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Pedido facturado')
    cliente = models.ForeignKey('terceros.Cliente', models.DO_NOTHING, db_column='cliente_id', related_name='+', db_constraint=False, db_comment='Cliente')
    fecha_emision = models.DateTimeField(db_comment='Fecha y hora de emisión')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Base')
    iva = models.DecimalField(max_digits=14, decimal_places=2, db_comment='IVA')
    total = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Total')
    forma_pago = models.CharField(max_length=7, choices=[('contado', 'contado'), ('credito', 'credito')], db_comment='Forma de pago')
    fecha_vencimiento = models.DateField(null=True, blank=True, db_comment='Fecha límite de pago (crédito): emisión más los días de plazo del cliente')
    saldo = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Lo que falta por pagar; lo mantienen los pagos confirmados y las permutas')
    cufe = models.CharField(max_length=96, null=True, blank=True, db_comment='Código único de factura electrónica')
    estado_dian = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('aceptada', 'aceptada'), ('rechazada', 'rechazada'), ('no_aplica', 'no_aplica')], db_default='pendiente', db_comment='Respuesta de la DIAN')
    xml_url = models.CharField(max_length=300, null=True, blank=True, db_comment='XML en el almacén de archivos')
    pdf_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Representación gráfica')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "factura" (las comillas separan esquema y tabla)
        db_table = 'comercial"."factura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Factura electrónica (o documento equivalente) generada por regla fija, no por la IA, y validada por la DIAN.'


# ==============================================================================================================
# Tabla comercial.pago  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/pagos/
# ==============================================================================================================
class Pago(models.Model):
    """Dinero recibido por un pedido o factura."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    pedido = models.ForeignKey('comercial.Pedido', models.DO_NOTHING, db_column='pedido_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Pedido')
    factura = models.ForeignKey('comercial.Factura', models.DO_NOTHING, db_column='factura_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Factura')
    fecha = models.DateTimeField(db_comment='Momento del pago')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    medio = models.CharField(max_length=20, choices=[('efectivo', 'efectivo'), ('nequi', 'nequi'), ('daviplata', 'daviplata'), ('transferencia', 'transferencia'), ('tarjeta', 'tarjeta'), ('bre_b', 'bre_b'), ('pasarela', 'pasarela'), ('compensacion_permuta', 'compensacion_permuta')], db_comment='Medio de pago; compensacion_permuta = saldado con una permuta')
    proveedor_pasarela = models.CharField(max_length=12, choices=[('wompi', 'wompi'), ('mercado_pago', 'mercado_pago'), ('epayco', 'epayco'), ('payu', 'payu')], null=True, blank=True, db_comment='Pasarela de pago local, si medio = pasarela (Stripe no opera en Colombia)')
    id_transaccion_pasarela = models.CharField(max_length=80, null=True, blank=True, db_comment='Id de la transacción en la pasarela (llave de idempotencia del webhook)')
    referencia = models.CharField(max_length=60, null=True, blank=True, db_comment='Número de transacción')
    estado = models.CharField(max_length=10, choices=[('pendiente', 'pendiente'), ('confirmado', 'confirmado'), ('reversado', 'reversado')], db_default='pendiente', db_comment='Situación')
    confirmado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='confirmado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién verificó el ingreso (un agente nunca confirma pagos)')
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
        # Nombre real en PostgreSQL: esquema "comercial", tabla "pago" (las comillas separan esquema y tabla)
        db_table = 'comercial"."pago'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Dinero recibido por un pedido o factura.'


# ==============================================================================================================
# Tabla comercial.entrega  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/entregas/
# ==============================================================================================================
class Entrega(models.Model):
    """Despacho de un pedido."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    pedido = models.ForeignKey('comercial.Pedido', models.DO_NOTHING, db_column='pedido_id', related_name='+', db_constraint=False, db_comment='Pedido')
    fecha_salida = models.DateTimeField(null=True, blank=True, db_comment='Salida de la finca')
    fecha_entrega = models.DateTimeField(null=True, blank=True, db_comment='Recepción por el cliente')
    responsable = models.CharField(max_length=120, null=True, blank=True, db_comment='Quien entrega')
    vehiculo = models.ForeignKey('inventario.Vehiculo', models.DO_NOTHING, db_column='vehiculo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Vehículo usado (su registrador de temperatura vigila la cadena de frío en ruta)')
    estado = models.CharField(max_length=10, choices=[('programada', 'programada'), ('en_ruta', 'en_ruta'), ('entregada', 'entregada'), ('fallida', 'fallida')], db_default='programada', db_comment='Situación')
    evidencia_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Foto o firma')
    calificacion_cliente = models.SmallIntegerField(null=True, blank=True, db_comment='De 1 a 5')
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
        # Nombre real en PostgreSQL: esquema "comercial", tabla "entrega" (las comillas separan esquema y tabla)
        db_table = 'comercial"."entrega'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Despacho de un pedido.'


# ==============================================================================================================
# Tabla comercial.reserva_lote  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/reservas-lote/
# ==============================================================================================================
class ReservaLote(models.Model):
    """Qué lotes se reservaron para cada línea de pedido, escogidos en orden FEFO; una línea puede tomar de varios lotes."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    pedido_detalle = models.ForeignKey('comercial.PedidoDetalle', models.DO_NOTHING, db_column='pedido_detalle_id', related_name='+', db_constraint=False, db_comment='Línea del pedido')
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, db_comment='Lote reservado')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad tomada de ese lote')
    estado = models.CharField(max_length=10, choices=[('reservada', 'reservada'), ('despachada', 'despachada'), ('liberada', 'liberada')], db_default='reservada', db_comment='Situación')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "reserva_lote" (las comillas separan esquema y tabla)
        db_table = 'comercial"."reserva_lote'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Qué lotes se reservaron para cada línea de pedido, escogidos en orden FEFO; una línea puede tomar de varios lotes.'


# ==============================================================================================================
# Tabla comercial.retiro_lote  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/retiros-lote/
# ==============================================================================================================
class RetiroLote(models.Model):
    """Retiro de un lote del mercado (recall): se bloquea el lote y se avisa a cada cliente que lo recibió."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, db_comment='Lote retirado')
    motivo = models.TextField(db_comment='Problema sanitario o de calidad')
    estado = models.CharField(max_length=17, choices=[('abierto', 'abierto'), ('clientes_avisados', 'clientes_avisados'), ('cerrado', 'cerrado')], db_default='abierto', db_comment='Situación')
    abierto_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='abierto_por', related_name='+', db_constraint=False, db_comment='Quién lo abrió')
    cerrado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se cerró')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "retiro_lote" (las comillas separan esquema y tabla)
        db_table = 'comercial"."retiro_lote'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Retiro de un lote del mercado (recall): se bloquea el lote y se avisa a cada cliente que lo recibió.'


# ==============================================================================================================
# Tabla comercial.retiro_aviso  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/retiros-aviso/
# ==============================================================================================================
class RetiroAviso(models.Model):
    """Cliente que recibió un lote retirado: cuánto recibió, cuándo se le avisó y cuánto devolvió."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    retiro_lote = models.ForeignKey('comercial.RetiroLote', models.DO_NOTHING, db_column='retiro_lote_id', related_name='+', db_constraint=False, db_comment='Retiro')
    cliente = models.ForeignKey('terceros.Cliente', models.DO_NOTHING, db_column='cliente_id', related_name='+', db_constraint=False, db_comment='Cliente')
    pedido = models.ForeignKey('comercial.Pedido', models.DO_NOTHING, db_column='pedido_id', related_name='+', db_constraint=False, db_comment='Pedido en que lo recibió')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad recibida de ese lote')
    avisado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se le avisó')
    medio_aviso = models.CharField(max_length=8, choices=[('whatsapp', 'whatsapp'), ('llamada', 'llamada'), ('visita', 'visita'), ('correo', 'correo')], null=True, blank=True, db_comment='Cómo')
    cantidad_devuelta = models.DecimalField(max_digits=12, decimal_places=2, db_default=0, db_comment='Lo que devolvió')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "retiro_aviso" (las comillas separan esquema y tabla)
        db_table = 'comercial"."retiro_aviso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cliente que recibió un lote retirado: cuánto recibió, cuándo se le avisó y cuánto devolvió.'


# ==============================================================================================================
# Tabla comercial.pedido_recurrente  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/pedidos-recurrente/
# ==============================================================================================================
class PedidoRecurrente(models.Model):
    """Pedido que se repite (tienda, restaurante, hotel); cada día la tarea crea en borrador los que tocan para que un vendedor los confirme."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    cliente = models.ForeignKey('terceros.Cliente', models.DO_NOTHING, db_column='cliente_id', related_name='+', db_constraint=False, db_comment='Cliente')
    frecuencia = models.CharField(max_length=9, choices=[('semanal', 'semanal'), ('quincenal', 'quincenal'), ('mensual', 'mensual')], db_comment='Cada cuánto')
    proxima_fecha = models.DateField(db_comment='Próxima entrega')
    canal = models.CharField(max_length=17, choices=[('whatsapp', 'whatsapp'), ('web', 'web'), ('redes', 'redes'), ('telefono', 'telefono'), ('finca', 'finca'), ('mercado_campesino', 'mercado_campesino')], db_default='whatsapp', db_comment='Canal con que se registra el pedido')
    forma_pago = models.CharField(max_length=7, choices=[('contado', 'contado'), ('credito', 'credito')], db_default='contado', db_comment='Forma de pago de los pedidos generados')
    activo = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "pedido_recurrente" (las comillas separan esquema y tabla)
        db_table = 'comercial"."pedido_recurrente'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Pedido que se repite (tienda, restaurante, hotel); cada día la tarea crea en borrador los que tocan para que un vendedor los confirme.'


# ==============================================================================================================
# Tabla comercial.pedido_recurrente_detalle  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/pedidos-recurrente-detalle/
# ==============================================================================================================
class PedidoRecurrenteDetalle(models.Model):
    """Productos y cantidades del pedido recurrente."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    pedido_recurrente = models.ForeignKey('comercial.PedidoRecurrente', models.DO_NOTHING, db_column='pedido_recurrente_id', related_name='+', db_constraint=False, db_comment='Pedido recurrente')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "pedido_recurrente_detalle" (las comillas separan esquema y tabla)
        db_table = 'comercial"."pedido_recurrente_detalle'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Productos y cantidades del pedido recurrente.'


# ==============================================================================================================
# Tabla comercial.permuta  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/permutas/
# ==============================================================================================================
class Permuta(models.Model):
    """Trueque formal: una venta (factura) y una compra (documento soporte) que se compensan; requiere la función permuta activa. El pago con mano de obra no se admite."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    factura = models.ForeignKey('comercial.Factura', models.DO_NOTHING, db_column='factura_id', related_name='+', db_constraint=False, db_comment='Venta')
    documento_soporte = models.ForeignKey('compras.DocumentoSoporte', models.DO_NOTHING, db_column='documento_soporte_id', related_name='+', db_constraint=False, db_comment='Compra')
    valor_compensado = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor que se cruza')
    acuerdo = models.TextField(db_comment='Qué se intercambió y cómo se valoró')
    registrado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='registrado_por', related_name='+', db_constraint=False, db_comment='Quién la registró')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "permuta" (las comillas separan esquema y tabla)
        db_table = 'comercial"."permuta'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Trueque formal: una venta (factura) y una compra (documento soporte) que se compensan; requiere la función permuta activa. El pago con mano de obra no se admite.'


# ==============================================================================================================
# Tabla comercial.huella_trazabilidad  ·  por finca (seguridad por filas)  ·  API: /api/v1/comercial/huellas-trazabilidad/
# ==============================================================================================================
class HuellaTrazabilidad(models.Model):
    """Cadena de huellas SHA-256 de los hechos de trazabilidad de los lotes: cada huella incluye la anterior, así cualquier alteración se detecta. Lista para anclarse en una red blockchain si un comprador lo exige."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, db_comment='Lote')
    hecho = models.CharField(max_length=11, choices=[('lote_creado', 'lote_creado'), ('despachado', 'despachado'), ('bloqueado', 'bloqueado'), ('liberado', 'liberado'), ('descartado', 'descartado'), ('retirado', 'retirado')], db_comment='Hecho registrado')
    contenido = models.JSONField(db_comment='Datos del hecho (lote, fechas, cliente, pedido)')
    hash_anterior = models.CharField(max_length=64, null=True, blank=True, db_comment='Huella anterior de la cadena de la finca')
    hash = models.CharField(max_length=64, db_comment='SHA-256 de la huella anterior más el contenido')
    anclaje_red = models.CharField(max_length=40, null=True, blank=True, db_comment='Red externa donde se ancló (vacío = no anclada)')
    anclaje_transaccion = models.CharField(max_length=120, null=True, blank=True, db_comment='Id de la transacción de anclaje')
    anclado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "comercial", tabla "huella_trazabilidad" (las comillas separan esquema y tabla)
        db_table = 'comercial"."huella_trazabilidad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cadena de huellas SHA-256 de los hechos de trazabilidad de los lotes: cada huella incluye la anterior, así cualquier alteración se detecta. Lista para anclarse en una red blockchain si un comprador lo exige.'
