"""Registro de la app «agenda» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'agenda.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class AgendaConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/agenda
    name = 'apps.agenda'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'agenda.Modelo'
    label = 'agenda'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Recursos agendables (cabañas, salón, vehículos, equipos), calendario sin cruces, visitas programadas e ingresos y salidas de personas y vehículos'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
