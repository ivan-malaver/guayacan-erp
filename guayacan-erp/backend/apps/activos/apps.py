"""Registro de la app «activos» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'activos.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class ActivosConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/activos
    name = 'apps.activos'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'activos.Modelo'
    label = 'activos'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Hoja de vida de equipos, planes y órdenes de mantenimiento, uso, repuestos y depreciación'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
