"""Serializers del esquema documental: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# documental.documento <-> JSON en /api/v1/documental/documentos/
class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Documento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# documental.version_documento <-> JSON en /api/v1/documental/documentos/{id}/versiones/
class VersionDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VersionDocumento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# documental.vinculo_documento <-> JSON en /api/v1/documental/vinculos-documento/
class VinculoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VinculoDocumento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
