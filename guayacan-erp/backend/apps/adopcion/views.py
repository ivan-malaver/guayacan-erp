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

from . import models, serializers, services


class AltaPorAdo01:
    """ADO-01: crear un plan, un sitio o un bien pasa por el servicio, que exige la función «adopcion» en la finca.

    Solo cambia el POST; listar, ver y modificar siguen siendo el CRUD de VistaModelo.
    lista_ado_01 es el nombre de la lista que recibe el servicio: 'planes', 'sitios' o 'bienes'.
    """

    lista_ado_01 = None

    def perform_create(self, serializer):
        creados = services.ado_01_configurar_catalogo_sitios(usuario=self.request.user,
                                                             **{self.lista_ado_01: [serializer.validated_data]})
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = creados[self.lista_ado_01][0]


# CRUD de adopcion.plan en /api/v1/adopcion/planes/  (el alta es ADO-01)
class PlanViewSet(AltaPorAdo01, VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Plan.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlanSerializer
    lista_ado_01 = 'planes'


# CRUD de adopcion.sitio en /api/v1/adopcion/sitios/  (el alta es ADO-01)
class SitioViewSet(AltaPorAdo01, VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Sitio.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SitioSerializer
    lista_ado_01 = 'sitios'


# CRUD de adopcion.bien en /api/v1/adopcion/bienes/  (el alta es ADO-01)
class BienViewSet(AltaPorAdo01, VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Bien.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BienSerializer
    lista_ado_01 = 'bienes'


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
