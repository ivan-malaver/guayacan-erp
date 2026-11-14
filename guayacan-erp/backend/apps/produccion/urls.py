"""Rutas de /api/v1/produccion/ (cómo una dirección web llega a su vista).

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
router.register('especies', views.EspecieViewSet, basename='produccion-especies')  # tabla produccion.especie
router.register('lotes-animal', views.LoteAnimalViewSet, basename='produccion-lotes-animal')  # tabla produccion.lote_animal
router.register('animales', views.AnimalViewSet, basename='produccion-animales')  # tabla produccion.animal
router.register('registros-postura', views.RegistroPosturaViewSet, basename='produccion-registros-postura')  # tabla produccion.registro_postura
router.register('registros-alimentacion', views.RegistroAlimentacionViewSet, basename='produccion-registros-alimentacion')  # tabla produccion.registro_alimentacion
router.register('eventos-sanitario', views.EventoSanitarioViewSet, basename='produccion-eventos-sanitario')  # tabla produccion.evento_sanitario
router.register('registros-pesaje', views.RegistroPesajeViewSet, basename='produccion-registros-pesaje')  # tabla produccion.registro_pesaje
router.register('eventos-reproductivo', views.EventoReproductivoViewSet, basename='produccion-eventos-reproductivo')  # tabla produccion.evento_reproductivo
router.register('calidad-agua', views.CalidadAguaEstanqueViewSet, basename='produccion-calidad-agua')  # tabla produccion.calidad_agua_estanque
router.register('cultivos', views.CultivoViewSet, basename='produccion-cultivos')  # tabla produccion.cultivo
router.register('siembras', views.SiembraViewSet, basename='produccion-siembras')  # tabla produccion.siembra
router.register('labores-cultural', views.LaborCulturalViewSet, basename='produccion-labores-cultural')  # tabla produccion.labor_cultural
router.register('cosechas', views.CosechaViewSet, basename='produccion-cosechas')  # tabla produccion.cosecha
router.register('analisis-suelo', views.AnalisisSueloViewSet, basename='produccion-analisis-suelo')  # tabla produccion.analisis_suelo
router.register('categorias-huevo', views.CategoriaHuevoViewSet, basename='produccion-categorias-huevo')  # tabla produccion.categoria_huevo
router.register('clasificaciones-postura', views.ClasificacionPosturaViewSet, basename='produccion-clasificaciones-postura')  # tabla produccion.clasificacion_postura
router.register('registros-bioseguridad', views.RegistroBioseguridadViewSet, basename='produccion-registros-bioseguridad')  # tabla produccion.registro_bioseguridad
router.register('producciones-abono', views.ProduccionAbonoViewSet, basename='produccion-producciones-abono')  # tabla produccion.produccion_abono

urlpatterns = [
    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)
    path('', include(router.urls)),
]
