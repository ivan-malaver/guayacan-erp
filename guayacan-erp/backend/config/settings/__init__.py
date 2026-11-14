"""Configuración por entorno:

  base.py   lo común a todos los entornos
  dev.py    desarrollo en su PC (DEBUG encendido) — es la que usa manage.py por defecto
  test.py   pruebas automáticas (pytest)
  prod.py   producción (HTTPS obligatorio)

Para elegir otra:  set DJANGO_SETTINGS_MODULE=config.settings.prod   (Windows)
                   export DJANGO_SETTINGS_MODULE=config.settings.prod (Linux/Mac)
"""
