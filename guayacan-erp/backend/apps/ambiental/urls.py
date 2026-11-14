"""Rutas de /api/v1/ambiental/ (cómo una dirección web llega a su vista).

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
router.register('factores-emision', views.FactorEmisionViewSet, basename='ambiental-factores-emision')  # tabla ambiental.factor_emision
router.register('registros-ambiental', views.RegistroAmbientalViewSet, basename='ambiental-registros-ambiental')  # tabla ambiental.registro_ambiental

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # AMB-03 · Consultar indicadores ambientales y CO₂ estimado: GET /api/v1/ambiental/indicadores/
    path('indicadores/', PorConstruir.as_view(caso_de_uso='AMB-03', metodo='GET'), name='amb-03-indicadores'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
