"""Registro de la app «ia» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'ia.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class IaConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/ia
    name = 'apps.ia'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'ia.Modelo'
    label = 'ia'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Agentes, herramientas, aprobaciones, base de conocimiento, recomendaciones, evaluaciones y consumo de IA'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
