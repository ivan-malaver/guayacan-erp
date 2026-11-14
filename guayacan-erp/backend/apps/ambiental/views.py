"""Vistas (endpoints CRUD) del esquema ambiental.

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


# CRUD de ambiental.factor_emision en /api/v1/ambiental/factores-emision/
class FactorEmisionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.FactorEmision.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FactorEmisionSerializer


# CRUD de ambiental.registro_ambiental en /api/v1/ambiental/registros-ambiental/
class RegistroAmbientalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroAmbiental.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroAmbientalSerializer
