"""Vistas (endpoints CRUD) del esquema produccion.

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


# CRUD de produccion.especie en /api/v1/produccion/especies/
class EspecieViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Especie.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EspecieSerializer


# CRUD de produccion.lote_animal en /api/v1/produccion/lotes-animal/
class LoteAnimalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LoteAnimal.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LoteAnimalSerializer


# CRUD de produccion.animal en /api/v1/produccion/animales/
class AnimalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Animal.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AnimalSerializer


# CRUD de produccion.registro_postura en /api/v1/produccion/registros-postura/
class RegistroPosturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroPostura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroPosturaSerializer


# CRUD de produccion.registro_alimentacion en /api/v1/produccion/registros-alimentacion/
class RegistroAlimentacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroAlimentacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroAlimentacionSerializer


# CRUD de produccion.evento_sanitario en /api/v1/produccion/eventos-sanitario/
class EventoSanitarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EventoSanitario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EventoSanitarioSerializer


# CRUD de produccion.registro_pesaje en /api/v1/produccion/registros-pesaje/
class RegistroPesajeViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroPesaje.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroPesajeSerializer


# CRUD de produccion.evento_reproductivo en /api/v1/produccion/eventos-reproductivo/
class EventoReproductivoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EventoReproductivo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EventoReproductivoSerializer


# CRUD de produccion.calidad_agua_estanque en /api/v1/produccion/calidad-agua/
class CalidadAguaEstanqueViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CalidadAguaEstanque.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CalidadAguaEstanqueSerializer


# CRUD de produccion.cultivo en /api/v1/produccion/cultivos/
class CultivoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cultivo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CultivoSerializer


# CRUD de produccion.siembra en /api/v1/produccion/siembras/
class SiembraViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Siembra.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SiembraSerializer


# CRUD de produccion.labor_cultural en /api/v1/produccion/labores-cultural/
class LaborCulturalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LaborCultural.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LaborCulturalSerializer


# CRUD de produccion.cosecha en /api/v1/produccion/cosechas/
class CosechaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cosecha.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CosechaSerializer


# CRUD de produccion.analisis_suelo en /api/v1/produccion/analisis-suelo/
class AnalisisSueloViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.AnalisisSuelo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AnalisisSueloSerializer


# CRUD de produccion.categoria_huevo en /api/v1/produccion/categorias-huevo/
class CategoriaHuevoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.CategoriaHuevo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CategoriaHuevoSerializer


# CRUD de produccion.clasificacion_postura en /api/v1/produccion/clasificaciones-postura/
class ClasificacionPosturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ClasificacionPostura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ClasificacionPosturaSerializer


# CRUD de produccion.registro_bioseguridad en /api/v1/produccion/registros-bioseguridad/
class RegistroBioseguridadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroBioseguridad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroBioseguridadSerializer


# CRUD de produccion.produccion_abono en /api/v1/produccion/producciones-abono/
class ProduccionAbonoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ProduccionAbono.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ProduccionAbonoSerializer
