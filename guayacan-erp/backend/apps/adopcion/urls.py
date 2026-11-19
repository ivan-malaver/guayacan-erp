"""Rutas de /api/v1/adopcion/ (cómo una dirección web llega a su vista).

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
router.register('planes', views.PlanViewSet, basename='adopcion-planes')  # tabla adopcion.plan
router.register('sitios', views.SitioViewSet, basename='adopcion-sitios')  # tabla adopcion.sitio
router.register('bienes', views.BienViewSet, basename='adopcion-bienes')  # tabla adopcion.bien
router.register('contratos', views.ContratoViewSet, basename='adopcion-contratos')  # tabla adopcion.contrato
router.register('cuotas', views.CuotaViewSet, basename='adopcion-cuotas')  # tabla adopcion.cuota
router.register('seguimientos', views.SeguimientoViewSet, basename='adopcion-seguimientos')  # tabla adopcion.seguimiento
router.register('liquidaciones', views.LiquidacionViewSet, basename='adopcion-liquidaciones')  # tabla adopcion.liquidacion
router.register('movimientos-saldo', views.MovimientoSaldoViewSet, basename='adopcion-movimientos-saldo')  # tabla adopcion.movimiento_saldo

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # ADO-02 · Comprar un árbol o un animal: POST /api/v1/adopcion/contratos/compra/ (el pago confirma en /api/v1/pagos/webhook/)
    path('contratos/compra/', views.Compra.as_view(), name='ado-02-contratos-compra'),
    # ADO-03 · Sembrar en persona: POST /api/v1/adopcion/bienes/{id}/siembra/
    path('bienes/<int:id>/siembra/', views.Siembra.as_view(), name='ado-03-bienes-id-siembra'),
    # ADO-05 · Cobrar y pagar la cuota mensual: POST /api/v1/adopcion/cuotas/{id}/pagar/
    path('cuotas/<int:id>/pagar/', PorConstruir.as_view(caso_de_uso='ADO-05', metodo='POST'), name='ado-05-cuotas-id-pagar'),
    # ADO-06 · Seguir mi árbol o mi animal: GET /api/v1/adopcion/mis-bienes/
    path('mis-bienes/', PorConstruir.as_view(caso_de_uso='ADO-06', metodo='GET'), name='ado-06-mis-bienes'),
    # ADO-06 · Seguir mi árbol o mi animal: GET /api/v1/adopcion/mis-bienes/{id}/seguimiento/
    path('mis-bienes/<int:id>/seguimiento/', PorConstruir.as_view(caso_de_uso='ADO-06', metodo='GET'), name='ado-06-mis-bienes-id-seguimiento'),
    # ADO-10 · Liquidar productos con el 5 %: POST /api/v1/adopcion/liquidaciones/{id}/aprobar/
    path('liquidaciones/<int:id>/aprobar/', PorConstruir.as_view(caso_de_uso='ADO-10', metodo='POST'), name='ado-10-liquidaciones-id-aprobar'),
    # ADO-10 · Liquidar productos con el 5 %: POST /api/v1/adopcion/adoptantes/{id}/pagar-saldo/
    path('adoptantes/<int:id>/pagar-saldo/', PorConstruir.as_view(caso_de_uso='ADO-10', metodo='POST'), name='ado-10-adoptantes-id-pagar-saldo'),
    # ADO-11 · Decidir en la madurez: mantener o liquidar: POST /api/v1/adopcion/contratos/{id}/decision/
    path('contratos/<int:id>/decision/', PorConstruir.as_view(caso_de_uso='ADO-11', metodo='POST'), name='ado-11-contratos-id-decision'),
    # ADO-13 · Reponer un bien muerto en garantía: POST /api/v1/adopcion/bienes/{id}/muerte/
    path('bienes/<int:id>/muerte/', PorConstruir.as_view(caso_de_uso='ADO-13', metodo='POST'), name='ado-13-bienes-id-muerte'),
    # ADO-14 · Ceder o regalar la adopción: POST /api/v1/adopcion/contratos/{id}/ceder/
    path('contratos/<int:id>/ceder/', PorConstruir.as_view(caso_de_uso='ADO-14', metodo='POST'), name='ado-14-contratos-id-ceder'),
    # ADO-15 · Consultar el tablero de adopción: GET /api/v1/adopcion/tablero/
    path('tablero/', PorConstruir.as_view(caso_de_uso='ADO-15', metodo='GET'), name='ado-15-tablero'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
