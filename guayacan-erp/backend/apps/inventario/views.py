"""Vistas (endpoints CRUD) del esquema inventario.

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


# CRUD de inventario.unidad_medida en /api/v1/inventario/unidades-medida/
class UnidadMedidaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.UnidadMedida.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.UnidadMedidaSerializer


# CRUD de inventario.categoria_producto en /api/v1/inventario/categorias-producto/
class CategoriaProductoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CategoriaProducto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CategoriaProductoSerializer


# CRUD de inventario.producto en /api/v1/inventario/productos/
class ProductoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Producto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ProductoSerializer


# CRUD de inventario.bodega en /api/v1/inventario/bodegas/
class BodegaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Bodega.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BodegaSerializer


# CRUD de inventario.lote_inventario en /api/v1/inventario/lotes-inventario/
class LoteInventarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LoteInventario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LoteInventarioSerializer


# CRUD de inventario.movimiento_inventario en /api/v1/inventario/movimientos-inventario/
class MovimientoInventarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MovimientoInventario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MovimientoInventarioSerializer


# CRUD de inventario.etiqueta en /api/v1/inventario/etiquetas/
class EtiquetaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Etiqueta.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EtiquetaSerializer


# CRUD de inventario.lectura_codigo en /api/v1/inventario/lecturas-codigo/
class LecturaCodigoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LecturaCodigo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LecturaCodigoSerializer


# CRUD de inventario.pesaje en /api/v1/inventario/pesajes/
class PesajeViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Pesaje.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PesajeSerializer


# CRUD de inventario.conteo_fisico en /api/v1/inventario/conteos/
class ConteoFisicoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ConteoFisico.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ConteoFisicoSerializer


# CRUD de inventario.conteo_detalle en /api/v1/inventario/conteos/{id}/detalles/
class ConteoDetalleViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ConteoDetalle.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ConteoDetalleSerializer


# CRUD de inventario.vehiculo en /api/v1/inventario/vehiculos/
class VehiculoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Vehiculo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.VehiculoSerializer


# CRUD de inventario.excursion_temperatura en /api/v1/inventario/excursiones-temperatura/
class ExcursionTemperaturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ExcursionTemperatura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ExcursionTemperaturaSerializer


# CRUD de inventario.bloqueo_lote en /api/v1/inventario/bloqueos-lote/
class BloqueoLoteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.BloqueoLote.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BloqueoLoteSerializer
