"""Vistas (endpoints CRUD) del esquema finanzas.

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


# CRUD de finanzas.cuenta_contable en /api/v1/finanzas/cuentas-contable/
class CuentaContableViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CuentaContable.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CuentaContableSerializer


# CRUD de finanzas.centro_costo en /api/v1/finanzas/centros-costo/
class CentroCostoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CentroCosto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CentroCostoSerializer


# CRUD de finanzas.comprobante en /api/v1/finanzas/comprobantes/
class ComprobanteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Comprobante.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ComprobanteSerializer


# CRUD de finanzas.movimiento_contable en /api/v1/finanzas/comprobantes/{id}/movimientos/
class MovimientoContableViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MovimientoContable.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MovimientoContableSerializer


# CRUD de finanzas.periodo_contable en /api/v1/finanzas/periodos-contable/
class PeriodoContableViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PeriodoContable.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PeriodoContableSerializer


# CRUD de finanzas.clasificacion_costo en /api/v1/finanzas/clasificaciones-costo/
class ClasificacionCostoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ClasificacionCosto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ClasificacionCostoSerializer


# CRUD de finanzas.actividad_costo en /api/v1/finanzas/actividades-costo/
class ActividadCostoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ActividadCosto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ActividadCostoSerializer


# CRUD de finanzas.asignacion_costo en /api/v1/finanzas/asignaciones-costo/
class AsignacionCostoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AsignacionCosto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AsignacionCostoSerializer


# CRUD de finanzas.costo_estandar en /api/v1/finanzas/costos-estandar/
class CostoEstandarViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CostoEstandar.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CostoEstandarSerializer


# CRUD de finanzas.presupuesto en /api/v1/finanzas/presupuestos/
class PresupuestoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Presupuesto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PresupuestoSerializer


# CRUD de finanzas.premisa_presupuesto en /api/v1/finanzas/premisas-presupuesto/
class PremisaPresupuestoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PremisaPresupuesto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PremisaPresupuestoSerializer


# CRUD de finanzas.presupuesto_detalle en /api/v1/finanzas/presupuestos/{id}/detalles/
class PresupuestoDetalleViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PresupuestoDetalle.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PresupuestoDetalleSerializer


# CRUD de finanzas.estado_financiero en /api/v1/finanzas/estados-financiero/
class EstadoFinancieroViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EstadoFinanciero.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EstadoFinancieroSerializer


# CRUD de finanzas.indicador en /api/v1/finanzas/indicadores/
class IndicadorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Indicador.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.IndicadorSerializer


# CRUD de finanzas.valor_indicador en /api/v1/finanzas/valores-indicador/
class ValorIndicadorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ValorIndicador.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ValorIndicadorSerializer


# CRUD de finanzas.anticipo_proveedor en /api/v1/finanzas/anticipos-proveedor/
class AnticipoProveedorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AnticipoProveedor.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AnticipoProveedorSerializer


# CRUD de finanzas.aplicacion_anticipo en /api/v1/finanzas/aplicaciones-anticipo/
class AplicacionAnticipoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AplicacionAnticipo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AplicacionAnticipoSerializer


# CRUD de finanzas.reporte_indicadores en /api/v1/finanzas/reportes-indicadores/
class ReporteIndicadoresViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ReporteIndicadores.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ReporteIndicadoresSerializer
