"""Serializers del esquema turismo: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# turismo.alojamiento <-> JSON en /api/v1/turismo/alojamientos/
class AlojamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Alojamiento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# turismo.plan_turistico <-> JSON en /api/v1/turismo/planes-turistico/
class PlanTuristicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlanTuristico  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# turismo.reserva <-> JSON en /api/v1/turismo/reservas/
class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reserva  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# turismo.bloqueo_calendario <-> JSON en /api/v1/turismo/bloqueos-calendario/
class BloqueoCalendarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BloqueoCalendario  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
