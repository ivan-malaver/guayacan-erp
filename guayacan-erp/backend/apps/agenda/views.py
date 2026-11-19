"""Vistas (endpoints CRUD) del esquema agenda.

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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from guayacan.permisos import SoloPersonas, requiere
from guayacan.vistas import VistaModelo

from . import models, serializers, services


# CRUD de agenda.recurso en /api/v1/agenda/recursos/
class RecursoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Recurso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RecursoSerializer


# CRUD de agenda.cita en /api/v1/agenda/citas/
class CitaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cita.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CitaSerializer


# CRUD de agenda.visita en /api/v1/agenda/visitas/
class VisitaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Visita.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.VisitaSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.agd_03_programar_aprobar_visita(usuario=self.request.user, **serializer.validated_data)


# CRUD de agenda.registro_acceso en /api/v1/agenda/registros-acceso/
class RegistroAccesoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroAcceso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroAccesoSerializer


class AprobarVisita(APIView):
    """AGD-03 · POST /api/v1/agenda/visitas/{id}/aprobar/ con {decision: aprobar | rechazar, motivo}."""

    permission_classes = [IsAuthenticated, SoloPersonas, requiere('agenda.aprobar_visita')]

    def post(self, request, id):
        datos = serializers.DecisionVisitaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        visita = services.agd_03_decidir_visita(usuario=request.user, visita_id=id, **datos.validated_data)
        return Response(serializers.VisitaSerializer(visita).data)


class PaseVisita(APIView):
    """AGD-03 · POST /api/v1/agenda/visitas/{id}/pase/: devuelve el código del pase (para el QR) una sola vez."""

    permission_classes = [IsAuthenticated, SoloPersonas, requiere('agenda.aprobar_visita')]

    def post(self, request, id):
        return Response({'visita': id, 'codigo_pase': services.agd_03_emitir_pase(usuario=request.user, visita_id=id)})
