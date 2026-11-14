"""Inicio de sesión (caso de uso SEG-01): entrega tokens JWT, pasando por el detector de ataques de la base.

CÓMO FUNCIONA
1. El frontend envía correo y contraseña a POST /api/v1/auth/token/.
2. Django comprueba la contraseña (cifrada con Argon2) con authenticate().
3. Cada intento, bueno o malo, se registra con la función de la base seguridad.registrar_intento(). La base
   decide si permite el ingreso o si bloquea la IP o la cuenta (fuerza bruta, relleno de credenciales, señuelos).
4. Si se permite, se devuelven dos tokens JWT:
   - acceso: dura 30 minutos y viaja en la cabecera Authorization de cada petición.
   - refresco: dura 14 días y sirve para pedir un acceso nuevo sin volver a escribir la contraseña.
   Ambos llevan la finca por defecto (predio_id) y si el usuario es superusuario (su).

POR QUÉ conservar_transaccion
Una respuesta 401 haría que contexto.py deshiciera la transacción, y el intento fallido se perdería; entonces
el detector nunca bloquearía a un atacante. Por eso esa respuesta marca conservar_transaccion = True.

QUÉ ES UN JWT
Un texto firmado por el servidor que dice «este es el usuario X». El servidor verifica la firma en cada
petición sin consultar una tabla de sesiones.
"""
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import connection
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Resultado que devuelve seguridad.registrar_intento() -> mensaje para la persona.
# Varios dicen lo mismo a propósito: no se le revela al atacante si acertó el correo o cayó en un señuelo.
MENSAJES = {
    'ip_bloqueada': 'Demasiados intentos desde esta red. Intente más tarde.',
    'ip_bloqueada_ahora': 'Demasiados intentos desde esta red. Intente más tarde.',
    'cuenta_bloqueada': 'La cuenta está bloqueada temporalmente.',
    'cuenta_bloqueada_ahora': 'La cuenta está bloqueada temporalmente.',
    'senuelo': 'Correo o contraseña incorrectos.',
    'rechazado': 'Correo o contraseña incorrectos.',
}


def ip_de(request):
    """IP de quien hace la petición. Detrás de Nginx la IP real llega en X-Forwarded-For (la primera de la lista)."""
    reenviada = request.META.get('HTTP_X_FORWARDED_FOR')
    return (reenviada.split(',')[0].strip() if reenviada else request.META.get('REMOTE_ADDR')) or '0.0.0.0'


def registrar_intento(correo, ip, exito, motivo, agente_usuario):
    """Registra el intento en la base y devuelve su decisión: 'permitido' o el motivo del rechazo."""
    with connection.cursor() as cur:
        # agente_usuario = navegador o app que hizo la petición (se recorta a 300 caracteres)
        cur.execute('select seguridad.registrar_intento(%s, %s::inet, %s, %s, %s)', [correo, ip, exito, motivo, agente_usuario[:300]])
        return cur.fetchone()[0]


def fincas_de(usuario_id):
    """Fincas a las que puede entrar el usuario, con su rol en cada una."""
    with connection.cursor() as cur:
        cur.execute('select predio_id, nombre, rol from nucleo.predios_del_usuario(%s)', [usuario_id])
        return [{'predio_id': p, 'nombre': n, 'rol': r} for p, n, r in cur.fetchall()]


def requiere_doble_factor(usuario_id):
    """True si el rol del usuario exige doble factor (administrador y contador)."""
    with connection.cursor() as cur:
        cur.execute('select seguridad.requiere_doble_factor(%s)', [usuario_id])
        return bool(cur.fetchone()[0])


def emitir_tokens(usuario, predio_id):
    """Crea el par de tokens JWT e incluye en ambos la finca por defecto y si es superusuario."""
    refresco = RefreshToken.for_user(usuario)
    refresco['predio_id'] = predio_id
    refresco['su'] = usuario.es_superusuario
    acceso = refresco.access_token
    acceso['predio_id'] = predio_id
    acceso['su'] = usuario.es_superusuario
    return {'acceso': str(acceso), 'refresco': str(refresco)}


class IngresoSerializer(serializers.Serializer):
    """Valida el cuerpo de la petición de ingreso."""
    correo = serializers.EmailField()
    contrasena = serializers.CharField(trim_whitespace=False)  # no se quitan espacios: podrían ser parte de la clave
    predio = serializers.IntegerField(required=False)          # opcional: finca con la que quiere entrar


class Ingreso(APIView):
    """POST /api/v1/auth/token/  ·  inicio de sesión."""

    permission_classes = [AllowAny]  # cualquiera puede intentar ingresar
    authentication_classes = []      # aquí todavía no hay token que leer

    def post(self, request):
        datos = IngresoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)  # si faltan datos responde 400 automáticamente
        correo = datos.validated_data['correo'].lower()
        usuario = authenticate(request, correo=correo, password=datos.validated_data['contrasena'])
        exito = usuario is not None and usuario.is_active
        # La base decide el motivo del fallo (por eso se envía None) y si hay que bloquear
        resultado = registrar_intento(correo, ip_de(request), exito, None,
                                      request.META.get('HTTP_USER_AGENT', ''))
        if resultado != 'permitido':
            respuesta = Response({'codigo': resultado, 'detalle': MENSAJES.get(resultado, 'No se pudo iniciar sesión.')},
                                 status=status.HTTP_401_UNAUTHORIZED)
            respuesta.conservar_transaccion = True  # que el intento fallido quede guardado (ver docstring)
            return respuesta
        # El doble factor es obligatorio en producción; en desarrollo (DEBUG) se puede omitir
        if requiere_doble_factor(usuario.pk) and getattr(settings, 'GUAYACAN_DOBLE_FACTOR_OBLIGATORIO', not settings.DEBUG):
            # SEG-01, flujo 3: falta construir el desafío TOTP (/auth/doble-factor/verificar/)
            return Response({'codigo': 'doble_factor_requerido', 'caso_de_uso': 'SEG-01'}, status=status.HTTP_501_NOT_IMPLEMENTED)
        fincas = fincas_de(usuario.pk)
        pedido = datos.validated_data.get('predio')
        ids = [f['predio_id'] for f in fincas]
        if pedido is not None and pedido not in ids and not usuario.es_superusuario:
            return Response({'codigo': 'finca_no_permitida'}, status=status.HTTP_403_FORBIDDEN)
        # Finca por defecto: la pedida o, si no pidió ninguna, la primera de su lista
        predio = pedido if pedido is not None else (ids[0] if ids else None)
        with connection.cursor() as cur:
            cur.execute('update nucleo.usuario set ultimo_ingreso = now() where id = %s', [usuario.pk])
        return Response({**emitir_tokens(usuario, predio), 'predio_id': predio, 'fincas': fincas})


class MisFincas(APIView):
    """GET /api/v1/nucleo/mis-fincas/  ·  NUC-03: fincas del usuario para el selector de finca (cabecera X-Predio)."""

    def get(self, request):
        return Response(fincas_de(request.user.pk))
