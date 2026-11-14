"""Modelos del esquema terceros: Personas y empresas con las que se relaciona la finca: clientes, proveedores, empleados y su consentimiento de datos.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «terceros». Django usa estas clases para leer y escribir
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
# Tabla terceros.tercero  ·  por finca (seguridad por filas)  ·  API: /api/v1/terceros/terceros/
# ==============================================================================================================
class Tercero(models.Model):
    """Toda persona natural o jurídica con la que se relaciona la finca. Un mismo tercero puede ser cliente, proveedor y empleado a la vez."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo_persona = models.CharField(max_length=8, choices=[('natural', 'natural'), ('juridica', 'juridica')], db_comment='Persona natural o empresa')
    tipo_documento = models.CharField(max_length=3, choices=[('CC', 'CC'), ('CE', 'CE'), ('NIT', 'NIT'), ('PAS', 'PAS'), ('TI', 'TI'), ('PPT', 'PPT')], null=True, blank=True, db_comment='Tipo de documento según la DIAN')
    numero_documento = models.CharField(max_length=20, null=True, blank=True, db_comment='Número de documento sin puntos')
    digito_verificacion = models.CharField(max_length=1, null=True, blank=True, db_comment='Dígito de verificación del NIT')
    nombres = models.CharField(max_length=120, null=True, blank=True, db_comment='Nombres (persona natural)')
    apellidos = models.CharField(max_length=120, null=True, blank=True, db_comment='Apellidos (persona natural)')
    razon_social = models.CharField(max_length=200, null=True, blank=True, db_comment='Nombre de la empresa (persona jurídica)')
    correo = models.EmailField(max_length=254, null=True, blank=True, db_comment='Correo de contacto')
    telefono = models.CharField(max_length=20, null=True, blank=True, db_comment='Teléfono')
    whatsapp = models.CharField(max_length=20, null=True, blank=True, db_comment='Número de WhatsApp en formato internacional')
    direccion = models.CharField(max_length=200, null=True, blank=True, db_comment='Dirección o indicación rural')
    codigo_dane_municipio = models.CharField(max_length=5, null=True, blank=True, db_comment='Municipio según DANE')
    es_cliente = models.BooleanField(db_default=False, db_comment='Marca rápida de rol')
    es_proveedor = models.BooleanField(db_default=False, db_comment='Marca rápida de rol')
    es_empleado = models.BooleanField(db_default=False, db_comment='Marca rápida de rol')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "terceros", tabla "tercero" (las comillas separan esquema y tabla)
        db_table = 'terceros"."tercero'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Toda persona natural o jurídica con la que se relaciona la finca. Un mismo tercero puede ser cliente, proveedor y empleado a la vez.'


# ==============================================================================================================
# Tabla terceros.consentimiento_datos  ·  por finca (seguridad por filas)  ·  API: /api/v1/terceros/consentimientos/
# ==============================================================================================================
class ConsentimientoDatos(models.Model):
    """Autorización de tratamiento de datos personales (Ley 1581 de 2012) por finalidad. Sin consentimiento vigente los agentes no personalizan ni envían publicidad."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Titular de los datos')
    finalidad = models.CharField(max_length=23, choices=[('atencion_pedidos', 'atencion_pedidos'), ('publicidad', 'publicidad'), ('personalizacion_ofertas', 'personalizacion_ofertas'), ('analitica', 'analitica'), ('imagen_redes', 'imagen_redes'), ('biometria_acceso', 'biometria_acceso')], db_comment='Para qué se autoriza el uso')
    version_politica = models.CharField(max_length=20, db_comment='Versión de la política de tratamiento aceptada')
    otorgado = models.BooleanField(db_comment='Verdadero si autorizó, falso si negó')
    medio = models.CharField(max_length=17, choices=[('whatsapp', 'whatsapp'), ('web', 'web'), ('formulario_fisico', 'formulario_fisico'), ('verbal_grabado', 'verbal_grabado'), ('correo', 'correo')], db_comment='Cómo se obtuvo')
    evidencia_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Ubicación de la prueba en el almacén de archivos')
    otorgado_en = models.DateTimeField(db_comment='Cuándo se dio la respuesta')
    revocado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo la retiró; vacío = vigente')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "terceros", tabla "consentimiento_datos" (las comillas separan esquema y tabla)
        db_table = 'terceros"."consentimiento_datos'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Autorización de tratamiento de datos personales (Ley 1581 de 2012) por finalidad. Sin consentimiento vigente los agentes no personalizan ni envían publicidad.'


# ==============================================================================================================
# Tabla terceros.cliente  ·  por finca (seguridad por filas)  ·  API: /api/v1/terceros/clientes/
# ==============================================================================================================
class Cliente(models.Model):
    """Datos comerciales del tercero que compra."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Tercero')
    segmento = models.CharField(max_length=11, choices=[('hogar', 'hogar'), ('tienda', 'tienda'), ('restaurante', 'restaurante'), ('hotel', 'hotel'), ('asadero', 'asadero'), ('carniceria', 'carniceria'), ('mayorista', 'mayorista'), ('turista', 'turista'), ('otro', 'otro')], db_comment='Tipo de cliente (restaurante y hotel forman el canal HORECA)')
    canal_origen = models.CharField(max_length=17, choices=[('whatsapp', 'whatsapp'), ('web', 'web'), ('redes', 'redes'), ('referido', 'referido'), ('mercado_campesino', 'mercado_campesino'), ('finca', 'finca'), ('otro', 'otro')], null=True, blank=True, db_comment='Por dónde llegó')
    frecuencia_compra_dias = models.SmallIntegerField(null=True, blank=True, db_comment='Cada cuántos días suele comprar (calculado)')
    fecha_primera_compra = models.DateField(null=True, blank=True, db_comment='Primera compra')
    cupo_credito = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Monto máximo de cartera abierta (solo aplica si la función venta_credito está activa)')
    dias_plazo = models.SmallIntegerField(db_default=0, db_comment='Días de plazo para pagar una factura a crédito')
    bloqueado_por_mora = models.BooleanField(db_default=False, db_comment='Si tiene facturas vencidas sin pagar no puede comprar a crédito')
    lista_precios = models.ForeignKey('comercial.ListaPrecios', models.DO_NOTHING, db_column='lista_precios_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Lista de precios que le aplica')
    perfil_interes_ref = models.CharField(max_length=24, null=True, blank=True, db_comment='Id del documento en MongoDB perfiles_interes')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "terceros", tabla "cliente" (las comillas separan esquema y tabla)
        db_table = 'terceros"."cliente'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Datos comerciales del tercero que compra.'


# ==============================================================================================================
# Tabla terceros.proveedor  ·  por finca (seguridad por filas)  ·  API: /api/v1/terceros/proveedores/
# ==============================================================================================================
class Proveedor(models.Model):
    """Datos de compra del tercero que vende insumos o servicios."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Tercero')
    categoria = models.CharField(max_length=12, choices=[('concentrado', 'concentrado'), ('animales', 'animales'), ('semillas', 'semillas'), ('medicamentos', 'medicamentos'), ('materiales', 'materiales'), ('servicios', 'servicios'), ('transporte', 'transporte'), ('otro', 'otro')], db_comment='Qué suministra')
    dias_credito = models.SmallIntegerField(db_default=0, db_comment='Días de plazo que concede')
    calificacion = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, db_comment='Calificación de 1 a 5 (precio, puntualidad, calidad)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "terceros", tabla "proveedor" (las comillas separan esquema y tabla)
        db_table = 'terceros"."proveedor'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Datos de compra del tercero que vende insumos o servicios.'


# ==============================================================================================================
# Tabla terceros.empleado  ·  por finca (seguridad por filas)  ·  API: /api/v1/terceros/empleados/
# ==============================================================================================================
class Empleado(models.Model):
    """Persona que trabaja en la finca, con su forma de vinculación."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Tercero')
    cargo = models.CharField(max_length=80, db_comment='Cargo, ej. operario de granja')
    tipo_vinculacion = models.CharField(max_length=20, choices=[('termino_fijo', 'termino_fijo'), ('termino_indefinido', 'termino_indefinido'), ('jornal', 'jornal'), ('prestacion_servicios', 'prestacion_servicios'), ('aprendiz', 'aprendiz')], db_comment='Tipo de contrato')
    salario_base = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Salario mensual o valor del jornal')
    forma_pago = models.CharField(max_length=7, choices=[('salario', 'salario'), ('jornal', 'jornal'), ('destajo', 'destajo'), ('mixto', 'mixto')], db_default='salario', db_comment='Cómo se le paga; el salario fijo nunca depende de tareas aprobadas')
    valor_jornal = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Valor del jornal, si se le paga por día')
    ruta_aprendizaje = models.CharField(max_length=60, null=True, blank=True, db_comment='Ruta de formación por cargo, ej. operario_galpon')
    fecha_ingreso = models.DateField(db_comment='Inicio')
    fecha_retiro = models.DateField(null=True, blank=True, db_comment='Fin; vacío = activo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "terceros", tabla "empleado" (las comillas separan esquema y tabla)
        db_table = 'terceros"."empleado'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Persona que trabaja en la finca, con su forma de vinculación.'
