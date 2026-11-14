"""Serializers del esquema adopcion: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# adopcion.plan <-> JSON en /api/v1/adopcion/planes/
class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Plan  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.sitio <-> JSON en /api/v1/adopcion/sitios/
class SitioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sitio  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.bien <-> JSON en /api/v1/adopcion/bienes/
class BienSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bien  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.contrato <-> JSON en /api/v1/adopcion/contratos/
class ContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contrato  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.cuota <-> JSON en /api/v1/adopcion/cuotas/
class CuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cuota  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.seguimiento <-> JSON en /api/v1/adopcion/seguimientos/
class SeguimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Seguimiento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.liquidacion <-> JSON en /api/v1/adopcion/liquidaciones/
class LiquidacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Liquidacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.movimiento_saldo <-> JSON en /api/v1/adopcion/movimientos-saldo/
class MovimientoSaldoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MovimientoSaldo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
