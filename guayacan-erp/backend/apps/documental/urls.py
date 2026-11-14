"""Rutas de /api/v1/documental/ (cómo una dirección web llega a su vista).

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
router.register('documentos', views.DocumentoViewSet, basename='documental-documentos')  # tabla documental.documento
router.register('vinculos-documento', views.VinculoDocumentoViewSet, basename='documental-vinculos-documento')  # tabla documental.vinculo_documento

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # DOC-02 · Vincular documentos y vigilar vencimientos: GET /api/v1/documental/vigentes/
    path('vigentes/', PorConstruir.as_view(caso_de_uso='DOC-02', metodo='GET'), name='doc-02-vigentes'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('documentos/<int:padre>/versiones/', views.VersionDocumentoViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='documento'), name='documental-versiones-lista'),
    path('documentos/<int:padre>/versiones/<int:pk>/', views.VersionDocumentoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='documento'), name='documental-versiones-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
