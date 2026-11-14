"""Colecciones MongoDB de GuayacanERP: genera validadores $jsonSchema, script mongosh y diccionario."""
import json, csv, sys, os
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')

# (coleccion, fase, descripcion, campos[(ruta, tipo, obligatorio, significado, enum)], indices, ttl_dias)
C = [
 ('conversaciones', 1, 'Una conversación con un cliente o visitante por un canal (WhatsApp, web, Instagram, Facebook). Agrupa los mensajes.', [
   ('canal', 'string', True, 'Canal de la conversación (redes.politica_canal)', ['whatsapp', 'web_chat', 'instagram', 'messenger', 'tiktok']),
   ('origen_entrada', 'string', False, 'Cómo llegó el cliente; un anuncio que abre chat amplía la ventana', ['organico', 'anuncio', 'qr', 'enlace_perfil', 'comentario']),
   ('ultimo_mensaje_cliente_en', 'date', False, 'Último mensaje del cliente: desde aquí corre la ventana del canal', None),
   ('ventana_cierra_en', 'date', False, 'Hasta cuándo puede responder el agente de IA sin plantilla', None),
   ('ventana_humano_cierra_en', 'date', False, 'Hasta cuándo puede responder una persona (Instagram y Messenger: 7 días)', None),
   ('mensajes_en_ventana', 'int', False, 'Mensajes enviados en la ventana actual (TikTok permite 10)', None),
   ('escalamiento_id', 'long', False, 'Escalamiento abierto (ia.escalamiento.id)', None),
   ('identificador_canal', 'string', True, 'Número de WhatsApp o id del usuario en la plataforma (cifrado si es personal)', None),
   ('tercero_id', 'long', False, 'Tercero en PostgreSQL, cuando se identifica al cliente', None),
   ('estado', 'string', True, 'Situación', ['abierta', 'en_espera_humano', 'atendida_humano', 'fuera_de_ventana', 'cerrada']),
   ('agente_actual', 'string', False, 'Código del agente que atiende (ia.agente.codigo)', None),
   ('intencion', 'string', False, 'Intención detectada por el orquestador', ['consulta_producto', 'pedido', 'estado_pedido', 'turismo', 'queja', 'proveedor', 'otro']),
   ('resumen', 'string', False, 'Resumen corto que actualiza el agente al cerrar (memoria de corto plazo)', None),
   ('pedido_ids', 'array', False, 'Pedidos creados en esta conversación (comercial.pedido.id)', None),
   ('consentimiento_vigente', 'bool', True, 'Copia de control: si el cliente autorizó personalización al iniciar', None),
   ('iniciada_en', 'date', True, 'Primer mensaje', None),
   ('ultima_actividad_en', 'date', True, 'Último mensaje', None),
 ], [{'canal': 1, 'identificador_canal': 1, 'ultima_actividad_en': -1}, {'tercero_id': 1}, {'estado': 1}], None),
 ('mensajes', 1, 'Cada mensaje de una conversación, del cliente, de un agente o de una persona del equipo.', [
   ('conversacion_id', 'objectId', True, 'Conversación', None),
   ('autor', 'string', True, 'Quién escribe', ['cliente', 'agente', 'humano', 'sistema']),
   ('agente', 'string', False, 'Código del agente, si lo escribió un agente', None),
   ('usuario_id', 'long', False, 'Usuario del equipo, si lo escribió una persona', None),
   ('tipo', 'string', True, 'Tipo de contenido', ['texto', 'imagen', 'audio', 'ubicacion', 'plantilla', 'botones']),
   ('texto', 'string', False, 'Contenido de texto (o transcripción del audio)', None),
   ('audio_url', 'string', False, 'Nota de voz del cliente en el almacén de archivos (se conserva hasta su vencimiento)', None),
   ('transcripcion', 'string', False, 'Texto obtenido del audio por el servicio de voz a texto', None),
   ('confianza_transcripcion', 'double', False, 'Confianza del servicio de voz a texto, de 0 a 1; si es baja, el agente pide confirmar', None),
   ('proveedor_voz_texto', 'string', False, 'Servicio de voz a texto usado (intercambiable)', None),
   ('pieza_audiovisual_id', 'long', False, 'Video aprobado que el asesor adjuntó (redes.pieza_audiovisual)', None),
   ('adjuntos', 'array', False, 'Rutas en MinIO de imágenes o audios', None),
   ('herramientas_usadas', 'array', False, 'Herramientas que el agente invocó para responder (códigos)', None),
   ('ejecucion_id', 'objectId', False, 'Registro en bitacora_agentes con el detalle', None),
   ('enviado_en', 'date', True, 'Momento', None),
 ], [{'conversacion_id': 1, 'enviado_en': 1}], 730),
 ('perfiles_interes', 1, 'Lo que se sabe de los intereses de cada cliente para personalizar ofertas. Solo se llena si su consentimiento de personalización está vigente.', [
   ('tercero_id', 'long', True, 'Cliente (terceros.tercero.id)', None),
   ('intereses', 'array', True, 'Lista de productos o temas con puntaje: {producto_id, tema, puntaje 0-1, fuente, actualizado_en}', None),
   ('intereses.fuente', 'string', False, 'De dónde salió el interés', ['compra', 'conversacion', 'interaccion_pagina_finca', 'declarado']),
   ('preferencias_declaradas', 'object', False, 'Lo que el cliente dijo explícitamente (presentación, día de entrega, alergias que mencione)', None),
   ('canal_preferido', 'string', False, 'Canal por el que más responde', None),
   ('horario_preferido', 'string', False, 'Franja en que suele comprar', None),
   ('segmentos', 'array', False, 'Segmentos calculados (ej. comprador_semanal_huevo)', None),
   ('resumen_memoria', 'string', False, 'Memoria de largo plazo en lenguaje natural que lee el vendedor personalizado', None),
   ('consentimiento_id', 'long', True, 'Consentimiento que lo autoriza (terceros.consentimiento_datos.id)', None),
   ('actualizado_en', 'date', True, 'Última actualización', None),
 ], [{'tercero_id': 1}], None),
 ('eventos_redes', 2, 'Interacciones con las cuentas de la finca (comentarios, reacciones, mensajes, menciones), leídas con las API oficiales. No incluye perfiles personales ajenos.', [
   ('plataforma', 'string', True, 'Red social', ['facebook_pagina', 'instagram', 'messenger', 'tiktok', 'whatsapp']),
   ('tipo', 'string', True, 'Tipo de interacción', ['comentario', 'reaccion', 'mensaje', 'mencion', 'compartido', 'resena']),
   ('respuesta_privada_hasta', 'date', False, 'Instagram: plazo de 7 días para la única respuesta privada a un comentario', None),
   ('publicacion_id', 'long', False, 'Publicación de la finca (redes.publicacion.id)', None),
   ('autor_hash', 'string', True, 'Identificador del autor cifrado con hash (no se guarda el nombre)', None),
   ('tercero_id', 'long', False, 'Cliente, si se pudo vincular con su autorización', None),
   ('texto', 'string', False, 'Texto del comentario o mensaje', None),
   ('sentimiento', 'string', False, 'Sentimiento calculado', ['positivo', 'neutro', 'negativo']),
   ('temas', 'array', False, 'Temas detectados (huevo, precio, entrega, turismo...)', None),
   ('respondido', 'bool', True, 'Si ya se respondió', None),
   ('ocurrido_en', 'date', True, 'Momento', None),
 ], [{'plataforma': 1, 'ocurrido_en': -1}, {'temas': 1}], 730),
 ('metricas_redes', 2, 'Métricas diarias de cada publicación y cuenta (alcance, impresiones, interacciones, seguidores).', [
   ('plataforma', 'string', True, 'Red social', None),
   ('cuenta_red_id', 'long', True, 'Cuenta (redes.cuenta_red.id)', None),
   ('publicacion_id', 'long', False, 'Publicación, si es métrica de una publicación', None),
   ('fecha', 'date', True, 'Día', None),
   ('metricas', 'object', True, 'Valores: alcance, impresiones, me_gusta, comentarios, compartidos, clics, seguidores_nuevos', None),
 ], [{'cuenta_red_id': 1, 'fecha': -1}], None),
 ('bitacora_agentes', 1, 'Registro detallado de cada ejecución de un agente: qué recibió, qué herramientas usó, qué respondió, cuánto costó y cuánto tardó. Base para auditar y mejorar.', [
   ('agente', 'string', True, 'Código del agente', None),
   ('version_instrucciones', 'string', True, 'Versión de instrucciones usada', None),
   ('modelo', 'string', True, 'Modelo usado', None),
   ('disparador', 'string', True, 'Qué la inició', ['mensaje', 'tarea_programada', 'evento', 'humano']),
   ('entrada_resumen', 'string', True, 'Resumen de la entrada (sin datos sensibles)', None),
   ('pasos', 'array', True, 'Secuencia {herramienta, parametros, resultado_resumen, duracion_ms}', None),
   ('salida_resumen', 'string', False, 'Resumen de la respuesta', None),
   ('tokens_entrada', 'int', True, 'Tokens enviados', None),
   ('tokens_salida', 'int', True, 'Tokens generados', None),
   ('costo_usd', 'double', True, 'Costo', None),
   ('latencia_ms', 'int', True, 'Duración total', None),
   ('error', 'string', False, 'Error, si lo hubo', None),
   ('ejecutado_en', 'date', True, 'Momento', None),
 ], [{'agente': 1, 'ejecutado_en': -1}], 365),
 ('informes_mercado', 1, 'Informe que genera el analista de mercados: precios comparados, proveedores, conclusiones y propuestas creadas.', [
   ('periodo', 'string', True, 'Periodo analizado, ej. 2026-10-S4', None),
   ('productos', 'array', True, 'Por producto: {producto_id, precio_finca, precio_mercado, costo_unitario, margen, tendencia}', None),
   ('proveedores', 'array', False, 'Comparación de proveedores: {producto_id, proveedor, precio, fecha, fuente}', None),
   ('fuentes', 'array', True, 'Fuentes consultadas con enlace y fecha', None),
   ('conclusiones', 'string', True, 'Conclusiones en lenguaje claro', None),
   ('propuestas_precio_ids', 'array', False, 'Propuestas creadas (comercial.propuesta_precio.id)', None),
   ('generado_en', 'date', True, 'Momento', None),
 ], [{'generado_en': -1}], None),
 ('tendencias', 2, 'Resultado del análisis periódico de redes y conversaciones: temas en alza, preguntas frecuentes, horarios, productos más consultados.', [
   ('periodo', 'string', True, 'Periodo', None),
   ('temas', 'array', True, '{tema, menciones, variacion, sentimiento}', None),
   ('productos_consultados', 'array', True, '{producto_id, consultas, conversion_pedido}', None),
   ('preguntas_frecuentes', 'array', False, 'Preguntas que más se repiten (para la base de conocimiento)', None),
   ('recomendacion_ids', 'array', False, 'Recomendaciones creadas (ia.recomendacion.id)', None),
   ('generado_en', 'date', True, 'Momento', None),
 ], [{'generado_en': -1}], None),
]


PREDIO = ('predio_id', 'long', True, 'Finca dueña del documento (nucleo.predio.id). MongoDB no tiene seguridad por filas: el servicio de agentes filtra siempre por este campo', None)


def schema(campos):
    """Construye el validador $jsonSchema de una colección: tipos, descripción, obligatorios y listas cerradas (enum)."""
    campos = [PREDIO] + list(campos)
    props, req = {}, []
    for ruta, tipo, obl, sig, enum in campos:
        if '.' in ruta:
            continue
        p = {'bsonType': tipo, 'description': sig}
        if enum:
            p['enum'] = enum
        props[ruta] = p
        if obl:
            req.append(ruta)
    return {'$jsonSchema': {'bsonType': 'object', 'required': req, 'properties': props}}


js = ['// GuayacanERP · Crear colecciones MongoDB con validación (generado; ejecutar con mongosh)', "db = db.getSiblingDB('guayacan');"]
allv = {}
for nombre, fase, desc, campos, idx, ttl in C:
    v = schema(campos)
    allv[nombre] = {'fase': fase, 'descripcion': desc, 'validador': v, 'indices': idx, 'ttl_dias': ttl}
    js.append(f'\n// {nombre}: {desc}')
    js.append(f"db.createCollection('{nombre}', {{ validator: {json.dumps(v, ensure_ascii=False)}, validationLevel: 'moderate' }});")
    for i in idx:
        js.append(f"db.{nombre}.createIndex({json.dumps({'predio_id': 1, **i})});")
    if ttl:
        campo = [c[0] for c in campos if c[1] == 'date'][-1]
        js.append(f"db.{nombre}.createIndex({{ {campo}: 1 }}, {{ expireAfterSeconds: {ttl * 86400} }}); // se borra a los {ttl} días")
os.makedirs(f'{OUT}/specs/modelo-datos', exist_ok=True)
open(f'{OUT}/specs/modelo-datos/colecciones_mongodb.js', 'w').write('\n'.join(js) + '\n')
json.dump(allv, open(f'{OUT}/specs/modelo-datos/colecciones_mongodb.json', 'w'), ensure_ascii=False, indent=2)
with open(f'{OUT}/specs/modelo-datos/diccionario_mongodb.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['coleccion', 'fase', 'campo', 'tipo', 'obligatorio', 'valores', 'significado'])
    for nombre, fase, desc, campos, idx, ttl in C:
        w.writerow([nombre, f'Fase {fase}', '_id', 'objectId', 'sí', '', 'Identificador que asigna MongoDB'])
        w.writerow([nombre, f'Fase {fase}', 'predio_id', 'long', 'sí', '', PREDIO[3]])
        for ruta, tipo, obl, sig, enum in campos:
            w.writerow([nombre, f'Fase {fase}', ruta, tipo, 'sí' if obl else 'no', ', '.join(enum or []), sig])
md = ['# Diccionario de datos · MongoDB (v4)', '', 'Base `guayacan`. Regla: Mongo guarda referencias (`*_id` de PostgreSQL), nunca copias de precios, existencias ni saldos.',
      'Todas las colecciones tienen `_id` y `predio_id` (finca dueña). MongoDB no tiene seguridad por filas, así que el repositorio de datos del servicio de agentes agrega `predio_id` a toda consulta y todos los índices empiezan por él.', '']
for nombre, fase, desc, campos, idx, ttl in C:
    md += [f'## `{nombre}` · Fase {fase}', '', desc + (f' Los documentos se borran solos a los {ttl} días.' if ttl else ''), '', '| Campo | Tipo | Obligatorio | Significado |', '| --- | --- | --- | --- |']
    for ruta, tipo, obl, sig, enum in campos:
        md.append(f"| `{ruta}` | {tipo} | {'sí' if obl else 'no'} | {sig}{(' · valores: ' + ', '.join(enum)) if enum else ''} |")
    md.append('')
open(f'{OUT}/specs/modelo-datos/diccionario_mongodb.md', 'w').write('\n'.join(md))
print(len(C), 'colecciones', sum(len(c[3]) for c in C), 'campos')
