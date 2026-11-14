"""Rutas de /api/v1/comercial/ (cómo una dirección web llega a su vista).

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
router.register('listas-precios', views.ListaPreciosViewSet, basename='comercial-listas-precios')  # tabla comercial.lista_precios
router.register('precios-producto', views.PrecioProductoViewSet, basename='comercial-precios-producto')  # tabla comercial.precio_producto
router.register('propuestas-precio', views.PropuestaPrecioViewSet, basename='comercial-propuestas-precio')  # tabla comercial.propuesta_precio
router.register('pedidos', views.PedidoViewSet, basename='comercial-pedidos')  # tabla comercial.pedido
router.register('facturas', views.FacturaViewSet, basename='comercial-facturas')  # tabla comercial.factura
router.register('pagos', views.PagoViewSet, basename='comercial-pagos')  # tabla comercial.pago
router.register('entregas', views.EntregaViewSet, basename='comercial-entregas')  # tabla comercial.entrega
router.register('reservas-lote', views.ReservaLoteViewSet, basename='comercial-reservas-lote')  # tabla comercial.reserva_lote
router.register('retiros-lote', views.RetiroLoteViewSet, basename='comercial-retiros-lote')  # tabla comercial.retiro_lote
router.register('retiros-aviso', views.RetiroAvisoViewSet, basename='comercial-retiros-aviso')  # tabla comercial.retiro_aviso
router.register('pedidos-recurrente', views.PedidoRecurrenteViewSet, basename='comercial-pedidos-recurrente')  # tabla comercial.pedido_recurrente
router.register('pedidos-recurrente-detalle', views.PedidoRecurrenteDetalleViewSet, basename='comercial-pedidos-recurrente-detalle')  # tabla comercial.pedido_recurrente_detalle
router.register('permutas', views.PermutaViewSet, basename='comercial-permutas')  # tabla comercial.permuta
router.register('huellas-trazabilidad', views.HuellaTrazabilidadViewSet, basename='comercial-huellas-trazabilidad')  # tabla comercial.huella_trazabilidad

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # VTA-02 · Proponer y aprobar un cambio de precio: POST /api/v1/comercial/propuestas-precio/{id}/aprobar/
    path('propuestas-precio/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='VTA-02', metodo='POST'), name='vta-02-propuestas-precio-id-aprobar'),
    # VTA-03 · Tomar y confirmar un pedido: POST /api/v1/comercial/pedidos/{id}/confirmar/
    path('pedidos/<int:id>/confirmar/', PorConstruir.as_view(caso_de_uso='VTA-03', metodo='POST'), name='vta-03-pedidos-id-confirmar'),
    # VTA-05 · Despachar y entregar un pedido: POST /api/v1/comercial/pedidos/{id}/despachar/
    path('pedidos/<int:id>/despachar/', PorConstruir.as_view(caso_de_uso='VTA-05', metodo='POST'), name='vta-05-pedidos-id-despachar'),
    # VTA-06 · Facturar electrónicamente: POST /api/v1/comercial/pedidos/{id}/facturar/
    path('pedidos/<int:id>/facturar/', PorConstruir.as_view(caso_de_uso='VTA-06', metodo='POST'), name='vta-06-pedidos-id-facturar'),
    # VTA-07 · Registrar y confirmar un pago: POST /api/v1/comercial/pagos/{id}/confirmar/
    path('pagos/<int:id>/confirmar/', PorConstruir.as_view(caso_de_uso='VTA-07', metodo='POST'), name='vta-07-pagos-id-confirmar'),
    # VTA-08 · Vender a crédito y controlar la cartera: GET /api/v1/comercial/cartera/
    path('cartera/', PorConstruir.as_view(caso_de_uso='VTA-08', metodo='GET'), name='vta-08-cartera'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('pedidos/<int:padre>/lineas/', views.PedidoDetalleViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='pedido'), name='comercial-lineas-lista'),
    path('pedidos/<int:padre>/lineas/<int:pk>/', views.PedidoDetalleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='pedido'), name='comercial-lineas-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
