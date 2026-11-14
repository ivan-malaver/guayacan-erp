-- GuayacanERP v5 · Datos iniciales (catálogos y situación real de la finca a octubre de 2026)
-- Ejecutar después de esquema_postgresql.sql. Las cifras de la finca son las reportadas por la familia.

begin;

-- Roles y usuario administrador (la contraseña real se define al instalar; este hash es un marcador)
insert into nucleo.rol (codigo, nombre, descripcion) values
 ('administrador', 'Administrador', 'Aprueba precios, pagos, publicaciones y acciones de los agentes'),
 ('operario_granja', 'Operario de granja', 'Registra postura, alimentación, sanidad, pesajes, riego y labores'),
 ('vendedor', 'Vendedor', 'Atiende clientes, crea pedidos y entregas'),
 ('contador', 'Contador', 'Revisa comprobantes, facturación e impuestos'),
 ('cliente', 'Cliente', 'Consulta catálogo, hace pedidos y ve su historial');

insert into nucleo.usuario (nombre_completo, correo, contrasena_hash, es_superusuario)
values ('Administrador GuayacanERP', 'admin@guayacan.local', 'argon2$POR_DEFINIR', true);
insert into nucleo.parametro (clave, valor, tipo_dato, vigente_desde, descripcion) values
 ('salario_minimo', '1750905', 'dinero', '2026-01-01', 'SMMLV 2026'),
 ('auxilio_transporte', '249095', 'dinero', '2026-01-01', 'Auxilio de transporte 2026'),
 ('iva_general', '19', 'porcentaje', '2026-01-01', 'Tarifa general de IVA'),
 ('margen_minimo_venta', '25', 'porcentaje', '2026-01-01', 'Ningún precio aprobado puede dejar un margen menor sobre el costo'),
 ('variacion_maxima_precio', '15', 'porcentaje', '2026-01-01', 'Variación máxima que un agente puede proponer en una sola propuesta'),
 ('vigencia_propuesta_horas', '72', 'entero', '2026-01-01', 'Horas para aprobar una propuesta antes de que venza');
-- Los anteriores son nacionales (predio_id vacío). Política de la finca aprobada por el administrador:


-- Predio y zonas (el predio es un catálogo compartido; lo demás pertenece a la finca)
insert into nucleo.predio (nombre, propietario, tenencia, area_m2, codigo_dane_municipio, vereda)
values ('El Guayacán de los Malaver', 'Alba Bibiana Gil Muñoz', 'comodato', 30025.70, '25488', 'Pueblo Nuevo');
-- Desde aquí todo se crea para esta finca (predio_id lo llena la base con la sesión)
select set_config('app.predio_id', (select id::text from nucleo.predio where nombre = 'El Guayacán de los Malaver'), false);
select set_config('app.usuario_id', (select id::text from nucleo.usuario where correo = 'admin@guayacan.local'), false);
insert into nucleo.usuario_rol (usuario_id, rol_id) select u.id, r.id from nucleo.usuario u, nucleo.rol r where r.codigo = 'administrador';
insert into nucleo.zona (predio_id, codigo, nombre, tipo_zona, area_m2) select p.id, z.codigo, z.nombre, z.tipo, z.area
from nucleo.predio p, (values
 ('LOT-PL', 'Lote de plátano', 'lote_cultivo', null::numeric),
 ('LOT-CA', 'Lote de cacao', 'lote_cultivo', null),
 ('LOT-AG', 'Lote de aguacate papelillo', 'lote_cultivo', null),
 ('LOT-CC', 'Lote de ciclo corto', 'lote_cultivo', null),
 ('EST-01', 'Estanque 1', 'estanque', 129),
 ('EST-02', 'Estanque 2', 'estanque', 94),
 ('RON-01', 'Ronda hídrica de la quebrada (30 m)', 'ronda_hidrica', 12488),
 ('BOD-01', 'Bodega', 'bodega', null)) as z(codigo, nombre, tipo, area);

-- Especies y cultivos
insert into produccion.especie (codigo, nombre_comun, nombre_cientifico, grupo, manejo_individual) values
 ('gallina', 'Gallina ponedora', 'Gallus gallus domesticus', 'ave', false),
 ('ovino', 'Oveja de pelo', 'Ovis aries', 'ovino', true),
 ('caprino', 'Cabra', 'Capra hircus', 'caprino', true),
 ('tilapia', 'Tilapia roja', 'Oreochromis sp.', 'pez', false),
 ('abeja', 'Abeja africanizada', 'Apis mellifera', 'abeja', false),
 ('lombriz', 'Lombriz roja californiana', 'Eisenia fetida', 'lombriz', false);
insert into produccion.cultivo (codigo, nombre_comun, nombre_cientifico, tipo_ciclo, dias_a_primera_cosecha) values
 ('platano', 'Plátano', 'Musa AAB', 'perenne', 330),
 ('cacao', 'Cacao', 'Theobroma cacao', 'perenne', 1095),
 ('aguacate', 'Aguacate', 'Persea americana', 'perenne', 1095),
 ('frijol', 'Fríjol', 'Phaseolus vulgaris', 'corto', 90),
 ('maiz', 'Maíz', 'Zea mays', 'corto', 120),
 ('calabacin', 'Calabacín', 'Cucurbita pepo', 'corto', 55),
 ('forraje', 'Forrajes (botón de oro, matarratón, pasto de corte)', null, 'forraje', 90);

-- Situación real de los cultivos (octubre de 2026)
insert into produccion.siembra (zona_id, cultivo_id, variedad, fecha_siembra, plantas_previstas, plantas_sembradas, plantas_vivas, estado, observaciones)
select z.id, c.id, s.variedad, s.fecha::date, s.prev, s.sem, s.vivas, s.estado, s.obs
from (values
 ('LOT-PL', 'platano', 'hartón', '2025-11-01', 5000, null::int, 600, 'recuperacion', 'Pérdidas por fenómeno de El Niño; producción esperada en unos 11 meses. Fecha de siembra aproximada'),
 ('LOT-CA', 'cacao', 'criollo (árboles viejos)', '2010-01-01', null, 150, 150, 'recuperacion', 'Árboles viejos en recuperación; última cosecha cerca de 65 kg. Fecha aproximada'),
 ('LOT-CA', 'cacao', null, '2026-06-01', null, null, null, 'sembrada', 'Siembra nueva con pérdidas por sequía y probable acidez del suelo (antiguo potrero). Fecha aproximada'),
 ('LOT-AG', 'aguacate', 'papelillo', '2026-10-15', 300, 300, 300, 'sembrada', 'Sembrados pocos días antes del registro. Fecha aproximada'),
 ('LOT-CC', 'frijol', null, '2026-10-01', null, null, null, 'sembrada', 'Siembra de prueba con 6 kg de semilla. Fecha aproximada')
) as s(zona, cultivo, variedad, fecha, prev, sem, vivas, estado, obs)
join nucleo.zona z on z.codigo = s.zona join produccion.cultivo c on c.codigo = s.cultivo;
update produccion.siembra set semilla_kg = 6 where cultivo_id = (select id from produccion.cultivo where codigo = 'frijol');

-- Agua y riego instalados: manguera con aspersores, dos tanques de 2.000 L y válvulas manuales
insert into riego.fuente_agua (nombre, tipo, requiere_concesion, apta_consumo_humano) values
 ('Nacedero de la finca', 'nacedero', true, false),
 ('Acueducto veredal Pueblo Nuevo', 'acueducto_veredal', false, false);
insert into riego.tanque (codigo, capacidad_litros, fuente_agua_id) select x.codigo, 2000, f.id
from (values ('TQ-01'), ('TQ-02')) as x(codigo), riego.fuente_agua f where f.tipo = 'nacedero';
insert into riego.sistema_riego (nombre, tipo, tanque_id, modo_control)
select 'Riego por aspersión con manguera', 'aspersion', t.id, 'manual' from riego.tanque t where t.codigo = 'TQ-01';
-- Las válvulas (una por aspersor) se registran al hacer el inventario físico: riego.valvula con tipo = 'manual'.

-- Inventario: unidades, categorías, productos de venta e insumos
insert into inventario.unidad_medida (codigo, nombre, unidad_base, factor_base) values
 ('und', 'Unidad', 'und', 1), ('cub30', 'Cubeta de 30 huevos', 'und', 30), ('kg', 'Kilogramo', 'kg', 1), ('bul40', 'Bulto de 40 kg', 'kg', 40), ('l', 'Litro', 'l', 1);
insert into inventario.categoria_producto (nombre) values ('Huevo'), ('Carne en pie'), ('Granos y hortalizas'), ('Frutas'), ('Alimento animal'), ('Sanidad animal'), ('Insumos agrícolas');
-- Vida útil y márgenes: valores iniciales a validar por la familia; el analista los ajusta con las mermas reales
insert into inventario.producto (sku, nombre, categoria_id, unidad_id, tipo, se_vende, se_compra, se_produce, perecedero,
  vida_util_ambiente_dias, vida_util_refrigerado_dias, dias_margen_venta, dias_alerta_venta, pesable, peso_nominal_kg, tolerancia_peso_pct, tarifa_iva)
select x.sku, x.nombre, c.id, u.id, x.tipo, x.v, x.c, x.p, x.per, x.amb, x.refr, x.marg, x.alerta, x.pes, x.peso, x.tol, 0
from (values
 ('HUE-AA-30', 'Huevo de gallinas en pastoreo AA · cubeta x 30', 'Huevo', 'cub30', 'producto_terminado', true, false, true, true, 21::smallint, 35::smallint, 5::smallint, 4::smallint, false, 1.950, 8.0),
 ('COR-PIE', 'Cordero en pie (kg)', 'Carne en pie', 'kg', 'producto_terminado', true, false, true, false, null, null, 0, 0, true, null, null),
 ('CAB-PIE', 'Cabrito en pie (kg)', 'Carne en pie', 'kg', 'producto_terminado', true, false, true, false, null, null, 0, 0, true, null, null),
 ('TIL-ROJ', 'Tilapia roja fresca (kg)', 'Carne en pie', 'kg', 'producto_terminado', true, false, true, true, 0, 3, 1, 1, true, null, null),
 ('FRI-KG', 'Fríjol (kg)', 'Granos y hortalizas', 'kg', 'producto_terminado', true, false, true, true, 180, 180, 15, 30, true, null, null),
 ('MAI-KG', 'Maíz (kg)', 'Granos y hortalizas', 'kg', 'producto_terminado', true, false, true, true, 180, 180, 15, 30, true, null, null),
 ('CAL-KG', 'Calabacín (kg)', 'Granos y hortalizas', 'kg', 'producto_terminado', true, false, true, true, 7, 14, 2, 2, true, null, null),
 ('PLA-KG', 'Plátano (kg)', 'Frutas', 'kg', 'producto_terminado', true, false, true, true, 10, 14, 2, 3, true, null, null),
 ('CAC-SEC', 'Cacao seco en grano (kg)', 'Granos y hortalizas', 'kg', 'producto_terminado', true, false, true, true, 365, 365, 30, 60, true, null, null),
 ('CON-POS', 'Concentrado de postura (bulto 40 kg)', 'Alimento animal', 'bul40', 'insumo', false, true, false, true, 90, 90, 0, 15, false, 40, 2.0),
 ('CAL-AGR', 'Cal agrícola (kg)', 'Insumos agrícolas', 'kg', 'insumo', false, true, false, false, null, null, 0, 0, true, null, null)
) as x(sku, nombre, cat, uni, tipo, v, c, p, per, amb, refr, marg, alerta, pes, peso, tol)
join inventario.categoria_producto c on c.nombre = x.cat join inventario.unidad_medida u on u.codigo = x.uni;
insert into inventario.bodega (codigo, nombre, zona_id) select 'B01', 'Bodega principal', id from nucleo.zona where codigo = 'BOD-01';

-- Listas y precios iniciales (referencias del plan de negocio, octubre de 2026)
insert into comercial.lista_precios (codigo, nombre) values ('PUBLICO', 'Precio al público'), ('TIENDAS', 'Tiendas y restaurantes');
insert into comercial.precio_producto (lista_precios_id, producto_id, precio_unitario, vigente_desde, aprobado_por)
select l.id, p.id, x.precio, '2026-10-25', (select id from nucleo.usuario where es_superusuario limit 1)
from (values ('HUE-AA-30', 19500), ('COR-PIE', 11500), ('CAB-PIE', 11500), ('TIL-ROJ', 13000), ('FRI-KG', 6000), ('MAI-KG', 2000), ('CAL-KG', 2500), ('PLA-KG', 3900), ('CAC-SEC', 16000)) as x(sku, precio)
join inventario.producto p on p.sku = x.sku, comercial.lista_precios l where l.codigo = 'PUBLICO';

insert into nucleo.parametro (predio_id, clave, valor, tipo_dato, vigente_desde, descripcion) values
 (nucleo.predio_actual(), 'descuento_por_vencer_pct', '15', 'porcentaje', '2026-10-25', 'Descuento de liquidación para lotes en alerta amarilla; política aprobada por el administrador, la aplica una regla fija');

-- Periodos contables abiertos
insert into finanzas.periodo_contable (anio, mes) values (2026, 10), (2026, 11), (2026, 12);

-- Centros de costo y cuentas PUC básicas
insert into finanzas.centro_costo (codigo, nombre) values
 ('AVI', 'Avícola'), ('OVC', 'Ovino-caprino'), ('PIS', 'Piscícola'), ('CCO', 'Ciclo corto y forrajes'), ('PER', 'Perennes (plátano, cacao, aguacate)'), ('TUR', 'Turismo'), ('ADM', 'Administración');
insert into finanzas.cuenta_contable (codigo, nombre, naturaleza, nivel, acepta_movimiento) values
 ('1105', 'Caja', 'debito', 3, true), ('1110', 'Bancos', 'debito', 3, true), ('1305', 'Clientes', 'debito', 3, true),
 ('1430', 'Productos terminados', 'debito', 3, true), ('1455', 'Materiales, repuestos y accesorios', 'debito', 3, true),
 ('2205', 'Proveedores nacionales', 'credito', 3, true), ('4120', 'Ingresos agricultura, ganadería, caza y silvicultura', 'credito', 3, true),
 ('6120', 'Costo de ventas agricultura, ganadería', 'debito', 3, true), ('5105', 'Gastos de personal', 'debito', 3, true);

-- Agentes de IA (instrucciones completas en el repositorio: servicios/agentes/instrucciones/<codigo>.md)
insert into ia.agente (codigo, nombre, rol, nivel_autonomia, proveedor_modelo, modelo, version_instrucciones, instrucciones, limite_costo_diario_usd) values
 ('orquestador', 'Orquestador', 'Recibe cada mensaje, identifica la intención y lo pasa al agente adecuado; nunca responde temas que no conoce', 'solo_lectura', 'anthropic', 'claude-haiku-5-5', '1.0', 'Ver instrucciones/orquestador.md', 2),
 ('asesor_clientes', 'Asesor virtual', 'Atiende clientes por WhatsApp y web: catálogo, precios vigentes, disponibilidad, pedidos y estado de entregas', 'propone', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/asesor_clientes.md', 5),
 ('guia_virtual', 'Guía virtual', 'Explica la finca, sus procesos y planes turísticos; acompaña visitas con información', 'solo_lectura', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/guia_virtual.md', 3),
 ('vendedor_personalizado', 'Vendedor personalizado', 'Ofrece a cada cliente lo que coincide con sus intereses y su historial, solo si autorizó la personalización', 'propone', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/vendedor_personalizado.md', 5),
 ('gestor_redes', 'Gestor de redes', 'Responde comentarios, redacta publicaciones para aprobación y analiza tendencias de las cuentas de la finca', 'propone', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/gestor_redes.md', 4),
 ('analista_mercados', 'Analista de mercados y proveedores', 'Compara precios de mercado y de proveedores, propone compras y cambios de precio con evidencia', 'propone', 'anthropic', 'claude-opus-5-5', '1.0', 'Ver instrucciones/analista_mercados.md', 5),
 ('analista_negocio', 'Analista de negocio', 'Calcula indicadores, detecta problemas y propone planes de acción y mejora continua (PHVA)', 'propone', 'anthropic', 'claude-opus-5-5', '1.0', 'Ver instrucciones/analista_negocio.md', 5),
 ('asistente_contable', 'Asistente contable', 'Revisa comprobantes, concilia pagos, alerta vencimientos tributarios y prepara informes; no contabiliza ni factura', 'propone', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/asistente_contable.md', 3);

insert into ia.herramienta (codigo, descripcion, tipo, requiere_aprobacion, esquema_entrada) values
 ('consultar_catalogo', 'Devuelve productos a la venta con precio vigente y cantidad disponible (vista v_catalogo_disponible)', 'lectura', false, '{"type":"object","properties":{"lista":{"type":"string"},"texto":{"type":"string"}}}'),
 ('consultar_pedido', 'Estado de un pedido del cliente que pregunta', 'lectura', false, '{"type":"object","required":["numero"],"properties":{"numero":{"type":"string"}}}'),
 ('crear_pedido_borrador', 'Crea un pedido en estado borrador; lo confirma el cliente y lo revisa un vendedor', 'escritura', false, '{"type":"object","required":["cliente_id","lineas"]}'),
 ('buscar_conocimiento', 'Busca en la base de conocimiento por significado (RAG)', 'lectura', false, '{"type":"object","required":["pregunta"],"properties":{"pregunta":{"type":"string"}}}'),
 ('consultar_perfil_interes', 'Lee intereses del cliente solo si su consentimiento de personalización está vigente', 'lectura', false, '{"type":"object","required":["tercero_id"]}'),
 ('consultar_precios_mercado', 'Precios de referencia (SIPSA, Corabastos) y cotizaciones de proveedores', 'lectura', false, '{"type":"object","properties":{"producto_id":{"type":"integer"},"desde":{"type":"string","format":"date"}}}'),
 ('proponer_precio', 'Crea una propuesta de precio con justificación y evidencia; queda pendiente de aprobación', 'propuesta', true, '{"type":"object","required":["producto_id","lista","precio_propuesto","justificacion","evidencia"]}'),
 ('proponer_publicacion', 'Crea un borrador de publicación para redes; se publica solo con aprobación', 'propuesta', true, '{"type":"object","required":["cuenta","texto"]}'),
 ('responder_comentario', 'Responde un comentario público con plantillas aprobadas', 'escritura', false, '{"type":"object","required":["evento_id","texto"]}'),
 ('consultar_indicadores', 'Indicadores de producción, ventas y costos por periodo y centro de costo', 'lectura', false, '{"type":"object","properties":{"desde":{"type":"string"},"hasta":{"type":"string"}}}'),
 ('crear_recomendacion', 'Registra un plan de acción o de mejora con evidencia', 'propuesta', false, '{"type":"object","required":["tipo","titulo","descripcion","evidencia","prioridad"]}'),
 ('consultar_contabilidad', 'Saldos, comprobantes y vencimientos tributarios (solo lectura)', 'lectura', false, '{"type":"object"}'),
 ('escalar_a_humano', 'Pasa la conversación a una persona y la avisa', 'escritura', false, '{"type":"object","required":["motivo"]}'),
 ('consultar_vencimientos', 'Lotes en alerta de vencimiento con precio de liquidación (vista v_alertas_vencimiento)', 'lectura', false, '{"type":"object","properties":{"semaforo":{"type":"string","enum":["amarillo","rojo"]}}}'),
 ('consultar_politica_canal', 'Reglas del canal de la conversación: ventana, plantillas y tope de mensajes', 'lectura', false, '{"type":"object","required":["plataforma"]}');

insert into ia.agente_herramienta (agente_id, herramienta_id)
select a.id, h.id from ia.agente a join ia.herramienta h on (a.codigo, h.codigo) in (
 ('orquestador', 'escalar_a_humano'),
 ('asesor_clientes', 'consultar_catalogo'), ('asesor_clientes', 'consultar_pedido'), ('asesor_clientes', 'crear_pedido_borrador'), ('asesor_clientes', 'buscar_conocimiento'), ('asesor_clientes', 'escalar_a_humano'),
 ('guia_virtual', 'buscar_conocimiento'), ('guia_virtual', 'escalar_a_humano'),
 ('vendedor_personalizado', 'consultar_catalogo'), ('vendedor_personalizado', 'consultar_perfil_interes'), ('vendedor_personalizado', 'consultar_vencimientos'),
 ('asesor_clientes', 'consultar_vencimientos'), ('asesor_clientes', 'consultar_politica_canal'), ('orquestador', 'consultar_politica_canal'),
 ('analista_mercados', 'consultar_vencimientos'), ('vendedor_personalizado', 'crear_pedido_borrador'), ('vendedor_personalizado', 'escalar_a_humano'),
 ('gestor_redes', 'proponer_publicacion'), ('gestor_redes', 'responder_comentario'), ('gestor_redes', 'buscar_conocimiento'), ('gestor_redes', 'crear_recomendacion'), ('gestor_redes', 'escalar_a_humano'),
 ('analista_mercados', 'consultar_precios_mercado'), ('analista_mercados', 'consultar_catalogo'), ('analista_mercados', 'proponer_precio'), ('analista_mercados', 'crear_recomendacion'),
 ('analista_negocio', 'consultar_indicadores'), ('analista_negocio', 'crear_recomendacion'),
 ('asistente_contable', 'consultar_contabilidad'), ('asistente_contable', 'consultar_indicadores'), ('asistente_contable', 'crear_recomendacion'));

-- Reglas de cada canal, verificadas el 2026-10-25 (actualizar cuando el proveedor cambie su política)
insert into redes.politica_canal (plataforma, ventana_horas, ventana_agente_humano_horas, ventana_anuncio_horas, max_mensajes_por_ventana,
  empresa_puede_iniciar, requiere_plantilla_fuera_ventana, cobra_por_mensaje, mensajes_servicio_gratis_mes, disponible, fuente_url, verificado_en) values
 ('whatsapp', 24, null, 168, null, true, true, true, 1000, true, 'https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing', '2026-10-25'),
 ('instagram', 24, 168, 168, null, false, false, false, null, true, 'https://setsmart.io/blog/instagram-messaging-api', '2026-10-25'),
 ('messenger', 24, 168, null, null, false, true, false, null, true, 'https://respond.io/help/facebook-messenger/message-tag', '2026-10-25'),
 ('tiktok', 48, null, null, 10, false, false, false, null, true, 'https://respond.io/help/tiktok/tiktok-overview', '2026-10-25'),
 ('web_chat', null, null, null, null, false, false, false, null, true, null, '2026-10-25'),
 ('facebook_pagina', null, null, null, null, false, false, false, null, true, null, '2026-10-25');

-- Guardia del orquestador: la IA solo atiende temas de la finca (política de WhatsApp desde enero de 2026)
insert into ia.regla_conversacion (tipo, descripcion, ejemplos, respuesta_plantilla, prioridad_escalamiento) values
 ('tema_permitido', 'Productos, precios vigentes, disponibilidad, pedidos, entregas, pagos, horarios, ubicación y visitas a la finca', '["¿tienen huevo?","¿cuánto vale la tilapia?","¿llegan a Girardot?"]', null, null),
 ('tema_permitido', 'Cómo se produce en la finca: gallinas en pastoreo, riego, cultivos, cuidado ambiental; planes turísticos cuando existan', '["¿las gallinas están sueltas?","¿se puede visitar?"]', null, null),
 ('tema_fuera_de_alcance', 'Preguntas generales sin relación con la finca: tareas, noticias, política, salud, programación, traducciones, otros negocios', '["hazme una tarea","¿quién ganó el partido?","escribe un poema"]',
  'Gracias por escribirnos. Este chat atiende solo temas de El Guayacán de los Malaver: productos, pedidos, entregas y visitas. ¿Le ayudo con algo de eso o prefiere hablar con una persona del equipo?', null),
 ('escalar_a_humano', 'El cliente pide hablar con una persona, está molesto o presenta una queja', '["quiero hablar con alguien","esto es una estafa","llegó roto"]', null, 'alta'),
 ('escalar_a_humano', 'Pagos, devoluciones, pedidos grandes o fuera de lo común, y preguntas que la base de conocimiento no responde', '["les transferí","quiero 40 cubetas","¿me fían?"]', null, 'media'),
 ('dato_prohibido', 'Nunca pedir ni guardar números de tarjeta, claves, códigos de verificación ni documentos completos por chat', '["mi tarjeta es...","el código que me llegó es..."]',
  'Por seguridad no recibimos datos de tarjetas ni claves por este chat. Los pagos se hacen por Nequi, Daviplata o transferencia con la referencia del pedido.', 'alta');

-- ============================================================================ v4
-- Funciones por finca: lo que espera equipo o decisión queda construido y apagado
insert into nucleo.funcionalidad (codigo, descripcion, fase, requiere_equipo, activa) values
 ('modo_aprendiz', 'Finca de práctica y tutoriales para aprender sin tocar la finca real', 1, null, true),
 ('pedidos_recurrentes', 'Pedidos que se repiten para tiendas, restaurantes y hoteles', 2, null, false),
 ('venta_credito', 'Venta a crédito con cupo, plazo y bloqueo por mora', 2, null, false),
 ('permuta', 'Trueque formal con factura y documento soporte que se compensan', 2, null, false),
 ('cadena_frio_finca', 'Neveras de la finca vigiladas con sensor; bloqueo automático de lotes', 2, 'Nevera solar y sensor de temperatura DS18B20', false),
 ('cadena_frio_transporte', 'Temperatura del vehículo de entregas con registrador que guarda sin señal', 2, 'Caja térmica y registrador de temperatura', false),
 ('notas_voz', 'Registro en campo por nota de voz con confirmación', 2, null, false),
 ('videos_promocionales', 'Videos y time-lapse para redes con aprobación humana', 2, 'Cámara o celular para time-lapse', false),
 ('pronostico_demanda', 'Pronóstico de demanda por producto', 3, 'Doce meses de ventas registradas', false),
 ('riego_automatico', 'Riego por reglas en la red local', 4, 'Electroválvulas, nodos ESP32 o PLC y pasarela solar', false),
 ('estacion_meteorologica', 'Suspender el riego si llovió', 4, 'Estación meteorológica', false),
 ('seguridad_perimetral', 'Alarma por zonas, sirena, reflectores y avisos', 4, 'Sensores, sirena, central y pasarela', false),
 ('camaras', 'Grabación por movimiento en la pasarela y clips a la nube', 4, 'Cámaras IP y almacenamiento local', false),
 ('camara_termica', 'Detección de presencia con cámara térmica (interfaz DetectorPresencia lista)', 4, 'Cámaras térmicas', false),
 ('reconocimiento_facial', 'Acceso facial solo con autorización expresa; siempre con PIN o tarjeta como alternativa', 4, 'Lector con cámara en la bodega', false),
 ('vision_artificial', 'Clasificación de huevos y detección de eventos con visión', 4, 'Cámara y equipo de cómputo en la pasarela', false),
 ('gemelo_3d', 'Gemelo digital 3D sobre el mismo servicio del mapa 2D', 4, 'Levantamiento 3D de la finca', false),
 ('anclaje_blockchain', 'Anclar la cadena de huellas de trazabilidad en una red externa', 4, 'Red exigida por el comprador', false);

-- Categorías del huevo por peso (rangos de la NTC 1240; verificar la versión vigente antes de producción)
insert into produccion.categoria_huevo (codigo, peso_min_g, peso_max_g, norma, vigente_desde) values
 ('jumbo', 78, null, 'NTC 1240 (por verificar)', '2026-01-01'),
 ('aaa', 67, 78, 'NTC 1240 (por verificar)', '2026-01-01'),
 ('aa', 60, 67, 'NTC 1240 (por verificar)', '2026-01-01'),
 ('a', 53, 60, 'NTC 1240 (por verificar)', '2026-01-01'),
 ('b', 46, 53, 'NTC 1240 (por verificar)', '2026-01-01'),
 ('c', 0, 46, 'NTC 1240 (por verificar)', '2026-01-01');

-- Abonos producidos en la finca
insert into inventario.categoria_producto (nombre) values ('Abonos orgánicos');
insert into inventario.producto (sku, nombre, categoria_id, unidad_id, tipo, se_vende, se_produce, perecedero)
select 'ABO-HUMUS-KG', 'Humus de lombriz por kilo', c.id, u.id, 'producto_terminado', true, true, false
from inventario.categoria_producto c, inventario.unidad_medida u where c.nombre = 'Abonos orgánicos' and u.codigo = 'kg';

-- Nevera (se usará cuando exista): rango supuesto 1 a 8 °C, a validar con la familia
insert into inventario.bodega (codigo, nombre, zona_id, refrigerada, temperatura_min_c, temperatura_max_c, minutos_tolerancia)
select 'NEV-01', 'Nevera solar (prevista)', id, true, 1, 8, 30 from nucleo.zona where codigo = 'BOD-01';
insert into inventario.vehiculo (codigo, tipo, refrigerado) values ('CAM-01', 'camioneta', false);

-- Zonas de seguridad previstas (fase 4)
insert into iot.zona_seguridad (zona_id, codigo, nombre, tipo, paso_personas, bioseguridad)
select z.id, x.codigo, x.nombre, x.tipo, x.paso, x.bio from (values
  ('BOD-01', 'SEG-BOD-01', 'Bodega de concentrado', 'bodega', false, false),
  (null, 'SEG-ACC-01', 'Acceso principal', 'acceso', true, false)) as x(zona, codigo, nombre, tipo, paso, bio)
left join nucleo.zona z on z.codigo = x.zona;

-- Particiones de los próximos meses (después, la tarea mensual nucleo.mantener_particiones)
select nucleo.mantener_particiones(3);

-- Finca de práctica para el modo aprendiz (aislada por la seguridad por filas)
insert into nucleo.predio (nombre, tenencia, codigo_dane_municipio, vereda, es_practica)
values ('Finca de práctica', 'otro', '25488', 'Pueblo Nuevo', true);
insert into nucleo.usuario_rol (predio_id, usuario_id, rol_id)
select p.id, u.id, r.id from nucleo.predio p, nucleo.usuario u, nucleo.rol r
where p.es_practica and u.correo = 'admin@guayacan.local' and r.codigo = 'administrador';

-- ============================================================================
-- v5 · Operación integral: personal, nómina, formación, activos, cumplimiento, seguros, seguridad, CRM y estrategia
-- Decisiones pendientes de la familia quedan configurables o apagadas (ver docs/adr/0006).
-- ============================================================================
select set_config('app.predio_id', (select id::text from nucleo.predio where nombre = 'El Guayacán de los Malaver'), false);

-- Funciones nuevas, apagadas hasta tener el trámite, el equipo o la decisión
insert into nucleo.funcionalidad (codigo, descripcion, fase, requiere_equipo, activa) values
 ('nomina_electronica', 'Transmitir el documento soporte de nómina electrónica (DIAN)', 2, 'Confirmar con el contador si la finca está obligada y elegir proveedor o servicio gratuito DIAN', false),
 ('diagnostico_imagen', 'Diagnóstico de plagas y enfermedades por foto con el agente Agrónomo', 2, null, false),
 ('api_b2b', 'API con llave para clientes HORECA', 3, 'Un cliente que la pida', false),
 ('webhooks_salientes', 'Eventos firmados a sistemas de compradores y logística', 3, null, false),
 ('indicadores_credito', 'Informe de indicadores verificables para Finagro, bancos y gremios', 3, null, false),
 ('cursos_externos', 'Cursos en Moodle u otra plataforma conectada por API', 3, 'Plataforma de cursos', false),
 ('dron_monitoreo', 'Misiones de dron para fotos y conteos (RAC 100)', 4, 'Dron registrado, piloto certificado y póliza', false),
 ('robot_campo', 'Piloto de robot de campo por la interfaz RobotCampo', 4, 'Convenio con una universidad', false),
 ('certificacion_bpa', 'Expediente de Buenas Prácticas Agrícolas (ICA 30021 de 2017)', 2, 'Un comprador que la pida', false),
 ('globalgap', 'Expediente GLOBALG.A.P. IFA v6', 4, 'Un comprador o exportador que la exija', false),
 ('seguro_parametrico', 'Pólizas paramétricas: vigilar el índice y armar evidencia', 2, 'Póliza paramétrica contratada', false);

-- Parámetros de nómina (nacionales; confirmar con el contador cada año) y de la finca
insert into nucleo.parametro (clave, valor, tipo_dato, vigente_desde, descripcion) values
 ('aporte_salud_empleado_pct', '4', 'porcentaje', '2026-01-01', 'Aporte del trabajador a salud'),
 ('aporte_pension_empleado_pct', '4', 'porcentaje', '2026-01-01', 'Aporte del trabajador a pensión'),
 ('provision_cesantias_pct', '8.33', 'porcentaje', '2026-01-01', 'Provisión mensual de cesantías'),
 ('provision_intereses_cesantias_pct', '1', 'porcentaje', '2026-01-01', 'Provisión mensual de intereses sobre cesantías (12 % anual)'),
 ('provision_prima_pct', '8.33', 'porcentaje', '2026-01-01', 'Provisión mensual de prima de servicios'),
 ('provision_vacaciones_pct', '4.17', 'porcentaje', '2026-01-01', 'Provisión mensual de vacaciones'),
 ('tarifa_renta_pct', '35', 'porcentaje', '2026-01-01', 'Tarifa general de renta (para EVA); el Régimen Simple usa otra base: confirmar con el contador');
insert into nucleo.parametro (predio_id, clave, valor, tipo_dato, vigente_desde, descripcion) values
 (nucleo.predio_actual(), 'monto_doble_aprobacion', '3000000', 'dinero', '2026-10-27', 'Pagos mayores necesitan segunda aprobación (por definir con la familia)'),
 (nucleo.predio_actual(), 'tope_reinversion_pct', '30', 'porcentaje', '2026-10-27', 'Parte máxima de la utilidad mensual de una línea que se reinvierte en nuevas iniciativas'),
 (nucleo.predio_actual(), 'costo_capital_anual_pct', '15', 'porcentaje', '2026-10-27', 'Tasa de oportunidad de la familia para VPN y EVA (supuesto, a definir)'),
 (nucleo.predio_actual(), 'volumen_referencia_prospecto', '1000000', 'dinero', '2026-10-27', 'Compra mensual que da el puntaje máximo de volumen a un prospecto');

-- Roles y permisos nuevos (quién aprueba tareas queda configurable: encargado, familia o ambos)
insert into nucleo.rol (codigo, nombre, descripcion) values
 ('encargado_finca', 'Encargado de la finca', 'Asigna y aprueba tareas, jornadas y ausencias; revisa la prenómina'),
 ('familia', 'Familia', 'Decide inversiones, aprueba pagos, cierres y nuevas iniciativas'),
 ('instructor', 'Instructor', 'Dicta sesiones presenciales y registra asistencia y notas'),
 ('estudiante', 'Estudiante', 'Practica en la finca de práctica y toma cursos');
insert into nucleo.permiso (codigo, nombre, modulo) values
 ('personal.aprobar_tarea', 'Aprobar o devolver tareas', 'personal'),
 ('personal.asignar_tarea', 'Asignar tareas', 'personal'),
 ('nomina.preparar', 'Preparar la prenómina', 'nomina'),
 ('nomina.cerrar', 'Cerrar el periodo de nómina', 'nomina'),
 ('nomina.aprobar_pago', 'Aprobar pagos de nómina', 'nomina'),
 ('estrategia.aprobar_iniciativa', 'Aprobar iniciativas y reinversiones', 'estrategia'),
 ('seguridad.atender_alerta', 'Atender alertas e incidentes de seguridad', 'seguridad');
insert into nucleo.rol_permiso (rol_id, permiso_id)
select r.id, p.id from nucleo.rol r join nucleo.permiso p on (r.codigo, p.codigo) in (
 ('administrador', 'personal.aprobar_tarea'), ('administrador', 'personal.asignar_tarea'), ('administrador', 'nomina.cerrar'),
 ('administrador', 'nomina.aprobar_pago'), ('administrador', 'estrategia.aprobar_iniciativa'), ('administrador', 'seguridad.atender_alerta'),
 ('encargado_finca', 'personal.aprobar_tarea'), ('encargado_finca', 'personal.asignar_tarea'), ('encargado_finca', 'nomina.preparar'),
 ('familia', 'personal.aprobar_tarea'), ('familia', 'nomina.cerrar'), ('familia', 'nomina.aprobar_pago'), ('familia', 'estrategia.aprobar_iniciativa'),
 ('contador', 'nomina.preparar'), ('contador', 'nomina.cerrar'));

-- Matriz de responsabilidades inicial (R responsable, A aprueba, C consultado, I informado)
insert into personal.matriz_responsabilidad (proceso, rol_id, responsabilidad)
select x.proceso, r.id, x.resp from (values
 ('postura', 'operario_granja', 'responsable'), ('postura', 'encargado_finca', 'aprueba'), ('postura', 'familia', 'informado'),
 ('bioseguridad', 'operario_granja', 'responsable'), ('bioseguridad', 'encargado_finca', 'aprueba'),
 ('venta', 'vendedor', 'responsable'), ('venta', 'administrador', 'aprueba'),
 ('nomina', 'contador', 'responsable'), ('nomina', 'familia', 'aprueba'), ('nomina', 'encargado_finca', 'consultado'),
 ('mantenimiento', 'operario_granja', 'responsable'), ('mantenimiento', 'encargado_finca', 'aprueba'),
 ('inversion', 'administrador', 'responsable'), ('inversion', 'familia', 'aprueba'), ('inversion', 'contador', 'consultado')) x(proceso, rol, resp)
join nucleo.rol r on r.codigo = x.rol;

-- Conceptos de nómina (salario, jornal y destajo conviven; tarifas en nucleo.parametro)
insert into nomina.concepto_nomina (codigo, nombre, tipo, base, parametro_clave, constitutivo_salario, codigo_dian) values
 ('SALARIO', 'Salario básico', 'devengado', 'salario', null, true, 'Basico'),
 ('AUX_TRANSPORTE', 'Auxilio de transporte', 'devengado', 'valor_fijo', 'auxilio_transporte', false, 'AuxilioTransporte'),
 ('JORNAL', 'Jornal', 'devengado', 'jornal', null, true, 'Basico'),
 ('DESTAJO', 'Pago a destajo', 'devengado', 'destajo', null, true, 'Basico'),
 ('HED', 'Hora extra diurna', 'devengado', 'horas', 'recargo_hora_extra_diurna_pct', true, 'HED'),
 ('RN', 'Recargo nocturno', 'devengado', 'horas', 'recargo_nocturno_pct', true, 'HRN'),
 ('SALUD_EMP', 'Aporte a salud del trabajador', 'deduccion', 'porcentaje', 'aporte_salud_empleado_pct', false, 'Salud'),
 ('PENSION_EMP', 'Aporte a pensión del trabajador', 'deduccion', 'porcentaje', 'aporte_pension_empleado_pct', false, 'FondoPension'),
 ('PRESTAMO', 'Descuento de préstamo autorizado', 'deduccion', 'valor_fijo', null, false, 'Deuda');

-- Competencias y cursos iniciales (la formación es para operarios y estudiantes)
insert into formacion.competencia (codigo, nombre, vigencia_meses, descripcion) values
 ('bioseguridad_avicola', 'Bioseguridad en granja avícola', 12, 'Entrar al galpón, desinfección, manejo de mortalidad (exigida por la granja avícola biosegura)'),
 ('aplicar_vacunas', 'Aplicar vacunas a las aves', 24, 'Registrar y aplicar el plan de vacunación'),
 ('aplicar_insumos', 'Aplicar fertilizantes y plaguicidas', 24, 'Dosis, equipo de protección y periodo de carencia'),
 ('liberar_lotes', 'Liberar lotes bloqueados', null, 'Revisar y liberar o descartar lotes bloqueados por frío o retiro'),
 ('operar_motosierra', 'Operar motosierra y guadaña', 24, 'Uso seguro y mantenimiento básico'),
 ('manipulacion_alimentos', 'Manipulación de alimentos', 12, 'Huevo y productos frescos para la venta');
insert into formacion.curso (codigo, nombre, publico, modalidad, competencia_id, nota_minima, duracion_horas, origen, ruta_cargo)
select x.codigo, x.nombre, x.publico, x.modalidad, c.id, 3.5, x.horas, x.origen, x.ruta from (values
 ('BIO-AVI', 'Bioseguridad en la granja avícola', 'ambos', 'mixto', 'bioseguridad_avicola', 8, 'propio', 'operario_galpon'),
 ('VAC-AVI', 'Plan de vacunación de aves', 'operarios', 'presencial', 'aplicar_vacunas', 4, 'propio', 'operario_galpon'),
 ('MAN-HUE', 'Manejo, clasificación y almacenamiento del huevo', 'ambos', 'virtual', 'manipulacion_alimentos', 4, 'propio', 'operario_galpon'),
 ('APL-INS', 'Aplicación segura de insumos agrícolas', 'operarios', 'mixto', 'aplicar_insumos', 6, 'propio', 'encargado_cultivos'),
 ('APP-CAMPO', 'Uso de la app de campo sin conexión', 'ambos', 'virtual', null, 2, 'propio', 'todos'),
 ('ERP-DEV', 'GuayacanERP como proyecto: arquitectura y datos', 'estudiantes', 'virtual', null, 20, 'propio', 'desarrollador')) x(codigo, nombre, publico, modalidad, comp, horas, origen, ruta)
left join formacion.competencia c on c.codigo = x.comp;

-- Plan de labores del galpón (sin zona hasta construirlo; jornal y destajo configurables)
insert into personal.plantilla_tarea (codigo, nombre, proceso, recurrencia, hora_limite, duracion_estimada_min, competencia_id, registro_que_crea, pasos, prioridad)
select x.codigo, x.nombre, x.proceso, x.rec, x.hora::time, x.min, c.id, x.reg, x.pasos::jsonb, x.prio from (values
 ('REC-HUEVO-AM', 'Recoger huevos (mañana)', 'postura', 'diaria', '10:00', 30, 'bioseguridad_avicola', 'postura', '["Desinfectar botas", "Recoger y contar", "Separar sucios y rotos", "Registrar en la app"]', 'alta'),
 ('REC-HUEVO-PM', 'Recoger huevos (tarde)', 'postura', 'diaria', '16:00', 30, 'bioseguridad_avicola', 'postura', '["Desinfectar botas", "Recoger y contar", "Registrar en la app"]', 'alta'),
 ('REV-BEBEDEROS', 'Revisar bebederos y comederos', 'postura', 'diaria', '08:00', 15, 'bioseguridad_avicola', 'alimentacion', '["Nivel de agua", "Limpieza", "Registrar alimento suministrado"]', 'media'),
 ('BIO-DESINF', 'Desinfección del galpón y pediluvio', 'bioseguridad', 'semanal', '12:00', 60, 'bioseguridad_avicola', 'bioseguridad', '["Cambiar pediluvio", "Desinfectar entrada", "Registrar producto y dosis"]', 'alta')) x(codigo, nombre, proceso, rec, hora, min, comp, reg, pasos, prio)
left join formacion.competencia c on c.codigo = x.comp;
update personal.plantilla_tarea set dias_semana = '{1}' where codigo = 'BIO-DESINF';

-- Normas: la granja avícola biosegura es obligatoria (sin interruptor); BPA y GLOBALG.A.P. quedan cargadas y apagadas
insert into cumplimiento.norma (codigo, nombre, entidad, referencia, obligatoria, condicion_obligatoria, funcion_codigo, vigencia_certificado_meses, url_fuente) values
 ('ICA_GAB', 'Granja avícola biosegura', 'ICA', 'Resolución ICA 3651 de 2014', true, 'Granjas de postura o levante desde 200 aves', null, 36, 'https://www.ica.gov.co'),
 ('ICA_BPA', 'Buenas Prácticas Agrícolas en producción primaria', 'ICA', 'Resolución ICA 30021 de 2017', false, 'Voluntaria: la solicita quien quiere certificar el predio', 'certificacion_bpa', 24, 'https://www.ica.gov.co'),
 ('GLOBALGAP_IFA6', 'GLOBALG.A.P. Aseguramiento Integrado de Fincas v6', 'GLOBALG.A.P.', 'IFA v6 Smart', false, 'Voluntaria: la piden compradores y exportadores', 'globalgap', 12, 'https://www.globalgap.org');
-- Requisitos resumidos: cargar el texto vigente de cada norma y revisarlo con el veterinario y el asesor técnico antes de auditar
insert into cumplimiento.requisito (norma_id, codigo, descripcion, tipo_evidencia, regla_evidencia, vigencia_dias, critico)
select n.id, x.codigo, x.descr, x.tipo, x.regla, x.dias, x.critico from (values
 ('ICA_GAB', 'GAB-01', 'Registro sanitario de predio avícola (RSPA) vigente', 'documento', null, null::smallint, true),
 ('ICA_GAB', 'GAB-02', 'Cerco perimetral y control de ingreso de personas y vehículos', 'inspeccion', null, null, true),
 ('ICA_GAB', 'GAB-03', 'Desinfección de personas y vehículos al ingreso (registros)', 'registro', 'registro:produccion.registro_bioseguridad', 30, true),
 ('ICA_GAB', 'GAB-04', 'Área y procedimiento para manejo de mortalidad', 'documento', null, null, true),
 ('ICA_GAB', 'GAB-05', 'Procedimientos de bioseguridad escritos y aprobados', 'documento', 'documento:protocolo', null, true),
 ('ICA_GAB', 'GAB-06', 'Plan sanitario con calendario de vacunación', 'documento', 'documento:plan', null, true),
 ('ICA_GAB', 'GAB-07', 'Personal capacitado en bioseguridad', 'certificado_formacion', 'competencia:bioseguridad_avicola', null, true),
 ('ICA_GAB', 'GAB-08', 'Registros de producción, sanidad y visitas conservados al menos un año', 'registro', 'registro:produccion.registro_postura', 7, false),
 ('ICA_BPA', 'BPA-01', 'Análisis de agua por fuente', 'analisis', null, 365, true),
 ('ICA_BPA', 'BPA-02', 'Plan de fertilización con análisis de suelo', 'analisis', 'registro:produccion.analisis_suelo', 730, true),
 ('ICA_BPA', 'BPA-03', 'Personal capacitado en aplicación de insumos', 'certificado_formacion', 'competencia:aplicar_insumos', null, true),
 ('ICA_BPA', 'BPA-04', 'Trazabilidad por lote de cosecha', 'registro', 'registro:produccion.cosecha', 90, true),
 ('ICA_BPA', 'BPA-05', 'Registro de aplicación de insumos y calibración de equipos', 'registro', 'registro:produccion.labor_cultural', 90, false),
 ('GLOBALGAP_IFA6', 'IFA-01', 'Autoevaluación anual con la lista de verificación vigente', 'documento', null, 365, true),
 ('GLOBALGAP_IFA6', 'IFA-02', 'Evaluación de riesgos del sitio y plan de gestión', 'documento', null, 365, true)) x(norma, codigo, descr, tipo, regla, dias, critico)
join cumplimiento.norma n on n.codigo = x.norma;
insert into cumplimiento.expediente (norma_id, estado) select id, 'en_preparacion' from cumplimiento.norma where codigo = 'ICA_GAB';

-- Cuentas PUC adicionales para costos, nómina, activos, anticipos y estados financieros
insert into finanzas.cuenta_contable (codigo, nombre, naturaleza, nivel, acepta_movimiento) values
 ('1330', 'Anticipos y avances a proveedores', 'debito', 3, true), ('1520', 'Maquinaria y equipo', 'debito', 3, true),
 ('1592', 'Depreciación acumulada', 'credito', 3, true), ('2105', 'Obligaciones financieras - bancos', 'credito', 3, true),
 ('2370', 'Retenciones y aportes de nómina', 'credito', 3, true), ('2505', 'Salarios por pagar', 'credito', 3, true),
 ('2510', 'Cesantías consolidadas', 'credito', 3, true), ('3105', 'Capital', 'credito', 3, true),
 ('3705', 'Utilidades acumuladas', 'credito', 3, true), ('5160', 'Depreciaciones (administración)', 'debito', 3, true),
 ('5305', 'Gastos financieros', 'debito', 3, true), ('5405', 'Impuesto de renta', 'debito', 3, true),
 ('7105', 'Materia prima (concentrado, semillas, insumos)', 'debito', 3, true), ('7205', 'Mano de obra directa', 'debito', 3, true),
 ('7305', 'Costos indirectos de producción', 'debito', 3, true);
insert into finanzas.clasificacion_costo (cuenta_id, elemento, comportamiento, parte_fija_pct, es_costo_producto)
select c.id, x.elem, x.comp, x.fija, x.prod from (values
 ('6120', 'material_directo', 'variable', null::numeric, true), ('7105', 'material_directo', 'variable', null, true),
 ('7205', 'mano_obra_directa', 'semivariable', 60, true), ('7305', 'cif', 'semivariable', 70, true),
 ('5105', 'gasto_administracion', 'fijo', null, false), ('5160', 'gasto_administracion', 'fijo', null, false),
 ('5305', 'gasto_financiero', 'fijo', null, false)) x(cuenta, elem, comp, fija, prod)
join finanzas.cuenta_contable c on c.codigo = x.cuenta;

-- Catálogo de indicadores (fórmulas de los documentos de finanzas del instructor)
insert into finanzas.indicador (codigo, nombre, grupo, formula, interpretacion, unidad, sentido) values
 ('capital_trabajo', 'Capital neto de trabajo (KNT)', 'liquidez', 'Activo corriente − Pasivo corriente', 'Recursos para operar después de pagar lo de corto plazo', 'pesos', 'mayor_mejor'),
 ('razon_corriente', 'Razón corriente', 'liquidez', 'Activo corriente / Pasivo corriente', 'Pesos de activo corriente por cada peso de deuda de corto plazo', 'veces', 'mayor_mejor'),
 ('prueba_acida', 'Prueba ácida', 'liquidez', '(Activo corriente − Inventarios) / Pasivo corriente', 'Capacidad de pago sin vender inventario', 'veces', 'mayor_mejor'),
 ('endeudamiento', 'Nivel de endeudamiento', 'endeudamiento', 'Pasivo total / Activo total × 100', 'Parte de los activos financiada por terceros', 'porcentaje', 'menor_mejor'),
 ('apalancamiento', 'Palanca financiera (multiplicador)', 'endeudamiento', 'Activo total / Patrimonio = 1 + D/K', 'Cuántas veces los activos superan el patrimonio', 'veces', 'rango'),
 ('cobertura_intereses', 'Cobertura de intereses', 'endeudamiento', 'Utilidad operacional / Intereses', 'Veces que la operación paga los intereses', 'veces', 'mayor_mejor'),
 ('margen_bruto', 'Margen bruto', 'rentabilidad', 'Utilidad bruta / Ventas × 100', 'Lo que queda después del costo de ventas', 'porcentaje', 'mayor_mejor'),
 ('margen_operacional', 'Margen operacional', 'rentabilidad', 'Utilidad operacional / Ventas × 100', 'Rentabilidad de la operación', 'porcentaje', 'mayor_mejor'),
 ('margen_neto', 'Margen neto (RSV)', 'rentabilidad', 'Utilidad neta / Ventas × 100', 'Rentabilidad sobre ventas', 'porcentaje', 'mayor_mejor'),
 ('ebitda', 'EBITDA (UAIIDA)', 'rentabilidad', 'Utilidad operacional + Depreciaciones y amortizaciones', 'Caja que genera la operación', 'pesos', 'mayor_mejor'),
 ('rsa', 'Rentabilidad sobre activos (RSA, ROA)', 'rentabilidad', 'Utilidad neta / Activo total × 100 = RSV × Rotación de activos (Du Pont)', 'Lo que rinde cada peso invertido en activos', 'porcentaje', 'mayor_mejor'),
 ('rsp', 'Rentabilidad sobre patrimonio (RSP, ROE)', 'rentabilidad', 'Utilidad neta / Patrimonio × 100 = RSA × Palanca financiera', 'Lo que rinde el dinero de la familia', 'porcentaje', 'mayor_mejor'),
 ('rotacion_activos', 'Rotación del activo total', 'actividad', 'Ventas / Activo total', 'Ventas generadas por cada peso de activo', 'veces', 'mayor_mejor'),
 ('dias_cartera', 'Días de cartera', 'actividad', 'Deudores / Ventas × días del periodo', 'Días promedio de cobro', 'dias', 'menor_mejor'),
 ('dias_inventario', 'Días de inventario', 'actividad', 'Inventarios / Costo de ventas × días del periodo', 'Días que tarda en venderse el inventario', 'dias', 'menor_mejor'),
 ('gpo', 'Grado de palanca operativa', 'palanca', 'Margen de contribución / Utilidad operacional', 'Cuánto cambia la utilidad operacional por cada 1 % de cambio en ventas', 'veces', 'rango'),
 ('gpf', 'Grado de palanca financiera', 'palanca', 'Utilidad operacional / (Utilidad operacional − Intereses)', 'Sensibilidad de la utilidad neta a la utilidad operacional (riesgo de la deuda)', 'veces', 'rango'),
 ('gpt', 'Grado de palanca total', 'palanca', 'GPO × GPF', 'Cambio de la utilidad por cada 1 % de cambio en ventas', 'veces', 'rango'),
 ('punto_equilibrio_pesos', 'Punto de equilibrio en ventas', 'palanca', 'Costos y gastos fijos / (Margen de contribución / Ventas)', 'Ventas mínimas para no perder', 'pesos', 'menor_mejor'),
 ('margen_seguridad', 'Margen de seguridad', 'riesgo', '(Ventas − Ventas de equilibrio) / Ventas × 100', 'Cuánto pueden caer las ventas antes de perder', 'porcentaje', 'mayor_mejor'),
 ('eva', 'Valor económico agregado (EVA)', 'valor', 'UO × (1 − tarifa de renta) − Capital de operación × costo de capital', 'Si la finca gana más que lo que cuesta su capital', 'pesos', 'mayor_mejor'),
 ('altman_z2', 'Z de Altman (no manufactureras)', 'riesgo', '6,56·KNT/AT + 3,26·Utilidades retenidas/AT + 6,72·UAII/AT + 1,05·Patrimonio/Pasivo', 'Mayor a 2,6 zona segura; menor a 1,1 zona de riesgo', 'veces', 'mayor_mejor'),
 ('postura_ave_dia', 'Postura por ave al día', 'produccion', 'Huevos recogidos / (aves × días) × 100', 'Porcentaje de postura del lote', 'porcentaje', 'mayor_mejor'),
 ('conversion_alimenticia', 'Conversión alimenticia', 'produccion', 'kg de alimento / kg de huevo o carne', 'Alimento por kilo producido', 'veces', 'menor_mejor'),
 ('tareas_vencidas', 'Tareas vencidas', 'personal', 'Tareas pendientes con plazo vencido', 'Trabajo que se quedó sin hacer', 'unidades', 'menor_mejor'),
 ('costo_por_cliente', 'Costo de adquisición por cliente', 'comercial', 'Costo de campañas / Clientes ganados', 'Cuánto cuesta conseguir un cliente', 'pesos', 'menor_mejor');

-- Agentes nuevos (proponen; nunca aprueban ni pagan)
insert into ia.agente (codigo, nombre, rol, nivel_autonomia, proveedor_modelo, modelo, version_instrucciones, instrucciones, limite_costo_diario_usd) values
 ('agronomo', 'Agrónomo', 'Analiza fotos y datos de campo y propone diagnósticos y labores; el agrónomo o veterinario humano decide', 'propone', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/agronomo.md', 4),
 ('coordinador', 'Coordinador', 'Propone el plan de tareas de la semana según clima, producción y disponibilidad; el encargado asigna', 'propone', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/coordinador.md', 3),
 ('instructor', 'Instructor', 'Responde preguntas técnicas solo con documentos aprobados y vigentes; si no sabe, remite al encargado', 'solo_lectura', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/instructor.md', 3),
 ('estratega', 'Estratega de negocio', 'Busca nuevos mercados, productos y negocios, arma la evaluación financiera (VPN, TIR, ROI, palancas) y propone iniciativas; la familia decide', 'propone', 'anthropic', 'claude-opus-5-5', '1.0', 'Ver instrucciones/estratega.md', 5),
 ('vigia_seguridad', 'Vigía de seguridad', 'Resume alertas e incidentes de seguridad y sugiere acciones; no bloquea ni desbloquea por su cuenta', 'solo_lectura', 'anthropic', 'claude-haiku-5-5', '1.0', 'Ver instrucciones/vigia_seguridad.md', 1);

-- Seguridad: reglas del detector de ataques y señuelos (cambiar los valores de los señuelos al instalar)
insert into seguridad.regla_deteccion (codigo, descripcion, umbral, ventana_min, severidad, respuesta, bloqueo_min) values
 ('fuerza_bruta_cuenta', 'Intentos fallidos seguidos contra la misma cuenta', 5, 15, 'alta', 'bloquear_cuenta', 30),
 ('relleno_credenciales', 'Muchas cuentas distintas fallidas desde la misma IP', 10, 10, 'alta', 'bloquear_ip', 60),
 ('senuelo', 'Uso de una cuenta o llave señuelo', 1, 1, 'critica', 'bloquear_ip', 1440),
 ('exportacion_masiva', 'Muchas exportaciones de datos del mismo usuario en poco tiempo', 20, 60, 'alta', 'revocar_sesiones', 0);
insert into seguridad.senuelo (tipo, valor, descripcion) values
 ('cuenta', 'soporte.ti@guayacan.local', 'Cuenta que nadie usa: cualquier intento es un intruso'),
 ('llave_api', 'gyc_cebo0001', 'Llave publicada solo en un archivo de configuración falso');

-- CRM: segmentos iniciales (la palanca de mercadeo: atender mejor a cada segmento)
insert into crm.segmento (codigo, nombre, criterios, propuesta_valor) values
 ('HOGAR', 'Hogares de Nilo y veredas vecinas', '{"municipios": ["25488"]}', 'Huevo campesino fresco a domicilio'),
 ('TIENDA', 'Tiendas de barrio', null, 'Entrega fija semanal y precio estable'),
 ('HORECA', 'Restaurantes y hoteles de Nilo, Girardot y Melgar', null, 'Pedido recurrente, frescura garantizada y trazabilidad por lote'),
 ('INSTITUCION', 'Colegios y casinos', null, 'Volumen estable con factura electrónica'),
 ('TURISTA', 'Visitantes de la finca', null, 'Producto de origen con historia de la finca');

-- Líneas de negocio actuales (una por centro de costo)
insert into estrategia.linea_negocio (codigo, nombre, centro_costo_id, estado, palanca_dominante)
select c.codigo, c.nombre, c.id, 'actual', case c.codigo when 'AVI' then 'produccion' when 'TUR' then 'mercadeo' else 'mercadeo' end
from finanzas.centro_costo c where c.codigo <> 'ADM';

-- Jornada laboral (Ley 2101 de 2021 y Ley 2466 de 2025; confirmar con el contador o abogado cada año)
insert into nucleo.parametro (clave, valor, tipo_dato, vigente_desde, vigente_hasta, descripcion) values
 ('jornada_maxima_semanal_horas', '44', 'decimal', '2025-07-15', '2026-07-14', 'Jornada máxima semanal (Ley 2101 de 2021)'),
 ('jornada_maxima_semanal_horas', '42', 'decimal', '2026-07-15', null, 'Jornada máxima semanal desde el 15 de julio de 2026 (Ley 2101 de 2021)'),
 ('horas_extra_max_semana', '12', 'decimal', '2026-01-01', null, 'Horas extra máximas por semana'),
 ('jornada_maxima_diaria_horas', '11', 'decimal', '2026-01-01', null, 'Máximo diario: hasta 9 horas ordinarias más 2 extra (confirmar con el contador)'),
 ('hora_inicio_nocturna', '19:00', 'texto', '2025-12-25', null, 'Desde esta hora el trabajo es nocturno (Ley 2466 de 2025)'),
 ('recargo_nocturno_pct', '35', 'porcentaje', '2026-01-01', null, 'Recargo por trabajo nocturno'),
 ('recargo_dominical_pct', '90', 'porcentaje', '2026-07-01', '2027-06-30', 'Recargo dominical y festivo (Ley 2466 de 2025: 100 % desde julio de 2027)'),
 ('recargo_dominical_pct', '100', 'porcentaje', '2027-07-01', null, 'Recargo dominical y festivo desde julio de 2027 (Ley 2466 de 2025)');
insert into nucleo.parametro (predio_id, clave, valor, tipo_dato, vigente_desde, descripcion) values
 (nucleo.predio_actual(), 'descanso_minimo_entre_turnos_horas', '10', 'decimal', '2026-10-27', 'Política de la finca: horas mínimas de descanso entre dos turnos'),
 (nucleo.predio_actual(), 'hora_checkin', '15:00', 'texto', '2026-10-27', 'Hora de llegada a las cabañas'),
 (nucleo.predio_actual(), 'hora_checkout', '12:00', 'texto', '2026-10-27', 'Hora de salida de las cabañas'),
 (nucleo.predio_actual(), 'tolerancia_visita_min', '60', 'entero', '2026-10-27', 'Minutos antes de la hora programada en que una visita puede entrar'),
 (nucleo.predio_actual(), 'cuarentena_aves_horas', '72', 'entero', '2026-10-27', 'Horas sin contacto con otras aves para entrar al galpón (validar con el veterinario)'),
 (nucleo.predio_actual(), 'dias_respuesta_queja', '15', 'entero', '2026-10-27', 'Días para responder una queja o apelación de formación');

insert into nucleo.funcionalidad (codigo, descripcion, fase, requiere_equipo, activa) values
 ('iso_21001', 'Expediente ISO 21001 para la formación (organización educativa)', 3, 'Decisión de certificar la formación', false);

insert into nucleo.permiso (codigo, nombre, modulo) values
 ('personal.publicar_cronograma', 'Publicar cronogramas de trabajo', 'personal'),
 ('agenda.aprobar_visita', 'Aprobar visitas e ingresos', 'agenda'),
 ('proyectos.decidir_cambio', 'Aprobar o rechazar cambios de proyectos', 'proyectos');
insert into nucleo.rol (codigo, nombre, descripcion) values ('porteria', 'Portería', 'Registra entradas y salidas de personas y vehículos');
insert into nucleo.rol_permiso (rol_id, permiso_id)
select r.id, p.id from nucleo.rol r join nucleo.permiso p on (r.codigo, p.codigo) in (
 ('administrador', 'personal.publicar_cronograma'), ('administrador', 'agenda.aprobar_visita'), ('administrador', 'proyectos.decidir_cambio'),
 ('encargado_finca', 'personal.publicar_cronograma'), ('encargado_finca', 'agenda.aprobar_visita'), ('familia', 'proyectos.decidir_cambio'));

-- Áreas de responsabilidad (las de 24/7 exigen cobertura continua)
insert into personal.area_responsabilidad (codigo, nombre, descripcion, centro_costo_id, opera_24_7)
select x.codigo, x.nombre, x.descr, cc.id, x.h24 from (values
 ('AR-GALPON', 'Galpón y aves', 'Postura, alimentación, sanidad y bioseguridad', 'AVI', true),
 ('AR-CULTIVOS', 'Cultivos y riego', 'Plátano, cacao, aguacate, ciclo corto y forrajes', 'PER', false),
 ('AR-ANIMALES', 'Ovinos, caprinos y peces', 'Aprisco y estanques', 'OVC', false),
 ('AR-TURISMO', 'Turismo y cabañas', 'Reservas, recibo de huéspedes, limpieza y alistamiento', 'TUR', false),
 ('AR-BODEGA', 'Bodega y despachos', 'Inventario, empaque, pedidos y entregas', 'ADM', false),
 ('AR-MANT', 'Mantenimiento', 'Equipos, herramientas, energía e infraestructura', 'ADM', false),
 ('AR-VIGILANCIA', 'Vigilancia y portería', 'Ingreso y salida de personas y vehículos, rondas', 'ADM', true)) x(codigo, nombre, descr, cc, h24)
left join finanzas.centro_costo cc on cc.codigo = x.cc;
update personal.plantilla_tarea set area_id = (select id from personal.area_responsabilidad where codigo = 'AR-GALPON') where proceso in ('postura', 'bioseguridad');
insert into personal.requerimiento_cobertura (area_id, dia_semana, hora_inicio, hora_fin, personas_min)
select a.id, null::smallint, x.hi::time, x.hf::time, 1 from personal.area_responsabilidad a, (values ('00:00', '23:59:59')) x(hi, hf) where a.codigo = 'AR-VIGILANCIA'
union all select a.id, null, '06:00', '18:00', 1 from personal.area_responsabilidad a where a.codigo = 'AR-GALPON';

-- Patrones de turno: semanal (días y horas a elección), cíclico 24/7 de 8 horas y flexible
insert into personal.patron_turno (codigo, nombre, tipo, ciclo_dias) values
 ('SEM-LS-6-13', 'Lunes a sábado de 6:00 a 13:00 (42 h), domingo descanso', 'semanal', 7),
 ('CIC-MMTTNNL', 'Rotación 24/7: 2 mañanas, 2 tardes, 2 noches y 1 descanso (8 h)', 'ciclico', 7),
 ('FLEX', 'Flexible: el encargado elige días y horas a mano', 'flexible', 7);
insert into personal.patron_turno_detalle (patron_id, dia_ciclo, hora_inicio, hora_fin, tipo)
select p.id, d, case when d = 7 then null else '06:00'::time end, case when d = 7 then null else '13:00'::time end, case when d = 7 then 'descanso' else 'diurno' end
from personal.patron_turno p, generate_series(1, 7) d where p.codigo = 'SEM-LS-6-13';
insert into personal.patron_turno_detalle (patron_id, dia_ciclo, hora_inicio, hora_fin, tipo)
select p.id, x.d, x.hi::time, x.hf::time, x.t from personal.patron_turno p, (values
 (1, '06:00', '14:00', 'diurno'), (2, '06:00', '14:00', 'diurno'), (3, '14:00', '22:00', 'mixto'), (4, '14:00', '22:00', 'mixto'),
 (5, '22:00', '06:00', 'nocturno'), (6, '22:00', '06:00', 'nocturno'), (7, null, null, 'descanso')) x(d, hi, hf, t) where p.codigo = 'CIC-MMTTNNL';

-- ISO 21001 (formación como organización educativa): requisitos resumidos por capítulo; cargar el texto licenciado de la norma antes de auditar
insert into cumplimiento.norma (codigo, nombre, entidad, referencia, obligatoria, condicion_obligatoria, funcion_codigo, vigencia_certificado_meses) values
 ('ISO_21001', 'Sistema de gestión para organizaciones educativas', 'ISO', 'ISO 21001:2018', false, 'Voluntaria', 'iso_21001', 36);
insert into cumplimiento.requisito (norma_id, codigo, descripcion, tipo_evidencia, regla_evidencia, vigencia_dias, critico)
select n.id, x.c, x.d, x.t, x.r, x.v, x.k from cumplimiento.norma n, (values
 ('21001-4.2', 'Necesidades y expectativas de los aprendices y demás interesados identificadas', 'registro', 'registro:formacion.necesidad_formacion', 365::smallint, true),
 ('21001-7.2', 'Competencia de instructores y personal de apoyo demostrada', 'certificado_formacion', null, null, true),
 ('21001-8.3', 'Diseño de cursos con objetivos, contenidos y evaluación', 'documento', null, null, true),
 ('21001-8.5', 'Entrega de la formación con registro de asistencia y evaluación', 'registro', 'registro:formacion.inscripcion', 180, true),
 ('21001-9.1', 'Seguimiento de la satisfacción de los aprendices', 'registro', 'registro:formacion.encuesta', 180, true),
 ('21001-9.1q', 'Quejas y apelaciones atendidas en plazo', 'registro', null, null, false),
 ('21001-9.2', 'Auditoría interna del sistema de formación', 'documento', null, 365, false)) x(c, d, t, r, v, k)
where n.codigo = 'ISO_21001';

-- Indicadores adicionales (análisis financiero y proyectos)
insert into finanzas.indicador (codigo, nombre, grupo, formula, interpretacion, unidad, sentido) values
 ('dias_proveedores', 'Días de pago a proveedores', 'actividad', 'Proveedores / Costo de ventas × días del periodo', 'Días que tarda la finca en pagar', 'dias', 'rango'),
 ('ciclo_efectivo', 'Ciclo de conversión del efectivo', 'actividad', 'Días de cartera + Días de inventario − Días de proveedores', 'Días que la plata está amarrada en la operación', 'dias', 'menor_mejor'),
 ('cpi', 'Índice de desempeño del costo (CPI)', 'proyecto', 'Valor ganado / Costo real', 'Menor que 1: el proyecto gasta más de lo planeado', 'veces', 'mayor_mejor'),
 ('spi', 'Índice de desempeño del cronograma (SPI)', 'proyecto', 'Valor ganado / Valor planificado', 'Menor que 1: el proyecto va atrasado', 'veces', 'mayor_mejor');

insert into ia.agente (codigo, nombre, rol, nivel_autonomia, proveedor_modelo, modelo, version_instrucciones, instrucciones, limite_costo_diario_usd) values
 ('director_proyectos', 'Asistente de proyectos', 'Arma borradores de EDT, cronograma, riesgos y reportes de valor ganado; no aprueba líneas base ni cambios', 'propone', 'anthropic', 'claude-sonnet-5-5', '1.0', 'Ver instrucciones/director_proyectos.md', 3);

-- Herramientas MCP de los agentes nuevos (todas leen o proponen; ninguna aprueba)
insert into ia.herramienta (codigo, descripcion, tipo, requiere_aprobacion, esquema_entrada) values
 ('proponer_tareas', 'Propone tareas de la semana sin asignarlas (el encargado asigna)', 'propuesta', false, '{"type":"object","required":["tareas"]}'),
 ('consultar_cronograma', 'Turnos, disponibilidad y huecos de cobertura de un área', 'lectura', false, '{"type":"object","required":["area"]}'),
 ('diagnosticar_imagen', 'Registra un diagnóstico propuesto a partir de una foto (lo confirma una persona)', 'propuesta', false, '{"type":"object","required":["foto_url","objetivo"]}'),
 ('consultar_documentos_aprobados', 'Lee solo documentos aprobados, vigentes y autorizados para agentes', 'lectura', false, '{"type":"object","properties":{"tema":{"type":"string"}}}'),
 ('consultar_estados_financieros', 'Estado de resultados, balance, indicadores, análisis vertical y horizontal', 'lectura', false, '{"type":"object","required":["desde","hasta"]}'),
 ('proponer_iniciativa', 'Registra una idea de nuevo mercado, producto o negocio con su evaluación', 'propuesta', false, '{"type":"object","required":["titulo","ansoff","palanca"]}'),
 ('evaluar_proyecto', 'Calcula VPN, TIR, ROI, equilibrio y palancas de una iniciativa', 'lectura', false, '{"type":"object","required":["evaluacion_id"]}'),
 ('consultar_alertas_seguridad', 'Resumen del tablero de seguridad (sin datos personales)', 'lectura', false, '{"type":"object"}'),
 ('consultar_prospectos', 'Embudo y prospectos sin datos de contacto', 'lectura', false, '{"type":"object"}'),
 ('consultar_proyecto', 'Cronograma, ruta crítica, riesgos y valor ganado de un proyecto', 'lectura', false, '{"type":"object","required":["codigo"]}');
insert into ia.agente_herramienta (agente_id, herramienta_id)
select a.id, h.id from ia.agente a join ia.herramienta h on (a.codigo, h.codigo) in (
 ('coordinador', 'proponer_tareas'), ('coordinador', 'consultar_cronograma'), ('agronomo', 'diagnosticar_imagen'), ('agronomo', 'consultar_documentos_aprobados'),
 ('instructor', 'consultar_documentos_aprobados'), ('estratega', 'consultar_estados_financieros'), ('estratega', 'proponer_iniciativa'), ('estratega', 'evaluar_proyecto'),
 ('estratega', 'consultar_prospectos'), ('vigia_seguridad', 'consultar_alertas_seguridad'), ('director_proyectos', 'consultar_proyecto'),
 ('director_proyectos', 'consultar_cronograma'), ('analista_negocio', 'consultar_estados_financieros'));

commit;
