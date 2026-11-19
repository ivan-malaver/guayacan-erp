-- GuayacanERP · Pruebas del apéndice A (adopción). Base nueva: esquema v5 + datos iniciales + apendice_a_adopcion.sql.
-- Corren con SET ROLE guayacan_app (sin saltar la seguridad por filas).
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
  begin execute p_sql;
  exception when others then
    if sqlerrm ilike '%' || p_patron || '%' then raise notice 'OK  % -> "%"', p_nombre, sqlerrm; return; end if;
    raise exception 'FALLA: % (error distinto: %)', p_nombre, sqlerrm;
  end;
  raise exception 'FALLA: % (no hubo error)', p_nombre;
end $$;
grant usage on schema prueba to guayacan_app;
grant execute on all functions in schema prueba to guayacan_app;

set role guayacan_app;
select set_config('app.predio_id', '1', false), set_config('app.usuario_id', '1', false), set_config('app.agente_id', '', false);

-- Función apagada al instalar
insert into adopcion.plan (codigo, nombre, tipo, cultivo_id, precio_compra, precio_readopcion, cuota_mensual, costo_bien, costo_cuidado_mensual, meses_madurez, requiere_permiso)
select 'ARB-AGU', 'Aguacate injertado', 'frutal', id, 150000, 60000, 25000, 45000, 9000, 48, 'ninguno' from produccion.cultivo where codigo = 'aguacate';
insert into adopcion.plan (codigo, nombre, tipo, cultivo_id, precio_compra, precio_readopcion, cuota_mensual, costo_bien, costo_cuidado_mensual, meses_madurez, requiere_permiso)
select 'ARB-GUA', 'Guayacán rosado', 'maderable', id, 180000, 60000, 15000, 50000, 5000, 180, 'tala_car' from produccion.cultivo where codigo = 'guayacan';
insert into adopcion.plan (codigo, nombre, tipo, especie_id, precio_compra, precio_readopcion, cuota_mensual, costo_bien, costo_cuidado_mensual, meses_madurez, requiere_permiso)
select 'ANI-OVI', 'Cordera de pelo', 'ovino', id, 380000, 150000, 45000, 250000, 26000, 12, 'planta_beneficio' from produccion.especie where codigo = 'ovino';
insert into adopcion.sitio (zona_id, codigo, tipo) select id, 'HS-001', 'hoyo_siembra' from nucleo.zona where codigo = 'LOT-AG';
insert into adopcion.sitio (zona_id, codigo, tipo) select id, 'HS-002', 'hoyo_siembra' from nucleo.zona where codigo = 'LOT-AG';
insert into adopcion.bien (codigo, plan_id, sitio_id) select 'AGU-0001', p.id, s.id from adopcion.plan p, adopcion.sitio s where p.codigo = 'ARB-AGU' and s.codigo = 'HS-001';
insert into adopcion.bien (codigo, plan_id, sitio_id) select 'GUA-0001', p.id, s.id from adopcion.plan p, adopcion.sitio s where p.codigo = 'ARB-GUA' and s.codigo = 'HS-002';
insert into terceros.tercero (tipo_persona, tipo_documento, numero_documento, nombres, apellidos, correo) values
 ('natural', 'PAS', 'X1234567', 'Anna', 'Schmidt', 'anna@example.com'), ('natural', 'PAS', 'Y7654321', 'John', 'Miller', 'john@example.com');
select id as t_anna from terceros.tercero where numero_documento = 'X1234567' \gset
select id as t_john from terceros.tercero where numero_documento = 'Y7654321' \gset
select id as b_agu from adopcion.bien where codigo = 'AGU-0001' \gset
select id as b_gua from adopcion.bien where codigo = 'GUA-0001' \gset

select prueba.esperar_error(format($q$insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual, modalidad_siembra)
  values ('ADO-0', %s, %s, 'compra', 150000, 25000, 'propia')$q$, :b_agu, :t_anna), 'no está activa', 'La adopción nace apagada');
update nucleo.funcionalidad set activa = true where codigo = 'adopcion';

-- Compra con siembra por trabajador: exige autorización de datos para el video
select prueba.esperar_error(format($q$insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual, modalidad_siembra)
  values ('ADO-1', %s, %s, 'compra', 150000, 25000, 'trabajador')$q$, :b_agu, :t_anna), 'autorización de datos', 'Siembra por trabajador sin autorización: rechazada');
select prueba.esperar_error(format($q$insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual)
  values ('ADO-1', %s, %s, 'compra', 150000, 25000)$q$, :b_agu, :t_anna), 'siembra el árbol en persona', 'Un árbol exige elegir quién lo siembra');
insert into terceros.consentimiento_datos (tercero_id, finalidad, version_politica, otorgado, medio, otorgado_en)
values (:t_anna, 'seguimiento_adopcion', '2026-10', true, 'web', now());
insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, fecha, precio, cuota_mensual, modalidad_siembra, consentimiento_id)
select 'ADO-1', :b_agu, :t_anna, 'compra', '2026-01-10', 150000, 25000, 'trabajador', max(id) from terceros.consentimiento_datos where tercero_id = :t_anna;
select prueba.ok((select estado from adopcion.bien where id = :b_agu) = 'reservado', 'Comprado y sin sembrar: el árbol queda reservado');
select prueba.ok((select es_adoptante from terceros.tercero where id = :t_anna), 'El comprador queda marcado como adoptante');
select prueba.esperar_error(format($q$insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual, modalidad_siembra)
  values ('ADO-X', %s, %s, 'compra', 150000, 25000, 'propia')$q$, :b_agu, :t_john), 'no está disponible', 'No se vende dos veces el mismo árbol');

-- Siembra
select prueba.esperar_error(format('select adopcion.registrar_siembra(%s, %L)', :b_agu, '2026-01-15'), 'exige el video', 'Siembra por trabajador sin video: rechazada');
select adopcion.registrar_siembra(:b_agu, '2026-01-15', null, 'https://minio.local/adopcion/AGU-0001.mp4');
select prueba.ok((select estado from adopcion.bien where id = :b_agu) = 'activo'
  and (select estado from adopcion.sitio where codigo = 'HS-001') = 'ocupado', 'Sembrado: árbol activo y sitio ocupado');
select prueba.ok(exists (select 1 from adopcion.seguimiento where bien_id = :b_agu and tipo = 'video_siembra')
  and exists (select 1 from nucleo.evento_salida where tipo_evento = 'adopcion.sembrado'), 'Queda el video en la bitácora y el evento para enviarlo');

-- Cuotas: el precio cubre el mes de compra; desde el mes siguiente una cuota por mes, sin duplicar
select prueba.ok(adopcion.generar_cuotas('2026-01-01') = 0, 'El mes de compra no genera cuota');
select adopcion.generar_cuotas('2026-02-01'); select adopcion.generar_cuotas('2026-02-01');
select adopcion.generar_cuotas('2026-03-01'); select adopcion.generar_cuotas('2026-04-01');
select prueba.ok((select count(*) from adopcion.cuota q join adopcion.contrato c on c.id = q.contrato_id where c.numero = 'ADO-1') = 3, 'Tres meses, tres cuotas (idempotente)');

-- Mora y abandono: un aviso por cada cuota que se vence; abandono solo con el tercer aviso entregado y 15 días de gracia
select adopcion.marcar_abandono('2026-03-12'); select adopcion.marcar_abandono('2026-03-13');
select prueba.ok((select estado from adopcion.contrato where numero = 'ADO-1') = 'activo'
  and (select count(*) from adopcion.seguimiento where bien_id = :b_agu and tipo = 'aviso_mora') = 1, 'Con 2 cuotas vencidas: un solo aviso aunque la tarea corra cada día; el contrato sigue');
select prueba.ok(exists (select 1 from nucleo.evento_salida where tipo_evento = 'adopcion.aviso_mora'), 'El aviso sale al adoptante por el outbox');
select prueba.ok(adopcion.marcar_abandono('2026-04-20') = 0, 'Con 3 cuotas vencidas: todavía sin abandono');
select prueba.ok((select count(*) from adopcion.seguimiento where bien_id = :b_agu and tipo = 'aviso_mora') = 2, 'Con la tercera cuota vencida sale el último aviso');
select prueba.ok(adopcion.marcar_abandono('2026-05-20') = 0, 'Sin aviso entregado nunca hay abandono');
update adopcion.seguimiento set enviado_al_adoptante = true where bien_id = :b_agu and tipo = 'aviso_mora' and fecha::date = '2026-04-20';
select prueba.ok(adopcion.marcar_abandono('2026-05-04') = 0, 'Aviso entregado hace 14 días: todavía no');
select prueba.ok(adopcion.marcar_abandono('2026-05-05') = 1, 'Tercer aviso entregado y 15 días de gracia: el contrato termina por abandono');
select prueba.ok((select estado from adopcion.bien where id = :b_agu) = 'en_readopcion'
  and not exists (select 1 from adopcion.cuota q join adopcion.contrato c on c.id = q.contrato_id where c.numero = 'ADO-1' and q.estado = 'pendiente'),
  'El árbol pasa a readopción y las cuotas pendientes se anulan');

-- Readopción por otro turista
select prueba.esperar_error(format($q$insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual)
  values ('ADO-Y', %s, %s, 'readopcion', 60000, 25000)$q$, :b_gua, :t_john), 'no está en readopción', 'Solo se readopta lo abandonado');
insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, fecha, precio, cuota_mensual) values ('ADO-2', :b_agu, :t_john, 'readopcion', '2026-04-25', 60000, 25000);
select prueba.ok((select estado from adopcion.bien where id = :b_agu) = 'activo', 'Readoptado: el árbol vuelve a tener dueño');

-- Muerte en garantía: se repone gratis y el contrato sigue con el nuevo árbol
select adopcion.registrar_muerte(:b_agu, '2026-06-01', 'Pudrición de raíz por encharcamiento');
select prueba.ok((select b.codigo from adopcion.contrato c join adopcion.bien b on b.id = c.bien_id where c.numero = 'ADO-2') = 'AGU-0001-R',
  'Muerte en garantía: reposición sin costo y el contrato pasa al árbol nuevo');

-- Animal: compra, madurez, decisión del dueño, sacrificio con soporte y liquidación del 5 %
insert into produccion.lote_animal (codigo, especie_id, zona_id, proposito, fecha_ingreso, cantidad_inicial, cantidad_actual)
select 'OV-ADO', e.id, z.id, 'engorde', '2025-09-01', 1, 1 from produccion.especie e, nucleo.zona z where e.codigo = 'ovino' and z.codigo = 'LOT-AG';
insert into produccion.animal (lote_animal_id, identificador, sexo) select id, 'OV-ADO-01', 'hembra' from produccion.lote_animal where codigo = 'OV-ADO';
insert into adopcion.bien (codigo, plan_id, animal_id) select 'OVI-0001', p.id, a.id from adopcion.plan p, produccion.animal a where p.codigo = 'ANI-OVI' and a.identificador = 'OV-ADO-01';
select id as b_ovi from adopcion.bien where codigo = 'OVI-0001' \gset
select prueba.esperar_error(format($q$insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual, modalidad_siembra)
  values ('ADO-Z', %s, %s, 'compra', 380000, 45000, 'trabajador')$q$, :b_ovi, :t_john), 'solo aplica a árboles', 'Un animal no tiene modalidad de siembra');
insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, fecha, precio, cuota_mensual) values ('ADO-3', :b_ovi, :t_john, 'compra', '2025-09-05', 380000, 45000);
select prueba.ok((select estado from adopcion.bien where id = :b_ovi) = 'activo', 'El animal comprado queda activo desde la compra');
select prueba.esperar_error($q$update adopcion.contrato set decision_madurez = 'liquidar' where numero = 'ADO-3'$q$, 'todavía no llega', 'No se decide antes de la madurez');
select prueba.ok(adopcion.marcar_madurez('2026-10-01') = 1, 'A los 12 meses la cordera llega a su madurez');
select set_config('app.agente_id', '1', false);
select prueba.esperar_error($q$update adopcion.contrato set decision_madurez = 'liquidar' where numero = 'ADO-3'$q$, 'Un agente de IA no puede', 'Un agente no decide por el dueño');
select set_config('app.agente_id', '', false);
update adopcion.contrato set decision_madurez = 'liquidar' where numero = 'ADO-3';
select id as c_ovi from adopcion.contrato where numero = 'ADO-3' \gset
select prueba.esperar_error(format($q$insert into adopcion.liquidacion (contrato_id, tipo, ingresos, gastos, estado)
  values (%s, 'sacrificio', 517500, 95000, 'aprobada')$q$, :c_ovi), 'exige el soporte', 'Sacrificio sin certificado de planta de beneficio: rechazado');
insert into documental.documento (codigo, titulo, tipo, entidad_emisora) values ('PB-2026-001', 'Certificado de beneficio OVI-0001', 'registro', 'Planta de beneficio autorizada INVIMA');
insert into adopcion.liquidacion (contrato_id, tipo, periodo_hasta, ingresos, gastos, estado, soporte_documento_id)
select :c_ovi, 'sacrificio', '2026-10-20', 517500, 95000, 'aprobada', id from documental.documento where codigo = 'PB-2026-001';
select prueba.ok((select utilidad_neta = 422500 and comision = 21125 and abono_adoptante = 401375 from adopcion.liquidacion where contrato_id = :c_ovi),
  'Liquidación: utilidad 422.500, comisión 5 % = 21.125, abono 401.375');
select prueba.ok((select estado from adopcion.bien where id = :b_ovi) = 'liquidado'
  and (select estado from adopcion.contrato where id = :c_ovi) = 'terminado_liquidacion', 'Liquidado: bien y contrato cerrados');
select prueba.esperar_error(format('update adopcion.liquidacion set gastos = 0 where contrato_id = %s', :c_ovi), 'ya fue', 'Una liquidación aprobada no cambia');

-- Saldo: compensa las cuotas pendientes del mismo adoptante y nunca queda negativo
select adopcion.generar_cuotas('2026-07-01');
select prueba.ok((select count(*) from adopcion.cuota q join adopcion.contrato c on c.id = q.contrato_id where c.numero = 'ADO-2' and q.estado = 'compensada') >= 1,
  'El abono de la liquidación paga las cuotas del otro árbol de John');
select prueba.esperar_error(format($q$insert into adopcion.movimiento_saldo (adoptante_id, tipo, valor) values (%s, 'pago_al_adoptante', 99999999)$q$, :t_john),
  'Saldo insuficiente', 'No se paga más que el saldo');
select prueba.esperar_error(format('update adopcion.movimiento_saldo set valor = 1 where adoptante_id = %s', :t_john), 'permission denied', 'La cuenta del adoptante es de solo inserción');

-- Productos sin utilidad: no hay comisión
insert into adopcion.liquidacion (contrato_id, tipo, ingresos, gastos, estado) select id, 'productos', 20000, 26000, 'aprobada' from adopcion.contrato where numero = 'ADO-2';
select prueba.ok((select comision = 0 and abono_adoptante = 0 and utilidad_neta = -6000 from adopcion.liquidacion where tipo = 'productos'),
  'Con pérdida no se cobra el 5 % ni se abona');

-- Tala de un maderable: exige decisión y permiso
insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual, modalidad_siembra) values ('ADO-4', :b_gua, :t_anna, 'compra', 180000, 15000, 'propia');
select prueba.esperar_error($q$insert into adopcion.liquidacion (contrato_id, tipo, ingresos, gastos) select id, 'tala', 1000000, 300000 from adopcion.contrato where numero = 'ADO-4'$q$,
  'no ha decidido liquidar', 'No se tala sin la decisión del dueño');

-- Cesión (regalo) del árbol a otra persona
insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual) select 'ADO-5', bien_id, :t_anna, 'cesion', 0, 25000 from adopcion.contrato where numero = 'ADO-2';
select prueba.ok((select estado from adopcion.contrato where numero = 'ADO-2') = 'cedido'
  and (select estado from adopcion.contrato where numero = 'ADO-5') = 'activo', 'Ceder: el contrato anterior queda cedido y el nuevo activo');

-- Otra finca no ve nada
select set_config('app.predio_id', '2', false);
select prueba.ok((select count(*) from adopcion.bien) = 0 and (select count(*) from adopcion.contrato) = 0, 'RLS: otra finca no ve bienes ni contratos');
select set_config('app.predio_id', '1', false);
select prueba.ok((select bienes_con_dueno from adopcion.v_tablero where tipo = 'frutal') = 1, 'Tablero por tipo');

-- ADO-02: el contrato nace pendiente de pago y solo toma el bien cuando la pasarela confirma
insert into adopcion.sitio (zona_id, codigo, tipo) select id, 'HS-003', 'hoyo_siembra' from nucleo.zona where codigo = 'LOT-AG';
insert into adopcion.bien (codigo, plan_id, sitio_id) select 'AGU-0002', p.id, s.id from adopcion.plan p, adopcion.sitio s where p.codigo = 'ARB-AGU' and s.codigo = 'HS-003';
select id as b_agu2 from adopcion.bien where codigo = 'AGU-0002' \gset
insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual, modalidad_siembra, estado)
values ('ADO-6', :b_agu2, :t_anna, 'compra', 150000, 25000, 'propia', 'pendiente_pago'),
       ('ADO-7', :b_agu2, :t_john, 'compra', 150000, 25000, 'propia', 'pendiente_pago');
select prueba.ok((select estado from adopcion.bien where id = :b_agu2) = 'disponible', 'Pendiente de pago: el bien sigue disponible');
update adopcion.contrato set estado = 'activo' where numero = 'ADO-6';
select prueba.ok((select estado from adopcion.bien where id = :b_agu2) = 'reservado', 'Pago confirmado: el árbol queda reservado');
select prueba.esperar_error($q$update adopcion.contrato set estado = 'activo' where numero = 'ADO-7'$q$, 'no está disponible',
  'Si otro pagó primero, el segundo pago no activa el contrato');
select prueba.esperar_error($q$update adopcion.contrato set estado = 'cedido' where numero = 'ADO-7'$q$, 'solo se activa o se cancela',
  'Un contrato pendiente solo se activa o se cancela');
select prueba.ok(adopcion.cancelar_pendientes_pago(0) = 1, 'El pendiente que no se paga vence');
select prueba.ok((select estado = 'cancelado' and terminado_en is not null from adopcion.contrato where numero = 'ADO-7'),
  'El contrato vencido queda cancelado y registrado');
select prueba.esperar_error($q$update adopcion.contrato set estado = 'activo' where numero = 'ADO-7'$q$, 'ya terminó',
  'Un contrato cancelado no revive');
select prueba.esperar_error(format($q$insert into adopcion.contrato (numero, bien_id, adoptante_id, tipo, precio, cuota_mensual, estado)
  values ('ADO-8', %s, %s, 'compra', 150000, 25000, 'cancelado')$q$, :b_agu2, :t_john), 'nace activo o pendiente', 'Un contrato no nace cancelado');
reset role;
select 'TODAS LAS PRUEBAS PASARON' as resultado;
