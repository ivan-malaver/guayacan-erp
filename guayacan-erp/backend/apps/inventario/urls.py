"""Rutas de /api/v1/inventario/ (cómo una dirección web llega a su vista).

ORDEN
1. Primero las acciones de los casos de uso. Mientras no se construyan usan PorConstruir, que responde
   501 con el código del caso de uso: el frontend y la documentación OpenAPI ya las conocen.
2. Después las rutas anidadas (hijos de un registro, p. ej. las líneas de un pedido), si las hay.
3. Al final el CRUD de cada tabla, que registra el «router» de Django REST Framework.

CÓMO CONSTRUIR UNA ACCIÓN: escriba la vista real (o un método @action en views.py) y reemplace aquí
PorConstruir por esa vista. Generado por docs/uml/fuentes/gen_apps.py."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from guayacan.vistas import PorConstruir, PorConstruirPublico  # noqa: F401

from . import views

# El router crea las rutas de lista (/recurso/) y detalle (/recurso/<id>/) de cada ViewSet
router = DefaultRouter()
router.register('unidades-medida', views.UnidadMedidaViewSet, basename='inventario-unidades-medida')  # tabla inventario.unidad_medida
router.register('categorias-producto', views.CategoriaProductoViewSet, basename='inventario-categorias-producto')  # tabla inventario.categoria_producto
router.register('productos', views.ProductoViewSet, basename='inventario-productos')  # tabla inventario.producto
router.register('bodegas', views.BodegaViewSet, basename='inventario-bodegas')  # tabla inventario.bodega
router.register('lotes-inventario', views.LoteInventarioViewSet, basename='inventario-lotes-inventario')  # tabla inventario.lote_inventario
router.register('movimientos-inventario', views.MovimientoInventarioViewSet, basename='inventario-movimientos-inventario')  # tabla inventario.movimiento_inventario
router.register('etiquetas', views.EtiquetaViewSet, basename='inventario-etiquetas')  # tabla inventario.etiqueta
router.register('lecturas-codigo', views.LecturaCodigoViewSet, basename='inventario-lecturas-codigo')  # tabla inventario.lectura_codigo
router.register('pesajes', views.PesajeViewSet, basename='inventario-pesajes')  # tabla inventario.pesaje
router.register('conteos', views.ConteoFisicoViewSet, basename='inventario-conteos')  # tabla inventario.conteo_fisico
router.register('vehiculos', views.VehiculoViewSet, basename='inventario-vehiculos')  # tabla inventario.vehiculo
router.register('excursiones-temperatura', views.ExcursionTemperaturaViewSet, basename='inventario-excursiones-temperatura')  # tabla inventario.excursion_temperatura
router.register('bloqueos-lote', views.BloqueoLoteViewSet, basename='inventario-bloqueos-lote')  # tabla inventario.bloqueo_lote

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # INV-06 · Vigilar vencimientos y liquidar: GET /api/v1/inventario/alertas-vencimiento/
    path('alertas-vencimiento/', PorConstruir.as_view(caso_de_uso='INV-06', metodo='GET'), name='inv-06-alertas-vencimiento'),
    # INV-07 · Vigilar la cadena de frío y decidir sobre un lote bloqueado: POST /api/v1/inventario/bloqueos-lote/{id}/decidir/
    path('bloqueos-lote/<int:id>/decidir/', PorConstruir.as_view(caso_de_uso='INV-07', metodo='POST'), name='inv-07-bloqueos-lote-id-decidir'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('conteos/<int:padre>/detalles/', views.ConteoDetalleViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='conteo_fisico'), name='inventario-detalles-lista'),
    path('conteos/<int:padre>/detalles/<int:pk>/', views.ConteoDetalleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='conteo_fisico'), name='inventario-detalles-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
