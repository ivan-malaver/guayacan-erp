"""Registro de la app «seguridad» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'seguridad.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class SeguridadConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/seguridad
    name = 'apps.seguridad'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'seguridad.Modelo'
    label = 'seguridad'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Doble factor, sesiones, intentos de acceso, detector de ataques, señuelos, bloqueos, alertas, incidentes, pruebas y copias de seguridad'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
