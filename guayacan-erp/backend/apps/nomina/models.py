"""Modelos del esquema nomina: Conceptos, periodos, novedades, liquidación, prestaciones, PILA, nómina electrónica (apagada) y pagos con doble aprobación.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «nomina». Django usa estas clases para leer y escribir
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
# Tabla nomina.concepto_nomina  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/conceptos-nomina/
# ==============================================================================================================
class ConceptoNomina(models.Model):
    """Concepto de la nómina (salario, auxilio, horas extra, recargos, jornal, destajo, deducciones, aportes). La tarifa vive en nucleo.parametro, nunca en el código."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=30, db_comment='Código, ej. SALARIO, AUX_TRANSPORTE, JORNAL, DESTAJO, SALUD_EMP')
    nombre = models.CharField(max_length=120, db_comment='Nombre')
    tipo = models.CharField(max_length=16, choices=[('devengado', 'devengado'), ('deduccion', 'deduccion'), ('aporte_empleador', 'aporte_empleador'), ('provision', 'provision')], db_comment='Tipo')
    base = models.CharField(max_length=10, choices=[('salario', 'salario'), ('jornal', 'jornal'), ('destajo', 'destajo'), ('horas', 'horas'), ('valor_fijo', 'valor_fijo'), ('porcentaje', 'porcentaje')], db_comment='Cómo se calcula')
    parametro_clave = models.CharField(max_length=80, null=True, blank=True, db_comment='Clave de nucleo.parametro con la tarifa vigente')
    constitutivo_salario = models.BooleanField(db_default=False, db_comment='Hace parte de la base para prestaciones')
    cuenta_contable = models.ForeignKey('finanzas.CuentaContable', models.DO_NOTHING, db_column='cuenta_contable_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Cuenta de causación')
    codigo_dian = models.CharField(max_length=40, null=True, blank=True, db_comment='Elemento del documento soporte de nómina electrónica')
    activo = models.BooleanField(db_default=True, db_comment='En uso')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "concepto_nomina" (las comillas separan esquema y tabla)
        db_table = 'nomina"."concepto_nomina'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Concepto de la nómina (salario, auxilio, horas extra, recargos, jornal, destajo, deducciones, aportes). La tarifa vive en nucleo.parametro, nunca en el código.'


# ==============================================================================================================
# Tabla nomina.periodo_nomina  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/periodos-nomina/
# ==============================================================================================================
class PeriodoNomina(models.Model):
    """Periodo de pago. Cerrado no se edita; las correcciones van como nota de ajuste. Cierre con doble aprobación y nunca por un agente."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    codigo = models.CharField(max_length=20, db_comment='Código, ej. 2026-11')
    tipo = models.CharField(max_length=9, choices=[('mensual', 'mensual'), ('quincenal', 'quincenal'), ('semanal', 'semanal')], db_comment='Frecuencia')
    desde = models.DateField(db_comment='Primer día')
    hasta = models.DateField(db_comment='Último día')
    estado = models.CharField(max_length=9, choices=[('abierto', 'abierto'), ('prenomina', 'prenomina'), ('cerrado', 'cerrado'), ('anulado', 'anulado')], db_default='abierto', db_comment='Estado')
    preparado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='preparado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién armó la prenómina')
    cerrado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='cerrado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Primera aprobación del cierre')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Segunda aprobación (persona distinta)')
    cerrado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    comprobante = models.ForeignKey('finanzas.Comprobante', models.DO_NOTHING, db_column='comprobante_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Comprobante de causación')
    ajusta_periodo = models.ForeignKey('nomina.PeriodoNomina', models.DO_NOTHING, db_column='ajusta_periodo_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Si es nota de ajuste, periodo que corrige')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "periodo_nomina" (las comillas separan esquema y tabla)
        db_table = 'nomina"."periodo_nomina'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Periodo de pago. Cerrado no se edita; las correcciones van como nota de ajuste. Cierre con doble aprobación y nunca por un agente.'


# ==============================================================================================================
# Tabla nomina.novedad  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/novedades/
# ==============================================================================================================
class Novedad(models.Model):
    """Hecho que se paga o descuenta en el periodo: salario fijo, jornales y destajo de tareas aprobadas, horas extra, ausencias, préstamos."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    periodo = models.ForeignKey('nomina.PeriodoNomina', models.DO_NOTHING, db_column='periodo_id', related_name='+', db_constraint=False, db_comment='Periodo')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    concepto = models.ForeignKey('nomina.ConceptoNomina', models.DO_NOTHING, db_column='concepto_id', related_name='+', db_constraint=False, db_comment='Concepto')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_default=1, db_comment='Días, horas, jornales o unidades')
    valor_unitario = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Valor por unidad')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor total')
    origen = models.CharField(max_length=8, choices=[('contrato', 'contrato'), ('tarea', 'tarea'), ('jornada', 'jornada'), ('ausencia', 'ausencia'), ('manual', 'manual')], db_comment='De dónde sale')
    tarea = models.ForeignKey('personal.Tarea', models.DO_NOTHING, db_column='tarea_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Tarea aprobada que la origina')
    jornada = models.ForeignKey('personal.Jornada', models.DO_NOTHING, db_column='jornada_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Jornada que la origina')
    ausencia = models.ForeignKey('personal.Ausencia', models.DO_NOTHING, db_column='ausencia_id', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Ausencia que la origina')
    observacion = models.CharField(max_length=200, null=True, blank=True, db_comment='Nota')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "novedad" (las comillas separan esquema y tabla)
        db_table = 'nomina"."novedad'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Hecho que se paga o descuenta en el periodo: salario fijo, jornales y destajo de tareas aprobadas, horas extra, ausencias, préstamos.'


# ==============================================================================================================
# Tabla nomina.liquidacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/liquidaciones/
# ==============================================================================================================
class Liquidacion(models.Model):
    """Resultado del periodo para un trabajador: devengado, deducciones y neto."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    periodo = models.ForeignKey('nomina.PeriodoNomina', models.DO_NOTHING, db_column='periodo_id', related_name='+', db_constraint=False, db_comment='Periodo')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    total_devengado = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Devengado')
    total_deducciones = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Deducciones')
    neto = models.DecimalField(max_digits=14, decimal_places=2, db_default=0, db_comment='Neto a pagar')
    estado = models.CharField(max_length=8, choices=[('borrador', 'borrador'), ('aprobada', 'aprobada'), ('pagada', 'pagada')], db_default='borrador', db_comment='Estado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "liquidacion" (las comillas separan esquema y tabla)
        db_table = 'nomina"."liquidacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Resultado del periodo para un trabajador: devengado, deducciones y neto.'


# ==============================================================================================================
# Tabla nomina.liquidacion_detalle  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/liquidaciones/{id}/detalles/
# ==============================================================================================================
class LiquidacionDetalle(models.Model):
    """Línea de la liquidación por concepto."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    liquidacion = models.ForeignKey('nomina.Liquidacion', models.DO_NOTHING, db_column='liquidacion_id', related_name='+', db_constraint=False, db_comment='Liquidación')
    concepto = models.ForeignKey('nomina.ConceptoNomina', models.DO_NOTHING, db_column='concepto_id', related_name='+', db_constraint=False, db_comment='Concepto')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, db_comment='Cantidad')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "liquidacion_detalle" (las comillas separan esquema y tabla)
        db_table = 'nomina"."liquidacion_detalle'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Línea de la liquidación por concepto.'


# ==============================================================================================================
# Tabla nomina.provision_prestacion  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/provisiones-prestacion/
# ==============================================================================================================
class ProvisionPrestacion(models.Model):
    """Provisión mensual de cesantías, intereses, prima y vacaciones."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    periodo = models.ForeignKey('nomina.PeriodoNomina', models.DO_NOTHING, db_column='periodo_id', related_name='+', db_constraint=False, db_comment='Periodo')
    empleado = models.ForeignKey('terceros.Empleado', models.DO_NOTHING, db_column='empleado_id', related_name='+', db_constraint=False, db_comment='Trabajador')
    tipo = models.CharField(max_length=19, choices=[('cesantias', 'cesantias'), ('intereses_cesantias', 'intereses_cesantias'), ('prima', 'prima'), ('vacaciones', 'vacaciones')], db_comment='Prestación')
    base = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Base')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor provisionado')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "provision_prestacion" (las comillas separan esquema y tabla)
        db_table = 'nomina"."provision_prestacion'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Provisión mensual de cesantías, intereses, prima y vacaciones.'


# ==============================================================================================================
# Tabla nomina.documento_nomina_electronica  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/documentos-nomina-electronica/
# ==============================================================================================================
class DocumentoNominaElectronica(models.Model):
    """Documento soporte de pago de nómina electrónica (uno por trabajador al mes). Se transmite por el servicio gratuito de la DIAN o un proveedor autorizado; se enciende con nomina_electronica."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    liquidacion = models.ForeignKey('nomina.Liquidacion', models.DO_NOTHING, db_column='liquidacion_id', related_name='+', db_constraint=False, db_comment='Liquidación')
    tipo = models.CharField(max_length=10, choices=[('individual', 'individual'), ('ajuste', 'ajuste')], db_default='individual', db_comment='Tipo')
    proveedor = models.CharField(max_length=21, choices=[('dian_gratuito', 'dian_gratuito'), ('proveedor_tecnologico', 'proveedor_tecnologico')], db_comment='Por dónde se transmite')
    cune = models.CharField(max_length=120, null=True, blank=True, db_comment='Código único devuelto por la DIAN')
    estado = models.CharField(max_length=9, choices=[('pendiente', 'pendiente'), ('enviado', 'enviado'), ('aceptado', 'aceptado'), ('rechazado', 'rechazado')], db_default='pendiente', db_comment='Estado')
    enviado_en = models.DateTimeField(null=True, blank=True, db_comment='Envío')
    respuesta = models.JSONField(null=True, blank=True, db_comment='Respuesta del proveedor')
    xml_url = models.CharField(max_length=300, null=True, blank=True, db_comment='XML firmado por el proveedor (nunca se firma a mano)')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "documento_nomina_electronica" (las comillas separan esquema y tabla)
        db_table = 'nomina"."documento_nomina_electronica'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Documento soporte de pago de nómina electrónica (uno por trabajador al mes). Se transmite por el servicio gratuito de la DIAN o un proveedor autorizado; se enciende con nomina_electronica.'


# ==============================================================================================================
# Tabla nomina.planilla_pila  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/planillas-pila/
# ==============================================================================================================
class PlanillaPila(models.Model):
    """Archivo de la planilla de seguridad social para el operador de la PILA; el pago lo hace una persona."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    periodo = models.ForeignKey('nomina.PeriodoNomina', models.DO_NOTHING, db_column='periodo_id', related_name='+', db_constraint=False, db_comment='Periodo')
    tipo_planilla = models.CharField(max_length=5, db_default='E', db_comment='Tipo de planilla (E = empleados)')
    archivo_url = models.CharField(max_length=300, db_comment='Archivo generado')
    operador = models.CharField(max_length=60, null=True, blank=True, db_comment='Operador de información')
    numero_planilla = models.CharField(max_length=30, null=True, blank=True, db_comment='Número asignado por el operador')
    pagada_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='pagada_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Quién la pagó')
    pagada_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "planilla_pila" (las comillas separan esquema y tabla)
        db_table = 'nomina"."planilla_pila'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Archivo de la planilla de seguridad social para el operador de la PILA; el pago lo hace una persona.'


# ==============================================================================================================
# Tabla nomina.pago_nomina  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/pagos-nomina/
# ==============================================================================================================
class PagoNomina(models.Model):
    """Pago de una liquidación (transferencia, Bre-B o efectivo). Lo prepara una persona y lo aprueba otra; nadie aprueba su propio pago."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    liquidacion = models.ForeignKey('nomina.Liquidacion', models.DO_NOTHING, db_column='liquidacion_id', related_name='+', db_constraint=False, db_comment='Liquidación')
    medio = models.CharField(max_length=13, choices=[('transferencia', 'transferencia'), ('bre_b', 'bre_b'), ('efectivo', 'efectivo')], db_comment='Medio')
    valor = models.DecimalField(max_digits=14, decimal_places=2, db_comment='Valor')
    preparado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='preparado_por', related_name='+', db_constraint=False, db_comment='Quién lo preparó')
    aprobado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='aprobado_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Primera aprobación')
    segunda_aprobacion_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='segunda_aprobacion_por', related_name='+', db_constraint=False, null=True, blank=True, db_comment='Segunda aprobación (pagos sobre el monto del parámetro monto_doble_aprobacion)')
    pagado_en = models.DateTimeField(null=True, blank=True, db_comment='Cuándo se pagó')
    referencia = models.CharField(max_length=80, null=True, blank=True, db_comment='Referencia bancaria')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "pago_nomina" (las comillas separan esquema y tabla)
        db_table = 'nomina"."pago_nomina'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Pago de una liquidación (transferencia, Bre-B o efectivo). Lo prepara una persona y lo aprueba otra; nadie aprueba su propio pago.'


# ==============================================================================================================
# Tabla nomina.exportacion_nomina  ·  por finca (seguridad por filas)  ·  API: /api/v1/nomina/exportaciones-nomina/
# ==============================================================================================================
class ExportacionNomina(models.Model):
    """Archivo para el contador cuando lleva la nómina en su propio programa."""

    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)
    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')
    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe
    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')
    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)
    periodo = models.ForeignKey('nomina.PeriodoNomina', models.DO_NOTHING, db_column='periodo_id', related_name='+', db_constraint=False, db_comment='Periodo')
    formato = models.CharField(max_length=12, choices=[('csv', 'csv'), ('excel', 'excel'), ('siigo', 'siigo'), ('world_office', 'world_office'), ('helisa', 'helisa'), ('otro', 'otro')], db_comment='Formato')
    archivo_url = models.CharField(max_length=300, db_comment='Archivo')
    generado_por = models.ForeignKey('nucleo.Usuario', models.DO_NOTHING, db_column='generado_por', related_name='+', db_constraint=False, db_comment='Quién lo generó')
    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)
    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')

    class Meta:
        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos
        managed = False
        # Nombre real en PostgreSQL: esquema "nomina", tabla "exportacion_nomina" (las comillas separan esquema y tabla)
        db_table = 'nomina"."exportacion_nomina'
        # Comentario de la tabla, el mismo que tiene la base
        db_table_comment = 'Archivo para el contador cuando lleva la nómina en su propio programa.'
