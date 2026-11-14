"""Rutas de /api/v1/seguros/ (cómo una dirección web llega a su vista).

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
router.register('polizas', views.PolizaViewSet, basename='seguros-polizas')  # tabla seguros.poliza
router.register('bienes-asegurados', views.BienAseguradoViewSet, basename='seguros-bienes-asegurados')  # tabla seguros.bien_asegurado
router.register('indices-poliza', views.IndicePolizaViewSet, basename='seguros-indices-poliza')  # tabla seguros.indice_poliza
router.register('avisos-siniestro', views.AvisoSiniestroViewSet, basename='seguros-avisos-siniestro')  # tabla seguros.aviso_siniestro

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # SGR-03 · Registrar y enviar un aviso de siniestro: POST /api/v1/seguros/avisos-siniestro/{id}/revisar/
    path('avisos-siniestro/<int:id>/revisar/', PorConstruir.as_view(caso_de_uso='SGR-03', metodo='POST'), name='sgr-03-avisos-siniestro-id-revisar'),
    # SGR-03 · Registrar y enviar un aviso de siniestro: POST /api/v1/seguros/avisos-siniestro/{id}/enviar/
    path('avisos-siniestro/<int:id>/enviar/', PorConstruir.as_view(caso_de_uso='SGR-03', metodo='POST'), name='sgr-03-avisos-siniestro-id-enviar'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
