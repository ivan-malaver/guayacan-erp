"""Vistas (endpoints CRUD) del esquema seguros.

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


# CRUD de seguros.poliza en /api/v1/seguros/polizas/
class PolizaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Poliza.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PolizaSerializer


# CRUD de seguros.bien_asegurado en /api/v1/seguros/bienes-asegurados/
class BienAseguradoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.BienAsegurado.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BienAseguradoSerializer


# CRUD de seguros.indice_poliza en /api/v1/seguros/indices-poliza/
class IndicePolizaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.IndicePoliza.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.IndicePolizaSerializer


# CRUD de seguros.aviso_siniestro en /api/v1/seguros/avisos-siniestro/
class AvisoSiniestroViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AvisoSiniestro.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AvisoSiniestroSerializer
