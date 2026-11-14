"""Vistas (endpoints CRUD) del esquema nomina.

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


# CRUD de nomina.concepto_nomina en /api/v1/nomina/conceptos-nomina/
class ConceptoNominaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ConceptoNomina.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ConceptoNominaSerializer


# CRUD de nomina.periodo_nomina en /api/v1/nomina/periodos-nomina/
class PeriodoNominaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PeriodoNomina.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PeriodoNominaSerializer


# CRUD de nomina.novedad en /api/v1/nomina/novedades/
class NovedadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Novedad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.NovedadSerializer


# CRUD de nomina.liquidacion en /api/v1/nomina/liquidaciones/
class LiquidacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Liquidacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LiquidacionSerializer


# CRUD de nomina.liquidacion_detalle en /api/v1/nomina/liquidaciones/{id}/detalles/
class LiquidacionDetalleViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LiquidacionDetalle.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LiquidacionDetalleSerializer


# CRUD de nomina.provision_prestacion en /api/v1/nomina/provisiones-prestacion/
class ProvisionPrestacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ProvisionPrestacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ProvisionPrestacionSerializer


# CRUD de nomina.documento_nomina_electronica en /api/v1/nomina/documentos-nomina-electronica/
class DocumentoNominaElectronicaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.DocumentoNominaElectronica.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DocumentoNominaElectronicaSerializer


# CRUD de nomina.planilla_pila en /api/v1/nomina/planillas-pila/
class PlanillaPilaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PlanillaPila.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlanillaPilaSerializer


# CRUD de nomina.pago_nomina en /api/v1/nomina/pagos-nomina/
class PagoNominaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PagoNomina.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PagoNominaSerializer


# CRUD de nomina.exportacion_nomina en /api/v1/nomina/exportaciones-nomina/
class ExportacionNominaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ExportacionNomina.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ExportacionNominaSerializer
