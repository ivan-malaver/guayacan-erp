"""Rutas de /api/v1/seguridad/ (cómo una dirección web llega a su vista).

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
router.register('factores-autenticacion', views.FactorAutenticacionViewSet, basename='seguridad-factores-autenticacion')  # tabla seguridad.factor_autenticacion
router.register('sesiones-usuario', views.SesionUsuarioViewSet, basename='seguridad-sesiones-usuario')  # tabla seguridad.sesion_usuario
router.register('intentos-acceso', views.IntentoAccesoViewSet, basename='seguridad-intentos-acceso')  # tabla seguridad.intento_acceso
router.register('reglas-deteccion', views.ReglaDeteccionViewSet, basename='seguridad-reglas-deteccion')  # tabla seguridad.regla_deteccion
router.register('bloqueos', views.BloqueoViewSet, basename='seguridad-bloqueos')  # tabla seguridad.bloqueo
router.register('senuelos', views.SenueloViewSet, basename='seguridad-senuelos')  # tabla seguridad.senuelo
router.register('alertas-seguridad', views.AlertaSeguridadViewSet, basename='seguridad-alertas-seguridad')  # tabla seguridad.alerta_seguridad
router.register('incidentes', views.IncidenteViewSet, basename='seguridad-incidentes')  # tabla seguridad.incidente
router.register('ejecuciones-prueba', views.EjecucionPruebaViewSet, basename='seguridad-ejecuciones-prueba')  # tabla seguridad.ejecucion_prueba
router.register('copias-seguridad', views.CopiaSeguridadViewSet, basename='seguridad-copias-seguridad')  # tabla seguridad.copia_seguridad

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # SEG-04 · Atender una alerta o un incidente de seguridad: GET /api/v1/seguridad/tablero/
    path('tablero/', PorConstruir.as_view(caso_de_uso='SEG-04', metodo='GET'), name='seg-04-tablero'),
    # SEG-05 · Revocar sesiones y levantar bloqueos: POST /api/v1/seguridad/sesiones/{id}/revocar/
    path('sesiones/<int:id>/revocar/', PorConstruir.as_view(caso_de_uso='SEG-05', metodo='POST'), name='seg-05-sesiones-id-revocar'),
    # SEG-05 · Revocar sesiones y levantar bloqueos: POST /api/v1/seguridad/bloqueos/{id}/levantar/
    path('bloqueos/<int:id>/levantar/', PorConstruir.as_view(caso_de_uso='SEG-05', metodo='POST'), name='seg-05-bloqueos-id-levantar'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
