"""Vistas (endpoints CRUD) del esquema iot.

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


# CRUD de iot.dispositivo en /api/v1/iot/dispositivos/
class DispositivoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Dispositivo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DispositivoSerializer


# CRUD de iot.sensor en /api/v1/iot/sensores/
class SensorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Sensor.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SensorSerializer


# CRUD de iot.actuador en /api/v1/iot/actuadores/
class ActuadorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Actuador.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ActuadorSerializer


# CRUD de iot.lectura en /api/v1/iot/lecturas/
class LecturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Lectura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LecturaSerializer


# CRUD de iot.regla_automatizacion en /api/v1/iot/reglas/
class ReglaAutomatizacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ReglaAutomatizacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ReglaAutomatizacionSerializer


# CRUD de iot.comando_actuador en /api/v1/iot/comandos/
class ComandoActuadorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ComandoActuador.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ComandoActuadorSerializer


# CRUD de iot.zona_seguridad en /api/v1/iot/zonas-seguridad/
class ZonaSeguridadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ZonaSeguridad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ZonaSeguridadSerializer


# CRUD de iot.cambio_estado_alarma en /api/v1/iot/cambios-estado-alarma/
class CambioEstadoAlarmaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CambioEstadoAlarma.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CambioEstadoAlarmaSerializer


# CRUD de iot.credencial_acceso en /api/v1/iot/credenciales-acceso/
class CredencialAccesoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CredencialAcceso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CredencialAccesoSerializer


# CRUD de iot.camara en /api/v1/iot/camaras/
class CamaraViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Camara.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CamaraSerializer


# CRUD de iot.evento_seguridad en /api/v1/iot/eventos-seguridad/
class EventoSeguridadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EventoSeguridad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EventoSeguridadSerializer


# CRUD de iot.clip_video en /api/v1/iot/clipes-video/
class ClipVideoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ClipVideo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ClipVideoSerializer


# CRUD de iot.mision_robot en /api/v1/iot/misiones-robot/
class MisionRobotViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MisionRobot.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MisionRobotSerializer


# CRUD de iot.prioridad_carga en /api/v1/iot/prioridades-carga/
class PrioridadCargaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PrioridadCarga.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PrioridadCargaSerializer
