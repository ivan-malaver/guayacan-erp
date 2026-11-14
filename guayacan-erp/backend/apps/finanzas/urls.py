"""Rutas de /api/v1/finanzas/ (cómo una dirección web llega a su vista).

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
router.register('cuentas-contable', views.CuentaContableViewSet, basename='finanzas-cuentas-contable')  # tabla finanzas.cuenta_contable
router.register('centros-costo', views.CentroCostoViewSet, basename='finanzas-centros-costo')  # tabla finanzas.centro_costo
router.register('comprobantes', views.ComprobanteViewSet, basename='finanzas-comprobantes')  # tabla finanzas.comprobante
router.register('periodos-contable', views.PeriodoContableViewSet, basename='finanzas-periodos-contable')  # tabla finanzas.periodo_contable
router.register('clasificaciones-costo', views.ClasificacionCostoViewSet, basename='finanzas-clasificaciones-costo')  # tabla finanzas.clasificacion_costo
router.register('actividades-costo', views.ActividadCostoViewSet, basename='finanzas-actividades-costo')  # tabla finanzas.actividad_costo
router.register('asignaciones-costo', views.AsignacionCostoViewSet, basename='finanzas-asignaciones-costo')  # tabla finanzas.asignacion_costo
router.register('costos-estandar', views.CostoEstandarViewSet, basename='finanzas-costos-estandar')  # tabla finanzas.costo_estandar
router.register('presupuestos', views.PresupuestoViewSet, basename='finanzas-presupuestos')  # tabla finanzas.presupuesto
router.register('premisas-presupuesto', views.PremisaPresupuestoViewSet, basename='finanzas-premisas-presupuesto')  # tabla finanzas.premisa_presupuesto
router.register('estados-financiero', views.EstadoFinancieroViewSet, basename='finanzas-estados-financiero')  # tabla finanzas.estado_financiero
router.register('indicadores', views.IndicadorViewSet, basename='finanzas-indicadores')  # tabla finanzas.indicador
router.register('valores-indicador', views.ValorIndicadorViewSet, basename='finanzas-valores-indicador')  # tabla finanzas.valor_indicador
router.register('anticipos-proveedor', views.AnticipoProveedorViewSet, basename='finanzas-anticipos-proveedor')  # tabla finanzas.anticipo_proveedor
router.register('aplicaciones-anticipo', views.AplicacionAnticipoViewSet, basename='finanzas-aplicaciones-anticipo')  # tabla finanzas.aplicacion_anticipo
router.register('reportes-indicadores', views.ReporteIndicadoresViewSet, basename='finanzas-reportes-indicadores')  # tabla finanzas.reporte_indicadores

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # FIN-04 · Cerrar el periodo contable: POST /api/v1/finanzas/periodos-contable/{id}/cerrar/
    path('periodos-contable/<int:id>/cerrar/', PorConstruir.as_view(caso_de_uso='FIN-04', metodo='POST'), name='fin-04-periodos-contable-id-cerrar'),
    # FIN-07 · Generar los estados financieros: GET /api/v1/finanzas/estado-resultados/
    path('estado-resultados/', PorConstruir.as_view(caso_de_uso='FIN-07', metodo='GET'), name='fin-07-estado-resultados'),
    # FIN-07 · Generar los estados financieros: GET /api/v1/finanzas/balance/
    path('balance/', PorConstruir.as_view(caso_de_uso='FIN-07', metodo='GET'), name='fin-07-balance'),
    # FIN-08 · Calcular indicadores y consultar el tablero: POST /api/v1/finanzas/indicadores/calcular/
    path('indicadores/calcular/', PorConstruir.as_view(caso_de_uso='FIN-08', metodo='POST'), name='fin-08-indicadores-calcular'),
    # FIN-09 · Analizar estados: vertical, horizontal, fuentes y usos: GET /api/v1/finanzas/analisis/
    path('analisis/', PorConstruir.as_view(caso_de_uso='FIN-09', metodo='GET'), name='fin-09-analisis'),
    # FIN-09 · Analizar estados: vertical, horizontal, fuentes y usos: GET /api/v1/finanzas/fuentes-usos/
    path('fuentes-usos/', PorConstruir.as_view(caso_de_uso='FIN-09', metodo='GET'), name='fin-09-fuentes-usos'),
    # FIN-10 · Calcular punto de equilibrio y palancas: GET /api/v1/finanzas/palancas/
    path('palancas/', PorConstruir.as_view(caso_de_uso='FIN-10', metodo='GET'), name='fin-10-palancas'),
    # FIN-02 · Contabilizar un comprobante: POST /api/v1/finanzas/comprobantes/{id}/contabilizar/
    path('comprobantes/<int:id>/contabilizar/', PorConstruir.as_view(caso_de_uso='FIN-02', metodo='POST'), name='fin-02-comprobantes-id-contabilizar'),
    # FIN-03 · Anular un comprobante o registrar una nota: POST /api/v1/finanzas/comprobantes/{id}/anular/
    path('comprobantes/<int:id>/anular/', PorConstruir.as_view(caso_de_uso='FIN-03', metodo='POST'), name='fin-03-comprobantes-id-anular'),
    # FIN-06 · Elaborar y aprobar el presupuesto maestro: POST /api/v1/finanzas/presupuestos/{id}/aprobar/
    path('presupuestos/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='FIN-06', metodo='POST'), name='fin-06-presupuestos-id-aprobar'),
    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear
    path('comprobantes/<int:padre>/movimientos/', views.MovimientoContableViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='comprobante'), name='finanzas-movimientos-lista'),
    path('comprobantes/<int:padre>/movimientos/<int:pk>/', views.MovimientoContableViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='comprobante'), name='finanzas-movimientos-detalle'),
    path('presupuestos/<int:padre>/detalles/', views.PresupuestoDetalleViewSet.as_view({'get': 'list', 'post': 'create'}, campo_padre='presupuesto'), name='finanzas-detalles-lista'),
    path('presupuestos/<int:padre>/detalles/<int:pk>/', views.PresupuestoDetalleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}, campo_padre='presupuesto'), name='finanzas-detalles-detalle'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
