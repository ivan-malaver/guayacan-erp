"""Serializers del esquema terceros: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# terceros.tercero <-> JSON en /api/v1/terceros/terceros/
class TerceroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tercero  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# terceros.consentimiento_datos <-> JSON en /api/v1/terceros/consentimientos/
class ConsentimientoDatosSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConsentimientoDatos  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# terceros.cliente <-> JSON en /api/v1/terceros/clientes/
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cliente  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# terceros.proveedor <-> JSON en /api/v1/terceros/proveedores/
class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Proveedor  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# terceros.empleado <-> JSON en /api/v1/terceros/empleados/
class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Empleado  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
