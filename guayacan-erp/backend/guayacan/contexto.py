"""ContextoFincaMiddleware: la pieza que hace funcionar la seguridad por filas (RLS).

QUÉ ES UN MIDDLEWARE
Código que Django ejecuta en TODAS las peticiones, antes y después de la vista. Este se registra en
config/settings/base.py (MIDDLEWARE).

QUÉ HACE, EN CADA PETICIÓN A /api/
1. Lee el token JWT (si viene) para saber quién es el usuario y, si actúa un agente de IA, cuál.
2. Toma la finca de la cabecera X-Predio o, si no viene, la finca por defecto guardada en el token.
3. Verifica con la función de la base nucleo.predios_del_usuario() que el usuario pertenezca a esa finca
   (el superusuario entra a cualquiera).
4. Abre una transacción y fija tres variables de sesión de PostgreSQL con set_config(..., true):
   app.predio_id, app.usuario_id y app.agente_id. Con «true» valen solo dentro de esa transacción; así una
   conexión reutilizada nunca arrastra la finca de la petición anterior.
5. Si la respuesta es un error (código 400 o mayor), deshace la transacción, salvo que la vista marque
   respuesta.conservar_transaccion (p. ej. el intento fallido de inicio de sesión debe quedar registrado).

POR QUÉ ASÍ
Las políticas de seguridad por filas de PostgreSQL leen app.predio_id: cada consulta solo ve las filas de esa
finca, aunque el código de la vista tenga un error. Las vistas no fijan nada: cuando corren, la base ya sabe
quién es y en qué finca está.
"""
import logging

from django.conf import settings
from django.db import connection, transaction
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

log = logging.getLogger(__name__)
# Django guarda las cabeceras HTTP en request.META con el prefijo HTTP_ y en mayúsculas: X-Predio -> HTTP_X_PREDIO
CABECERA_PREDIO = 'HTTP_X_PREDIO'


class Contexto:
    """Datos de quién hace la petición. __slots__ fija los atributos permitidos (ocupa menos memoria y evita errores de escritura)."""

    __slots__ = ('usuario_id', 'agente_id', 'predio_id', 'es_superusuario')

    def __init__(self, usuario_id=None, agente_id=None, predio_id=None, es_superusuario=False):
        self.usuario_id, self.agente_id, self.predio_id, self.es_superusuario = usuario_id, agente_id, predio_id, es_superusuario


def _leer_token(request):
    """Devuelve el token JWT ya validado (firma y vencimiento) o None.

    Un token inválido no se rechaza aquí: se deja seguir y Django REST Framework responderá 401 en la vista.
    Así este middleware no duplica la lógica de autenticación.
    """
    jwt = JWTAuthentication()
    cabecera = jwt.get_header(request)          # la cabecera Authorization completa
    if cabecera is None:
        return None
    crudo = jwt.get_raw_token(cabecera)         # solo el token, sin la palabra "Bearer"
    if crudo is None:
        return None
    try:
        return jwt.get_validated_token(crudo)   # verifica firma y fecha de vencimiento
    except (InvalidToken, TokenError):
        return None


def _entero(valor):
    """Convierte a entero; si viene vacío o no es un número devuelve None en vez de fallar."""
    try:
        return int(valor) if valor not in (None, '') else None
    except (TypeError, ValueError):
        return None


def resolver_contexto(request):
    """Arma el Contexto de la petición a partir del token y de la cabecera X-Predio."""
    token = _leer_token(request)
    if token is None:
        return Contexto()  # petición anónima: sin usuario ni finca
    ctx = Contexto(usuario_id=_entero(token.get('usuario_id')), agente_id=_entero(token.get('agente_id')),
                   es_superusuario=bool(token.get('su', False)))
    pedido = request.META.get(CABECERA_PREDIO)
    # La finca elegida en pantalla (X-Predio) tiene prioridad sobre la finca por defecto del token
    ctx.predio_id = _entero(pedido) if pedido else _entero(token.get('predio_id'))
    return ctx


def pertenece(ctx):
    """True si el usuario puede entrar a la finca pedida. Se consulta a la base, que es la dueña de los permisos."""
    if ctx.predio_id is None or ctx.usuario_id is None:
        return True  # sin finca: la RLS no deja ver nada; las vistas que la necesitan responderán vacío o 403
    if ctx.es_superusuario:
        return True
    with connection.cursor() as cur:
        # %s son parámetros: el conector los envía aparte y así no hay inyección de SQL
        cur.execute('select exists (select 1 from nucleo.predios_del_usuario(%s) where predio_id = %s)', [ctx.usuario_id, ctx.predio_id])
        return cur.fetchone()[0]


def fijar(ctx):
    """Escribe la finca, el usuario y el agente en la sesión de PostgreSQL, solo para la transacción actual."""
    with connection.cursor() as cur:
        cur.execute(
            "select set_config('app.predio_id', %s, true), set_config('app.usuario_id', %s, true), set_config('app.agente_id', %s, true)",
            # set_config solo acepta texto: None se envía como cadena vacía
            ['' if ctx.predio_id is None else str(ctx.predio_id), '' if ctx.usuario_id is None else str(ctx.usuario_id),
             '' if ctx.agente_id is None else str(ctx.agente_id)])


class ContextoFincaMiddleware:
    """Middleware registrado en settings.MIDDLEWARE. Django crea una instancia y la llama en cada petición."""

    def __init__(self, get_response):
        # get_response es «el resto de Django»: los demás middlewares y la vista
        self.get_response = get_response
        # Rutas que pasan por aquí (por defecto todas las que empiezan por /api/)
        self.prefijos = tuple(getattr(settings, 'GUAYACAN_PREFIJOS_API', ('/api/',)))

    def __call__(self, request):
        # Fuera de la API (p. ej. archivos estáticos) no hace nada
        if not request.path.startswith(self.prefijos):
            return self.get_response(request)
        ctx = resolver_contexto(request)
        request.contexto_finca = ctx  # queda disponible para las vistas y los permisos (guayacan/permisos.py)
        # Una transacción por petición: o se guarda todo lo que hizo la vista, o nada
        with transaction.atomic():
            if not pertenece(ctx):
                return JsonResponse({'codigo': 'finca_no_permitida', 'detalle': 'El usuario no tiene acceso a esa finca'}, status=403)
            fijar(ctx)
            respuesta = self.get_response(request)  # aquí corre la vista
            if respuesta.status_code >= 400 and not getattr(respuesta, 'conservar_transaccion', False):
                transaction.set_rollback(True)  # error: se deshace lo que alcanzó a escribir la vista
        return respuesta
