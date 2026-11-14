"""Rutas de /api/v1/redes/ (cómo una dirección web llega a su vista).

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
router.register('cuentas-red', views.CuentaRedViewSet, basename='redes-cuentas-red')  # tabla redes.cuenta_red
router.register('publicaciones', views.PublicacionViewSet, basename='redes-publicaciones')  # tabla redes.publicacion
router.register('politicas-canal', views.PoliticaCanalViewSet, basename='redes-politicas-canal')  # tabla redes.politica_canal
router.register('plantillas-mensaje', views.PlantillaMensajeViewSet, basename='redes-plantillas-mensaje')  # tabla redes.plantilla_mensaje
router.register('mensajes-salientes', views.MensajeSalienteViewSet, basename='redes-mensajes-salientes')  # tabla redes.mensaje_saliente
router.register('piezas-audiovisual', views.PiezaAudiovisualViewSet, basename='redes-piezas-audiovisual')  # tabla redes.pieza_audiovisual
router.register('piezas-persona', views.PiezaPersonaViewSet, basename='redes-piezas-persona')  # tabla redes.pieza_persona

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # RED-03 · Enviar un mensaje saliente dentro de las reglas del canal: POST /api/v1/redes/mensajes-salientes/verificar/
    path('mensajes-salientes/verificar/', PorConstruir.as_view(caso_de_uso='RED-03', metodo='POST'), name='red-03-mensajes-salientes-verificar'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
