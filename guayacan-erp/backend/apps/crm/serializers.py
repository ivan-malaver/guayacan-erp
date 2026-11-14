"""Serializers del esquema crm: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# crm.segmento <-> JSON en /api/v1/crm/segmentos/
class SegmentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Segmento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# crm.campana <-> JSON en /api/v1/crm/campanas/
class CampanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Campana  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# crm.formulario_captura <-> JSON en /api/v1/crm/formularios-captura/
class FormularioCapturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FormularioCaptura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# crm.prospecto <-> JSON en /api/v1/crm/prospectos/
class ProspectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Prospecto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# crm.contacto_empresa <-> JSON en /api/v1/crm/contactos-empresa/
class ContactoEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ContactoEmpresa  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# crm.interaccion <-> JSON en /api/v1/crm/interacciones/
class InteraccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Interaccion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# crm.oportunidad <-> JSON en /api/v1/crm/oportunidades/
class OportunidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Oportunidad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
