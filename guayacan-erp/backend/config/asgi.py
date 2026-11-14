"""Punto de entrada ASGI (servidores asíncronos como uvicorn o daphne).

Hoy GuayacanERP se sirve con gunicorn por WSGI (ver wsgi.py); este archivo queda listo por si en el futuro se
usan conexiones en tiempo real. Por defecto carga la configuración de producción.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
application = get_asgi_application()
