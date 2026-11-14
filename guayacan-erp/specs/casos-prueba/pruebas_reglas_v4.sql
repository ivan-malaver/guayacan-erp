-- GuayacanERP · Pruebas de las reglas de negocio v4 (PostgreSQL 18; también corren en 16 y 17)
-- Ejecutar como superusuario sobre una base recién creada con esquema_postgresql.sql + datos_iniciales.sql.
-- Las pruebas corren con SET ROLE guayacan_app, que no puede saltarse la seguridad por filas.
\set ON_ERROR_STOP 1
set client_min_messages = notice;

create schema if not exists prueba;
create or replace function prueba.ok(p_cond boolean, p_nombre text) returns void language plpgsql as $$
begin
  if not coalesce(p_cond, false) then raise exception 'FALLA: %', p_nombre; end if;
  raise notice 'OK  %', p_nombre;
end $$;
create or replace function prueba.esperar_error(p_sql text, p_patron text, p_nombre text) returns void language plpgsql as $$
begin
  begin
    execute p_sql;
  exception when others then
    if sqlerrm ilike '%' || p_patron || '%' then raise notice 'OK  % -> "%"', p_nombre, sqlerrm; return; end if;
    raise exception 'FALLA: % (error distinto: %)', p_nombre, sqlerrm;
  end;
  raise exception 'FALLA: % (no hubo error)', p_nombre;
end $$;
grant usage on schema prueba to guayacan_app;
grant execute on all functions in schema prueba to guayacan_app;

-- Segunda finca para probar aislamiento (la crea el administrador del sistema)
insert into nucleo.predio (nombre, tenencia) values ('Finca de prueba', 'propio');
select set_config('app.predio_id', (select id::text from nucleo.predio where nombre = 'Finca de prueba'), false);
insert into inventario.bodega (codigo, nombre) values ('B01', 'Bodega finca de prueba');
insert into inventario.producto (sku, nombre, categoria_id, unidad_id, tipo, se_vende)
select 'HUE-AA-30', 'Huevo de otra finca', c.id, u.id, 'producto_terminado', true
from inventario.categoria_producto c, inventario.unidad_medida u where c.nombre = 'Huevo' and u.codigo = 'cub30';
select id as f2 from nucleo.predio where nombre = 'Finca de prueba' \gset
select id as fp from nucleo.predio where es_practica \gset

-- ===================================================================== sesión de la API en la finca 1
set role guayacan_app;
select set_config('app.predio_id', (select '1'), false);
select set_config('app.usuario_id', '1', false);

-- 1. Seguridad por filas
select prueba.ok((select count(*) from inventario.producto) = 12, 'RLS: la finca 1 ve solo sus 12 productos');
select prueba.ok((select count(*) from inventario.producto where nombre = 'Huevo de otra finca') = 0, 'RLS: no ve el producto de la otra finca');
select prueba.esperar_error(format($$insert into inventario.bodega (predio_id, codigo, nombre) values (%s, 'X', 'intrusa')$$, :f2), 'row-level security', 'RLS: no puede escribir en otra finca');
select set_config('app.predio_id', '', false);
select prueba.ok((select count(*) from inventario.producto) = 0, 'RLS: sin finca en la sesión no ve nada');
select set_config('app.predio_id', :'f2', false);
select prueba.esperar_error($$insert into inventario.lote_inventario (producto_id, bodega_id, codigo_lote, origen, fecha_produccion, cantidad_inicial, costo_unitario)
                              select 1, id, 'INTRUSO', 'compra', current_date, 5, 100 from inventario.bodega$$, 'foreign key', 'Llave compuesta: la finca 2 no puede usar el producto 1 de la finca 1 aunque sepa su número');
select set_config('app.predio_id', '1', false);

-- 2. Vencimiento estimado y kardex
insert into inventario.lote_inventario (producto_id, bodega_id, codigo_lote, origen, fecha_produccion, cantidad_inicial, costo_unitario)
select p.id, b.id, x.cod, 'produccion', current_date - x.edad, x.cant, 11918
from (values ('LOTE-A', 14, 50), ('LOTE-B', 1, 40), ('LOTE-C', 20, 10)) x(cod, edad, cant), inventario.producto p, inventario.bodega b
where p.sku = 'HUE-AA-30' and b.codigo = 'B01';
select prueba.ok((select fecha_vencimiento = current_date + 7 and fecha_limite_venta = current_date + 2 from inventario.lote_inventario where codigo_lote = 'LOTE-A'),
                 'Vencimiento: huevo de 14 días vence en 7 y su límite de venta es en 2 (21 días de vida útil, 5 de margen)');
select prueba.ok((select sum(cantidad_disponible) from inventario.lote_inventario) = 100, 'Kardex: cada lote nuevo genera su entrada (50 + 40 + 10)');
select prueba.ok((select count(*) from inventario.movimiento_inventario where tipo = 'entrada') = 3, 'Kardex: 3 movimientos de entrada');
select prueba.esperar_error($$update inventario.lote_inventario set cantidad_disponible = 999 where codigo_lote = 'LOTE-A'$$, 'solo cambian con un movimiento', 'Kardex: nadie edita cantidades a mano');
select prueba.esperar_error($$update inventario.movimiento_inventario set cantidad = 1$$, 'solo inserción', 'Kardex: los movimientos no se editan');
select prueba.ok((select semaforo from inventario.v_alertas_vencimiento where codigo_lote = 'LOTE-A') = 'amarillo', 'Alerta: LOTE-A en amarillo (2 días para el límite, alerta a 4)');
select prueba.ok((select precio_liquidacion from inventario.v_alertas_vencimiento where codigo_lote = 'LOTE-A') = 16575, 'Alerta: precio de liquidación $16.575 (15 % sobre $19.500)');
select prueba.ok((select semaforo from inventario.v_alertas_vencimiento where codigo_lote = 'LOTE-C') = 'rojo', 'Alerta: LOTE-C en rojo (pasó su fecha límite de venta)');
select prueba.ok((select cantidad_disponible from comercial.v_catalogo_disponible where sku = 'HUE-AA-30') = 90, 'Catálogo: ofrece 90, no los 10 del lote pasado de fecha');

-- 3. Pedido con reserva FEFO
insert into terceros.tercero (tipo_persona, nombres, es_cliente) values ('natural', 'Cliente Prueba', true);
insert into terceros.cliente (tercero_id, segmento) select id, 'tienda' from terceros.tercero where nombres = 'Cliente Prueba';
insert into comercial.pedido (numero, cliente_id, canal) select 'PED-1', id, 'whatsapp' from terceros.cliente;
insert into comercial.pedido_detalle (pedido_id, producto_id, cantidad, precio_producto_id, precio_unitario, total_linea)
select pe.id, pp.producto_id, 60, pp.id, pp.precio_unitario, 60 * pp.precio_unitario
from comercial.pedido pe, comercial.precio_producto pp join inventario.producto p on p.id = pp.producto_id and p.sku = 'HUE-AA-30' where pe.numero = 'PED-1';
select comercial.confirmar_pedido((select id from comercial.pedido where numero = 'PED-1'));
select prueba.ok((select string_agg(l.codigo_lote || ':' || rl.cantidad::int, ',' order by l.codigo_lote) from comercial.reserva_lote rl join inventario.lote_inventario l on l.id = rl.lote_inventario_id) = 'LOTE-A:50,LOTE-B:10',
                 'FEFO: toma primero las 50 del lote que vence antes y 10 del siguiente; ignora el lote pasado de fecha');
select prueba.ok((select total from comercial.pedido where numero = 'PED-1') = 1170000, 'Pedido: total $1.170.000 (60 × $19.500)');
insert into comercial.pedido (numero, cliente_id, canal) select 'PED-2', id, 'web' from terceros.cliente;
insert into comercial.pedido_detalle (pedido_id, producto_id, cantidad, precio_producto_id, precio_unitario, total_linea)
select pe.id, pp.producto_id, 40, pp.id, pp.precio_unitario, 40 * pp.precio_unitario
from comercial.pedido pe, comercial.precio_producto pp join inventario.producto p on p.id = pp.producto_id and p.sku = 'HUE-AA-30' where pe.numero = 'PED-2';
select prueba.esperar_error($$select comercial.confirmar_pedido((select id from comercial.pedido where numero = 'PED-2'))$$, 'Inventario insuficiente', 'FEFO: no reserva más de lo que hay (quedan 30 vendibles)');
select prueba.ok((select estado from comercial.pedido where numero = 'PED-2') = 'borrador' and (select count(*) from comercial.reserva_lote) = 2, 'FEFO: el intento fallido no dejó reservas a medias');
select comercial.despachar_pedido((select id from comercial.pedido where numero = 'PED-1'));
select prueba.ok((select estado from inventario.lote_inventario where codigo_lote = 'LOTE-A') = 'agotado' and (select cantidad_disponible from inventario.lote_inventario where codigo_lote = 'LOTE-B') = 30,
                 'Despacho: LOTE-A agotado y LOTE-B con 30');
select prueba.ok(inventario.marcar_vencidos() = 0, 'Vencidos: ningún lote pasó aún su fecha de vencimiento');
select prueba.esperar_error($$insert into inventario.movimiento_inventario (lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id) select id, 'merma', 2, 11918, 'revision', 1 from inventario.lote_inventario where codigo_lote = 'LOTE-C'$$,
                            'causa', 'Merma: exige la causa');
insert into inventario.movimiento_inventario (lote_inventario_id, tipo, cantidad, costo_unitario, causa_merma, documento_tipo, documento_id)
select id, 'merma', 10, 11918, 'vencido', 'revision', 1 from inventario.lote_inventario where codigo_lote = 'LOTE-C';
select prueba.ok((select estado from inventario.lote_inventario where codigo_lote = 'LOTE-C') = 'agotado', 'Merma: LOTE-C dado de baja por vencido');

-- 4. Captura sin conexión repetida (idempotencia)
insert into inventario.movimiento_inventario (lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, id_cliente, capturado_en)
select id, 'consumo_interno', 1, 11918, 'consumo', 1, '01929a4e-0000-7000-8000-000000000001', now() - interval '3 hours' from inventario.lote_inventario where codigo_lote = 'LOTE-B'
on conflict (id_cliente) do nothing;
insert into inventario.movimiento_inventario (lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, id_cliente, capturado_en)
select id, 'consumo_interno', 1, 11918, 'consumo', 1, '01929a4e-0000-7000-8000-000000000001', now() - interval '3 hours' from inventario.lote_inventario where codigo_lote = 'LOTE-B'
on conflict (id_cliente) do nothing;
select prueba.ok((select cantidad_disponible from inventario.lote_inventario where codigo_lote = 'LOTE-B') = 29, 'Sin conexión: el mismo registro enviado dos veces se aplica una sola vez');

-- 5. Auditoría automática
update inventario.producto set nombre = 'Huevo AA de pastoreo · cubeta x 30' where sku = 'HUE-AA-30';
select prueba.ok((select datos_despues ->> 'nombre' = 'Huevo AA de pastoreo · cubeta x 30' and usuario_id = 1 and not (datos_despues ? 'sku')
                  from nucleo.auditoria where esquema_tabla = 'inventario.producto' and accion = 'actualizar' order by id desc limit 1),
                 'Auditoría: guarda solo el campo cambiado y quién lo cambió');
select prueba.esperar_error($$delete from nucleo.auditoria$$, 'permission denied', 'Auditoría: la API no puede borrarla');

-- 6. Cuadre contable
insert into finanzas.comprobante (tipo, numero, fecha, descripcion) values ('ingreso', 'RC-1', current_date, 'Venta PED-1');
insert into finanzas.movimiento_contable (comprobante_id, cuenta_id, debito, credito)
select c.id, cu.id, x.d, x.c from finanzas.comprobante c, (values ('1105', 1170000, 0), ('4120', 0, 1100000)) x(cta, d, c)
join finanzas.cuenta_contable cu on cu.codigo = x.cta where c.numero = 'RC-1';
select prueba.esperar_error($$update finanzas.comprobante set estado = 'contabilizado' where numero = 'RC-1'; set constraints all immediate$$, 'descuadrado', 'Contabilidad: no contabiliza si débitos ≠ créditos');
update finanzas.movimiento_contable set credito = 1170000 where credito = 1100000;
update finanzas.comprobante set estado = 'contabilizado' where numero = 'RC-1';
set constraints all immediate;
select prueba.ok((select contabilizado_en is not null from finanzas.comprobante where numero = 'RC-1'), 'Contabilidad: cuadrado, se contabiliza y registra el momento');
select prueba.esperar_error($$update finanzas.movimiento_contable set debito = 1 where debito = 1170000$$, 'no se pueden cambiar', 'Contabilidad: contabilizado = movimientos inmutables');
select prueba.esperar_error($$update finanzas.comprobante set descripcion = 'otra' where numero = 'RC-1'$$, 'solo se puede anular', 'Contabilidad: solo se anula, con motivo');
insert into finanzas.comprobante (tipo, numero, fecha, descripcion) values ('egreso', 'CE-1', '2026-01-15', 'Compra en periodo sin abrir');
select prueba.esperar_error($$update finanzas.comprobante set estado = 'contabilizado' where numero = 'CE-1'$$, 'cerrado o no existe', 'Contabilidad: periodo cerrado o inexistente');

-- 7. Reglas de canal
insert into redes.cuenta_red (plataforma, nombre_cuenta, identificador_externo, secreto_ref) values
 ('whatsapp', '+57 300 000 0000', 'wa-1', 'WHATSAPP_TOKEN'), ('instagram', '@elguayacan', 'ig-1', 'META_TOKEN'), ('tiktok', '@elguayacan', 'tt-1', 'TIKTOK_TOKEN');
insert into redes.plantilla_mensaje (cuenta_red_id, nombre, categoria, cuerpo, estado_meta, finalidad_requerida)
select id, 'promo_semana', 'marketing', 'Hola {{1}}, esta semana...', 'aprobada', 'publicidad' from redes.cuenta_red where plataforma = 'whatsapp';
select prueba.ok(redes.verificar_envio((select id from redes.cuenta_red where plataforma = 'whatsapp'), (select id from terceros.tercero limit 1), now() - interval '2 hours', false, 'agente') = 'permitido: servicio',
                 'WhatsApp: el agente responde dentro de las 24 h');
select prueba.ok(redes.verificar_envio((select id from redes.cuenta_red where plataforma = 'whatsapp'), (select id from terceros.tercero limit 1), now() - interval '30 hours', false, 'agente') like 'bloqueado: fuera de la ventana; solo con plantilla%',
                 'WhatsApp: a las 30 h exige plantilla aprobada');
select prueba.ok(redes.verificar_envio((select id from redes.cuenta_red where plataforma = 'whatsapp'), (select id from terceros.tercero limit 1), now() - interval '30 hours', false, 'agente',
                 (select id from redes.plantilla_mensaje where nombre = 'promo_semana')) like 'bloqueado: el cliente no ha autorizado publicidad%', 'WhatsApp: plantilla de mercadeo bloqueada sin consentimiento de publicidad');
select prueba.ok(redes.verificar_envio((select id from redes.cuenta_red where plataforma = 'instagram'), null, now() - interval '3 days', false, 'humano') = 'permitido: servicio',
                 'Instagram: una persona puede responder hasta 7 días (agente humano)');
select prueba.ok(redes.verificar_envio((select id from redes.cuenta_red where plataforma = 'instagram'), null, now() - interval '3 days', false, 'agente') like 'bloqueado: fuera de la ventana; el canal no permite%',
                 'Instagram: el agente de IA no puede usar la extensión de 7 días');
insert into redes.mensaje_saliente (cuenta_red_id, tercero_id, tipo, autor, dentro_ventana, enviado_en)
select cr.id, t.id, 'servicio', 'agente', true, now() - interval '1 hour' from redes.cuenta_red cr, terceros.tercero t, generate_series(1, 10) where cr.plataforma = 'tiktok';
select prueba.ok(redes.verificar_envio((select id from redes.cuenta_red where plataforma = 'tiktok'), (select id from terceros.tercero limit 1), now() - interval '5 hours', false, 'agente') like '%tope de mensajes%',
                 'TikTok: después de 10 mensajes en la ventana se detiene');

-- ===================================================================== v4
-- 8. Funciones por finca y finca de práctica
select prueba.ok(not nucleo.funcion_activa('venta_credito') and nucleo.funcion_activa('modo_aprendiz'), 'Funciones: crédito apagado y modo aprendiz encendido al iniciar');
select prueba.ok((select count(*) from nucleo.predio) = 1, 'Práctica: la finca real no ve la finca de práctica');
select set_config('app.predio_id', :'fp', false);
select prueba.ok((select count(*) from inventario.producto) = 0 and (select count(*) from inventario.lote_inventario) = 0, 'Práctica: en la finca de práctica no aparece nada de la finca real');
select set_config('app.predio_id', '1', false);
select prueba.esperar_error($$select count(*) from nucleo.auditoria_202610$$, 'permission denied', 'Particiones: la API solo lee la auditoría por la tabla madre (con seguridad por filas)');
select prueba.ok((select count(*) from nucleo.auditoria) > 0, 'Particiones: la auditoría se consulta normal por la tabla madre');

-- 9. Huevo: clasificación por peso
select prueba.ok(produccion.clasificar_por_peso(68) = 'aaa' and produccion.clasificar_por_peso(59.9) = 'a' and produccion.clasificar_por_peso(80) = 'jumbo',
                 'Huevo: 68 g = AAA, 59,9 g = A, 80 g = jumbo según los rangos vigentes');
insert into nucleo.zona (codigo, nombre, tipo_zona) values ('GAL-01', 'Galpón 1', 'galpon');
insert into produccion.lote_animal (codigo, especie_id, zona_id, proposito, fecha_ingreso, cantidad_inicial, cantidad_actual)
select 'AV-2026-01', e.id, z.id, 'postura', current_date - 120, 100, 100 from produccion.especie e, nucleo.zona z where e.codigo = 'gallina' and z.codigo = 'GAL-01';
insert into produccion.registro_postura (lote_animal_id, fecha, huevos_recogidos, huevos_rotos, registrado_por) select id, current_date, 100, 4, 1 from produccion.lote_animal;
insert into produccion.clasificacion_postura (registro_postura_id, categoria_huevo_id, cantidad, metodo)
select r.id, c.id, x.n, 'peso_bascula' from produccion.registro_postura r, (values ('aa', 60), ('a', 30)) x(cat, n) join produccion.categoria_huevo c on c.codigo = x.cat;
select prueba.esperar_error($$insert into produccion.clasificacion_postura (registro_postura_id, categoria_huevo_id, cantidad) select r.id, c.id, 10 from produccion.registro_postura r, produccion.categoria_huevo c where c.codigo = 'b'$$,
                            'solo hay 96 buenos', 'Huevo: la clasificación no supera los huevos buenos (100 − 4 rotos)');
select prueba.esperar_error($$insert into produccion.clasificacion_postura (registro_postura_id, categoria_huevo_id, cantidad, metodo) select r.id, c.id, 1, 'vision' from produccion.registro_postura r, produccion.categoria_huevo c where c.codigo = 'c'$$,
                            'vision_artificial no está activa', 'Huevo: la clasificación con visión espera su equipo (función apagada)');

-- 10. Cadena de frío: excursión, bloqueo automático y liberación humana
insert into iot.dispositivo (codigo, tipo, topico_mqtt) values ('REG-NEV-01', 'registrador_temperatura', 'guayacan/frio/nev01');
insert into iot.sensor (dispositivo_id, codigo, magnitud, unidad) select id, 'T-NEV-01', 'temperatura', '°C' from iot.dispositivo where codigo = 'REG-NEV-01';
update inventario.bodega set sensor_temperatura_id = (select id from iot.sensor where codigo = 'T-NEV-01') where codigo = 'NEV-01';
insert into inventario.lote_inventario (producto_id, bodega_id, codigo_lote, origen, fecha_produccion, condicion_almacenamiento, cantidad_inicial, costo_unitario)
select p.id, b.id, 'LOTE-N', 'produccion', current_date, 'refrigerado', 20, 11918 from inventario.producto p, inventario.bodega b where p.sku = 'HUE-AA-30' and b.codigo = 'NEV-01';
select prueba.ok((select fecha_vencimiento = current_date + 35 from inventario.lote_inventario where codigo_lote = 'LOTE-N'), 'Frío: un lote refrigerado usa la vida útil refrigerada (35 días)');
select prueba.ok((select cantidad_disponible from comercial.v_catalogo_disponible where sku = 'HUE-AA-30') = 49, 'Frío: antes de la excursión el catálogo ofrece 49 (29 + 20)');
insert into inventario.excursion_temperatura (sensor_id, bodega_id, inicio, temperatura_extrema_c, minutos_fuera)
select s.id, b.id, now() - interval '10 minutes', 11.5, 10 from iot.sensor s, inventario.bodega b where s.codigo = 'T-NEV-01' and b.codigo = 'NEV-01';
select prueba.ok((select lotes_bloqueados from inventario.excursion_temperatura) = 0, 'Frío: 10 minutos fuera de rango aún no bloquean (tolerancia 30)');
update inventario.excursion_temperatura set minutos_fuera = 45, fin = now(), estado = 'cerrada';
select prueba.ok((select lotes_bloqueados from inventario.excursion_temperatura) = 1 and (select estado from inventario.lote_inventario where codigo_lote = 'LOTE-N') = 'bloqueado',
                 'Frío: a los 45 minutos la regla bloquea el lote de la nevera');
select prueba.ok((select cantidad_disponible from comercial.v_catalogo_disponible where sku = 'HUE-AA-30') = 29, 'Frío: el catálogo deja de ofrecer el lote bloqueado');
select prueba.ok(not inventario.puede_venderse((select l from inventario.lote_inventario l where codigo_lote = 'LOTE-N')), 'Frío: la especificación "se puede vender" lo excluye');
select prueba.ok((select count(*) from nucleo.evento_salida where tipo_evento in ('lote.bloqueado', 'temperatura.fuera_de_rango')) = 2, 'Frío: publica los eventos lote.bloqueado y temperatura.fuera_de_rango');
select set_config('app.agente_id', (select id::text from ia.agente limit 1), false);
select prueba.esperar_error($$update inventario.bloqueo_lote set decision = 'liberado'$$, 'Solo una persona', 'Frío: un agente de IA no puede liberar un lote');
select set_config('app.agente_id', '', false);
update inventario.bloqueo_lote set decision = 'liberado', observacion = 'Revisado: huevo íntegro, temperatura recuperada';
select prueba.ok((select estado from inventario.lote_inventario where codigo_lote = 'LOTE-N') = 'disponible' and (select decidido_por from inventario.bloqueo_lote) = 1,
                 'Frío: una persona lo libera y queda registrado quién decidió');
select prueba.esperar_error($$update inventario.bloqueo_lote set decision = 'descartado'$$, 'ya fue decidido', 'Frío: una decisión tomada no se cambia');

-- 11. Trazabilidad y retiro de lotes
select prueba.ok((select cliente from comercial.v_trazabilidad_lote where codigo_lote = 'LOTE-A' and pedido = 'PED-1') = 'Cliente Prueba', 'Trazabilidad: el lote A llegó al cliente del pedido PED-1');
select comercial.abrir_retiro((select id from inventario.lote_inventario where codigo_lote = 'LOTE-A'), 'Prueba de retiro por sospecha sanitaria');
select prueba.ok((select count(*) from comercial.retiro_aviso) = 1 and (select cantidad from comercial.retiro_aviso) = 50 and (select estado from inventario.lote_inventario where codigo_lote = 'LOTE-A') = 'bloqueado',
                 'Retiro: bloquea el lote y crea el aviso al cliente que recibió 50');

-- 12. Cadena de huellas (lista para blockchain)
select prueba.ok((select bool_and(valida) and count(*) >= 8 from comercial.verificar_cadena_huellas()), 'Huellas: la cadena SHA-256 de la finca se verifica completa');
select prueba.esperar_error($$update comercial.huella_trazabilidad set contenido = '{}' where id = (select min(id) from comercial.huella_trazabilidad)$$, 'permission denied', 'Huellas: nadie puede alterar una huella');
update comercial.huella_trazabilidad set anclaje_red = 'red_de_prueba', anclaje_transaccion = 'tx-1', anclado_en = now() where id = (select min(id) from comercial.huella_trazabilidad);
select prueba.ok((select bool_and(valida) from comercial.verificar_cadena_huellas()), 'Huellas: registrar el anclaje no rompe la cadena');

-- 13. Venta a crédito (apagada hasta que se decida)
update terceros.cliente set cupo_credito = 500000, dias_plazo = 30;
insert into comercial.pedido (numero, cliente_id, canal, forma_pago) select 'PED-C1', id, 'whatsapp', 'credito' from terceros.cliente;
insert into comercial.pedido_detalle (pedido_id, producto_id, cantidad, precio_producto_id, precio_unitario, total_linea)
select pe.id, pp.producto_id, 20, pp.id, pp.precio_unitario, 20 * pp.precio_unitario
from comercial.pedido pe, comercial.precio_producto pp join inventario.producto p on p.id = pp.producto_id and p.sku = 'HUE-AA-30' where pe.numero = 'PED-C1';
select prueba.esperar_error($$select comercial.confirmar_pedido((select id from comercial.pedido where numero = 'PED-C1'))$$, 'venta_credito no está activa', 'Crédito: apagado, no se vende a crédito');
update nucleo.funcionalidad set activa = true where codigo = 'venta_credito';
select prueba.ok((select activada_por = 1 and activada_en is not null from nucleo.funcionalidad where codigo = 'venta_credito'), 'Funciones: encender una función registra quién y cuándo');
select comercial.confirmar_pedido((select id from comercial.pedido where numero = 'PED-C1'));
insert into comercial.factura (prefijo, numero, pedido_id, cliente_id, fecha_emision, subtotal, iva, total, forma_pago)
select 'FE', 1, id, cliente_id, now(), total, 0, total, 'credito' from comercial.pedido where numero = 'PED-C1';
select prueba.ok((select saldo = 390000 and fecha_vencimiento = current_date + 30 from comercial.factura where numero = 1), 'Crédito: factura de $390.000 con saldo completo y vence a 30 días');
insert into comercial.pedido (numero, cliente_id, canal, forma_pago) select 'PED-C2', id, 'whatsapp', 'credito' from terceros.cliente;
insert into comercial.pedido_detalle (pedido_id, producto_id, cantidad, precio_producto_id, precio_unitario, total_linea)
select pe.id, pp.producto_id, 10, pp.id, pp.precio_unitario, 10 * pp.precio_unitario
from comercial.pedido pe, comercial.precio_producto pp join inventario.producto p on p.id = pp.producto_id and p.sku = 'HUE-AA-30' where pe.numero = 'PED-C2';
select prueba.esperar_error($$select comercial.confirmar_pedido((select id from comercial.pedido where numero = 'PED-C2'))$$, 'Cupo de crédito insuficiente', 'Crédito: no pasa del cupo ($390.000 + $195.000 > $500.000)');
update comercial.factura set fecha_vencimiento = current_date - 5 where numero = 1;
select comercial.actualizar_mora();
select prueba.ok((select bloqueado_por_mora from terceros.cliente) and (select edad from comercial.v_cartera where factura = 'FE-1') = '1_30', 'Crédito: factura vencida hace 5 días = cartera de 1 a 30 días y cliente bloqueado');
select prueba.esperar_error($$select comercial.confirmar_pedido((select id from comercial.pedido where numero = 'PED-C2'))$$, 'facturas vencidas', 'Crédito: cliente en mora no compra a crédito');
select set_config('app.agente_id', (select id::text from ia.agente limit 1), false);
select prueba.esperar_error($$insert into comercial.pago (factura_id, fecha, valor, medio, estado) select id, now(), 390000, 'nequi', 'confirmado' from comercial.factura where numero = 1$$, 'agente no puede confirmar', 'Pagos: un agente no confirma pagos');
select set_config('app.agente_id', '', false);
insert into comercial.pago (factura_id, fecha, valor, medio, estado, confirmado_por) select id, now(), 390000, 'nequi', 'confirmado', 1 from comercial.factura where numero = 1;
select comercial.actualizar_mora();
select prueba.ok((select saldo from comercial.factura where numero = 1) = 0 and not (select bloqueado_por_mora from terceros.cliente), 'Crédito: al pagar, el saldo queda en cero y se levanta el bloqueo');

-- 14. Permuta (apagada hasta que se decida)
insert into terceros.tercero (tipo_persona, nombres, es_proveedor) values ('natural', 'Vecino Proveedor', true);
insert into terceros.proveedor (tercero_id, categoria) select id, 'otro' from terceros.tercero where nombres = 'Vecino Proveedor';
insert into compras.documento_soporte (proveedor_id, prefijo, numero, fecha, descripcion, total) select id, 'DS', 1, current_date, 'Bulto de abono a cambio de huevo', 100000 from terceros.proveedor;
insert into comercial.factura (prefijo, numero, cliente_id, fecha_emision, subtotal, iva, total, forma_pago) select 'FE', 2, id, now(), 150000, 0, 150000, 'contado' from terceros.cliente;
select prueba.esperar_error($$insert into comercial.permuta (factura_id, documento_soporte_id, valor_compensado, acuerdo) select f.id, d.id, 100000, 'abono por huevo' from comercial.factura f, compras.documento_soporte d where f.numero = 2$$,
                            'permuta no está activa', 'Permuta: apagada, no se registra');
update nucleo.funcionalidad set activa = true where codigo = 'permuta';
insert into comercial.permuta (factura_id, documento_soporte_id, valor_compensado, acuerdo) select f.id, d.id, 100000, 'Un bulto de abono por huevo' from comercial.factura f, compras.documento_soporte d where f.numero = 2;
select prueba.ok((select saldo from comercial.factura where numero = 2) = 50000 and exists (select 1 from comercial.pago where medio = 'compensacion_permuta' and valor = 100000),
                 'Permuta: compensa $100.000 con un pago de compensación; la factura queda debiendo $50.000');
select prueba.esperar_error($$insert into comercial.permuta (factura_id, documento_soporte_id, valor_compensado, acuerdo) select f.id, d.id, 10000, 'otra' from comercial.factura f, compras.documento_soporte d where f.numero = 2$$,
                            'supera', 'Permuta: no compensa más de lo que vale el documento soporte');

-- 15. Pedidos recurrentes
insert into comercial.pedido_recurrente (cliente_id, frecuencia, proxima_fecha) select id, 'semanal', current_date from terceros.cliente;
insert into comercial.pedido_recurrente_detalle (pedido_recurrente_id, producto_id, cantidad) select r.id, p.id, 2 from comercial.pedido_recurrente r, inventario.producto p where p.sku = 'HUE-AA-30';
select prueba.ok(comercial.generar_pedidos_recurrentes() = 0, 'Recurrentes: con la función apagada no genera nada');
update nucleo.funcionalidad set activa = true where codigo = 'pedidos_recurrentes';
select prueba.ok(comercial.generar_pedidos_recurrentes() = 1, 'Recurrentes: genera el pedido del día');
select prueba.ok((select estado = 'borrador' from comercial.pedido where pedido_recurrente_id is not null) and (select proxima_fecha from comercial.pedido_recurrente) = current_date + 7,
                 'Recurrentes: queda en borrador para que un vendedor lo confirme y la próxima fecha pasa a dentro de 7 días');

-- 16. Audiovisual: consentimiento de imagen y retención de clips
insert into redes.pieza_audiovisual (tipo, guion, personas_identificables, estado) values ('video_promocional', 'Recolección de huevos al amanecer', true, 'propuesta');
insert into redes.pieza_persona (pieza_audiovisual_id, tercero_id) select p.id, t.id from redes.pieza_audiovisual p, terceros.tercero t where t.nombres = 'Cliente Prueba';
select prueba.esperar_error($$update redes.pieza_audiovisual set estado = 'aprobada'$$, 'Falta autorización de imagen', 'Audiovisual: no se aprueba si alguien que aparece no autorizó su imagen');
insert into terceros.consentimiento_datos (tercero_id, finalidad, version_politica, otorgado, medio, otorgado_en) select id, 'imagen_redes', '1.0', true, 'formulario_fisico', now() from terceros.tercero where nombres = 'Cliente Prueba';
select set_config('app.agente_id', (select id::text from ia.agente limit 1), false);
select prueba.esperar_error($$update redes.pieza_audiovisual set estado = 'aprobada'$$, 'Solo una persona aprueba', 'Audiovisual: un agente no aprueba contenido');
select set_config('app.agente_id', '', false);
update redes.pieza_audiovisual set estado = 'aprobada';
select prueba.ok((select aprobado_por from redes.pieza_audiovisual) = 1, 'Audiovisual: con autorización, una persona la aprueba');
insert into iot.dispositivo (codigo, tipo, topico_mqtt) values ('CAM-01', 'camara', 'guayacan/camaras/cam01');
insert into iot.camara (dispositivo_id, tipo, retencion_dias, aviso_visible) select id, 'ip_rtsp', 30, true from iot.dispositivo where codigo = 'CAM-01';
insert into iot.clip_video (camara_id, inicio, fin, motivo, archivo_url, para_redes)
select c.id, x.ini, x.ini + interval '20 seconds', 'movimiento', 'pasarela://clips/' || x.n, x.redes from iot.camara c,
 (values (1, now() - interval '40 days', false), (2, now() - interval '40 days', true), (3, now() - interval '2 days', false)) x(n, ini, redes);
select prueba.ok(iot.depurar_clips() = 1, 'Cámaras: borra solo el clip de seguridad vencido (30 días); conserva el elegido para redes y el reciente');
select prueba.esperar_error($$insert into iot.camara (dispositivo_id, tipo) select id, 'termica' from iot.dispositivo where codigo = 'CAM-01'$$, 'camara_termica no está activa',
                            'Listo para crecer: la cámara térmica espera su equipo (función apagada)');

-- 17. Seguridad perimetral
select iot.cambiar_estado_alarma((select id from iot.zona_seguridad where codigo = 'SEG-ACC-01'), 'armado', 'app_nube');
select prueba.esperar_error($$select iot.cambiar_estado_alarma((select id from iot.zona_seguridad where codigo = 'SEG-ACC-01'), 'mantenimiento', 'app_nube')$$, 'no permitido',
                            'Alarma: de armado no se pasa a mantenimiento sin desarmar');
select prueba.esperar_error($$update iot.zona_seguridad set estado_alarma = 'desarmado' where codigo = 'SEG-ACC-01'$$, 'solo cambia con', 'Alarma: el estado no se edita directo');
select prueba.ok((select count(*) from iot.cambio_estado_alarma) = 1, 'Alarma: el cambio queda en el historial');
insert into iot.dispositivo (codigo, tipo, topico_mqtt) values ('CEN-01', 'central_alarma', 'guayacan/seguridad/central');
select prueba.esperar_error($$insert into iot.actuador (dispositivo_id, codigo, tipo, zona_seguridad_id, modo_falla) select d.id, 'CER-ACC', 'cerradura', z.id, 'cierra_sin_energia' from iot.dispositivo d, iot.zona_seguridad z where d.codigo = 'CEN-01' and z.codigo = 'SEG-ACC-01'$$,
                            'debe abrir sin energía', 'Seguridad: una cerradura en un paso de personas no puede quedar cerrada sin energía');
insert into iot.actuador (dispositivo_id, codigo, tipo, zona_seguridad_id, modo_falla) select d.id, 'CER-BOD', 'cerradura', z.id, 'cierra_sin_energia' from iot.dispositivo d, iot.zona_seguridad z where d.codigo = 'CEN-01' and z.codigo = 'SEG-BOD-01';
select prueba.ok(exists (select 1 from iot.actuador where codigo = 'CER-BOD'), 'Seguridad: la bodega de concentrado sí puede quedar cerrada sin energía');
insert into iot.evento_seguridad (zona_seguridad_id, tipo, detector, severidad, estado_alarma, ocurrido_en)
select id, 'intrusion', 'pir', 'alta', 'armado', now() from iot.zona_seguridad where codigo = 'SEG-ACC-01';
select prueba.esperar_error($$update iot.evento_seguridad set tipo = 'puerta_abierta'$$, 'no se modifica', 'Seguridad: un evento no se altera');
update iot.evento_seguridad set atendido_por = 1, atendido_en = now(), nota_atencion = 'Perro en el lindero';
select prueba.ok((select atendido_por from iot.evento_seguridad) = 1, 'Seguridad: se registra la atención del evento');

-- 18. Credenciales: PIN siempre; rostro solo con función activa y autorización expresa
insert into iot.credencial_acceso (tercero_id, metodo, referencia_hash, vigente_desde) select id, 'pin', 'hash-pin', current_date from terceros.tercero where nombres = 'Cliente Prueba';
select prueba.esperar_error($$insert into iot.credencial_acceso (tercero_id, metodo, consentimiento_id, vigente_desde) select t.id, 'facial', c.id, current_date from terceros.tercero t join terceros.consentimiento_datos c on c.tercero_id = t.id where t.nombres = 'Cliente Prueba'$$,
                            'reconocimiento_facial no está activa', 'Biometría: el rostro espera su equipo (función apagada)');
update nucleo.funcionalidad set activa = true where codigo = 'reconocimiento_facial';
select prueba.esperar_error($$insert into iot.credencial_acceso (tercero_id, metodo, consentimiento_id, vigente_desde) select t.id, 'facial', c.id, current_date from terceros.tercero t join terceros.consentimiento_datos c on c.tercero_id = t.id where t.nombres = 'Cliente Prueba'$$,
                            'autorización expresa', 'Biometría: una autorización de imagen no sirve para biometría');
insert into terceros.consentimiento_datos (tercero_id, finalidad, version_politica, otorgado, medio, otorgado_en) select id, 'biometria_acceso', '1.0', true, 'formulario_fisico', now() from terceros.tercero where nombres = 'Cliente Prueba';
insert into iot.credencial_acceso (tercero_id, metodo, consentimiento_id, vigente_desde) select t.id, 'facial', c.id, current_date from terceros.tercero t join terceros.consentimiento_datos c on c.tercero_id = t.id and c.finalidad = 'biometria_acceso' where t.nombres = 'Cliente Prueba';
update terceros.consentimiento_datos set revocado_en = now() where finalidad = 'biometria_acceso';
select prueba.ok(not (select activa from iot.credencial_acceso where metodo = 'facial') and (select activa from iot.credencial_acceso where metodo = 'pin'),
                 'Biometría: al revocar la autorización se apaga el acceso facial; el PIN sigue');

-- 19. Indicadores ambientales
insert into ambiental.registro_ambiental (magnitud, cantidad, fecha, origen) values ('kwh_solar', 100, current_date, 'manual');
select prueba.ok((select kgco2e_estimado from ambiental.v_indicadores) is null, 'Ambiental: sin factor con fuente no se calcula CO₂');
insert into ambiental.factor_emision (magnitud, factor_kgco2e, fuente, vigente_desde) values ('kwh_solar', 0.1, 'Factor de prueba (no oficial)', '2026-01-01');
select prueba.ok((select kgco2e_estimado = 10 and fuente is not null from ambiental.v_indicadores), 'Ambiental: CO₂ estimado = cantidad × factor, con la fuente a la vista');

reset role;
select 'TODAS LAS PRUEBAS PASARON' as resultado;

