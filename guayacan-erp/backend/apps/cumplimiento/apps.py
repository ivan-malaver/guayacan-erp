"""Registro de la app «cumplimiento» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'cumplimiento.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class CumplimientoConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/cumplimiento
    name = 'apps.cumplimiento'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'cumplimiento.Modelo'
    label = 'cumplimiento'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Normas (granja avícola biosegura, BPA, GLOBALG.A.P.), requisitos, expediente, evidencias, auditorías y acciones correctivas'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
