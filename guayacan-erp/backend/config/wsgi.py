"""Punto de entrada WSGI: lo usa gunicorn en producción (ver backend/Dockerfile).

WSGI es el estándar con que un servidor web habla con una aplicación Python. Por defecto carga la
configuración de producción (config/settings/prod.py).
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
application = get_wsgi_application()
