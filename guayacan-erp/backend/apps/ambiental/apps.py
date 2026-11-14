"""Registro de la app «ambiental» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'ambiental.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class AmbientalConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/ambiental
    name = 'apps.ambiental'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'ambiental.Modelo'
    label = 'ambiental'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Mediciones ambientales (energía solar, biogás, compost, agua) y factores de emisión con su fuente'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
