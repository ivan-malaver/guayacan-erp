"""Registro de la app «riego» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'riego.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class RiegoConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/riego
    name = 'apps.riego'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'riego.Modelo'
    label = 'riego'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Fuentes de agua, tanques, sistemas de riego, válvulas y eventos de riego (manual hoy, automático en la fase IoT)'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
