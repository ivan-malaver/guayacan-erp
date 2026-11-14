"""Modelos del esquema finanzas: Plan de cuentas (PUC), centros de costo, comprobantes y movimientos contables.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «finanzas». Django usa estas clases para leer y escribir
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
# Tabla finanzas.cuenta_contable  ·  catálogo compartido entre fincas  ·  API: /api/v1/finanzas/cuentas-contable/
# ==============================================================================================================
class CuentaContable(models.Model):
    """Plan Único de Cuentas (PUC) adaptado a la finca."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=10, unique=True, db_comment='Código PUC, ej. 413505')
    nombre = models.CharField(max_length=150, db_comment='Nombre')
    naturaleza = models.CharField(max_length=7, choices=[('debito', 'debito'), ('credito', 'credito')], db_comment='Naturaleza')
    nivel = models.SmallIntegerField(db_comment='1 clase, 2 grupo, 3 cuenta, 4 subcuenta, 5 auxiliar')
    padre = models.ForeignKey('finanzas.CuentaContable', models.DO_NOTHING, db_column='padre_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cuenta superior')
    acepta_movimiento = models.BooleanField(db_default=False, db_comment='Solo las auxiliares reciben movimientos')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "cuenta_contable" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."cuenta_contable'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Plan Único de Cuentas (PUC) adaptado a la finca.'


# ==============================================================================================================
# Tabla finanzas.centro_costo  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/centros-costo/
# ==============================================================================================================
class CentroCosto(models.Model):
    """Unidad de negocio para medir rentabilidad (avícola, ovino-caprino, piscícola, ciclo corto, perennes, turismo, administración)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=10, db_comment='Código, ej. AVI')
    nombre = models.CharField(max_length=80, db_comment='Nombre')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "centro_costo" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."centro_costo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Unidad de negocio para medir rentabilidad (avícola, ovino-caprino, piscícola, ciclo corto, perennes, turismo, administración).'


# ==============================================================================================================
# Tabla finanzas.comprobante  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/comprobantes/
# ==============================================================================================================
class Comprobante(models.Model):
    """Documento contable (ingreso, egreso, nota, causación). Lo generan reglas a partir de ventas, compras y nómina; el agente contador solo sugiere."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=13, choices=[('ingreso', 'ingreso'), ('egreso', 'egreso'), ('nota_contable', 'nota_contable'), ('causacion', 'causacion'), ('nomina', 'nomina'), ('ajuste', 'ajuste')], db_comment='Tipo')
    numero = models.CharField(max_length=20, db_comment='Consecutivo por tipo')
    fecha = models.DateField(db_comment='Fecha contable')
    descripcion = models.TextField(db_comment='Concepto')
    origen_tabla = models.CharField(max_length=60, null=True, blank=True, db_comment='Documento de negocio que lo generó')
    origen_id = models.BigIntegerField(null=True, blank=True, db_comment='Id del documento')
    estado = models.CharField(max_length=13, choices=[('borrador', 'borrador'), ('contabilizado', 'contabilizado'), ('anulado', 'anulado')], db_default='borrador', db_comment='Situación; solo se contabiliza si débitos = créditos y el periodo está abierto')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quien lo contabilizó')
    contabilizado_en = models.DateTimeField(null=True, blank=True, db_comment='Momento en que quedó contabilizado (desde ahí sus movimientos no se pueden cambiar)')
    motivo_anulacion = models.TextField(null=True, blank=True, db_comment='Por qué se anuló')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "comprobante" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."comprobante'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Documento contable (ingreso, egreso, nota, causación). Lo generan reglas a partir de ventas, compras y nómina; el agente contador solo sugiere.'


# ==============================================================================================================
# Tabla finanzas.movimiento_contable  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/comprobantes/{id}/movimientos/
# ==============================================================================================================
class MovimientoContable(models.Model):
    """Línea débito o crédito de un comprobante."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    comprobante = models.ForeignKey('finanzas.Comprobante', models.DO_NOTHING, db_column='comprobante_id', related_name='+', db_constraint=False, db_comment='Comprobante')
    cuenta = models.ForeignKey('finanzas.CuentaContable', models.DO_NOTHING, db_column='cuenta_id', related_name='+', db_constraint=False, db_comment='Cuenta')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tercero')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Centro de costo')
    debito = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Débito')
    credito = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Crédito')
    detalle = models.CharField(max_length=200, null=True, blank=True, db_comment='Detalle')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "movimiento_contable" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."movimiento_contable'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Línea débito o crédito de un comprobante.'


# ==============================================================================================================
# Tabla finanzas.periodo_contable  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/periodos-contable/
# ==============================================================================================================
class PeriodoContable(models.Model):
    """Mes contable; un comprobante solo se contabiliza o anula si su mes está abierto."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    anio = models.SmallIntegerField(db_comment='Año')
    mes = models.SmallIntegerField(db_comment='Mes (1 a 12)')
    estado = models.CharField(max_length=7, choices=[('abierto', 'abierto'), ('cerrado', 'cerrado')], db_default='abierto', db_comment='Estado')
    cerrado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='cerrado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo cerró')
    cerrado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "periodo_contable" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."periodo_contable'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Mes contable; un comprobante solo se contabiliza o anula si su mes está abierto.'


# ==============================================================================================================
# Tabla finanzas.clasificacion_costo  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/clasificaciones-costo/
# ==============================================================================================================
class ClasificacionCosto(models.Model):
    """Cómo se comporta cada cuenta de costo o gasto: elemento (MD, MOD, CIF, administración, ventas, financiero) y comportamiento (fijo, variable, semivariable, escalonado). Base del costeo variable y de las palancas."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    cuenta = models.ForeignKey('finanzas.CuentaContable', models.DO_NOTHING, db_column='cuenta_id', related_name='+', db_constraint=False, db_comment='Cuenta')
    elemento = models.CharField(max_length=20, choices=[('material_directo', 'material_directo'), ('mano_obra_directa', 'mano_obra_directa'), ('cif', 'cif'), ('gasto_administracion', 'gasto_administracion'), ('gasto_ventas', 'gasto_ventas'), ('gasto_financiero', 'gasto_financiero'), ('otro', 'otro')], db_comment='Elemento del costo')
    comportamiento = models.CharField(max_length=12, choices=[('fijo', 'fijo'), ('variable', 'variable'), ('semivariable', 'semivariable'), ('escalonado', 'escalonado')], db_comment='Comportamiento frente al volumen')
    parte_fija_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_comment='Porcentaje fijo de un costo semivariable')
    controlable = models.BooleanField(db_default=True, db_comment='Lo controla el responsable del centro')
    es_costo_producto = models.BooleanField(db_comment='Costo del producto (va al inventario) o costo del periodo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "clasificacion_costo" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."clasificacion_costo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Cómo se comporta cada cuenta de costo o gasto: elemento (MD, MOD, CIF, administración, ventas, financiero) y comportamiento (fijo, variable, semivariable, escalonado). Base del costeo variable y de las palancas.'


# ==============================================================================================================
# Tabla finanzas.actividad_costo  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/actividades-costo/
# ==============================================================================================================
class ActividadCosto(models.Model):
    """Actividad para costeo basado en actividades (ABC) con su inductor: horas de máquina, aves-día, jornales, m² regados."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código, ej. ALIMENTAR_AVES')
    nombre = models.CharField(max_length=120, db_comment='Actividad')
    inductor = models.CharField(max_length=60, db_comment='Inductor de costo, ej. aves_dia, horas_maquina, jornales')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Centro de servicio que la presta')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "actividad_costo" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."actividad_costo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Actividad para costeo basado en actividades (ABC) con su inductor: horas de máquina, aves-día, jornales, m² regados.'


# ==============================================================================================================
# Tabla finanzas.asignacion_costo  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/asignaciones-costo/
# ==============================================================================================================
class AsignacionCosto(models.Model):
    """Reparto mensual de costos indirectos a los centros según el inductor consumido."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    mes = models.DateField(db_comment='Mes')
    actividad = models.ForeignKey('finanzas.ActividadCosto', models.DO_NOTHING, db_column='actividad_id', related_name='+', db_constraint=False, db_comment='Actividad')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, db_comment='Centro que la consume')
    cantidad_inductor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Cantidad del inductor consumida')
    valor_asignado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Valor asignado (lo calcula la regla)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "asignacion_costo" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."asignacion_costo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Reparto mensual de costos indirectos a los centros según el inductor consumido.'


# ==============================================================================================================
# Tabla finanzas.costo_estandar  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/costos-estandar/
# ==============================================================================================================
class CostoEstandar(models.Model):
    """Costo estándar por unidad de producto (materiales, mano de obra y CIF) para comparar contra el real."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, db_comment='Producto')
    vigente_desde = models.DateField(db_comment='Desde')
    material_directo = models.DecimalField(max_digits=14, decimal_places=2, db_comment='MD por unidad')
    mano_obra_directa = models.DecimalField(max_digits=14, decimal_places=2, db_comment='MOD por unidad')
    cif = models.DecimalField(max_digits=14, decimal_places=2, db_comment='CIF por unidad')
    costo_variable_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Parte variable del costo unitario')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "costo_estandar" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."costo_estandar'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Costo estándar por unidad de producto (materiales, mano de obra y CIF) para comparar contra el real.'


# ==============================================================================================================
# Tabla finanzas.presupuesto  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/presupuestos/
# ==============================================================================================================
class Presupuesto(models.Model):
    """Presupuesto maestro del año (operación y financiero), con versión y aprobación; puede ser base cero. Base para el informe al Fondo Emprender."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    nombre = models.CharField(max_length=150, db_comment='Nombre')
    anio = models.SmallIntegerField(db_comment='Año')
    version = models.SmallIntegerField(db_default=1, db_comment='Versión')
    base_cero = models.BooleanField(db_default=False, db_comment='Cada rubro se justifica desde cero')
    fuente = models.CharField(max_length=15, choices=[('propio', 'propio'), ('fondo_emprender', 'fondo_emprender'), ('credito', 'credito'), ('mixto', 'mixto')], db_default='propio', db_comment='Fuente de los recursos')
    estado = models.CharField(max_length=8, choices=[('borrador', 'borrador'), ('aprobado', 'aprobado'), ('cerrado', 'cerrado')], db_default='borrador', db_comment='Estado')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo aprobó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "presupuesto" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."presupuesto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Presupuesto maestro del año (operación y financiero), con versión y aprobación; puede ser base cero. Base para el informe al Fondo Emprender.'


# ==============================================================================================================
# Tabla finanzas.premisa_presupuesto  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/premisas-presupuesto/
# ==============================================================================================================
class PremisaPresupuesto(models.Model):
    """Premisas del presupuesto: inflación, salario mínimo, precio del concentrado, crecimiento del mercado, política de cartera."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    presupuesto = models.ForeignKey('finanzas.Presupuesto', models.DO_NOTHING, db_column='presupuesto_id', related_name='+', db_constraint=False, db_comment='Presupuesto')
    tipo = models.CharField(max_length=14, choices=[('macroeconomica', 'macroeconomica'), ('microeconomica', 'microeconomica')], db_comment='Tipo de premisa')
    variable = models.CharField(max_length=80, db_comment='Variable, ej. inflacion, precio_concentrado, pct_ventas_contado')
    valor = models.DecimalField(max_digits=14, decimal_places=4, db_comment='Valor')
    fuente = models.CharField(max_length=200, null=True, blank=True, db_comment='Fuente (DANE, Banco de la República, cotización)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "premisa_presupuesto" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."premisa_presupuesto'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Premisas del presupuesto: inflación, salario mínimo, precio del concentrado, crecimiento del mercado, política de cartera.'


# ==============================================================================================================
# Tabla finanzas.presupuesto_detalle  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/presupuestos/{id}/detalles/
# ==============================================================================================================
class PresupuestoDetalle(models.Model):
    """Rubro del presupuesto por mes, centro de costo y cuenta, en la secuencia del presupuesto maestro (ventas, producción, materias primas, mano de obra, CIF, gastos, inversión, financiación, caja)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    presupuesto = models.ForeignKey('finanzas.Presupuesto', models.DO_NOTHING, db_column='presupuesto_id', related_name='+', db_constraint=False, db_comment='Presupuesto')
    componente = models.CharField(max_length=16, choices=[('ventas', 'ventas'), ('produccion', 'produccion'), ('materia_prima', 'materia_prima'), ('mano_obra', 'mano_obra'), ('cif', 'cif'), ('gastos_operacion', 'gastos_operacion'), ('inversion', 'inversion'), ('financiacion', 'financiacion'), ('flujo_caja', 'flujo_caja')], db_comment='Componente del presupuesto maestro')
    mes = models.SmallIntegerField(db_comment='Mes (1 a 12)')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Centro de costo')
    cuenta = models.ForeignKey('finanzas.CuentaContable', models.DO_NOTHING, db_column='cuenta_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cuenta')
    producto = models.ForeignKey('inventario.Producto', models.DO_NOTHING, db_column='producto_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Producto (ventas y producción)')
    cantidad = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, db_comment='Unidades')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    justificacion = models.TextField(null=True, blank=True, db_comment='Justificación (obligatoria en base cero)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "presupuesto_detalle" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."presupuesto_detalle'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Rubro del presupuesto por mes, centro de costo y cuenta, en la secuencia del presupuesto maestro (ventas, producción, materias primas, mano de obra, CIF, gastos, inversión, financiación, caja).'


# ==============================================================================================================
# Tabla finanzas.estado_financiero  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/estados-financiero/
# ==============================================================================================================
class EstadoFinanciero(models.Model):
    """Estado financiero generado y congelado (balance, resultados por costeo variable o absorbente, flujo de efectivo directo o indirecto), real o presupuestado."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    tipo = models.CharField(max_length=24, choices=[('balance_general', 'balance_general'), ('resultados_absorbente', 'resultados_absorbente'), ('resultados_variable', 'resultados_variable'), ('flujo_efectivo_directo', 'flujo_efectivo_directo'), ('flujo_efectivo_indirecto', 'flujo_efectivo_indirecto'), ('cambios_patrimonio', 'cambios_patrimonio')], db_comment='Estado')
    desde = models.DateField(db_comment='Desde')
    hasta = models.DateField(db_comment='Hasta')
    presupuestado = models.BooleanField(db_default=False, db_comment='Es proforma (del presupuesto)')
    datos = models.JSONField(db_comment='Partidas y totales')
    generado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='generado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién lo generó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "estado_financiero" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."estado_financiero'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Estado financiero generado y congelado (balance, resultados por costeo variable o absorbente, flujo de efectivo directo o indirecto), real o presupuestado.'


# ==============================================================================================================
# Tabla finanzas.indicador  ·  catálogo compartido entre fincas  ·  API: /api/v1/finanzas/indicadores/
# ==============================================================================================================
class Indicador(models.Model):
    """Catálogo de indicadores financieros y de gestión con su fórmula, meta y semáforo (liquidez, endeudamiento, rentabilidad, rotación, EBITDA, EVA, Altman, palancas, postura por ave…)."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=40, unique=True, db_comment='Código, ej. razon_corriente, rsp, gpo')
    nombre = models.CharField(max_length=150, db_comment='Nombre')
    grupo = models.CharField(max_length=13, choices=[('liquidez', 'liquidez'), ('endeudamiento', 'endeudamiento'), ('rentabilidad', 'rentabilidad'), ('actividad', 'actividad'), ('valor', 'valor'), ('riesgo', 'riesgo'), ('palanca', 'palanca'), ('produccion', 'produccion'), ('comercial', 'comercial'), ('personal', 'personal'), ('proyecto', 'proyecto')], db_comment='Grupo')
    formula = models.TextField(db_comment='Fórmula')
    interpretacion = models.TextField(null=True, blank=True, db_comment='Cómo leerlo')
    unidad = models.CharField(max_length=10, choices=[('veces', 'veces'), ('porcentaje', 'porcentaje'), ('pesos', 'pesos'), ('dias', 'dias'), ('unidades', 'unidades')], db_comment='Unidad')
    sentido = models.CharField(max_length=11, choices=[('mayor_mejor', 'mayor_mejor'), ('menor_mejor', 'menor_mejor'), ('rango', 'rango')], db_comment='Qué es mejor')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "indicador" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."indicador'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Catálogo de indicadores financieros y de gestión con su fórmula, meta y semáforo (liquidez, endeudamiento, rentabilidad, rotación, EBITDA, EVA, Altman, palancas, postura por ave…).'


# ==============================================================================================================
# Tabla finanzas.valor_indicador  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/valores-indicador/
# ==============================================================================================================
class ValorIndicador(models.Model):
    """Valor calculado de un indicador en un periodo, con meta y semáforo para el tablero del administrador."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    indicador = models.ForeignKey('finanzas.Indicador', models.DO_NOTHING, db_column='indicador_id', related_name='+', db_constraint=False, db_comment='Indicador')
    desde = models.DateField(db_comment='Desde')
    hasta = models.DateField(db_comment='Hasta')
    centro_costo = models.ForeignKey('finanzas.CentroCosto', models.DO_NOTHING, db_column='centro_costo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Línea, si es por línea')
    valor = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, db_comment='Valor')
    meta = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True, db_comment='Meta')
    semaforo = models.CharField(max_length=8, choices=[('verde', 'verde'), ('amarillo', 'amarillo'), ('rojo', 'rojo'), ('sin_meta', 'sin_meta'), ('sin_dato', 'sin_dato')], db_comment='Semáforo (sin_meta: hay valor pero no hay meta fijada)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "valor_indicador" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."valor_indicador'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Valor calculado de un indicador en un periodo, con meta y semáforo para el tablero del administrador.'


# ==============================================================================================================
# Tabla finanzas.anticipo_proveedor  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/anticipos-proveedor/
# ==============================================================================================================
class AnticipoProveedor(models.Model):
    """Pago adelantado a un proveedor: queda como saldo a favor y se descuenta en las compras siguientes; nunca queda negativo. No se reciben recargas de clientes."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    proveedor = models.ForeignKey('terceros.Proveedor', models.DO_NOTHING, db_column='proveedor_id', related_name='+', db_constraint=False, db_comment='Proveedor')
    fecha = models.DateField(db_comment='Fecha')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    saldo = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Saldo por descontar')
    comprobante = models.ForeignKey('finanzas.Comprobante', models.DO_NOTHING, db_column='comprobante_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Comprobante')
    estado = models.CharField(max_length=8, choices=[('abierto', 'abierto'), ('aplicado', 'aplicado'), ('devuelto', 'devuelto')], db_default='abierto', db_comment='Estado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "anticipo_proveedor" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."anticipo_proveedor'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Pago adelantado a un proveedor: queda como saldo a favor y se descuenta en las compras siguientes; nunca queda negativo. No se reciben recargas de clientes.'


# ==============================================================================================================
# Tabla finanzas.aplicacion_anticipo  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/aplicaciones-anticipo/
# ==============================================================================================================
class AplicacionAnticipo(models.Model):
    """Descuento de un anticipo en una orden de compra."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    anticipo = models.ForeignKey('finanzas.AnticipoProveedor', models.DO_NOTHING, db_column='anticipo_id', related_name='+', db_constraint=False, db_comment='Anticipo')
    orden_compra = models.ForeignKey('compras.OrdenCompra', models.DO_NOTHING, db_column='orden_compra_id', related_name='+', db_constraint=False, db_comment='Compra')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor descontado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "aplicacion_anticipo" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."aplicacion_anticipo'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Descuento de un anticipo en una orden de compra.'


# ==============================================================================================================
# Tabla finanzas.reporte_indicadores  ·  por finca (seguridad por filas)  ·  API: /api/v1/finanzas/reportes-indicadores/
# ==============================================================================================================
class ReporteIndicadores(models.Model):
    """Informe de indicadores verificables para Finagro, bancos, gremios o certificadores, con autorización del titular y sin costos ni datos personales."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    destinatario = models.CharField(max_length=15, choices=[('finagro', 'finagro'), ('banco', 'banco'), ('gremio', 'gremio'), ('certificador', 'certificador'), ('fondo_emprender', 'fondo_emprender'), ('otro', 'otro')], db_comment='A quién va')
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Entidad')
    desde = models.DateField(db_comment='Desde')
    hasta = models.DateField(db_comment='Hasta')
    contenido = models.JSONField(db_comment='Indicadores (producción, ventas, cumplimiento)')
    hash_sha256 = models.CharField(max_length=64, db_comment='Huella del contenido (verificable)')
    autorizado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='autorizado_por', related_name='+', db_constraint=False, db_comment='Titular que autorizó compartirlo')
    enviado_en = models.DateTimeField(null=True, blank=True, db_comment='Envío')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "finanzas", tabla "reporte_indicadores" (las comillas separan esquema y tabla)
        db_table = 'finanzas"."reporte_indicadores'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Informe de indicadores verificables para Finagro, bancos, gremios o certificadores, con autorización del titular y sin costos ni datos personales.'
