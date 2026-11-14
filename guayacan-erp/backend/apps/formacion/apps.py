"""Registro de la app «formacion» en Django.

Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
con qué etiqueta corta se nombran sus modelos (p. ej. 'formacion.Modelo') y qué nombre mostrar.
La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
from django.apps import AppConfig


class FormacionConfig(AppConfig):
    # Ruta del paquete Python: la carpeta backend/apps/formacion
    name = 'apps.formacion'
    # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. 'formacion.Modelo'
    label = 'formacion'
    # Nombre en español que muestran las herramientas de Django
    verbose_name = 'Cursos, lecciones, evaluaciones, sesiones presenciales, certificados y habilitaciones que permiten asignar tareas'
    # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
    default_auto_field = 'django.db.models.BigAutoField'
