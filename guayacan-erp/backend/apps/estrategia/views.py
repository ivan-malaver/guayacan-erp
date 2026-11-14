"""Vistas (endpoints CRUD) del esquema estrategia.

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


# CRUD de estrategia.linea_negocio en /api/v1/estrategia/lineas-negocio/
class LineaNegocioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LineaNegocio.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LineaNegocioSerializer


# CRUD de estrategia.factor_dofa en /api/v1/estrategia/factores-dofa/
class FactorDofaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.FactorDofa.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FactorDofaSerializer


# CRUD de estrategia.estudio_mercado en /api/v1/estrategia/estudios-mercado/
class EstudioMercadoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EstudioMercado.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EstudioMercadoSerializer


# CRUD de estrategia.iniciativa en /api/v1/estrategia/iniciativas/
class IniciativaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Iniciativa.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.IniciativaSerializer


# CRUD de estrategia.evaluacion_proyecto en /api/v1/estrategia/evaluaciones-proyecto/
class EvaluacionProyectoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EvaluacionProyecto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EvaluacionProyectoSerializer


# CRUD de estrategia.flujo_proyecto en /api/v1/estrategia/evaluaciones-proyecto/{id}/flujos/
class FlujoProyectoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.FlujoProyecto.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FlujoProyectoSerializer


# CRUD de estrategia.reinversion en /api/v1/estrategia/reinversiones/
class ReinversionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Reinversion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ReinversionSerializer


# CRUD de estrategia.seguimiento_iniciativa en /api/v1/estrategia/seguimientos-iniciativa/
class SeguimientoIniciativaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.SeguimientoIniciativa.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SeguimientoIniciativaSerializer


# CRUD de estrategia.objetivo en /api/v1/estrategia/objetivos/
class ObjetivoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Objetivo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ObjetivoSerializer
