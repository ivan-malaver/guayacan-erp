# Diccionario de datos · MongoDB (v4)

Base `guayacan`. Regla: Mongo guarda referencias (`*_id` de PostgreSQL), nunca copias de precios, existencias ni saldos.
Todas las colecciones tienen `_id` y `predio_id` (finca dueña). MongoDB no tiene seguridad por filas, así que el repositorio de datos del servicio de agentes agrega `predio_id` a toda consulta y todos los índices empiezan por él.

## `conversaciones` · Fase 1

Una conversación con un cliente o visitante por un canal (WhatsApp, web, Instagram, Facebook). Agrupa los mensajes.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `canal` | string | sí | Canal de la conversación (redes.politica_canal) · valores: whatsapp, web_chat, instagram, messenger, tiktok |
| `origen_entrada` | string | no | Cómo llegó el cliente; un anuncio que abre chat amplía la ventana · valores: organico, anuncio, qr, enlace_perfil, comentario |
| `ultimo_mensaje_cliente_en` | date | no | Último mensaje del cliente: desde aquí corre la ventana del canal |
| `ventana_cierra_en` | date | no | Hasta cuándo puede responder el agente de IA sin plantilla |
| `ventana_humano_cierra_en` | date | no | Hasta cuándo puede responder una persona (Instagram y Messenger: 7 días) |
| `mensajes_en_ventana` | int | no | Mensajes enviados en la ventana actual (TikTok permite 10) |
| `escalamiento_id` | long | no | Escalamiento abierto (ia.escalamiento.id) |
| `identificador_canal` | string | sí | Número de WhatsApp o id del usuario en la plataforma (cifrado si es personal) |
| `tercero_id` | long | no | Tercero en PostgreSQL, cuando se identifica al cliente |
| `estado` | string | sí | Situación · valores: abierta, en_espera_humano, atendida_humano, fuera_de_ventana, cerrada |
| `agente_actual` | string | no | Código del agente que atiende (ia.agente.codigo) |
| `intencion` | string | no | Intención detectada por el orquestador · valores: consulta_producto, pedido, estado_pedido, turismo, queja, proveedor, otro |
| `resumen` | string | no | Resumen corto que actualiza el agente al cerrar (memoria de corto plazo) |
| `pedido_ids` | array | no | Pedidos creados en esta conversación (comercial.pedido.id) |
| `consentimiento_vigente` | bool | sí | Copia de control: si el cliente autorizó personalización al iniciar |
| `iniciada_en` | date | sí | Primer mensaje |
| `ultima_actividad_en` | date | sí | Último mensaje |

## `mensajes` · Fase 1

Cada mensaje de una conversación, del cliente, de un agente o de una persona del equipo. Los documentos se borran solos a los 730 días.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `conversacion_id` | objectId | sí | Conversación |
| `autor` | string | sí | Quién escribe · valores: cliente, agente, humano, sistema |
| `agente` | string | no | Código del agente, si lo escribió un agente |
| `usuario_id` | long | no | Usuario del equipo, si lo escribió una persona |
| `tipo` | string | sí | Tipo de contenido · valores: texto, imagen, audio, ubicacion, plantilla, botones |
| `texto` | string | no | Contenido de texto (o transcripción del audio) |
| `audio_url` | string | no | Nota de voz del cliente en el almacén de archivos (se conserva hasta su vencimiento) |
| `transcripcion` | string | no | Texto obtenido del audio por el servicio de voz a texto |
| `confianza_transcripcion` | double | no | Confianza del servicio de voz a texto, de 0 a 1; si es baja, el agente pide confirmar |
| `proveedor_voz_texto` | string | no | Servicio de voz a texto usado (intercambiable) |
| `pieza_audiovisual_id` | long | no | Video aprobado que el asesor adjuntó (redes.pieza_audiovisual) |
| `adjuntos` | array | no | Rutas en MinIO de imágenes o audios |
| `herramientas_usadas` | array | no | Herramientas que el agente invocó para responder (códigos) |
| `ejecucion_id` | objectId | no | Registro en bitacora_agentes con el detalle |
| `enviado_en` | date | sí | Momento |

## `perfiles_interes` · Fase 1

Lo que se sabe de los intereses de cada cliente para personalizar ofertas. Solo se llena si su consentimiento de personalización está vigente.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `tercero_id` | long | sí | Cliente (terceros.tercero.id) |
| `intereses` | array | sí | Lista de productos o temas con puntaje: {producto_id, tema, puntaje 0-1, fuente, actualizado_en} |
| `intereses.fuente` | string | no | De dónde salió el interés · valores: compra, conversacion, interaccion_pagina_finca, declarado |
| `preferencias_declaradas` | object | no | Lo que el cliente dijo explícitamente (presentación, día de entrega, alergias que mencione) |
| `canal_preferido` | string | no | Canal por el que más responde |
| `horario_preferido` | string | no | Franja en que suele comprar |
| `segmentos` | array | no | Segmentos calculados (ej. comprador_semanal_huevo) |
| `resumen_memoria` | string | no | Memoria de largo plazo en lenguaje natural que lee el vendedor personalizado |
| `consentimiento_id` | long | sí | Consentimiento que lo autoriza (terceros.consentimiento_datos.id) |
| `actualizado_en` | date | sí | Última actualización |

## `eventos_redes` · Fase 2

Interacciones con las cuentas de la finca (comentarios, reacciones, mensajes, menciones), leídas con las API oficiales. No incluye perfiles personales ajenos. Los documentos se borran solos a los 730 días.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `plataforma` | string | sí | Red social · valores: facebook_pagina, instagram, messenger, tiktok, whatsapp |
| `tipo` | string | sí | Tipo de interacción · valores: comentario, reaccion, mensaje, mencion, compartido, resena |
| `respuesta_privada_hasta` | date | no | Instagram: plazo de 7 días para la única respuesta privada a un comentario |
| `publicacion_id` | long | no | Publicación de la finca (redes.publicacion.id) |
| `autor_hash` | string | sí | Identificador del autor cifrado con hash (no se guarda el nombre) |
| `tercero_id` | long | no | Cliente, si se pudo vincular con su autorización |
| `texto` | string | no | Texto del comentario o mensaje |
| `sentimiento` | string | no | Sentimiento calculado · valores: positivo, neutro, negativo |
| `temas` | array | no | Temas detectados (huevo, precio, entrega, turismo...) |
| `respondido` | bool | sí | Si ya se respondió |
| `ocurrido_en` | date | sí | Momento |

## `metricas_redes` · Fase 2

Métricas diarias de cada publicación y cuenta (alcance, impresiones, interacciones, seguidores).

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `plataforma` | string | sí | Red social |
| `cuenta_red_id` | long | sí | Cuenta (redes.cuenta_red.id) |
| `publicacion_id` | long | no | Publicación, si es métrica de una publicación |
| `fecha` | date | sí | Día |
| `metricas` | object | sí | Valores: alcance, impresiones, me_gusta, comentarios, compartidos, clics, seguidores_nuevos |

## `bitacora_agentes` · Fase 1

Registro detallado de cada ejecución de un agente: qué recibió, qué herramientas usó, qué respondió, cuánto costó y cuánto tardó. Base para auditar y mejorar. Los documentos se borran solos a los 365 días.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `agente` | string | sí | Código del agente |
| `version_instrucciones` | string | sí | Versión de instrucciones usada |
| `modelo` | string | sí | Modelo usado |
| `disparador` | string | sí | Qué la inició · valores: mensaje, tarea_programada, evento, humano |
| `entrada_resumen` | string | sí | Resumen de la entrada (sin datos sensibles) |
| `pasos` | array | sí | Secuencia {herramienta, parametros, resultado_resumen, duracion_ms} |
| `salida_resumen` | string | no | Resumen de la respuesta |
| `tokens_entrada` | int | sí | Tokens enviados |
| `tokens_salida` | int | sí | Tokens generados |
| `costo_usd` | double | sí | Costo |
| `latencia_ms` | int | sí | Duración total |
| `error` | string | no | Error, si lo hubo |
| `ejecutado_en` | date | sí | Momento |

## `informes_mercado` · Fase 1

Informe que genera el analista de mercados: precios comparados, proveedores, conclusiones y propuestas creadas.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `periodo` | string | sí | Periodo analizado, ej. 2026-10-S4 |
| `productos` | array | sí | Por producto: {producto_id, precio_finca, precio_mercado, costo_unitario, margen, tendencia} |
| `proveedores` | array | no | Comparación de proveedores: {producto_id, proveedor, precio, fecha, fuente} |
| `fuentes` | array | sí | Fuentes consultadas con enlace y fecha |
| `conclusiones` | string | sí | Conclusiones en lenguaje claro |
| `propuestas_precio_ids` | array | no | Propuestas creadas (comercial.propuesta_precio.id) |
| `generado_en` | date | sí | Momento |

## `tendencias` · Fase 2

Resultado del análisis periódico de redes y conversaciones: temas en alza, preguntas frecuentes, horarios, productos más consultados.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `periodo` | string | sí | Periodo |
| `temas` | array | sí | {tema, menciones, variacion, sentimiento} |
| `productos_consultados` | array | sí | {producto_id, consultas, conversion_pedido} |
| `preguntas_frecuentes` | array | no | Preguntas que más se repiten (para la base de conocimiento) |
| `recomendacion_ids` | array | no | Recomendaciones creadas (ia.recomendacion.id) |
| `generado_en` | date | sí | Momento |
