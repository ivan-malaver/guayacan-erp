"""Paquete de configuración del proyecto Django (settings, rutas principales, Celery, WSGI y ASGI).

Se importa Celery aquí para que la aplicación de tareas se cargue junto con Django y los decoradores
@shared_task de guayacan/tareas.py queden registrados en ella.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
