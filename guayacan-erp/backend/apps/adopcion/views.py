"""Vistas (endpoints CRUD) del esquema adopcion.

QUÉ HACE UNA VISTA
Recibe la petición HTTP, usa el serializer para validar o convertir los datos y responde. Cada clase de abajo
es un «ViewSet»: una sola clase atiende varias rutas de la misma tabla.

QUÉ OPERACIONES OFRECE (heredadas de guayacan.vistas.VistaModelo)
  GET    /recurso/        lista paginada (50 por página; ?pagina=2&tamano=100)
  GET    /recurso/{id}/   detalle de un registro
  POST   /recurso/        crear
  PUT o PATCH /recurso/{id}/   modificar todo o una parte
  No hay DELETE: en GuayacanERP los registros se desactivan, se anulan o se cierran, no se borran.

La seguridad no se programa aquí: el middleware fija la finca y el usuario, y PostgreSQL solo deja ver y
cambiar lo de esa finca. Las acciones de los casos de uso (aprobar, confirmar, liquidar...) están en urls.py.
Generado por docs/uml/fuentes/gen_apps.py."""
from guayacan.vistas import VistaModelo

from . import models, serializers


# CRUD de adopcion.plan en /api/v1/adopcion/planes/
class PlanViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Plan.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlanSerializer


# CRUD de adopcion.sitio en /api/v1/adopcion/sitios/
class SitioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Sitio.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SitioSerializer


# CRUD de adopcion.bien en /api/v1/adopcion/bienes/
class BienViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Bien.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BienSerializer


# CRUD de adopcion.contrato en /api/v1/adopcion/contratos/
class ContratoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Contrato.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ContratoSerializer


# CRUD de adopcion.cuota en /api/v1/adopcion/cuotas/
class CuotaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cuota.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CuotaSerializer


# CRUD de adopcion.seguimiento en /api/v1/adopcion/seguimientos/
class SeguimientoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Seguimiento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SeguimientoSerializer


# CRUD de adopcion.liquidacion en /api/v1/adopcion/liquidaciones/
class LiquidacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Liquidacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LiquidacionSerializer


# CRUD de adopcion.movimiento_saldo en /api/v1/adopcion/movimientos-saldo/
class MovimientoSaldoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MovimientoSaldo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MovimientoSaldoSerializer
