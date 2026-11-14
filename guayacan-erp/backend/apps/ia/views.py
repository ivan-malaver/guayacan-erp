"""Vistas (endpoints CRUD) del esquema ia.

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


# CRUD de ia.agente en /api/v1/ia/agentes/
class AgenteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Agente.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AgenteSerializer


# CRUD de ia.herramienta en /api/v1/ia/herramientas/
class HerramientaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Herramienta.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.HerramientaSerializer


# CRUD de ia.agente_herramienta en /api/v1/ia/agentes/{id}/herramientas/
class AgenteHerramientaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AgenteHerramienta.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AgenteHerramientaSerializer


# CRUD de ia.solicitud_aprobacion en /api/v1/ia/solicitudes-aprobacion/
class SolicitudAprobacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.SolicitudAprobacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SolicitudAprobacionSerializer


# CRUD de ia.documento_conocimiento en /api/v1/ia/documentos-conocimiento/
class DocumentoConocimientoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.DocumentoConocimiento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DocumentoConocimientoSerializer


# CRUD de ia.fragmento_conocimiento en /api/v1/ia/fragmentos-conocimiento/
class FragmentoConocimientoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.FragmentoConocimiento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FragmentoConocimientoSerializer


# CRUD de ia.recomendacion en /api/v1/ia/recomendaciones/
class RecomendacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Recomendacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RecomendacionSerializer


# CRUD de ia.evaluacion_respuesta en /api/v1/ia/evaluaciones-respuesta/
class EvaluacionRespuestaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EvaluacionRespuesta.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EvaluacionRespuestaSerializer


# CRUD de ia.consumo_ia en /api/v1/ia/consumos/
class ConsumoIaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ConsumoIa.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ConsumoIaSerializer


# CRUD de ia.regla_conversacion en /api/v1/ia/reglas-conversacion/
class ReglaConversacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ReglaConversacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ReglaConversacionSerializer


# CRUD de ia.escalamiento en /api/v1/ia/escalamientos/
class EscalamientoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Escalamiento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EscalamientoSerializer


# CRUD de ia.modelo_pronostico en /api/v1/ia/modelos-pronostico/
class ModeloPronosticoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ModeloPronostico.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ModeloPronosticoSerializer


# CRUD de ia.pronostico_demanda en /api/v1/ia/pronosticos-demanda/
class PronosticoDemandaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.PronosticoDemanda.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PronosticoDemandaSerializer


# CRUD de ia.diagnostico_imagen en /api/v1/ia/diagnosticos-imagen/
class DiagnosticoImagenViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.DiagnosticoImagen.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DiagnosticoImagenSerializer


# CRUD de ia.escenario en /api/v1/ia/escenarios/
class EscenarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Escenario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EscenarioSerializer


# CRUD de ia.decision en /api/v1/ia/decisiones/
class DecisionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Decision.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DecisionSerializer
