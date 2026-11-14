"""Vistas (endpoints CRUD) del esquema cumplimiento.

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


# CRUD de cumplimiento.norma en /api/v1/cumplimiento/normas/
class NormaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Norma.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.NormaSerializer


# CRUD de cumplimiento.requisito en /api/v1/cumplimiento/requisitos/
class RequisitoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Requisito.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RequisitoSerializer


# CRUD de cumplimiento.expediente en /api/v1/cumplimiento/expedientes/
class ExpedienteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Expediente.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ExpedienteSerializer


# CRUD de cumplimiento.evaluacion_requisito en /api/v1/cumplimiento/evaluaciones-requisito/
class EvaluacionRequisitoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EvaluacionRequisito.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EvaluacionRequisitoSerializer


# CRUD de cumplimiento.evidencia_requisito en /api/v1/cumplimiento/evidencias-requisito/
class EvidenciaRequisitoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EvidenciaRequisito.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EvidenciaRequisitoSerializer


# CRUD de cumplimiento.auditoria_externa en /api/v1/cumplimiento/auditorias-externas/
class AuditoriaExternaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AuditoriaExterna.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AuditoriaExternaSerializer


# CRUD de cumplimiento.no_conformidad en /api/v1/cumplimiento/no-conformidades/
class NoConformidadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.NoConformidad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.NoConformidadSerializer


# CRUD de cumplimiento.accion_correctiva en /api/v1/cumplimiento/acciones-correctivas/
class AccionCorrectivaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AccionCorrectiva.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AccionCorrectivaSerializer
