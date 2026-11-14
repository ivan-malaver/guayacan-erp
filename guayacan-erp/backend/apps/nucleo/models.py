"""Modelos del esquema nucleo: Usuarios, roles, permisos, parámetros con vigencia, auditoría, predio y zonas, eventos de integración.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «nucleo». Django usa estas clases para leer y escribir
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


# El usuario se escribió a mano (apps/nucleo/usuario.py) porque Django necesita métodos especiales para
# iniciar sesión; aquí solo se importa para que Django lo encuentre como nucleo.Usuario.
from .usuario import Usuario, UsuarioManager  # noqa: E402,F401


# ==============================================================================================================
# Tabla nucleo.rol  ·  catálogo compartido entre fincas  ·  API: /api/v1/nucleo/roles/
# ==============================================================================================================
class Rol(models.Model):
    """Conjunto de permisos que se asigna a usuarios o agentes (administrador, operario de granja, contador, vendedor)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=40, unique=True, db_comment='Código corto en minúscula, ej. administrador, operario_granja')
    nombre = models.CharField(max_length=80, db_comment='Nombre visible del rol')
    descripcion = models.TextField(null=True, blank=True, db_comment='Qué puede hacer quien tiene este rol')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "rol" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."rol'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Conjunto de permisos que se asigna a usuarios o agentes (administrador, operario de granja, contador, vendedor).'


# ==============================================================================================================
# Tabla nucleo.permiso  ·  catálogo compartido entre fincas  ·  API: /api/v1/nucleo/permisos/
# ==============================================================================================================
class Permiso(models.Model):
    """Acción concreta que se puede autorizar, por módulo (ej. comercial.aprobar_precio)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=80, unique=True, db_comment='Código módulo.accion, ej. comercial.aprobar_precio')
    nombre = models.CharField(max_length=120, db_comment='Descripción corta de la acción')
    modulo = models.CharField(max_length=40, db_comment='Módulo al que pertenece (esquema)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "permiso" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."permiso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Acción concreta que se puede autorizar, por módulo (ej. comercial.aprobar_precio).'


# ==============================================================================================================
# Tabla nucleo.rol_permiso  ·  catálogo compartido entre fincas  ·  API: /api/v1/nucleo/roles/{id}/permisos/
# ==============================================================================================================
class RolPermiso(models.Model):
    """Qué permisos tiene cada rol (relación muchos a muchos)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    rol = models.ForeignKey('nucleo.Rol', models.DO_NOTHING, db_column='rol_id', related_name='+', db_constraint=False, db_comment='Rol')
    permiso = models.ForeignKey('nucleo.Permiso', models.DO_NOTHING, db_column='permiso_id', related_name='+', db_constraint=False, db_comment='Permiso concedido al rol')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "rol_permiso" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."rol_permiso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Qué permisos tiene cada rol (relación muchos a muchos).'


# ==============================================================================================================
# Tabla nucleo.usuario_rol  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/usuarios/{id}/roles/
# ==============================================================================================================
class UsuarioRol(models.Model):
    """Qué roles tiene cada usuario en cada finca (un usuario puede trabajar en varias fincas con roles distintos)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, db_comment='Usuario')
    rol = models.ForeignKey('nucleo.Rol', models.DO_NOTHING, db_column='rol_id', related_name='+', db_constraint=False, db_comment='Rol asignado')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "usuario_rol" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."usuario_rol'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Qué roles tiene cada usuario en cada finca (un usuario puede trabajar en varias fincas con roles distintos).'


# ==============================================================================================================
# Tabla nucleo.parametro  ·  catálogo compartido entre fincas  ·  API: /api/v1/nucleo/parametros/
# ==============================================================================================================
class Parametro(models.Model):
    """Valores de negocio que cambian con el tiempo (IVA, salario mínimo, tarifa de domicilio, margen mínimo). Nunca van fijos en el código."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Vacío = parámetro nacional (vale para todas las fincas); con valor = solo para esa finca
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Vacío = parámetro nacional')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    clave = models.CharField(max_length=80, db_comment='Nombre del parámetro, ej. salario_minimo, iva_general, margen_minimo_huevo')
    valor = models.TextField(db_comment='Valor como texto; se interpreta según tipo_dato')
    tipo_dato = models.CharField(max_length=10, choices=[('entero', 'entero'), ('decimal', 'decimal'), ('porcentaje', 'porcentaje'), ('dinero', 'dinero'), ('texto', 'texto'), ('booleano', 'booleano'), ('json', 'json')], db_comment='Cómo interpretar el valor')
    vigente_desde = models.DateField(db_comment='Primer día en que aplica')
    vigente_hasta = models.DateField(null=True, blank=True, db_comment='Último día en que aplica; vacío = vigente hoy')
    descripcion = models.TextField(null=True, blank=True, db_comment='Para qué se usa y de dónde sale (norma, decreto, decisión)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "parametro" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."parametro'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Valores de negocio que cambian con el tiempo (IVA, salario mínimo, tarifa de domicilio, margen mínimo). Nunca van fijos en el código.'


# ==============================================================================================================
# Tabla nucleo.auditoria  ·  catálogo compartido entre fincas  ·  API: /api/v1/nucleo/auditoria/
# ==============================================================================================================
class Auditoria(models.Model):
    """Registro inalterable de cada cambio importante: quién (persona o agente), qué, cuándo y cómo estaba antes. Particionada por mes."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca en la que ocurrió el cambio auditado
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, null=True, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca en la que ocurrió el cambio')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    esquema_tabla = models.CharField(max_length=80, db_comment='Tabla afectada, ej. comercial.precio_producto')
    registro_id = models.BigIntegerField(db_comment='Id del registro afectado')
    accion = models.CharField(max_length=14, choices=[('crear', 'crear'), ('actualizar', 'actualizar'), ('eliminar', 'eliminar'), ('aprobar', 'aprobar'), ('rechazar', 'rechazar'), ('iniciar_sesion', 'iniciar_sesion'), ('exportar', 'exportar')], db_comment='Tipo de acción')
    datos_antes = models.JSONField(null=True, blank=True, db_comment='Valores antes del cambio')
    datos_despues = models.JSONField(null=True, blank=True, db_comment='Valores después del cambio')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona que hizo o aprobó la acción')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente de IA que la propuso o ejecutó, si aplica')
    direccion_ip = models.GenericIPAddressField(null=True, blank=True, db_comment='IP de origen')
    ocurrido_en = models.DateTimeField(db_default=Now(), db_comment='Momento exacto del cambio')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "auditoria" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."auditoria'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Registro inalterable de cada cambio importante: quién (persona o agente), qué, cuándo y cómo estaba antes. Particionada por mes.'


# ==============================================================================================================
# Tabla nucleo.evento_salida  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/eventos-salida/
# ==============================================================================================================
class EventoSalida(models.Model):
    """Bandeja de salida (patrón outbox): cada hecho de negocio se escribe aquí en la misma transacción y luego se publica a MongoDB, a los agentes y a otros servicios."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo_evento = models.CharField(max_length=80, db_comment='Nombre del hecho, ej. pedido.confirmado, precio.aprobado')
    entidad = models.CharField(max_length=80, db_comment='Tabla de origen')
    entidad_id = models.BigIntegerField(db_comment='Id del registro de origen')
    carga = models.JSONField(db_comment='Datos del evento')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('publicado', 'publicado'), ('fallido', 'fallido')], db_default='pendiente', db_comment='Si ya se entregó a los consumidores')
    intentos = models.SmallIntegerField(db_default=0, db_comment='Veces que se intentó publicar')
    publicado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se publicó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "evento_salida" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."evento_salida'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Bandeja de salida (patrón outbox): cada hecho de negocio se escribe aquí en la misma transacción y luego se publica a MongoDB, a los agentes y a otros servicios.'


# ==============================================================================================================
# Tabla nucleo.predio  ·  catálogo compartido entre fincas  ·  API: /api/v1/nucleo/predios/
# ==============================================================================================================
class Predio(models.Model):
    """Finca o terreno donde opera el sistema (permite replicarlo en otras fincas)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=120, db_comment='Nombre de la finca, ej. El Guayacán de los Malaver')
    matricula_inmobiliaria = models.CharField(max_length=40, null=True, blank=True, db_comment='Número de matrícula del certificado de tradición')
    propietario = models.CharField(max_length=150, null=True, blank=True, db_comment='Titular del predio según el certificado')
    tenencia = models.CharField(max_length=8, choices=[('propio', 'propio'), ('comodato', 'comodato'), ('arriendo', 'arriendo'), ('otro', 'otro')], db_comment='Cómo se usa el predio')
    area_m2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Área total en metros cuadrados')
    codigo_dane_municipio = models.CharField(max_length=5, null=True, blank=True, db_comment='Código DANE del municipio (Nilo = 25488)')
    vereda = models.CharField(max_length=80, null=True, blank=True, db_comment='Vereda')
    geometria = Geometria(tipo='MultiPolygon', srid=9377, null=True, blank=True, db_comment='Linderos en el sistema de coordenadas oficial CTM12 (EPSG 9377)')
    es_practica = models.BooleanField(db_default=False, db_comment='Finca de práctica para el modo aprendiz: datos de ejemplo aislados de la finca real')
    regimen_tributario = models.CharField(max_length=14, choices=[('por_definir', 'por_definir'), ('ordinario', 'ordinario'), ('simple', 'simple'), ('no_responsable', 'no_responsable')], db_default='por_definir', db_comment='Régimen del empleador (lo confirma el contador); define si la nómina electrónica es obligatoria')
    empleador_tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='empleador_tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona o empresa que figura como empleador')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "predio" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."predio'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Finca o terreno donde opera el sistema (permite replicarlo en otras fincas).'


# ==============================================================================================================
# Tabla nucleo.zona  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/zonas/
# ==============================================================================================================
class Zona(models.Model):
    """Área dentro del predio con un uso (galpón, aprisco, estanque, lote de cultivo, potrero, bodega, ronda hídrica)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código corto, ej. GAL-01, EST-02, LOT-C3')
    nombre = models.CharField(max_length=120, db_comment='Nombre descriptivo')
    tipo_zona = models.CharField(max_length=13, choices=[('galpon', 'galpon'), ('aprisco', 'aprisco'), ('estanque', 'estanque'), ('lote_cultivo', 'lote_cultivo'), ('potrero', 'potrero'), ('bodega', 'bodega'), ('vivienda', 'vivienda'), ('ronda_hidrica', 'ronda_hidrica'), ('apiario', 'apiario'), ('lombricultivo', 'lombricultivo'), ('biodigestor', 'biodigestor'), ('otra', 'otra')], db_comment='Uso de la zona')
    area_m2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Área en metros cuadrados')
    capacidad = models.IntegerField(null=True, blank=True, db_comment='Capacidad máxima (aves, animales, plantas o m³ según el tipo)')
    geometria = Geometria(tipo='Polygon', srid=9377, null=True, blank=True, db_comment='Polígono de la zona en CTM12')
    modelo_3d_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Modelo 3D de la zona en el almacén de archivos (gemelo digital, listo para cuando exista el levantamiento)')
    activa = models.BooleanField(db_default=True, db_comment='Si está en uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "zona" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."zona'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Área dentro del predio con un uso (galpón, aprisco, estanque, lote de cultivo, potrero, bodega, ronda hídrica).'


# ==============================================================================================================
# Tabla nucleo.dispositivo_captura  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/dispositivos-captura/
# ==============================================================================================================
class DispositivoCaptura(models.Model):
    """Equipo con el que se capturan datos: celulares con la app, lectores de código de barras, básculas e impresoras de etiquetas."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código, ej. CEL-SAMID, BAS-01, LEC-01')
    tipo = models.CharField(max_length=19, choices=[('celular', 'celular'), ('tableta', 'tableta'), ('lector_codigo', 'lector_codigo'), ('bascula', 'bascula'), ('impresora_etiquetas', 'impresora_etiquetas')], db_comment='Tipo de equipo')
    conexion = models.CharField(max_length=16, choices=[('camara', 'camara'), ('teclado_hid', 'teclado_hid'), ('bluetooth_ble', 'bluetooth_ble'), ('bluetooth_serial', 'bluetooth_serial'), ('usb', 'usb'), ('red_local', 'red_local')], db_comment='Cómo se conecta: teclado_hid = el lector escribe como un teclado; red_local = a través de la pasarela de la finca')
    marca_modelo = models.CharField(max_length=80, null=True, blank=True, db_comment='Marca y modelo')
    numero_serie = models.CharField(max_length=60, null=True, blank=True, db_comment='Serie del fabricante')
    capacidad_max_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, db_comment='Báscula: peso máximo')
    division_g = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, db_comment='Báscula: resolución en gramos')
    uso_comercial = models.BooleanField(db_default=False, db_comment='Báscula usada para vender por peso: sujeta a verificación metrológica de la SIC')
    ultima_verificacion = models.DateField(null=True, blank=True, db_comment='Fecha de la última verificación o calibración')
    proxima_verificacion = models.DateField(null=True, blank=True, db_comment='Fecha en que vence la verificación')
    certificado_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Certificado de verificación o calibración')
    usuario_asignado = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_asignado_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona a cargo (celulares)')
    activo = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "dispositivo_captura" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."dispositivo_captura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Equipo con el que se capturan datos: celulares con la app, lectores de código de barras, básculas e impresoras de etiquetas.'


# ==============================================================================================================
# Tabla nucleo.sincronizacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/sincronizaciones/
# ==============================================================================================================
class Sincronizacion(models.Model):
    """Cada sincronización de la app sin conexión: cuántos registros subió, cuántos se rechazaron y por qué."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    dispositivo_captura = models.ForeignKey('nucleo.DispositivoCaptura', models.DO_NOTHING, db_column='dispositivo_captura_id', related_name='+', db_constraint=False, db_comment='Celular o tableta que sincroniza')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, db_comment='Usuario que tenía la sesión')
    version_app = models.CharField(max_length=20, db_comment='Versión de la app')
    iniciada_en = models.DateTimeField(db_comment='Inicio')
    terminada_en = models.DateTimeField(null=True, blank=True, db_comment='Fin')
    registros_recibidos = models.IntegerField(db_default=0, db_comment='Registros que llegaron')
    registros_duplicados = models.IntegerField(db_default=0, db_comment='Ya existían (mismo id_cliente); se ignoran sin error')
    registros_rechazados = models.IntegerField(db_default=0, db_comment='No pasaron una regla (ej. dos personas registraron la postura del mismo lote y día)')
    detalle_rechazos = models.JSONField(null=True, blank=True, db_comment='Qué se rechazó y por qué, para resolverlo en la app')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "sincronizacion" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."sincronizacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cada sincronización de la app sin conexión: cuántos registros subió, cuántos se rechazaron y por qué.'


# ==============================================================================================================
# Tabla nucleo.funcionalidad  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/funcionalidades/
# ==============================================================================================================
class Funcionalidad(models.Model):
    """Interruptor de funciones por finca (feature flag): lo que aún no tiene equipo o decisión queda construido y apagado, y se enciende sin desplegar otra versión."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=40, db_comment='Código, ej. venta_credito, permuta, camara_termica, reconocimiento_facial')
    descripcion = models.TextField(db_comment='Qué habilita')
    fase = models.SmallIntegerField(db_comment='Fase del plan en que se prevé')
    requiere_equipo = models.CharField(max_length=150, null=True, blank=True, db_comment='Equipo que hay que comprar antes de activarla, si aplica')
    activa = models.BooleanField(db_default=False, db_comment='Encendida en esta finca')
    activada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='activada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la encendió')
    activada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "funcionalidad" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."funcionalidad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Interruptor de funciones por finca (feature flag): lo que aún no tiene equipo o decisión queda construido y apagado, y se enciende sin desplegar otra versión.'


# ==============================================================================================================
# Tabla nucleo.nota_voz  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/notas-voz/
# ==============================================================================================================
class NotaVoz(models.Model):
    """Nota de voz grabada en campo sin conexión; se transcribe al sincronizar y el operario confirma lo interpretado antes de crear el registro."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, db_comment='Quién grabó')
    audio_url = models.CharField(max_length=300, db_comment='Audio en el almacén de archivos')
    duracion_seg = models.SmallIntegerField(null=True, blank=True, db_comment='Duración en segundos')
    transcripcion = models.TextField(null=True, blank=True, db_comment='Texto obtenido por el servicio de voz a texto')
    proveedor_voz_texto = models.CharField(max_length=40, null=True, blank=True, db_comment='Servicio usado (intercambiable)')
    interpretacion = models.JSONField(null=True, blank=True, db_comment='Registro propuesto, ej. {"tabla":"registro_postura","lote":"AV-2026-01","huevos":87}')
    estado = models.CharField(max_length=12, choices=[('pendiente', 'pendiente'), ('interpretada', 'interpretada'), ('confirmada', 'confirmada'), ('descartada', 'descartada')], db_default='pendiente', db_comment='Solo una nota confirmada por la persona crea el registro')
    registro_tabla = models.CharField(max_length=60, null=True, blank=True, db_comment='Tabla del registro creado')
    registro_id = models.BigIntegerField(null=True, blank=True, db_comment='Id del registro creado')
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
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "nota_voz" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."nota_voz'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Nota de voz grabada en campo sin conexión; se transcribe al sincronizar y el operario confirma lo interpretado antes de crear el registro.'


# ==============================================================================================================
# Tabla nucleo.llave_api  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/llaves-api/
# ==============================================================================================================
class LlaveApi(models.Model):
    """Llave de un cliente B2B (HORECA) para la API: guarda solo su huella, con alcances, límite de peticiones y vencimiento. Se enciende con api_b2b."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Cliente dueño de la llave')
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    prefijo = models.CharField(max_length=12, db_comment='Prefijo visible para identificarla')
    hash_llave = models.CharField(max_length=64, db_comment='Huella SHA-256 de la llave (la llave nunca se guarda)')
    alcances = ArrayField(models.TextField(), db_default='{catalogo:leer}', db_comment='Permisos: catalogo:leer, pedidos:leer, pedidos:crear')
    limite_por_minuto = models.SmallIntegerField(db_default=60, db_comment='Límite de peticiones')
    activa = models.BooleanField(db_default=False, db_comment='Encendida')
    vence_en = models.DateField(db_comment='Vencimiento')
    ultimo_uso = models.DateTimeField(null=True, blank=True, db_comment='Último uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "llave_api" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."llave_api'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Llave de un cliente B2B (HORECA) para la API: guarda solo su huella, con alcances, límite de peticiones y vencimiento. Se enciende con api_b2b.'


# ==============================================================================================================
# Tabla nucleo.webhook_suscripcion  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/webhooks-suscripcion/
# ==============================================================================================================
class WebhookSuscripcion(models.Model):
    """Sistema externo (comprador, logística) que recibe eventos firmados del outbox: pedido confirmado, lote despachado, factura emitida."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Dueño')
    url = models.CharField(max_length=300, db_comment='URL https de destino')
    eventos = ArrayField(models.TextField(), db_comment='Tipos de evento')
    secreto_ref = models.CharField(max_length=120, db_comment='Nombre del secreto para firmar (HMAC); nunca el secreto')
    activa = models.BooleanField(db_default=False, db_comment='Encendida')
    fallos_seguidos = models.SmallIntegerField(db_default=0, db_comment='Fallos seguidos (al llegar a 10 se apaga)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "webhook_suscripcion" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."webhook_suscripcion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Sistema externo (comprador, logística) que recibe eventos firmados del outbox: pedido confirmado, lote despachado, factura emitida.'


# ==============================================================================================================
# Tabla nucleo.webhook_entrega  ·  por finca (seguridad por filas)  ·  API: /api/v1/nucleo/webhooks-entrega/
# ==============================================================================================================
class WebhookEntrega(models.Model):
    """Intento de entrega de un evento a un webhook, con reintentos."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    suscripcion = models.ForeignKey('nucleo.WebhookSuscripcion', models.DO_NOTHING, db_column='suscripcion_id', related_name='+', db_constraint=False, db_comment='Suscripción')
    evento_salida_id = models.BigIntegerField(db_comment='Evento del outbox')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('entregado', 'entregado'), ('fallido', 'fallido')], db_default='pendiente', db_comment='Estado')
    intentos = models.SmallIntegerField(db_default=0, db_comment='Intentos')
    codigo_respuesta = models.SmallIntegerField(null=True, blank=True, db_comment='Código HTTP')
    proximo_intento = models.DateTimeField(null=True, blank=True, db_comment='Próximo intento')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nucleo", tabla "webhook_entrega" (las comillas separan esquema y tabla)
        db_table = 'nucleo"."webhook_entrega'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Intento de entrega de un evento a un webhook, con reintentos.'
