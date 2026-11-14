"""Registro de la app «comercial» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'comercial.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class ComercialConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/comercial
    name = 'apps.comercial'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'comercial.Modelo'
    label = 'comercial'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Precios con vigencia, propuestas de precio, pedidos, facturas, pagos y entregas'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
