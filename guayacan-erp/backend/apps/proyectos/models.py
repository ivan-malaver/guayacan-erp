"""Modelos del esquema proyectos: Dirección de proyectos (PMBOK 8): acta, interesados, EDT, cronograma con ruta crítica, iteraciones, riesgos, cambios, líneas base y valor ganado.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «proyectos». Django usa estas clases para leer y escribir
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
# Tabla proyectos.proyecto  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/proyectos/
# ==============================================================================================================
class Proyecto(models.Model):
    """Proyecto de la finca (nuevo galpón, sistema solar, cabañas, certificación, piloto de robot) con acta de constitución, enfoque predictivo, adaptativo o híbrido y área de enfoque actual."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. PRY-GAL-500')
    nombre = models.CharField(max_length=200, db_comment='Nombre')
    objetivo = models.TextField(db_comment='Objetivo (resultado y valor esperado)')
    justificacion = models.TextField(null=True, blank=True, db_comment='Por qué (caso de negocio)')
    criterios_exito = models.TextField(null=True, blank=True, db_comment='Cómo se sabrá que salió bien')
    iniciativa = models.ForeignKey('estrategia.Iniciativa', models.DO_NOTHING, db_column='iniciativa_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Iniciativa de negocio que lo origina')
    linea_negocio = models.ForeignKey('estrategia.LineaNegocio', models.DO_NOTHING, db_column='linea_negocio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Línea')
    enfoque = models.CharField(max_length=10, choices=[('predictivo', 'predictivo'), ('adaptativo', 'adaptativo'), ('hibrido', 'hibrido')], db_default='hibrido', db_comment='Enfoque de desarrollo')
    area_enfoque = models.CharField(max_length=17, choices=[('inicio', 'inicio'), ('planificacion', 'planificacion'), ('ejecucion', 'ejecucion'), ('monitoreo_control', 'monitoreo_control'), ('cierre', 'cierre')], db_default='inicio', db_comment='Área de enfoque en que está')
    estado = models.CharField(max_length=10, choices=[('propuesto', 'propuesto'), ('aprobado', 'aprobado'), ('en_curso', 'en_curso'), ('suspendido', 'suspendido'), ('cerrado', 'cerrado'), ('cancelado', 'cancelado')], db_default='propuesto', db_comment='Estado')
    patrocinador = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='patrocinador_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Patrocinador (quien aprueba y responde por el valor)')
    director = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='director_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Director del proyecto')
    presupuesto = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Presupuesto al concluir (BAC) de la línea base vigente')
    fuente_fondos = models.CharField(max_length=20, choices=[('utilidades_retenidas', 'utilidades_retenidas'), ('credito', 'credito'), ('fondo_emprender', 'fondo_emprender'), ('aporte_familia', 'aporte_familia'), ('convenio', 'convenio'), ('mixto', 'mixto')], null=True, blank=True, db_comment='Financiación')
    inicio_plan = models.DateField(null=True, blank=True, db_comment='Inicio planeado')
    fin_plan = models.DateField(null=True, blank=True, db_comment='Fin planeado')
    inicio_real = models.DateField(null=True, blank=True, db_comment='Inicio real')
    fin_real = models.DateField(null=True, blank=True, db_comment='Fin real')
    acta_documento = models.ForeignKey('documental.Documento', models.DO_NOTHING, db_column='acta_documento_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Acta de constitución firmada')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo aprobó')
    aprobado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "proyecto" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."proyecto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Proyecto de la finca (nuevo galpón, sistema solar, cabañas, certificación, piloto de robot) con acta de constitución, enfoque predictivo, adaptativo o híbrido y área de enfoque actual.'


# ==============================================================================================================
# Tabla proyectos.interesado  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/interesados/
# ==============================================================================================================
class Interesado(models.Model):
    """Interesado del proyecto con su interés, influencia y estrategia de relación (dominio de interesados)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Persona o entidad')
    usuario = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='usuario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Usuario interno')
    nombre = models.CharField(max_length=150, db_comment='Nombre o rol')
    rol = models.CharField(max_length=80, null=True, blank=True, db_comment='Rol en el proyecto')
    interes = models.SmallIntegerField(db_comment='Interés 1 a 5')
    influencia = models.SmallIntegerField(db_comment='Influencia 1 a 5')
    estrategia = models.CharField(max_length=30, null=True, blank=True, db_comment='gestionar_de_cerca, mantener_satisfecho, mantener_informado o monitorear (la calcula la base)')
    expectativas = models.TextField(null=True, blank=True, db_comment='Qué espera')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "interesado" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."interesado'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Interesado del proyecto con su interés, influencia y estrategia de relación (dominio de interesados).'


# ==============================================================================================================
# Tabla proyectos.elemento_edt  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/elementos-edt/
# ==============================================================================================================
class ElementoEdt(models.Model):
    """Estructura de desglose del trabajo (EDT): entregables y paquetes de trabajo con su criterio de aceptación."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    padre = models.ForeignKey('proyectos.ElementoEdt', models.DO_NOTHING, db_column='padre_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Elemento superior')
    codigo = models.CharField(max_length=20, db_comment='Código EDT, ej. 1.2.3')
    nombre = models.CharField(max_length=200, db_comment='Nombre')
    es_entregable = models.BooleanField(db_default=False, db_comment='Es un entregable que se acepta')
    criterio_aceptacion = models.TextField(null=True, blank=True, db_comment='Cómo se acepta')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('en_curso', 'en_curso'), ('terminado', 'terminado'), ('aceptado', 'aceptado'), ('rechazado', 'rechazado')], db_default='pendiente', db_comment='Estado')
    aceptado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aceptado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo aceptó')
    aceptado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "elemento_edt" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."elemento_edt'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Estructura de desglose del trabajo (EDT): entregables y paquetes de trabajo con su criterio de aceptación.'


# ==============================================================================================================
# Tabla proyectos.iteracion  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/iteraciones/
# ==============================================================================================================
class Iteracion(models.Model):
    """Iteración o sprint para la parte adaptativa del proyecto."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    numero = models.SmallIntegerField(db_comment='Número')
    objetivo = models.TextField(null=True, blank=True, db_comment='Objetivo de la iteración')
    inicio = models.DateField(db_comment='Inicio')
    fin = models.DateField(db_comment='Fin')
    estado = models.CharField(max_length=8, choices=[('planeada', 'planeada'), ('en_curso', 'en_curso'), ('cerrada', 'cerrada')], db_default='planeada', db_comment='Estado')
    retrospectiva = models.TextField(null=True, blank=True, db_comment='Qué se aprendió')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "iteracion" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."iteracion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Iteración o sprint para la parte adaptativa del proyecto.'


# ==============================================================================================================
# Tabla proyectos.actividad  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/actividades/
# ==============================================================================================================
class Actividad(models.Model):
    """Actividad del cronograma (o historia de la iteración) con duración, fechas, avance, costo y responsable; la ruta crítica la calcula la base."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    elemento_edt = models.ForeignKey('proyectos.ElementoEdt', models.DO_NOTHING, db_column='elemento_edt_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Paquete de trabajo')
    iteracion = models.ForeignKey('proyectos.Iteracion', models.DO_NOTHING, db_column='iteracion_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Iteración')
    codigo = models.CharField(max_length=20, db_comment='Código')
    nombre = models.CharField(max_length=200, db_comment='Nombre')
    es_hito = models.BooleanField(db_default=False, db_comment='Hito (duración 0)')
    duracion_dias = models.SmallIntegerField(db_comment='Duración en días')
    inicio_temprano = models.SmallIntegerField(null=True, blank=True, db_comment='Día de inicio temprano (CPM, desde el día 0)')
    fin_temprano = models.SmallIntegerField(null=True, blank=True, db_comment='Día de fin temprano')
    inicio_tardio = models.SmallIntegerField(null=True, blank=True, db_comment='Día de inicio tardío')
    fin_tardio = models.SmallIntegerField(null=True, blank=True, db_comment='Día de fin tardío')
    holgura = models.SmallIntegerField(null=True, blank=True, db_comment='Holgura total en días')
    critica = models.BooleanField(db_default=False, db_comment='Está en la ruta crítica')
    inicio_plan = models.DateField(null=True, blank=True, db_comment='Inicio planeado')
    fin_plan = models.DateField(null=True, blank=True, db_comment='Fin planeado')
    inicio_real = models.DateField(null=True, blank=True, db_comment='Inicio real')
    fin_real = models.DateField(null=True, blank=True, db_comment='Fin real')
    avance_pct = models.DecimalField(max_digits=5, decimal_places=2, db_default=0, db_comment='Avance físico')
    costo_plan = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Costo planeado')
    costo_real = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Costo real')
    responsable = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    area = models.ForeignKey('personal.AreaResponsabilidad', models.DO_NOTHING, db_column='area_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Área de responsabilidad')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea de campo que la ejecuta')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "actividad" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."actividad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Actividad del cronograma (o historia de la iteración) con duración, fechas, avance, costo y responsable; la ruta crítica la calcula la base.'


# ==============================================================================================================
# Tabla proyectos.dependencia  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/actividades/{id}/dependencias/
# ==============================================================================================================
class Dependencia(models.Model):
    """Relación entre actividades (fin a comienzo, comienzo a comienzo, fin a fin, comienzo a fin) con adelanto o retraso."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    predecesora = models.ForeignKey('proyectos.Actividad', models.DO_NOTHING, db_column='predecesora_id', related_name='+', db_constraint=False, db_comment='Actividad predecesora')
    sucesora = models.ForeignKey('proyectos.Actividad', models.DO_NOTHING, db_column='sucesora_id', related_name='+', db_constraint=False, db_comment='Actividad sucesora')
    tipo = models.CharField(max_length=2, choices=[('FC', 'FC'), ('CC', 'CC'), ('FF', 'FF'), ('CF', 'CF')], db_default='FC', db_comment='Tipo de relación')
    desfase_dias = models.SmallIntegerField(db_default=0, db_comment='Adelanto (negativo) o retraso (positivo)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "dependencia" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."dependencia'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Relación entre actividades (fin a comienzo, comienzo a comienzo, fin a fin, comienzo a fin) con adelanto o retraso.'


# ==============================================================================================================
# Tabla proyectos.riesgo  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/riesgos/
# ==============================================================================================================
class Riesgo(models.Model):
    """Riesgo del proyecto (amenaza u oportunidad) con probabilidad, impacto, respuesta y responsable."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    descripcion = models.TextField(db_comment='Causa, riesgo y efecto')
    tipo = models.CharField(max_length=11, choices=[('amenaza', 'amenaza'), ('oportunidad', 'oportunidad')], db_default='amenaza', db_comment='Tipo')
    categoria = models.CharField(max_length=10, choices=[('tecnico', 'tecnico'), ('clima', 'clima'), ('sanitario', 'sanitario'), ('mercado', 'mercado'), ('financiero', 'financiero'), ('legal', 'legal'), ('personas', 'personas'), ('proveedor', 'proveedor'), ('seguridad', 'seguridad')], db_comment='Categoría')
    probabilidad = models.SmallIntegerField(db_comment='1 a 5')
    impacto = models.SmallIntegerField(db_comment='1 a 5')
    severidad = models.GeneratedField(expression=models.F('probabilidad') * models.F('impacto'), output_field=models.SmallIntegerField(), db_persist=True, db_comment='Probabilidad × impacto (1 a 25)')
    respuesta = models.CharField(max_length=10, choices=[('evitar', 'evitar'), ('mitigar', 'mitigar'), ('transferir', 'transferir'), ('aceptar', 'aceptar'), ('escalar', 'escalar'), ('explotar', 'explotar'), ('mejorar', 'mejorar'), ('compartir', 'compartir')], null=True, blank=True, db_comment='Estrategia de respuesta')
    plan_respuesta = models.TextField(null=True, blank=True, db_comment='Qué se hará')
    disparador = models.CharField(max_length=200, null=True, blank=True, db_comment='Señal de que se está materializando')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Dueño del riesgo')
    estado = models.CharField(max_length=13, choices=[('identificado', 'identificado'), ('en_respuesta', 'en_respuesta'), ('materializado', 'materializado'), ('cerrado', 'cerrado')], db_default='identificado', db_comment='Estado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "riesgo" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."riesgo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Riesgo del proyecto (amenaza u oportunidad) con probabilidad, impacto, respuesta y responsable.'


# ==============================================================================================================
# Tabla proyectos.registro  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/registros/
# ==============================================================================================================
class Registro(models.Model):
    """Registro de incidentes, supuestos, restricciones, decisiones y lecciones aprendidas del proyecto."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    tipo = models.CharField(max_length=17, choices=[('incidente', 'incidente'), ('supuesto', 'supuesto'), ('restriccion', 'restriccion'), ('decision', 'decision'), ('leccion_aprendida', 'leccion_aprendida')], db_comment='Tipo')
    descripcion = models.TextField(db_comment='Descripción')
    responsable = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='responsable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Responsable')
    estado = models.CharField(max_length=7, choices=[('abierto', 'abierto'), ('cerrado', 'cerrado')], db_default='abierto', db_comment='Estado')
    fecha = models.DateField(db_default=sql('current_date'), db_comment='Fecha')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "registro" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."registro'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Registro de incidentes, supuestos, restricciones, decisiones y lecciones aprendidas del proyecto.'


# ==============================================================================================================
# Tabla proyectos.solicitud_cambio  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/solicitudes-cambio/
# ==============================================================================================================
class SolicitudCambio(models.Model):
    """Solicitud de cambio al alcance, cronograma o costo; la aprueba una persona distinta de quien la pide y, si se aprueba, crea una nueva línea base."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    descripcion = models.TextField(db_comment='Qué cambia y por qué')
    solicitada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='solicitada_por', related_name='+', db_constraint=False, db_comment='Quién la pide')
    impacto_alcance = models.TextField(null=True, blank=True, db_comment='Impacto en el alcance')
    impacto_dias = models.SmallIntegerField(db_default=0, db_comment='Días que agrega o quita')
    impacto_costo = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Costo que agrega o quita')
    estado = models.CharField(max_length=9, choices=[('propuesta', 'propuesta'), ('aprobada', 'aprobada'), ('rechazada', 'rechazada')], db_default='propuesta', db_comment='Estado')
    decidida_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='decidida_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién decidió')
    decidida_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "solicitud_cambio" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."solicitud_cambio'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Solicitud de cambio al alcance, cronograma o costo; la aprueba una persona distinta de quien la pide y, si se aprueba, crea una nueva línea base.'


# ==============================================================================================================
# Tabla proyectos.linea_base  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/lineas-base/
# ==============================================================================================================
class LineaBase(models.Model):
    """Línea base aprobada de alcance, cronograma y costo; no se edita: cada cambio aprobado crea una versión nueva."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    version = models.SmallIntegerField(db_comment='Versión')
    presupuesto = models.DecimalField(max_digits=14, decimal_places=2, db_comment='BAC')
    fin_plan = models.DateField(db_comment='Fecha de fin')
    alcance = models.TextField(db_comment='Resumen del alcance')
    solicitud_cambio = models.ForeignKey('proyectos.SolicitudCambio', models.DO_NOTHING, db_column='solicitud_cambio_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cambio que la originó')
    aprobada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobada_por', related_name='+', db_constraint=False, db_comment='Quién la aprobó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "linea_base" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."linea_base'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Línea base aprobada de alcance, cronograma y costo; no se edita: cada cambio aprobado crea una versión nueva.'


# ==============================================================================================================
# Tabla proyectos.medicion_valor_ganado  ·  por finca (seguridad por filas)  ·  API: /api/v1/proyectos/mediciones-valor-ganado/
# ==============================================================================================================
class MedicionValorGanado(models.Model):
    """Medición del desempeño en una fecha de corte por valor ganado: PV, EV, AC, CPI, SPI, EAC, ETC y VAC."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proyecto = models.ForeignKey('proyectos.Proyecto', models.DO_NOTHING, db_column='proyecto_id', related_name='+', db_constraint=False, db_comment='Proyecto')
    fecha_corte = models.DateField(db_comment='Fecha de corte')
    pv = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor planificado')
    ev = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor ganado')
    ac = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Costo real')
    cpi = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, db_comment='Índice de desempeño del costo (EV/AC)')
    spi = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, db_comment='Índice de desempeño del cronograma (EV/PV)')
    eac = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Estimación a la conclusión (BAC/CPI)')
    etc = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Estimación hasta concluir (EAC − AC)')
    vac = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Variación a la conclusión (BAC − EAC)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "proyectos", tabla "medicion_valor_ganado" (las comillas separan esquema y tabla)
        db_table = 'proyectos"."medicion_valor_ganado'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Medición del desempeño en una fecha de corte por valor ganado: PV, EV, AC, CPI, SPI, EAC, ETC y VAC.'
