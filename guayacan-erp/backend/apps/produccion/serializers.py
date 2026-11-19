"""Serializers del esquema produccion: convierten los modelos en JSON y el JSON recibido en datos validados.

QUÉ HACE UN SERIALIZER
1. Al responder: toma una fila (objeto del modelo) y la convierte en JSON para el frontend.
2. Al recibir (POST, PUT, PATCH): revisa que el JSON traiga los campos obligatorios, con el tipo correcto y
   valores permitidos, antes de enviarlo a la base. La base vuelve a validar las reglas de negocio.

Generado por docs/uml/fuentes/gen_apps.py. Un caso de uso que necesite otros campos crea su propio serializer
aquí mismo, debajo de los generados."""
from rest_framework import serializers

from . import models

# Campos que pone la base (identificador, finca, fechas de control): el usuario puede verlos pero no enviarlos
SOLO_LECTURA = ('id', 'predio', 'creado_en', 'actualizado_en')


# produccion.especie <-> JSON en /api/v1/produccion/especies/
class EspecieSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Especie  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.lote_animal <-> JSON en /api/v1/produccion/lotes-animal/
class LoteAnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LoteAnimal  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
        # PRO-01: si no se envían, el servicio iguala cantidad_actual a cantidad_inicial y la base pone estado 'activo'
        extra_kwargs = {'cantidad_actual': {'required': False}, 'estado': {'required': False}}


# produccion.animal <-> JSON en /api/v1/produccion/animales/
class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Animal  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


class ClasificacionManualSerializer(serializers.Serializer):
    """PRO-02: una categoría contada a mano (o por visión) dentro del alta de la postura."""
    categoria_huevo = serializers.PrimaryKeyRelatedField(queryset=models.CategoriaHuevo.objects.all())
    cantidad = serializers.IntegerField(min_value=0)
    metodo = serializers.ChoiceField(choices=['manual', 'vision'], default='manual')


# produccion.registro_postura <-> JSON en /api/v1/produccion/registros-postura/
class RegistroPosturaSerializer(serializers.ModelSerializer):
    # PRO-02: clasificación opcional en el mismo envío; solo se reciben (no se muestran en la respuesta)
    clasificacion = ClasificacionManualSerializer(many=True, required=False, write_only=True)
    pesos_g = serializers.ListField(child=serializers.DecimalField(max_digits=5, decimal_places=1, min_value=0),
                                    required=False, write_only=True)

    class Meta:
        model = models.RegistroPostura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
        # PRO-02: en la API lo pone el servicio con el usuario del token; la sincronización sin conexión aún lo recibe del cliente
        extra_kwargs = {'registrado_por': {'required': False}, 'huevos_rotos': {'required': False}}


# produccion.registro_alimentacion <-> JSON en /api/v1/produccion/registros-alimentacion/
class RegistroAlimentacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroAlimentacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.evento_sanitario <-> JSON en /api/v1/produccion/eventos-sanitario/
class EventoSanitarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventoSanitario  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.registro_pesaje <-> JSON en /api/v1/produccion/registros-pesaje/
class RegistroPesajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroPesaje  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.evento_reproductivo <-> JSON en /api/v1/produccion/eventos-reproductivo/
class EventoReproductivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventoReproductivo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.calidad_agua_estanque <-> JSON en /api/v1/produccion/calidad-agua/
class CalidadAguaEstanqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CalidadAguaEstanque  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.cultivo <-> JSON en /api/v1/produccion/cultivos/
class CultivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cultivo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.siembra <-> JSON en /api/v1/produccion/siembras/
class SiembraSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Siembra  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.labor_cultural <-> JSON en /api/v1/produccion/labores-cultural/
class LaborCulturalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LaborCultural  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.cosecha <-> JSON en /api/v1/produccion/cosechas/
class CosechaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cosecha  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.analisis_suelo <-> JSON en /api/v1/produccion/analisis-suelo/
class AnalisisSueloSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AnalisisSuelo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.categoria_huevo <-> JSON en /api/v1/produccion/categorias-huevo/
class CategoriaHuevoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CategoriaHuevo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.clasificacion_postura <-> JSON en /api/v1/produccion/clasificaciones-postura/
class ClasificacionPosturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ClasificacionPostura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.registro_bioseguridad <-> JSON en /api/v1/produccion/registros-bioseguridad/
class RegistroBioseguridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RegistroBioseguridad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# produccion.produccion_abono <-> JSON en /api/v1/produccion/producciones-abono/
class ProduccionAbonoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProduccionAbono  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
