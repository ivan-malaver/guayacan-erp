"""Vistas (endpoints CRUD) del esquema proyectos.

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


# CRUD de proyectos.proyecto en /api/v1/proyectos/proyectos/
class ProyectoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Proyecto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ProyectoSerializer


# CRUD de proyectos.interesado en /api/v1/proyectos/interesados/
class InteresadoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Interesado.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.InteresadoSerializer


# CRUD de proyectos.elemento_edt en /api/v1/proyectos/elementos-edt/
class ElementoEdtViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ElementoEdt.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ElementoEdtSerializer


# CRUD de proyectos.iteracion en /api/v1/proyectos/iteraciones/
class IteracionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Iteracion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.IteracionSerializer


# CRUD de proyectos.actividad en /api/v1/proyectos/actividades/
class ActividadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Actividad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ActividadSerializer


# CRUD de proyectos.dependencia en /api/v1/proyectos/actividades/{id}/dependencias/
class DependenciaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Dependencia.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DependenciaSerializer


# CRUD de proyectos.riesgo en /api/v1/proyectos/riesgos/
class RiesgoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Riesgo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RiesgoSerializer


# CRUD de proyectos.registro en /api/v1/proyectos/registros/
class RegistroViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Registro.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroSerializer


# CRUD de proyectos.solicitud_cambio en /api/v1/proyectos/solicitudes-cambio/
class SolicitudCambioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.SolicitudCambio.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SolicitudCambioSerializer


# CRUD de proyectos.linea_base en /api/v1/proyectos/lineas-base/
class LineaBaseViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LineaBase.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LineaBaseSerializer


# CRUD de proyectos.medicion_valor_ganado en /api/v1/proyectos/mediciones-valor-ganado/
class MedicionValorGanadoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MedicionValorGanado.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MedicionValorGanadoSerializer
