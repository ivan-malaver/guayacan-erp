"""Rutas de /api/v1/ia/ (cómo una dirección web llega a su vista).

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
router.register('agentes', views.AgenteViewSet, basename='ia-agentes')  # tabla ia.agente
router.register('herramientas', views.HerramientaViewSet, basename='ia-herramientas')  # tabla ia.herramienta
router.register('solicitudes-aprobacion', views.SolicitudAprobacionViewSet, basename='ia-solicitudes-aprobacion')  # tabla ia.solicitud_aprobacion
router.register('documentos-conocimiento', views.DocumentoConocimientoViewSet, basename='ia-documentos-conocimiento')  # tabla ia.documento_conocimiento
router.register('fragmentos-conocimiento', views.FragmentoConocimientoViewSet, basename='ia-fragmentos-conocimiento')  # tabla ia.fragmento_conocimiento
router.register('recomendaciones', views.RecomendacionViewSet, basename='ia-recomendaciones')  # tabla ia.recomendacion
router.register('evaluaciones-respuesta', views.EvaluacionRespuestaViewSet, basename='ia-evaluaciones-respuesta')  # tabla ia.evaluacion_respuesta
router.register('consumos', views.ConsumoIaViewSet, basename='ia-consumos')  # tabla ia.consumo_ia
router.register('reglas-conversacion', views.ReglaConversacionViewSet, basename='ia-reglas-conversacion')  # tabla ia.regla_conversacion
router.register('escalamientos', views.EscalamientoViewSet, basename='ia-escalamientos')  # tabla ia.escalamiento
router.register('modelos-pronostico', views.ModeloPronosticoViewSet, basename='ia-modelos-pronostico')  # tabla ia.modelo_pronostico
router.register('pronosticos-demanda', views.PronosticoDemandaViewSet, basename='ia-pronosticos-demanda')  # tabla ia.pronostico_demanda
router.register('diagnosticos-imagen', views.DiagnosticoImagenViewSet, basename='ia-diagnosticos-imagen')  # tabla ia.diagnostico_imagen
router.register('escenarios', views.EscenarioViewSet, basename='ia-escenarios')  # tabla ia.escenario
router.register('decisiones', views.DecisionViewSet, basename='ia-decisiones')  # tabla ia.decision

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # IA-02 · Resolver la bandeja de aprobaciones: POST /api/v1/ia/solicitudes-aprobacion/{id}/aprobar/
    path('solicitudes-aprobacion/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='IA-02', metodo='POST'), name='ia-02-solicitudes-aprobacion-id-aprobar'),
    # IA-03 · Alimentar la base de conocimiento: POST /api/v1/ia/documentos-conocimiento/{id}/indexar/
    path('documentos-conocimiento/<int:id>/indexar/', PorConstruir.as_view(caso_de_uso='IA-03', metodo='POST'), name='ia-03-documentos-conocimiento-id-indexar'),
    # IA-03 · Alimentar la base de conocimiento: POST /api/v1/ia/buscar/
    path('buscar/', PorConstruir.as_view(caso_de_uso='IA-03', metodo='POST'), name='ia-03-buscar'),
    # RED-02 · Escalar una conversación a una persona: POST /api/v1/ia/escalamientos/{id}/tomar/
    path('escalamientos/<int:id>/tomar/', PorConstruir.as_view(caso_de_uso='RED-02', metodo='POST'), name='red-02-escalamientos-id-tomar'),
    # IA-02 · Resolver la bandeja de aprobaciones: POST /api/v1/ia/solicitudes-aprobacion/{id}/rechazar/
    path('solicitudes-aprobacion/<int:id>/rechazar/', PorConstruir.as_view(caso_de_uso='IA-02', metodo='POST'), name='ia-02-solicitudes-aprobacion-id-rechazar'),
    # IA-08 · Diagnosticar una foto de campo: POST /api/v1/ia/diagnosticos-imagen/{id}/revisar/
    path('diagnosticos-imagen/<int:id>/revisar/', PorConstruir.as_view(caso_de_uso='IA-08', metodo='POST'), name='ia-08-diagnosticos-imagen-id-revisar'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('agentes/<int:padre>/herramientas/', views.AgenteHerramientaViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='agente'), name='ia-herramientas-lista'),
    path('agentes/<int:padre>/herramientas/<int:pk>/', views.AgenteHerramientaViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='agente'), name='ia-herramientas-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
