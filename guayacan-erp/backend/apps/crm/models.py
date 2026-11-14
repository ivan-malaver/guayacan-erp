"""Modelos del esquema crm: Posibles clientes (personas y empresas), formularios de captura con autorización de datos, campañas, interacciones y oportunidades.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «crm». Django usa estas clases para leer y escribir
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
# Tabla crm.segmento  ·  por finca (seguridad por filas)  ·  API: /api/v1/crm/segmentos/
# ==============================================================================================================
class Segmento(models.Model):
    """Segmento de mercado (hogares, tiendas, restaurantes, hoteles, colegios, exportadores) con sus criterios: base de la palanca de mercadeo."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    criterios = models.JSONField(null=True, blank=True, db_comment='Criterios (municipio, tipo de negocio, volumen)')
    propuesta_valor = models.TextField(null=True, blank=True, db_comment='Qué se le ofrece y por qué paga más')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "crm", tabla "segmento" (las comillas separan esquema y tabla)
        db_table = 'crm"."segmento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Segmento de mercado (hogares, tiendas, restaurantes, hoteles, colegios, exportadores) con sus criterios: base de la palanca de mercadeo.'


# ==============================================================================================================
# Tabla crm.campana  ·  por finca (seguridad por filas)  ·  API: /api/v1/crm/campanas/
# ==============================================================================================================
class Campana(models.Model):
    """Campaña para captar clientes: canal, segmento, presupuesto, costo real y conversiones (costo por cliente nuevo)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=150, db_comment='Nombre')
    canal = models.CharField(max_length=17, choices=[('whatsapp', 'whatsapp'), ('instagram', 'instagram'), ('facebook', 'facebook'), ('tiktok', 'tiktok'), ('feria', 'feria'), ('mercado_campesino', 'mercado_campesino'), ('visita_finca', 'visita_finca'), ('referidos', 'referidos'), ('web', 'web'), ('volanteo', 'volanteo'), ('otro', 'otro')], db_comment='Canal')
    segmento = models.ForeignKey('crm.Segmento', models.DO_NOTHING, db_column='segmento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Segmento')
    objetivo = models.TextField(null=True, blank=True, db_comment='Objetivo')
    desde = models.DateField(db_comment='Inicio')
    hasta = models.DateField(null=True, blank=True, db_comment='Fin')
    presupuesto = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Presupuesto')
    costo_real = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Costo real')
    publicacion = models.ForeignKey('redes.Publicacion', models.DO_NOTHING, db_column='publicacion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Publicación de redes asociada')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "crm", tabla "campana" (las comillas separan esquema y tabla)
        db_table = 'crm"."campana'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Campaña para captar clientes: canal, segmento, presupuesto, costo real y conversiones (costo por cliente nuevo).'


# ==============================================================================================================
# Tabla crm.formulario_captura  ·  por finca (seguridad por filas)  ·  API: /api/v1/crm/formularios-captura/
# ==============================================================================================================
class FormularioCaptura(models.Model):
    """Formulario para registrar posibles clientes (web, QR en ferias, WhatsApp) con su texto de autorización de datos y finalidad."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    canal = models.CharField(max_length=12, choices=[('web', 'web'), ('qr_feria', 'qr_feria'), ('whatsapp', 'whatsapp'), ('tablet_finca', 'tablet_finca'), ('otro', 'otro')], db_comment='Dónde se usa')
    campos = models.JSONField(db_comment='Campos que pide (mínimos necesarios)')
    texto_autorizacion = models.TextField(db_comment='Texto de autorización de tratamiento de datos (Ley 1581)')
    finalidad = models.TextField(db_comment='Para qué se usarán los datos')
    campana = models.ForeignKey('crm.Campana', models.DO_NOTHING, db_column='campana_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Campaña')
    activo = models.BooleanField(db_default=True, db_comment='Publicado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "crm", tabla "formulario_captura" (las comillas separan esquema y tabla)
        db_table = 'crm"."formulario_captura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Formulario para registrar posibles clientes (web, QR en ferias, WhatsApp) con su texto de autorización de datos y finalidad.'


# ==============================================================================================================
# Tabla crm.prospecto  ·  por finca (seguridad por filas)  ·  API: /api/v1/crm/prospectos/
# ==============================================================================================================
class Prospecto(models.Model):
    """Posible cliente, persona o empresa. No se le escribe sin autorización; al comprar se convierte en tercero y cliente."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=7, choices=[('persona', 'persona'), ('empresa', 'empresa')], db_comment='Tipo')
    nombre = models.CharField(max_length=150, db_comment='Nombre o razón social')
    nit = models.CharField(max_length=20, null=True, blank=True, db_comment='NIT de la empresa (las personas no necesitan documento para ser prospecto)')
    sector = models.CharField(max_length=15, choices=[('hogar', 'hogar'), ('tienda', 'tienda'), ('restaurante', 'restaurante'), ('hotel', 'hotel'), ('colegio', 'colegio'), ('casino', 'casino'), ('supermercado', 'supermercado'), ('distribuidor', 'distribuidor'), ('exportador', 'exportador'), ('agencia_turismo', 'agencia_turismo'), ('institucion', 'institucion'), ('otro', 'otro')], db_comment='Sector')
    municipio = models.CharField(max_length=80, null=True, blank=True, db_comment='Municipio')
    telefono = models.CharField(max_length=20, null=True, blank=True, db_comment='Celular')
    correo = models.EmailField(max_length=254, null=True, blank=True, db_comment='Correo')
    canal_origen = models.CharField(max_length=17, choices=[('whatsapp', 'whatsapp'), ('instagram', 'instagram'), ('facebook', 'facebook'), ('tiktok', 'tiktok'), ('feria', 'feria'), ('mercado_campesino', 'mercado_campesino'), ('visita_finca', 'visita_finca'), ('referido', 'referido'), ('web', 'web'), ('llamada', 'llamada'), ('base_publica', 'base_publica'), ('otro', 'otro')], db_comment='Cómo llegó')
    formulario = models.ForeignKey('crm.FormularioCaptura', models.DO_NOTHING, db_column='formulario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Formulario por el que se registró')
    campana = models.ForeignKey('crm.Campana', models.DO_NOTHING, db_column='campana_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Campaña')
    segmento = models.ForeignKey('crm.Segmento', models.DO_NOTHING, db_column='segmento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Segmento')
    intereses = ArrayField(models.TextField(), null=True, blank=True, db_comment='Productos o servicios de interés')
    volumen_estimado_mes = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Compra mensual estimada')
    etapa = models.CharField(max_length=11, choices=[('nuevo', 'nuevo'), ('contactado', 'contactado'), ('calificado', 'calificado'), ('propuesta', 'propuesta'), ('negociacion', 'negociacion'), ('ganado', 'ganado'), ('perdido', 'perdido'), ('descartado', 'descartado')], db_default='nuevo', db_comment='Etapa del embudo')
    puntaje = models.SmallIntegerField(db_default=0, db_comment='Puntaje de calificación (0 a 100)')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Vendedor responsable')
    consentimiento = models.ForeignKey('terceros.ConsentimientoDatos', models.DO_NOTHING, db_column='consentimiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Autorización de datos; sin ella solo se guarda la empresa (datos públicos), no se contacta')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tercero al convertirse en cliente')
    motivo_perdida = models.CharField(max_length=200, null=True, blank=True, db_comment='Por qué se perdió')
    proximo_contacto = models.DateField(null=True, blank=True, db_comment='Próximo contacto')
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
        # Nombre real en PostgreSQL: esquema "crm", tabla "prospecto" (las comillas separan esquema y tabla)
        db_table = 'crm"."prospecto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Posible cliente, persona o empresa. No se le escribe sin autorización; al comprar se convierte en tercero y cliente.'


# ==============================================================================================================
# Tabla crm.contacto_empresa  ·  por finca (seguridad por filas)  ·  API: /api/v1/crm/contactos-empresa/
# ==============================================================================================================
class ContactoEmpresa(models.Model):
    """Persona de contacto dentro de una empresa prospecto (compras, chef, administrador), con su propia autorización."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    prospecto = models.ForeignKey('crm.Prospecto', models.DO_NOTHING, db_column='prospecto_id', related_name='+', db_constraint=False, db_comment='Empresa')
    nombre = models.CharField(max_length=150, db_comment='Nombre')
    cargo = models.CharField(max_length=80, null=True, blank=True, db_comment='Cargo')
    telefono = models.CharField(max_length=20, null=True, blank=True, db_comment='Celular')
    correo = models.EmailField(max_length=254, null=True, blank=True, db_comment='Correo')
    consentimiento = models.ForeignKey('terceros.ConsentimientoDatos', models.DO_NOTHING, db_column='consentimiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Autorización')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "crm", tabla "contacto_empresa" (las comillas separan esquema y tabla)
        db_table = 'crm"."contacto_empresa'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Persona de contacto dentro de una empresa prospecto (compras, chef, administrador), con su propia autorización.'


# ==============================================================================================================
# Tabla crm.interaccion  ·  por finca (seguridad por filas)  ·  API: /api/v1/crm/interacciones/
# ==============================================================================================================
class Interaccion(models.Model):
    """Contacto con un prospecto o cliente (llamada, WhatsApp, visita, degustación, feria) y su próximo paso."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    prospecto = models.ForeignKey('crm.Prospecto', models.DO_NOTHING, db_column='prospecto_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Prospecto')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cliente existente')
    tipo = models.CharField(max_length=12, choices=[('llamada', 'llamada'), ('whatsapp', 'whatsapp'), ('visita', 'visita'), ('correo', 'correo'), ('reunion', 'reunion'), ('degustacion', 'degustacion'), ('feria', 'feria'), ('visita_finca', 'visita_finca')], db_comment='Tipo')
    fecha = models.DateTimeField(db_comment='Cuándo')
    resumen = models.TextField(db_comment='Qué se habló')
    proximo_paso = models.CharField(max_length=200, null=True, blank=True, db_comment='Próximo paso')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente, si la atendió uno')
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
        # Nombre real en PostgreSQL: esquema "crm", tabla "interaccion" (las comillas separan esquema y tabla)
        db_table = 'crm"."interaccion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Contacto con un prospecto o cliente (llamada, WhatsApp, visita, degustación, feria) y su próximo paso.'


# ==============================================================================================================
# Tabla crm.oportunidad  ·  por finca (seguridad por filas)  ·  API: /api/v1/crm/oportunidades/
# ==============================================================================================================
class Oportunidad(models.Model):
    """Negocio posible con un prospecto o cliente: productos, valor, probabilidad y fecha de cierre (proyección del embudo)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    prospecto = models.ForeignKey('crm.Prospecto', models.DO_NOTHING, db_column='prospecto_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Prospecto')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cliente')
    titulo = models.CharField(max_length=150, db_comment='Título')
    productos = models.JSONField(null=True, blank=True, db_comment='Productos y cantidades')
    valor_estimado = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor estimado')
    probabilidad_pct = models.SmallIntegerField(db_comment='Probabilidad de cierre')
    cierre_estimado = models.DateField(null=True, blank=True, db_comment='Fecha estimada')
    estado = models.CharField(max_length=7, choices=[('abierta', 'abierta'), ('ganada', 'ganada'), ('perdida', 'perdida')], db_default='abierta', db_comment='Estado')
    pedido = models.ForeignKey('comercial.Pedido', models.DO_NOTHING, db_column='pedido_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Pedido que la cerró')
    linea_negocio = models.ForeignKey('estrategia.LineaNegocio', models.DO_NOTHING, db_column='linea_negocio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Línea de negocio')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "crm", tabla "oportunidad" (las comillas separan esquema y tabla)
        db_table = 'crm"."oportunidad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Negocio posible con un prospecto o cliente: productos, valor, probabilidad y fecha de cierre (proyección del embudo).'
