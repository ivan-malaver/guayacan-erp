# Imagen de base de datos de GuayacanERP (desarrollo, pruebas e integración continua).
# Parte de la imagen oficial de PostGIS (PostgreSQL 18 + PostGIS 3.6, para datos de mapas: lotes, cercas, puntos)
# y le agrega pgvector (búsqueda por significado en la base de conocimiento de los agentes de IA).
FROM postgis/postgis:18-3.6
# Instala pgvector desde los paquetes de PostgreSQL y borra la caché de apt para que la imagen pese menos
RUN apt-get update \
 && apt-get install -y --no-install-recommends postgresql-18-pgvector \
 && rm -rf /var/lib/apt/lists/*
