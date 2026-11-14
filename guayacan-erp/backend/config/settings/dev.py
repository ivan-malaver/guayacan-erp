"""Configuración de desarrollo (la que usa manage.py por defecto).

DEBUG encendido para ver los errores en detalle. Si no hay .env, pone claves de prueba para que el proyecto
arranque; esas claves NUNCA deben usarse en producción.
"""
import os

# setdefault solo asigna si la variable no existe (no pisa lo que venga del .env)
os.environ.setdefault('DJANGO_SECRET_KEY', 'solo-para-desarrollo-cambiar')
os.environ.setdefault('POSTGRES_API_CLAVE', 'cambiar_esta_clave')

from .base import *  # noqa: E402,F403  (trae toda la configuración común)

DEBUG = True
ALLOWED_HOSTS = ['*']  # en su PC se acepta cualquier nombre de servidor
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405  sin límite de peticiones mientras desarrolla
