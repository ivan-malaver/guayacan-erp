"""Registro de la app «nomina» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'nomina.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class NominaConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/nomina
    name = 'apps.nomina'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'nomina.Modelo'
    label = 'nomina'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Conceptos, periodos, novedades, liquidación, prestaciones, PILA, nómina electrónica (apagada) y pagos con doble aprobación'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
