"""Vistas (endpoints CRUD) del esquema formacion.

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


# CRUD de formacion.competencia en /api/v1/formacion/competencias/
class CompetenciaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Competencia.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CompetenciaSerializer


# CRUD de formacion.curso en /api/v1/formacion/cursos/
class CursoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Curso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CursoSerializer


# CRUD de formacion.leccion en /api/v1/formacion/lecciones/
class LeccionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Leccion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LeccionSerializer


# CRUD de formacion.evaluacion en /api/v1/formacion/evaluaciones/
class EvaluacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Evaluacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EvaluacionSerializer


# CRUD de formacion.pregunta en /api/v1/formacion/preguntas/
class PreguntaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Pregunta.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PreguntaSerializer


# CRUD de formacion.inscripcion en /api/v1/formacion/inscripciones/
class InscripcionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Inscripcion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.InscripcionSerializer


# CRUD de formacion.progreso en /api/v1/formacion/progresos/
class ProgresoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Progreso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ProgresoSerializer


# CRUD de formacion.sesion_presencial en /api/v1/formacion/sesiones-presencial/
class SesionPresencialViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.SesionPresencial.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SesionPresencialSerializer


# CRUD de formacion.asistencia en /api/v1/formacion/asistencias/
class AsistenciaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Asistencia.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AsistenciaSerializer


# CRUD de formacion.certificado en /api/v1/formacion/certificados/
class CertificadoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Certificado.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CertificadoSerializer


# CRUD de formacion.habilitacion en /api/v1/formacion/habilitaciones/
class HabilitacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Habilitacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.HabilitacionSerializer


# CRUD de formacion.necesidad_formacion en /api/v1/formacion/necesidades-formacion/
class NecesidadFormacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.NecesidadFormacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.NecesidadFormacionSerializer


# CRUD de formacion.encuesta en /api/v1/formacion/encuestas/
class EncuestaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Encuesta.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EncuestaSerializer


# CRUD de formacion.queja_apelacion en /api/v1/formacion/quejas-apelacion/
class QuejaApelacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.QuejaApelacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.QuejaApelacionSerializer
