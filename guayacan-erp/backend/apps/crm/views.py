"""Vistas (endpoints CRUD) del esquema crm.

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


# CRUD de crm.segmento en /api/v1/crm/segmentos/
class SegmentoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Segmento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SegmentoSerializer


# CRUD de crm.campana en /api/v1/crm/campanas/
class CampanaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Campana.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CampanaSerializer


# CRUD de crm.formulario_captura en /api/v1/crm/formularios-captura/
class FormularioCapturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.FormularioCaptura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FormularioCapturaSerializer


# CRUD de crm.prospecto en /api/v1/crm/prospectos/
class ProspectoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Prospecto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ProspectoSerializer


# CRUD de crm.contacto_empresa en /api/v1/crm/contactos-empresa/
class ContactoEmpresaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ContactoEmpresa.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ContactoEmpresaSerializer


# CRUD de crm.interaccion en /api/v1/crm/interacciones/
class InteraccionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Interaccion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.InteraccionSerializer


# CRUD de crm.oportunidad en /api/v1/crm/oportunidades/
class OportunidadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Oportunidad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.OportunidadSerializer
