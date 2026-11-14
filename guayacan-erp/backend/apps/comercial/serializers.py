"""Serializers del esquema comercial: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# comercial.lista_precios <-> JSON en /api/v1/comercial/listas-precios/
class ListaPreciosSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ListaPrecios  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.precio_producto <-> JSON en /api/v1/comercial/precios-producto/
class PrecioProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PrecioProducto  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.propuesta_precio <-> JSON en /api/v1/comercial/propuestas-precio/
class PropuestaPrecioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PropuestaPrecio  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.pedido <-> JSON en /api/v1/comercial/pedidos/
class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pedido  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.pedido_detalle <-> JSON en /api/v1/comercial/pedidos/{id}/lineas/
class PedidoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PedidoDetalle  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.factura <-> JSON en /api/v1/comercial/facturas/
class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Factura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.pago <-> JSON en /api/v1/comercial/pagos/
class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Pago  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.entrega <-> JSON en /api/v1/comercial/entregas/
class EntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Entrega  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.reserva_lote <-> JSON en /api/v1/comercial/reservas-lote/
class ReservaLoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReservaLote  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.retiro_lote <-> JSON en /api/v1/comercial/retiros-lote/
class RetiroLoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RetiroLote  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.retiro_aviso <-> JSON en /api/v1/comercial/retiros-aviso/
class RetiroAvisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RetiroAviso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.pedido_recurrente <-> JSON en /api/v1/comercial/pedidos-recurrente/
class PedidoRecurrenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PedidoRecurrente  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.pedido_recurrente_detalle <-> JSON en /api/v1/comercial/pedidos-recurrente-detalle/
class PedidoRecurrenteDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PedidoRecurrenteDetalle  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.permuta <-> JSON en /api/v1/comercial/permutas/
class PermutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Permuta  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# comercial.huella_trazabilidad <-> JSON en /api/v1/comercial/huellas-trazabilidad/
class HuellaTrazabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HuellaTrazabilidad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
