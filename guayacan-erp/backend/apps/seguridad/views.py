"""Vistas (endpoints CRUD) del esquema seguridad.

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


# CRUD de seguridad.factor_autenticacion en /api/v1/seguridad/factores-autenticacion/
class FactorAutenticacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.FactorAutenticacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FactorAutenticacionSerializer


# CRUD de seguridad.sesion_usuario en /api/v1/seguridad/sesiones-usuario/
class SesionUsuarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.SesionUsuario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SesionUsuarioSerializer


# CRUD de seguridad.intento_acceso en /api/v1/seguridad/intentos-acceso/
class IntentoAccesoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.IntentoAcceso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.IntentoAccesoSerializer


# CRUD de seguridad.regla_deteccion en /api/v1/seguridad/reglas-deteccion/
class ReglaDeteccionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ReglaDeteccion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ReglaDeteccionSerializer


# CRUD de seguridad.bloqueo en /api/v1/seguridad/bloqueos/
class BloqueoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Bloqueo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BloqueoSerializer


# CRUD de seguridad.senuelo en /api/v1/seguridad/senuelos/
class SenueloViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Senuelo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SenueloSerializer


# CRUD de seguridad.alerta_seguridad en /api/v1/seguridad/alertas-seguridad/
class AlertaSeguridadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AlertaSeguridad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AlertaSeguridadSerializer


# CRUD de seguridad.incidente en /api/v1/seguridad/incidentes/
class IncidenteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Incidente.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.IncidenteSerializer


# CRUD de seguridad.ejecucion_prueba en /api/v1/seguridad/ejecuciones-prueba/
class EjecucionPruebaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EjecucionPrueba.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EjecucionPruebaSerializer


# CRUD de seguridad.copia_seguridad en /api/v1/seguridad/copias-seguridad/
class CopiaSeguridadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CopiaSeguridad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CopiaSeguridadSerializer
