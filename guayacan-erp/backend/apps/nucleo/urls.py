"""Rutas de /api/v1/nucleo/ (cómo una dirección web llega a su vista).

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
router.register('usuarios', views.UsuarioViewSet, basename='nucleo-usuarios')  # tabla nucleo.usuario
router.register('roles', views.RolViewSet, basename='nucleo-roles')  # tabla nucleo.rol
router.register('permisos', views.PermisoViewSet, basename='nucleo-permisos')  # tabla nucleo.permiso
router.register('parametros', views.ParametroViewSet, basename='nucleo-parametros')  # tabla nucleo.parametro
router.register('auditoria', views.AuditoriaViewSet, basename='nucleo-auditoria')  # tabla nucleo.auditoria
router.register('eventos-salida', views.EventoSalidaViewSet, basename='nucleo-eventos-salida')  # tabla nucleo.evento_salida
router.register('predios', views.PredioViewSet, basename='nucleo-predios')  # tabla nucleo.predio
router.register('zonas', views.ZonaViewSet, basename='nucleo-zonas')  # tabla nucleo.zona
router.register('dispositivos-captura', views.DispositivoCapturaViewSet, basename='nucleo-dispositivos-captura')  # tabla nucleo.dispositivo_captura
router.register('sincronizaciones', views.SincronizacionViewSet, basename='nucleo-sincronizaciones')  # tabla nucleo.sincronizacion
router.register('funcionalidades', views.FuncionalidadViewSet, basename='nucleo-funcionalidades')  # tabla nucleo.funcionalidad
router.register('notas-voz', views.NotaVozViewSet, basename='nucleo-notas-voz')  # tabla nucleo.nota_voz
router.register('llaves-api', views.LlaveApiViewSet, basename='nucleo-llaves-api')  # tabla nucleo.llave_api
router.register('webhooks-suscripcion', views.WebhookSuscripcionViewSet, basename='nucleo-webhooks-suscripcion')  # tabla nucleo.webhook_suscripcion
router.register('webhooks-entrega', views.WebhookEntregaViewSet, basename='nucleo-webhooks-entrega')  # tabla nucleo.webhook_entrega

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # NUC-07 · Registrar una nota de voz en campo y confirmarla: POST /api/v1/nucleo/notas-voz/{id}/confirmar/
    path('notas-voz/<int:id>/confirmar/', PorConstruir.as_view(caso_de_uso='NUC-07', metodo='POST'), name='nuc-07-notas-voz-id-confirmar'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('roles/<int:padre>/permisos/', views.RolPermisoViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='rol'), name='nucleo-permisos-lista'),
    path('roles/<int:padre>/permisos/<int:pk>/', views.RolPermisoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='rol'), name='nucleo-permisos-detalle'),
    path('usuarios/<int:padre>/roles/', views.UsuarioRolViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='usuario'), name='nucleo-roles-lista'),
    path('usuarios/<int:padre>/roles/<int:pk>/', views.UsuarioRolViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='usuario'), name='nucleo-roles-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
