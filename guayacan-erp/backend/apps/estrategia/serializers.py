"""Serializers del esquema estrategia: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# estrategia.linea_negocio <-> JSON en /api/v1/estrategia/lineas-negocio/
class LineaNegocioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LineaNegocio  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.factor_dofa <-> JSON en /api/v1/estrategia/factores-dofa/
class FactorDofaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FactorDofa  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.estudio_mercado <-> JSON en /api/v1/estrategia/estudios-mercado/
class EstudioMercadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EstudioMercado  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.iniciativa <-> JSON en /api/v1/estrategia/iniciativas/
class IniciativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Iniciativa  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.evaluacion_proyecto <-> JSON en /api/v1/estrategia/evaluaciones-proyecto/
class EvaluacionProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EvaluacionProyecto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.flujo_proyecto <-> JSON en /api/v1/estrategia/evaluaciones-proyecto/{id}/flujos/
class FlujoProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FlujoProyecto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.reinversion <-> JSON en /api/v1/estrategia/reinversiones/
class ReinversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reinversion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.seguimiento_iniciativa <-> JSON en /api/v1/estrategia/seguimientos-iniciativa/
class SeguimientoIniciativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SeguimientoIniciativa  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# estrategia.objetivo <-> JSON en /api/v1/estrategia/objetivos/
class ObjetivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Objetivo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
