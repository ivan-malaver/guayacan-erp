"""Serializers del esquema seguros: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# seguros.poliza <-> JSON en /api/v1/seguros/polizas/
class PolizaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Poliza  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguros.bien_asegurado <-> JSON en /api/v1/seguros/bienes-asegurados/
class BienAseguradoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BienAsegurado  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguros.indice_poliza <-> JSON en /api/v1/seguros/indices-poliza/
class IndicePolizaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndicePoliza  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguros.aviso_siniestro <-> JSON en /api/v1/seguros/avisos-siniestro/
class AvisoSiniestroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AvisoSiniestro  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
