"""Registro de la app «redes» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'redes.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class RedesConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/redes
    name = 'apps.redes'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'redes.Modelo'
    label = 'redes'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Cuentas de redes sociales y publicaciones con su flujo de aprobación'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
