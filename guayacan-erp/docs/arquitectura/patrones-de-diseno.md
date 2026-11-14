# Patrones de diseño de GuayacanERP

Cada patrón aparece donde resuelve un problema real del sistema, no por adorno. La columna "Dónde" dice el
componente concreto; "Por qué" dice el problema que evita. Al construir un módulo nuevo se declara aquí qué patrón usa.

## 1. Patrones de arquitectura

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Monolito modular | Django, una app por esquema | Un solo despliegue y una sola base transaccional mientras el equipo es pequeño; los límites entre apps evitan el "monolito espagueti" |
| Arquitectura hexagonal (puertos y adaptadores) | Capas de cada app: API → casos de uso → dominio → adaptadores | La regla de negocio no depende de Django, de MongoDB ni de Meta; cambiar un proveedor toca solo su adaptador |
| Microservicio por necesidad | Servicio de agentes (FastAPI) y servicio IoT | Escalan distinto (conversación en tiempo real, lecturas masivas) y sus fallas no tumban el ERP |
| Base de datos por servicio | PostgreSQL del ERP, MongoDB de agentes, TimescaleDB de IoT | Un dato tiene un solo dueño; nadie escribe en la base de otro |
| API Gateway | Nginx frente a /api, /agentes, /iot | Un solo punto para TLS, límites de peticiones y autenticación |
| Backend for Frontend (ligero) | Endpoints de sincronización de la PWA | La app de campo recibe exactamente lo que necesita sin conexión, no todo el ERP |
| Edge computing / store-and-forward | Pasarela local de riego, registrador de temperatura del transporte | La finca sigue operando sin internet; los datos suben cuando hay señal |

## 2. Patrones de datos y consistencia

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Unit of Work | `transaction.atomic` en cada caso de uso | Un pedido, sus reservas y su evento se guardan juntos o no se guardan |
| Transactional Outbox | `nucleo.evento_salida` + Celery | Publicar eventos sin "escrituras dobles" que dejen datos inconsistentes |
| Publicar/suscribir (Observer distribuido) | Redis Streams: pedido.confirmado, precio.aplicado, lote.bloqueado | Los agentes reaccionan a lo que pasa en el ERP sin que el ERP los conozca |
| CQRS ligero | Vistas `v_catalogo_disponible`, `v_alertas_vencimiento`; réplica de lectura para informes | Lecturas rápidas y seguras para agentes e informes, sin tocar el modelo de escritura |
| Clave de idempotencia | `id_cliente` (UUIDv7) en la captura sin conexión; id de mensaje en webhooks | Un registro o un webhook repetido se aplica una sola vez |
| Registro inmutable (append-only) | Kardex, auditoría, mensajes salientes | Nada se edita; las correcciones son movimientos nuevos, así la historia es confiable |
| Precio con vigencia (temporal) | `precio_producto.vigente_desde/hasta`, `parametro` | Saber qué precio o tarifa regía en cualquier fecha |
| Multi-inquilino con aislamiento por filas | `predio_id` + RLS + llaves compuestas | Varias fincas en la misma base sin poder verse entre sí, aunque el código falle |
| Repositorio | Repositorio de MongoDB en FastAPI | Centraliza el filtro obligatorio por `predio_id` (MongoDB no tiene RLS) |
| Active Record | Modelos Django | Sencillo para CRUD; la lógica compleja se saca a servicios para no engordar los modelos |
| Particionamiento | Auditoría y lecturas IoT por mes (v4) | Tablas que crecen sin límite siguen siendo rápidas y se archivan por partes |

## 3. Patrones de dominio (comportamiento del negocio)

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Máquina de estados (State) | Pedido, propuesta de precio, lote, bloqueo de lote, comprobante, conversación, escalamiento, comando de actuador, alarma (`iot.cambiar_estado_alarma`) | Solo se permiten transiciones válidas (un pedido despachado no se cancela) |
| Strategy | Salida FEFO o FIFO; proveedor de IA (LiteLLM); pasarela de pago; modelo de pronóstico; proveedor de voz a texto | Cambiar el algoritmo o el proveedor sin tocar quien lo usa |
| Specification | `inventario.puede_venderse(lote)` = disponible ∧ con existencias ∧ antes de la fecha límite ∧ sin bloqueo abierto; la usan la reserva FEFO y el catálogo | Reglas componibles, probables por separado y reutilizables en catálogo, reserva y escaneo |
| Policy (política configurable) | `redes.politica_canal`, `parametro` (margen mínimo, descuento por vencer) | Las reglas que cambian por decisión de negocio o del proveedor viven en datos, no en código |
| Command | `iot.comando_actuador`, `ia.solicitud_aprobacion` | Una orden es un objeto con estado, vencimiento y auditoría; se puede aprobar, ejecutar, reintentar o descartar |
| Human-in-the-loop (aprobación) | Precios, publicaciones, piezas audiovisuales, reglas de riego, liberar o descartar lotes bloqueados, confirmar pagos | La IA o la regla propone; la persona decide lo que es irreversible o costoso |
| Domain events | lote.bloqueado, temperatura.fuera_de_rango, pedido.confirmado | Expresan hechos del negocio que otros módulos escuchan |
| Value Object | Dinero (COP), peso (kg), rango de temperatura | Evita errores de unidades y redondeo |
| Process manager / Saga | Pedido → factura DIAN → pago; permuta (factura + documento soporte + pago de compensación); retiro de lote (bloqueo + avisos) | Pasos con sistemas externos que pueden fallar; cada paso sabe compensar o reintentar |

## 4. Patrones de integración

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Adapter | WhatsApp, Instagram, Messenger, TikTok, chat web → mensaje común; SIPSA SOAP → precio_mercado | Cada proveedor habla distinto; el sistema habla un solo idioma |
| Anti-corruption layer | DIAN, Meta, SIPSA, pasarelas de pago | El modelo de la finca no se contamina con los conceptos y nombres de terceros |
| Circuit breaker + reintento con espera exponencial | Llamadas a proveedor de IA, DIAN, Meta, SIPSA | Un proveedor caído no tumba la atención; se degrada con mensaje de cortesía o escalamiento |
| Timeout y bulkhead | Colas separadas de Celery (ERP, agentes, informes) | Un informe pesado no frena la facturación |
| Facade | Servidor MCP | Los agentes ven 15 herramientas simples, no los 400 endpoints del ERP |
| Webhook con verificación de firma | Meta y TikTok | Solo se aceptan mensajes auténticos |

## 5. Patrones de agentes de IA

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Router (enrutador) | Orquestador | Cada mensaje va al agente correcto o a una persona |
| Chain of Responsibility (cadena de guardias) | Dato prohibido → fuera de dominio → intención → agente → `verificar_envio` | Cada eslabón puede detener o desviar el mensaje; fácil de probar por partes |
| Tool use con mínimo privilegio | `ia.agente_herramienta` | Cada agente solo puede lo que su rol necesita |
| RAG (recuperación aumentada) | Base de conocimiento con pgvector | Respuestas con información de la finca, no inventadas |
| Factory / configuración | Agentes definidos en `ia.agente` (modelo, instrucciones, límites) | Crear o ajustar un agente sin programar uno nuevo |
| Template Method | Flujo base de un agente: recibir → clasificar → consultar → responder → registrar | Todos los agentes comparten pasos de seguridad y bitácora |
| Evaluador (evals) | Conjunto fijo de conversaciones + `evaluacion_respuesta` | Cambiar instrucciones o modelo solo si no empeora |

## 6. Patrones de frontend y campo

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Offline-first con bandeja de salida local | PWA: IndexedDB + cola de pendientes | El operario registra sin señal; nada se pierde |
| Store con signals (estado reactivo) | Angular | Un solo lugar para el estado de la pantalla, fácil de seguir |
| Componentes contenedor / presentacional | Angular | Pantallas simples de probar y reutilizar |
| Interfaz orientada a tareas | Modo campo (botones grandes, una tarea por pantalla) | Uso con guantes, al sol y con poca experiencia digital |
| Feature toggle | `nucleo.funcionalidad`: crédito, permuta, cadena de frío, cámaras, rostro, visión, gemelo 3D, blockchain; finca de práctica | Encender funciones de a poco y practicar sin riesgo |

## 7. Patrones de IoT

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Device shadow (gemelo del dispositivo) | `actuador.estado_actual` (reportado) vs. comando (deseado) | Saber si la válvula hizo lo que se le pidió |
| Fail-safe y watchdog | Electroválvulas normalmente cerradas, tiempo máximo en el nodo | Si algo falla, el agua se cierra |
| Regla en el borde con versión | `regla_automatizacion.version / desplegada_version` | La finca ejecuta la última regla aprobada aunque no haya internet |
| Observer por MQTT | Sensores de seguridad, humo, gas y temperatura publican; la pasarela reacciona | Agregar un sensor no cambia las reglas |
| Falla segura para personas | `actuador.modo_falla`: en un paso de personas la cerradura abre sin energía | Nadie queda encerrado si se va la luz |
| Retención limitada | `camara.retencion_dias`, `iot.depurar_clips()` | Ley 1581: los videos de seguridad no se guardan sin límite |

## 8. Listo para crecer (puertos para el equipo futuro)

| Puerto | Implementación de hoy | Implementación futura | Interruptor |
| --- | --- | --- | --- |
| `DetectorPresencia` | Sensores PIR y magnéticos | Cámara térmica | `camara_termica` |
| `VerificadorIdentidad` | PIN o tarjeta RFID | Rostro con autorización expresa | `reconocimiento_facial` |
| `MapaFinca` | Mapa 2D con zonas PostGIS | Gemelo digital 3D | `gemelo_3d` |
| `RegistroExterno` | Cadena de huellas SHA-256 (`comercial.huella_trazabilidad`) | Anclaje en blockchain | `anclaje_blockchain` |
| `ClasificadorHuevo` | Peso en báscula (`clasificar_por_peso`) | Visión artificial | `vision_artificial` |

## 9. Versión 5: personas, dinero, agenda, proyectos y seguridad

| Patrón | Dónde | Por qué |
| --- | --- | --- |
| Segregación de funciones (cuatro ojos) | Pagos y cierre de nómina, cambios de proyecto, tareas | Nadie aprueba lo propio; los montos grandes llevan dos personas |
| Guardia "solo personas" (`nucleo.exigir_persona`) | Toda aprobación | La IA propone y una persona decide, verificado en la base y no solo en la API |
| Máquina de estados | Tarea, periodo de nómina, visita, misión, proyecto, cronograma | Transiciones válidas y estados finales que no se editan |
| Registro inmutable y versionado | Líneas base, documentos, accesos, alertas, informes de indicadores | Auditoría: lo aprobado no cambia, se crea una versión nueva |
| Restricción de exclusión | `agenda.cita` | Sin dobles reservas aunque lleguen al mismo tiempo |
| Generador desde plantilla | Plan de labores, patrones de turno, órdenes de mantenimiento | Lo repetitivo se crea solo y queda editable |
| Specification | `personal.empleado_disponible`, `formacion.esta_habilitado`, `agenda.recurso_libre` | Una sola definición que usan reglas, pantallas y agentes |
| Evidencia derivada | `cumplimiento.evaluar_expediente` | El expediente se arma con los datos que ya existen; lo vencido deja de cumplir |
| Señuelo (honeytoken) | Cuenta y llave de API señuelo | Detecta intrusos con cero falsos positivos |
| Limitación por ventana | Detector de fuerza bruta y relleno de credenciales | Bloqueo temporal automático sin intervención |
| Cálculo en la base | VPN, TIR, CPM, valor ganado, estados financieros | Un solo resultado para pantallas, agentes e informes |

## Antipatrones que el diseño evita

| Antipatrón | Riesgo | Cómo se evita |
| --- | --- | --- |
| Monolito distribuido | Que FastAPI llame al ERP para todo y uno caído tumbe al otro | Caché del catálogo, eventos, circuit breaker y respuestas degradadas |
| Escritura doble | Guardar en PostgreSQL y publicar a mano: si falla una, quedan distintas | Outbox |
| Modelo gordo / servicio dios | Toda la lógica en un modelo o en una vista | Casos de uso por app y reglas críticas en la base |
| Agente con superpoderes | Una IA que puede cambiar precios o pagar | Herramientas de propuesta + aprobación humana |
| Event sourcing prematuro | Complejidad sin necesidad | Outbox + auditoría particionada; kardex, eventos de seguridad y huellas ya son de solo inserción |
| Cifrar todo sin gestión de llaves | Falsa seguridad o datos irrecuperables | Cifrado por campo solo en datos sensibles, llaves en el gestor de secretos |
