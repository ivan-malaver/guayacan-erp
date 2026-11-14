"""Serializers del esquema compras: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# compras.orden_compra <-> JSON en /api/v1/compras/ordenes-compra/
class OrdenCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenCompra  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# compras.orden_compra_detalle <-> JSON en /api/v1/compras/ordenes-compra/{id}/lineas/
class OrdenCompraDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrdenCompraDetalle  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# compras.cotizacion_proveedor <-> JSON en /api/v1/compras/cotizaciones-proveedor/
class CotizacionProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CotizacionProveedor  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# compras.precio_mercado <-> JSON en /api/v1/compras/precios-mercado/
class PrecioMercadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PrecioMercado  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# compras.documento_soporte <-> JSON en /api/v1/compras/documentos-soporte/
class DocumentoSoporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocumentoSoporte  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
