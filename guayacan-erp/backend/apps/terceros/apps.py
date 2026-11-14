"""Registro de la app «terceros» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'terceros.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class TercerosConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/terceros
    name = 'apps.terceros'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'terceros.Modelo'
    label = 'terceros'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Personas y empresas con las que se relaciona la finca: clientes, proveedores, empleados y su consentimiento de datos'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
