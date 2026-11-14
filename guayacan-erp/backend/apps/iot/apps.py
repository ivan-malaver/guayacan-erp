"""Registro de la app «iot» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'iot.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class IotConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/iot
    name = 'apps.iot'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'iot.Modelo'
    label = 'iot'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Red local de la finca: dispositivos, sensores, actuadores, reglas, seguridad perimetral y cámaras (fase 4, con diseño listo desde ya)'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
