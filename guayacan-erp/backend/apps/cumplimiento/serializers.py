"""Serializers del esquema cumplimiento: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# cumplimiento.norma <-> JSON en /api/v1/cumplimiento/normas/
class NormaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Norma  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# cumplimiento.requisito <-> JSON en /api/v1/cumplimiento/requisitos/
class RequisitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Requisito  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# cumplimiento.expediente <-> JSON en /api/v1/cumplimiento/expedientes/
class ExpedienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Expediente  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# cumplimiento.evaluacion_requisito <-> JSON en /api/v1/cumplimiento/evaluaciones-requisito/
class EvaluacionRequisitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EvaluacionRequisito  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# cumplimiento.evidencia_requisito <-> JSON en /api/v1/cumplimiento/evidencias-requisito/
class EvidenciaRequisitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EvidenciaRequisito  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# cumplimiento.auditoria_externa <-> JSON en /api/v1/cumplimiento/auditorias-externas/
class AuditoriaExternaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AuditoriaExterna  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# cumplimiento.no_conformidad <-> JSON en /api/v1/cumplimiento/no-conformidades/
class NoConformidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NoConformidad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# cumplimiento.accion_correctiva <-> JSON en /api/v1/cumplimiento/acciones-correctivas/
class AccionCorrectivaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AccionCorrectiva  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
