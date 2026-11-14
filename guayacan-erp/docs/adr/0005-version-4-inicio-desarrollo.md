# ADR 0005 · Versión 4 del modelo: base para iniciar el desarrollo

- Estado: aceptado
- Fecha: 2026-10-26
- Reemplaza: la propuesta v3 (aplicada aquí) · Relacionado: ADR 0002, 0003, 0004, `docs/arquitectura/patrones-de-diseno.md`

## Contexto

La versión 2 del modelo (90 tablas, 36 pruebas) quedó probada. Después se evaluaron dos documentos de recomendaciones
externas (ADR 0004 y el informe ejecutivo del 26-oct-2026): cadena de frío, retiro de lotes, cartera, trueque,
seguridad perimetral, cámaras, contenido audiovisual y tendencias como cámaras térmicas, reconocimiento facial,
gemelo digital y blockchain. La familia decidió:

| Decisión | Respuesta |
| --- | --- |
| Cadena de frío | Dejar listo en la finca y en el transporte |
| Venta a crédito | Dejar lista y apagada |
| Trueque (permuta) | Dejar listo y apagado |
| Funciones que esperan equipos costosos | No se posponen: se diseñan ahora y se encienden al comprar el equipo |
| Versión de PostgreSQL de producción | PostgreSQL 18 |

## Decisión

1. **Funciones por finca (feature flags).** Toda función que espera una decisión o un equipo se construye completa y
   se enciende con `nucleo.funcionalidad`. Si está apagada, la regla de la base rechaza la operación con un mensaje claro.
2. **Puertos listos para el equipo futuro** (arquitectura hexagonal):

   | Puerto | Hoy | Al comprar el equipo |
   | --- | --- | --- |
   | `DetectorPresencia` | Sensores PIR y magnéticos | Cámara térmica |
   | `VerificadorIdentidad` | PIN o tarjeta RFID | Rostro, solo con autorización expresa de biometría (Ley 1581) y siempre con alternativa |
   | `MapaFinca` (estado en GeoJSON) | Mapa 2D con las zonas PostGIS | Gemelo digital 3D (`zona.modelo_3d_url`) |
   | `RegistroExterno` | Cadena de huellas SHA-256 en PostgreSQL | Anclaje en una red blockchain |

3. **Modelo v4:** 119 tablas en 13 esquemas (nuevo esquema `ambiental`), 1.396 campos, 103 tablas por finca con
   seguridad por filas, 22 con captura sin conexión, 49 auditadas. Auditoría y lecturas IoT particionadas por mes.
4. **Reglas nuevas en la base:** especificación única "se puede vender", bloqueo de lotes con decisión humana,
   excursiones de temperatura, retiro de lotes, cadena de huellas, clasificación del huevo por peso, cartera con cupo
   y mora, permuta con dos documentos, pedidos recurrentes, consentimiento de imagen en piezas audiovisuales,
   retención de clips, estados de la alarma, cerraduras que abren sin energía en pasos de personas y credenciales
   biométricas condicionadas.
5. **Pruebas:** 90 pruebas automáticas (36 de la v2 adaptadas y 54 nuevas), todas aprobadas con el rol de la API.

## Correcciones a las recomendaciones

| Recomendación | Corrección |
| --- | --- |
| Cerraduras que se cierran solas al irse la luz | Solo en bodegas; en pasos de personas deben abrir sin energía. La base lo exige |
| Transcribir el audio de las cámaras de seguridad | No se adopta: grabar conversaciones de trabajadores sin aviso es un riesgo legal alto |
| Event sourcing para inventario y videos | No se adopta: el kardex, la auditoría y los eventos de seguridad ya son de solo inserción |
| Stripe | Solo pasarelas que operan en Colombia: Wompi, Mercado Pago, ePayco, PayU |

## Consecuencias

- El desarrollo arranca con la "Ruta manual" del mapa de APIs v4, BLOQUE 1: proyecto Django, app `nucleo` y finca de práctica.
- Las pruebas corrieron en PostgreSQL 16 con PostGIS y pgvector sustituidos por tipos simples (no estaban disponibles en
  el entorno de verificación). La primera tarea del BLOQUE 1 es correr `pruebas_reglas_v4.sql` en el contenedor
  PostgreSQL 18 con PostGIS y pgvector reales (`docker/postgres/Dockerfile`).
- Quedan por validar con la familia: rangos de peso del huevo (NTC 1240 vigente), temperaturas de la nevera
  (supuesto 1 a 8 °C), vida útil de los productos y factores de emisión con fuente oficial.
