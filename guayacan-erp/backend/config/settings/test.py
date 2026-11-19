"""Configuración de pruebas (pytest la usa por pyproject.toml).

Las pruebas usan una base ya cargada con esquema_postgresql.sql y datos_iniciales.sql: Django no crea tablas.
Ejecute pytest contra una base recién cargada (ver conftest.py e INSTALAR.md).
"""
import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'solo-para-pruebas')
os.environ.setdefault('POSTGRES_API_CLAVE', 'cambiar_esta_clave')
os.environ.setdefault('PASARELA_SECRETO', 'secreto-de-pruebas')

from .base import *  # noqa: E402,F403

DEBUG = False
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']  # rápido e inseguro: SOLO en pruebas
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []  # noqa: F405  sin límite de peticiones en las pruebas
