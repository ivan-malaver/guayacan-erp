"""Rutas transversales bajo /api/v1/: autenticación, finca, sincronización, consultas públicas y webhook de pagos.

«Transversal» = no pertenece a una sola app. Estas rutas se cargan ANTES que las de las apps (ver
config/urls.py); por eso /api/v1/nucleo/mis-fincas/ se resuelve aquí y no en apps/nucleo/urls.py.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .autenticacion import Ingreso, MisFincas
from .sincronizacion import SincronizarLote
from .vistas import PorConstruir, PorConstruirPublico

urlpatterns = [
    # SEG-01 · Iniciar sesión: recibe correo y contraseña y devuelve los tokens de acceso y de refresco
    path('auth/token/', Ingreso.as_view(), name='auth-token'),
    # Renueva el token de acceso (dura 30 minutos) con el de refresco (dura 14 días), sin pedir la contraseña
    path('auth/token/refrescar/', TokenRefreshView.as_view(), name='auth-refrescar'),
    # SEG-01 y SEG-02 · Doble factor y recuperación de contraseña (por construir: responden 501)
    path('auth/doble-factor/verificar/', PorConstruir.as_view(caso_de_uso='SEG-01', metodo='POST'), name='seg-01-verificar'),
    path('auth/doble-factor/inscribir/', PorConstruir.as_view(caso_de_uso='SEG-02', metodo='POST'), name='seg-02-inscribir'),
    path('auth/recuperar/', PorConstruirPublico.as_view(caso_de_uso='SEG-02', metodo='POST'), name='seg-02-recuperar'),
    # NUC-03 · Fincas del usuario, para el selector de finca de la pantalla
    path('nucleo/mis-fincas/', MisFincas.as_view(), name='nuc-03-mis-fincas'),
    # NUC-05 · Sube los registros capturados sin conexión en la app de campo
    path('sincronizacion/lote/', SincronizarLote.as_view(), name='nuc-05-sincronizar'),
    # Públicas (sin sesión): resuelven el código con una función de la base y nunca exponen otras fincas
    path('publico/trazabilidad/<str:codigo>/', PorConstruirPublico.as_view(caso_de_uso='VTA-11', metodo='GET'), name='vta-11-trazabilidad'),
    path('publico/certificados/<str:codigo>/', PorConstruirPublico.as_view(caso_de_uso='FOR-05', metodo='GET'), name='for-05-certificado'),
    # Webhook de la pasarela de pagos: al construirse debe validar la firma antes de tocar la base
    path('pagos/webhook/', PorConstruirPublico.as_view(caso_de_uso='VTA-07', metodo='POST'), name='vta-07-webhook'),
]
