"""Rutas de /api/v1/compras/ (cómo una dirección web llega a su vista).

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
router.register('ordenes-compra', views.OrdenCompraViewSet, basename='compras-ordenes-compra')  # tabla compras.orden_compra
router.register('cotizaciones-proveedor', views.CotizacionProveedorViewSet, basename='compras-cotizaciones-proveedor')  # tabla compras.cotizacion_proveedor
router.register('precios-mercado', views.PrecioMercadoViewSet, basename='compras-precios-mercado')  # tabla compras.precio_mercado
router.register('documentos-soporte', views.DocumentoSoporteViewSet, basename='compras-documentos-soporte')  # tabla compras.documento_soporte

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # CMP-02 · Crear y aprobar una orden de compra: POST /api/v1/compras/ordenes-compra/{id}/aprobar/
    path('ordenes-compra/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='CMP-02', metodo='POST'), name='cmp-02-ordenes-compra-id-aprobar'),
    # CMP-03 · Recibir una compra en bodega: POST /api/v1/compras/ordenes-compra/{id}/recibir/
    path('ordenes-compra/<int:id>/recibir/', PorConstruir.as_view(caso_de_uso='CMP-03', metodo='POST'), name='cmp-03-ordenes-compra-id-recibir'),
    # CMP-04 · Emitir un documento soporte electrónico: POST /api/v1/compras/documentos-soporte/{id}/transmitir/
    path('documentos-soporte/<int:id>/transmitir/', PorConstruir.as_view(caso_de_uso='CMP-04', metodo='POST'), name='cmp-04-documentos-soporte-id-transmitir'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('ordenes-compra/<int:padre>/lineas/', views.OrdenCompraDetalleViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='orden_compra'), name='compras-lineas-lista'),
    path('ordenes-compra/<int:padre>/lineas/<int:pk>/', views.OrdenCompraDetalleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='orden_compra'), name='compras-lineas-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
