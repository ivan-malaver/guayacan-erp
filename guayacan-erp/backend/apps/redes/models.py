"""Modelos del esquema redes: Cuentas de redes sociales y publicaciones con su flujo de aprobación.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «redes». Django usa estas clases para leer y escribir
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
# Tabla redes.cuenta_red  ·  por finca (seguridad por filas)  ·  API: /api/v1/redes/cuentas-red/
# ==============================================================================================================
class CuentaRed(models.Model):
    """Cuenta de la finca en un canal de mensajería o red social; las credenciales van en el gestor de secretos, no aquí."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    plataforma = models.ForeignKey('redes.PoliticaCanal', models.DO_NOTHING, to_field='plataforma', db_column='plataforma', related_name='+', db_constraint=False, db_comment='Canal (whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina)')
    nombre_cuenta = models.CharField(max_length=100, db_comment='Nombre o número')
    identificador_externo = models.CharField(max_length=80, db_comment='Id en la plataforma')
    secreto_ref = models.CharField(max_length=120, db_comment='Nombre del secreto con el token de acceso')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "redes", tabla "cuenta_red" (las comillas separan esquema y tabla)
        db_table = 'redes"."cuenta_red'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cuenta de la finca en un canal de mensajería o red social; las credenciales van en el gestor de secretos, no aquí.'


# ==============================================================================================================
# Tabla redes.publicacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/redes/publicaciones/
# ==============================================================================================================
class Publicacion(models.Model):
    """Contenido para redes: lo redacta el agente de redes y se publica solo con aprobación."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    cuenta_red = models.ForeignKey('redes.CuentaRed', models.DO_NOTHING, db_column='cuenta_red_id', related_name='+', db_constraint=False, db_comment='Cuenta')
    texto = models.TextField(db_comment='Texto')
    medios = models.JSONField(null=True, blank=True, db_comment='Imágenes o videos (rutas en MinIO)')
    estado = models.CharField(max_length=10, choices=[('borrador', 'borrador'), ('propuesta', 'propuesta'), ('aprobada', 'aprobada'), ('programada', 'programada'), ('publicada', 'publicada'), ('rechazada', 'rechazada')], db_default='borrador', db_comment='Situación')
    programada_para = models.DateTimeField(null=True, blank=True, db_comment='Fecha de publicación')
    publicada_en = models.DateTimeField(null=True, blank=True, db_comment='Fecha real')
    id_externo = models.CharField(max_length=80, null=True, blank=True, db_comment='Id en la plataforma')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente que la redactó')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    recomendacion = models.ForeignKey('ia.Recomendacion', models.DO_NOTHING, db_column='recomendacion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Recomendación que la motivó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "redes", tabla "publicacion" (las comillas separan esquema y tabla)
        db_table = 'redes"."publicacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Contenido para redes: lo redacta el agente de redes y se publica solo con aprobación.'


# ==============================================================================================================
# Tabla redes.politica_canal  ·  catálogo compartido entre fincas  ·  API: /api/v1/redes/politicas-canal/
# ==============================================================================================================
class PoliticaCanal(models.Model):
    """Reglas de cada canal según su proveedor (Meta, TikTok): ventana para responder, quién inicia, límites y cobro. Se actualiza cuando cambian las políticas."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    plataforma = models.CharField(max_length=20, unique=True, db_comment='Código del canal: whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina')
    ventana_horas = models.SmallIntegerField(null=True, blank=True, db_comment='Horas para responder después del último mensaje del cliente; vacío = sin límite (web propia)')
    ventana_agente_humano_horas = models.SmallIntegerField(null=True, blank=True, db_comment='Horas extra solo para respuestas de una persona (etiqueta de agente humano de Meta)')
    ventana_anuncio_horas = models.SmallIntegerField(null=True, blank=True, db_comment='Ventana ampliada si el cliente llegó por un anuncio que abre chat')
    max_mensajes_por_ventana = models.SmallIntegerField(null=True, blank=True, db_comment='Tope de mensajes de la empresa por ventana (TikTok: 10)')
    empresa_puede_iniciar = models.BooleanField(db_comment='Si la empresa puede escribir primero (WhatsApp solo con plantilla aprobada)')
    requiere_plantilla_fuera_ventana = models.BooleanField(db_comment='Fuera de la ventana solo se envían plantillas aprobadas')
    cobra_por_mensaje = models.BooleanField(db_comment='El proveedor cobra por mensaje enviado')
    mensajes_servicio_gratis_mes = models.IntegerField(null=True, blank=True, db_comment='Mensajes de servicio sin costo al mes (WhatsApp: 1.000 por número)')
    solo_bot_del_negocio = models.BooleanField(db_default=True, db_comment='El bot debe limitarse a temas de la finca; no puede ser un asistente general')
    disponible = models.BooleanField(db_default=True, db_comment='Si el canal está disponible para cuentas registradas en Colombia')
    fuente_url = models.CharField(max_length=300, null=True, blank=True, db_comment='Documento donde se verificó la regla')
    verificado_en = models.DateField(db_comment='Cuándo se verificó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "redes", tabla "politica_canal" (las comillas separan esquema y tabla)
        db_table = 'redes"."politica_canal'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Reglas de cada canal según su proveedor (Meta, TikTok): ventana para responder, quién inicia, límites y cobro. Se actualiza cuando cambian las políticas.'


# ==============================================================================================================
# Tabla redes.plantilla_mensaje  ·  por finca (seguridad por filas)  ·  API: /api/v1/redes/plantillas-mensaje/
# ==============================================================================================================
class PlantillaMensaje(models.Model):
    """Plantilla aprobada por Meta para escribir fuera de la ventana de 24 horas de WhatsApp (confirmaciones, recordatorios, promociones)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    cuenta_red = models.ForeignKey('redes.CuentaRed', models.DO_NOTHING, db_column='cuenta_red_id', related_name='+', db_constraint=False, db_comment='Cuenta de WhatsApp')
    nombre = models.CharField(max_length=80, db_comment='Nombre técnico, ej. pedido_confirmado')
    categoria = models.CharField(max_length=14, choices=[('marketing', 'marketing'), ('utility', 'utility'), ('authentication', 'authentication')], db_comment='Categoría de Meta; define el precio y si exige consentimiento de publicidad')
    idioma = models.CharField(max_length=10, db_default='es_CO', db_comment='Idioma')
    cuerpo = models.TextField(db_comment='Texto con variables {{1}}, {{2}}')
    variables = models.JSONField(null=True, blank=True, db_comment='Qué dato va en cada variable')
    estado_meta = models.CharField(max_length=9, choices=[('borrador', 'borrador'), ('enviada', 'enviada'), ('aprobada', 'aprobada'), ('rechazada', 'rechazada'), ('pausada', 'pausada')], db_default='borrador', db_comment='Estado de revisión en Meta')
    id_externo = models.CharField(max_length=80, null=True, blank=True, db_comment='Id en Meta')
    finalidad_requerida = models.CharField(max_length=16, choices=[('atencion_pedidos', 'atencion_pedidos'), ('publicidad', 'publicidad')], db_comment='Consentimiento que debe tener el cliente para recibirla')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "redes", tabla "plantilla_mensaje" (las comillas separan esquema y tabla)
        db_table = 'redes"."plantilla_mensaje'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Plantilla aprobada por Meta para escribir fuera de la ventana de 24 horas de WhatsApp (confirmaciones, recordatorios, promociones).'


# ==============================================================================================================
# Tabla redes.mensaje_saliente  ·  por finca (seguridad por filas)  ·  API: /api/v1/redes/mensajes-salientes/
# ==============================================================================================================
class MensajeSaliente(models.Model):
    """Registro de control de cada mensaje que la finca envía por un canal: si estaba dentro de la ventana, qué plantilla usó, qué consentimiento lo permitió y cuánto costó."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    cuenta_red = models.ForeignKey('redes.CuentaRed', models.DO_NOTHING, db_column='cuenta_red_id', related_name='+', db_constraint=False, db_comment='Canal')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Destinatario, si está identificado')
    conversacion_ref = models.CharField(max_length=24, null=True, blank=True, db_comment='Conversación en MongoDB')
    tipo = models.CharField(max_length=28, choices=[('servicio', 'servicio'), ('plantilla', 'plantilla'), ('respuesta_privada_comentario', 'respuesta_privada_comentario')], db_comment='Servicio = respuesta normal dentro de la ventana')
    plantilla = models.ForeignKey('redes.PlantillaMensaje', models.DO_NOTHING, db_column='plantilla_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Plantilla usada')
    autor = models.CharField(max_length=7, choices=[('agente', 'agente'), ('humano', 'humano'), ('sistema', 'sistema')], db_comment='Quién lo generó')
    dentro_ventana = models.BooleanField(db_comment='Si se envió dentro de la ventana del canal')
    consentimiento = models.ForeignKey('terceros.ConsentimientoDatos', models.DO_NOTHING, db_column='consentimiento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Consentimiento que lo autoriza (obligatorio para publicidad)')
    costo_estimado_usd = models.DecimalField(max_digits=10, decimal_places=4, db_default=0, db_comment='Costo según la tarifa del canal')
    estado_entrega = models.CharField(max_length=19, choices=[('enviado', 'enviado'), ('entregado', 'entregado'), ('leido', 'leido'), ('fallido', 'fallido'), ('bloqueado_por_regla', 'bloqueado_por_regla')], db_default='enviado', db_comment='Resultado; bloqueado_por_regla = el sistema lo detuvo (fuera de ventana, sin consentimiento)')
    enviado_en = models.DateTimeField(db_default=Now(), db_comment='Momento')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "redes", tabla "mensaje_saliente" (las comillas separan esquema y tabla)
        db_table = 'redes"."mensaje_saliente'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Registro de control de cada mensaje que la finca envía por un canal: si estaba dentro de la ventana, qué plantilla usó, qué consentimiento lo permitió y cuánto costó.'


# ==============================================================================================================
# Tabla redes.pieza_audiovisual  ·  por finca (seguridad por filas)  ·  API: /api/v1/redes/piezas-audiovisual/
# ==============================================================================================================
class PiezaAudiovisual(models.Model):
    """Video, time-lapse o foto preparada para redes: la IA propone guion y texto, FFmpeg arma el archivo y una persona aprueba. Si aparecen personas, todas deben tener consentimiento de imagen."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=17, choices=[('video_promocional', 'video_promocional'), ('timelapse', 'timelapse'), ('reel', 'reel'), ('foto', 'foto')], db_comment='Tipo')
    clips = models.JSONField(null=True, blank=True, db_comment='Clips de origen (ids de iot.clip_video o archivos subidos)')
    guion = models.TextField(null=True, blank=True, db_comment='Guion propuesto')
    texto_publicacion = models.TextField(null=True, blank=True, db_comment='Texto para la red')
    musica_ref = models.CharField(max_length=120, null=True, blank=True, db_comment='Pista con licencia de uso')
    archivo_url = models.CharField(max_length=300, null=True, blank=True, db_comment='MP4 o imagen final')
    personas_identificables = models.BooleanField(db_default=False, db_comment='Si aparecen personas reconocibles')
    estado = models.CharField(max_length=9, choices=[('borrador', 'borrador'), ('propuesta', 'propuesta'), ('aprobada', 'aprobada'), ('rechazada', 'rechazada'), ('publicada', 'publicada')], db_default='borrador', db_comment='Situación')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente que la propuso')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    publicacion = models.ForeignKey('redes.Publicacion', models.DO_NOTHING, db_column='publicacion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Publicación en la que se usó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "redes", tabla "pieza_audiovisual" (las comillas separan esquema y tabla)
        db_table = 'redes"."pieza_audiovisual'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Video, time-lapse o foto preparada para redes: la IA propone guion y texto, FFmpeg arma el archivo y una persona aprueba. Si aparecen personas, todas deben tener consentimiento de imagen.'


# ==============================================================================================================
# Tabla redes.pieza_persona  ·  por finca (seguridad por filas)  ·  API: /api/v1/redes/piezas-persona/
# ==============================================================================================================
class PiezaPersona(models.Model):
    """Persona que aparece en una pieza audiovisual y su consentimiento de imagen."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    pieza_audiovisual = models.ForeignKey('redes.PiezaAudiovisual', models.DO_NOTHING, db_column='pieza_audiovisual_id', related_name='+', db_constraint=False, db_comment='Pieza')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, db_comment='Persona')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "redes", tabla "pieza_persona" (las comillas separan esquema y tabla)
        db_table = 'redes"."pieza_persona'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Persona que aparece en una pieza audiovisual y su consentimiento de imagen.'
