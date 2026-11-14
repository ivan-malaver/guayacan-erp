"""Serializers del esquema proyectos: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# proyectos.proyecto <-> JSON en /api/v1/proyectos/proyectos/
class ProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proyecto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.interesado <-> JSON en /api/v1/proyectos/interesados/
class InteresadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Interesado  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.elemento_edt <-> JSON en /api/v1/proyectos/elementos-edt/
class ElementoEdtSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ElementoEdt  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.iteracion <-> JSON en /api/v1/proyectos/iteraciones/
class IteracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Iteracion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.actividad <-> JSON en /api/v1/proyectos/actividades/
class ActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Actividad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.dependencia <-> JSON en /api/v1/proyectos/actividades/{id}/dependencias/
class DependenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dependencia  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.riesgo <-> JSON en /api/v1/proyectos/riesgos/
class RiesgoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Riesgo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.registro <-> JSON en /api/v1/proyectos/registros/
class RegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Registro  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.solicitud_cambio <-> JSON en /api/v1/proyectos/solicitudes-cambio/
class SolicitudCambioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SolicitudCambio  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.linea_base <-> JSON en /api/v1/proyectos/lineas-base/
class LineaBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LineaBase  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# proyectos.medicion_valor_ganado <-> JSON en /api/v1/proyectos/mediciones-valor-ganado/
class MedicionValorGanadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MedicionValorGanado  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
