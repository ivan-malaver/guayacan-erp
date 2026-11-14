"""Vistas (endpoints CRUD) del esquema turismo.

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


# CRUD de turismo.alojamiento en /api/v1/turismo/alojamientos/
class AlojamientoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Alojamiento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AlojamientoSerializer


# CRUD de turismo.plan_turistico en /api/v1/turismo/planes-turistico/
class PlanTuristicoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PlanTuristico.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlanTuristicoSerializer


# CRUD de turismo.reserva en /api/v1/turismo/reservas/
class ReservaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Reserva.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ReservaSerializer


# CRUD de turismo.bloqueo_calendario en /api/v1/turismo/bloqueos-calendario/
class BloqueoCalendarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.BloqueoCalendario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BloqueoCalendarioSerializer
