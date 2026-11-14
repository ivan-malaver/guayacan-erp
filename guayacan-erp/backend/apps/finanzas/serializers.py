"""Serializers del esquema finanzas: convierten los modelos en JSON y el JSON recibido en datos validados.

QUÉ HACE UN SERIALIZER
1. Al responder: toma una fila (objeto del modelo) y la convierte en JSON para el frontend.
2. Al recibir (POST, PUT, PATCH): revisa que el JSON traiga los campos obligatorios, con el tipo correcto y
   valores permitidos, antes de enviarlo a la base. La base vuelve a validar las reglas de negocio.

Generado por docs/uml/fuentes/gen_apps.py. Un caso de uso que necesite otros campos crea su propio serializer
aquí mismo, debajo de los generados."""
from rest_framework import serializers

from . import models

# Campos que pone la base (identificador, finca, fechas de control): el usuario puede verlos pero no enviarlos
SOLO_LECTURA = ('id', 'predio', 'creado_en', 'actualizado_en')


# finanzas.cuenta_contable <-> JSON en /api/v1/finanzas/cuentas-contable/
class CuentaContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CuentaContable  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.centro_costo <-> JSON en /api/v1/finanzas/centros-costo/
class CentroCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CentroCosto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.comprobante <-> JSON en /api/v1/finanzas/comprobantes/
class ComprobanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comprobante  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.movimiento_contable <-> JSON en /api/v1/finanzas/comprobantes/{id}/movimientos/
class MovimientoContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MovimientoContable  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.periodo_contable <-> JSON en /api/v1/finanzas/periodos-contable/
class PeriodoContableSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PeriodoContable  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.clasificacion_costo <-> JSON en /api/v1/finanzas/clasificaciones-costo/
class ClasificacionCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClasificacionCosto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.actividad_costo <-> JSON en /api/v1/finanzas/actividades-costo/
class ActividadCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ActividadCosto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.asignacion_costo <-> JSON en /api/v1/finanzas/asignaciones-costo/
class AsignacionCostoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AsignacionCosto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.costo_estandar <-> JSON en /api/v1/finanzas/costos-estandar/
class CostoEstandarSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CostoEstandar  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.presupuesto <-> JSON en /api/v1/finanzas/presupuestos/
class PresupuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Presupuesto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.premisa_presupuesto <-> JSON en /api/v1/finanzas/premisas-presupuesto/
class PremisaPresupuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PremisaPresupuesto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.presupuesto_detalle <-> JSON en /api/v1/finanzas/presupuestos/{id}/detalles/
class PresupuestoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PresupuestoDetalle  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.estado_financiero <-> JSON en /api/v1/finanzas/estados-financiero/
class EstadoFinancieroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstadoFinanciero  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.indicador <-> JSON en /api/v1/finanzas/indicadores/
class IndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Indicador  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.valor_indicador <-> JSON en /api/v1/finanzas/valores-indicador/
class ValorIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ValorIndicador  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.anticipo_proveedor <-> JSON en /api/v1/finanzas/anticipos-proveedor/
class AnticipoProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AnticipoProveedor  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.aplicacion_anticipo <-> JSON en /api/v1/finanzas/aplicaciones-anticipo/
class AplicacionAnticipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AplicacionAnticipo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# finanzas.reporte_indicadores <-> JSON en /api/v1/finanzas/reportes-indicadores/
class ReporteIndicadoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReporteIndicadores  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
