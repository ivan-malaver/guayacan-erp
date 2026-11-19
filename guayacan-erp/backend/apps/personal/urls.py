"""Rutas de /api/v1/personal/ (cómo una dirección web llega a su vista).

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
router.register('cuadrillas', views.CuadrillaViewSet, basename='personal-cuadrillas')  # tabla personal.cuadrilla
router.register('cuadrillas-miembro', views.CuadrillaMiembroViewSet, basename='personal-cuadrillas-miembro')  # tabla personal.cuadrilla_miembro
router.register('turnos', views.TurnoViewSet, basename='personal-turnos')  # tabla personal.turno
router.register('ausencias', views.AusenciaViewSet, basename='personal-ausencias')  # tabla personal.ausencia
router.register('plantillas-tarea', views.PlantillaTareaViewSet, basename='personal-plantillas-tarea')  # tabla personal.plantilla_tarea
router.register('tareas', views.TareaViewSet, basename='personal-tareas')  # tabla personal.tarea
router.register('matrices-responsabilidad', views.MatrizResponsabilidadViewSet, basename='personal-matrices-responsabilidad')  # tabla personal.matriz_responsabilidad
router.register('asignaciones-equipo', views.AsignacionEquipoViewSet, basename='personal-asignaciones-equipo')  # tabla personal.asignacion_equipo
router.register('credenciales-trabajo', views.CredencialTrabajoViewSet, basename='personal-credenciales-trabajo')  # tabla personal.credencial_trabajo
router.register('jornadas', views.JornadaViewSet, basename='personal-jornadas')  # tabla personal.jornada
router.register('areas-responsabilidad', views.AreaResponsabilidadViewSet, basename='personal-areas-responsabilidad')  # tabla personal.area_responsabilidad
router.register('miembros-area', views.MiembroAreaViewSet, basename='personal-miembros-area')  # tabla personal.miembro_area
router.register('patrones-turno', views.PatronTurnoViewSet, basename='personal-patrones-turno')  # tabla personal.patron_turno
router.register('cronogramas', views.CronogramaViewSet, basename='personal-cronogramas')  # tabla personal.cronograma
router.register('asignaciones-patron', views.AsignacionPatronViewSet, basename='personal-asignaciones-patron')  # tabla personal.asignacion_patron
router.register('requerimientos-cobertura', views.RequerimientoCoberturaViewSet, basename='personal-requerimientos-cobertura')  # tabla personal.requerimiento_cobertura
router.register('disponibilidades', views.DisponibilidadViewSet, basename='personal-disponibilidades')  # tabla personal.disponibilidad

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # PER-03 · Generar las tareas del día: POST /api/v1/personal/tareas/generar-dia/
    path('tareas/generar-dia/', PorConstruir.as_view(caso_de_uso='PER-03', metodo='POST'), name='per-03-tareas-generar-dia'),
    # PER-06 · Aprobar o devolver una tarea: POST /api/v1/personal/tareas/{id}/aprobar/
    path('tareas/<int:id>/aprobar/', views.RevisarTarea.as_view(decision='aprobar'), name='per-06-tareas-id-aprobar'),
    # PER-07 · Armar y publicar el cronograma de turnos: POST /api/v1/personal/cronogramas/{id}/generar/
    path('cronogramas/<int:id>/generar/', PorConstruir.as_view(caso_de_uso='PER-07', metodo='POST'), name='per-07-cronogramas-id-generar'),
    # PER-07 · Armar y publicar el cronograma de turnos: GET /api/v1/personal/cronogramas/{id}/huecos/
    path('cronogramas/<int:id>/huecos/', PorConstruir.as_view(caso_de_uso='PER-07', metodo='GET'), name='per-07-cronogramas-id-huecos'),
    # PER-07 · Armar y publicar el cronograma de turnos: POST /api/v1/personal/cronogramas/{id}/publicar/
    path('cronogramas/<int:id>/publicar/', PorConstruir.as_view(caso_de_uso='PER-07', metodo='POST'), name='per-07-cronogramas-id-publicar'),
    # PER-06 · Aprobar o devolver una tarea: POST /api/v1/personal/tareas/{id}/devolver/
    path('tareas/<int:id>/devolver/', views.RevisarTarea.as_view(decision='devolver'), name='per-06-tareas-id-devolver'),
    # PER-06 · Aprobar una jornada: POST /api/v1/personal/jornadas/{id}/aprobar/
    # TODO(Nómina): construir con NOM-02; la prenómina usa las jornadas aprobadas
    path('jornadas/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='PER-06', metodo='POST'), name='per-06-jornadas-id-aprobar'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('tareas/<int:padre>/pasos/', views.PasoTareaViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='tarea'), name='personal-pasos-lista'),
    path('tareas/<int:padre>/pasos/<int:pk>/', views.PasoTareaViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='tarea'), name='personal-pasos-detalle'),
    path('tareas/<int:padre>/evidencias/', views.EvidenciaTareaViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='tarea'), name='personal-evidencias-lista'),
    path('tareas/<int:padre>/evidencias/<int:pk>/', views.EvidenciaTareaViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='tarea'), name='personal-evidencias-detalle'),
    path('patrones-turno/<int:padre>/dias/', views.PatronTurnoDetalleViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='patron'), name='personal-dias-lista'),
    path('patrones-turno/<int:padre>/dias/<int:pk>/', views.PatronTurnoDetalleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='patron'), name='personal-dias-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
