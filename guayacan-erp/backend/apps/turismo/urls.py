"""Rutas de /api/v1/turismo/ (cómo una dirección web llega a su vista).

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
router.register('alojamientos', views.AlojamientoViewSet, basename='turismo-alojamientos')  # tabla turismo.alojamiento
router.register('planes-turistico', views.PlanTuristicoViewSet, basename='turismo-planes-turistico')  # tabla turismo.plan_turistico
router.register('reservas', views.ReservaViewSet, basename='turismo-reservas')  # tabla turismo.reserva
router.register('bloqueos-calendario', views.BloqueoCalendarioViewSet, basename='turismo-bloqueos-calendario')  # tabla turismo.bloqueo_calendario

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # TUR-03 · Pagar anticipadamente una reserva: POST /api/v1/turismo/reservas/{id}/pagar/
    path('reservas/<int:id>/pagar/', PorConstruir.as_view(caso_de_uso='TUR-03', metodo='POST'), name='tur-03-reservas-id-pagar'),
    # TUR-04 · Hacer check-in y check-out de huéspedes: POST /api/v1/turismo/reservas/{id}/check-in/
    path('reservas/<int:id>/check-in/', PorConstruir.as_view(caso_de_uso='TUR-04', metodo='POST'), name='tur-04-reservas-id-check-in'),
    # TUR-04 · Hacer check-in y check-out de huéspedes: POST /api/v1/turismo/reservas/{id}/check-out/
    path('reservas/<int:id>/check-out/', PorConstruir.as_view(caso_de_uso='TUR-04', metodo='POST'), name='tur-04-reservas-id-check-out'),
    # TUR-05 · Atender la solicitud de un grupo: POST /api/v1/turismo/solicitudes-grupo/
    path('solicitudes-grupo/', PorConstruir.as_view(caso_de_uso='TUR-05', metodo='POST'), name='tur-05-solicitudes-grupo'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
