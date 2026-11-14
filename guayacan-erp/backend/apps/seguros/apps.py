"""Registro de la app «seguros» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'seguros.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class SegurosConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/seguros
    name = 'apps.seguros'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'seguros.Modelo'
    label = 'seguros'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Pólizas, bienes asegurados, índices de seguros paramétricos y avisos de siniestro con evidencia'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
