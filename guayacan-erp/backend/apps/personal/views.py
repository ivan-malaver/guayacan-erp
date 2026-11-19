"""Vistas (endpoints CRUD) del esquema personal.

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
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from guayacan.permisos import SoloPersonas
from guayacan.vistas import VistaModelo

from . import models, serializers, services


# CRUD de personal.cuadrilla en /api/v1/personal/cuadrillas/
class CuadrillaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cuadrilla.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CuadrillaSerializer


# CRUD de personal.cuadrilla_miembro en /api/v1/personal/cuadrillas-miembro/
class CuadrillaMiembroViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CuadrillaMiembro.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CuadrillaMiembroSerializer


# CRUD de personal.turno en /api/v1/personal/turnos/
class TurnoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Turno.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.TurnoSerializer


# CRUD de personal.ausencia en /api/v1/personal/ausencias/
class AusenciaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Ausencia.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AusenciaSerializer


# CRUD de personal.plantilla_tarea en /api/v1/personal/plantillas-tarea/
class PlantillaTareaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PlantillaTarea.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlantillaTareaSerializer


# CRUD de personal.tarea en /api/v1/personal/tareas/
class TareaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Tarea.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.TareaSerializer

    def perform_update(self, serializer):
        # PER-04: cambiar a quién se asigna (persona o cuadrilla) pasa por el servicio; el resto es el CRUD
        if {'empleado', 'cuadrilla'} & serializer.validated_data.keys():
            serializer.instance = services.per_04_asignar_tarea(usuario=self.request.user, tarea=serializer.instance,
                                                                **serializer.validated_data)
        elif 'estado' in serializer.validated_data:
            # PER-05: iniciar o terminar (las reglas de quién y cuándo están en la base)
            serializer.instance = services.per_05_ejecutar_tarea_evidencia(usuario=self.request.user, tarea=serializer.instance,
                                                                           **serializer.validated_data)
        else:
            serializer.save()

    @action(detail=True, methods=['get'])
    def candidatos(self, request, pk=None):
        """PER-04 · GET /api/v1/personal/tareas/{id}/candidatos/: a quién se le puede asignar la tarea ese día."""
        return Response(services.per_04_candidatos(tarea_id=self.get_object().pk))


# CRUD de personal.paso_tarea en /api/v1/personal/tareas/{id}/pasos/
class PasoTareaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PasoTarea.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PasoTareaSerializer

    def perform_update(self, serializer):
        serializer.save()
        serializer.instance.refresh_from_db()  # PER-05: hecho_en lo pone la base al marcar el paso


# CRUD de personal.evidencia_tarea en /api/v1/personal/tareas/{id}/evidencias/
class EvidenciaTareaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EvidenciaTarea.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EvidenciaTareaSerializer


# CRUD de personal.matriz_responsabilidad en /api/v1/personal/matrices-responsabilidad/
class MatrizResponsabilidadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MatrizResponsabilidad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MatrizResponsabilidadSerializer


# CRUD de personal.asignacion_equipo en /api/v1/personal/asignaciones-equipo/
class AsignacionEquipoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AsignacionEquipo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AsignacionEquipoSerializer


# CRUD de personal.credencial_trabajo en /api/v1/personal/credenciales-trabajo/
class CredencialTrabajoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CredencialTrabajo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CredencialTrabajoSerializer


# CRUD de personal.jornada en /api/v1/personal/jornadas/
class JornadaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Jornada.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.JornadaSerializer
    # AGD-04: la jornada nace solo en portería (agenda.validar_acceso la abre y la cierra); sin POST aquí no hay dos
    # caminos que la dupliquen. Quien no tiene carné entra por portería con empleado y método manual.
    # TODO(PER): revisar al construir los casos de Personal (la sincronización sin conexión tampoco la acepta: guayacan/captura.py)
    http_method_names = ['get', 'put', 'patch', 'head', 'options']


# CRUD de personal.area_responsabilidad en /api/v1/personal/areas-responsabilidad/
class AreaResponsabilidadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AreaResponsabilidad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AreaResponsabilidadSerializer


# CRUD de personal.miembro_area en /api/v1/personal/miembros-area/
class MiembroAreaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MiembroArea.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MiembroAreaSerializer


# CRUD de personal.patron_turno en /api/v1/personal/patrones-turno/
class PatronTurnoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PatronTurno.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PatronTurnoSerializer


# CRUD de personal.patron_turno_detalle en /api/v1/personal/patrones-turno/{id}/dias/
class PatronTurnoDetalleViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PatronTurnoDetalle.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PatronTurnoDetalleSerializer


# CRUD de personal.cronograma en /api/v1/personal/cronogramas/
class CronogramaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cronograma.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CronogramaSerializer


# CRUD de personal.asignacion_patron en /api/v1/personal/asignaciones-patron/
class AsignacionPatronViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AsignacionPatron.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AsignacionPatronSerializer


# CRUD de personal.requerimiento_cobertura en /api/v1/personal/requerimientos-cobertura/
class RequerimientoCoberturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RequerimientoCobertura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RequerimientoCoberturaSerializer


# CRUD de personal.disponibilidad en /api/v1/personal/disponibilidades/
class DisponibilidadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Disponibilidad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DisponibilidadSerializer


class RevisarTarea(APIView):
    """PER-06 · POST /api/v1/personal/tareas/{id}/aprobar/ y /devolver/ ({motivo}, obligatorio al devolver).

    Permisos y «nadie aprueba su propia tarea» los decide la base (403); aquí solo se bloquea a los agentes de IA.
    """

    permission_classes = [IsAuthenticated, SoloPersonas]
    decision = None  # 'aprobar' o 'devolver', lo fija urls.py

    def post(self, request, id):
        datos = serializers.RevisionTareaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        if self.decision == 'devolver' and not datos.validated_data.get('motivo'):
            raise ValidationError({'motivo': 'Para devolver una tarea hay que decir por qué'})
        tarea = services.per_06_aprobar_devolver_tarea(usuario=request.user, tarea_id=id, decision=self.decision,
                                                       **datos.validated_data)
        return Response(serializers.TareaSerializer(tarea).data)
