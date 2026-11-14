"""Vistas (endpoints CRUD) del esquema compras.

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
from guayacan.vistas import VistaModelo

from . import models, serializers


# CRUD de compras.orden_compra en /api/v1/compras/ordenes-compra/
class OrdenCompraViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.OrdenCompra.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.OrdenCompraSerializer


# CRUD de compras.orden_compra_detalle en /api/v1/compras/ordenes-compra/{id}/lineas/
class OrdenCompraDetalleViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.OrdenCompraDetalle.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.OrdenCompraDetalleSerializer


# CRUD de compras.cotizacion_proveedor en /api/v1/compras/cotizaciones-proveedor/
class CotizacionProveedorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CotizacionProveedor.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CotizacionProveedorSerializer


# CRUD de compras.precio_mercado en /api/v1/compras/precios-mercado/
class PrecioMercadoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PrecioMercado.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PrecioMercadoSerializer


# CRUD de compras.documento_soporte en /api/v1/compras/documentos-soporte/
class DocumentoSoporteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.DocumentoSoporte.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DocumentoSoporteSerializer
