"""Serializers del esquema redes: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# redes.cuenta_red <-> JSON en /api/v1/redes/cuentas-red/
class CuentaRedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CuentaRed  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# redes.publicacion <-> JSON en /api/v1/redes/publicaciones/
class PublicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Publicacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# redes.politica_canal <-> JSON en /api/v1/redes/politicas-canal/
class PoliticaCanalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PoliticaCanal  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# redes.plantilla_mensaje <-> JSON en /api/v1/redes/plantillas-mensaje/
class PlantillaMensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlantillaMensaje  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# redes.mensaje_saliente <-> JSON en /api/v1/redes/mensajes-salientes/
class MensajeSalienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MensajeSaliente  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# redes.pieza_audiovisual <-> JSON en /api/v1/redes/piezas-audiovisual/
class PiezaAudiovisualSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PiezaAudiovisual  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# redes.pieza_persona <-> JSON en /api/v1/redes/piezas-persona/
class PiezaPersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PiezaPersona  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
