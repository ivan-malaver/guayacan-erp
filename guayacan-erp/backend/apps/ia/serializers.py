"""Serializers del esquema ia: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# ia.agente <-> JSON en /api/v1/ia/agentes/
class AgenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Agente  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.herramienta <-> JSON en /api/v1/ia/herramientas/
class HerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Herramienta  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.agente_herramienta <-> JSON en /api/v1/ia/agentes/{id}/herramientas/
class AgenteHerramientaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AgenteHerramienta  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.solicitud_aprobacion <-> JSON en /api/v1/ia/solicitudes-aprobacion/
class SolicitudAprobacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SolicitudAprobacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.documento_conocimiento <-> JSON en /api/v1/ia/documentos-conocimiento/
class DocumentoConocimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocumentoConocimiento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.fragmento_conocimiento <-> JSON en /api/v1/ia/fragmentos-conocimiento/
class FragmentoConocimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FragmentoConocimiento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.recomendacion <-> JSON en /api/v1/ia/recomendaciones/
class RecomendacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Recomendacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.evaluacion_respuesta <-> JSON en /api/v1/ia/evaluaciones-respuesta/
class EvaluacionRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EvaluacionRespuesta  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.consumo_ia <-> JSON en /api/v1/ia/consumos/
class ConsumoIaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConsumoIa  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.regla_conversacion <-> JSON en /api/v1/ia/reglas-conversacion/
class ReglaConversacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReglaConversacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.escalamiento <-> JSON en /api/v1/ia/escalamientos/
class EscalamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Escalamiento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.modelo_pronostico <-> JSON en /api/v1/ia/modelos-pronostico/
class ModeloPronosticoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ModeloPronostico  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.pronostico_demanda <-> JSON en /api/v1/ia/pronosticos-demanda/
class PronosticoDemandaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PronosticoDemanda  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.diagnostico_imagen <-> JSON en /api/v1/ia/diagnosticos-imagen/
class DiagnosticoImagenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DiagnosticoImagen  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.escenario <-> JSON en /api/v1/ia/escenarios/
class EscenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Escenario  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# ia.decision <-> JSON en /api/v1/ia/decisiones/
class DecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Decision  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
