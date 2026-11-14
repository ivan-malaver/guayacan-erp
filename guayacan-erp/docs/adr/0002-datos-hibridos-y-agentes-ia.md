# ADR 0002 · Datos híbridos (PostgreSQL + MongoDB) y servicio de agentes de IA

- Estado: propuesto
- Fecha: 2026-10-25
- Reemplaza en parte: ADR 0001 (stack de referencia)

## Contexto

GuayacanERP debe atender clientes por WhatsApp, web y redes con agentes de IA (asesor, guía, vendedor
personalizado, gestor de redes, analista de mercados, analista de negocio, asistente contable), analizar
tendencias y proponer precios, sin perder el control humano sobre dinero, precios ni publicaciones.
El backend y el frontend deben ser independientes y escalables.

## Decisión

1. **Lenguaje**: Python. Núcleo ERP en Django + Django REST Framework (monolito modular).
2. **Servicio de agentes aparte** en FastAPI, con LangGraph para los flujos y LiteLLM como capa de proveedor
   (Claude primero, intercambiable). Los agentes solo actúan mediante herramientas del ERP expuestas por un
   servidor MCP con token de servicio; nunca escriben directo en la base de datos.
3. **Datos híbridos con dueño único**:
   - PostgreSQL (+ PostGIS + pgvector) es la fuente de verdad: dinero, existencias, producción, contabilidad,
     agentes, aprobaciones y base de conocimiento.
   - MongoDB guarda conversaciones, mensajes, perfiles de interés, eventos y métricas de redes, bitácoras de
     agentes, informes de mercado y tendencias. Solo guarda referencias a Postgres.
   - Redis para caché, colas y sesiones; MinIO para archivos; TimescaleDB para sensores (fase 4).
4. **Integración por eventos** con patrón outbox (`nucleo.evento_salida`) publicado por Celery a Redis Streams.
5. **Nombres en español** en tablas, columnas, colecciones y endpoints; significado de cada campo en
   `COMMENT` de la base y en el diccionario generado.
6. **La IA propone, el humano decide**: herramientas de tipo `propuesta` crean `ia.solicitud_aprobacion`;
   los precios se aplican con `comercial.aplicar_propuesta_precio`, que no toca lo vendido ni lo reservado.
7. **Riego**: el modelo arranca con el sistema manual instalado (aspersores, 2 tanques de 2.000 L, válvulas
   manuales) y queda listo para electroválvulas, ESP32/PLC y MQTT en la fase 4.

## Consecuencias

- Más servicios que operar (MongoDB y el servicio de agentes) a cambio de escalar la conversación por separado
  y enseñar ambos mundos SQL y NoSQL.
- Ninguna personalización usa datos de perfiles personales en redes de terceros (Ley 1581 de 2012); solo
  interacciones con las cuentas de la finca, historial de compras y preferencias declaradas con consentimiento.
- CLAUDE.md debe actualizar el "Stack de referencia": agregar FastAPI (servicio de agentes), MongoDB,
  LangGraph/LiteLLM y servidor MCP; cambiar "InfluxDB o TimescaleDB" por TimescaleDB.

## Verificación hecha

- `esquema_postgresql.sql` cargó sin errores en PostgreSQL 16 (75 tablas, 1 vista, 116 llaves foráneas;
  PostGIS y pgvector sustituidos por tipos equivalentes solo para la prueba).
- `datos_iniciales.sql` cargó la situación real de la finca.
- Prueba del flujo de precios: pedido confirmado a $19.500 conservó su precio tras aprobar $21.000;
  un solo precio vigente; auditoría y evento `precio.aplicado` creados; la auditoría rechaza UPDATE.
- `colecciones_mongodb.js` es JavaScript válido; no se ejecutó contra un MongoDB real.
