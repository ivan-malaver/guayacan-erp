"""Vistas (endpoints CRUD) del esquema documental.

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


# CRUD de documental.documento en /api/v1/documental/documentos/
class DocumentoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Documento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DocumentoSerializer


# CRUD de documental.version_documento en /api/v1/documental/documentos/{id}/versiones/
class VersionDocumentoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.VersionDocumento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.VersionDocumentoSerializer


# CRUD de documental.vinculo_documento en /api/v1/documental/vinculos-documento/
class VinculoDocumentoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.VinculoDocumento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.VinculoDocumentoSerializer
