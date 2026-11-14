"""Rutas de /api/v1/estrategia/ (cómo una dirección web llega a su vista).

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
router.register('lineas-negocio', views.LineaNegocioViewSet, basename='estrategia-lineas-negocio')  # tabla estrategia.linea_negocio
router.register('factores-dofa', views.FactorDofaViewSet, basename='estrategia-factores-dofa')  # tabla estrategia.factor_dofa
router.register('estudios-mercado', views.EstudioMercadoViewSet, basename='estrategia-estudios-mercado')  # tabla estrategia.estudio_mercado
router.register('iniciativas', views.IniciativaViewSet, basename='estrategia-iniciativas')  # tabla estrategia.iniciativa
router.register('evaluaciones-proyecto', views.EvaluacionProyectoViewSet, basename='estrategia-evaluaciones-proyecto')  # tabla estrategia.evaluacion_proyecto
router.register('reinversiones', views.ReinversionViewSet, basename='estrategia-reinversiones')  # tabla estrategia.reinversion
router.register('seguimientos-iniciativa', views.SeguimientoIniciativaViewSet, basename='estrategia-seguimientos-iniciativa')  # tabla estrategia.seguimiento_iniciativa
router.register('objetivos', views.ObjetivoViewSet, basename='estrategia-objetivos')  # tabla estrategia.objetivo

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # EST-01 · Mantener las líneas de negocio y la matriz DOFA: GET /api/v1/estrategia/lineas/
    path('lineas/', PorConstruir.as_view(caso_de_uso='EST-01', metodo='GET'), name='est-01-lineas'),
    # EST-04 · Evaluar financieramente una iniciativa: POST /api/v1/estrategia/evaluaciones-proyecto/{id}/calcular/
    path('evaluaciones-proyecto/<int:id>/calcular/', PorConstruir.as_view(caso_de_uso='EST-04', metodo='POST'), name='est-04-evaluaciones-proyecto-id-calcular'),
    # EST-07 · Seguir el retorno de las iniciativas: GET /api/v1/estrategia/retorno/
    path('retorno/', PorConstruir.as_view(caso_de_uso='EST-07', metodo='GET'), name='est-07-retorno'),
    # EST-05 · Aprobar una iniciativa: POST /api/v1/estrategia/iniciativas/{id}/aprobar/
    path('iniciativas/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='EST-05', metodo='POST'), name='est-05-iniciativas-id-aprobar'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('evaluaciones-proyecto/<int:padre>/flujos/', views.FlujoProyectoViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='evaluacion'), name='estrategia-flujos-lista'),
    path('evaluaciones-proyecto/<int:padre>/flujos/<int:pk>/', views.FlujoProyectoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='evaluacion'), name='estrategia-flujos-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
