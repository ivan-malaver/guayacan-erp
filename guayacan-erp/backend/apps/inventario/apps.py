"""Registro de la app «inventario» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'inventario.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class InventarioConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/inventario
    name = 'apps.inventario'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'inventario.Modelo'
    label = 'inventario'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Catálogo de productos, bodegas, lotes de inventario y kardex de movimientos'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
