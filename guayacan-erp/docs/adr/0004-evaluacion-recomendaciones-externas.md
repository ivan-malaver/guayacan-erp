# ADR 0004 · Evaluación de las recomendaciones externas (cuadro "qué, para qué, cómo, por qué, dónde")

- Estado: aceptado y aplicado en la versión 4 (ver ADR 0005)
- Fecha: 2026-10-26
- Relacionado: ADR 0002, ADR 0003, `docs/arquitectura/patrones-de-diseno.md`, `specs/modelo-datos/propuesta_v3.md`

## Criterio de evaluación

Cada recomendación se califica por **viabilidad técnica** (funciona en las condiciones reales de la finca: sin red
eléctrica, señal débil, Android), **valor** (ingreso, ahorro o reducción de riesgo), **costo y complejidad para un equipo
que aprende**, y **riesgo legal**. Decisión posible: Adoptar · Adaptar (se adopta con cambios) · Posponer · Corregir
(la recomendación tiene un dato erróneo) · Rechazar.

## Correcciones al cuadro general

| Punto del cuadro | Corrección | Fuente |
| --- | --- | --- |
| Turismo: "pasarela de pagos (Stripe/MercadoPago)" | Stripe limita su operación en Latinoamérica a México y Brasil; para cobros locales usar Wompi, Mercado Pago, ePayco o PayU, y Bre-B para transferencias inmediatas | Forbes Colombia, 29-abr-2024 |
| Integraciones: "API de precios de Corabastos" | No se conoce una API pública de Corabastos. El DANE publica SIPSA por un servicio web SOAP oficial (mayoristas diario a las 2:00 p. m., mensual el día 8; abastecimiento el día 10) | DANE, servicio web SIPSA |
| UX: "comandos de voz con Web Speech API" sin conexión | El reconocimiento en el dispositivo (`processLocally`) es experimental y su lanzamiento cubre Windows, Mac y Linux, no Android. En la PWA de campo la voz sin señal no es confiable | MDN; Chromium Intent to Ship |
| Auditoría: "encriptación de datos" | Precisar en tres capas: TLS en tránsito, cifrado en reposo (disco y respaldos) y cifrado por campo solo para datos sensibles (documento, teléfono) con llaves fuera de la base | — |
| Asociatividad: "5 asociados" | La modalidad recomendada para el Fondo Emprender es individual; el onboarding sigue aplicando a la familia y a los operarios | ADR del plan Fondo Emprender |

## Decisión por recomendación

| # | Recomendación | Decisión | Fase | Ajuste o complemento |
| --- | --- | --- | --- | --- |
| 1 | Comandos de voz en la PWA | Adaptar | 2 | Sin señal: **grabar nota de voz** (MediaRecorder funciona sin conexión) y transcribir al sincronizar en el servidor; el operario confirma lo interpretado. Con señal: dictado opcional. Vocabulario cerrado ("postura lote 3, ochenta y siete") para reducir errores |
| 2 | Botones gigantes y alto contraste | Adoptar | 1 | Modo campo: objetivos táctiles ≥ 48 px, contraste WCAG AA a pleno sol, un registro por pantalla, confirmación con sonido y vibración |
| 3 | Modo aprendiz y tutoriales | Adoptar | 1 | Aprovechar la multi-finca: una **finca de práctica** (`predio.es_practica`) con datos de ejemplo; lo registrado allí nunca toca la finca real (aislado por RLS) |
| 4 | Estación meteorológica y anular riego si llueve | Adoptar | 4 | Lluvia y humedad locales por MQTT + pronóstico externo cuando hay internet; la regla de riego incluye "no regar si llovió > X mm en 24 h o la probabilidad de lluvia > Y %" |
| 5 | Cadena de frío con sensores DS18B20 | Adoptar (adelantar) | 2 | Es inocuidad alimentaria y cuesta poco. Sensores en neveras y en el transporte con registrador que guarda sin señal; si la temperatura sale del rango por más de N minutos, una **regla fija bloquea los lotes** de esa bodega y avisa; liberar el lote es decisión humana |
| 6 | Visión artificial para clasificar huevos | Adaptar | 1 → 4 | Primero **clasificación por peso** con la báscula (las categorías comerciales del huevo en Colombia se definen por peso; verificar rangos en la NTC 1240 vigente). Visión para fisuras y suciedad con ovoscopio + cámara: piloto en fase 4 |
| 7 | Predicción de demanda (Prophet) | Adaptar | 2–3 | Requiere al menos 12 meses de ventas para captar Semana Santa y diciembre. Empezar con una línea base estacional, comparar contra modelos de series de tiempo y quedarse con el que menos error tenga |
| 8 | Notas de voz de clientes (Whisper) | Adoptar | 1–2 | El cliente rural envía audios por WhatsApp: transcribir, guardar la transcripción en `mensajes.texto` y conservar el audio con su vencimiento. Proveedor de voz a texto intercambiable |
| 9 | Huella de carbono | Adaptar | 2 | Primero **medir** (kWh solares, m³ de biogás, kg de compost y humus, litros de agua reutilizada). CO₂ solo con factores documentados y marcado "estimado"; afirmaciones ambientales sin respaldo exponen a sanciones por publicidad engañosa |
| 10 | Residuos como producto (humus, compost) | Adoptar | 1 | Categoría "Abonos orgánicos" y lotes de humus o compost producidos por el lombricultivo, vendibles con el mismo inventario |
| 11 | Trueque y pago en especie | Adaptar | 2 | Modelar como **permuta**: una venta y una compra valoradas que se compensan, cada una con su documento (factura y documento soporte). Pago con mano de obra: excluido, porque crea obligaciones laborales; usar contrato aparte |
| 12 | Microcrédito con intereses y scoring | Adaptar (limitar) | 2 | Sí a **cartera**: venta a crédito con cupo, plazo, vencimientos y mora. Intereses de mora nunca por encima de la tasa de usura vigente. Nada de "financiación propia" como negocio sin asesoría. Scoring con reglas simples y explicables, nunca decisión automática de la IA, y respetando el hábeas data financiero |
| 13 | TimescaleDB para auditoría y event sourcing | Rechazar el event sourcing · Adaptar | 2–3 | El outbox ya publica eventos. La auditoría se **particiona por mes** en PostgreSQL; la analítica va a una réplica de lectura o a DuckDB. TimescaleDB queda para IoT |
| 14 | mTLS entre agentes y ERP | Adaptar | 1 → 3 | Fase 1: red interna de Docker sin exponer el ERP, token de servicio de corta duración con permisos mínimos y firma de solicitudes. mTLS cuando los servicios estén en máquinas distintas o en Kubernetes |
| 15 | GitOps desde la fase 0 | Adaptar | 0 → 3 | Fase 0–2: GitOps ligero con GitHub Actions, imágenes etiquetadas por commit y `docker compose` declarativo en el servidor. Argo CD o Flux al llegar Kubernetes |
| 16 | Precios de referencia diarios | Corregir y Adoptar | 1 | Adaptador al servicio SOAP de SIPSA que corre a diario después de las 2:00 p. m. y llena `compras.precio_mercado` |
| 17 | Marketplace B2B (HORECA) | Adoptar | 2 | Portal para restaurantes y mayoristas sobre el mismo catálogo: lista de precios por segmento, **pedidos recurrentes**, cupo de crédito y facturación automática |
| 18 | Turismo: calendario, reservas y check-in | Adoptar | 3 | Con pasarela local (ver corrección) y depósito de reserva |

## Complementos propios (no estaban en las recomendaciones)

| Complemento | Por qué | Fase |
| --- | --- | --- |
| Trazabilidad y retiro de lotes (recall) | Con `reserva_lote` ya se sabe qué cliente recibió qué lote; falta la vista y el procedimiento para avisar y retirar en minutos si hay un problema sanitario | 1 |
| Registros de bioseguridad e inocuidad | Limpieza y desinfección, control de plagas, visitas al galpón, agua: los exige la bioseguridad avícola del ICA y suman para certificaciones | 1 |
| Activación de funciones por fase (feature flags) | Encender módulos por finca y por fase sin desplegar otra versión; útil para aprender y para la finca de práctica | 1 |
| Avisos por SMS cuando no hay datos | Alertas críticas (nevera caliente, válvula abierta) llegan aunque el celular no tenga datos | 2 |
| Pedidos recurrentes | La tienda o el restaurante que compra cada semana no repite el pedido; base del B2B | 2 |

## Consecuencias

- La versión 3 del modelo agrega unas 14 tablas y cambia 6 (ver `propuesta_v3.md`); se aplicará con su batería de pruebas, como la v2.
- Se fija el catálogo de patrones de diseño; cada módulo nuevo debe declarar qué patrón usa y por qué.
- Quedan por confirmar con la familia: rangos de peso del huevo según la norma vigente, umbrales de temperatura de neveras, y si se ofrecerá venta a crédito.
