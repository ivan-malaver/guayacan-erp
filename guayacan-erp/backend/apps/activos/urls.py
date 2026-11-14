"""Rutas de /api/v1/activos/ (cómo una dirección web llega a su vista).

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
router.register('activos', views.ActivoViewSet, basename='activos-activos')  # tabla activos.activo
router.register('planes-mantenimiento', views.PlanMantenimientoViewSet, basename='activos-planes-mantenimiento')  # tabla activos.plan_mantenimiento
router.register('ordenes-trabajo', views.OrdenTrabajoViewSet, basename='activos-ordenes-trabajo')  # tabla activos.orden_trabajo
router.register('usos-activo', views.UsoActivoViewSet, basename='activos-usos-activo')  # tabla activos.uso_activo
router.register('depreciaciones', views.DepreciacionViewSet, basename='activos-depreciaciones')  # tabla activos.depreciacion

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # ACT-03 · Generar y cerrar órdenes de mantenimiento: POST /api/v1/activos/ordenes-trabajo/generar/
    path('ordenes-trabajo/generar/', PorConstruir.as_view(caso_de_uso='ACT-03', metodo='POST'), name='act-03-ordenes-trabajo-generar'),
    # ACT-04 · Depreciar los activos del mes: POST /api/v1/activos/depreciar/
    path('depreciar/', PorConstruir.as_view(caso_de_uso='ACT-04', metodo='POST'), name='act-04-depreciar'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('ordenes-trabajo/<int:padre>/repuestos/', views.RepuestoOrdenViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='orden'), name='activos-repuestos-lista'),
    path('ordenes-trabajo/<int:padre>/repuestos/<int:pk>/', views.RepuestoOrdenViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='orden'), name='activos-repuestos-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
