"""Serializers del esquema formacion: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# formacion.competencia <-> JSON en /api/v1/formacion/competencias/
class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Competencia  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.curso <-> JSON en /api/v1/formacion/cursos/
class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Curso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.leccion <-> JSON en /api/v1/formacion/lecciones/
class LeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Leccion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.evaluacion <-> JSON en /api/v1/formacion/evaluaciones/
class EvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Evaluacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.pregunta <-> JSON en /api/v1/formacion/preguntas/
class PreguntaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pregunta  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.inscripcion <-> JSON en /api/v1/formacion/inscripciones/
class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Inscripcion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.progreso <-> JSON en /api/v1/formacion/progresos/
class ProgresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Progreso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.sesion_presencial <-> JSON en /api/v1/formacion/sesiones-presencial/
class SesionPresencialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SesionPresencial  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.asistencia <-> JSON en /api/v1/formacion/asistencias/
class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Asistencia  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.certificado <-> JSON en /api/v1/formacion/certificados/
class CertificadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Certificado  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.habilitacion <-> JSON en /api/v1/formacion/habilitaciones/
class HabilitacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Habilitacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.necesidad_formacion <-> JSON en /api/v1/formacion/necesidades-formacion/
class NecesidadFormacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NecesidadFormacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.encuesta <-> JSON en /api/v1/formacion/encuestas/
class EncuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Encuesta  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# formacion.queja_apelacion <-> JSON en /api/v1/formacion/quejas-apelacion/
class QuejaApelacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.QuejaApelacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
