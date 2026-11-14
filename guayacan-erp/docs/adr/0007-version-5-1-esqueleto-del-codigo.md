# ADR 0007 · Versión 5.1: documento técnico y esqueleto del código

Fecha: 29 de octubre de 2026 · Estado: aceptada

## Contexto

El modelo v5 (25 esquemas, 246 tablas, 305 pruebas de reglas) está cerrado. Falta que un equipo pueda empezar a
construir sin redescubrir la arquitectura ni reinterpretar los requerimientos.

## Decisiones

1. **La arquitectura v5 reemplaza al documento de requerimientos v1.0** donde difieren: Angular PWA en lugar de React
   o Vue, PostgreSQL 18 en lugar de 15, tablas particionadas en lugar de InfluxDB. Los RF y RNF siguen vigentes.
2. **Modelos de Django `managed=False`, generados desde `modelo.py`.** La base se crea con `esquema_postgresql.sql`;
   Django no migra tablas de negocio. Solo `contenttypes` y `auth` se migran, en el esquema `django`, con la conexión admin.
3. **La transacción de cada petición la abre `ContextoFincaMiddleware`**, no `ATOMIC_REQUESTS`, porque
   `set_config(..., true)` debe correr dentro de la misma transacción que la vista.
4. **Sin GeoDjango.** Las dos columnas PostGIS usan un campo propio (`guayacan.db.Geometria`) para no exigir GDAL en
   Windows; las consultas espaciales se hacen en SQL.
5. **CRUD sin borrado por defecto** (`VistaModelo`). Lo que se borra se decide caso a caso.
6. **Acciones declaradas antes de construirse**: cada endpoint de caso de uso existe desde el día uno y responde 501
   con su ID, así OpenAPI, el frontend y las pruebas de contrato pueden avanzar en paralelo.
7. **Un solo catálogo** (`docs/uml/fuentes/catalogo.py`) genera diagramas de casos de uso, apps, rutas de Angular y
   la trazabilidad en Excel.

## Consecuencias

- Cambiar una tabla exige regenerar `models.py`; el generador no toca `services.py` ni las vistas ya escritas.
- Las versiones de dependencias son mínimas: la primera instalación debe fijarlas (`requirements.lock`, `package-lock.json`).
- El esqueleto no se pudo instalar ni ejecutar donde se generó (sin acceso a PyPI ni npm); la primera corrida de la CI
  lo valida. El SQL que usa (contexto, ingreso, tareas programadas) sí se probó como `guayacan_api` en PostgreSQL 16.
