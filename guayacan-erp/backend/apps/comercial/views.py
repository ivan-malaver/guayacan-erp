"""Vistas (endpoints CRUD) del esquema comercial.

QUÉ HACE UNA VISTA
Recibe la petición HTTP, usa el serializer para validar o convertir los datos y responde. Cada clase de abajo
es un «ViewSet»: una sola clase atiende varias rutas de la misma tabla.

QUÉ OPERACIONES OFRECE (heredadas de guayacan.vistas.VistaModelo)
  GET    /recurso/        lista paginada (50 por página; ?pagina=2&tamano=100)
  GET    /recurso/{id}/   detalle de un registro
  POST   /recurso/        crear
  PUT o PATCH /recurso/{id}/   modificar todo o una parte
  No hay DELETE: en GuayacanERP los registros se desactivan, se anulan o se cierran, no se borran.

La seguridad no se programa aquí: el middleware fija la finca y el usuario, y PostgreSQL solo deja ver y
cambiar lo de esa finca. Las acciones de los casos de uso (aprobar, confirmar, liquidar...) están en urls.py.
Generado por docs/uml/fuentes/gen_apps.py."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from guayacan.permisos import SoloPersonas, requiere
from guayacan.vistas import VistaModelo

from . import models, serializers, services


# CRUD de comercial.lista_precios en /api/v1/comercial/listas-precios/
class ListaPreciosViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ListaPrecios.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ListaPreciosSerializer


# CRUD de comercial.precio_producto en /api/v1/comercial/precios-producto/
class PrecioProductoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PrecioProducto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PrecioProductoSerializer


# CRUD de comercial.propuesta_precio en /api/v1/comercial/propuestas-precio/
class PropuestaPrecioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PropuestaPrecio.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PropuestaPrecioSerializer


# CRUD de comercial.pedido en /api/v1/comercial/pedidos/
class PedidoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Pedido.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PedidoSerializer

    def perform_create(self, serializer):
        serializer.instance = services.crear_pedido(usuario=self.request.user, **serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.actualizar_pedido(usuario=self.request.user, pedido_id=serializer.instance.pk,
                                                         **serializer.validated_data)


# CRUD de comercial.pedido_detalle en /api/v1/comercial/pedidos/{id}/lineas/
class PedidoDetalleViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PedidoDetalle.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PedidoDetalleSerializer

    def perform_create(self, serializer):
        serializer.instance = services.guardar_linea(usuario=self.request.user, pedido_id=self.kwargs['padre'],
                                                     **serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.guardar_linea(usuario=self.request.user, pedido_id=self.kwargs['padre'],
                                                     linea=serializer.instance, **serializer.validated_data)


class ConfirmarPedido(APIView):
    """VTA-03 · POST /api/v1/comercial/pedidos/{id}/confirmar/: un vendedor o el administrador confirma el borrador."""

    permission_classes = [IsAuthenticated, SoloPersonas, requiere('comercial.confirmar_pedido')]

    def post(self, request, id):
        return Response(serializers.PedidoSerializer(services.vta_03_tomar_confirmar_pedido(usuario=request.user, pedido_id=id)).data)


class CancelarPedido(APIView):
    """VTA-03 5a · POST /api/v1/comercial/pedidos/{id}/cancelar/: libera las reservas si aún no salió de la finca."""

    permission_classes = [IsAuthenticated, SoloPersonas, requiere('comercial.confirmar_pedido')]

    def post(self, request, id):
        return Response(serializers.PedidoSerializer(services.cancelar_pedido(usuario=request.user, pedido_id=id)).data)


# CRUD de comercial.factura en /api/v1/comercial/facturas/
class FacturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Factura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FacturaSerializer


# CRUD de comercial.pago en /api/v1/comercial/pagos/
class PagoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Pago.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PagoSerializer


# CRUD de comercial.entrega en /api/v1/comercial/entregas/
class EntregaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Entrega.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EntregaSerializer


# CRUD de comercial.reserva_lote en /api/v1/comercial/reservas-lote/
class ReservaLoteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ReservaLote.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ReservaLoteSerializer


# CRUD de comercial.retiro_lote en /api/v1/comercial/retiros-lote/
class RetiroLoteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RetiroLote.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RetiroLoteSerializer


# CRUD de comercial.retiro_aviso en /api/v1/comercial/retiros-aviso/
class RetiroAvisoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RetiroAviso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RetiroAvisoSerializer


# CRUD de comercial.pedido_recurrente en /api/v1/comercial/pedidos-recurrente/
class PedidoRecurrenteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PedidoRecurrente.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PedidoRecurrenteSerializer


# CRUD de comercial.pedido_recurrente_detalle en /api/v1/comercial/pedidos-recurrente-detalle/
class PedidoRecurrenteDetalleViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PedidoRecurrenteDetalle.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PedidoRecurrenteDetalleSerializer


# CRUD de comercial.permuta en /api/v1/comercial/permutas/
class PermutaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Permuta.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PermutaSerializer


# CRUD de comercial.huella_trazabilidad en /api/v1/comercial/huellas-trazabilidad/
class HuellaTrazabilidadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.HuellaTrazabilidad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.HuellaTrazabilidadSerializer
