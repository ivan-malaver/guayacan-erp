"""Serializers del esquema agenda: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# agenda.recurso <-> JSON en /api/v1/agenda/recursos/
class RecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Recurso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# agenda.cita <-> JSON en /api/v1/agenda/citas/
class CitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cita  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# agenda.visita <-> JSON en /api/v1/agenda/visitas/
class VisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Visita  # tabla que representa
        # AGD-03: la huella del pase no se muestra (con ella se podría adivinar el código por fuerza bruta)
        exclude = ('pase_hash',)
        # AGD-03: el estado y la decisión cambian solo con /aprobar/ (permiso agenda.aprobar_visita) y en portería
        read_only_fields = SOLO_LECTURA + ('estado', 'aprobada_por', 'motivo_rechazo')
        # Si no se envían, el servicio pone al usuario como anfitrión y la base personas = 1
        extra_kwargs = {'anfitrion': {'required': False}, 'personas': {'required': False},
                        'requiere_bioseguridad': {'required': False}}


class DecisionVisitaSerializer(serializers.Serializer):
    """AGD-03: lo que envía el encargado en POST /api/v1/agenda/visitas/{id}/aprobar/."""
    decision = serializers.ChoiceField(choices=['aprobar', 'rechazar'])
    motivo = serializers.CharField(max_length=200, required=False)


# agenda.registro_acceso <-> JSON en /api/v1/agenda/registros-acceso/
class RegistroAccesoSerializer(serializers.ModelSerializer):
    # AGD-04: lo que lee el portero; el servicio lo convierte en visita o empleado (solo se reciben)
    codigo_pase = serializers.CharField(max_length=40, required=False, write_only=True)
    codigo_carne = serializers.CharField(max_length=80, required=False, write_only=True)

    class Meta:
        model = models.RegistroAcceso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        # AGD-04: quién registró lo pone la base con el usuario de la sesión
        read_only_fields = SOLO_LECTURA + ('registrado_por',)
        # Si no se envían, el servicio deduce el método y la base pone la hora, el punto y la desinfección
        extra_kwargs = {'metodo': {'required': False}, 'ocurrido_en': {'required': False}, 'punto': {'required': False},
                        'desinfeccion': {'required': False}}
