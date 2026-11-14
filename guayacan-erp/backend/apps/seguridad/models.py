"""Modelos del esquema seguridad: Doble factor, sesiones, intentos de acceso, detector de ataques, señuelos, bloqueos, alertas, incidentes, pruebas y copias de seguridad.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «seguridad». Django usa estas clases para leer y escribir
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
# Tabla seguridad.factor_autenticacion  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/factores-autenticacion/
# ==============================================================================================================
class FactorAutenticacion(models.Model):
    """Segundo factor del usuario: app TOTP o llave de acceso (passkey/WebAuthn). Obligatorio para administrador y contador. El secreto vive en el gestor de secretos."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, db_comment='Usuario')
    tipo = models.CharField(max_length=15, choices=[('totp', 'totp'), ('webauthn', 'webauthn'), ('codigo_respaldo', 'codigo_respaldo')], db_comment='Tipo (sin biometría guardada en el servidor)')
    nombre = models.CharField(max_length=60, db_comment='Nombre del dispositivo')
    secreto_ref = models.CharField(max_length=120, db_comment='Referencia al secreto o a la llave pública')
    activo = models.BooleanField(db_default=True, db_comment='En uso')
    ultimo_uso = models.DateTimeField(null=True, blank=True, db_comment='Último uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "factor_autenticacion" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."factor_autenticacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Segundo factor del usuario: app TOTP o llave de acceso (passkey/WebAuthn). Obligatorio para administrador y contador. El secreto vive en el gestor de secretos.'


# ==============================================================================================================
# Tabla seguridad.sesion_usuario  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/sesiones-usuario/
# ==============================================================================================================
class SesionUsuario(models.Model):
    """Sesión iniciada: método, IP, dispositivo y vencimiento; se puede revocar en bloque ante un incidente."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, db_comment='Usuario')
    metodo = models.CharField(max_length=17, choices=[('contrasena', 'contrasena'), ('doble_factor', 'doble_factor'), ('llave_acceso', 'llave_acceso'), ('token_dispositivo', 'token_dispositivo')], db_comment='Cómo se autenticó')
    ip = models.GenericIPAddressField(db_comment='IP')
    agente_usuario = models.CharField(max_length=300, null=True, blank=True, db_comment='Navegador o app')
    dispositivo_captura_id = models.BigIntegerField(null=True, blank=True, db_comment='Celular de campo registrado')
    iniciada_en = models.DateTimeField(db_default=Now(), db_comment='Inicio')
    vence_en = models.DateTimeField(db_comment='Vencimiento')
    revocada_en = models.DateTimeField(null=True, blank=True, db_comment='Revocación')
    motivo_revocacion = models.CharField(max_length=120, null=True, blank=True, db_comment='Motivo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "sesion_usuario" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."sesion_usuario'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Sesión iniciada: método, IP, dispositivo y vencimiento; se puede revocar en bloque ante un incidente.'


# ==============================================================================================================
# Tabla seguridad.intento_acceso  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/intentos-acceso/
# ==============================================================================================================
class IntentoAcceso(models.Model):
    """Cada intento de inicio de sesión, exitoso o no (solo inserción). Alimenta el detector de ataques."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    correo = models.EmailField(max_length=254, db_comment='Correo intentado')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Usuario, si existe')
    ip = models.GenericIPAddressField(db_comment='IP')
    exito = models.BooleanField(db_comment='Entró')
    motivo_fallo = models.CharField(max_length=19, choices=[('contrasena', 'contrasena'), ('usuario_inexistente', 'usuario_inexistente'), ('cuenta_bloqueada', 'cuenta_bloqueada'), ('ip_bloqueada', 'ip_bloqueada'), ('segundo_factor', 'segundo_factor'), ('cuenta_inactiva', 'cuenta_inactiva'), ('senuelo', 'senuelo')], null=True, blank=True, db_comment='Motivo del fallo')
    agente_usuario = models.CharField(max_length=300, null=True, blank=True, db_comment='Navegador o app')
    ocurrido_en = models.DateTimeField(db_default=Now(), db_comment='Momento')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "intento_acceso" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."intento_acceso'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cada intento de inicio de sesión, exitoso o no (solo inserción). Alimenta el detector de ataques.'


# ==============================================================================================================
# Tabla seguridad.regla_deteccion  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/reglas-deteccion/
# ==============================================================================================================
class ReglaDeteccion(models.Model):
    """Regla del detector de ataques: cuántos hechos en cuánto tiempo, severidad y respuesta automática."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=40, unique=True, db_comment='Código, ej. fuerza_bruta_cuenta')
    descripcion = models.TextField(db_comment='Qué detecta')
    umbral = models.SmallIntegerField(db_comment='Número de hechos')
    ventana_min = models.SmallIntegerField(db_comment='Minutos')
    severidad = models.CharField(max_length=7, choices=[('baja', 'baja'), ('media', 'media'), ('alta', 'alta'), ('critica', 'critica')], db_comment='Severidad')
    respuesta = models.CharField(max_length=16, choices=[('alertar', 'alertar'), ('bloquear_ip', 'bloquear_ip'), ('bloquear_cuenta', 'bloquear_cuenta'), ('revocar_sesiones', 'revocar_sesiones')], db_comment='Qué hace sola')
    bloqueo_min = models.SmallIntegerField(db_default=30, db_comment='Minutos de bloqueo')
    activa = models.BooleanField(db_default=True, db_comment='Encendida')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "regla_deteccion" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."regla_deteccion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Regla del detector de ataques: cuántos hechos en cuánto tiempo, severidad y respuesta automática.'


# ==============================================================================================================
# Tabla seguridad.bloqueo  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/bloqueos/
# ==============================================================================================================
class Bloqueo(models.Model):
    """Bloqueo temporal de una cuenta o una IP por una regla o una persona."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=6, choices=[('cuenta', 'cuenta'), ('ip', 'ip')], db_comment='Qué se bloquea')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cuenta')
    ip = models.CharField(max_length=43, null=True, blank=True, db_comment='IP o red')
    regla = models.ForeignKey('seguridad.ReglaDeteccion', models.DO_NOTHING, db_column='regla_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Regla que lo puso')
    motivo = models.CharField(max_length=200, db_comment='Motivo')
    desde = models.DateTimeField(db_default=Now(), db_comment='Desde')
    hasta = models.DateTimeField(null=True, blank=True, db_comment='Hasta; vacío = indefinido')
    levantado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='levantado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo levantó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "bloqueo" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."bloqueo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Bloqueo temporal de una cuenta o una IP por una regla o una persona.'


# ==============================================================================================================
# Tabla seguridad.senuelo  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/senuelos/
# ==============================================================================================================
class Senuelo(models.Model):
    """Señuelo para intrusos (cuenta, llave de API o URL que nadie legítimo usa): tocarlo dispara una alerta crítica y bloquea la IP."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=9, choices=[('cuenta', 'cuenta'), ('llave_api', 'llave_api'), ('url', 'url'), ('registro', 'registro')], db_comment='Tipo')
    valor = models.CharField(max_length=200, unique=True, db_comment='Correo, prefijo o ruta del señuelo')
    descripcion = models.CharField(max_length=200, null=True, blank=True, db_comment='Para qué está')
    activo = models.BooleanField(db_default=True, db_comment='Encendido')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "senuelo" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."senuelo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Señuelo para intrusos (cuenta, llave de API o URL que nadie legítimo usa): tocarlo dispara una alerta crítica y bloquea la IP.'


# ==============================================================================================================
# Tabla seguridad.alerta_seguridad  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/alertas-seguridad/
# ==============================================================================================================
class AlertaSeguridad(models.Model):
    """Hecho sospechoso detectado por las reglas, el WAF, la pasarela o la base (fuerza bruta, escalada de permisos, exportación masiva, señuelo). Solo inserción salvo su atención."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=23, choices=[('fuerza_bruta', 'fuerza_bruta'), ('relleno_credenciales', 'relleno_credenciales'), ('senuelo', 'senuelo'), ('escalada_privilegios', 'escalada_privilegios'), ('cambio_permisos', 'cambio_permisos'), ('exportacion_masiva', 'exportacion_masiva'), ('acceso_ip_nueva', 'acceso_ip_nueva'), ('sesion_sin_doble_factor', 'sesion_sin_doble_factor'), ('inyeccion', 'inyeccion'), ('abuso_api', 'abuso_api'), ('dispositivo_desconocido', 'dispositivo_desconocido'), ('firmware_no_firmado', 'firmware_no_firmado'), ('copia_fallida', 'copia_fallida'), ('otro', 'otro')], db_comment='Qué pasó')
    severidad = models.CharField(max_length=7, choices=[('baja', 'baja'), ('media', 'media'), ('alta', 'alta'), ('critica', 'critica')], db_comment='Severidad')
    fuente = models.CharField(max_length=10, choices=[('app', 'app'), ('base_datos', 'base_datos'), ('waf', 'waf'), ('api', 'api'), ('pasarela', 'pasarela'), ('agente_ia', 'agente_ia'), ('monitoreo', 'monitoreo')], db_comment='Quién lo detectó')
    regla = models.ForeignKey('seguridad.ReglaDeteccion', models.DO_NOTHING, db_column='regla_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Regla')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Usuario implicado')
    ip = models.GenericIPAddressField(null=True, blank=True, db_comment='IP')
    detalle = models.JSONField(null=True, blank=True, db_comment='Datos del hecho')
    ocurrido_en = models.DateTimeField(db_default=Now(), db_comment='Momento')
    estado = models.CharField(max_length=14, choices=[('nueva', 'nueva'), ('en_analisis', 'en_analisis'), ('contenida', 'contenida'), ('falso_positivo', 'falso_positivo'), ('cerrada', 'cerrada')], db_default='nueva', db_comment='Atención')
    atendida_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='atendida_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la atendió')
    incidente = models.ForeignKey('seguridad.Incidente', models.DO_NOTHING, db_column='incidente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Incidente al que pertenece')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "alerta_seguridad" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."alerta_seguridad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Hecho sospechoso detectado por las reglas, el WAF, la pasarela o la base (fuerza bruta, escalada de permisos, exportación masiva, señuelo). Solo inserción salvo su atención.'


# ==============================================================================================================
# Tabla seguridad.incidente  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/incidentes/
# ==============================================================================================================
class Incidente(models.Model):
    """Incidente de seguridad con su atención; si compromete datos personales se reporta a la SIC (Ley 1581)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    titulo = models.CharField(max_length=200, db_comment='Título')
    severidad = models.CharField(max_length=7, choices=[('baja', 'baja'), ('media', 'media'), ('alta', 'alta'), ('critica', 'critica')], db_comment='Severidad')
    estado = models.CharField(max_length=10, choices=[('abierto', 'abierto'), ('contenido', 'contenido'), ('erradicado', 'erradicado'), ('cerrado', 'cerrado')], db_default='abierto', db_comment='Estado')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, db_comment='Responsable')
    datos_personales_afectados = models.BooleanField(db_default=False, db_comment='Hubo datos personales comprometidos')
    reportado_sic_en = models.DateField(null=True, blank=True, db_comment='Reporte a la Superintendencia de Industria y Comercio')
    abierto_en = models.DateTimeField(db_default=Now(), db_comment='Apertura')
    cerrado_en = models.DateTimeField(null=True, blank=True, db_comment='Cierre')
    lecciones = models.TextField(null=True, blank=True, db_comment='Lecciones aprendidas')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "incidente" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."incidente'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Incidente de seguridad con su atención; si compromete datos personales se reporta a la SIC (Ley 1581).'


# ==============================================================================================================
# Tabla seguridad.ejecucion_prueba  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/ejecuciones-prueba/
# ==============================================================================================================
class EjecucionPrueba(models.Model):
    """Módulo de pruebas: cada corrida de pruebas (unitarias, de reglas de la base, extremo a extremo, carga, dependencias, SAST, DAST, pentest, restauración de copias) con su resultado."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=19, choices=[('unitaria', 'unitaria'), ('integracion', 'integracion'), ('reglas_bd', 'reglas_bd'), ('extremo_a_extremo', 'extremo_a_extremo'), ('carga', 'carga'), ('dependencias', 'dependencias'), ('sast', 'sast'), ('dast', 'dast'), ('pentest', 'pentest'), ('restauracion_copia', 'restauracion_copia'), ('simulacro_incidente', 'simulacro_incidente')], db_comment='Tipo de prueba')
    suite = models.CharField(max_length=80, db_comment='Suite, ej. pruebas_reglas_v5')
    version_sistema = models.CharField(max_length=20, db_comment='Versión probada')
    entorno = models.CharField(max_length=10, choices=[('desarrollo', 'desarrollo'), ('pruebas', 'pruebas'), ('practica', 'practica'), ('produccion', 'produccion')], db_comment='Dónde corrió (nunca pentest en producción sin aprobación)')
    total = models.IntegerField(db_comment='Casos')
    aprobadas = models.IntegerField(db_comment='Aprobados')
    fallidas = models.IntegerField(db_comment='Fallidos')
    hallazgos_criticos = models.IntegerField(db_default=0, db_comment='Hallazgos críticos (seguridad)')
    herramienta = models.CharField(max_length=60, null=True, blank=True, db_comment='Herramienta, ej. pytest, pgTAP, OWASP ZAP, pip-audit')
    informe_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Informe')
    ejecutada_en = models.DateTimeField(db_default=Now(), db_comment='Cuándo')
    ejecutada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='ejecutada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "ejecucion_prueba" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."ejecucion_prueba'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Módulo de pruebas: cada corrida de pruebas (unitarias, de reglas de la base, extremo a extremo, carga, dependencias, SAST, DAST, pentest, restauración de copias) con su resultado.'


# ==============================================================================================================
# Tabla seguridad.copia_seguridad  ·  catálogo compartido entre fincas  ·  API: /api/v1/seguridad/copias-seguridad/
# ==============================================================================================================
class CopiaSeguridad(models.Model):
    """Copia cifrada de la base o los archivos (regla 3-2-1) y su prueba mensual de restauración."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    alcance = models.CharField(max_length=13, choices=[('postgresql', 'postgresql'), ('mongodb', 'mongodb'), ('archivos', 'archivos'), ('configuracion', 'configuracion')], db_comment='Qué se copió')
    destino = models.CharField(max_length=13, choices=[('local', 'local'), ('nube', 'nube'), ('disco_externo', 'disco_externo')], db_comment='Dónde')
    inicio = models.DateTimeField(db_comment='Inicio')
    fin = models.DateTimeField(null=True, blank=True, db_comment='Fin')
    tamano_mb = models.DecimalField(max_digits=12, decimal_places=1, null=True, blank=True, db_comment='Tamaño')
    hash_sha256 = models.CharField(max_length=64, null=True, blank=True, db_comment='Huella')
    cifrada = models.BooleanField(db_comment='Cifrada')
    exitosa = models.BooleanField(db_comment='Terminó bien')
    restauracion_probada_en = models.DateTimeField(null=True, blank=True, db_comment='Última prueba de restauración')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "seguridad", tabla "copia_seguridad" (las comillas separan esquema y tabla)
        db_table = 'seguridad"."copia_seguridad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Copia cifrada de la base o los archivos (regla 3-2-1) y su prueba mensual de restauración.'
