"""Vistas (endpoints CRUD) del esquema redes.

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


# CRUD de redes.cuenta_red en /api/v1/redes/cuentas-red/
class CuentaRedViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CuentaRed.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CuentaRedSerializer


# CRUD de redes.publicacion en /api/v1/redes/publicaciones/
class PublicacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Publicacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PublicacionSerializer


# CRUD de redes.politica_canal en /api/v1/redes/politicas-canal/
class PoliticaCanalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PoliticaCanal.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PoliticaCanalSerializer


# CRUD de redes.plantilla_mensaje en /api/v1/redes/plantillas-mensaje/
class PlantillaMensajeViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PlantillaMensaje.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlantillaMensajeSerializer


# CRUD de redes.mensaje_saliente en /api/v1/redes/mensajes-salientes/
class MensajeSalienteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MensajeSaliente.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MensajeSalienteSerializer


# CRUD de redes.pieza_audiovisual en /api/v1/redes/piezas-audiovisual/
class PiezaAudiovisualViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PiezaAudiovisual.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PiezaAudiovisualSerializer


# CRUD de redes.pieza_persona en /api/v1/redes/piezas-persona/
class PiezaPersonaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PiezaPersona.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PiezaPersonaSerializer
