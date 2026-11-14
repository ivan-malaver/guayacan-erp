# Imagen del Servicio de agentes y canales (FastAPI). La construye docker-compose.yml (perfil "app").
FROM python:3.12-slim
# No escribir archivos .pyc y mostrar los registros de inmediato
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# Dependencias primero (Docker reutiliza esta capa si solo cambia el código)
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir -e .
# El programa no corre como administrador (root) dentro del contenedor
RUN useradd --create-home guayacan
USER guayacan
EXPOSE 8100
# uvicorn es el servidor de aplicaciones FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
