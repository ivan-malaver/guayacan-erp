"""Serializers del esquema riego: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# riego.fuente_agua <-> JSON en /api/v1/riego/fuentes-agua/
class FuenteAguaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FuenteAgua  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# riego.tanque <-> JSON en /api/v1/riego/tanques/
class TanqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tanque  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# riego.sistema_riego <-> JSON en /api/v1/riego/sistemas-riego/
class SistemaRiegoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SistemaRiego  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# riego.valvula <-> JSON en /api/v1/riego/valvulas/
class ValvulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Valvula  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# riego.evento_riego <-> JSON en /api/v1/riego/eventos-riego/
class EventoRiegoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventoRiego  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
