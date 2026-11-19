"""Rutas de /api/v1/agenda/ (cómo una dirección web llega a su vista).

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
router.register('recursos', views.RecursoViewSet, basename='agenda-recursos')  # tabla agenda.recurso
router.register('citas', views.CitaViewSet, basename='agenda-citas')  # tabla agenda.cita
router.register('visitas', views.VisitaViewSet, basename='agenda-visitas')  # tabla agenda.visita
router.register('registros-acceso', views.RegistroAccesoViewSet, basename='agenda-registros-acceso')  # tabla agenda.registro_acceso

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # TUR-02 · Reservar una cabaña o un plan: GET /api/v1/agenda/recursos/{id}/disponible/
    path('recursos/<int:id>/disponible/', PorConstruir.as_view(caso_de_uso='TUR-02', metodo='GET'), name='tur-02-recursos-id-disponible'),
    # AGD-03 · Programar y aprobar una visita: POST /api/v1/agenda/visitas/{id}/aprobar/
    path('visitas/<int:id>/aprobar/', views.AprobarVisita.as_view(), name='agd-03-visitas-id-aprobar'),
    # AGD-03 · Programar y aprobar una visita: POST /api/v1/agenda/visitas/{id}/pase/
    path('visitas/<int:id>/pase/', views.PaseVisita.as_view(), name='agd-03-visitas-id-pase'),
    # AGD-05 · Consultar quién está en la finca: GET /api/v1/agenda/en-sitio/
    path('en-sitio/', PorConstruir.as_view(caso_de_uso='AGD-05', metodo='GET'), name='agd-05-sitio'),
    # AGD-06 · Consultar la agenda del día: GET /api/v1/agenda/dia/
    path('dia/', PorConstruir.as_view(caso_de_uso='AGD-06', metodo='GET'), name='agd-06-dia'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
