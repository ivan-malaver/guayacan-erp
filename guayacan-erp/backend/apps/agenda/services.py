"""Casos de uso del esquema agenda: una función por caso de uso.

POR QUÉ UNA CAPA DE SERVICIOS
Las vistas solo reciben y responden. La operación de negocio vive aquí para poder llamarla desde la API,
desde una tarea programada (Celery) o desde una prueba, siempre de la misma manera.

PATRÓN PARA CONSTRUIR CADA FUNCIÓN (ejemplo completo en docs/desarrollo/02_construir_un_caso_de_uso.md)
1. with transaction.atomic():  todo o nada; si algo falla no queda nada a medias.
2. Llamar la función de PostgreSQL que aplica la regla (están listadas en «Reglas en la base»).
   No repita la regla en Python: la base ya la valida y está probada.
3. Si la base rechaza, lanza un error con el mensaje en español; guayacan/errores.py lo convierte en
   una respuesta 422 o 409 para el usuario. No hace falta capturarlo aquí.
4. publicar(...) un evento si otros módulos o los agentes deben enterarse (patrón outbox).
5. Devolver el objeto o los datos que mostrará la respuesta.

Cada función está vacía (NotImplementedError) y su documentación resume la especificación.
Especificación completa: documento técnico (pestaña de casos de uso) y docs/casos-de-uso/."""
# transaction y publicar aún no se usan (las funciones están vacías); «noqa» evita el aviso del revisor
import hashlib

from django.db import connection, transaction  # noqa: F401
from rest_framework.exceptions import ValidationError

from apps.personal.models import CredencialTrabajo
from guayacan.eventos import publicar  # noqa: F401

from . import models


def agd_01_configurar_recursos_agendables(*, usuario, **datos):
    """AGD-01 · Configurar recursos agendables

    Actores: Administrador
    Fase 3
    Tablas: agenda.recurso
    Reglas en la base: formato y permisos de DRF
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-01:
    # 1. with transaction.atomic():
    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-01: por construir')


def agd_02_agendar_cita_recurso(*, usuario, **datos):
    """AGD-02 · Agendar una cita en un recurso

    Actores: Encargado de finca, Vendedor
    Fase 3
    Tablas: agenda.cita
    Reglas en la base: agenda.preparar_cita(), exclusión GiST sin cruces, agenda.recurso_libre()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-02:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.preparar_cita(), exclusión GiST sin cruces, agenda.recurso_libre()
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-02: por construir')


def agd_03_programar_aprobar_visita(*, usuario, **datos):
    """AGD-03 · Programar y aprobar una visita

    Actores: Encargado de finca; secundarios: Visitante o turista, Correo y SMS
    Fase 2
    Tablas: agenda.visita
    Reglas en la base: agenda.validar_visita(), agenda.emitir_pase()
    Endpoints: POST /api/v1/agenda/visitas/{id}/aprobar/; POST /api/v1/agenda/visitas/{id}/pase/
    Requerimientos: RQ-39, RF-16

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó VisitaSerializer).
    Paso 1 (registrar): la visita nace solicitada; el anfitrión, si no se indica, es quien la registra.
    La aprobación y el pase son agd_03_decidir_visita y agd_03_emitir_pase.
    Devuelve la visita creada.
    """
    datos.setdefault('anfitrion', usuario)
    # La declaración de bioseguridad (paso 2) viaja en contacto_aves_reciente; la base la exige al aprobar
    return models.Visita.objects.create(**datos)


def agd_03_decidir_visita(*, usuario, visita_id, decision, motivo=None):
    """AGD-03 paso 3: aprobar o rechazar (con motivo) una visita solicitada.

    La base exige que decida una persona, la declaración de 72 horas sin contacto con aves si va al galpón (3a)
    y el motivo del rechazo (3b). Devuelve la visita.
    """
    visita = models.Visita.objects.select_for_update().get(pk=visita_id)
    if visita.estado != 'solicitada':
        raise ValidationError({'estado': f'La visita ya está {visita.estado}'})
    with transaction.atomic():
        if decision == 'aprobar':
            visita.estado = 'aprobada'
        else:
            visita.estado, visita.motivo_rechazo = 'rechazada', motivo
        visita.save(update_fields=['estado', 'motivo_rechazo'])
        visita.refresh_from_db(fields=['aprobada_por'])  # lo pone la base al aprobar
        publicar(f'agenda.visita_{visita.estado}', 'agenda.visita', visita.id,
                 {'tipo': visita.tipo, 'nombre': visita.nombre, 'ingreso_programado': visita.ingreso_programado,
                  'motivo_rechazo': visita.motivo_rechazo})
    return visita


def agd_03_emitir_pase(*, usuario, visita_id):
    """AGD-03 paso 4: código del pase de una visita aprobada. La base guarda solo su huella.

    El código no va al outbox: quedaría en claro en nucleo.evento_salida. Se devuelve solo a quien lo pide.
    """
    # TODO(Volumen 4): enviarlo al visitante como QR por WhatsApp o correo (SQ14) cuando existan esos canales
    with connection.cursor() as cur:
        # Solo una visita aprobada recibe pase: si no, la base responde 422
        cur.execute('select agenda.emitir_pase(%s)', [visita_id])
        return cur.fetchone()[0]


def agd_04_registrar_entradas_salidas_porteria(*, usuario, **datos):
    """AGD-04 · Registrar entradas y salidas en portería

    Actores: Portería; secundarios: Visitante o turista
    Fase 2
    Tablas: agenda.registro_acceso, personal.jornada
    Reglas en la base: agenda.validar_acceso()
    Endpoints: CRUD de sus tablas
    Requerimientos: RQ-39, RF-16

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó RegistroAccesoSerializer).
      codigo_pase   código del QR del pase (AGD-03): se busca la visita por su huella
      codigo_carne  código del carné QR o NFC: se busca el trabajador por la huella de su credencial vigente
      corrige       registro que este corrige (4b); exige observacion
    Devuelve el registro creado.

    La base (agenda.validar_acceso) hace el resto: visita aprobada y en horario, placa, desinfección al galpón,
    visita a en_sitio o salio, y la jornada del trabajador: la abre al entrar y la cierra al salir. Este servicio
    nunca escribe personal.jornada, así no hay dos caminos que la creen.
    """
    codigo_pase = datos.pop('codigo_pase', None)
    codigo_carne = datos.pop('codigo_carne', None)
    if codigo_pase:
        visita = models.Visita.objects.filter(pase_hash=_huella(codigo_pase.strip().upper())).first()
        if not visita:
            raise ValidationError({'codigo_pase': 'El pase no corresponde a ninguna visita'})
        datos['visita'] = visita
        datos.setdefault('metodo', 'pase_qr')
    if codigo_carne:
        credencial = CredencialTrabajo.objects.filter(codigo_hash=_huella(codigo_carne.strip()), revocada_en__isnull=True).first()
        if not credencial:
            raise ValidationError({'codigo_carne': 'Carné desconocido o revocado'})
        datos['empleado_id'] = credencial.empleado_id
        datos.setdefault('metodo', f'carne_{credencial.tipo}')
    datos.setdefault('metodo', 'lectura_placa' if datos.get('placa') and not datos.get('nombre') else 'manual')
    if datos.get('corrige') and not datos.get('observacion'):
        raise ValidationError({'observacion': 'Una corrección dice qué se corrige'})
    return models.RegistroAcceso.objects.create(**datos)


def _huella(codigo):
    """Huella SHA-256 con que la base guarda los códigos de pases y carnés."""
    return hashlib.sha256(codigo.encode()).hexdigest()


def agd_05_consultar_quien_esta_finca(*, usuario, **datos):
    """AGD-05 · Consultar quién está en la finca

    Actores: Portería, Administrador; secundarios: Pasarela IoT local
    Fase 2
    Tablas: agenda.registro_acceso
    Reglas en la base: agenda.v_en_sitio
    Endpoints: GET /api/v1/agenda/en-sitio/
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-05:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.v_en_sitio
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-05: por construir')


def agd_06_consultar_agenda_dia(*, usuario, **datos):
    """AGD-06 · Consultar la agenda del día

    Actores: Encargado de finca, Portería
    Fase 2
    Tablas: agenda.cita, agenda.visita, personal.turno
    Reglas en la base: agenda.v_agenda_dia
    Endpoints: GET /api/v1/agenda/dia/?fecha=
    Requerimientos: RQ-39

    Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).
    """
    # Por construir. Pasos sugeridos para AGD-06:
    # 1. with transaction.atomic():
    # 3. Llamar a la base: agenda.v_agenda_dia
    # 4. publicar('agenda.<hecho>', '<esquema.tabla>', id, {...}) si otros módulos deben enterarse
    # 5. Devolver el resultado para la respuesta
    raise NotImplementedError('AGD-06: por construir')
