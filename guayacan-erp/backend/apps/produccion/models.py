"""Modelos del esquema produccion: Producción animal (aves, ovinos, caprinos, peces, abejas, lombrices) y agrícola (siembras, labores, cosechas, suelo).

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «produccion». Django usa estas clases para leer y escribir
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
# Tabla produccion.especie  ·  catálogo compartido entre fincas  ·  API: /api/v1/produccion/especies/
# ==============================================================================================================
class Especie(models.Model):
    """Catálogo de especies animales que maneja la finca."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, unique=True, db_comment='Código, ej. gallina, ovino, caprino, tilapia, abeja, lombriz')
    nombre_comun = models.CharField(max_length=80, db_comment='Nombre común')
    nombre_cientifico = models.CharField(max_length=120, null=True, blank=True, db_comment='Nombre científico')
    grupo = models.CharField(max_length=7, choices=[('ave', 'ave'), ('ovino', 'ovino'), ('caprino', 'caprino'), ('pez', 'pez'), ('abeja', 'abeja'), ('lombriz', 'lombriz'), ('otro', 'otro')], db_comment='Grupo productivo')
    manejo_individual = models.BooleanField(db_default=False, db_comment='Si se registra animal por animal (ovinos, caprinos) o solo por lote (aves, peces)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "produccion", tabla "especie" (las comillas separan esquema y tabla)
        db_table = 'produccion"."especie'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Catálogo de especies animales que maneja la finca.'


# ==============================================================================================================
# Tabla produccion.lote_animal  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/lotes-animal/
# ==============================================================================================================
class LoteAnimal(models.Model):
    """Grupo de animales que entra junto y se maneja junto (un lote de 100 gallinas, un ciclo de 1.000 alevinos, un rebaño)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. AV-2026-01')
    especie = models.ForeignKey('produccion.Especie', models.DO_NOTHING, db_column='especie_id', related_name='+', db_constraint=False, db_comment='Especie')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Galpón, aprisco o estanque donde está')
    raza_linea = models.CharField(max_length=80, null=True, blank=True, db_comment='Raza o línea genética')
    proposito = models.CharField(max_length=12, choices=[('postura', 'postura'), ('engorde', 'engorde'), ('cria', 'cria'), ('reproduccion', 'reproduccion'), ('miel', 'miel'), ('humus', 'humus')], db_comment='Para qué se tiene')
    fecha_ingreso = models.DateField(db_comment='Fecha de llegada o nacimiento')
    edad_ingreso_semanas = models.SmallIntegerField(null=True, blank=True, db_comment='Edad al llegar')
    cantidad_inicial = models.IntegerField(db_comment='Animales al ingresar')
    cantidad_actual = models.IntegerField(db_comment='Animales vivos hoy (se actualiza con mortalidad, ventas y nacimientos)')
    costo_ingreso = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Costo total de compra del lote')
    estado = models.CharField(max_length=7, choices=[('activo', 'activo'), ('cerrado', 'cerrado')], db_default='activo', db_comment='Activo o cerrado (vendido o descartado)')
    fecha_cierre = models.DateField(null=True, blank=True, db_comment='Fecha de cierre')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "produccion", tabla "lote_animal" (las comillas separan esquema y tabla)
        db_table = 'produccion"."lote_animal'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Grupo de animales que entra junto y se maneja junto (un lote de 100 gallinas, un ciclo de 1.000 alevinos, un rebaño).'


# ==============================================================================================================
# Tabla produccion.animal  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/animales/
# ==============================================================================================================
class Animal(models.Model):
    """Animal identificado individualmente (ovinos y caprinos), con su genealogía."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, db_comment='Lote o rebaño al que pertenece')
    identificador = models.CharField(max_length=20, db_comment='Número de arete o chapeta')
    sexo = models.CharField(max_length=6, choices=[('hembra', 'hembra'), ('macho', 'macho')], db_comment='Sexo')
    fecha_nacimiento = models.DateField(null=True, blank=True, db_comment='Nacimiento')
    madre = models.ForeignKey('produccion.Animal', models.DO_NOTHING, db_column='madre_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Madre, si nació en la finca')
    padre = models.ForeignKey('produccion.Animal', models.DO_NOTHING, db_column='padre_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Padre, si se conoce')
    estado = models.CharField(max_length=10, choices=[('activo', 'activo'), ('vendido', 'vendido'), ('muerto', 'muerto'), ('descartado', 'descartado')], db_default='activo', db_comment='Situación actual')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "produccion", tabla "animal" (las comillas separan esquema y tabla)
        db_table = 'produccion"."animal'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Animal identificado individualmente (ovinos y caprinos), con su genealogía.'


# ==============================================================================================================
# Tabla produccion.registro_postura  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/registros-postura/
# ==============================================================================================================
class RegistroPostura(models.Model):
    """Huevos recogidos por día y por lote; las categorías por peso se registran en clasificacion_postura."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, db_comment='Lote de gallinas')
    fecha = models.DateField(db_comment='Día de recolección')
    huevos_recogidos = models.IntegerField(db_comment='Total de huevos recogidos en el día')
    huevos_rotos = models.IntegerField(db_default=0, db_comment='Rotos o sucios (no vendibles); la clasificación de los buenos va en clasificacion_postura')
    registrado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='registrado_por', related_name='+', db_constraint=False, db_comment='Quien registró')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "registro_postura" (las comillas separan esquema y tabla)
        db_table = 'produccion"."registro_postura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Huevos recogidos por día y por lote; las categorías por peso se registran en clasificacion_postura.'


# ==============================================================================================================
# Tabla produccion.registro_alimentacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/registros-alimentacion/
# ==============================================================================================================
class RegistroAlimentacion(models.Model):
    """Alimento suministrado a un lote, distinguiendo lo comprado de lo producido en la finca (base para medir el ahorro)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, db_comment='Lote alimentado')
    fecha = models.DateField(db_comment='Día')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Alimento (concentrado, maíz, forraje, lombriz)')
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2, db_comment='Kilogramos suministrados')
    origen = models.CharField(max_length=8, choices=[('comprado', 'comprado'), ('propio', 'propio')], db_comment='Comprado o producido en la finca')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "registro_alimentacion" (las comillas separan esquema y tabla)
        db_table = 'produccion"."registro_alimentacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Alimento suministrado a un lote, distinguiendo lo comprado de lo producido en la finca (base para medir el ahorro).'


# ==============================================================================================================
# Tabla produccion.evento_sanitario  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/eventos-sanitario/
# ==============================================================================================================
class EventoSanitario(models.Model):
    """Vacunas, desparasitaciones, tratamientos, revisiones y muertes."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, db_comment='Lote afectado')
    animal = models.ForeignKey('produccion.Animal', models.DO_NOTHING, db_column='animal_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Animal, si el evento es individual')
    fecha = models.DateField(db_comment='Día')
    tipo = models.CharField(max_length=15, choices=[('vacuna', 'vacuna'), ('desparasitacion', 'desparasitacion'), ('tratamiento', 'tratamiento'), ('revision', 'revision'), ('mortalidad', 'mortalidad'), ('descarte', 'descarte')], db_comment='Tipo de evento')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Medicamento o vacuna usada')
    dosis = models.CharField(max_length=40, null=True, blank=True, db_comment='Dosis aplicada')
    cantidad_afectada = models.IntegerField(db_default=1, db_comment='Animales tratados o muertos')
    causa = models.CharField(max_length=150, null=True, blank=True, db_comment='Diagnóstico o causa probable')
    responsable = models.CharField(max_length=120, null=True, blank=True, db_comment='Quien lo aplicó (operario, veterinario)')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "evento_sanitario" (las comillas separan esquema y tabla)
        db_table = 'produccion"."evento_sanitario'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Vacunas, desparasitaciones, tratamientos, revisiones y muertes.'


# ==============================================================================================================
# Tabla produccion.registro_pesaje  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/registros-pesaje/
# ==============================================================================================================
class RegistroPesaje(models.Model):
    """Pesos de animales o muestras de un lote (corderos, cabritos, tilapia)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    lote_animal = models.ForeignKey('produccion.LoteAnimal', models.DO_NOTHING, db_column='lote_animal_id', related_name='+', db_constraint=False, db_comment='Lote')
    animal = models.ForeignKey('produccion.Animal', models.DO_NOTHING, db_column='animal_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Animal pesado, si es individual')
    fecha = models.DateField(db_comment='Día')
    animales_muestreados = models.IntegerField(db_default=1, db_comment='Cuántos se pesaron')
    peso_promedio_kg = models.DecimalField(max_digits=8, decimal_places=3, db_comment='Peso promedio en kg')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "registro_pesaje" (las comillas separan esquema y tabla)
        db_table = 'produccion"."registro_pesaje'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Pesos de animales o muestras de un lote (corderos, cabritos, tilapia).'


# ==============================================================================================================
# Tabla produccion.evento_reproductivo  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/eventos-reproductivo/
# ==============================================================================================================
class EventoReproductivo(models.Model):
    """Montas, partos, abortos y destetes de ovinos y caprinos."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    hembra = models.ForeignKey('produccion.Animal', models.DO_NOTHING, db_column='hembra_id', related_name='+', db_constraint=False, db_comment='Hembra')
    macho = models.ForeignKey('produccion.Animal', models.DO_NOTHING, db_column='macho_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Macho, en montas')
    tipo = models.CharField(max_length=7, choices=[('monta', 'monta'), ('parto', 'parto'), ('aborto', 'aborto'), ('destete', 'destete')], db_comment='Tipo de evento')
    fecha = models.DateField(db_comment='Día')
    crias_vivas = models.SmallIntegerField(null=True, blank=True, db_comment='Crías vivas (partos)')
    crias_muertas = models.SmallIntegerField(null=True, blank=True, db_comment='Crías muertas (partos)')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "evento_reproductivo" (las comillas separan esquema y tabla)
        db_table = 'produccion"."evento_reproductivo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Montas, partos, abortos y destetes de ovinos y caprinos.'


# ==============================================================================================================
# Tabla produccion.calidad_agua_estanque  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/calidad-agua/
# ==============================================================================================================
class CalidadAguaEstanque(models.Model):
    """Mediciones del agua de los estanques de peces."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Estanque')
    medido_en = models.DateTimeField(db_comment='Fecha y hora')
    oxigeno_mg_l = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Oxígeno disuelto en mg/L')
    temperatura_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, db_comment='Temperatura en °C')
    ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, db_comment='pH')
    amonio_mg_l = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Amonio en mg/L')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "calidad_agua_estanque" (las comillas separan esquema y tabla)
        db_table = 'produccion"."calidad_agua_estanque'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Mediciones del agua de los estanques de peces.'


# ==============================================================================================================
# Tabla produccion.cultivo  ·  catálogo compartido entre fincas  ·  API: /api/v1/produccion/cultivos/
# ==============================================================================================================
class Cultivo(models.Model):
    """Catálogo de cultivos (plátano, cacao, aguacate papelillo, maíz, frijol, calabacín, forrajes)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, unique=True, db_comment='Código, ej. platano, cacao, maiz')
    nombre_comun = models.CharField(max_length=80, db_comment='Nombre común')
    nombre_cientifico = models.CharField(max_length=120, null=True, blank=True, db_comment='Nombre científico')
    tipo_ciclo = models.CharField(max_length=7, choices=[('corto', 'corto'), ('perenne', 'perenne'), ('forraje', 'forraje')], db_comment='Ciclo corto, perenne o forraje')
    dias_a_primera_cosecha = models.IntegerField(null=True, blank=True, db_comment='Días desde la siembra hasta la primera cosecha')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "produccion", tabla "cultivo" (las comillas separan esquema y tabla)
        db_table = 'produccion"."cultivo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Catálogo de cultivos (plátano, cacao, aguacate papelillo, maíz, frijol, calabacín, forrajes).'


# ==============================================================================================================
# Tabla produccion.siembra  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/siembras/
# ==============================================================================================================
class Siembra(models.Model):
    """Una siembra en una zona: cuántas plantas se sembraron y cuántas siguen vivas (ej. 5.000 plátanos previstos, 600 vivos)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Lote de cultivo')
    cultivo = models.ForeignKey('produccion.Cultivo', models.DO_NOTHING, db_column='cultivo_id', related_name='+', db_constraint=False, db_comment='Cultivo')
    variedad = models.CharField(max_length=80, null=True, blank=True, db_comment='Variedad, ej. papelillo, hartón')
    fecha_siembra = models.DateField(db_comment='Fecha de siembra')
    plantas_previstas = models.IntegerField(null=True, blank=True, db_comment='Plantas planeadas')
    plantas_sembradas = models.IntegerField(null=True, blank=True, db_comment='Plantas sembradas')
    plantas_vivas = models.IntegerField(null=True, blank=True, db_comment='Plantas vivas en el último conteo')
    semilla_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_comment='Semilla usada en kg (granos)')
    area_m2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, db_comment='Área sembrada')
    fecha_estimada_cosecha = models.DateField(null=True, blank=True, db_comment='Primera cosecha esperada')
    estado = models.CharField(max_length=13, choices=[('planeada', 'planeada'), ('sembrada', 'sembrada'), ('en_produccion', 'en_produccion'), ('recuperacion', 'recuperacion'), ('perdida', 'perdida'), ('finalizada', 'finalizada')], db_default='sembrada', db_comment='Situación actual')
    observaciones = models.TextField(null=True, blank=True, db_comment='Notas (ej. pérdidas por fenómeno de El Niño)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "produccion", tabla "siembra" (las comillas separan esquema y tabla)
        db_table = 'produccion"."siembra'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Una siembra en una zona: cuántas plantas se sembraron y cuántas siguen vivas (ej. 5.000 plátanos previstos, 600 vivos).'


# ==============================================================================================================
# Tabla produccion.labor_cultural  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/labores-cultural/
# ==============================================================================================================
class LaborCultural(models.Model):
    """Trabajo hecho a una siembra: encalado, fertilización, deshierbe, control de plagas, poda, resiembra."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    siembra = models.ForeignKey('produccion.Siembra', models.DO_NOTHING, db_column='siembra_id', related_name='+', db_constraint=False, db_comment='Siembra')
    fecha = models.DateField(db_comment='Día')
    tipo = models.CharField(max_length=14, choices=[('encalado', 'encalado'), ('fertilizacion', 'fertilizacion'), ('deshierbe', 'deshierbe'), ('control_plagas', 'control_plagas'), ('poda', 'poda'), ('resiembra', 'resiembra'), ('aporque', 'aporque'), ('conteo', 'conteo')], db_comment='Tipo de labor')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Insumo usado')
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_comment='Cantidad de insumo')
    jornales = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Jornales empleados')
    metodo = models.CharField(max_length=8, choices=[('manual', 'manual'), ('mecanico', 'mecanico'), ('robot', 'robot'), ('dron', 'dron')], db_default='manual', db_comment='Cómo se hizo (robot y dron llegan por la interfaz RobotCampo)')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea de la que salió')
    mision_robot = models.ForeignKey('iot.MisionRobot', models.DO_NOTHING, db_column='mision_robot_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Misión de robot o dron que la hizo')
    observaciones = models.TextField(null=True, blank=True, db_comment='Notas')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "labor_cultural" (las comillas separan esquema y tabla)
        db_table = 'produccion"."labor_cultural'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Trabajo hecho a una siembra: encalado, fertilización, deshierbe, control de plagas, poda, resiembra.'


# ==============================================================================================================
# Tabla produccion.cosecha  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/cosechas/
# ==============================================================================================================
class Cosecha(models.Model):
    """Producto cosechado y a dónde se fue (venta, alimento para los animales, semilla o pérdida)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    siembra = models.ForeignKey('produccion.Siembra', models.DO_NOTHING, db_column='siembra_id', related_name='+', db_constraint=False, db_comment='Siembra')
    fecha = models.DateField(db_comment='Día')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto resultante')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad')
    destino = models.CharField(max_length=15, choices=[('venta', 'venta'), ('alimento_animal', 'alimento_animal'), ('semilla', 'semilla'), ('autoconsumo', 'autoconsumo'), ('perdida', 'perdida')], db_comment='Destino')
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Lote de inventario creado al entrar a bodega')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "cosecha" (las comillas separan esquema y tabla)
        db_table = 'produccion"."cosecha'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Producto cosechado y a dónde se fue (venta, alimento para los animales, semilla o pérdida).'


# ==============================================================================================================
# Tabla produccion.analisis_suelo  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/analisis-suelo/
# ==============================================================================================================
class AnalisisSuelo(models.Model):
    """Resultados de laboratorio del suelo de una zona y la recomendación de encalado."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Zona muestreada')
    fecha_muestreo = models.DateField(db_comment='Fecha de la muestra')
    laboratorio = models.CharField(max_length=120, null=True, blank=True, db_comment='Laboratorio')
    ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, db_comment='pH')
    materia_organica_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Materia orgánica %')
    aluminio_cmol_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, db_comment='Aluminio intercambiable cmol/kg')
    resultados = models.JSONField(null=True, blank=True, db_comment='Demás elementos (P, K, Ca, Mg...)')
    recomendacion = models.TextField(null=True, blank=True, db_comment='Recomendación del agrónomo')
    archivo_url = models.CharField(max_length=300, null=True, blank=True, db_comment='PDF del resultado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "produccion", tabla "analisis_suelo" (las comillas separan esquema y tabla)
        db_table = 'produccion"."analisis_suelo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Resultados de laboratorio del suelo de una zona y la recomendación de encalado.'


# ==============================================================================================================
# Tabla produccion.categoria_huevo  ·  catálogo compartido entre fincas  ·  API: /api/v1/produccion/categorias-huevo/
# ==============================================================================================================
class CategoriaHuevo(models.Model):
    """Categorías comerciales del huevo por rango de peso, con la norma de la que salen (verificar NTC 1240 vigente)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=10, db_comment='Código, ej. jumbo, aaa, aa, a, b, c')
    peso_min_g = models.DecimalField(max_digits=5, decimal_places=1, db_comment='Peso mínimo en gramos (incluido)')
    peso_max_g = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, db_comment='Peso máximo en gramos (excluido); vacío = sin tope')
    norma = models.CharField(max_length=80, db_comment='Norma o fuente de los rangos')
    vigente_desde = models.DateField(db_comment='Desde cuándo aplica')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "produccion", tabla "categoria_huevo" (las comillas separan esquema y tabla)
        db_table = 'produccion"."categoria_huevo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Categorías comerciales del huevo por rango de peso, con la norma de la que salen (verificar NTC 1240 vigente).'


# ==============================================================================================================
# Tabla produccion.clasificacion_postura  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/clasificaciones-postura/
# ==============================================================================================================
class ClasificacionPostura(models.Model):
    """Huevos de un registro de postura por categoría; el método dice si se clasificó con báscula, a mano o con visión artificial."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    registro_postura = models.ForeignKey('produccion.RegistroPostura', models.DO_NOTHING, db_column='registro_postura_id', related_name='+', db_constraint=False, db_comment='Registro de postura')
    categoria_huevo = models.ForeignKey('produccion.CategoriaHuevo', models.DO_NOTHING, db_column='categoria_huevo_id', related_name='+', db_constraint=False, db_comment='Categoría')
    cantidad = models.IntegerField(db_comment='Huevos de esa categoría')
    metodo = models.CharField(max_length=12, choices=[('peso_bascula', 'peso_bascula'), ('manual', 'manual'), ('vision', 'vision')], db_default='manual', db_comment='Cómo se clasificó (vision = piloto de fase 4)')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "clasificacion_postura" (las comillas separan esquema y tabla)
        db_table = 'produccion"."clasificacion_postura'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Huevos de un registro de postura por categoría; el método dice si se clasificó con báscula, a mano o con visión artificial.'


# ==============================================================================================================
# Tabla produccion.registro_bioseguridad  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/registros-bioseguridad/
# ==============================================================================================================
class RegistroBioseguridad(models.Model):
    """Registros de bioseguridad e inocuidad que pide el ICA: limpieza, desinfección, plagas, visitas, cambio de cama y agua."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, db_comment='Galpón, bodega o zona')
    fecha = models.DateField(db_comment='Día')
    tipo = models.CharField(max_length=15, choices=[('limpieza', 'limpieza'), ('desinfeccion', 'desinfeccion'), ('control_plagas', 'control_plagas'), ('visita', 'visita'), ('cambio_cama', 'cambio_cama'), ('calidad_agua', 'calidad_agua'), ('vacio_sanitario', 'vacio_sanitario')], db_comment='Tipo de registro')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Desinfectante o insumo usado')
    responsable = models.CharField(max_length=120, db_comment='Quién lo hizo o quién visitó')
    observaciones = models.TextField(null=True, blank=True, db_comment='Notas')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "registro_bioseguridad" (las comillas separan esquema y tabla)
        db_table = 'produccion"."registro_bioseguridad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Registros de bioseguridad e inocuidad que pide el ICA: limpieza, desinfección, plagas, visitas, cambio de cama y agua.'


# ==============================================================================================================
# Tabla produccion.produccion_abono  ·  por finca (seguridad por filas)  ·  API: /api/v1/produccion/producciones-abono/
# ==============================================================================================================
class ProduccionAbono(models.Model):
    """Humus y compost producidos por el lombricultivo o la compostera; al entrar a bodega crean un lote vendible."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    origen = models.CharField(max_length=13, choices=[('lombricultivo', 'lombricultivo'), ('compostera', 'compostera'), ('biodigestor', 'biodigestor')], db_comment='De dónde sale')
    zona = models.ForeignKey('nucleo.Zona', models.DO_NOTHING, db_column='zona_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Zona')
    fecha = models.DateField(db_comment='Día de cosecha del abono')
    kg = models.DecimalField(max_digits=10, decimal_places=2, db_comment='Kilogramos')
    lote_inventario = models.ForeignKey('inventario.LoteInventario', models.DO_NOTHING, db_column='lote_inventario_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Lote creado en inventario')
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
        # Nombre real en PostgreSQL: esquema "produccion", tabla "produccion_abono" (las comillas separan esquema y tabla)
        db_table = 'produccion"."produccion_abono'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Humus y compost producidos por el lombricultivo o la compostera; al entrar a bodega crean un lote vendible.'
