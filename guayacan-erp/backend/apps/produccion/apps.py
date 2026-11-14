"""Registro de la app «produccion» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'produccion.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class ProduccionConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/produccion
    name = 'apps.produccion'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'produccion.Modelo'
    label = 'produccion'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Producción animal (aves, ovinos, caprinos, peces, abejas, lombrices) y agrícola (siembras, labores, cosechas, suelo)'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
