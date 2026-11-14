"""Rutas de /api/v1/crm/ (cómo una dirección web llega a su vista).

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
router.register('segmentos', views.SegmentoViewSet, basename='crm-segmentos')  # tabla crm.segmento
router.register('campanas', views.CampanaViewSet, basename='crm-campanas')  # tabla crm.campana
router.register('formularios-captura', views.FormularioCapturaViewSet, basename='crm-formularios-captura')  # tabla crm.formulario_captura
router.register('prospectos', views.ProspectoViewSet, basename='crm-prospectos')  # tabla crm.prospecto
router.register('contactos-empresa', views.ContactoEmpresaViewSet, basename='crm-contactos-empresa')  # tabla crm.contacto_empresa
router.register('interacciones', views.InteraccionViewSet, basename='crm-interacciones')  # tabla crm.interaccion
router.register('oportunidades', views.OportunidadViewSet, basename='crm-oportunidades')  # tabla crm.oportunidad

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # CRM-01 · Capturar un posible cliente con autorización: POST /api/v1/crm/captura/{formulario}/ (pública, sin sesión)
    path('captura/<str:formulario>/', PorConstruirPublico.as_view(caso_de_uso='CRM-01', metodo='POST'), name='crm-01-captura-formulario'),
    # CRM-04 · Calificar los prospectos: POST /api/v1/crm/prospectos/{id}/calificar/
    path('prospectos/<int:id>/calificar/', PorConstruir.as_view(caso_de_uso='CRM-04', metodo='POST'), name='crm-04-prospectos-id-calificar'),
    # CRM-05 · Convertir un prospecto en cliente: POST /api/v1/crm/prospectos/{id}/convertir/
    path('prospectos/<int:id>/convertir/', PorConstruir.as_view(caso_de_uso='CRM-05', metodo='POST'), name='crm-05-prospectos-id-convertir'),
    # CRM-06 · Gestionar oportunidades y proyectar ventas: GET /api/v1/crm/embudo/
    path('embudo/', PorConstruir.as_view(caso_de_uso='CRM-06', metodo='GET'), name='crm-06-embudo'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
