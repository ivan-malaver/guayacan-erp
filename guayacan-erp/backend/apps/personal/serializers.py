"""Serializers del esquema personal: convierten los modelos en JSON y el JSON recibido en datos validados.

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


# personal.cuadrilla <-> JSON en /api/v1/personal/cuadrillas/
class CuadrillaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cuadrilla  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.cuadrilla_miembro <-> JSON en /api/v1/personal/cuadrillas-miembro/
class CuadrillaMiembroSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CuadrillaMiembro  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.turno <-> JSON en /api/v1/personal/turnos/
class TurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Turno  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.ausencia <-> JSON en /api/v1/personal/ausencias/
class AusenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ausencia  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.plantilla_tarea <-> JSON en /api/v1/personal/plantillas-tarea/
class PlantillaTareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlantillaTarea  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.tarea <-> JSON en /api/v1/personal/tareas/
class TareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tarea  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        # PER-04/06: quién aprobó y las horas los pone la base con el usuario de la sesión; si el cliente los enviara,
        # podría aprobar a nombre de otra persona
        read_only_fields = SOLO_LECTURA + ('aprobado_por', 'aprobado_en', 'iniciada_en', 'terminada_en')

    def validate_estado(self, estado):
        if estado in ('aprobada', 'devuelta'):
            raise serializers.ValidationError('Se aprueba con /aprobar/ y se devuelve con /devolver/ (PER-06)')
        return estado


# personal.paso_tarea <-> JSON en /api/v1/personal/tareas/{id}/pasos/
class RevisionTareaSerializer(serializers.Serializer):
    """PER-06: lo que envía el aprobador en /aprobar/ (comentario opcional) o /devolver/ (motivo obligatorio)."""
    motivo = serializers.CharField(required=False)


class PasoTareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PasoTarea  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        # PER-05: la hora en que se marcó la pone la base (o la sincronización con la hora del celular)
        read_only_fields = SOLO_LECTURA + ('hecho_en',)
        extra_kwargs = {'hecho': {'required': False}}  # nace sin marcar


# personal.evidencia_tarea <-> JSON en /api/v1/personal/tareas/{id}/evidencias/
class EvidenciaTareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EvidenciaTarea  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.matriz_responsabilidad <-> JSON en /api/v1/personal/matrices-responsabilidad/
class MatrizResponsabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MatrizResponsabilidad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.asignacion_equipo <-> JSON en /api/v1/personal/asignaciones-equipo/
class AsignacionEquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AsignacionEquipo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.credencial_trabajo <-> JSON en /api/v1/personal/credenciales-trabajo/
class CredencialTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CredencialTrabajo  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.jornada <-> JSON en /api/v1/personal/jornadas/
class JornadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Jornada  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.area_responsabilidad <-> JSON en /api/v1/personal/areas-responsabilidad/
class AreaResponsabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AreaResponsabilidad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.miembro_area <-> JSON en /api/v1/personal/miembros-area/
class MiembroAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MiembroArea  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.patron_turno <-> JSON en /api/v1/personal/patrones-turno/
class PatronTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PatronTurno  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.patron_turno_detalle <-> JSON en /api/v1/personal/patrones-turno/{id}/dias/
class PatronTurnoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PatronTurnoDetalle  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.cronograma <-> JSON en /api/v1/personal/cronogramas/
class CronogramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cronograma  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.asignacion_patron <-> JSON en /api/v1/personal/asignaciones-patron/
class AsignacionPatronSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AsignacionPatron  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.requerimiento_cobertura <-> JSON en /api/v1/personal/requerimientos-cobertura/
class RequerimientoCoberturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RequerimientoCobertura  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario


# personal.disponibilidad <-> JSON en /api/v1/personal/disponibilidades/
class DisponibilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Disponibilidad  # tabla que representa
        fields = '__all__'  # expone todas sus columnas
        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario
