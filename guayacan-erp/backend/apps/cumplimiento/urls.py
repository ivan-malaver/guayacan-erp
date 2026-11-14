"""Rutas de /api/v1/cumplimiento/ (cómo una dirección web llega a su vista).

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
router.register('normas', views.NormaViewSet, basename='cumplimiento-normas')  # tabla cumplimiento.norma
router.register('requisitos', views.RequisitoViewSet, basename='cumplimiento-requisitos')  # tabla cumplimiento.requisito
router.register('expedientes', views.ExpedienteViewSet, basename='cumplimiento-expedientes')  # tabla cumplimiento.expediente
router.register('evaluaciones-requisito', views.EvaluacionRequisitoViewSet, basename='cumplimiento-evaluaciones-requisito')  # tabla cumplimiento.evaluacion_requisito
router.register('evidencias-requisito', views.EvidenciaRequisitoViewSet, basename='cumplimiento-evidencias-requisito')  # tabla cumplimiento.evidencia_requisito
router.register('auditorias-externas', views.AuditoriaExternaViewSet, basename='cumplimiento-auditorias-externas')  # tabla cumplimiento.auditoria_externa
router.register('no-conformidades', views.NoConformidadViewSet, basename='cumplimiento-no-conformidades')  # tabla cumplimiento.no_conformidad
router.register('acciones-correctivas', views.AccionCorrectivaViewSet, basename='cumplimiento-acciones-correctivas')  # tabla cumplimiento.accion_correctiva

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # CUM-03 · Evaluar el expediente contra su evidencia: POST /api/v1/cumplimiento/expedientes/{id}/evaluar/
    path('expedientes/<int:id>/evaluar/', PorConstruir.as_view(caso_de_uso='CUM-03', metodo='POST'), name='cum-03-expedientes-id-evaluar'),
    # CUM-05 · Registrar una auditoría externa y sus no conformidades: GET /api/v1/cumplimiento/expedientes/{id}/paquete-auditor/
    path('expedientes/<int:id>/paquete-auditor/', PorConstruir.as_view(caso_de_uso='CUM-05', metodo='GET'), name='cum-05-expedientes-id-paquete-auditor'),
    # CUM-07 · Vigilar la obligación de granja avícola biosegura: GET /api/v1/cumplimiento/granja-biosegura/
    path('granja-biosegura/', PorConstruir.as_view(caso_de_uso='CUM-07', metodo='GET'), name='cum-07-granja-biosegura'),
    # CUM-06 · Ejecutar y verificar acciones correctivas: POST /api/v1/cumplimiento/acciones-correctivas/{id}/verificar/
    path('acciones-correctivas/<int:id>/verificar/', PorConstruir.as_view(caso_de_uso='CUM-06', metodo='POST'), name='cum-06-acciones-correctivas-id-verificar'),
    # CUM-06 · Ejecutar y verificar acciones correctivas: POST /api/v1/cumplimiento/no-conformidades/{id}/cerrar/
    path('no-conformidades/<int:id>/cerrar/', PorConstruir.as_view(caso_de_uso='CUM-06', metodo='POST'), name='cum-06-no-conformidades-id-cerrar'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
