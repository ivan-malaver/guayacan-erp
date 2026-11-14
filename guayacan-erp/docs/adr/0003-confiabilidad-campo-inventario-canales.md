# ADR 0003 · Confiabilidad en campo, inventario perecedero, varias fincas y canales

- Estado: propuesto
- Fecha: 2026-10-25
- Complementa: ADR 0002

## Contexto

La finca tiene señal débil y no tiene red eléctrica; sus productos son perecederos; el sistema debe poder
replicarse en otras fincas; y los agentes atenderán WhatsApp, Instagram, Messenger, TikTok y el chat web, cada uno
con reglas propias del proveedor (verificadas el 2026-10-25).

## Decisiones

1. **App de campo PWA sin conexión desde la fase 1** (Angular + service worker + IndexedDB/Dexie). Cada registro
   lleva `id_cliente` (UUIDv7) y se inserta con `ON CONFLICT (id_cliente) DO NOTHING`. El servidor está en la nube.
2. **Riego con red local**: pasarela local con broker MQTT y motor de reglas; nodos ESP32 o PLC con electroválvulas
   normalmente cerradas y tiempo máximo propio; la nube solo supervisa y despliega reglas aprobadas con versión.
3. **Inventario perecedero**: vencimiento y fecha límite de venta estimados por la base; salida FEFO con bloqueo de fila;
   el kardex es la única forma de cambiar existencias; semáforo de venta con precio de liquidación aprobado.
4. **Captura con equipos**: lectores en modo teclado (HID) como estándar; BarcodeDetector/ZXing con cámara;
   básculas por Web Bluetooth o Web Serial (Android, Chrome 137+) o conectadas a la pasarela; registro de verificación
   metrológica de las básculas de venta (SIC).
5. **Varias fincas**: `predio_id` en 76 tablas, seguridad por filas forzada, llaves foráneas compuestas `(predio_id, id)`
   y rol `guayacan_app` sin BYPASSRLS. En MongoDB, `predio_id` en todos los documentos e índices.
6. **Auditoría genérica** por disparador en 36 tablas sensibles (solo campos cambiados, usuario y agente de la sesión).
7. **Contabilidad**: contabilizar exige débitos = créditos (disparador diferido), periodo abierto y deja los
   movimientos inmutables; solo se anula con motivo.
8. **Canales**: reglas por canal en `redes.politica_canal`; `redes.verificar_envio` decide antes de cada envío;
   guardia de dominio del orquestador (`ia.regla_conversacion`) por la política de WhatsApp de enero de 2026;
   escalamientos con plazo según la ventana del canal.

## Consecuencias

- Más lógica en la base de datos: se prueba con `specs/casos-prueba/pruebas_reglas_v2.sql` (36 pruebas) en CI.
- Las vidas útiles iniciales son supuestos; deben validarse con la familia y ajustarse con las mermas reales.
- Las políticas de los canales cambian (WhatsApp cambió precios el 1 de octubre de 2026): revisar `politica_canal`
  cada trimestre y cuando el proveedor avise.
- Producción debe usar PostgreSQL 18 (uuidv7 nativo); la prueba se hizo en PostgreSQL 16 con PostGIS y pgvector
  sustituidos por tipos equivalentes. MongoDB no se probó contra un servidor real.
