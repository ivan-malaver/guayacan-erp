"""Modelos del esquema iot: Red local de la finca: dispositivos, sensores, actuadores, reglas, seguridad perimetral y cámaras (fase 4, con diseño listo desde ya).

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «iot». Django usa estas clases para leer y escribir
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
# Tabla iot.dispositivo  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/dispositivos/
# ==============================================================================================================
class Dispositivo(models.Model):
    """Equipo físico de la red local de la finca (ESP32, PLC, estación meteorológica) o la pasarela que la coordina. Los nodos hablan con la pasarela por MQTT local; la pasarela sincroniza con la nube cuando hay internet."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código')
    tipo = models.CharField(max_length=23, choices=[('esp32', 'esp32'), ('plc', 'plc'), ('estacion_clima', 'estacion_clima'), ('pasarela', 'pasarela'), ('registrador_temperatura', 'registrador_temperatura'), ('camara', 'camara'), ('camara_termica', 'camara_termica'), ('lector_acceso', 'lector_acceso'), ('central_alarma', 'central_alarma'), ('otro', 'otro')], db_comment='Tipo; la pasarela es el cerebro local que ejecuta las reglas, graba los clips y guarda datos sin internet')
    pasarela = models.ForeignKey('iot.Dispositivo', models.DO_NOTHING, db_column='pasarela_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Pasarela a la que reporta este nodo (vacío si es la pasarela)')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ubicación')
    topico_mqtt = models.CharField(max_length=120, db_comment='Tópico base en el broker local, ej. guayacan/riego/v03')
    direccion_red_local = models.GenericIPAddressField(null=True, blank=True, db_comment='IP fija en la red local de la finca')
    version_firmware = models.CharField(max_length=30, null=True, blank=True, db_comment='Versión del programa instalado')
    ultima_conexion = models.DateTimeField(null=True, blank=True, db_comment='Último latido recibido')
    ultima_sincronizacion_nube = models.DateTimeField(null=True, blank=True, db_comment='Solo pasarela: última vez que subió datos a la nube')
    activo = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "dispositivo" (las comillas separan esquema y tabla)
        db_table = 'iot"."dispositivo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Equipo físico de la red local de la finca (ESP32, PLC, estación meteorológica) o la pasarela que la coordina. Los nodos hablan con la pasarela por MQTT local; la pasarela sincroniza con la nube cuando hay internet.'


# ==============================================================================================================
# Tabla iot.sensor  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/sensores/
# ==============================================================================================================
class Sensor(models.Model):
    """Sensor de un dispositivo (humedad de suelo, nivel de tanque, caudal, temperatura, movimiento, puerta, humo, gas)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    dispositivo = models.ForeignKey('iot.Dispositivo', models.DO_NOTHING, db_column='dispositivo_id', related_name='+', db_constraint=False, db_comment='Dispositivo')
    codigo = models.CharField(max_length=30, db_comment='Código')
    magnitud = models.CharField(max_length=17, choices=[('humedad_suelo', 'humedad_suelo'), ('nivel_tanque', 'nivel_tanque'), ('caudal', 'caudal'), ('temperatura', 'temperatura'), ('humedad_aire', 'humedad_aire'), ('lluvia', 'lluvia'), ('oxigeno_agua', 'oxigeno_agua'), ('ph', 'ph'), ('movimiento', 'movimiento'), ('puerta', 'puerta'), ('rotura_vidrio', 'rotura_vidrio'), ('humo', 'humo'), ('gas', 'gas'), ('amoniaco', 'amoniaco'), ('presencia_termica', 'presencia_termica')], db_comment='Qué mide o detecta')
    unidad = models.CharField(max_length=10, db_comment='Unidad, ej. %, cm, L/min')
    valor_minimo_alerta = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, db_comment='Alerta por debajo')
    valor_maximo_alerta = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, db_comment='Alerta por encima')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "sensor" (las comillas separan esquema y tabla)
        db_table = 'iot"."sensor'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Sensor de un dispositivo (humedad de suelo, nivel de tanque, caudal, temperatura, movimiento, puerta, humo, gas).'


# ==============================================================================================================
# Tabla iot.actuador  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/actuadores/
# ==============================================================================================================
class Actuador(models.Model):
    """Elemento que el sistema puede accionar (electroválvula, bomba, relé, sirena, reflector, cerradura, cortina, extractor)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    dispositivo = models.ForeignKey('iot.Dispositivo', models.DO_NOTHING, db_column='dispositivo_id', related_name='+', db_constraint=False, db_comment='Dispositivo')
    codigo = models.CharField(max_length=30, db_comment='Código')
    tipo = models.CharField(max_length=14, choices=[('electrovalvula', 'electrovalvula'), ('bomba', 'bomba'), ('rele', 'rele'), ('motor', 'motor'), ('sirena', 'sirena'), ('reflector', 'reflector'), ('cerradura', 'cerradura'), ('cortina', 'cortina'), ('extractor', 'extractor')], db_comment='Tipo')
    zona_seguridad = models.ForeignKey('iot.ZonaSeguridad', models.DO_NOTHING, db_column='zona_seguridad_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona de seguridad que protege (sirenas, cerraduras, reflectores)')
    modo_falla = models.CharField(max_length=18, choices=[('cierra_sin_energia', 'cierra_sin_energia'), ('abre_sin_energia', 'abre_sin_energia'), ('mantiene', 'mantiene')], db_default='mantiene', db_comment='Qué hace si se va la energía: una cerradura en un paso de personas debe abrir sin energía')
    estado_actual = models.CharField(max_length=11, choices=[('abierto', 'abierto'), ('cerrado', 'cerrado'), ('encendido', 'encendido'), ('apagado', 'apagado'), ('desconocido', 'desconocido')], db_default='desconocido', db_comment='Último estado reportado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "actuador" (las comillas separan esquema y tabla)
        db_table = 'iot"."actuador'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Elemento que el sistema puede accionar (electroválvula, bomba, relé, sirena, reflector, cerradura, cortina, extractor).'


# ==============================================================================================================
# Tabla iot.lectura  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/lecturas/
# ==============================================================================================================
class Lectura(models.Model):
    """Medición de un sensor, particionada por mes (o hipertabla si se usa TimescaleDB); sin columnas de auditoría por volumen. La pasarela guarda las lecturas mientras no hay internet y las sube después."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    sensor = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_id', related_name='+', db_constraint=False, db_comment='Sensor')
    medido_en = models.DateTimeField(db_comment='Momento de la medición (reloj de la pasarela)')
    recibido_en = models.DateTimeField(db_default=Now(), db_comment='Momento en que llegó a la nube; la diferencia muestra el tiempo sin conexión')
    valor = models.FloatField(db_comment='Valor medido')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "lectura" (las comillas separan esquema y tabla)
        db_table = 'iot"."lectura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Medición de un sensor, particionada por mes (o hipertabla si se usa TimescaleDB); sin columnas de auditoría por volumen. La pasarela guarda las lecturas mientras no hay internet y las sube después.'


# ==============================================================================================================
# Tabla iot.regla_automatizacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/reglas/
# ==============================================================================================================
class ReglaAutomatizacion(models.Model):
    """Regla determinista que acciona un actuador (ej. abrir V-03 si humedad < 30 % y tanque > 40 %). Se ejecuta en la pasarela local, así funciona sin internet. La IA puede sugerir reglas pero no activarlas."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    condicion = models.JSONField(db_comment='Condición sobre sensores, horario y clima')
    actuador = models.ForeignKey('iot.Actuador', models.DO_NOTHING, db_column='actuador_id', related_name='+', db_constraint=False, db_comment='Actuador')
    accion = models.CharField(max_length=8, choices=[('abrir', 'abrir'), ('cerrar', 'cerrar'), ('encender', 'encender'), ('apagar', 'apagar')], db_comment='Acción')
    duracion_max_min = models.SmallIntegerField(db_comment='Tiempo máximo de seguridad; el nodo ESP32 también lo aplica por su cuenta')
    ejecuta_en = models.CharField(max_length=14, choices=[('pasarela_local', 'pasarela_local'), ('nodo', 'nodo'), ('nube', 'nube')], db_default='pasarela_local', db_comment='Dónde corre la regla; la nube solo para reglas no críticas')
    version = models.IntegerField(db_default=1, db_comment='Versión; sube con cada cambio')
    desplegada_version = models.IntegerField(null=True, blank=True, db_comment='Versión que confirmó tener la pasarela; distinta de version = cambio pendiente de bajar')
    activa = models.BooleanField(db_default=False, db_comment='Las reglas nacen inactivas hasta que un humano las activa')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la activó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "regla_automatizacion" (las comillas separan esquema y tabla)
        db_table = 'iot"."regla_automatizacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Regla determinista que acciona un actuador (ej. abrir V-03 si humedad < 30 % y tanque > 40 %). Se ejecuta en la pasarela local, así funciona sin internet. La IA puede sugerir reglas pero no activarlas.'


# ==============================================================================================================
# Tabla iot.comando_actuador  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/comandos/
# ==============================================================================================================
class ComandoActuador(models.Model):
    """Orden manual o automática a un actuador (abrir o cerrar una válvula), con su resultado. Funciona desde la red local aunque no haya internet."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    actuador = models.ForeignKey('iot.Actuador', models.DO_NOTHING, db_column='actuador_id', related_name='+', db_constraint=False, db_comment='Actuador')
    accion = models.CharField(max_length=8, choices=[('abrir', 'abrir'), ('cerrar', 'cerrar'), ('encender', 'encender'), ('apagar', 'apagar')], db_comment='Acción')
    origen = models.CharField(max_length=13, choices=[('app_nube', 'app_nube'), ('app_red_local', 'app_red_local'), ('regla', 'regla'), ('boton_fisico', 'boton_fisico')], db_comment='De dónde salió la orden')
    regla = models.ForeignKey('iot.ReglaAutomatizacion', models.DO_NOTHING, db_column='regla_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Regla que la emitió, si aplica')
    solicitado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='solicitado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona que la pidió, si aplica')
    duracion_max_min = models.SmallIntegerField(db_comment='Tiempo máximo antes de cerrar solo')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('enviado', 'enviado'), ('ejecutado', 'ejecutado'), ('fallido', 'fallido'), ('expirado', 'expirado')], db_default='pendiente', db_comment='Resultado')
    expira_en = models.DateTimeField(db_comment='Si no se ejecuta antes, se descarta (evita que una orden vieja se ejecute al volver la conexión)')
    ejecutado_en = models.DateTimeField(null=True, blank=True, db_comment='Confirmación del nodo')
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
        # Nombre real en PostgreSQL: esquema "iot", tabla "comando_actuador" (las comillas separan esquema y tabla)
        db_table = 'iot"."comando_actuador'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Orden manual o automática a un actuador (abrir o cerrar una válvula), con su resultado. Funciona desde la red local aunque no haya internet.'


# ==============================================================================================================
# Tabla iot.zona_seguridad  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/zonas-seguridad/
# ==============================================================================================================
class ZonaSeguridad(models.Model):
    """Área vigilada (perímetro, galpón, bodega, acceso) con su estado de alarma; las reglas corren en la pasarela local."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona del predio')
    codigo = models.CharField(max_length=20, db_comment='Código, ej. SEG-BOD-01')
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    tipo = models.CharField(max_length=9, choices=[('perimetro', 'perimetro'), ('acceso', 'acceso'), ('galpon', 'galpon'), ('bodega', 'bodega'), ('vivienda', 'vivienda'), ('otra', 'otra')], db_comment='Tipo')
    paso_personas = models.BooleanField(db_default=True, db_comment='Si por sus puertas salen personas: sus cerraduras deben abrir sin energía')
    bioseguridad = models.BooleanField(db_default=False, db_comment='Exige registro de visita y desinfección para entrar (galpones)')
    estado_alarma = models.CharField(max_length=13, choices=[('desarmado', 'desarmado'), ('armado', 'armado'), ('noche', 'noche'), ('mantenimiento', 'mantenimiento')], db_default='desarmado', db_comment='Estado actual; solo cambia con iot.cambiar_estado_alarma')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "zona_seguridad" (las comillas separan esquema y tabla)
        db_table = 'iot"."zona_seguridad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Área vigilada (perímetro, galpón, bodega, acceso) con su estado de alarma; las reglas corren en la pasarela local.'


# ==============================================================================================================
# Tabla iot.cambio_estado_alarma  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/cambios-estado-alarma/
# ==============================================================================================================
class CambioEstadoAlarma(models.Model):
    """Historial de cambios de estado de la alarma (solo inserción)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona_seguridad = models.ForeignKey('iot.ZonaSeguridad', models.DO_NOTHING, db_column='zona_seguridad_id', related_name='+', db_constraint=False, db_comment='Zona')
    estado_anterior = models.CharField(max_length=20, db_comment='Estado antes')
    estado_nuevo = models.CharField(max_length=20, db_comment='Estado después')
    origen = models.CharField(max_length=13, choices=[('app_nube', 'app_nube'), ('app_red_local', 'app_red_local'), ('teclado', 'teclado'), ('horario', 'horario'), ('regla', 'regla')], db_comment='De dónde salió el cambio')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona, si aplica')
    ocurrido_en = models.DateTimeField(db_default=Now(), db_comment='Momento')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "cambio_estado_alarma" (las comillas separan esquema y tabla)
        db_table = 'iot"."cambio_estado_alarma'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Historial de cambios de estado de la alarma (solo inserción).'


# ==============================================================================================================
# Tabla iot.credencial_acceso  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/credenciales-acceso/
# ==============================================================================================================
class CredencialAcceso(models.Model):
    """Credencial para abrir una puerta: PIN, tarjeta RFID o rostro. El rostro exige autorización expresa de biometría y su plantilla solo vive cifrada en la pasarela local, nunca en la nube."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Persona autorizada')
    zona_seguridad = models.ForeignKey('iot.ZonaSeguridad', models.DO_NOTHING, db_column='zona_seguridad_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona a la que da acceso; vacío = todas')
    metodo = models.CharField(max_length=6, choices=[('pin', 'pin'), ('rfid', 'rfid'), ('facial', 'facial')], db_comment='Método')
    referencia_hash = models.CharField(max_length=128, null=True, blank=True, db_comment='Hash del PIN o del número de tarjeta (nunca el valor en claro)')
    consentimiento = models.ForeignKey('terceros.ConsentimientoDatos', models.DO_NOTHING, db_column='consentimiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Autorización de biometría (obligatoria si el método es facial)')
    vigente_desde = models.DateField(db_comment='Desde')
    vigente_hasta = models.DateField(null=True, blank=True, db_comment='Hasta')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "credencial_acceso" (las comillas separan esquema y tabla)
        db_table = 'iot"."credencial_acceso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Credencial para abrir una puerta: PIN, tarjeta RFID o rostro. El rostro exige autorización expresa de biometría y su plantilla solo vive cifrada en la pasarela local, nunca en la nube.'


# ==============================================================================================================
# Tabla iot.camara  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/camaras/
# ==============================================================================================================
class Camara(models.Model):
    """Cámara de la finca: graba en la pasarela local por movimiento y sube solo clips elegidos."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    dispositivo = models.ForeignKey('iot.Dispositivo', models.DO_NOTHING, db_column='dispositivo_id', related_name='+', db_constraint=False, db_comment='Dispositivo')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ubicación')
    zona_seguridad = models.ForeignKey('iot.ZonaSeguridad', models.DO_NOTHING, db_column='zona_seguridad_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona de seguridad que vigila')
    tipo = models.CharField(max_length=9, choices=[('ip_rtsp', 'ip_rtsp'), ('termica', 'termica'), ('timelapse', 'timelapse')], db_comment='Tipo')
    graba_por_movimiento = models.BooleanField(db_default=True, db_comment='Graba solo cuando hay movimiento (ahorra energía y almacenamiento)')
    intervalo_timelapse_min = models.SmallIntegerField(null=True, blank=True, db_comment='Minutos entre fotos de time-lapse')
    retencion_dias = models.SmallIntegerField(db_default=30, db_comment='Días que se guardan los clips de seguridad antes de borrarse')
    aviso_visible = models.BooleanField(db_default=False, db_comment='Hay aviso de zona vigilada (Ley 1581)')
    stream_secreto_ref = models.CharField(max_length=120, null=True, blank=True, db_comment='Nombre del secreto con la URL y la clave del video')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "camara" (las comillas separan esquema y tabla)
        db_table = 'iot"."camara'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cámara de la finca: graba en la pasarela local por movimiento y sube solo clips elegidos.'


# ==============================================================================================================
# Tabla iot.evento_seguridad  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/eventos-seguridad/
# ==============================================================================================================
class EventoSeguridad(models.Model):
    """Hecho de seguridad detectado (intrusión, puerta, humo, gas, acceso): lo publica la pasarela, aunque no haya internet, y queda para su atención (solo inserción salvo la atención)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona_seguridad = models.ForeignKey('iot.ZonaSeguridad', models.DO_NOTHING, db_column='zona_seguridad_id', related_name='+', db_constraint=False, db_comment='Zona')
    tipo = models.CharField(max_length=16, choices=[('intrusion', 'intrusion'), ('puerta_abierta', 'puerta_abierta'), ('humo', 'humo'), ('gas', 'gas'), ('amoniaco', 'amoniaco'), ('temperatura', 'temperatura'), ('sabotaje', 'sabotaje'), ('falla_energia', 'falla_energia'), ('acceso_concedido', 'acceso_concedido'), ('acceso_denegado', 'acceso_denegado')], db_comment='Qué pasó')
    detector = models.CharField(max_length=14, choices=[('pir', 'pir'), ('magnetico', 'magnetico'), ('vidrio', 'vidrio'), ('camara', 'camara'), ('camara_termica', 'camara_termica'), ('sensor_gas', 'sensor_gas'), ('lector_acceso', 'lector_acceso'), ('manual', 'manual')], db_comment='Qué lo detectó: las reglas usan el hecho, no el tipo de sensor (así una cámara térmica entra sin cambiar reglas)')
    sensor = models.ForeignKey('iot.Sensor', models.DO_NOTHING, db_column='sensor_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Sensor')
    camara = models.ForeignKey('iot.Camara', models.DO_NOTHING, db_column='camara_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cámara')
    credencial = models.ForeignKey('iot.CredencialAcceso', models.DO_NOTHING, db_column='credencial_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Credencial usada (accesos)')
    severidad = models.CharField(max_length=11, choices=[('informativa', 'informativa'), ('media', 'media'), ('alta', 'alta'), ('critica', 'critica')], db_comment='Severidad')
    estado_alarma = models.CharField(max_length=20, db_comment='Estado de la alarma cuando ocurrió')
    acciones = models.JSONField(null=True, blank=True, db_comment='Lo que hizo la pasarela: sirena, reflectores, extractor, aviso push o SMS')
    ocurrido_en = models.DateTimeField(db_comment='Momento (reloj de la pasarela)')
    atendido_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='atendido_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo atendió')
    atendido_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    nota_atencion = models.TextField(null=True, blank=True, db_comment='Qué se encontró')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "evento_seguridad" (las comillas separan esquema y tabla)
        db_table = 'iot"."evento_seguridad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Hecho de seguridad detectado (intrusión, puerta, humo, gas, acceso): lo publica la pasarela, aunque no haya internet, y queda para su atención (solo inserción salvo la atención).'


# ==============================================================================================================
# Tabla iot.clip_video  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/clipes-video/
# ==============================================================================================================
class ClipVideo(models.Model):
    """Clip grabado por una cámara: los de seguridad se borran al vencer su retención; los marcados para redes pasan a una pieza audiovisual."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    camara = models.ForeignKey('iot.Camara', models.DO_NOTHING, db_column='camara_id', related_name='+', db_constraint=False, db_comment='Cámara')
    inicio = models.DateTimeField(db_comment='Inicio')
    fin = models.DateTimeField(db_comment='Fin')
    motivo = models.CharField(max_length=16, choices=[('movimiento', 'movimiento'), ('evento_seguridad', 'evento_seguridad'), ('timelapse', 'timelapse'), ('manual', 'manual')], db_comment='Por qué se grabó')
    evento_seguridad = models.ForeignKey('iot.EventoSeguridad', models.DO_NOTHING, db_column='evento_seguridad_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Evento asociado')
    ubicacion = models.CharField(max_length=8, choices=[('pasarela', 'pasarela'), ('nube', 'nube')], db_default='pasarela', db_comment='Dónde está guardado')
    archivo_url = models.CharField(max_length=300, db_comment='Ruta del archivo')
    para_redes = models.BooleanField(db_default=False, db_comment='Elegido para contenido de redes (se conserva)')
    retener_hasta = models.DateField(db_comment='Fecha de borrado automático')
    borrado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se borró el archivo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "clip_video" (las comillas separan esquema y tabla)
        db_table = 'iot"."clip_video'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Clip grabado por una cámara: los de seguridad se borran al vencer su retención; los marcados para redes pasan a una pieza audiovisual.'


# ==============================================================================================================
# Tabla iot.mision_robot  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/misiones-robot/
# ==============================================================================================================
class MisionRobot(models.Model):
    """Misión de un dron de monitoreo o de un robot de campo en piloto: una persona la aprueba; el robot opera solo en zonas sin personas y con parada de emergencia probada."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    activo = models.ForeignKey('activos.Activo', models.DO_NOTHING, db_column='activo_id', related_name='+', db_constraint=False, db_comment='Dron o robot')
    tipo = models.CharField(max_length=15, choices=[('dron_monitoreo', 'dron_monitoreo'), ('robot_deshierbe', 'robot_deshierbe'), ('robot_monitoreo', 'robot_monitoreo')], db_comment='Tipo')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Zona')
    estado = models.CharField(max_length=9, choices=[('propuesta', 'propuesta'), ('aprobada', 'aprobada'), ('en_curso', 'en_curso'), ('terminada', 'terminada'), ('abortada', 'abortada')], db_default='propuesta', db_comment='Estado')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    piloto = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='piloto_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Piloto certificado (dron)')
    poliza = models.ForeignKey('seguros.Poliza', models.DO_NOTHING, db_column='poliza_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Póliza de responsabilidad civil (dron)')
    altura_max_m = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, db_comment='Altura máxima (RAC 100: hasta 122 m)')
    zona_sin_personas = models.BooleanField(db_default=False, db_comment='Se confirmó que no hay personas en la zona')
    parada_emergencia_probada = models.BooleanField(db_default=False, db_comment='Se probó la parada de emergencia')
    inicio = models.DateTimeField(null=True, blank=True, db_comment='Inicio')
    fin = models.DateTimeField(null=True, blank=True, db_comment='Fin')
    resultado = models.JSONField(null=True, blank=True, db_comment='Fotos, conteos y lecturas devueltas')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "mision_robot" (las comillas separan esquema y tabla)
        db_table = 'iot"."mision_robot'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Misión de un dron de monitoreo o de un robot de campo en piloto: una persona la aprueba; el robot opera solo en zonas sin personas y con parada de emergencia probada.'


# ==============================================================================================================
# Tabla iot.prioridad_carga  ·  por finca (seguridad por filas)  ·  API: /api/v1/iot/prioridades-carga/
# ==============================================================================================================
class PrioridadCarga(models.Model):
    """Prioridad de cada carga eléctrica: con batería baja se cortan primero las no esenciales; alarma, nevera y agua de animales van primero."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    actuador = models.ForeignKey('iot.Actuador', models.DO_NOTHING, db_column='actuador_id', related_name='+', db_constraint=False, db_comment='Carga (relé)')
    prioridad = models.SmallIntegerField(db_comment='1 = crítica … 5 = prescindible')
    esencial = models.BooleanField(db_comment='Nunca se corta automáticamente')
    corte_bateria_pct = models.SmallIntegerField(null=True, blank=True, db_comment='Porcentaje de batería bajo el cual se corta')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "iot", tabla "prioridad_carga" (las comillas separan esquema y tabla)
        db_table = 'iot"."prioridad_carga'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Prioridad de cada carga eléctrica: con batería baja se cortan primero las no esenciales; alarma, nevera y agua de animales van primero.'
