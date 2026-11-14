"""Permisos por acción, consultados a la base con nucleo.tiene_permiso(usuario, código).

Uso en una vista:
    from rest_framework.permissions import IsAuthenticated
    from guayacan.permisos import requiere, SoloPersonas

    class AprobarTarea(APIView):
        permission_classes = [IsAuthenticated, SoloPersonas, requiere('personal.aprobar_tarea')]

Por qué existe si la base ya protege: la base vuelve a verificar lo crítico (nucleo.exigir_persona y las
reglas). Revisar antes en la API solo evita llamadas inútiles y da un mensaje 403 más claro.
"""
from django.db import connection
from rest_framework.permissions import BasePermission


def tiene_permiso(usuario_id, codigo):
    """Pregunta a la base si el usuario tiene el permiso en la finca de la sesión."""
    with connection.cursor() as cur:
        cur.execute('select nucleo.tiene_permiso(%s, %s)', [usuario_id, codigo])
        return bool(cur.fetchone()[0])


def requiere(codigo):
    """Fábrica de clases de permiso: requiere('personal.aprobar_tarea') devuelve una clase lista para usar.

    Se crea una clase nueva por código porque Django REST Framework espera clases (no objetos) en
    permission_classes.
    """
    class Permiso(BasePermission):
        message = f'Necesita el permiso {codigo}'  # texto de la respuesta 403

        def has_permission(self, request, view):
            return bool(request.user and request.user.is_authenticated and tiene_permiso(request.user.pk, codigo))

    # Nombre legible para depurar, p. ej. Requiere_personal_aprobar_tarea
    Permiso.__name__ = f'Requiere_{codigo.replace(".", "_")}'
    return Permiso


class SoloPersonas(BasePermission):
    """Bloquea en la API lo que un agente de IA nunca puede hacer (aprobar, pagar, publicar, decidir).

    El contexto de la petición (guayacan/contexto.py) trae agente_id cuando el token es de un agente.
    La base también lo impide con app.agente_id; esta es una primera barrera.
    """
    message = 'Un agente de IA no puede hacer esto: lo hace una persona'

    def has_permission(self, request, view):
        ctx = getattr(request, 'contexto_finca', None)
        return ctx is None or ctx.agente_id is None
