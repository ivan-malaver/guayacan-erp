"""Rutas de /api/v1/proyectos/ (cómo una dirección web llega a su vista).

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
router.register('proyectos', views.ProyectoViewSet, basename='proyectos-proyectos')  # tabla proyectos.proyecto
router.register('interesados', views.InteresadoViewSet, basename='proyectos-interesados')  # tabla proyectos.interesado
router.register('elementos-edt', views.ElementoEdtViewSet, basename='proyectos-elementos-edt')  # tabla proyectos.elemento_edt
router.register('iteraciones', views.IteracionViewSet, basename='proyectos-iteraciones')  # tabla proyectos.iteracion
router.register('actividades', views.ActividadViewSet, basename='proyectos-actividades')  # tabla proyectos.actividad
router.register('riesgos', views.RiesgoViewSet, basename='proyectos-riesgos')  # tabla proyectos.riesgo
router.register('registros', views.RegistroViewSet, basename='proyectos-registros')  # tabla proyectos.registro
router.register('solicitudes-cambio', views.SolicitudCambioViewSet, basename='proyectos-solicitudes-cambio')  # tabla proyectos.solicitud_cambio
router.register('lineas-base', views.LineaBaseViewSet, basename='proyectos-lineas-base')  # tabla proyectos.linea_base
router.register('mediciones-valor-ganado', views.MedicionValorGanadoViewSet, basename='proyectos-mediciones-valor-ganado')  # tabla proyectos.medicion_valor_ganado

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # PRY-02 · Aprobar un proyecto: POST /api/v1/proyectos/proyectos/{id}/aprobar/
    path('proyectos/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='PRY-02', metodo='POST'), name='pry-02-proyectos-id-aprobar'),
    # PRY-04 · Calcular la ruta crítica: POST /api/v1/proyectos/proyectos/{id}/ruta-critica/
    path('proyectos/<int:id>/ruta-critica/', PorConstruir.as_view(caso_de_uso='PRY-04', metodo='POST'), name='pry-04-proyectos-id-ruta-critica'),
    # PRY-06 · Registrar avance y medir el valor ganado: POST /api/v1/proyectos/proyectos/{id}/valor-ganado/
    path('proyectos/<int:id>/valor-ganado/', PorConstruir.as_view(caso_de_uso='PRY-06', metodo='POST'), name='pry-06-proyectos-id-valor-ganado'),
    # PRY-06 · Registrar avance y medir el valor ganado: GET /api/v1/proyectos/tablero/
    path('tablero/', PorConstruir.as_view(caso_de_uso='PRY-06', metodo='GET'), name='pry-06-tablero'),
    # PRY-07 · Solicitar y decidir un cambio: POST /api/v1/proyectos/solicitudes-cambio/{id}/decidir/
    path('solicitudes-cambio/<int:id>/decidir/', PorConstruir.as_view(caso_de_uso='PRY-07', metodo='POST'), name='pry-07-solicitudes-cambio-id-decidir'),
    # PRY-08 · Aceptar entregables y cerrar el proyecto: POST /api/v1/proyectos/elementos-edt/{id}/aceptar/
    path('elementos-edt/<int:id>/aceptar/', PorConstruir.as_view(caso_de_uso='PRY-08', metodo='POST'), name='pry-08-elementos-edt-id-aceptar'),
    # PRY-08 · Aceptar entregables y cerrar el proyecto: POST /api/v1/proyectos/proyectos/{id}/cerrar/
    path('proyectos/<int:id>/cerrar/', PorConstruir.as_view(caso_de_uso='PRY-08', metodo='POST'), name='pry-08-proyectos-id-cerrar'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('actividades/<int:padre>/dependencias/', views.DependenciaViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='predecesora'), name='proyectos-dependencias-lista'),
    path('actividades/<int:padre>/dependencias/<int:pk>/', views.DependenciaViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='predecesora'), name='proyectos-dependencias-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
