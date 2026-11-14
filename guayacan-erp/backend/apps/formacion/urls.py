"""Rutas de /api/v1/formacion/ (cómo una dirección web llega a su vista).

ORDEN
1. Primero las acciones de los casos de uso. Mientras no se construyan usan PorConstruir, que responde
   501 con el código del caso de uso: el frontend y la documentación OpenAPI ya las conocen.
2. Después las rutas anidadas (hijos de un registro, p. ej. las líneas de un pedido), si las hay.
3. Al final el CRUD de cada tabla, que registra el «router» de Django REST Framework.

CÓMO CONSTRUIR UNA ACCIÓN: escriba la vista real (o un método @action en views.py) y reemplace aquí
PorConstruir por esa vista. Generado por docs/uml/fuentes/gen_apps.py."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from guayacan.vistas import PorConstruir, PorConstruirPublico  # noqa: F401

from . import views

# El router crea las rutas de lista (/recurso/) y detalle (/recurso/<id>/) de cada ViewSet
router = DefaultRouter()
router.register('competencias', views.CompetenciaViewSet, basename='formacion-competencias')  # tabla formacion.competencia
router.register('cursos', views.CursoViewSet, basename='formacion-cursos')  # tabla formacion.curso
router.register('lecciones', views.LeccionViewSet, basename='formacion-lecciones')  # tabla formacion.leccion
router.register('evaluaciones', views.EvaluacionViewSet, basename='formacion-evaluaciones')  # tabla formacion.evaluacion
router.register('preguntas', views.PreguntaViewSet, basename='formacion-preguntas')  # tabla formacion.pregunta
router.register('inscripciones', views.InscripcionViewSet, basename='formacion-inscripciones')  # tabla formacion.inscripcion
router.register('progresos', views.ProgresoViewSet, basename='formacion-progresos')  # tabla formacion.progreso
router.register('sesiones-presencial', views.SesionPresencialViewSet, basename='formacion-sesiones-presencial')  # tabla formacion.sesion_presencial
router.register('asistencias', views.AsistenciaViewSet, basename='formacion-asistencias')  # tabla formacion.asistencia
router.register('certificados', views.CertificadoViewSet, basename='formacion-certificados')  # tabla formacion.certificado
router.register('habilitaciones', views.HabilitacionViewSet, basename='formacion-habilitaciones')  # tabla formacion.habilitacion
router.register('necesidades-formacion', views.NecesidadFormacionViewSet, basename='formacion-necesidades-formacion')  # tabla formacion.necesidad_formacion
router.register('encuestas', views.EncuestaViewSet, basename='formacion-encuestas')  # tabla formacion.encuesta
router.register('quejas-apelacion', views.QuejaApelacionViewSet, basename='formacion-quejas-apelacion')  # tabla formacion.queja_apelacion

urlpatterns = [
    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)
    # FOR-03 · Dictar una sesión presencial y registrar asistencia: POST /api/v1/formacion/sesiones-presenciales/{id}/certificar/
    path('sesiones-presenciales/<int:id>/certificar/', PorConstruir.as_view(caso_de_uso='FOR-03', metodo='POST'), name='for-03-sesiones-presenciales-id-certificar'),
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
