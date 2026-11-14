"""Registro del paquete «guayacan» como app de Django (necesario para que Django encuentre sus tareas y pruebas)."""
from django.apps import AppConfig


class GuayacanConfig(AppConfig):
    name = 'guayacan'                     # ruta del paquete: backend/guayacan
    verbose_name = 'Núcleo transversal'   # nombre visible
