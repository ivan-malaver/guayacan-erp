"""Serializers del esquema nomina: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# nomina.concepto_nomina <-> JSON en /api/v1/nomina/conceptos-nomina/
class ConceptoNominaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConceptoNomina  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.periodo_nomina <-> JSON en /api/v1/nomina/periodos-nomina/
class PeriodoNominaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PeriodoNomina  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.novedad <-> JSON en /api/v1/nomina/novedades/
class NovedadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Novedad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.liquidacion <-> JSON en /api/v1/nomina/liquidaciones/
class LiquidacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Liquidacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.liquidacion_detalle <-> JSON en /api/v1/nomina/liquidaciones/{id}/detalles/
class LiquidacionDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LiquidacionDetalle  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.provision_prestacion <-> JSON en /api/v1/nomina/provisiones-prestacion/
class ProvisionPrestacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProvisionPrestacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.documento_nomina_electronica <-> JSON en /api/v1/nomina/documentos-nomina-electronica/
class DocumentoNominaElectronicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocumentoNominaElectronica  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.planilla_pila <-> JSON en /api/v1/nomina/planillas-pila/
class PlanillaPilaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlanillaPila  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.pago_nomina <-> JSON en /api/v1/nomina/pagos-nomina/
class PagoNominaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PagoNomina  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nomina.exportacion_nomina <-> JSON en /api/v1/nomina/exportaciones-nomina/
class ExportacionNominaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExportacionNomina  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
