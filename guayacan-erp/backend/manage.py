#!/usr/bin/env python
"""Herramienta de línea de comandos de Django para GuayacanERP.

Comandos más usados (desde la carpeta backend, con el venv activo):
    python manage.py check                      revisa que el proyecto esté bien armado
    python manage.py migrate --database=admin   crea las tablas internas de Django (solo la primera vez)
    python manage.py runserver                  arranca la API en http://localhost:8000
    python manage.py shell                      consola de Python con Django cargado
"""
import os
import sys


def main():
    # Si no se indica otra, se usa la configuración de desarrollo
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
