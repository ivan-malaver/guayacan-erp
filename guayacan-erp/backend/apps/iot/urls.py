"""Rutas de /api/v1/iot/ (cómo una dirección web llega a su vista).

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
router.register('dispositivos', views.DispositivoViewSet, basename='iot-dispositivos')  # tabla iot.dispositivo
router.register('sensores', views.SensorViewSet, basename='iot-sensores')  # tabla iot.sensor
router.register('actuadores', views.ActuadorViewSet, basename='iot-actuadores')  # tabla iot.actuador
router.register('lecturas', views.LecturaViewSet, basename='iot-lecturas')  # tabla iot.lectura
router.register('reglas', views.ReglaAutomatizacionViewSet, basename='iot-reglas')  # tabla iot.regla_automatizacion
router.register('comandos', views.ComandoActuadorViewSet, basename='iot-comandos')  # tabla iot.comando_actuador
router.register('zonas-seguridad', views.ZonaSeguridadViewSet, basename='iot-zonas-seguridad')  # tabla iot.zona_seguridad
router.register('cambios-estado-alarma', views.CambioEstadoAlarmaViewSet, basename='iot-cambios-estado-alarma')  # tabla iot.cambio_estado_alarma
router.register('credenciales-acceso', views.CredencialAccesoViewSet, basename='iot-credenciales-acceso')  # tabla iot.credencial_acceso
router.register('camaras', views.CamaraViewSet, basename='iot-camaras')  # tabla iot.camara
router.register('eventos-seguridad', views.EventoSeguridadViewSet, basename='iot-eventos-seguridad')  # tabla iot.evento_seguridad
router.register('clipes-video', views.ClipVideoViewSet, basename='iot-clipes-video')  # tabla iot.clip_video
router.register('misiones-robot', views.MisionRobotViewSet, basename='iot-misiones-robot')  # tabla iot.mision_robot
router.register('prioridades-carga', views.PrioridadCargaViewSet, basename='iot-prioridades-carga')  # tabla iot.prioridad_carga

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # IOT-04 · Armar y desarmar la alarma por zonas: POST /api/v1/iot/zonas-seguridad/{id}/estado/
    path('zonas-seguridad/<int:id>/estado/', PorConstruir.as_view(caso_de_uso='IOT-04', metodo='POST'), name='iot-04-zonas-seguridad-id-estado'),
    # IOT-08 · Planear y ejecutar una misión de dron o robot: POST /api/v1/iot/misiones-robot/{id}/aprobar/
    path('misiones-robot/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='IOT-08', metodo='POST'), name='iot-08-misiones-robot-id-aprobar'),
    # IOT-02 · Recibir lecturas de sensores: POST /api/v1/iot/lecturas/lote/
    path('lecturas/lote/', PorConstruir.as_view(caso_de_uso='IOT-02', metodo='POST'), name='iot-02-lecturas-lote'),
    # IOT-05 · Atender un evento de seguridad perimetral: POST /api/v1/iot/eventos-seguridad/{id}/atender/
    path('eventos-seguridad/<int:id>/atender/', PorConstruir.as_view(caso_de_uso='IOT-05', metodo='POST'), name='iot-05-eventos-seguridad-id-atender'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
