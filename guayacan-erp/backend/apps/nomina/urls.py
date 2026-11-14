"""Rutas de /api/v1/nomina/ (cómo una dirección web llega a su vista).

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
router.register('conceptos-nomina', views.ConceptoNominaViewSet, basename='nomina-conceptos-nomina')  # tabla nomina.concepto_nomina
router.register('periodos-nomina', views.PeriodoNominaViewSet, basename='nomina-periodos-nomina')  # tabla nomina.periodo_nomina
router.register('novedades', views.NovedadViewSet, basename='nomina-novedades')  # tabla nomina.novedad
router.register('liquidaciones', views.LiquidacionViewSet, basename='nomina-liquidaciones')  # tabla nomina.liquidacion
router.register('provisiones-prestacion', views.ProvisionPrestacionViewSet, basename='nomina-provisiones-prestacion')  # tabla nomina.provision_prestacion
router.register('documentos-nomina-electronica', views.DocumentoNominaElectronicaViewSet, basename='nomina-documentos-nomina-electronica')  # tabla nomina.documento_nomina_electronica
router.register('planillas-pila', views.PlanillaPilaViewSet, basename='nomina-planillas-pila')  # tabla nomina.planilla_pila
router.register('pagos-nomina', views.PagoNominaViewSet, basename='nomina-pagos-nomina')  # tabla nomina.pago_nomina
router.register('exportaciones-nomina', views.ExportacionNominaViewSet, basename='nomina-exportaciones-nomina')  # tabla nomina.exportacion_nomina

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # NOM-02 · Preparar la prenómina: POST /api/v1/nomina/periodos/{id}/prenomina/
    path('periodos/<int:id>/prenomina/', PorConstruir.as_view(caso_de_uso='NOM-02', metodo='POST'), name='nom-02-periodos-id-prenomina'),
    # NOM-04 · Liquidar la nómina: POST /api/v1/nomina/periodos/{id}/liquidar/
    path('periodos/<int:id>/liquidar/', PorConstruir.as_view(caso_de_uso='NOM-04', metodo='POST'), name='nom-04-periodos-id-liquidar'),
    # NOM-05 · Cerrar el periodo de nómina: POST /api/v1/nomina/periodos/{id}/cerrar/
    path('periodos/<int:id>/cerrar/', PorConstruir.as_view(caso_de_uso='NOM-05', metodo='POST'), name='nom-05-periodos-id-cerrar'),
    # NOM-07 · Generar la PILA y exportar al contador: GET /api/v1/nomina/periodos/{id}/pila/
    path('periodos/<int:id>/pila/', PorConstruir.as_view(caso_de_uso='NOM-07', metodo='GET'), name='nom-07-periodos-id-pila'),
    # NOM-07 · Generar la PILA y exportar al contador: GET /api/v1/nomina/periodos/{id}/exportar/
    path('periodos/<int:id>/exportar/', PorConstruir.as_view(caso_de_uso='NOM-07', metodo='GET'), name='nom-07-periodos-id-exportar'),
    # NOM-08 · Transmitir la nómina electrónica: POST /api/v1/nomina/periodos/{id}/transmitir/
    path('periodos/<int:id>/transmitir/', PorConstruir.as_view(caso_de_uso='NOM-08', metodo='POST'), name='nom-08-periodos-id-transmitir'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('liquidaciones/<int:padre>/detalles/', views.LiquidacionDetalleViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='liquidacion'), name='nomina-detalles-lista'),
    path('liquidaciones/<int:padre>/detalles/<int:pk>/', views.LiquidacionDetalleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='liquidacion'), name='nomina-detalles-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
