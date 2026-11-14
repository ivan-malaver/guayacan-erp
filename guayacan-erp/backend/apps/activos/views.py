"""Vistas (endpoints CRUD) del esquema activos.

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


# CRUD de activos.activo en /api/v1/activos/activos/
class ActivoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Activo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ActivoSerializer


# CRUD de activos.plan_mantenimiento en /api/v1/activos/planes-mantenimiento/
class PlanMantenimientoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PlanMantenimiento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlanMantenimientoSerializer


# CRUD de activos.orden_trabajo en /api/v1/activos/ordenes-trabajo/
class OrdenTrabajoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.OrdenTrabajo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.OrdenTrabajoSerializer


# CRUD de activos.repuesto_orden en /api/v1/activos/ordenes-trabajo/{id}/repuestos/
class RepuestoOrdenViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RepuestoOrden.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RepuestoOrdenSerializer


# CRUD de activos.uso_activo en /api/v1/activos/usos-activo/
class UsoActivoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.UsoActivo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.UsoActivoSerializer


# CRUD de activos.depreciacion en /api/v1/activos/depreciaciones/
class DepreciacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Depreciacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DepreciacionSerializer
