"""Serializers del esquema seguridad: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# seguridad.factor_autenticacion <-> JSON en /api/v1/seguridad/factores-autenticacion/
class FactorAutenticacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FactorAutenticacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.sesion_usuario <-> JSON en /api/v1/seguridad/sesiones-usuario/
class SesionUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SesionUsuario  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.intento_acceso <-> JSON en /api/v1/seguridad/intentos-acceso/
class IntentoAccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IntentoAcceso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.regla_deteccion <-> JSON en /api/v1/seguridad/reglas-deteccion/
class ReglaDeteccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReglaDeteccion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.bloqueo <-> JSON en /api/v1/seguridad/bloqueos/
class BloqueoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bloqueo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.senuelo <-> JSON en /api/v1/seguridad/senuelos/
class SenueloSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Senuelo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.alerta_seguridad <-> JSON en /api/v1/seguridad/alertas-seguridad/
class AlertaSeguridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AlertaSeguridad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.incidente <-> JSON en /api/v1/seguridad/incidentes/
class IncidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Incidente  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.ejecucion_prueba <-> JSON en /api/v1/seguridad/ejecuciones-prueba/
class EjecucionPruebaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EjecucionPrueba  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# seguridad.copia_seguridad <-> JSON en /api/v1/seguridad/copias-seguridad/
class CopiaSeguridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CopiaSeguridad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
