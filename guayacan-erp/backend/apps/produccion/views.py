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

from . import models, serializers, services


# CRUD de produccion.especie en /api/v1/produccion/especies/
class EspecieViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Especie.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EspecieSerializer


# CRUD de produccion.lote_animal en /api/v1/produccion/lotes-animal/  (el alta es PRO-01)
class LoteAnimalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LoteAnimal.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LoteAnimalSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_01_registrar_ingreso_lote_animales(usuario=self.request.user,
                                                                             **serializer.validated_data)


# CRUD de produccion.animal en /api/v1/produccion/animales/
class AnimalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Animal.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AnimalSerializer


# CRUD de produccion.registro_postura en /api/v1/produccion/registros-postura/  (el alta es PRO-02)
class RegistroPosturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroPostura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroPosturaSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_02_registrar_postura_diaria_clasificar_huevo(usuario=self.request.user,
                                                                                       **serializer.validated_data)


# CRUD de produccion.registro_alimentacion en /api/v1/produccion/registros-alimentacion/  (el alta es PRO-03)
class RegistroAlimentacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroAlimentacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroAlimentacionSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_03_registrar_alimentacion_pesajes_eventos_sanitarios(
            usuario=self.request.user, modelo=models.RegistroAlimentacion, **serializer.validated_data)


# CRUD de produccion.evento_sanitario en /api/v1/produccion/eventos-sanitario/  (el alta es PRO-03)
class EventoSanitarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EventoSanitario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EventoSanitarioSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_03_registrar_alimentacion_pesajes_eventos_sanitarios(
            usuario=self.request.user, modelo=models.EventoSanitario, **serializer.validated_data)


# CRUD de produccion.registro_pesaje en /api/v1/produccion/registros-pesaje/  (el alta es PRO-03)
class RegistroPesajeViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RegistroPesaje.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RegistroPesajeSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_03_registrar_alimentacion_pesajes_eventos_sanitarios(
            usuario=self.request.user, modelo=models.RegistroPesaje, **serializer.validated_data)


# CRUD de produccion.evento_reproductivo en /api/v1/produccion/eventos-reproductivo/  (el alta es PRO-04)
class EventoReproductivoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EventoReproductivo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EventoReproductivoSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_04_registrar_eventos_reproductivos_ovinos_caprinos(
            usuario=self.request.user, **serializer.validated_data)


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


# CRUD de produccion.siembra en /api/v1/produccion/siembras/  (el alta es PRO-05)
class SiembraViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Siembra.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SiembraSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_05_registrar_siembra_labores_culturales(
            usuario=self.request.user, modelo=models.Siembra, **serializer.validated_data)


# CRUD de produccion.labor_cultural en /api/v1/produccion/labores-cultural/  (el alta es PRO-05)
class LaborCulturalViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LaborCultural.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LaborCulturalSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_05_registrar_siembra_labores_culturales(
            usuario=self.request.user, modelo=models.LaborCultural, **serializer.validated_data)


# CRUD de produccion.cosecha en /api/v1/produccion/cosechas/  (el alta es PRO-06)
class CosechaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cosecha.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CosechaSerializer

    def perform_create(self, serializer):
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = services.pro_06_registrar_cosecha_destino(usuario=self.request.user,
                                                                        **serializer.validated_data)


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
