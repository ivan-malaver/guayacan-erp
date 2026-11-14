"""Serializers del esquema inventario: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# inventario.unidad_medida <-> JSON en /api/v1/inventario/unidades-medida/
class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UnidadMedida  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.categoria_producto <-> JSON en /api/v1/inventario/categorias-producto/
class CategoriaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CategoriaProducto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.producto <-> JSON en /api/v1/inventario/productos/
class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Producto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.bodega <-> JSON en /api/v1/inventario/bodegas/
class BodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bodega  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.lote_inventario <-> JSON en /api/v1/inventario/lotes-inventario/
class LoteInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteInventario  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.movimiento_inventario <-> JSON en /api/v1/inventario/movimientos-inventario/
class MovimientoInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MovimientoInventario  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.etiqueta <-> JSON en /api/v1/inventario/etiquetas/
class EtiquetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Etiqueta  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.lectura_codigo <-> JSON en /api/v1/inventario/lecturas-codigo/
class LecturaCodigoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LecturaCodigo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.pesaje <-> JSON en /api/v1/inventario/pesajes/
class PesajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pesaje  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.conteo_fisico <-> JSON en /api/v1/inventario/conteos/
class ConteoFisicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConteoFisico  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.conteo_detalle <-> JSON en /api/v1/inventario/conteos/{id}/detalles/
class ConteoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConteoDetalle  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.vehiculo <-> JSON en /api/v1/inventario/vehiculos/
class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Vehiculo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.excursion_temperatura <-> JSON en /api/v1/inventario/excursiones-temperatura/
class ExcursionTemperaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExcursionTemperatura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# inventario.bloqueo_lote <-> JSON en /api/v1/inventario/bloqueos-lote/
class BloqueoLoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BloqueoLote  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
