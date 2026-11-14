"""Configuración de producción: HTTPS obligatorio detrás de Nginx; todos los secretos vienen del entorno."""
from .base import *  # noqa: F403

DEBUG = False
# Nginx recibe HTTPS y reenvía a Django por HTTP; esta cabecera le dice a Django que la petición original era segura
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True             # toda petición HTTP se redirige a HTTPS
SECURE_HSTS_SECONDS = 31536000         # el navegador recordará usar solo HTTPS durante un año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True     # el navegador no adivina tipos de archivo (evita ataques)
SESSION_COOKIE_SECURE = True           # cookies solo por HTTPS
CSRF_COOKIE_SECURE = True
# Conexión cifrada con la base de datos
DATABASES['default']['OPTIONS']['sslmode'] = entorno('POSTGRES_SSLMODE', 'require')  # noqa: F405
