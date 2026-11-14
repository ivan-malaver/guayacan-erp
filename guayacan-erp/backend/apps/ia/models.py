"""Modelos del esquema ia: Agentes, herramientas, aprobaciones, base de conocimiento, recomendaciones, evaluaciones y consumo de IA.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «ia». Django usa estas clases para leer y escribir
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
# Tabla ia.agente  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/agentes/
# ==============================================================================================================
class Agente(models.Model):
    """Agente de IA con un rol, sus instrucciones versionadas, su modelo y su nivel de autonomía."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=40, db_comment='Código, ej. asesor_clientes, analista_mercados')
    nombre = models.CharField(max_length=80, db_comment='Nombre visible, ej. Asesor virtual')
    rol = models.TextField(db_comment='Qué hace y qué no hace')
    nivel_autonomia = models.CharField(max_length=17, choices=[('solo_lectura', 'solo_lectura'), ('propone', 'propone'), ('ejecuta_con_regla', 'ejecuta_con_regla')], db_comment='Hasta dónde puede actuar')
    proveedor_modelo = models.CharField(max_length=40, db_comment='Proveedor, ej. anthropic')
    modelo = models.CharField(max_length=60, db_comment='Modelo, ej. claude-sonnet-5-5')
    modelo_respaldo = models.CharField(max_length=60, null=True, blank=True, db_comment='Modelo si el principal falla')
    version_instrucciones = models.CharField(max_length=20, db_comment='Versión del prompt de sistema vigente')
    instrucciones = models.TextField(db_comment='Prompt de sistema vigente')
    limite_costo_diario_usd = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, db_comment='Tope de gasto por día')
    activo = models.BooleanField(db_default=True, db_comment='Si atiende')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "agente" (las comillas separan esquema y tabla)
        db_table = 'ia"."agente'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Agente de IA con un rol, sus instrucciones versionadas, su modelo y su nivel de autonomía.'


# ==============================================================================================================
# Tabla ia.herramienta  ·  catálogo compartido entre fincas  ·  API: /api/v1/ia/herramientas/
# ==============================================================================================================
class Herramienta(models.Model):
    """Función del ERP que un agente puede invocar (por MCP o API), con su nivel de riesgo."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=60, unique=True, db_comment='Código, ej. consultar_catalogo, proponer_precio')
    descripcion = models.TextField(db_comment='Qué hace (es lo que lee el modelo)')
    tipo = models.CharField(max_length=9, choices=[('lectura', 'lectura'), ('propuesta', 'propuesta'), ('escritura', 'escritura')], db_comment='Lectura no cambia nada; propuesta crea una solicitud; escritura cambia datos')
    requiere_aprobacion = models.BooleanField(db_default=False, db_comment='Si cada uso pasa por un humano')
    esquema_entrada = models.JSONField(db_comment='JSON Schema de los parámetros')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "herramienta" (las comillas separan esquema y tabla)
        db_table = 'ia"."herramienta'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Función del ERP que un agente puede invocar (por MCP o API), con su nivel de riesgo.'


# ==============================================================================================================
# Tabla ia.agente_herramienta  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/agentes/{id}/herramientas/
# ==============================================================================================================
class AgenteHerramienta(models.Model):
    """Qué herramientas puede usar cada agente (mínimo privilegio)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, db_comment='Agente')
    herramienta = models.ForeignKey('ia.Herramienta', models.DO_NOTHING, db_column='herramienta_id', related_name='+', db_constraint=False, db_comment='Herramienta')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "agente_herramienta" (las comillas separan esquema y tabla)
        db_table = 'ia"."agente_herramienta'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Qué herramientas puede usar cada agente (mínimo privilegio).'


# ==============================================================================================================
# Tabla ia.solicitud_aprobacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/solicitudes-aprobacion/
# ==============================================================================================================
class SolicitudAprobacion(models.Model):
    """Bandeja del administrador: toda acción que un agente quiere hacer y requiere permiso humano."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, db_comment='Agente que pide')
    herramienta = models.ForeignKey('ia.Herramienta', models.DO_NOTHING, db_column='herramienta_id', related_name='+', db_constraint=False, db_comment='Acción solicitada')
    entidad = models.CharField(max_length=60, db_comment='Tabla afectada, ej. comercial.propuesta_precio')
    entidad_id = models.BigIntegerField(null=True, blank=True, db_comment='Registro afectado')
    resumen = models.TextField(db_comment='Qué se pide, en una frase')
    carga = models.JSONField(db_comment='Parámetros exactos que se ejecutarán')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('aprobada', 'aprobada'), ('rechazada', 'rechazada'), ('vencida', 'vencida'), ('ejecutada', 'ejecutada'), ('fallida', 'fallida')], db_default='pendiente', db_comment='Situación')
    vence_en = models.DateTimeField(db_comment='Límite para decidir')
    resuelto_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='resuelto_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién decidió')
    resuelto_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    motivo = models.TextField(null=True, blank=True, db_comment='Motivo de la decisión')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "solicitud_aprobacion" (las comillas separan esquema y tabla)
        db_table = 'ia"."solicitud_aprobacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Bandeja del administrador: toda acción que un agente quiere hacer y requiere permiso humano.'


# ==============================================================================================================
# Tabla ia.documento_conocimiento  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/documentos-conocimiento/
# ==============================================================================================================
class DocumentoConocimiento(models.Model):
    """Fuente de la base de conocimiento: fichas de producto, políticas, preguntas frecuentes, manuales técnicos, informes."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    titulo = models.CharField(max_length=200, db_comment='Título')
    tipo = models.CharField(max_length=18, choices=[('ficha_producto', 'ficha_producto'), ('politica', 'politica'), ('pregunta_frecuente', 'pregunta_frecuente'), ('manual_tecnico', 'manual_tecnico'), ('informe', 'informe'), ('receta', 'receta'), ('turismo', 'turismo')], db_comment='Tipo')
    contenido = models.TextField(db_comment='Texto completo')
    fuente = models.CharField(max_length=300, null=True, blank=True, db_comment='Origen (archivo, URL, autor)')
    version = models.SmallIntegerField(db_default=1, db_comment='Versión')
    vigente = models.BooleanField(db_default=True, db_comment='Si los agentes lo usan')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién validó el contenido')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "documento_conocimiento" (las comillas separan esquema y tabla)
        db_table = 'ia"."documento_conocimiento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Fuente de la base de conocimiento: fichas de producto, políticas, preguntas frecuentes, manuales técnicos, informes.'


# ==============================================================================================================
# Tabla ia.fragmento_conocimiento  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/fragmentos-conocimiento/
# ==============================================================================================================
class FragmentoConocimiento(models.Model):
    """Trozo de un documento con su vector semántico (pgvector) para que los agentes encuentren la información relevante (RAG)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    documento = models.ForeignKey('ia.DocumentoConocimiento', models.DO_NOTHING, db_column='documento_id', related_name='+', db_constraint=False, db_comment='Documento')
    orden = models.IntegerField(db_comment='Posición dentro del documento')
    texto = models.TextField(db_comment='Texto del fragmento')
    vector = VectorField(dimensions=1024, db_comment='Representación numérica del significado (embedding)')
    metadatos = models.JSONField(null=True, blank=True, db_comment='Producto, tema, vigencia')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "fragmento_conocimiento" (las comillas separan esquema y tabla)
        db_table = 'ia"."fragmento_conocimiento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Trozo de un documento con su vector semántico (pgvector) para que los agentes encuentren la información relevante (RAG).'


# ==============================================================================================================
# Tabla ia.recomendacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/recomendaciones/
# ==============================================================================================================
class Recomendacion(models.Model):
    """Plan de acción o mejora continua propuesto por un agente analista, con su seguimiento (ciclo PHVA)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, db_comment='Agente que la propone')
    tipo = models.CharField(max_length=15, choices=[('mejora_continua', 'mejora_continua'), ('comercial', 'comercial'), ('compra', 'compra'), ('produccion', 'produccion'), ('contenido_redes', 'contenido_redes'), ('riesgo', 'riesgo')], db_comment='Tipo')
    titulo = models.CharField(max_length=200, db_comment='Título')
    descripcion = models.TextField(db_comment='Qué hacer y por qué')
    evidencia = models.JSONField(db_comment='Datos que la sustentan')
    indicador = models.CharField(max_length=120, null=True, blank=True, db_comment='Indicador que debería mejorar')
    prioridad = models.CharField(max_length=5, choices=[('alta', 'alta'), ('media', 'media'), ('baja', 'baja')], db_comment='Prioridad')
    estado = models.CharField(max_length=12, choices=[('nueva', 'nueva'), ('aceptada', 'aceptada'), ('descartada', 'descartada'), ('en_ejecucion', 'en_ejecucion'), ('cumplida', 'cumplida')], db_default='nueva', db_comment='Situación')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    fecha_limite = models.DateField(null=True, blank=True, db_comment='Plazo')
    resultado = models.TextField(null=True, blank=True, db_comment='Qué pasó al ejecutarla (aprendizaje)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "recomendacion" (las comillas separan esquema y tabla)
        db_table = 'ia"."recomendacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Plan de acción o mejora continua propuesto por un agente analista, con su seguimiento (ciclo PHVA).'


# ==============================================================================================================
# Tabla ia.evaluacion_respuesta  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/evaluaciones-respuesta/
# ==============================================================================================================
class EvaluacionRespuesta(models.Model):
    """Calificación de una respuesta de un agente por el cliente o el administrador; alimenta la mejora de instrucciones y conocimiento."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, db_comment='Agente evaluado')
    mensaje_ref = models.CharField(max_length=24, db_comment='Id del mensaje en MongoDB')
    origen = models.CharField(max_length=21, choices=[('cliente', 'cliente'), ('administrador', 'administrador'), ('evaluacion_automatica', 'evaluacion_automatica')], db_comment='Quién califica')
    calificacion = models.SmallIntegerField(db_comment='De 1 a 5')
    motivo = models.CharField(max_length=10, choices=[('correcta', 'correcta'), ('incorrecta', 'incorrecta'), ('incompleta', 'incompleta'), ('tono', 'tono'), ('demora', 'demora'), ('otro', 'otro')], null=True, blank=True, db_comment='Motivo')
    comentario = models.TextField(null=True, blank=True, db_comment='Comentario')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "evaluacion_respuesta" (las comillas separan esquema y tabla)
        db_table = 'ia"."evaluacion_respuesta'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Calificación de una respuesta de un agente por el cliente o el administrador; alimenta la mejora de instrucciones y conocimiento.'


# ==============================================================================================================
# Tabla ia.consumo_ia  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/consumos/
# ==============================================================================================================
class ConsumoIa(models.Model):
    """Tokens y costo por agente, modelo y día, para controlar el gasto."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, db_comment='Agente')
    fecha = models.DateField(db_comment='Día')
    proveedor_modelo = models.CharField(max_length=40, db_comment='Proveedor')
    modelo = models.CharField(max_length=60, db_comment='Modelo')
    solicitudes = models.IntegerField(db_default=0, db_comment='Llamadas')
    tokens_entrada = models.BigIntegerField(db_default=0, db_comment='Tokens enviados')
    tokens_salida = models.BigIntegerField(db_default=0, db_comment='Tokens generados')
    costo_usd = models.DecimalField(max_digits=10, decimal_places=4, db_default=0, db_comment='Costo en dólares')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "consumo_ia" (las comillas separan esquema y tabla)
        db_table = 'ia"."consumo_ia'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Tokens y costo por agente, modelo y día, para controlar el gasto.'


# ==============================================================================================================
# Tabla ia.regla_conversacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/reglas-conversacion/
# ==============================================================================================================
class ReglaConversacion(models.Model):
    """Guardia del orquestador: temas permitidos, temas que se rechazan con cortesía y casos que pasan a una persona."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=21, choices=[('tema_permitido', 'tema_permitido'), ('tema_fuera_de_alcance', 'tema_fuera_de_alcance'), ('escalar_a_humano', 'escalar_a_humano'), ('dato_prohibido', 'dato_prohibido')], db_comment='Clase de regla')
    descripcion = models.TextField(db_comment='Qué cubre, en lenguaje claro')
    ejemplos = models.JSONField(null=True, blank=True, db_comment='Frases de ejemplo para el clasificador')
    respuesta_plantilla = models.TextField(null=True, blank=True, db_comment='Texto de respuesta (ej. cortesía al rechazar un tema ajeno a la finca)')
    prioridad_escalamiento = models.CharField(max_length=5, choices=[('alta', 'alta'), ('media', 'media'), ('baja', 'baja')], null=True, blank=True, db_comment='Si escala, con qué prioridad')
    activa = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "regla_conversacion" (las comillas separan esquema y tabla)
        db_table = 'ia"."regla_conversacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Guardia del orquestador: temas permitidos, temas que se rechazan con cortesía y casos que pasan a una persona.'


# ==============================================================================================================
# Tabla ia.escalamiento  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/escalamientos/
# ==============================================================================================================
class Escalamiento(models.Model):
    """Conversación pasada a una persona: motivo, quién la atiende y hasta cuándo se puede responder según la ventana del canal."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    conversacion_ref = models.CharField(max_length=24, db_comment='Conversación en MongoDB')
    canal = models.CharField(max_length=20, db_comment='Canal (whatsapp, instagram, ...)')
    motivo = models.CharField(max_length=26, choices=[('solicitud_cliente', 'solicitud_cliente'), ('queja', 'queja'), ('fuera_de_alcance', 'fuera_de_alcance'), ('sin_respuesta_conocimiento', 'sin_respuesta_conocimiento'), ('pedido_grande', 'pedido_grande'), ('pago', 'pago'), ('error_agente', 'error_agente')], db_comment='Por qué escaló')
    prioridad = models.CharField(max_length=5, choices=[('alta', 'alta'), ('media', 'media'), ('baja', 'baja')], db_comment='Prioridad')
    asignado_a = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='asignado_a', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona que atiende')
    estado = models.CharField(max_length=11, choices=[('pendiente', 'pendiente'), ('en_atencion', 'en_atencion'), ('resuelto', 'resuelto'), ('vencido', 'vencido')], db_default='pendiente', db_comment='Situación; vencido = se cerró la ventana sin respuesta')
    responder_antes_de = models.DateTimeField(db_comment='Límite según la ventana del canal (incluye la extensión de agente humano cuando aplica)')
    atendido_en = models.DateTimeField(null=True, blank=True, db_comment='Primera respuesta de la persona')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "escalamiento" (las comillas separan esquema y tabla)
        db_table = 'ia"."escalamiento'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Conversación pasada a una persona: motivo, quién la atiende y hasta cuándo se puede responder según la ventana del canal.'


# ==============================================================================================================
# Tabla ia.modelo_pronostico  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/modelos-pronostico/
# ==============================================================================================================
class ModeloPronostico(models.Model):
    """Modelo de pronóstico de demanda entrenado; gana el de menor error (necesita al menos 12 meses de ventas)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    algoritmo = models.CharField(max_length=15, choices=[('base_estacional', 'base_estacional'), ('promedio_movil', 'promedio_movil'), ('ets', 'ets'), ('prophet', 'prophet'), ('otro', 'otro')], db_comment='Algoritmo')
    version = models.CharField(max_length=20, db_comment='Versión')
    entrenado_en = models.DateTimeField(db_comment='Cuándo se entrenó')
    meses_historia = models.SmallIntegerField(db_comment='Meses de ventas usados')
    error_mape = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, db_comment='Error porcentual medio en la validación')
    activo = models.BooleanField(db_default=False, db_comment='Modelo en uso para ese producto')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "modelo_pronostico" (las comillas separan esquema y tabla)
        db_table = 'ia"."modelo_pronostico'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Modelo de pronóstico de demanda entrenado; gana el de menor error (necesita al menos 12 meses de ventas).'


# ==============================================================================================================
# Tabla ia.pronostico_demanda  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/pronosticos-demanda/
# ==============================================================================================================
class PronosticoDemanda(models.Model):
    """Cantidad esperada de venta por producto y periodo, con su rango."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    modelo_pronostico = models.ForeignKey('ia.ModeloPronostico', models.DO_NOTHING, db_column='modelo_pronostico_id', related_name='+', db_constraint=False, db_comment='Modelo')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    periodo_inicio = models.DateField(db_comment='Inicio')
    periodo_fin = models.DateField(db_comment='Fin')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad esperada')
    limite_inferior = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Rango bajo')
    limite_superior = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Rango alto')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "pronostico_demanda" (las comillas separan esquema y tabla)
        db_table = 'ia"."pronostico_demanda'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cantidad esperada de venta por producto y periodo, con su rango.'


# ==============================================================================================================
# Tabla ia.diagnostico_imagen  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/diagnosticos-imagen/
# ==============================================================================================================
class DiagnosticoImagen(models.Model):
    """Foto de hoja, fruto o animal analizada por el agente Agrónomo. Es una propuesta: no crea compras ni aplicaciones; la confirma una persona."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, db_comment='Agente')
    foto_url = models.CharField(max_length=300, db_comment='Foto')
    objetivo = models.CharField(max_length=6, choices=[('hoja', 'hoja'), ('fruto', 'fruto'), ('tallo', 'tallo'), ('animal', 'animal'), ('huevo', 'huevo'), ('otro', 'otro')], db_comment='Qué se fotografió')
    siembra = models.ForeignKey('produccion.Siembra', models.DO_NOTHING, db_column='siembra_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Siembra')
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Lote')
    tomada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='tomada_por', related_name='+', db_constraint=False, db_comment='Quién la tomó')
    diagnostico_propuesto = models.CharField(max_length=150, null=True, blank=True, db_comment='Plaga o enfermedad probable')
    confianza = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True, db_comment='Confianza del modelo (0 a 1)')
    resultado = models.JSONField(null=True, blank=True, db_comment='Alternativas y fotos parecidas')
    estado = models.CharField(max_length=10, choices=[('pendiente', 'pendiente'), ('confirmado', 'confirmado'), ('corregido', 'corregido'), ('descartado', 'descartado')], db_default='pendiente', db_comment='Revisión humana')
    diagnostico_final = models.CharField(max_length=150, null=True, blank=True, db_comment='Lo que decidió el agrónomo o el veterinario')
    revisado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='revisado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién revisó')
    revisado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
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
        # Nombre real en PostgreSQL: esquema "ia", tabla "diagnostico_imagen" (las comillas separan esquema y tabla)
        db_table = 'ia"."diagnostico_imagen'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Foto de hoja, fruto o animal analizada por el agente Agrónomo. Es una propuesta: no crea compras ni aplicaciones; la confirma una persona.'


# ==============================================================================================================
# Tabla ia.escenario  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/escenarios/
# ==============================================================================================================
class Escenario(models.Model):
    """Simulación "qué pasa si" (sube el concentrado 10 %, se pasa de 100 a 500 gallinas, cae la postura)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=150, db_comment='Nombre')
    supuestos = models.JSONField(db_comment='Variables y valores supuestos')
    resultado = models.JSONField(null=True, blank=True, db_comment='Resultado (margen, caja, punto de equilibrio)')
    creado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='creado_por', related_name='+', db_constraint=False, db_comment='Quién')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente que lo preparó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "escenario" (las comillas separan esquema y tabla)
        db_table = 'ia"."escenario'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Simulación "qué pasa si" (sube el concentrado 10 %, se pasa de 100 a 500 gallinas, cae la postura).'


# ==============================================================================================================
# Tabla ia.decision  ·  por finca (seguridad por filas)  ·  API: /api/v1/ia/decisiones/
# ==============================================================================================================
class Decision(models.Model):
    """Registro de decisiones: contexto, opciones, evidencia, quién decidió y, después, el resultado. Memoria de la finca."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    titulo = models.CharField(max_length=200, db_comment='Decisión')
    contexto = models.TextField(db_comment='Situación')
    opciones = models.JSONField(db_comment='Opciones evaluadas')
    evidencia = models.JSONField(null=True, blank=True, db_comment='Cifras y documentos')
    opcion_elegida = models.CharField(max_length=200, null=True, blank=True, db_comment='Lo que se decidió')
    decidido_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='decidido_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién decidió (persona)')
    decidido_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    resultado_esperado = models.TextField(null=True, blank=True, db_comment='Qué se espera')
    revisar_en = models.DateField(null=True, blank=True, db_comment='Cuándo revisar el resultado')
    resultado_real = models.TextField(null=True, blank=True, db_comment='Qué pasó')
    recomendacion = models.ForeignKey('ia.Recomendacion', models.DO_NOTHING, db_column='recomendacion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Recomendación que la originó')
    escenario = models.ForeignKey('ia.Escenario', models.DO_NOTHING, db_column='escenario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Escenario usado')
    iniciativa = models.ForeignKey('estrategia.Iniciativa', models.DO_NOTHING, db_column='iniciativa_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Iniciativa de negocio decidida')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "ia", tabla "decision" (las comillas separan esquema y tabla)
        db_table = 'ia"."decision'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Registro de decisiones: contexto, opciones, evidencia, quién decidió y, después, el resultado. Memoria de la finca.'
