"""Registro de la app «personal» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'personal.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class PersonalConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/personal
    name = 'apps.personal'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'personal.Modelo'
    label = 'personal'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Tareas, plan de labores, cuadrillas, turnos, ausencias (sin diagnósticos), matriz de responsabilidades, equipos asignados, carné QR o NFC y jornada'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
