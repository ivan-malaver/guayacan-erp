# Parte I · Documento técnico

Oct 28, 2026 · @Ivan Malaver Fierro

## Cómo usar este documento

Este documento es la puerta de entrada para quien va a construir GuayacanERP: explica el modelo v5 con diagramas UML, especifica todos los casos de uso y dice en qué orden construir. El modelo de datos (25 esquemas, 246 tablas, 305 pruebas aprobadas) ya existe y no se rediseña: el trabajo del equipo es construir encima de él la API, los servicios y las pantallas.

| Si usted es… | Lea primero | Luego |
| --- | --- | --- |
| Desarrollador backend (Django) | Arquitectura, modelo de dominio, convenciones | Casos de uso del módulo que le toca y su secuencia |
| Desarrollador frontend (Angular PWA) | Actores y roles, casos de uso, sincronización sin conexión | Estados de cada entidad (qué botones se muestran) |
| Desarrollador de agentes o IoT (FastAPI) | Arquitectura, secuencias de atención y de riego | Casos de uso de IA, redes e IoT |
| Instructor o estudiante | Visión y actores, plan por sprints | Un módulo completo de punta a punta |
| Líder técnico o revisor | Trazabilidad y definición de terminado | Todo lo demás, por muestreo |

Qué acompaña a este documento:

- **Pestañas de casos de uso**: la especificación completa de cada caso, agrupada por área del negocio.
- **Paquete del repositorio** (zip): el modelo v5, el esqueleto del código (backend, servicios, frontend, CI), las fuentes de todos los diagramas UML y las guías de desarrollo en Markdown.
- **Excel de trazabilidad**: cada requerimiento con sus casos de uso, tablas, reglas en la base, endpoints y pruebas.
- **Diccionario de datos v5 y mapa de APIs v5**, entregados con la versión 5.

Tres reglas atraviesan todo el sistema y conviene tenerlas presentes desde la primera línea de código: la base de datos aplica las reglas críticas, la IA propone y una persona decide, y cada finca ve solo sus datos.

## Visión, alcance, actores y roles

GuayacanERP es la plataforma de la finca agro-turística El Guayacán de los Malaver (Pueblo Nuevo, Nilo, Cundinamarca): registra lo que pasa en el campo, lo vende, lo contabiliza y ayuda a decidir. La misma plataforma sirve a otras fincas sin mezclar datos, y tiene una finca de práctica para enseñar.

| Fase | Qué entra | Para qué |
| --- | --- | --- |
| 1 · MVP productivo | Núcleo, seguridad, terceros, producción, riego manual, inventario, compras, ventas, finanzas básicas, IA con aprobación, personal y tareas | Generar caja, controlar costos y demostrar trazabilidad |
| 2 · Validación comercial | Cadena de frío, crédito, recurrentes, redes, CRM, nómina, formación, activos, costos y presupuesto, estrategia, proyectos, seguros, visitas y portería | Recurrencia de clientes y operación ordenada |
| 3 · Turismo y crecimiento | Cabañas, planes, reservas con pago, agenda de recursos, API B2B, pronóstico | Validar el turismo sin construir de más |
| 4 · Automatización | IoT de riego, seguridad perimetral, cámaras, dron y robot, visión artificial, gemelo 3D, anclaje de huellas | Cuando se compren los equipos |

Lo que espera equipo, trámite o decisión ya está construido y apagado con una función por finca: el equipo no lo vuelve a diseñar, solo construye su pantalla y su API.

![Actores humanos de GuayacanERP](../uml/casos-uso/CU_00_actores.png)

Todos los actores con cuenta heredan de Usuario autenticado: inician sesión y operan solo en las fincas donde tienen un rol. El patrocinador de un proyecto es un rol que cumple la familia. Los actores sin cuenta llegan por un formulario público, un pase de visita o un canal de mensajería.

| Actor | Rol en la base | Qué hace en el sistema |
| --- | --- | --- |
| Administrador | `administrador` | Configura la finca, usuarios, funciones, precios y agentes; aprueba lo que proponen los agentes |
| Familia | `familia` | Decide inversiones, cierra nómina, aprueba pagos, iniciativas y proyectos |
| Encargado de finca | `encargado_finca` | Asigna y aprueba tareas, publica cronogramas, aprueba visitas, decide sobre lotes bloqueados |
| Operario de campo | `operario_granja` | Registra producción, labores, riego, cosechas y tareas desde la PWA, con o sin señal |
| Vendedor | `vendedor` | Toma y confirma pedidos, atiende clientes y prospectos, vende en feria |
| Contador | `contador` | Contabiliza, prepara y liquida nómina, estados financieros e impuestos |
| Portería | `porteria` | Registra entradas y salidas de personas y vehículos |
| Instructor y estudiante | `instructor`, `estudiante` | Dictan y toman cursos; los estudiantes practican en la finca de práctica |
| Director de proyecto | por proyecto | Planifica, mide avance y pide cambios |
| Cliente | `cliente` | Compra, reserva, paga y consulta la trazabilidad |
| Posible cliente, visitante, titular de datos, auditor, operador turístico | sin cuenta | Dejan sus datos con autorización, visitan, ejercen derechos de datos, auditan o piden grupos |

![Agentes de IA](../uml/casos-uso/CU_00_agentes.png)

Los 14 agentes son actores secundarios: consultan y proponen por herramientas del servidor MCP, y la base impide que aprueben, paguen, asignen o cierren nada (`nucleo.exigir_persona()`). Los sistemas externos son DIAN, canales de Meta y TikTok, la pasarela de pagos, el proveedor de IA, las fuentes de mercado (SIPSA-DANE), la aseguradora, la plataforma de cursos, la estación meteorológica y el cliente B2B; los procesos automáticos son las tareas programadas de Celery Beat, la pasarela IoT local y la integración continua.

## Arquitectura: componentes, despliegue y capas

El sistema es un monolito modular en Django dueño de PostgreSQL, más un servicio de agentes en FastAPI y una PWA en Angular. Los agentes y la pasarela IoT nunca escriben en la base: pasan por la API, que fija la finca de la sesión y deja que las reglas de la base acepten o rechacen.

![Diagrama de componentes](../uml/arquitectura/CO01_componentes.png)

| Capa | Tecnología | Responsabilidad |
| --- | --- | --- |
| PWA de campo y panel | Angular (componentes standalone, signals), Angular Material, service worker, Dexie | Capturar sin señal, escanear, pesar, aprobar, consultar tableros |
| Puerta de entrada | Nginx | HTTPS, límites de peticiones, rutas a ERP y agentes |
| Núcleo ERP | Python, Django, Django REST Framework, SimpleJWT, drf-spectacular | API REST, contexto de finca, servicios por caso de uso |
| Tareas | Celery y Celery Beat sobre Redis | Tareas diarias y mensuales, outbox, facturación, avisos |
| Agentes | FastAPI, SDK de Anthropic, LangGraph, LiteLLM, servidor MCP | Conversación por canales y propuestas con evidencia |
| Datos | PostgreSQL 18 + PostGIS + pgvector, MongoDB, Redis, MinIO | Fuente de verdad, conversaciones, colas, archivos |
| IoT (fase 4) | Mosquitto, ESP32, reglas en la pasarela, TimescaleDB opcional | Riego, alarmas y energía que funcionan sin internet |

El documento de requerimientos v1.0 proponía React o Vue, PostgreSQL 15 e InfluxDB. Esta versión sigue la arquitectura acordada: Angular PWA, PostgreSQL 18 y series de tiempo dentro de PostgreSQL (ADR 0002 a 0006). Las versiones exactas de cada librería se fijan en el primer sprint y quedan en el ADR 0001 del repositorio.

![Diagrama de despliegue](../uml/arquitectura/DE01_despliegue.png)

En la fase 1 todo corre en un VPS con Docker Compose y copias cifradas fuera del servidor. La finca solo necesita celulares con la PWA; la pasarela local llega con los equipos de la fase 4 y sigue operando sin internet. Cuando la carga lo pida, los mismos contenedores pasan a Kubernetes.

![Capas dentro de cada app de Django](../uml/arquitectura/CO02_capas_app.png)

Cada app de Django tiene cuatro capas. La regla de oro: **una regla crítica vive en la base y en ningún otro lado**. Python valida formato y orquesta; si la base rechaza, el servicio traduce el error a una respuesta 422 con el mensaje en español que ya trae la regla.

## Modelo de dominio e interacción entre módulos

El dominio se reparte en 25 paquetes, uno por esquema de PostgreSQL y una app de Django por paquete. Todos dependen de `nucleo` (finca, usuarios, parámetros) y casi todos de `terceros`; las dependencias entre los demás siguen el flujo del negocio, del campo al dinero.

![Diagrama de paquetes](../uml/paquetes/PK_dependencias.png)

Cómo leer el diagrama: cada flecha es «usa datos de» y el número dice cuántas llaves foráneas la sostienen. Construya un paquete solo cuando los paquetes a los que apunta ya existan. Los diagramas de clases de cada módulo están en su pestaña de casos de uso; los módulos grandes van en dos partes.

| Interacción | Módulos | Cómo ocurre |
| --- | --- | --- |
| Del campo a la bodega | produccion → inventario | Cosecha, postura o abono crean un lote; el kardex registra la entrada |
| De la bodega al cliente | inventario → comercial | El pedido reserva lotes en orden FEFO; despacho descuenta; la huella SHA-256 traza el lote |
| De la venta a la contabilidad | comercial → finanzas | Factura y pago generan comprobantes por regla fija |
| Del trabajo a la nómina | personal → nomina → finanzas | Tareas y jornadas aprobadas generan jornal o destajo; el cierre exige comprobante contabilizado |
| De la formación a la asignación | formacion → personal | Sin habilitación vigente no se asigna la tarea |
| Del mantenimiento al trabajo | activos → personal | La orden de trabajo crea su tarea |
| De la evidencia al cumplimiento | personal, produccion, documental, formacion → cumplimiento | El expediente se evalúa solo contra registros, documentos y habilitaciones |
| Del prospecto al cliente | crm → terceros → comercial | La conversión crea tercero y cliente |
| De la utilidad a la inversión | finanzas → estrategia → proyectos | La utilidad de cada línea financia iniciativas aprobadas que se ejecutan como proyectos |
| De la reserva a la agenda | turismo → agenda → personal | La reserva ocupa la cabaña sin cruces; la salida crea la limpieza |
| De la portería a la jornada | agenda → personal | El carné abre y cierra la jornada |
| Del sensor a la decisión | iot → inventario, riego, seguros | Frío bloquea lotes, humedad riega, el índice climático prepara el aviso de siniestro |
| De los agentes al ERP | ia → todos | Solo por herramientas MCP; lo que cambia algo queda en la bandeja de aprobación |

Convenciones del modelo que todo desarrollador debe conocer:

- **Campos comunes**: `id`, `predio_id`, `creado_en` y `actualizado_en` en las tablas por finca; `id_cliente` (UUIDv7), `capturado_en` y `dispositivo_captura_id` en las 35 tablas que se capturan sin conexión.
- **Seguridad por filas**: 217 tablas por finca con política RLS sobre `nucleo.predio_actual()`; las llaves foráneas son compuestas `(predio_id, id)`, así una finca no apunta a datos de otra.
- **Catálogos compartidos**: especies, cultivos, unidades, PUC, normas, indicadores y reglas de seguridad no llevan finca.
- **Auditoría**: 102 tablas sensibles disparan `nucleo.auditar()`, que guarda solo los campos cambiados y quién (persona o agente).
- **Solo inserción**: kardex, huellas, accesos de portería, intentos de acceso, líneas base y alertas no se editan ni se borran.
- **Estados**: cada `estado` es una lista cerrada con CHECK; las transiciones válidas están en los diagramas de estados de la sección siguiente.
- **Dinero** en `numeric(14,2)` pesos; **fechas** como `fecha_<hecho>` o `<hecho>_en`; **nombres** en español, singular y minúscula.

## Comportamiento: secuencias, estados y actividades

Quince secuencias muestran cómo colaboran los componentes en los flujos que más pesan; diecisiete máquinas de estado dicen qué transiciones acepta la base, y por tanto qué botones muestra cada pantalla; cuatro actividades describen las tareas programadas, el cierre de mes, la mejora continua y el flujo de trabajo del equipo.

### Secuencias

**SQ01 · Toda petición a la API.** El middleware fija la finca y el usuario en la transacción; la base filtra y aplica las reglas; un rechazo llega como 422 con el mensaje de la regla.

![SQ01 petición con contexto de finca](../uml/secuencia/SQ01_peticion_api_contexto_finca.png)

**SQ02 · Inicio de sesión con doble factor y detector de ataques** (SEG-01, SEG-03).

![SQ02 inicio de sesión](../uml/secuencia/SQ02_inicio_sesion_doble_factor.png)

**SQ03 · Sincronización sin conexión** (NUC-05). Idempotente por `id_cliente`: enviar dos veces cuenta una.

![SQ03 sincronización](../uml/secuencia/SQ03_sincronizacion_sin_conexion.png)

**SQ04 · Confirmar pedido con reserva FEFO y outbox** (VTA-03).

![SQ04 confirmar pedido](../uml/secuencia/SQ04_confirmar_pedido_fefo.png)

**SQ05 · Atención por WhatsApp con agentes** (RED-01).

![SQ05 atención por WhatsApp](../uml/secuencia/SQ05_atencion_whatsapp_agentes.png)

**SQ06 · Cambio de precio propuesto por IA y aprobado por una persona** (VTA-02, IA-02).

![SQ06 cambio de precio](../uml/secuencia/SQ06_cambio_precio_aprobado.png)

**SQ07 · De la tarea del día a la nómina** (PER-03 a PER-06, NOM-02, NOM-04).

![SQ07 tarea a nómina](../uml/secuencia/SQ07_tarea_a_nomina.png)

**SQ08 · Cierre y pago de nómina con segregación de funciones** (NOM-05, NOM-06).

![SQ08 cierre y pago de nómina](../uml/secuencia/SQ08_cierre_y_pago_nomina.png)

**SQ09 · Reserva de cabaña, pago, agenda y limpieza** (TUR-02 a TUR-04).

![SQ09 reserva de cabaña](../uml/secuencia/SQ09_reserva_cabana.png)

**SQ10 · Cadena de frío y decisión humana sobre el lote** (INV-07).

![SQ10 cadena de frío](../uml/secuencia/SQ10_cadena_frio_bloqueo.png)

**SQ11 · De la iniciativa al proyecto** (EST-03 a EST-06, PRY-01, PRY-02).

![SQ11 iniciativa a proyecto](../uml/secuencia/SQ11_iniciativa_a_proyecto.png)

**SQ12 · Cronograma 24/7** (PER-07).

![SQ12 cronograma 24/7](../uml/secuencia/SQ12_cronograma_24_7.png)

**SQ13 · Riego automático en la red local** (RIE-03, fase 4).

![SQ13 riego automático](../uml/secuencia/SQ13_riego_automatico_local.png)

**SQ14 · Visita y portería** (AGD-03, AGD-04).

![SQ14 visita y portería](../uml/secuencia/SQ14_visita_porteria.png)

**SQ15 · Captura y conversión de un posible cliente** (CRM-01 a CRM-05).

![SQ15 captura de prospecto](../uml/secuencia/SQ15_captura_prospecto.png)

### Máquinas de estado

Una transición que no aparece aquí la rechaza la base. En la PWA y el panel, muestre solo los botones de las transiciones que salen del estado actual.

![ST01 pedido](../uml/estados/ST01_pedido.png)

![ST02 lote de inventario](../uml/estados/ST02_lote_inventario.png)

![ST03 tarea](../uml/estados/ST03_tarea.png)

![ST04 periodo de nómina](../uml/estados/ST04_periodo_nomina.png)

![ST05 comprobante contable](../uml/estados/ST05_comprobante.png)

![ST06 propuesta de precio](../uml/estados/ST06_propuesta_precio.png)

![ST07 reserva turística](../uml/estados/ST07_reserva_turistica.png)

![ST08 visita](../uml/estados/ST08_visita.png)

![ST09 proyecto](../uml/estados/ST09_proyecto.png)

![ST10 iniciativa](../uml/estados/ST10_iniciativa.png)

![ST11 prospecto](../uml/estados/ST11_prospecto.png)

![ST12 cronograma](../uml/estados/ST12_cronograma.png)

![ST13 misión de dron o robot](../uml/estados/ST13_mision_robot.png)

![ST14 alarma por zona](../uml/estados/ST14_alarma.png)

![ST15 alerta de seguridad](../uml/estados/ST15_alerta_seguridad.png)

![ST16 siembra](../uml/estados/ST16_siembra.png)

![ST17 solicitud de aprobación](../uml/estados/ST17_solicitud_aprobacion.png)

### Actividades

**AC01 · Tareas programadas de cada noche.** El orden importa: primero vencimientos y habilitaciones, después se generan tareas y órdenes.

![AC01 tareas programadas diarias](../uml/actividad/AC01_tareas_programadas_diarias.png)

**AC02 · Cierre mensual.**

![AC02 cierre mensual](../uml/actividad/AC02_cierre_mensual.png)

**AC03 · Mejora continua (PHVA) con el Analista de negocio.**

![AC03 mejora continua](../uml/actividad/AC03_mejora_continua_phva.png)

**AC04 · Cómo se construye una historia de usuario.**

![AC04 flujo de una historia](../uml/actividad/AC04_flujo_de_una_historia.png)

## Casos de uso: catálogo, diagramas y plantilla

El sistema tiene 177 casos de uso en 25 módulos; 18 de ellos esperan una función por finca encendida. Cada caso lleva un código de prefijo y número (por ejemplo VTA-03) que se usa en el backlog, en las ramas de git, en los commits y en el nombre de las pruebas.

| Pestaña | Módulos y casos |
| --- | --- |
| Casos de uso 1 · Plataforma y seguridad | Núcleo NUC-01 a 10, Seguridad SEG-01 a 07, Terceros TER-01 a 04, Documental DOC-01 a 03 (24 casos) |
| Casos de uso 2 · Producción y campo | Producción PRO-01 a 10, Riego RIE-01 a 03, IoT IOT-01 a 09, Ambiental AMB-01 a 03 (25 casos) |
| Casos de uso 3 · Inventario, compras y activos | Inventario INV-01 a 07, Compras CMP-01 a 04, Activos ACT-01 a 05 (16 casos) |
| Casos de uso 4 · Ventas, clientes y turismo | Ventas VTA-01 a 12, CRM CRM-01 a 06, Redes RED-01 a 06, Turismo TUR-01 a 06, Agenda AGD-01 a 06 (36 casos) |
| Casos de uso 5 · Personas | Personal PER-01 a 10, Formación FOR-01 a 09, Nómina NOM-01 a 08 (27 casos) |
| Casos de uso 6 · Dinero y decisiones | Finanzas FIN-01 a 12, Estrategia EST-01 a 08, Proyectos PRY-01 a 09, Seguros SGR-01 a 04 (33 casos) |
| Casos de uso 7 · Cumplimiento e inteligencia artificial | Cumplimiento CUM-01 a 07, Inteligencia artificial IA-01 a 09 (16 casos) |

Cómo leer los diagramas de casos de uso:

- **Monigote a la izquierda**: actor primario, quien inicia el caso. **Caja gris a la derecha**: sistema externo o proceso automático. **Caja morada punteada**: agente de IA, que participa pero no decide.
- **Óvalo verde**: caso del módulo. **Óvalo punteado** con «\[función …\]»: construido y apagado hasta encender esa función. **Óvalo gris** en «Casos de otros módulos»: caso de otro módulo con el que se relaciona.
- **«include»**: el caso siempre ejecuta el otro (registrar postura siempre sincroniza). **«extend»**: el otro caso añade comportamiento solo bajo una condición (la venta a crédito extiende la confirmación del pedido).

Cada especificación sigue la misma plantilla, pensada para que un desarrollador la convierta en historia de usuario sin preguntar:

| Campo | Qué contiene |
| --- | --- |
| Objetivo | Qué logra el actor, en una frase |
| Actores | Primario y secundarios (sistemas y agentes) |
| Fase y función | Fase del plan y función por finca que lo enciende, si aplica |
| Disparador y precondiciones | Qué lo inicia y qué debe ser cierto antes |
| Flujo principal | Pasos numerados, actor y sistema alternados |
| Flujos alternos y excepciones | Numerados por el paso del que salen (3a, 5b); cada excepción con el mensaje que devuelve la base |
| Postcondiciones | Qué queda en la base y qué eventos se publican |
| Reglas de negocio | Funciones y disparadores de la base que lo garantizan |
| Datos | Tablas que lee y escribe |
| API | Endpoints o acciones; los CRUD siguen la convención /api/v1/esquema/recurso/ |
| Pruebas | Áreas de pruebas\_reglas\_v4.sql y v5.sql que ya lo cubren |
| Requerimientos | RF, RNF o RQ que satisface |

## Del caso de uso a la historia de usuario

Las especificaciones completas están en las siete pestañas de casos de uso. Para trabajar, cada caso se parte en una o más historias con criterios de aceptación en formato Dado/Cuando/Entonces; los criterios salen de los flujos alternos y de las reglas, y casi todos ya tienen su prueba en SQL.

Ejemplo con **VTA-03 Tomar y confirmar un pedido**:

```markdown
Historia VTA-03.1 · Como vendedor quiero confirmar un pedido en borrador
para reservar el producto que vence primero y no vender lo que no hay.

Criterios de aceptación
- Dado un pedido en borrador de 60 cubetas y lotes de 50 y 40 vendibles,
  cuando lo confirmo, entonces toma 50 del lote que vence antes y 10 del siguiente.
- Dado que solo hay 30 cubetas vendibles, cuando confirmo 40,
  entonces recibo 422 "Inventario insuficiente…" y no queda ninguna reserva.
- Dado un lote pasado de su fecha límite de venta, cuando confirmo,
  entonces ese lote no se reserva.
- Dado que el precio cambió después de crear el pedido, cuando confirmo,
  entonces recibo 422 y debo actualizar la línea.

Pruebas existentes: v4 FEFO, Pedido, Catálogo.
Tareas: serializer de confirmación, servicio confirmar_pedido, vista POST
/pedidos/{id}/confirmar/, prueba pytest de la API, botón Confirmar en la PWA
visible solo en estado borrador.
```

Una historia está lista para empezar cuando tiene su caso de uso, sus criterios, las tablas identificadas y la prueba SQL que la respalda (nueva o existente).

## 8. Trazabilidad

Cada requerimiento llega a uno o más casos de uso, y cada caso de uso nombra sus tablas, reglas, endpoints y pruebas. La matriz completa (caso de uso × actor, requerimiento, tabla, regla, endpoint y prueba) está en el Excel de trazabilidad del paquete; esta tabla es el resumen. Las dos fuentes salen del mismo catálogo (`docs/uml/fuentes/catalogo.py`), así que si cambia un caso de uso se regeneran juntas.

### 8.1 Decisiones que reemplazan al documento de requerimientos v1.0

El documento de requerimientos v1.0 es la base funcional, pero varias decisiones técnicas cambiaron en las versiones 2 a 5 de la arquitectura. Donde los dos difieren, manda la arquitectura v5.

| Tema | Requerimientos v1.0 | Arquitectura v5 (vigente) | Por qué |
| --- | --- | --- | --- |
| Frontend | React o Vue | Angular PWA (campo y panel) | Un solo framework con service worker, formularios tipados e inyección de dependencias; ADR 0003 |
| Base de datos | PostgreSQL 15 | PostgreSQL 18 con PostGIS, pgvector y btree\_gist | Seguridad por filas, exclusión de rangos, UUIDv7 nativo, vectores para la IA; ADR 0003 y 0005 |
| Series de tiempo | InfluxDB | Tablas particionadas de PostgreSQL (`iot.lectura`) | Un motor menos que operar; particiones por mes desde la v4 y TimescaleDB solo si la fase 4 lo pide; ADR 0002, 0004 y 0005 |
| Conversaciones | No previsto | MongoDB 8 | Mensajes y bitácoras de agentes con esquema flexible; ADR 0002 |
| Requerimientos nuevos | RF-01 a RF-22 y RNF-01 a RNF-14 | Más RQ-23 a RQ-44 | Agentes, canales, IoT, personal, nómina, formación, finanzas, estrategia, agenda y proyectos |

### 8.2 Requerimiento → casos de uso

| Requerimiento | Casos de uso |
| --- | --- |
| RF-01 · Registro e inicio de sesión | NUC-02, SEG-01 |
| RF-02 · Gestión basada en roles | NUC-02 |
| RF-03 · Autenticación segura (JWT) y recuperación de contraseña | SEG-01, SEG-02 |
| RF-04 · Lotes y cultivos georreferenciados | NUC-01, PRO-05, PRO-07 |
| RF-05 · Registro de labores culturales | PRO-05 |
| RF-06 · Trazabilidad con código QR por lote | PRO-02, PRO-06, INV-02, INV-03, CMP-03, VTA-11, VTA-12 |
| RF-07 · Inventario vivo: mortalidad, resiembra y plantas vivas | PRO-01, PRO-03, PRO-04, PRO-05 |
| RF-08 · Bioinsumos: compost, humus y lixiviados | PRO-09 |
| RF-09 · Catálogo con precios por canal | INV-01, VTA-01, VTA-02 |
| RF-10 · Pedidos de clientes recurrentes y finales | TER-01, TER-04, VTA-03, VTA-05, VTA-09 |
| RF-11 · Control de cartera y bloqueo por mora | VTA-08 |
| RF-12 · Punto de venta móvil sin conexión | NUC-05, VTA-04 |
| RF-13 · Calendario de disponibilidad turística | TUR-01, TUR-02, TUR-06 |
| RF-14 · Reservas en línea con pago anticipado | TUR-02, TUR-03 |
| RF-15 · Gestión de grupos | TUR-05 |
| RF-16 · Check-in digital con consentimiento | TUR-04, AGD-03, AGD-04 |
| RF-17 · Tablero financiero por línea | FIN-01, FIN-02, FIN-07, FIN-08 |
| RF-18 · Reportes de producción y costo por kilogramo | PRO-02, PRO-03, PRO-06, PRO-10, FIN-05, FIN-08 |
| RF-19 · Reportes de sostenibilidad | RIE-02, AMB-01, AMB-03 |
| RF-20 · Notificaciones automáticas | NUC-09, RED-03 |
| RF-21 · Pasarela de pagos | VTA-07, TUR-03 |
| RF-22 · Georreferenciación y mapa de la finca | NUC-01 |
| RNF-01 · Crecimiento modular | NUC-01, NUC-03, NUC-04 |
| RNF-02 · Respuesta de la API menor a 2 segundos | Arquitectura y convenciones (3 y 10): índices, paginación, prueba de carga en CI |
| RNF-03 · Operación sin conexión (PWA) | NUC-05, NUC-07, INV-03, VTA-04, PER-05 |
| RNF-04 · Ley 1581 de protección de datos | NUC-06, SEG-04, TER-02, TER-03, IOT-06, CRM-01, RED-03, RED-05, TUR-04 |
| RNF-05 · Cifrado en tránsito y en reposo | SEG-07 |
| RNF-06 · Copias de seguridad diarias | SEG-07 |
| RNF-07 · Interfaz responsiva para campo | NUC-07 |
| RNF-08 · Español de Colombia y términos agrarios locales | Convenciones (10): nombres en español, mensajes de la base en español |
| RNF-09 · Identidad visual de la marca | Convenciones (10): tema de Angular Material con los colores de la marca |
| RNF-10 · Disponibilidad del 99 % | Arquitectura (3): despliegue, copias y monitoreo |
| RNF-11 · Código documentado (PEP 8, ESLint) | NUC-08, SEG-06 |
| RNF-12 · Bajo costo inicial y escalado a Kubernetes | IA-06 y arquitectura (3): VPS con Docker Compose |
| RNF-13 · Reportes para el Fondo Emprender | NUC-06, AMB-03, CMP-04, VTA-06, VTA-10, FIN-02, FIN-03, FIN-04, FIN-06, FIN-12 |
| RNF-14 · Economía circular: residuos y energía | PRO-09, IOT-09, AMB-01 |
| RQ-23 · Agentes de IA que proponen y una persona decide | DOC-03, CMP-01, CMP-02, VTA-02, RED-01, RED-04, FOR-09, EST-03, IA-01 a IA-09 |
| RQ-24 · Atención por WhatsApp, Instagram, Messenger y TikTok | RED-01 a RED-06 |
| RQ-25 · Riego e IoT en red local | RIE-01, RIE-02, RIE-03, IOT-01, IOT-02, IOT-03, IOT-09, SGR-04 |
| RQ-26 · Seguridad perimetral y cámaras | IOT-01, IOT-04, IOT-05, IOT-06, IOT-07 |
| RQ-27 · Inventario perecedero, FEFO y cadena de frío | INV-02, INV-04, INV-05, INV-06, INV-07, VTA-03, VTA-05, VTA-12 |
| RQ-28 · Tareas, áreas de responsabilidad y evidencias | ACT-05, PER-01 a PER-06, PER-09, PER-10, CUM-06 |
| RQ-29 · Nómina con salario, jornal y destajo | PER-06, PER-09, NOM-01 a NOM-08 |
| RQ-30 · Formación, cursos y habilitaciones | PER-04, FOR-01 a FOR-09 |
| RQ-31 · Activos y mantenimiento | ACT-01 a ACT-05 |
| RQ-32 · Gestión documental | DOC-01, DOC-02, DOC-03 |
| RQ-33 · Cumplimiento y certificaciones | DOC-02, PRO-08, FOR-06, FOR-07, FOR-08, CUM-01 a CUM-07 |
| RQ-34 · Seguros | SGR-01 a SGR-04 |
| RQ-35 · Seguridad informática | SEG-01 a SEG-06 |
| RQ-36 · Captura de clientes potenciales (CRM) | CRM-01 a CRM-06 |
| RQ-37 · Estrategia de negocio y reinversión | FIN-10, EST-01 a EST-08, IA-09 |
| RQ-38 · Costos, presupuesto, estados e indicadores | ACT-04, CRM-06, FIN-05 a FIN-12, EST-08 |
| RQ-39 · Agenda de cabañas, visitas y portería | TUR-02, AGD-01 a AGD-06 |
| RQ-40 · Cronograma de trabajo flexible 24/7 | PER-07, PER-08 |
| RQ-41 · Dirección de proyectos (PMBOK 8) | PRY-01 a PRY-09 |
| RQ-42 · Robótica y drones | IOT-08 |
| RQ-43 · Integraciones externas (API B2B, webhooks) | NUC-10 |
| RQ-44 · Ambiental y CO₂ estimado con fuente | AMB-01, AMB-02, AMB-03 |

### 8.3 Endpoints nuevos que definen los casos de uso

Además del CRUD que genera el mapa de APIs v5, las especificaciones fijan estas acciones. Todas van en el esqueleto como rutas declaradas que responden 501 hasta que se construyan.

| Endpoint | Caso de uso |
| --- | --- |
| `GET /api/v1/nucleo/mis-fincas/` y cabecera `X-Predio` | NUC-03 |
| `POST /api/v1/sincronizacion/lote/` | NUC-05 |
| `POST /api/v1/auth/doble-factor/inscribir/`, `POST /api/v1/auth/recuperar/` | SEG-01, SEG-02 |
| `POST /api/v1/terceros/consentimientos/{id}/revocar/`, `POST /api/v1/terceros/terceros/{id}/anonimizar/` | TER-02, TER-03 |
| `GET /api/v1/publico/trazabilidad/{codigo}/`, `GET /api/v1/publico/certificados/{codigo}/` | VTA-11, FOR-05 |
| `POST /api/v1/iot/lecturas/lote/`, `POST /api/v1/iot/eventos-seguridad/{id}/atender/` | IOT-02, IOT-05 |
| `POST /api/v1/turismo/reservas/{id}/pagar/`, `/check-in/`, `/check-out/`; `/api/v1/turismo/solicitudes-grupo/` | TUR-03, TUR-04, TUR-05 |
| `POST /api/v1/personal/tareas/{id}/devolver/`, `POST /api/v1/personal/jornadas/{id}/aprobar/` | PER-03, PER-06 |
| `POST /api/v1/nomina/periodos/{id}/transmitir/` | NOM-08 |
| `POST /api/v1/compras/documentos-soporte/{id}/transmitir/` | CMP-04 |
| `POST /api/v1/redes/mensajes-salientes/verificar/`, `POST /api/v1/ia/escalamientos/{id}/tomar/` | RED-03, RED-02 |
| `POST /agentes/instructor/preguntar` (servicio de agentes) | FOR-09 |

## 9. Guía de arranque y esqueleto del repositorio

El paquete v5.1 es el repositorio inicial: trae el modelo de datos verificado de la v5 y, encima, un esqueleto sin lógica de negocio para Django, FastAPI y Angular, con Docker y GitHub Actions. El esqueleto deja resuelto lo transversal (contexto de finca, errores, sincronización, rutas) para que cada desarrollador solo escriba casos de uso.

### 9.1 Estructura

```
guayacan-erp/
├── backend/                  Django + DRF, el monolito dueño de PostgreSQL
│   ├── manage.py, pyproject.toml
│   ├── config/               settings/{base,dev,test,prod}.py, urls.py, celery.py, wsgi.py, asgi.py
│   ├── guayacan/             lo transversal: contexto.py, errores.py, sincronizacion.py, eventos.py, permisos.py
│   └── apps/<esquema>/       25 apps: models.py, serializers.py, views.py, urls.py, services.py, tests/, README.md
├── servicios/
│   ├── agentes/              FastAPI: webhooks de canales, orquestador y cliente MCP
│   └── iot/                  FastAPI: puente MQTT y lecturas por lote (fase 4)
├── frontend/                 Angular PWA: core/ (interceptores, cola sin conexión), features/<módulo>/ perezosos
├── specs/                    esquema SQL, datos iniciales, generador y pruebas de reglas (v5)
├── docs/                     adr/, arquitectura/, diagramas/, uml/, casos-de-uso/, desarrollo/, manuales/
├── docker/, docker-compose.yml, .env.ejemplo
└── .github/workflows/ci.yml
```

El README de cada app lista sus casos de uso, sus tablas y las reglas de la base que la protegen, sacados del catálogo.

### 9.2 Primer día

1. Instale Docker Desktop, Python 3.12, Node 22 y Git. Clone el repositorio y copie `.env.ejemplo` como `.env`.
2. Levante los servicios: `docker compose up -d --build postgres mongodb redis`.
3. Cargue la base y corra las pruebas de reglas (ver `specs/modelo-datos/LEEME.md`). La última línea debe decir `TODAS LAS PRUEBAS PASARON`.
4. Backend: `cd backend`, cree el entorno virtual, `pip install -e .[dev]`, `python manage.py check` y `python manage.py runserver`. La documentación de la API queda en `/api/docs/`.
5. Frontend: `cd frontend`, `npm ci`, `npm start`. La PWA abre en `http://localhost:4200` y llama a la API por el proxy.
6. Lea esta guía, el ADR 0006 y la pestaña de casos de uso de su módulo antes de escribir código.

### 9.3 Cómo se construye un caso de uso

1. Tome el caso de uso del tablero; la rama se llama `cu/VTA-03-confirmar-pedido`.
2. Escriba primero la prueba de aceptación con el escenario Gherkin (sección 7) en `apps/<esquema>/tests/`.
3. Complete el modelo `managed=False` de las tablas que toca (los nombres de columna salen del diccionario).
4. Escriba el método del servicio: abre la transacción, llama a la base y publica el evento en el outbox. No repita en Python las reglas que ya están en la base.
5. Exponga el endpoint con su serializer y su permiso. Los errores de la base se traducen solos (sección 10.3).
6. En Angular, agregue la pantalla al módulo perezoso; si el caso de uso funciona sin conexión, use la cola de sincronización.
7. Corra las pruebas y abra el pull request con el ID del caso de uso.

### 9.4 Lo que el esqueleto ya resuelve

| Pieza | Archivo | Qué hace |
| --- | --- | --- |
| Contexto de finca | `backend/guayacan/contexto.py` | Toma la finca de la cabecera `X-Predio` o del token, verifica con nucleo.predios\_del\_usuario() que el usuario pertenezca a ella y fija `app.predio_id`, `app.usuario_id` y `app.agente_id` con `set_config(..., true)` dentro de la transacción de la petición |
| Errores | `backend/guayacan/errores.py` | Traduce los errores de PostgreSQL a HTTP con el mensaje en español de la regla |
| Sincronización | `backend/guayacan/sincronizacion.py` | Recibe lotes de la PWA y los inserta con `ON CONFLICT (id_cliente) DO NOTHING` |
| Outbox | `backend/guayacan/eventos.py` | Publica eventos en `nucleo.evento_salida` dentro de la misma transacción |
| Usuario | `backend/apps/nucleo/models.py` | Modelo de usuario sobre `nucleo.usuario` (sin migraciones) y modelos de finca, zona y funcionalidad |
| Tareas | `backend/config/celery.py` | Celery Beat con las tareas programadas que necesita la base |
| PWA | `frontend/src/app/core/` | Interceptor de token y finca, cola sin conexión en IndexedDB (Dexie) con UUIDv7 y servicio de sincronización |
| CI | `.github/workflows/ci.yml` | Carga la base, corre las dos baterías de reglas, el backend y el frontend |

## 10. Convenciones de desarrollo

### 10.1 Nombres e idioma

- Código de dominio en español sin tildes (`confirmar_pedido`, `PedidoSerializer`); palabras técnicas del framework en inglés (`views`, `services`).
- Una app de Django por esquema, con el mismo nombre. Rutas `/api/v1/<esquema>/<recurso>/` en minúsculas con guiones y la primera palabra en plural (`lotes-animal`).
- Acciones como subrecursos con verbo: `POST /pedidos/{id}/confirmar/`.
- Textos de la interfaz en español de Colombia con términos de la finca (galpón, cubeta, jornal, potrero).

### 10.2 Ramas, commits y revisiones

- `main` siempre desplegable; ramas `cu/<ID>-<resumen>`, `fix/<resumen>`, `docs/<resumen>`.
- Commits en español con el ID: `VTA-03: reserva FEFO al confirmar el pedido`.
- Todo pull request pasa CI y una revisión de otra persona; los cambios en `specs/` necesitan además correr las dos baterías de reglas.
- Nunca se suben claves ni el `.env`.

### 10.3 Errores de la base a HTTP

| SQLSTATE | Origen | HTTP | Respuesta |
| --- | --- | --- | --- |
| `P0001` | `raise exception` de una regla | 422 | `{"codigo":"regla_negocio","detalle":"<mensaje de la regla>"}` |
| `42501` | Seguridad por filas o permiso | 403 | `{"codigo":"sin_permiso"}` |
| `23505` | Único repetido | 409 | `{"codigo":"duplicado","campo":...}` |
| `23P01` | Exclusión (cruce de reservas o turnos) | 409 | `{"codigo":"cruce"}` |
| `23514` | Restricción CHECK | 422 | `{"codigo":"valor_invalido"}` |
| `23503` | Llave foránea | 422 | `{"codigo":"referencia_invalida"}` |
| `40001`, `40P01` | Serialización o interbloqueo | 503 con reintento | El cliente reintenta con espera |

### 10.4 Sincronización sin conexión

1. La PWA genera un UUIDv7 (`id_cliente`) por registro y lo guarda en la cola de IndexedDB con la fecha del dispositivo.
2. Al volver la señal envía lotes de hasta 200 registros a `POST /api/v1/sincronizacion/lote/`.
3. El servidor inserta cada registro con `ON CONFLICT (id_cliente) DO NOTHING (la columna es única en toda la tabla)` y responde por registro: creado, repetido o rechazado con el mensaje de la regla.
4. La PWA borra de la cola lo creado y lo repetido y muestra lo rechazado para que la persona lo corrija.
5. Las 35 tablas con captura sin conexión están listadas en el diccionario (columna `id_cliente`).

### 10.5 Pruebas

| Nivel | Herramienta | Qué prueba |
| --- | --- | --- |
| Reglas de la base | `pruebas_reglas_v4.sql` y `pruebas_reglas_v5.sql` | Las 305 pruebas de reglas, con el rol de la API |
| Servicios y API | pytest y pytest-django sobre una base cargada | Cada caso de uso: flujo principal y cada flujo alterno |
| Contrato | drf-spectacular + schemathesis | Que la API cumpla su OpenAPI |
| Frontend | Jest o Karma para componentes; Playwright para los flujos de campo | Incluye el modo sin conexión |
| Carga | k6 en CI nocturno | RNF-02: respuesta menor a 2 segundos |

### 10.6 Definición de terminado

Un caso de uso está terminado cuando: el flujo principal y los alternos tienen prueba y pasan; el endpoint aparece en OpenAPI; la pantalla funciona en un celular de gama media (y sin conexión si aplica); los mensajes son los de la base; CI está en verde; el README de la app y la pestaña del caso de uso se actualizaron si algo cambió; y otra persona lo revisó.

## 11. Plan por fases y sprints

Sprints de dos semanas. Las fases son las del catálogo (79 casos de uso en la fase 1, 77 en la 2, 11 en la 3 y 10 en la 4). Cada sprint cierra con una demostración en la finca de práctica y una revisión de lecciones aprendidas, como pide el módulo de proyectos.

| Sprint | Fase | Casos de uso | Resultado |
| --- | --- | --- | --- |
| 0 | 1 | Entorno, CI, esqueleto, NUC-02, SEG-01, SEG-02 | Ingreso con doble factor sobre la base real |
| 1 | 1 | NUC-01, NUC-03, NUC-04, NUC-08, NUC-09, SEG-03 a SEG-07, TER-01 a TER-04 | Finca, zonas, funciones, seguridad y terceros con consentimiento |
| 2 | 1 | NUC-05, NUC-06, DOC-01 a DOC-03 | PWA instalable con sincronización; gestor documental |
| 3 | 1 | PRO-01 a PRO-05 | Lotes, postura, mortalidad y labores desde el celular |
| 4 | 1 | PRO-06 a PRO-10, RIE-01, RIE-02, CUM-01 a CUM-04, CUM-07 | Cosecha, bioinsumos, riego manual y granja biosegura |
| 5 | 1 | INV-01 a INV-06, CMP-01 a CMP-04 | Inventario FEFO y compras con documento soporte |
| 6 | 1 | VTA-01 a VTA-03, VTA-05 a VTA-07, VTA-11, VTA-12, FIN-01 a FIN-04 | Ventas, factura, trazabilidad QR y contabilidad básica |
| 7 | 1 | PER-01 a PER-06, PER-09, PER-10 | Tareas con evidencia, jornada y áreas |
| 8 | 1 | RED-01 a RED-03, RED-06, IA-01 a IA-06 | Atención por WhatsApp con agentes y bandeja de aprobaciones |
| 9 | 2 | NUC-07, INV-07, VTA-04, VTA-08 a VTA-10 | Punto de venta sin conexión, cartera y pedidos recurrentes |
| 10 | 2 | FOR-01 a FOR-09 | Formación y habilitaciones |
| 11 | 2 | NOM-01 a NOM-08, PER-07, PER-08 | Nómina y cronogramas 24/7 |
| 12 | 2 | ACT-01 a ACT-05, AMB-01 a AMB-03, SGR-01 a SGR-04 | Activos, ambiental y seguros |
| 13 | 2 | FIN-05 a FIN-11 | Costos, presupuesto, estados e indicadores |
| 14 | 2 | EST-01 a EST-08 | Estrategia y reinversión |
| 15 | 2 | PRY-01 a PRY-09 | Proyectos PMBOK 8 |
| 16 | 2 | CRM-01 a CRM-06, RED-04, RED-05, AGD-03 a AGD-06, CUM-05, CUM-06, IA-08, IA-09 | CRM, portería, auditorías y diagnóstico por foto |
| 17 | 3 | TUR-01 a TUR-06, AGD-01, AGD-02 | Turismo con reservas y pago |
| 18 | 3 | NUC-10, FIN-12, IA-07 | API B2B, informe para crédito y pronóstico |
| 19 | 4 | RIE-03, IOT-01 a IOT-05 | Riego automatizado y sensores |
| 20 | 4 | IOT-06 a IOT-09 | Cámaras, alarmas, robot y energía |

El orden dentro de cada fase puede cambiar con la familia; lo que no cambia es que la fase 1 va completa antes de abrir funciones de la fase 2 en producción.

## 12. Fuentes

| Fuente | Para qué se usó |
| --- | --- |
| Documento de requerimientos v1.0 de GuayacanERP | RF-01 a RF-22 y RNF-01 a RNF-14 |
| ADR 0002 a 0006 y `docs/arquitectura/patrones-de-diseno.md` | Decisiones de arquitectura y patrones |
| `specs/modelo-datos/esquema_postgresql.sql`, `generador/reglas_negocio.sql` y diccionarios v5 | Tablas, columnas y reglas citadas en cada caso de uso |
| `specs/casos-prueba/pruebas_reglas_v4.sql` y `pruebas_reglas_v5.sql` | Las pruebas que respaldan cada regla |
| Mapa de APIs y modelos v5 (Excel) | Endpoints CRUD y ruta manual de construcción |
| PMI, PMBOK Guide, 8.ª edición | Módulo de proyectos |
| ISO 21001:2018 | Módulo de formación |
| Ley 1581 de 2012 y Decreto 1377 de 2013 | Datos personales y consentimientos |
| Resolución ICA 3651 de 2014 | Granja avícola biosegura |
| Ley 2101 de 2021 y Ley 2466 de 2025 | Jornada, recargos y trabajo nocturno |
| OMG UML 2.5.1 | Notación de los diagramas |
