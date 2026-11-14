"""Vistas (endpoints CRUD) del esquema riego.

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


# CRUD de riego.fuente_agua en /api/v1/riego/fuentes-agua/
class FuenteAguaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.FuenteAgua.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FuenteAguaSerializer


# CRUD de riego.tanque en /api/v1/riego/tanques/
class TanqueViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Tanque.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.TanqueSerializer


# CRUD de riego.sistema_riego en /api/v1/riego/sistemas-riego/
class SistemaRiegoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.SistemaRiego.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SistemaRiegoSerializer


# CRUD de riego.valvula en /api/v1/riego/valvulas/
class ValvulaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Valvula.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ValvulaSerializer


# CRUD de riego.evento_riego en /api/v1/riego/eventos-riego/
class EventoRiegoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EventoRiego.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EventoRiegoSerializer
