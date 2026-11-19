"""Serializers del esquema adopcion: convierten los modelos en JSON y el JSON recibido en datos validados.

QUÉ HACE UN SERIALIZER
1. Al responder: toma una fila (objeto del modelo) y la convierte en JSON para el frontend.
2. Al recibir (POST, PUT, PATCH): revisa que el JSON traiga los campos obligatorios, con el tipo correcto y
   valores permitidos, antes de enviarlo a la base. La base vuelve a validar las reglas de negocio.

Generado por docs/uml/fuentes/gen_apps.py. Un caso de uso que necesite otros campos crea su propio serializer
aquí mismo, debajo de los generados."""
from rest_framework import serializers

from apps.agenda.models import Visita
from apps.personal.models import Tarea

from . import models

# Campos que pone la base (identificador, finca, fechas de control): el usuario puede verlos pero no enviarlos
SOLO_LECTURA = ('id', 'predio', 'creado_en', 'actualizado_en')


# adopcion.plan <-> JSON en /api/v1/adopcion/planes/
class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Plan  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.sitio <-> JSON en /api/v1/adopcion/sitios/
class SitioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sitio  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.bien <-> JSON en /api/v1/adopcion/bienes/
class BienSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Bien  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.contrato <-> JSON en /api/v1/adopcion/contratos/
class ContratoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contrato  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.cuota <-> JSON en /api/v1/adopcion/cuotas/
class CuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cuota  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.seguimiento <-> JSON en /api/v1/adopcion/seguimientos/
class SeguimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Seguimiento  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.liquidacion <-> JSON en /api/v1/adopcion/liquidaciones/
class LiquidacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Liquidacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# adopcion.movimiento_saldo <-> JSON en /api/v1/adopcion/movimientos-saldo/
class MovimientoSaldoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MovimientoSaldo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


class AdoptanteSerializer(serializers.Serializer):
    """ADO-02: datos del adoptante; si ya existe un tercero con ese documento se usa el existente."""
    tipo_persona = serializers.ChoiceField(choices=['natural', 'juridica'], default='natural')
    tipo_documento = serializers.ChoiceField(choices=['CC', 'CE', 'NIT', 'PAS', 'TI', 'PPT'])
    numero_documento = serializers.CharField(max_length=20)
    nombres = serializers.CharField(max_length=120)
    apellidos = serializers.CharField(max_length=120, required=False)
    correo = serializers.EmailField(required=False)
    telefono = serializers.CharField(max_length=20, required=False)
    whatsapp = serializers.CharField(max_length=20, required=False)


class CompraSerializer(serializers.Serializer):
    """ADO-02: lo que envía el vendedor (o el agente) en POST /api/v1/adopcion/contratos/compra/."""
    bien = serializers.PrimaryKeyRelatedField(queryset=models.Bien.objects.all())
    adoptante = AdoptanteSerializer()
    modalidad_siembra = serializers.ChoiceField(choices=['propia', 'trabajador', 'no_aplica'], default='no_aplica')
    # Ley 1581: autorización expresa para tratar los datos y evidencia de cómo se dio
    autoriza_datos = serializers.BooleanField()
    autoriza_seguimiento = serializers.BooleanField(default=False)  # fotos y video del bien (obligatoria si siembra un trabajador)
    version_politica = serializers.CharField(max_length=20)
    medio_autorizacion = serializers.ChoiceField(choices=['whatsapp', 'web', 'formulario_fisico', 'verbal_grabado', 'correo'])
    evidencia_url = serializers.URLField(max_length=300, required=False)


class AvisoPagoSerializer(serializers.Serializer):
    """ADO-02: aviso (webhook) de la pasarela, ya con la firma verificada."""
    referencia = serializers.RegexField(r'^\d+:.+$', max_length=60)  # '<predio_id>:<número del contrato>'
    estado = serializers.ChoiceField(choices=['aprobado', 'rechazado'])
    id_transaccion = serializers.CharField(max_length=80)
    valor = serializers.DecimalField(max_digits=14, decimal_places=2)


class SiembraPersonaSerializer(serializers.Serializer):
    """ADO-03: lo que envía el encargado en POST /api/v1/adopcion/bienes/{id}/siembra/."""
    fecha = serializers.DateField()
    visita = serializers.PrimaryKeyRelatedField(queryset=Visita.objects.all())


class SiembraTrabajadorSerializer(serializers.Serializer):
    """ADO-04: lo que envía el trabajador (o el encargado) en POST /api/v1/adopcion/bienes/{id}/siembra/."""
    fecha = serializers.DateField()
    tarea = serializers.PrimaryKeyRelatedField(queryset=Tarea.objects.all())
    video_url = serializers.URLField(max_length=300)  # obligatorio: sin video no hay siembra por trabajador
