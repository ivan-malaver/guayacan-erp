"""Serializers del esquema nucleo: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# Usuario: nunca se devuelve la contraseña (ni siquiera cifrada)
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Usuario
        exclude = ('password',)  # todos los campos menos la contraseña
        read_only_fields = ('id', 'last_login', 'creado_en', 'actualizado_en')


# nucleo.rol <-> JSON en /api/v1/nucleo/roles/
class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rol  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.permiso <-> JSON en /api/v1/nucleo/permisos/
class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Permiso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.rol_permiso <-> JSON en /api/v1/nucleo/roles/{id}/permisos/
class RolPermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RolPermiso  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.usuario_rol <-> JSON en /api/v1/nucleo/usuarios/{id}/roles/
class UsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UsuarioRol  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.parametro <-> JSON en /api/v1/nucleo/parametros/
class ParametroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Parametro  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.auditoria <-> JSON en /api/v1/nucleo/auditoria/
class AuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Auditoria  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.evento_salida <-> JSON en /api/v1/nucleo/eventos-salida/
class EventoSalidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventoSalida  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.predio <-> JSON en /api/v1/nucleo/predios/
class PredioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Predio  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.zona <-> JSON en /api/v1/nucleo/zonas/
class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Zona  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.dispositivo_captura <-> JSON en /api/v1/nucleo/dispositivos-captura/
class DispositivoCapturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DispositivoCaptura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.sincronizacion <-> JSON en /api/v1/nucleo/sincronizaciones/
class SincronizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Sincronizacion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.funcionalidad <-> JSON en /api/v1/nucleo/funcionalidades/
class FuncionalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Funcionalidad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.nota_voz <-> JSON en /api/v1/nucleo/notas-voz/
class NotaVozSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NotaVoz  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.llave_api <-> JSON en /api/v1/nucleo/llaves-api/
class LlaveApiSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.LlaveApi  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.webhook_suscripcion <-> JSON en /api/v1/nucleo/webhooks-suscripcion/
class WebhookSuscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebhookSuscripcion  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# nucleo.webhook_entrega <-> JSON en /api/v1/nucleo/webhooks-entrega/
class WebhookEntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WebhookEntrega  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
