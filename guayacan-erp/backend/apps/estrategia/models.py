"""Modelos del esquema estrategia: Líneas de negocio, DOFA, estudios de mercado, iniciativas de crecimiento, evaluación de proyectos (VPN, TIR, ROI, palancas) y reinversión de utilidades.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «estrategia». Django usa estas clases para leer y escribir
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
# Tabla estrategia.linea_negocio  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/lineas-negocio/
# ==============================================================================================================
class LineaNegocio(models.Model):
    """Línea de negocio de la finca (avícola, piscícola, perennes, turismo…) o una nueva en estudio, unida a su centro de costo."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Centro de costo')
    estado = models.CharField(max_length=10, choices=[('actual', 'actual'), ('en_estudio', 'en_estudio'), ('piloto', 'piloto'), ('descartada', 'descartada'), ('cerrada', 'cerrada')], db_default='actual', db_comment='Estado')
    palanca_dominante = models.CharField(max_length=11, choices=[('mercadeo', 'mercadeo'), ('produccion', 'produccion'), ('operacional', 'operacional'), ('financiera', 'financiera')], null=True, blank=True, db_comment='Palanca con la que genera recursos')
    descripcion = models.TextField(null=True, blank=True, db_comment='Descripción')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "linea_negocio" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."linea_negocio'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Línea de negocio de la finca (avícola, piscícola, perennes, turismo…) o una nueva en estudio, unida a su centro de costo.'


# ==============================================================================================================
# Tabla estrategia.factor_dofa  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/factores-dofa/
# ==============================================================================================================
class FactorDofa(models.Model):
    """Debilidad, oportunidad, fortaleza o amenaza de la finca o de una línea, con su fuente."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=11, choices=[('debilidad', 'debilidad'), ('oportunidad', 'oportunidad'), ('fortaleza', 'fortaleza'), ('amenaza', 'amenaza')], db_comment='Tipo')
    linea_negocio = models.ForeignKey('estrategia.LineaNegocio', models.DO_NOTHING, db_column='linea_negocio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Línea (vacío = toda la finca)')
    descripcion = models.TextField(db_comment='Descripción')
    impacto = models.SmallIntegerField(db_comment='Impacto 1 a 5')
    fuente = models.CharField(max_length=200, null=True, blank=True, db_comment='Fuente')
    vigente = models.BooleanField(db_default=True, db_comment='Vigente')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "factor_dofa" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."factor_dofa'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Debilidad, oportunidad, fortaleza o amenaza de la finca o de una línea, con su fuente.'


# ==============================================================================================================
# Tabla estrategia.estudio_mercado  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/estudios-mercado/
# ==============================================================================================================
class EstudioMercado(models.Model):
    """Dato de un mercado posible: tamaño, precio de referencia, competidores y fuente (SIPSA, DANE, gremios, visitas)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    mercado = models.CharField(max_length=150, db_comment='Mercado, ej. huevo campesino en hoteles de Girardot')
    segmento = models.ForeignKey('crm.Segmento', models.DO_NOTHING, db_column='segmento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Segmento')
    tamano_estimado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Ventas anuales estimadas del mercado')
    precio_referencia = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Precio de referencia')
    competidores = models.TextField(null=True, blank=True, db_comment='Competidores')
    barreras = models.TextField(null=True, blank=True, db_comment='Barreras de entrada (registros, certificaciones, frío)')
    fuente = models.CharField(max_length=200, db_comment='Fuente')
    fecha = models.DateField(db_comment='Fecha del dato')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "estudio_mercado" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."estudio_mercado'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Dato de un mercado posible: tamaño, precio de referencia, competidores y fuente (SIPSA, DANE, gremios, visitas).'


# ==============================================================================================================
# Tabla estrategia.iniciativa  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/iniciativas/
# ==============================================================================================================
class Iniciativa(models.Model):
    """Idea de crecimiento: nuevo mercado, producto, canal o negocio, clasificada por la matriz de Ansoff y por la palanca que usa. La IA puede proponerla; decide la familia."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    titulo = models.CharField(max_length=200, db_comment='Título')
    descripcion = models.TextField(db_comment='Descripción')
    ansoff = models.CharField(max_length=19, choices=[('penetracion_mercado', 'penetracion_mercado'), ('desarrollo_mercado', 'desarrollo_mercado'), ('desarrollo_producto', 'desarrollo_producto'), ('diversificacion', 'diversificacion')], db_comment='Cuadrante de la matriz de Ansoff')
    tipo = models.CharField(max_length=20, choices=[('nuevo_mercado', 'nuevo_mercado'), ('nuevo_producto', 'nuevo_producto'), ('nuevo_canal', 'nuevo_canal'), ('nueva_linea', 'nueva_linea'), ('valor_agregado', 'valor_agregado'), ('integracion_vertical', 'integracion_vertical'), ('mejora_proceso', 'mejora_proceso')], db_comment='Tipo')
    palanca = models.CharField(max_length=11, choices=[('mercadeo', 'mercadeo'), ('produccion', 'produccion'), ('operacional', 'operacional'), ('financiera', 'financiera')], db_comment='Palanca principal')
    linea_negocio = models.ForeignKey('estrategia.LineaNegocio', models.DO_NOTHING, db_column='linea_negocio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Línea existente o nueva')
    segmento = models.ForeignKey('crm.Segmento', models.DO_NOTHING, db_column='segmento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Segmento al que apunta')
    hipotesis = models.TextField(null=True, blank=True, db_comment='Qué se cree y cómo se probará')
    estado = models.CharField(max_length=13, choices=[('idea', 'idea'), ('en_evaluacion', 'en_evaluacion'), ('aprobada', 'aprobada'), ('piloto', 'piloto'), ('escalada', 'escalada'), ('descartada', 'descartada')], db_default='idea', db_comment='Estado')
    propuesta_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='propuesta_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la propuso')
    agente = models.ForeignKey('ia.Agente', models.DO_NOTHING, db_column='agente_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Agente que la propuso')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó (persona)')
    aprobada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    puntaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Puntaje de priorización')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "iniciativa" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."iniciativa'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Idea de crecimiento: nuevo mercado, producto, canal o negocio, clasificada por la matriz de Ansoff y por la palanca que usa. La IA puede proponerla; decide la familia.'


# ==============================================================================================================
# Tabla estrategia.evaluacion_proyecto  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/evaluaciones-proyecto/
# ==============================================================================================================
class EvaluacionProyecto(models.Model):
    """Evaluación financiera de una iniciativa: inversión, flujos, VPN, TIR, ROI, recuperación, punto de equilibrio, margen de seguridad y grados de palanca. La calcula la base."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    iniciativa = models.ForeignKey('estrategia.Iniciativa', models.DO_NOTHING, db_column='iniciativa_id', related_name='+', db_constraint=False, db_comment='Iniciativa')
    version = models.SmallIntegerField(db_default=1, db_comment='Versión')
    inversion_inicial = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Inversión inicial')
    horizonte_meses = models.SmallIntegerField(db_comment='Horizonte')
    tasa_descuento_anual = models.DecimalField(max_digits=6, decimal_places=4, db_comment='Costo de capital (tasa de oportunidad) anual')
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Precio de venta por unidad')
    costo_variable_unitario = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Costo variable por unidad')
    costos_fijos_mes = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Costos fijos operacionales del mes')
    intereses_mes = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Intereses del mes si se financia con deuda')
    unidades_mes = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Unidades esperadas por mes')
    fuente_fondos = models.CharField(max_length=20, choices=[('utilidades_retenidas', 'utilidades_retenidas'), ('credito', 'credito'), ('fondo_emprender', 'fondo_emprender'), ('aporte_familia', 'aporte_familia'), ('mixto', 'mixto')], db_comment='De dónde sale la plata')
    vpn = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Valor presente neto')
    tir_anual = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, db_comment='Tasa interna de retorno anual')
    roi_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, db_comment='Retorno sobre la inversión en el horizonte')
    recuperacion_meses = models.SmallIntegerField(null=True, blank=True, db_comment='Meses para recuperar la inversión')
    punto_equilibrio_unidades = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Unidades por mes para no perder')
    margen_seguridad_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, db_comment='Cuánto pueden caer las ventas sin pérdida')
    gpo = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, db_comment='Grado de palanca operativa')
    gpf = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, db_comment='Grado de palanca financiera')
    gpt = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, db_comment='Grado de palanca total')
    riesgos = models.TextField(null=True, blank=True, db_comment='Riesgos (costos fijos, deuda, precio)')
    calculado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se calculó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "evaluacion_proyecto" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."evaluacion_proyecto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Evaluación financiera de una iniciativa: inversión, flujos, VPN, TIR, ROI, recuperación, punto de equilibrio, margen de seguridad y grados de palanca. La calcula la base.'


# ==============================================================================================================
# Tabla estrategia.flujo_proyecto  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/evaluaciones-proyecto/{id}/flujos/
# ==============================================================================================================
class FlujoProyecto(models.Model):
    """Flujo de caja proyectado de una evaluación por mes (mes 0 = inversión)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    evaluacion = models.ForeignKey('estrategia.EvaluacionProyecto', models.DO_NOTHING, db_column='evaluacion_id', related_name='+', db_constraint=False, db_comment='Evaluación')
    mes = models.SmallIntegerField(db_comment='Mes (0 = inversión)')
    ingresos = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Ingresos')
    egresos = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Egresos')
    inversion = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Inversión')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "flujo_proyecto" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."flujo_proyecto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Flujo de caja proyectado de una evaluación por mes (mes 0 = inversión).'


# ==============================================================================================================
# Tabla estrategia.reinversion  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/reinversiones/
# ==============================================================================================================
class Reinversion(models.Model):
    """Parte de la utilidad de una línea que se destina a una iniciativa (apalancarse con lo ganado). Nunca de una línea con pérdida ni por encima del tope de reinversión."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    anio = models.SmallIntegerField(db_comment='Año de la utilidad')
    mes = models.SmallIntegerField(db_comment='Mes de la utilidad')
    linea_origen = models.ForeignKey('estrategia.LineaNegocio', models.DO_NOTHING, db_column='linea_origen_id', related_name='+', db_constraint=False, db_comment='Línea que generó la utilidad')
    utilidad_linea = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Utilidad neta de la línea en el mes (de la contabilidad)')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor reinvertido')
    iniciativa = models.ForeignKey('estrategia.Iniciativa', models.DO_NOTHING, db_column='iniciativa_id', related_name='+', db_constraint=False, db_comment='Iniciativa destino')
    estado = models.CharField(max_length=9, choices=[('propuesta', 'propuesta'), ('aprobada', 'aprobada'), ('ejecutada', 'ejecutada'), ('cancelada', 'cancelada')], db_default='propuesta', db_comment='Estado')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la aprobó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "reinversion" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."reinversion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Parte de la utilidad de una línea que se destina a una iniciativa (apalancarse con lo ganado). Nunca de una línea con pérdida ni por encima del tope de reinversión.'


# ==============================================================================================================
# Tabla estrategia.seguimiento_iniciativa  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/seguimientos-iniciativa/
# ==============================================================================================================
class SeguimientoIniciativa(models.Model):
    """Resultado real mes a mes de una iniciativa en piloto o escalada, contra lo proyectado: así se mide el retorno de verdad."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    iniciativa = models.ForeignKey('estrategia.Iniciativa', models.DO_NOTHING, db_column='iniciativa_id', related_name='+', db_constraint=False, db_comment='Iniciativa')
    mes = models.DateField(db_comment='Mes')
    ingresos_reales = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Ingresos')
    egresos_reales = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Egresos')
    unidades_reales = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Unidades')
    nota = models.TextField(null=True, blank=True, db_comment='Aprendizajes')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "seguimiento_iniciativa" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."seguimiento_iniciativa'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Resultado real mes a mes de una iniciativa en piloto o escalada, contra lo proyectado: así se mide el retorno de verdad.'


# ==============================================================================================================
# Tabla estrategia.objetivo  ·  por finca (seguridad por filas)  ·  API: /api/v1/estrategia/objetivos/
# ==============================================================================================================
class Objetivo(models.Model):
    """Objetivo estratégico por perspectiva del cuadro de mando (financiera, clientes, procesos, aprendizaje), con indicador y meta."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    perspectiva = models.CharField(max_length=11, choices=[('financiera', 'financiera'), ('clientes', 'clientes'), ('procesos', 'procesos'), ('aprendizaje', 'aprendizaje')], db_comment='Perspectiva')
    descripcion = models.TextField(db_comment='Objetivo')
    indicador = models.ForeignKey('finanzas.Indicador', models.DO_NOTHING, db_column='indicador_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Indicador')
    meta = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, db_comment='Meta')
    fecha_meta = models.DateField(null=True, blank=True, db_comment='Para cuándo')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "estrategia", tabla "objetivo" (las comillas separan esquema y tabla)
        db_table = 'estrategia"."objetivo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Objetivo estratégico por perspectiva del cuadro de mando (financiera, clientes, procesos, aprendizaje), con indicador y meta.'
