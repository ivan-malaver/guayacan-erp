"""Configuración común de GuayacanERP (la heredan dev.py, test.py y prod.py).

REGLA DE ORO: los valores secretos (claves, contraseñas) salen del entorno, nunca se escriben aquí.
En su PC se guardan en el archivo .env de la raíz del proyecto (copie .env.ejemplo como .env). Ese archivo
está en .gitignore: no se sube a GitHub.
"""
import os
from datetime import timedelta
from pathlib import Path

# Carpeta backend/ (este archivo está en backend/config/settings/, por eso se sube dos niveles con parents[2])
BASE_DIR = Path(__file__).resolve().parents[2]

# Carga el archivo .env de la raíz del proyecto (guayacan-erp/.env) si existe y si python-dotenv está instalado.
# Así, al correr «python manage.py runserver» en su PC, Django encuentra las claves sin configurarlas a mano.
# En Docker las variables ya vienen del docker-compose (env_file), y override=False respeta las que ya existan.
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR.parent / '.env', override=False)
except ImportError:  # sin python-dotenv se usan solo las variables del sistema
    pass


def entorno(nombre, defecto=None, obligatorio=False):
    """Lee una variable de entorno. Si es obligatoria y falta, detiene el arranque con un mensaje claro."""
    valor = os.environ.get(nombre, defecto)
    if obligatorio and not valor:
        raise RuntimeError(f'Falta la variable de entorno {nombre} (ver .env.ejemplo)')
    return valor


# Clave con que Django firma datos (cookies, tokens). Debe ser larga, aleatoria y secreta.
SECRET_KEY = entorno('DJANGO_SECRET_KEY', obligatorio=True)
# DEBUG muestra errores detallados en el navegador: solo en desarrollo (dev.py lo enciende)
DEBUG = False
# Nombres de servidor desde los que se acepta la API (separados por coma en .env)
ALLOWED_HOSTS = [h for h in entorno('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h]

# Una app de Django por esquema de PostgreSQL (25 de la v5 + adopcion del Apéndice A).
# El orden no importa porque los modelos son managed=False (Django no crea tablas).
ESQUEMAS = [
    'nucleo', 'terceros', 'produccion', 'riego', 'inventario', 'comercial', 'compras', 'finanzas', 'ia', 'redes',
    'turismo', 'iot', 'ambiental', 'personal', 'nomina', 'formacion', 'activos', 'documental', 'cumplimiento',
    'seguros', 'seguridad', 'crm', 'estrategia', 'agenda', 'proyectos',
    'adopcion',  # Apéndice A · adopción de árboles y animales
]

# Apps que Django carga al arrancar
INSTALLED_APPS = [
    'django.contrib.contenttypes',  # registro interno de modelos (lo necesita auth)
    'django.contrib.auth',          # usuarios y contraseñas (el modelo de usuario es nucleo.Usuario)
    'django.contrib.staticfiles',   # archivos estáticos (la página de documentación de la API)
    'corsheaders',                  # permite que el frontend (otro puerto u otro dominio) llame a la API
    'rest_framework',               # Django REST Framework: la API
    'drf_spectacular',              # documentación OpenAPI automática
    'guayacan',                     # lo transversal (contexto de finca, errores, sincronización...)
] + [f'apps.{e}' for e in ESQUEMAS]  # las 26 apps de negocio

# Middlewares: código que corre en cada petición, en este orden
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',   # cabeceras de seguridad HTTP
    'corsheaders.middleware.CorsMiddleware',           # respuestas CORS para el frontend
    'django.middleware.common.CommonMiddleware',       # normaliza las rutas (barra final, etc.)
    # Fija la finca, el usuario y el agente de la petición dentro de una transacción (ver guayacan/contexto.py)
    'guayacan.contexto.ContextoFincaMiddleware',
]

ROOT_URLCONF = 'config.urls'                   # mapa de rutas principal
WSGI_APPLICATION = 'config.wsgi.application'   # servidor de producción (gunicorn)
ASGI_APPLICATION = 'config.asgi.application'

# Plantillas HTML: solo las usa la página de documentación de la API
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.request']},
}]

# --------------------------------------------------------------------------------------- base de datos
# Dos conexiones a la misma base:
#  default: con la que trabaja la API. Usuario guayacan_api, miembro del rol guayacan_app: sin superusuario ni
#           BYPASSRLS, así la seguridad por filas SIEMPRE aplica. Lo crea backend/sql/preparar_api.sql.
#  admin:   usuario dueño de la base. Solo para crear las tablas internas de Django (contenttypes, auth) en el
#           esquema «django» con:  python manage.py migrate --database=admin   y para tareas de mantenimiento.
_BASE = {
    'ENGINE': 'django.db.backends.postgresql',
    'HOST': entorno('POSTGRES_HOST', 'localhost'),
    'PORT': entorno('POSTGRES_PORT', '5432'),
    'NAME': entorno('POSTGRES_DB', 'guayacan'),
    # search_path: dónde busca PostgreSQL las tablas sin esquema (las de Django van al esquema «django»)
    'OPTIONS': {'options': '-c search_path=django,public'},
    'CONN_MAX_AGE': 60,  # reutiliza la conexión hasta 60 segundos (más rápido)
    # La transacción de cada petición la abre ContextoFincaMiddleware, no ATOMIC_REQUESTS
    'ATOMIC_REQUESTS': False,
}
DATABASES = {
    'default': {**_BASE, 'USER': entorno('POSTGRES_API_USUARIO', 'guayacan_api'),
                'PASSWORD': entorno('POSTGRES_API_CLAVE', obligatorio=True)},
    'admin': {**_BASE, 'USER': entorno('POSTGRES_ADMIN_USUARIO', 'postgres'),
              'PASSWORD': entorno('POSTGRES_PASSWORD', '')},
}
# Decide qué se puede migrar y con qué conexión (ver guayacan/db.py, clase RutaAdmin)
DATABASE_ROUTERS = ['guayacan.db.RutaAdmin']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------------------- usuarios
AUTH_USER_MODEL = 'nucleo.Usuario'  # el usuario es la tabla nucleo.usuario, no la de Django
PASSWORD_HASHERS = ['django.contrib.auth.hashers.Argon2PasswordHasher']  # cifrado de contraseñas recomendado
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},  # rechaza claves muy comunes
]

# --------------------------------------------------------------------------------------- idioma y zona horaria
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True  # las fechas se guardan con zona horaria (timestamptz)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'  # carpeta donde collectstatic reúne los archivos estáticos (está en .gitignore)

# --------------------------------------------------------------------------------------- API (Django REST Framework)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],  # token JWT
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],  # todo exige sesión salvo lo público
    'DEFAULT_PAGINATION_CLASS': 'guayacan.paginacion.Paginacion',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'guayacan.errores.manejar_error',  # errores de la base -> respuestas en español
    # Límite de peticiones por minuto (frena abusos); en desarrollo y pruebas se apaga
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'anon': '30/min', 'user': '600/min'},
}

# Tokens JWT (ver guayacan/autenticacion.py)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),   # el de acceso vence pronto (menos riesgo si lo roban)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),     # el de refresco permite volver sin escribir la clave
    'ROTATE_REFRESH_TOKENS': True,                    # cada refresco entrega un token de refresco nuevo
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'usuario_id',                    # nombre del dato del usuario dentro del token
    'SIGNING_KEY': entorno('JWT_CLAVE', SECRET_KEY),  # clave de firma (si no hay una propia, la de Django)
}

# Documentación de la API en /api/docs/
SPECTACULAR_SETTINGS = {
    'TITLE': 'GuayacanERP API',
    'DESCRIPTION': 'API del ERP de El Guayacán de los Malaver. Cada endpoint de acción nombra su caso de uso.',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS: direcciones del frontend que pueden llamar a la API desde el navegador
CORS_ALLOWED_ORIGINS = [o for o in entorno('CORS_ORIGENES', 'http://localhost:4200').split(',') if o]
# Cabeceras que el frontend puede enviar (x-predio = finca elegida; x-id-cliente = registro capturado sin conexión)
CORS_ALLOW_HEADERS = ['authorization', 'content-type', 'x-predio', 'x-id-cliente']

# Celery usa Redis como cola de tareas
CELERY_BROKER_URL = entorno('REDIS_URL', 'redis://localhost:6379/0')
CELERY_TIMEZONE = TIME_ZONE

# Rutas que pasan por el contexto de finca (todas las de la API)
GUAYACAN_PREFIJOS_API = ('/api/',)

# Secreto con que la pasarela firma sus avisos (guayacan/pasarela.py). Vacío = se rechaza todo aviso de pago
PASARELA_SECRETO = entorno('PASARELA_SECRETO', '')

# Registro de eventos (logs): se imprimen en la consola; el nivel se cambia con NIVEL_LOG en .env
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'consola': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['consola'], 'level': entorno('NIVEL_LOG', 'INFO')},
}
