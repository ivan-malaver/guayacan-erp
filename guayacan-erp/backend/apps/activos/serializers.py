"""Serializers del esquema activos: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# activos.activo <-> JSON en /api/v1/activos/activos/
class ActivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Activo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# activos.plan_mantenimiento <-> JSON en /api/v1/activos/planes-mantenimiento/
class PlanMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlanMantenimiento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# activos.orden_trabajo <-> JSON en /api/v1/activos/ordenes-trabajo/
class OrdenTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenTrabajo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# activos.repuesto_orden <-> JSON en /api/v1/activos/ordenes-trabajo/{id}/repuestos/
class RepuestoOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RepuestoOrden  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# activos.uso_activo <-> JSON en /api/v1/activos/usos-activo/
class UsoActivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UsoActivo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# activos.depreciacion <-> JSON en /api/v1/activos/depreciaciones/
class DepreciacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Depreciacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
