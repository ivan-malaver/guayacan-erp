# Imagen del núcleo ERP (Django + DRF). La misma imagen corre la API (gunicorn) y Celery (worker y beat):
# docker-compose.yml solo cambia el comando de arranque.
FROM python:3.12-slim
# No escribir archivos .pyc y mostrar los registros de inmediato (sin búfer)
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# Primero las dependencias y luego el código (Docker reutiliza capas si solo cambia el código)
COPY pyproject.toml ./
COPY config ./config
COPY guayacan ./guayacan
COPY apps ./apps
COPY manage.py conftest.py ./
RUN pip install --no-cache-dir -e .[dev]
# Por seguridad el programa no corre como administrador (root) dentro del contenedor
RUN useradd --create-home guayacan
USER guayacan
EXPOSE 8000
# Servidor de producción: 3 procesos atendiendo peticiones; corta las que tarden más de 60 segundos
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
