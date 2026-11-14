"""Rutas de /api/v1/terceros/ (cómo una dirección web llega a su vista).

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
router.register('terceros', views.TerceroViewSet, basename='terceros-terceros')  # tabla terceros.tercero
router.register('consentimientos', views.ConsentimientoDatosViewSet, basename='terceros-consentimientos')  # tabla terceros.consentimiento_datos
router.register('clientes', views.ClienteViewSet, basename='terceros-clientes')  # tabla terceros.cliente
router.register('proveedores', views.ProveedorViewSet, basename='terceros-proveedores')  # tabla terceros.proveedor
router.register('empleados', views.EmpleadoViewSet, basename='terceros-empleados')  # tabla terceros.empleado

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # TER-03 · Atender una solicitud del titular de datos: GET /api/v1/terceros/{id}/datos-personales/
    path('<int:id>/datos-personales/', PorConstruir.as_view(caso_de_uso='TER-03', metodo='GET'), name='ter-03-id-datos-personales'),
    # TER-02 · Registrar y revocar una autorización de datos: POST /api/v1/terceros/consentimientos/{id}/revocar/
    path('consentimientos/<int:id>/revocar/', PorConstruir.as_view(caso_de_uso='TER-02', metodo='POST'), name='ter-02-consentimientos-id-revocar'),
    # TER-03 · Atender una solicitud del titular de datos: POST /api/v1/terceros/terceros/{id}/anonimizar/
    path('terceros/<int:id>/anonimizar/', PorConstruir.as_view(caso_de_uso='TER-03', metodo='POST'), name='ter-03-terceros-id-anonimizar'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
