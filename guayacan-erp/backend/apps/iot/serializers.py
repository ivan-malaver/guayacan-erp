"""Serializers del esquema iot: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# iot.dispositivo <-> JSON en /api/v1/iot/dispositivos/
class DispositivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dispositivo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.sensor <-> JSON en /api/v1/iot/sensores/
class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sensor  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.actuador <-> JSON en /api/v1/iot/actuadores/
class ActuadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Actuador  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.lectura <-> JSON en /api/v1/iot/lecturas/
class LecturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Lectura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.regla_automatizacion <-> JSON en /api/v1/iot/reglas/
class ReglaAutomatizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReglaAutomatizacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.comando_actuador <-> JSON en /api/v1/iot/comandos/
class ComandoActuadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ComandoActuador  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.zona_seguridad <-> JSON en /api/v1/iot/zonas-seguridad/
class ZonaSeguridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ZonaSeguridad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.cambio_estado_alarma <-> JSON en /api/v1/iot/cambios-estado-alarma/
class CambioEstadoAlarmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CambioEstadoAlarma  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.credencial_acceso <-> JSON en /api/v1/iot/credenciales-acceso/
class CredencialAccesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CredencialAcceso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.camara <-> JSON en /api/v1/iot/camaras/
class CamaraSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Camara  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.evento_seguridad <-> JSON en /api/v1/iot/eventos-seguridad/
class EventoSeguridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventoSeguridad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.clip_video <-> JSON en /api/v1/iot/clipes-video/
class ClipVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClipVideo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.mision_robot <-> JSON en /api/v1/iot/misiones-robot/
class MisionRobotSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MisionRobot  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# iot.prioridad_carga <-> JSON en /api/v1/iot/prioridades-carga/
class PrioridadCargaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PrioridadCarga  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
