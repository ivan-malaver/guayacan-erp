-- GuayacanERP · Pruebas de las reglas de negocio v5 (PostgreSQL 18; también corren en 16 y 17)
-- Ejecutar como superusuario sobre una base recién creada con esquema_postgresql.sql + datos_iniciales.sql.
-- Cubre personal, áreas y cronogramas 24/7, formación (ISO 21001), nómina, activos, documental, cumplimiento, seguros, IA,
-- finanzas (costos, estados, indicadores, palancas, análisis vertical y horizontal), estrategia (VPN, TIR, ROI, reinversión),
-- agenda (cabañas, visitas, portería), proyectos (PMBOK 8), seguridad informática, CRM, robótica e integraciones.
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

-- ===================================================================== datos de la prueba (como instalador)
select set_config('app.predio_id', '1', false);
select set_config('app.usuario_id', '1', false);
insert into terceros.tercero (tipo_persona, nombres, apellidos) values
 ('natural', 'Operario', 'Uno'), ('natural', 'Jornalero', 'Dos'), ('natural', 'Encargado', 'Finca'), ('natural', 'Familia', 'Malaver'), ('natural', 'Contadora', 'Externa');
select id as t_op from terceros.tercero where nombres = 'Operario' \gset
select id as t_jor from terceros.tercero where nombres = 'Jornalero' \gset
select id as t_enc from terceros.tercero where nombres = 'Encargado' \gset
select id as t_fam from terceros.tercero where nombres = 'Familia' \gset
select id as t_con from terceros.tercero where nombres = 'Contadora' \gset
insert into nucleo.usuario (nombre_completo, correo, contrasena_hash, tercero_id) values
 ('Encargado', 'encargado@guayacan.local', 'x', :t_enc), ('Familia', 'familia@guayacan.local', 'x', :t_fam),
 ('Operario', 'operario@guayacan.local', 'x', :t_op), ('Contadora', 'contadora@guayacan.local', 'x', :t_con);
select id as u_enc from nucleo.usuario where correo = 'encargado@guayacan.local' \gset
select id as u_fam from nucleo.usuario where correo = 'familia@guayacan.local' \gset
select id as u_op from nucleo.usuario where correo = 'operario@guayacan.local' \gset
select id as u_con from nucleo.usuario where correo = 'contadora@guayacan.local' \gset
insert into nucleo.usuario_rol (usuario_id, rol_id) select u.id, r.id from nucleo.usuario u join nucleo.rol r on (u.correo, r.codigo) in
 (('encargado@guayacan.local', 'encargado_finca'), ('familia@guayacan.local', 'familia'), ('operario@guayacan.local', 'operario_granja'), ('contadora@guayacan.local', 'contador'));
insert into terceros.empleado (tercero_id, cargo, tipo_vinculacion, salario_base, forma_pago, valor_jornal, fecha_ingreso) values
 (:t_op, 'Operario de granja', 'termino_indefinido', 1750905, 'salario', null, '2026-10-01'),
 (:t_jor, 'Jornalero', 'jornal', null, 'jornal', 70000, '2026-10-01'),
 (:t_enc, 'Encargado', 'termino_indefinido', 2500000, 'salario', null, '2026-10-01');
select id as e_op from terceros.empleado where tercero_id = :t_op \gset
select id as e_jor from terceros.empleado where tercero_id = :t_jor \gset
select id as e_enc from terceros.empleado where tercero_id = :t_enc \gset
insert into nucleo.zona (predio_id, codigo, nombre, tipo_zona) values (1, 'GAL-01', 'Galpón 1', 'galpon');
-- Áreas: el operario es del galpón y responsable de cultivos; el jornalero es de cultivos; cuatro vigilantes para la operación 24/7
insert into personal.miembro_area (predio_id, area_id, empleado_id, es_responsable, desde)
select 1, a.id, x.e, x.r, '2026-10-01' from personal.area_responsabilidad a join (values ('AR-GALPON', :e_op, false), ('AR-CULTIVOS', :e_op, true), ('AR-CULTIVOS', :e_jor, false)) x(ar, e, r) on a.codigo = x.ar;
insert into terceros.tercero (predio_id, tipo_persona, nombres) select 1, 'natural', 'Vigilante ' || g from generate_series(1, 4) g;
insert into terceros.empleado (predio_id, tercero_id, cargo, tipo_vinculacion, salario_base, forma_pago, fecha_ingreso)
select 1, t.id, 'Vigilante', 'termino_indefinido', 1750905, 'salario', '2026-11-01' from terceros.tercero t where t.nombres like 'Vigilante %';
insert into personal.miembro_area (predio_id, area_id, empleado_id, desde)
select 1, a.id, e.id, '2026-10-01' from personal.area_responsabilidad a, terceros.empleado e where a.codigo = 'AR-VIGILANCIA' and e.cargo = 'Vigilante';
select id as z_gal from nucleo.zona where codigo = 'GAL-01' \gset
select id as z_pl from nucleo.zona where codigo = 'LOT-PL' \gset

-- ===================================================================== sesión de la API en la finca 1
set role guayacan_app;
select set_config('app.predio_id', '1', false);
select set_config('app.usuario_id', '1', false);
select set_config('app.agente_id', '', false);

-- 1. Formación y habilitaciones
select prueba.esperar_error(format($$insert into personal.tarea (plantilla_tarea_id, titulo, fecha, empleado_id)
  select id, 'Recoger huevos', current_date, %s from personal.plantilla_tarea where codigo = 'REC-HUEVO-AM'$$, :e_op),
  'no está habilitado', 'Personal: no se asigna una tarea a quien no tiene la habilitación');
insert into formacion.inscripcion (curso_id, tercero_id) select id, :t_op from formacion.curso where codigo = 'BIO-AVI';
select prueba.esperar_error(format($$update formacion.inscripcion set estado = 'aprobado', nota = 3.0 where tercero_id = %s$$, :t_op),
  'menor que la mínima', 'Formación: con nota menor a la mínima no se aprueba');
update formacion.inscripcion set estado = 'aprobado', nota = 4.2 where tercero_id = :t_op;
select prueba.ok((select count(*) = 1 and min(vence_en) = (current_date + interval '12 months')::date from formacion.certificado where tercero_id = :t_op),
  'Formación: aprobar el curso emite el certificado con vencimiento a 12 meses');
select prueba.ok((select formacion.esta_habilitado(:t_op, c.id) from formacion.competencia c where c.codigo = 'bioseguridad_avicola'),
  'Formación: el certificado crea la habilitación');
select prueba.esperar_error($$insert into formacion.curso (codigo, nombre, modalidad, origen) values ('MOO-1', 'Curso Moodle', 'virtual', 'moodle')$$,
  'cursos_externos', 'Formación: un curso de Moodle exige la función cursos_externos');
insert into formacion.certificado (tercero_id, competencia_id, inscripcion_id, emitido_en, vence_en, codigo_verificacion)
select :t_jor, c.id, i.id, current_date - 400, current_date - 1, 'VENCIDO-1' from formacion.competencia c, formacion.inscripcion i where c.codigo = 'aplicar_vacunas' limit 1;
select prueba.ok((select not formacion.esta_habilitado(:t_jor, c.id) from formacion.competencia c where c.codigo = 'aplicar_vacunas'),
  'Formación: un certificado vencido no habilita');
select prueba.ok(formacion.actualizar_habilitaciones() = 1, 'Formación: la tarea diaria retira la habilitación vencida');
insert into formacion.sesion_presencial (curso_id, instructor_id, fecha, duracion_horas) select id, :t_enc, current_date, 4 from formacion.curso where codigo = 'VAC-AVI';
insert into formacion.asistencia (sesion_id, tercero_id, asistio, nota) select id, :t_jor, true, 4 from formacion.sesion_presencial;
select prueba.ok((select formacion.certificar_sesion(id) from formacion.sesion_presencial) = 1, 'Formación: la asistencia presencial certifica igual que un curso virtual');

-- 2. Personal: disponibilidad, aprobación y plan de labores
insert into personal.ausencia (empleado_id, tipo, desde, hasta) values (:e_op, 'vacaciones', current_date + 1, current_date + 3);
select prueba.esperar_error(format($$insert into personal.tarea (plantilla_tarea_id, titulo, fecha, empleado_id)
  select id, 'Recoger huevos', current_date + 1, %s from personal.plantilla_tarea where codigo = 'REC-HUEVO-AM'$$, :e_op),
  'no está disponible', 'Personal: no se asigna a quien está de vacaciones');
insert into personal.tarea (plantilla_tarea_id, titulo, fecha, empleado_id)
select id, 'Recoger huevos', current_date, :e_op from personal.plantilla_tarea where codigo = 'REC-HUEVO-AM';
select id as tar1 from personal.tarea where titulo = 'Recoger huevos' \gset
select set_config('app.agente_id', (select id::text from ia.agente where codigo = 'coordinador'), false);
select prueba.esperar_error(format($$insert into personal.tarea (titulo, fecha, empleado_id, origen) values ('Propuesta', current_date, %s, 'agente')$$, :e_op),
  'no las asigna', 'Personal: el agente Coordinador propone pero no asigna');
insert into personal.tarea (titulo, fecha, origen) values ('Revisar cortinas del galpón', current_date, 'agente');
select prueba.ok((select count(*) = 1 from personal.tarea where origen = 'agente' and empleado_id is null), 'Personal: la propuesta del agente queda sin asignar');
select set_config('app.agente_id', '', false);
select prueba.esperar_error(format($$update personal.tarea set estado = 'aprobada' where id = %s$$, :tar1), 'terminada', 'Personal: solo se aprueba una tarea terminada');
update personal.tarea set estado = 'en_curso' where id = :tar1;
update personal.tarea set estado = 'terminada', cantidad = 96, unidad = 'huevos' where id = :tar1;
select set_config('app.usuario_id', :'u_op', false);
select prueba.esperar_error(format($$update personal.tarea set estado = 'aprobada' where id = %s$$, :tar1), 'personal.aprobar_tarea', 'Personal: el operario no tiene permiso para aprobar');
select set_config('app.usuario_id', :'u_enc', false);
select prueba.esperar_error(format($$update personal.tarea set estado = 'devuelta' where id = %s$$, :tar1), 'por qué', 'Personal: devolver exige comentario');
update personal.tarea set estado = 'aprobada' where id = :tar1;
select prueba.ok((select aprobado_por = :u_enc and aprobado_en is not null and iniciada_en is not null and terminada_en is not null from personal.tarea where id = :tar1),
  'Personal: el encargado aprueba y quedan las marcas de inicio, fin y aprobación');
select prueba.esperar_error(format($$update personal.tarea set cantidad = 200 where id = %s$$, :tar1), 'no se edita', 'Personal: una tarea aprobada no se edita');
insert into personal.tarea (titulo, fecha, empleado_id, estado) values ('Tarea del encargado', current_date, :e_enc, 'pendiente');
update personal.tarea set estado = 'terminada' where titulo = 'Tarea del encargado';
select prueba.esperar_error($$update personal.tarea set estado = 'aprobada' where titulo = 'Tarea del encargado'$$, 'propia tarea', 'Personal: nadie aprueba su propia tarea');
select set_config('app.usuario_id', '1', false);
select prueba.ok(personal.generar_tareas_del_dia(current_date + 7) >= 3, 'Personal: el plan de labores crea las tareas del día');
select prueba.ok(personal.generar_tareas_del_dia(current_date + 7) = 0, 'Personal: generar dos veces el mismo día no duplica');
select prueba.ok((select count(*) = 4 from personal.paso_tarea p join personal.tarea t on t.id = p.tarea_id
                  where t.fecha = current_date + 7 and t.titulo = 'Recoger huevos (mañana)'), 'Personal: la tarea del plan trae su lista de chequeo');
insert into personal.jornada (empleado_id, fecha, entrada, salida, labor, metodo_registro)
values (:e_jor, current_date, current_date + time '07:00', current_date + time '15:00', 'Deshierbe lote de plátano', 'qr');
select prueba.ok((select horas = 8 from personal.jornada where empleado_id = :e_jor), 'Personal: la jornada calcula las horas desde el carné');
select set_config('app.usuario_id', :'u_enc', false);
update personal.jornada set aprobada_por = :u_enc where empleado_id = :e_jor;
select set_config('app.usuario_id', '1', false);
select prueba.esperar_error(format($$insert into personal.credencial_trabajo (empleado_id, tipo, codigo_hash, emitida_en) values (%s, 'huella', repeat('a', 64), current_date)$$, :e_op),
  'check', 'Personal: el carné es QR o NFC, nunca biométrico');

-- 3. Nómina: prenómina, liquidación, cierre con dos personas y pagos
insert into personal.plantilla_tarea (codigo, nombre, proceso, recurrencia, forma_pago, valor_unitario, unidad_destajo, activa)
values ('COS-PLA', 'Cosecha de plátano a destajo', 'cosecha', 'unica', 'destajo', 500, 'kg', false);
insert into personal.tarea (plantilla_tarea_id, titulo, fecha, empleado_id) select id, 'Cosecha a destajo', current_date, :e_jor from personal.plantilla_tarea where codigo = 'COS-PLA';
update personal.tarea set estado = 'terminada', cantidad = 100 where titulo = 'Cosecha a destajo';
select set_config('app.usuario_id', :'u_enc', false);
update personal.tarea set estado = 'aprobada' where titulo = 'Cosecha a destajo';
select set_config('app.usuario_id', '1', false);
insert into nomina.periodo_nomina (codigo, tipo, desde, hasta) values ('2026-10', 'mensual', date_trunc('month', current_date), (date_trunc('month', current_date) + interval '1 month - 1 day')::date);
select id as per from nomina.periodo_nomina where codigo = '2026-10' \gset
select prueba.ok(nomina.preparar_prenomina(:per) = 6, 'Nómina: la prenómina reúne 2 salarios, 2 auxilios, 1 destajo y 1 jornal');
select prueba.ok((select valor = 1750905 and cantidad = 30 from nomina.novedad where empleado_id = :e_op and origen = 'contrato' and concepto_id = nomina.concepto('SALARIO')),
  'Nómina: salario de 30 días del contrato');
select prueba.ok((select valor = 50000 from nomina.novedad where empleado_id = :e_jor and origen = 'tarea'), 'Nómina: destajo de 100 kg a $500 desde la tarea aprobada');
select prueba.ok((select valor = 70000 from nomina.novedad where empleado_id = :e_jor and origen = 'jornada'), 'Nómina: jornal desde la jornada aprobada');
select prueba.esperar_error(format($$insert into nomina.novedad (periodo_id, empleado_id, concepto_id, valor, origen, tarea_id) values (%s, %s, nomina.concepto('SALARIO'), 1, 'tarea', %s)$$, :per, :e_op, :tar1),
  'no depende', 'Nómina: el salario de un contrato no depende de tareas');
select prueba.ok(nomina.liquidar(:per) = 3, 'Nómina: liquida a los 3 trabajadores');
select prueba.ok((select total_devengado = 2000000 and total_deducciones = 140072 and neto = 1859928 from nomina.liquidacion where empleado_id = :e_op),
  'Nómina: devengado 2.000.000, salud y pensión 4 % + 4 % sobre 1.750.905, neto 1.859.928');
select prueba.ok((select valor = 166600 from nomina.provision_prestacion where empleado_id = :e_op and tipo = 'cesantias'), 'Nómina: provisión de cesantías 8,33 %');
select prueba.ok((select count(*) = 0 from nomina.provision_prestacion where empleado_id = :e_jor), 'Nómina: el jornalero no provisiona prestaciones de contrato');
select prueba.esperar_error(format($$update nomina.periodo_nomina set estado = 'cerrado', cerrado_por = %s where id = %s$$, :u_fam, :per), 'dos personas', 'Nómina: el cierre necesita dos personas');
select prueba.esperar_error(format($$update nomina.periodo_nomina set estado = 'cerrado', cerrado_por = %s, aprobado_por = %s where id = %s$$, :u_fam, :u_enc, :per),
  'comprobante', 'Nómina: el cierre necesita su comprobante contabilizado');
begin;
insert into finanzas.comprobante (tipo, numero, fecha, descripcion) values ('nomina', 'NOM-2026-10', current_date, 'Causación nómina octubre');
insert into finanzas.movimiento_contable (comprobante_id, cuenta_id, centro_costo_id, debito)
select k.id, c.id, (select id from finanzas.centro_costo where codigo = 'ADM'), 2000000 from finanzas.comprobante k, finanzas.cuenta_contable c where k.numero = 'NOM-2026-10' and c.codigo = '5105';
insert into finanzas.movimiento_contable (comprobante_id, cuenta_id, credito)
select k.id, c.id, 2000000 from finanzas.comprobante k, finanzas.cuenta_contable c where k.numero = 'NOM-2026-10' and c.codigo = '2505';
update finanzas.comprobante set estado = 'contabilizado' where numero = 'NOM-2026-10';
commit;
select set_config('app.agente_id', (select id::text from ia.agente where codigo = 'asistente_contable'), false);
select prueba.esperar_error(format($$update nomina.periodo_nomina set estado = 'cerrado', cerrado_por = %s, aprobado_por = %s, comprobante_id = (select id from finanzas.comprobante where numero = 'NOM-2026-10') where id = %s$$, :u_fam, :u_enc, :per),
  'agente', 'Nómina: ningún agente cierra la nómina');
select set_config('app.agente_id', '', false);
update nomina.periodo_nomina set estado = 'cerrado', cerrado_por = :u_fam, aprobado_por = :u_enc, comprobante_id = (select id from finanzas.comprobante where numero = 'NOM-2026-10') where id = :per;
select prueba.ok((select bool_and(estado = 'aprobada') from nomina.liquidacion where periodo_id = :per), 'Nómina: al cerrar, las liquidaciones quedan aprobadas');
select prueba.esperar_error(format($$insert into nomina.novedad (periodo_id, empleado_id, concepto_id, valor, origen) values (%s, %s, nomina.concepto('PRESTAMO'), 1, 'manual')$$, :per, :e_op),
  'está cerrado', 'Nómina: un periodo cerrado no recibe novedades');
select prueba.esperar_error(format($$update nomina.periodo_nomina set hasta = hasta + 1 where id = %s$$, :per), 'nota de ajuste', 'Nómina: un periodo cerrado no se edita');
select id as liq_op from nomina.liquidacion where empleado_id = :e_op \gset
select id as liq_jor from nomina.liquidacion where empleado_id = :e_jor \gset
select prueba.esperar_error(format($$insert into nomina.pago_nomina (liquidacion_id, medio, valor, preparado_por, aprobado_por) values (%s, 'transferencia', 1859928, %s, %s)$$, :liq_op, :u_con, :u_con),
  'Quien prepara', 'Nómina: quien prepara el pago no lo aprueba');
select prueba.esperar_error(format($$insert into nomina.pago_nomina (liquidacion_id, medio, valor, preparado_por, aprobado_por) values (%s, 'transferencia', 1859928, %s, %s)$$, :liq_op, :u_con, :u_op),
  'propio pago', 'Nómina: nadie aprueba su propio pago');
select prueba.esperar_error(format($$insert into nomina.pago_nomina (liquidacion_id, medio, valor, preparado_por) values (%s, 'transferencia', 1859929, %s)$$, :liq_op, :u_con),
  'supera el neto', 'Nómina: no se paga más que el neto');
update nucleo.parametro set valor = '1000000' where clave = 'monto_doble_aprobacion';
insert into nomina.pago_nomina (liquidacion_id, medio, valor, preparado_por, aprobado_por) values (:liq_op, 'bre_b', 1859928, :u_con, :u_fam);
select prueba.esperar_error(format($$update nomina.pago_nomina set pagado_en = now() where liquidacion_id = %s$$, :liq_op), 'segunda aprobación', 'Nómina: pagos grandes necesitan segunda aprobación');
select prueba.esperar_error(format($$update nomina.pago_nomina set segunda_aprobacion_por = %s where liquidacion_id = %s$$, :u_fam, :liq_op), 'tercera persona', 'Nómina: la segunda aprobación es de otra persona');
update nomina.pago_nomina set segunda_aprobacion_por = :u_enc where liquidacion_id = :liq_op;
update nomina.pago_nomina set pagado_en = now(), referencia = 'BREB-001' where liquidacion_id = :liq_op;
select prueba.ok((select estado = 'pagada' from nomina.liquidacion where id = :liq_op), 'Nómina: pagada por completo, la liquidación queda pagada (aun con el periodo cerrado)');
select prueba.esperar_error(format($$insert into nomina.documento_nomina_electronica (liquidacion_id, proveedor) values (%s, 'dian_gratuito')$$, :liq_op),
  'nomina_electronica', 'Nómina: la nómina electrónica queda apagada hasta confirmar la obligación');

-- 4. Activos: uso, órdenes de trabajo y depreciación
insert into activos.activo (codigo, nombre, tipo, valor_compra, vida_util_meses, fecha_compra, responsable_id)
values ('ACT-GUA-01', 'Guadaña', 'herramienta', 1200000, 12, date_trunc('month', current_date) - interval '1 month', :e_op);
select id as act from activos.activo where codigo = 'ACT-GUA-01' \gset
insert into activos.plan_mantenimiento (activo_id, nombre, frecuencia_tipo, frecuencia_valor) values (:act, 'Cambio de aceite y afilado', 'horas', 50);
insert into activos.uso_activo (activo_id, fecha, horas) values (:act, current_date, 30);
select prueba.ok(activos.generar_ordenes_trabajo() = 0, 'Activos: con 30 horas aún no toca mantenimiento');
insert into activos.uso_activo (activo_id, fecha, horas) values (:act, current_date, 25);
select prueba.ok(activos.generar_ordenes_trabajo() = 1, 'Activos: a las 55 horas se crea la orden de trabajo');
select prueba.ok((select t.origen = 'orden_trabajo' and t.activo_id = :act from activos.orden_trabajo o join personal.tarea t on t.id = o.tarea_id), 'Activos: la orden llega como tarea');
select prueba.ok(activos.generar_ordenes_trabajo() = 0, 'Activos: no se duplica la orden abierta');
update activos.orden_trabajo set estado = 'cerrada' where activo_id = :act;
select prueba.ok((select ultima_lectura = 55 from activos.plan_mantenimiento where activo_id = :act), 'Activos: al cerrar, el plan reinicia desde el horómetro actual');
select prueba.ok(activos.depreciar_mes(current_date) = 1, 'Activos: se deprecia el activo del mes');
select prueba.ok((select valor = 100000 from activos.depreciacion where activo_id = :act), 'Activos: depreciación en línea recta 1.200.000 / 12');
select prueba.ok(activos.depreciar_mes(current_date) = 0, 'Activos: el mismo mes no se deprecia dos veces');

-- 5. Documental
insert into documental.documento (codigo, titulo, tipo) values ('PRT-BIO-01', 'Protocolo de bioseguridad del galpón', 'protocolo');
select id as doc from documental.documento where codigo = 'PRT-BIO-01' \gset
insert into documental.version_documento (documento_id, version, archivo_url, hash_sha256, estado) values (:doc, 1, 's3://doc/v1.pdf', repeat('1', 64), 'aprobada');
insert into documental.version_documento (documento_id, version, archivo_url, hash_sha256, estado) values (:doc, 2, 's3://doc/v2.pdf', repeat('2', 64), 'aprobada');
select prueba.ok((select string_agg(estado, ',' order by version) = 'obsoleta,aprobada' from documental.version_documento where documento_id = :doc),
  'Documental: aprobar la versión 2 vuelve obsoleta la 1');
select prueba.esperar_error(format($$update documental.version_documento set archivo_url = 'otro' where documento_id = %s and version = 2$$, :doc), 'no cambia su archivo', 'Documental: una versión aprobada no cambia su archivo');
select prueba.esperar_error(format($$select documental.documento_para_agente(%s)$$, :doc), 'autorizado para agentes', 'Documental: un agente no lee documentos no autorizados');
update documental.documento set uso_agentes = true where id = :doc;
select prueba.ok(documental.documento_para_agente(:doc) = 's3://doc/v2.pdf', 'Documental: el agente recibe solo la versión aprobada y vigente');
select set_config('app.agente_id', (select id::text from ia.agente where codigo = 'instructor'), false);
select prueba.esperar_error(format($$insert into documental.version_documento (documento_id, version, archivo_url, hash_sha256, estado) values (%s, 3, 'x', repeat('3', 64), 'aprobada')$$, :doc),
  'agente', 'Documental: un agente no aprueba documentos');
select set_config('app.agente_id', '', false);
select prueba.esperar_error($$insert into documental.documento (codigo, titulo, tipo, contiene_datos_personales) values ('CON-01', 'Contrato', 'contrato', true)$$,
  'check', 'Documental: con datos personales se exige finalidad y tiempo de conservación (Ley 1581)');

-- 6. Cumplimiento
select prueba.esperar_error($$insert into cumplimiento.expediente (norma_id) select id from cumplimiento.norma where codigo = 'ICA_BPA'$$,
  'certificacion_bpa', 'Cumplimiento: BPA queda cargada y apagada');
select id as exp from cumplimiento.expediente \gset
select prueba.ok(cumplimiento.evaluar_expediente(:exp) > 0, 'Cumplimiento: la granja biosegura aún tiene requisitos pendientes');
select prueba.ok((select ev.estado = 'cumple' from cumplimiento.evaluacion_requisito ev join cumplimiento.requisito q on q.id = ev.requisito_id where q.codigo = 'GAB-07'),
  'Cumplimiento: "personal capacitado" se cumple solo con las habilitaciones vigentes');
select prueba.ok((select ev.estado = 'cumple' from cumplimiento.evaluacion_requisito ev join cumplimiento.requisito q on q.id = ev.requisito_id where q.codigo = 'GAB-05'),
  'Cumplimiento: "procedimientos escritos" se cumple con el protocolo aprobado');
select prueba.ok((select ev.estado = 'no_cumple' from cumplimiento.evaluacion_requisito ev join cumplimiento.requisito q on q.id = ev.requisito_id where q.codigo = 'GAB-03'),
  'Cumplimiento: sin registros de desinfección recientes no se cumple');
insert into produccion.registro_bioseguridad (zona_id, fecha, tipo, responsable) select :z_gal, current_date, t, 'Operario' from (select (regexp_match(pg_get_constraintdef(oid), '''([a-z_]+)'''))[1] t from pg_constraint where conname = 'ck_registro_bioseguridad_tipo') x;
select cumplimiento.evaluar_expediente(:exp);
select prueba.ok((select ev.estado = 'cumple' from cumplimiento.evaluacion_requisito ev join cumplimiento.requisito q on q.id = ev.requisito_id where q.codigo = 'GAB-03'),
  'Cumplimiento: al registrar la desinfección, el requisito pasa a cumple');
insert into cumplimiento.evidencia_requisito (evaluacion_id, documento_id, descripcion, vence_en)
select ev.id, :doc, 'RSPA (copia)', current_date - 1 from cumplimiento.evaluacion_requisito ev join cumplimiento.requisito q on q.id = ev.requisito_id where q.codigo = 'GAB-01';
select cumplimiento.evaluar_expediente(:exp);
select prueba.ok((select ev.estado = 'no_cumple' from cumplimiento.evaluacion_requisito ev join cumplimiento.requisito q on q.id = ev.requisito_id where q.codigo = 'GAB-01'),
  'Cumplimiento: con la evidencia vencida el requisito pasa solo a no cumple');
insert into cumplimiento.no_conformidad (expediente_id, descripcion, severidad, detectada_en) values (:exp, 'Pediluvio sin cambiar', 'menor', current_date);
select prueba.esperar_error($$update cumplimiento.no_conformidad set estado = 'cerrada', verificacion = 'ok'$$, 'acciones correctivas', 'Cumplimiento: no se cierra sin acciones verificadas');
insert into cumplimiento.accion_correctiva (no_conformidad_id, descripcion, responsable_id, plazo) select id, 'Cambiar diario el pediluvio', :u_enc, current_date + 7 from cumplimiento.no_conformidad;
select prueba.esperar_error($$update cumplimiento.accion_correctiva set estado = 'verificada'$$, 'acción hecha', 'Cumplimiento: solo se verifica una acción hecha');
update cumplimiento.accion_correctiva set estado = 'hecha';
update cumplimiento.accion_correctiva set estado = 'verificada';
select prueba.esperar_error($$update cumplimiento.no_conformidad set estado = 'cerrada'$$, 'verificación', 'Cumplimiento: el cierre registra la verificación');
update cumplimiento.no_conformidad set estado = 'cerrada', verificacion = 'Se revisó durante una semana';
select prueba.ok((select cerrada_por = 1 and cerrada_en is not null from cumplimiento.no_conformidad), 'Cumplimiento: no conformidad cerrada con responsable');
insert into produccion.lote_animal (codigo, especie_id, zona_id, proposito, fecha_ingreso, cantidad_inicial, cantidad_actual)
select 'AV-2026-02', id, :z_gal, 'postura', current_date, 250, 250 from produccion.especie where codigo = 'gallina';
select prueba.ok((select situacion like 'alerta%' from cumplimiento.v_granja_biosegura), 'Cumplimiento: con 250 gallinas y sin certificado ICA hay alerta');

-- 7. Seguros
insert into terceros.tercero (tipo_persona, razon_social) values ('juridica', 'Aseguradora de prueba');
select id as t_aseg from terceros.tercero where razon_social = 'Aseguradora de prueba' \gset
insert into seguros.poliza (numero, aseguradora_id, tipo, desde, hasta, prima, incentivo_pct, suma_asegurada, estado)
values ('POL-1', :t_aseg, 'equipos', current_date - 10, current_date + 20, 1000000, 80, 50000000, 'vigente');
select prueba.ok((select valor_subsidiado = 800000 from seguros.poliza where numero = 'POL-1'), 'Seguros: el incentivo del 80 % queda como valor subsidiado');
select prueba.ok((select count(*) = 1 from seguros.v_por_vencer), 'Seguros: aviso de póliza próxima a vencer');
select prueba.esperar_error(format($$insert into seguros.poliza (numero, aseguradora_id, tipo, desde, hasta, prima, suma_asegurada) values ('POL-P', %s, 'parametrico', current_date, current_date + 365, 1, 1)$$, :t_aseg),
  'seguro_parametrico', 'Seguros: el paramétrico queda apagado');
insert into seguros.aviso_siniestro (poliza_id, detectado_en, descripcion) select id, now(), 'Daño de la bomba' from seguros.poliza where numero = 'POL-1';
select prueba.esperar_error($$update seguros.aviso_siniestro set estado = 'enviado'$$, 'se revisa', 'Seguros: no hay reclamación automática');
select set_config('app.agente_id', (select id::text from ia.agente where codigo = 'analista_negocio'), false);
select prueba.esperar_error($$update seguros.aviso_siniestro set estado = 'revisado'$$, 'agente', 'Seguros: un agente no revisa avisos');
select set_config('app.agente_id', '', false);
update seguros.aviso_siniestro set estado = 'revisado';
update seguros.aviso_siniestro set estado = 'enviado';
select prueba.ok((select revisado_por = 1 and enviado_en is not null from seguros.aviso_siniestro), 'Seguros: revisado por una persona y enviado');

-- 8. IA: diagnóstico por foto y registro de decisiones
select prueba.esperar_error($$insert into ia.diagnostico_imagen (agente_id, foto_url, objetivo, tomada_por) select id, 'f.jpg', 'hoja', 1 from ia.agente where codigo = 'agronomo'$$,
  'diagnostico_imagen', 'IA: el diagnóstico por foto queda apagado');
update nucleo.funcionalidad set activa = true where codigo = 'diagnostico_imagen';
insert into ia.diagnostico_imagen (agente_id, foto_url, objetivo, tomada_por, diagnostico_propuesto, confianza) select id, 'f.jpg', 'hoja', 1, 'Sigatoka negra', 0.82 from ia.agente where codigo = 'agronomo';
select set_config('app.agente_id', (select id::text from ia.agente where codigo = 'agronomo'), false);
select prueba.esperar_error($$update ia.diagnostico_imagen set estado = 'confirmado'$$, 'agente', 'IA: el agente no confirma su propio diagnóstico');
select set_config('app.agente_id', '', false);
update ia.diagnostico_imagen set estado = 'confirmado';
select prueba.ok((select diagnostico_final = 'Sigatoka negra' and revisado_por = 1 from ia.diagnostico_imagen), 'IA: confirmado por una persona');
insert into ia.decision (titulo, contexto, opciones) values ('Crecer el galpón', 'Pasar de 100 a 500 gallinas', '["sí", "no"]');
select set_config('app.agente_id', (select id::text from ia.agente where codigo = 'estratega'), false);
select prueba.esperar_error($$update ia.decision set opcion_elegida = 'sí'$$, 'agente', 'IA: un agente no toma decisiones');
select set_config('app.agente_id', '', false);
update ia.decision set opcion_elegida = 'sí';
select prueba.esperar_error($$update ia.decision set opcion_elegida = 'no'$$, 'decisión nueva', 'IA: una decisión tomada no se cambia');

-- 9. Finanzas: anticipos, clasificación de costos, presupuesto, estados, indicadores y palancas
insert into terceros.tercero (tipo_persona, razon_social, es_proveedor) values ('juridica', 'Concentrados SA', true), ('juridica', 'Otro proveedor', true);
insert into terceros.proveedor (tercero_id, categoria) select id, 'concentrado' from terceros.tercero where razon_social in ('Concentrados SA', 'Otro proveedor');
select p.id as prov from terceros.proveedor p join terceros.tercero t on t.id = p.tercero_id where t.razon_social = 'Concentrados SA' \gset
select p.id as prov2 from terceros.proveedor p join terceros.tercero t on t.id = p.tercero_id where t.razon_social = 'Otro proveedor' \gset
insert into finanzas.anticipo_proveedor (proveedor_id, fecha, valor) values (:prov, current_date, 500000);
insert into compras.orden_compra (numero, proveedor_id, fecha) values ('OC-1', :prov, current_date), ('OC-2', :prov2, current_date);
insert into finanzas.aplicacion_anticipo (anticipo_id, orden_compra_id, valor) select a.id, o.id, 300000 from finanzas.anticipo_proveedor a, compras.orden_compra o where o.numero = 'OC-1';
select prueba.ok((select saldo = 200000 from finanzas.anticipo_proveedor), 'Finanzas: el anticipo se descuenta en la compra');
select prueba.esperar_error($$insert into finanzas.aplicacion_anticipo (anticipo_id, orden_compra_id, valor) select a.id, o.id, 300000 from finanzas.anticipo_proveedor a, compras.orden_compra o where o.numero = 'OC-1'$$,
  'saldo de', 'Finanzas: el anticipo nunca queda negativo');
select prueba.esperar_error($$insert into finanzas.aplicacion_anticipo (anticipo_id, orden_compra_id, valor) select a.id, o.id, 1000 from finanzas.anticipo_proveedor a, compras.orden_compra o where o.numero = 'OC-2'$$,
  'otro proveedor', 'Finanzas: un anticipo solo se descuenta al mismo proveedor');
select prueba.esperar_error($$insert into finanzas.clasificacion_costo (cuenta_id, elemento, comportamiento, es_costo_producto) select id, 'cif', 'semivariable', true from finanzas.cuenta_contable where codigo = '1105'$$,
  'parte fija', 'Finanzas: un costo semivariable declara su parte fija');
insert into finanzas.presupuesto (nombre, anio, base_cero) values ('Presupuesto 2027', 2027, true);
select prueba.esperar_error($$insert into finanzas.presupuesto_detalle (presupuesto_id, componente, mes, valor) select id, 'ventas', 1, 1000 from finanzas.presupuesto$$,
  'se justifica', 'Finanzas: en base cero cada rubro se justifica');
insert into finanzas.presupuesto_detalle (presupuesto_id, componente, mes, valor, justificacion) select id, 'ventas', 1, 1000, 'Pedidos HORECA confirmados' from finanzas.presupuesto;
update finanzas.presupuesto set estado = 'aprobado';
select prueba.esperar_error($$insert into finanzas.presupuesto_detalle (presupuesto_id, componente, mes, valor, justificacion) select id, 'ventas', 2, 1, 'x' from finanzas.presupuesto$$,
  'aprobado', 'Finanzas: un presupuesto aprobado no cambia sus rubros');
-- Contabilidad del mes: ventas 10 M (AVI), costo variable 4 M (AVI), gasto fijo 2 M (AVI), intereses 0,5 M, capital 20 M, préstamo 5 M (+ nómina 2 M)
begin;
insert into finanzas.comprobante (tipo, numero, fecha, descripcion) values ('ingreso', 'P-1', current_date, 'Prueba');
insert into finanzas.movimiento_contable (comprobante_id, cuenta_id, centro_costo_id, debito, credito)
select k.id, c.id, cc.id, x.d, x.c from finanzas.comprobante k, (values
  ('1105', 'AVI', 10000000, 0), ('4120', 'AVI', 0, 10000000), ('6120', 'AVI', 4000000, 0), ('1430', 'AVI', 0, 4000000),
  ('5105', 'AVI', 2000000, 0), ('1110', null, 0, 2000000), ('5305', null, 500000, 0), ('1110', null, 0, 500000),
  ('1110', null, 20000000, 0), ('3105', null, 0, 20000000), ('1110', null, 5000000, 0), ('2105', null, 0, 5000000)) x(cta, cc, d, c)
join finanzas.cuenta_contable c on c.codigo = x.cta left join finanzas.centro_costo cc on cc.codigo = x.cc where k.numero = 'P-1';
update finanzas.comprobante set estado = 'contabilizado' where numero = 'P-1';
commit;
select (finanzas.estado_resultados(date_trunc('month', current_date)::date, current_date)) as er \gset
select prueba.ok(((:'er')::jsonb->>'margen_contribucion')::numeric = 6000000 and ((:'er')::jsonb->>'utilidad_operacional')::numeric = 2000000
                 and ((:'er')::jsonb->>'utilidad_neta')::numeric = 1500000, 'Finanzas: costeo variable: MC 6 M, UO 2 M, utilidad neta 1,5 M');
select prueba.ok((finanzas.balance_general(current_date)->>'cuadra')::boolean and (finanzas.balance_general(current_date)->>'activo_total')::numeric = 28500000,
  'Finanzas: el balance cuadra (activo 28,5 M = pasivo 7 M + patrimonio 21,5 M)');
select prueba.ok(finanzas.calcular_indicadores(date_trunc('month', current_date)::date, current_date) >= 20, 'Finanzas: se calculan los indicadores del periodo');
select prueba.ok((select round(v.valor, 2) = 3 from finanzas.valor_indicador v join finanzas.indicador i on i.id = v.indicador_id where i.codigo = 'gpo'), 'Finanzas: GPO = MC / UO = 3');
select prueba.ok((select round(v.valor, 2) = 1.33 from finanzas.valor_indicador v join finanzas.indicador i on i.id = v.indicador_id where i.codigo = 'gpf'), 'Finanzas: GPF = UO / (UO − I) = 1,33');
select prueba.ok((select round(v.valor, 4) = 4.0714 from finanzas.valor_indicador v join finanzas.indicador i on i.id = v.indicador_id where i.codigo = 'razon_corriente'), 'Finanzas: razón corriente 28,5 / 7');
select prueba.ok((select semaforo = 'sin_meta' from finanzas.valor_indicador v join finanzas.indicador i on i.id = v.indicador_id where i.codigo = 'rsp'), 'Finanzas: sin meta el semáforo lo dice');
select prueba.ok((select gpo = 2 and gpf = 1.25 and gpt = 2.5 and punto_equilibrio_unidades = 500 and margen_seguridad_pct = 50 from finanzas.palancas(1000, 100, 80, 10000, 2000)),
  'Finanzas: palancas del documento: PE = CF/(P−CV) = 500, GPO 2, GPF 1,25, GPT 2,5');
select prueba.esperar_error($$insert into finanzas.reporte_indicadores (destinatario, desde, hasta, contenido, hash_sha256, autorizado_por) values ('finagro', current_date, current_date, '{}', '', 1)$$,
  'indicadores_credito', 'Finanzas: los indicadores para crédito quedan apagados');
update nucleo.funcionalidad set activa = true where codigo = 'indicadores_credito';
select prueba.esperar_error($$insert into finanzas.reporte_indicadores (destinatario, desde, hasta, contenido, hash_sha256, autorizado_por) values ('finagro', current_date, current_date, '{"costos": 1}', '', 1)$$,
  'no lleva costos', 'Finanzas: el informe externo no lleva costos ni datos personales');
insert into finanzas.reporte_indicadores (destinatario, desde, hasta, contenido, hash_sha256, autorizado_por) values ('finagro', current_date, current_date, '{"postura_pct": 82}', '', 1);
select prueba.ok((select length(hash_sha256) = 64 from finanzas.reporte_indicadores), 'Finanzas: el informe queda con su huella verificable');

-- 10. Estrategia: iniciativas, evaluación y reinversión de utilidades
select set_config('app.agente_id', (select id::text from ia.agente where codigo = 'estratega'), false);
select prueba.esperar_error($$insert into estrategia.iniciativa (titulo, descripcion, ansoff, tipo, palanca, estado) values ('x', 'x', 'desarrollo_mercado', 'nuevo_mercado', 'mercadeo', 'aprobada')$$,
  'solo propone', 'Estrategia: un agente solo propone ideas');
insert into estrategia.iniciativa (titulo, descripcion, ansoff, tipo, palanca, linea_negocio_id)
select 'Huevo campesino para hoteles de Girardot', 'Abrir el canal HORECA con pedidos recurrentes', 'desarrollo_mercado', 'nuevo_mercado', 'mercadeo', id from estrategia.linea_negocio where codigo = 'AVI';
select prueba.ok((select agente_id is not null and estado = 'idea' from estrategia.iniciativa), 'Estrategia: la idea del agente queda registrada a su nombre');
select set_config('app.agente_id', '', false);
select id as ini from estrategia.iniciativa \gset
select prueba.esperar_error(format($$update estrategia.iniciativa set estado = 'aprobada' where id = %s$$, :ini), 'evaluación financiera', 'Estrategia: no se aprueba sin evaluación financiera');
insert into estrategia.evaluacion_proyecto (iniciativa_id, inversion_inicial, horizonte_meses, tasa_descuento_anual, precio_unitario, costo_variable_unitario, costos_fijos_mes, unidades_mes, fuente_fondos)
values (:ini, 12000000, 24, 0.15, 12000, 8000, 1000000, 500, 'utilidades_retenidas');
select prueba.ok(abs(estrategia.evaluar_proyecto((select id from estrategia.evaluacion_proyecto)) - 8815882.38) < 1, 'Estrategia: VPN al 15 % anual = 8.815.882');
select prueba.ok((select roi_pct = 100 and recuperacion_meses = 12 and punto_equilibrio_unidades = 250 and margen_seguridad_pct = 50 and gpo = 2
                    and abs(tir_anual - 1.1270) < 0.001 from estrategia.evaluacion_proyecto),
  'Estrategia: ROI 100 %, recuperación en 12 meses, equilibrio 250 cubetas, margen de seguridad 50 %, GPO 2, TIR 112,7 % anual');
update estrategia.iniciativa set estado = 'aprobada' where id = :ini;
select prueba.ok((select aprobada_por = 1 from estrategia.iniciativa), 'Estrategia: aprobada por una persona con su evaluación');
insert into estrategia.reinversion (anio, mes, linea_origen_id, utilidad_linea, valor, iniciativa_id, estado)
select extract(year from current_date), extract(month from current_date), id, 0, 1000000, :ini, 'aprobada' from estrategia.linea_negocio where codigo = 'AVI';
select prueba.ok((select utilidad_linea = 4000000 from estrategia.reinversion), 'Estrategia: la utilidad de la línea avícola (4 M) sale de la contabilidad');
select prueba.esperar_error(format($$insert into estrategia.reinversion (anio, mes, linea_origen_id, utilidad_linea, valor, iniciativa_id)
  select extract(year from current_date), extract(month from current_date), id, 0, 300000, %s from estrategia.linea_negocio where codigo = 'AVI'$$, :ini),
  'supera el tope', 'Estrategia: no se reinvierte más del 30 % de la utilidad de la línea');
select prueba.esperar_error(format($$insert into estrategia.reinversion (anio, mes, linea_origen_id, utilidad_linea, valor, iniciativa_id)
  select extract(year from current_date), extract(month from current_date), id, 0, 1000, %s from estrategia.linea_negocio where codigo = 'OVC'$$, :ini),
  'pérdida', 'Estrategia: no se reinvierte desde una línea sin utilidad');
insert into estrategia.seguimiento_iniciativa (iniciativa_id, mes, ingresos_reales, egresos_reales) values (:ini, date_trunc('month', current_date), 6000000, 4500000);
select prueba.ok((select reinvertido = 1000000 and roi_proyectado_pct = 100 and roi_real_pct is not null from estrategia.v_retorno_iniciativas), 'Estrategia: retorno proyectado contra real y lo reinvertido');
select prueba.ok((select utilidad_anio = 4000000 from estrategia.v_matriz_lineas where codigo = 'AVI'), 'Estrategia: matriz de líneas muestra la utilidad de cada sección');

-- 11. Seguridad informática: detector de ataques, señuelos, doble factor y vigilancia de privilegios
select prueba.ok((select bool_and(seguridad.registrar_intento('operario@guayacan.local', '200.1.1.1', false) = 'rechazado') from generate_series(1, 4)), 'Seguridad: 4 fallos se registran');
select prueba.ok(seguridad.registrar_intento('operario@guayacan.local', '200.1.1.1', false) = 'cuenta_bloqueada_ahora', 'Seguridad: al 5.º fallo en 15 minutos la cuenta se bloquea');
select prueba.ok(seguridad.registrar_intento('operario@guayacan.local', '200.1.1.1', true) = 'cuenta_bloqueada', 'Seguridad: con la cuenta bloqueada ni la contraseña correcta entra');
select prueba.ok((select count(*) = 1 from seguridad.alerta_seguridad where tipo = 'fuerza_bruta'), 'Seguridad: alerta de fuerza bruta');
select prueba.ok((select count(*) filter (where r <> 'ip_bloqueada_ahora') = 9 and count(*) filter (where r = 'ip_bloqueada_ahora') = 1
                  from (select seguridad.registrar_intento('usuario' || g || '@x.com', '10.0.0.9', false) r from generate_series(1, 10) g) x),
  'Seguridad: 10 cuentas distintas fallidas desde una IP la bloquean (relleno de credenciales)');
select prueba.ok(seguridad.registrar_intento('admin@guayacan.local', '10.0.0.9', true) = 'ip_bloqueada', 'Seguridad: la IP bloqueada no entra ni con clave correcta');
select prueba.ok(seguridad.registrar_intento('soporte.ti@guayacan.local', '10.0.0.50', false) = 'senuelo', 'Seguridad: tocar la cuenta señuelo delata al intruso');
select prueba.ok((select count(*) = 1 from seguridad.alerta_seguridad where tipo = 'senuelo' and severidad = 'critica') and seguridad.ip_bloqueada('10.0.0.50'),
  'Seguridad: el señuelo crea alerta crítica y bloquea la IP 24 horas');
insert into seguridad.sesion_usuario (usuario_id, metodo, ip, vence_en) values (:u_fam, 'contrasena', '190.1.1.1', now() + interval '8 hours');
select prueba.ok((select count(*) = 1 from seguridad.sesion_usuario where usuario_id = :u_fam), 'Seguridad: sesión normal de un usuario sin rol crítico');
select prueba.esperar_error(format($$insert into seguridad.sesion_usuario (usuario_id, metodo, ip, vence_en) values (%s, 'contrasena', '190.1.1.1', now() + interval '8 hours')$$, :u_con),
  'doble factor', 'Seguridad: el contador entra solo con doble factor');
insert into seguridad.sesion_usuario (usuario_id, metodo, ip, vence_en) values (:u_con, 'doble_factor', '190.1.1.1', now() + interval '8 hours');
select prueba.esperar_error(format($$insert into seguridad.sesion_usuario (usuario_id, metodo, ip, vence_en) values (%s, 'doble_factor', '190.1.1.1', now() + interval '24 hours')$$, :u_con),
  '12 horas', 'Seguridad: las sesiones vencen a las 12 horas');
select prueba.esperar_error(format($$insert into seguridad.sesion_usuario (usuario_id, metodo, ip, vence_en) values (%s, 'doble_factor', '190.1.1.1', now() + interval '1 hour')$$, :u_op),
  'bloqueada', 'Seguridad: una cuenta bloqueada no abre sesión');
select count(*) as alertas_antes from seguridad.alerta_seguridad where tipo = 'escalada_privilegios' and severidad = 'alta' \gset
insert into nucleo.usuario_rol (usuario_id, rol_id) select :u_fam, id from nucleo.rol where codigo = 'administrador';
select prueba.ok((select count(*) = :alertas_antes + 1 from seguridad.alerta_seguridad where tipo = 'escalada_privilegios' and severidad = 'alta'), 'Seguridad: dar rol de administrador genera alerta');
select prueba.esperar_error($$update seguridad.alerta_seguridad set severidad = 'baja' where tipo = 'senuelo'$$, 'permission denied', 'Seguridad: la API no puede rebajar una alerta');
update seguridad.alerta_seguridad set estado = 'en_analisis' where tipo = 'senuelo';
select prueba.ok((select atendida_por = 1 from seguridad.alerta_seguridad where tipo = 'senuelo'), 'Seguridad: la atención de la alerta queda a nombre de quien la atiende');
select prueba.esperar_error($$delete from seguridad.intento_acceso$$, 'permission denied', 'Seguridad: los intentos de acceso no se borran');
insert into nucleo.auditoria (esquema_tabla, registro_id, accion, usuario_id) select 'crm.prospecto', g, 'exportar', :u_enc from generate_series(1, 20) g;
select prueba.ok((select count(*) = 1 from seguridad.alerta_seguridad where tipo = 'exportacion_masiva'), 'Seguridad: 20 exportaciones en una hora generan alerta de exportación masiva');
select prueba.ok(seguridad.revisar_copias() = 2, 'Seguridad: sin copia diaria ni prueba de restauración hay dos alertas');
select prueba.esperar_error($$insert into seguridad.copia_seguridad (alcance, destino, inicio, cifrada, exitosa) values ('postgresql', 'nube', now(), false, true)$$, 'check', 'Seguridad: toda copia va cifrada');
insert into seguridad.ejecucion_prueba (tipo, suite, version_sistema, entorno, total, aprobadas, fallidas, herramienta) values ('reglas_bd', 'pruebas_reglas_v5', '5.0', 'pruebas', 1, 1, 0, 'psql');
select prueba.ok((select count(*) = 1 from seguridad.ejecucion_prueba), 'Seguridad: el módulo de pruebas registra cada corrida');
select prueba.ok((select alertas_24h > 0 and bloqueos_activos >= 3 from seguridad.v_tablero), 'Seguridad: tablero de monitoreo');

-- 12. Integraciones externas
select id as t_cli from terceros.tercero where razon_social = 'Concentrados SA' \gset
select prueba.esperar_error(format($$insert into nucleo.llave_api (tercero_id, nombre, prefijo, hash_llave, vence_en, activa) values (%s, 'HORECA', 'gyc_abc12345', repeat('f', 64), current_date + 90, true)$$, :t_cli),
  'api_b2b', 'Integración: la API B2B queda apagada');
update nucleo.funcionalidad set activa = true where codigo = 'api_b2b';
select prueba.esperar_error(format($$insert into nucleo.llave_api (tercero_id, nombre, prefijo, hash_llave, vence_en, activa) values (%s, 'HORECA', 'gyc_abc12345', repeat('f', 64), current_date + 90, true)$$, :t_cli),
  'Solo un cliente', 'Integración: solo un cliente tiene llave');
select prueba.ok(nucleo.autenticar_llave_api('gyc_cebo0001', repeat('0', 64), '45.1.1.1') is null, 'Integración: la llave señuelo no da acceso');
select prueba.ok(seguridad.ip_bloqueada('45.1.1.1'), 'Integración: la llave señuelo bloquea la IP de quien la use');
select prueba.esperar_error($$insert into nucleo.webhook_suscripcion (nombre, url, eventos, secreto_ref, activa) values ('Logística', 'https://x.co/h', '{pedido.confirmado}', 'WH_X', true)$$,
  'webhooks_salientes', 'Integración: los webhooks quedan apagados');
select prueba.esperar_error($$insert into nucleo.webhook_suscripcion (nombre, url, eventos, secreto_ref) values ('Logística', 'http://x.co/h', '{pedido.confirmado}', 'WH_X')$$,
  'check', 'Integración: un webhook solo va por https');

-- 13. CRM: posibles clientes con autorización de datos
select prueba.esperar_error($$insert into crm.prospecto (tipo, nombre, sector, telefono, canal_origen) values ('persona', 'Vecina', 'hogar', '+573000000000', 'feria')$$,
  'autorización', 'CRM: el teléfono de una persona solo se guarda con su autorización');
insert into crm.prospecto (tipo, nombre, sector, canal_origen) values ('persona', 'Vecina sin datos', 'hogar', 'feria');
insert into terceros.tercero (tipo_persona, nombres) values ('natural', 'Vecina con permiso');
insert into terceros.consentimiento_datos (tercero_id, finalidad, version_politica, otorgado, medio, otorgado_en)
select id, 'publicidad', '1.0', true, 'formulario_fisico', now() from terceros.tercero where nombres = 'Vecina con permiso';
insert into crm.prospecto (tipo, nombre, sector, telefono, canal_origen, consentimiento_id, tercero_id)
select 'persona', 'Vecina con permiso', 'hogar', '+573001112233', 'feria', c.id, c.tercero_id from terceros.consentimiento_datos c join terceros.tercero t on t.id = c.tercero_id where t.nombres = 'Vecina con permiso';
insert into crm.campana (nombre, canal, desde, costo_real) values ('Feria de Nilo', 'feria', current_date, 300000);
insert into crm.prospecto (tipo, nombre, nit, sector, telefono, canal_origen, volumen_estimado_mes, campana_id)
select 'empresa', 'Hotel de prueba', '900000000', 'hotel', '+576000000000', 'feria', 2000000, id from crm.campana;
select id as pr_hot from crm.prospecto where nombre = 'Hotel de prueba' \gset
insert into crm.interaccion (prospecto_id, tipo, fecha, resumen) values (:pr_hot, 'whatsapp', now(), 'Pide muestra de huevo AA');
select prueba.ok((select etapa = 'contactado' from crm.prospecto where id = :pr_hot), 'CRM: el primer contacto mueve el prospecto a contactado');
select prueba.ok(crm.calificar(:pr_hot) = 85, 'CRM: puntaje 85 (empresa, sector HORECA, volumen alto, contacto reciente)');
update terceros.consentimiento_datos set revocado_en = now() where tercero_id = (select id from terceros.tercero where nombres = 'Vecina con permiso');
select prueba.esperar_error($$insert into crm.interaccion (prospecto_id, tipo, fecha, resumen) select id, 'whatsapp', now(), 'Oferta' from crm.prospecto where nombre = 'Vecina con permiso'$$,
  'sin su autorización', 'CRM: revocada la autorización, no se le escribe');
select prueba.esperar_error(format($$update crm.prospecto set etapa = 'ganado' where id = %s$$, :pr_hot), 'conviértalo', 'CRM: para ganarlo hay que convertirlo en cliente');
select prueba.ok(crm.convertir_prospecto(:pr_hot, 'hotel') is not null, 'CRM: la conversión devuelve el tercero');
select prueba.ok((select etapa = 'ganado' from crm.prospecto where id = :pr_hot)
                 and exists (select 1 from terceros.cliente c join crm.prospecto p on p.tercero_id = c.tercero_id where p.id = :pr_hot), 'CRM: convertido en tercero y cliente');
select prueba.esperar_error($$update crm.prospecto set etapa = 'perdido' where nombre = 'Vecina sin datos'$$, 'por qué', 'CRM: un prospecto perdido registra el motivo');
select prueba.ok((select costo_por_cliente = 300000 from crm.v_campanas), 'CRM: costo por cliente ganado de la campaña');

-- 14. Robótica y energía
select prueba.esperar_error(format($$insert into iot.mision_robot (activo_id, tipo, zona_id) values (%s, 'dron_monitoreo', %s)$$, :act, :z_pl), 'dron_monitoreo', 'Robótica: el dron queda apagado');
update nucleo.funcionalidad set activa = true where codigo in ('dron_monitoreo', 'robot_campo');
select prueba.esperar_error(format($$insert into iot.mision_robot (activo_id, tipo, zona_id) values (%s, 'dron_monitoreo', %s)$$, :act, :z_pl), 'tipo dron', 'Robótica: la misión de dron usa un dron');
insert into activos.activo (codigo, nombre, tipo) values ('ACT-DRON-01', 'Dron de monitoreo', 'dron'), ('ACT-ROB-01', 'Robot en piloto', 'robot');
insert into iot.mision_robot (activo_id, tipo, zona_id) select id, 'dron_monitoreo', :z_pl from activos.activo where codigo = 'ACT-DRON-01';
select prueba.esperar_error($$update iot.mision_robot set estado = 'en_curso' where tipo = 'dron_monitoreo'$$, 'aprobada', 'Robótica: sin aprobación humana no arranca');
update iot.mision_robot set estado = 'aprobada' where tipo = 'dron_monitoreo';
select prueba.esperar_error($$update iot.mision_robot set estado = 'en_curso' where tipo = 'dron_monitoreo'$$, 'Aerocivil', 'Robótica: el dron debe estar registrado (RAC 100)');
update activos.activo set registro_aerocivil = 'UAEAC-0001' where codigo = 'ACT-DRON-01';
select prueba.esperar_error(format($$update iot.mision_robot set estado = 'en_curso', piloto_id = %s, altura_max_m = 150 where tipo = 'dron_monitoreo'$$, :t_enc), '122', 'Robótica: altura máxima 122 m');
select prueba.esperar_error(format($$update iot.mision_robot set estado = 'en_curso', piloto_id = %s, altura_max_m = 100 where tipo = 'dron_monitoreo'$$, :t_enc), 'póliza', 'Robótica: el vuelo necesita póliza de responsabilidad civil');
insert into seguros.poliza (numero, aseguradora_id, tipo, desde, hasta, prima, suma_asegurada, estado) values ('POL-RC', :t_aseg, 'responsabilidad_civil', current_date, current_date + 365, 500000, 100000000, 'vigente');
update iot.mision_robot set estado = 'en_curso', piloto_id = :t_enc, altura_max_m = 100, poliza_id = (select id from seguros.poliza where numero = 'POL-RC') where tipo = 'dron_monitoreo';
select prueba.ok((select inicio is not null and aprobada_por = 1 from iot.mision_robot where tipo = 'dron_monitoreo'), 'Robótica: vuelo aprobado, registrado, con piloto y póliza');
insert into iot.mision_robot (activo_id, tipo, zona_id, estado) select id, 'robot_deshierbe', :z_pl, 'propuesta' from activos.activo where codigo = 'ACT-ROB-01';
update iot.mision_robot set estado = 'aprobada' where tipo = 'robot_deshierbe';
select prueba.esperar_error($$update iot.mision_robot set estado = 'en_curso' where tipo = 'robot_deshierbe'$$, 'sin personas', 'Robótica: el robot solo opera sin personas y con parada de emergencia probada');
insert into produccion.siembra (zona_id, cultivo_id, fecha_siembra) select :z_pl, id, current_date from produccion.cultivo where codigo = 'platano';
select prueba.esperar_error($$insert into produccion.labor_cultural (siembra_id, fecha, tipo, metodo) select id, current_date, 'deshierbe', 'robot' from produccion.siembra$$,
  'check', 'Robótica: una labor hecha por robot viene de una misión');
insert into iot.dispositivo (codigo, tipo, topico_mqtt) values ('ESP-GAL-01', 'esp32', 'finca/gal01');
insert into iot.actuador (dispositivo_id, codigo, tipo) select id, x.c, 'rele' from iot.dispositivo, (values ('R-NEVERA'), ('R-LUCES'), ('R-BOMBA-RIEGO')) x(c);
insert into iot.prioridad_carga (actuador_id, prioridad, esencial, corte_bateria_pct) select id, x.p, x.e, x.c from iot.actuador a join (values ('R-NEVERA', 1, true, null), ('R-LUCES', 5, false, 40), ('R-BOMBA-RIEGO', 3, false, 25)) x(cod, p, e, c) on x.cod = a.codigo;
select prueba.esperar_error($$update iot.prioridad_carga set corte_bateria_pct = 10 where esencial$$, 'check', 'Energía: una carga esencial nunca se corta');
select prueba.ok((select array_agg(a.codigo order by c.prioridad desc) = '{R-LUCES}' from iot.cargas_a_cortar(30) c join iot.actuador a on a.id = c.actuador_id), 'Energía: con 30 % de batería solo se cortan las luces');
select prueba.ok((select count(*) = 2 from iot.cargas_a_cortar(20)), 'Energía: con 20 % se cortan luces y riego; la nevera sigue');


-- 16. Áreas de responsabilidad y cronograma flexible 24/7
select prueba.esperar_error(format($$insert into personal.tarea (plantilla_tarea_id, titulo, fecha, empleado_id) select id, 'Huevos', current_date, %s from personal.plantilla_tarea where codigo = 'REV-BEBEDEROS'$$, :e_jor),
  'no pertenece al área', 'Áreas: no se asigna una tarea del galpón a quien no es del área');
insert into personal.tarea (titulo, fecha, empleado_id, area_id) select 'Deshierbe lote de plátano', current_date, :e_jor, id from personal.area_responsabilidad where codigo = 'AR-CULTIVOS';
update personal.tarea set estado = 'terminada' where titulo = 'Deshierbe lote de plátano';
select set_config('app.usuario_id', :'u_op', false);
update personal.tarea set estado = 'aprobada' where titulo = 'Deshierbe lote de plátano';
select set_config('app.usuario_id', '1', false);
select prueba.ok((select aprobado_por = :u_op from personal.tarea where titulo = 'Deshierbe lote de plátano'), 'Áreas: el responsable del área aprueba las tareas de su área aunque no tenga el permiso general');
insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin, tipo) values (:e_enc, current_date, '22:00', '06:00', 'nocturno');
select prueba.ok((select horas = 8 from personal.turno where empleado_id = :e_enc and fecha = current_date), 'Turnos: el turno de noche cruza la medianoche y suma 8 horas');
select prueba.esperar_error(format($$insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin) values (%s, current_date, '23:00', '02:00')$$, :e_enc), 'se cruza', 'Turnos: dos turnos de la misma persona no se cruzan');
select prueba.esperar_error(format($$insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin) values (%s, current_date + 1, '08:00', '12:00')$$, :e_enc), 'descanso', 'Turnos: entre turnos hay al menos 10 horas de descanso');
select prueba.esperar_error(format($$insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin) values (%s, current_date + 10, '05:00', '18:00')$$, :e_enc), 'jornada máxima', 'Turnos: un turno no supera la jornada máxima diaria');
select prueba.esperar_error(format($$insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin) values (%s, current_date + 2, '06:00', '12:00')$$, :e_op), 'ausencia', 'Turnos: no se programa a quien está de vacaciones');
insert into personal.cronograma (nombre, area_id, desde, hasta) select 'Vigilancia 2 al 15 de noviembre', id, '2026-11-02', '2026-11-15' from personal.area_responsabilidad where codigo = 'AR-VIGILANCIA';
select id as cro from personal.cronograma where nombre like 'Vigilancia%' \gset
insert into personal.asignacion_patron (cronograma_id, empleado_id, patron_id, desfase_dias)
select :cro, e.id, p.id, (row_number() over (order by e.id) - 1) * 2 from terceros.empleado e, personal.patron_turno p where e.cargo = 'Vigilante' and p.codigo = 'CIC-MMTTNNL';
select prueba.ok(personal.generar_turnos(:cro) = 56, 'Cronograma: 4 vigilantes × 14 días generados desde la rotación 24/7');
select prueba.ok((select count(*) = 6 from personal.huecos_cobertura(:cro)), 'Cronograma: detecta el hueco de 0:00 a 6:00 del primer día (nadie entró de noche el día anterior)');
select prueba.esperar_error(format($$update personal.cronograma set estado = 'publicado' where id = %s$$, :cro), 'Falta cobertura', 'Cronograma: no se publica con huecos de cobertura');
insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin, tipo, area_id)
select ap.empleado_id, '2026-11-01', '22:00', '06:00', 'nocturno', c.area_id from personal.asignacion_patron ap join personal.cronograma c on c.id = ap.cronograma_id where ap.cronograma_id = :cro and ap.desfase_dias = 6;
select prueba.ok((select count(*) = 0 from personal.huecos_cobertura(:cro)), 'Cronograma: con el turno de la noche anterior queda cubierto 24/7');
update personal.cronograma set estado = 'publicado' where id = :cro;
select prueba.ok((select publicado_por = 1 from personal.cronograma where id = :cro), 'Cronograma: publicado por una persona');
select prueba.ok((select max(horas) = 48 and min(dias_trabajados) >= 6 from personal.v_carga_semanal v join terceros.empleado e on e.id = v.empleado_id where e.cargo = 'Vigilante' and v.semana = '2026-11-02'),
  'Cronograma: 48 horas por semana (42 + 6 extra), dentro del límite');
select prueba.esperar_error(format($$insert into personal.tarea (titulo, fecha, empleado_id) select 'Ronda', '2026-11-02', ap.empleado_id from personal.asignacion_patron ap where ap.cronograma_id = %s and ap.desfase_dias = 6$$, :cro),
  'no está disponible', 'Cronograma: no se asignan tareas en el día de descanso');
insert into personal.patron_turno (codigo, nombre, tipo, ciclo_dias) values ('TODOS', 'Todos los días', 'semanal', 7);
insert into personal.patron_turno_detalle (patron_id, dia_ciclo, hora_inicio, hora_fin, tipo) select id, d, '06:00', '12:00', 'diurno' from personal.patron_turno, generate_series(1, 7) d where codigo = 'TODOS';
insert into personal.cronograma (nombre, area_id, desde, hasta, permitir_huecos) select 'Galpón diciembre', id, '2026-12-07', '2026-12-13', true from personal.area_responsabilidad where codigo = 'AR-GALPON';
insert into personal.asignacion_patron (cronograma_id, empleado_id, patron_id) select c.id, :e_op, p.id from personal.cronograma c, personal.patron_turno p where c.nombre = 'Galpón diciembre' and p.codigo = 'TODOS';
select personal.generar_turnos(id) from personal.cronograma where nombre = 'Galpón diciembre';
select prueba.esperar_error($$update personal.cronograma set estado = 'publicado' where nombre = 'Galpón diciembre'$$, 'día de descanso', 'Cronograma: nadie trabaja 7 días seguidos sin descanso');

-- 17. Agenda de cabañas sin cruces
insert into turismo.alojamiento (codigo, nombre, capacidad_personas, tarifa_noche) values ('CAB-01', 'Cabaña del guayacán', 4, 250000);
insert into agenda.recurso (codigo, nombre, tipo, alojamiento_id, capacidad, minutos_preparacion) select 'REC-CAB-01', 'Cabaña del guayacán', 'cabana', id, 4, 120 from turismo.alojamiento where codigo = 'CAB-01';
select c.id as cli from terceros.cliente c join crm.prospecto p on p.tercero_id = c.tercero_id where p.id = :pr_hot \gset
insert into turismo.reserva (codigo, cliente_id, alojamiento_id, fecha_inicio, fecha_fin, personas, total, estado)
select 'R-1', :cli, id, '2026-12-10', '2026-12-12', 3, 500000, 'confirmada' from turismo.alojamiento where codigo = 'CAB-01';
select prueba.ok((select inicio = '2026-12-10 15:00-05' and fin_con_preparacion = '2026-12-12 14:00-05' from agenda.cita where reserva_id = (select id from turismo.reserva where codigo = 'R-1')),
  'Agenda: la reserva confirmada ocupa la cabaña de 15:00 a 12:00 más 2 horas de limpieza');
insert into turismo.reserva (codigo, cliente_id, alojamiento_id, fecha_inicio, fecha_fin, personas, total, estado)
select 'R-2', :cli, id, '2026-12-12', '2026-12-13', 2, 250000, 'confirmada' from turismo.alojamiento where codigo = 'CAB-01';
select prueba.ok((select count(*) = 2 from agenda.cita where estado = 'confirmada'), 'Agenda: otra reserva puede llegar el mismo día de la salida, después de la limpieza');
select prueba.esperar_error(format($$insert into turismo.reserva (codigo, cliente_id, alojamiento_id, fecha_inicio, fecha_fin, personas, total, estado) select 'R-3', %s, id, '2026-12-11', '2026-12-12', 2, 1, 'confirmada' from turismo.alojamiento where codigo = 'CAB-01'$$, :cli),
  'ya está ocupada', 'Agenda: no hay dos reservas cruzadas en la misma cabaña');
select prueba.esperar_error(format($$insert into turismo.reserva (codigo, cliente_id, alojamiento_id, fecha_inicio, fecha_fin, personas, total) select 'R-4', %s, id, '2026-12-20', '2026-12-21', 6, 1 from turismo.alojamiento where codigo = 'CAB-01'$$, :cli),
  'admite 4', 'Agenda: no se supera la capacidad de la cabaña');
insert into turismo.bloqueo_calendario (alojamiento_id, desde, hasta, motivo) select id, '2026-12-20', '2026-12-21', 'Pintura de la cabaña' from turismo.alojamiento where codigo = 'CAB-01';
select prueba.esperar_error(format($$insert into turismo.reserva (codigo, cliente_id, alojamiento_id, fecha_inicio, fecha_fin, personas, total, estado) select 'R-5', %s, id, '2026-12-21', '2026-12-22', 2, 1, 'confirmada' from turismo.alojamiento where codigo = 'CAB-01'$$, :cli),
  'ya está ocupada', 'Agenda: el bloqueo por mantenimiento también ocupa el calendario');
update turismo.reserva set estado = 'cancelada' where codigo = 'R-2';
insert into turismo.reserva (codigo, cliente_id, alojamiento_id, fecha_inicio, fecha_fin, personas, total, estado)
select 'R-3', :cli, id, '2026-12-12', '2026-12-13', 2, 250000, 'confirmada' from turismo.alojamiento where codigo = 'CAB-01';
select prueba.ok((select count(*) = 1 from agenda.cita where estado = 'cancelada'), 'Agenda: al cancelar, la fecha queda libre para otra reserva');
select prueba.ok(not agenda.recurso_libre((select id from agenda.recurso where codigo = 'REC-CAB-01'), '2026-12-11 10:00-05', '2026-12-11 11:00-05')
                 and agenda.recurso_libre((select id from agenda.recurso where codigo = 'REC-CAB-01'), '2026-12-15 10:00-05', '2026-12-16 11:00-05'), 'Agenda: consulta de disponibilidad');
update turismo.reserva set checkout_en = '2026-12-12 11:30-05' where codigo = 'R-1';
select prueba.ok((select count(*) = 1 from personal.tarea t join personal.area_responsabilidad a on a.id = t.area_id where t.origen = 'agenda' and a.codigo = 'AR-TURISMO'),
  'Agenda: la salida del huésped crea la tarea de limpieza del área de turismo');

-- 18. Visitas, ingresos y salidas de personas y vehículos
insert into agenda.visita (tipo, nombre, vehiculo_placa, vehiculo_tipo, motivo, zona_destino_id, ingreso_programado, salida_programada, anfitrion_id, requiere_bioseguridad)
values ('proveedor', 'Concentrados SA', 'ABC123', 'camion', 'Entrega de concentrado', :z_gal, now() - interval '10 minutes', now() + interval '2 hours', :u_enc, true);
select id as vis from agenda.visita where nombre = 'Concentrados SA' \gset
select prueba.esperar_error(format($$update agenda.visita set estado = 'aprobada' where id = %s$$, :vis), 'contacto con otras aves', 'Visitas: al galpón solo entra quien declara no haber tenido contacto con otras aves');
update agenda.visita set contacto_aves_reciente = false, estado = 'aprobada' where id = :vis;
select prueba.ok(length(agenda.emitir_pase(:vis)) = 12, 'Visitas: se emite el código del pase');
select prueba.ok((select length(pase_hash) = 64 from agenda.visita where id = :vis), 'Visitas: la base guarda solo la huella del pase');
select prueba.esperar_error(format($$insert into agenda.registro_acceso (sentido, tipo, visita_id, placa, metodo, desinfeccion) values ('entrada', 'vehiculo', %s, 'XYZ999', 'pase_qr', true)$$, :vis), 'no corresponde', 'Portería: la placa debe ser la de la visita');
select prueba.esperar_error(format($$insert into agenda.registro_acceso (sentido, tipo, visita_id, placa, metodo) values ('entrada', 'vehiculo', %s, 'ABC123', 'pase_qr')$$, :vis), 'desinfección', 'Portería: sin desinfección no entra al galpón');
insert into agenda.registro_acceso (sentido, tipo, visita_id, placa, metodo, desinfeccion) values ('entrada', 'vehiculo', :vis, 'abc123', 'pase_qr', true);
select prueba.ok((select estado = 'en_sitio' from agenda.visita where id = :vis) and exists (select 1 from agenda.v_en_sitio where visita_id = :vis), 'Portería: el camión queda en sitio');
insert into agenda.registro_acceso (sentido, tipo, visita_id, metodo) values ('salida', 'vehiculo', :vis, 'pase_qr');
select prueba.ok((select estado = 'salio' from agenda.visita where id = :vis) and not exists (select 1 from agenda.v_en_sitio where visita_id = :vis), 'Portería: al salir deja de estar en sitio');
insert into agenda.visita (tipo, nombre, motivo, ingreso_programado, salida_programada, anfitrion_id, estado)
values ('tecnico', 'Técnico de paneles', 'Revisión', now() + interval '1 day', now() + interval '1 day 2 hours', :u_enc, 'aprobada');
select prueba.esperar_error($$insert into agenda.registro_acceso (sentido, tipo, visita_id, metodo) select 'entrada', 'persona', id, 'pase_qr' from agenda.visita where nombre = 'Técnico de paneles'$$,
  'fuera del horario', 'Portería: una visita no entra fuera de su horario');
insert into agenda.registro_acceso (sentido, tipo, empleado_id, metodo, ocurrido_en) values ('entrada', 'persona', :e_enc, 'carne_nfc', now() - interval '8 hours');
select prueba.ok((select count(*) = 1 from personal.jornada where empleado_id = :e_enc and salida is null), 'Portería: el carné del trabajador abre su jornada');
insert into agenda.registro_acceso (sentido, tipo, empleado_id, metodo) values ('salida', 'persona', :e_enc, 'carne_nfc');
select prueba.ok((select horas between 7.99 and 8.01 from personal.jornada where empleado_id = :e_enc), 'Portería: la salida cierra la jornada con sus horas');
select prueba.esperar_error($$insert into agenda.registro_acceso (sentido, tipo, nombre, metodo) values ('salida', 'persona', 'Desconocido', 'manual')$$, 'No hay una entrada', 'Portería: no se registra la salida de quien no entró');
select prueba.esperar_error($$update agenda.registro_acceso set placa = 'OTRA'$$, 'solo inserción', 'Portería: los registros de acceso no se alteran');

-- 19. Formación con enfoque ISO 21001
insert into formacion.queja_apelacion (tipo, tercero_id, curso_id, descripcion) select 'apelacion', :t_jor, id, 'No estoy de acuerdo con la nota práctica' from formacion.curso where codigo = 'VAC-AVI';
select prueba.ok((select responder_antes = current_date + 15 from formacion.queja_apelacion), 'Formación: la apelación tiene plazo de respuesta de 15 días');
select set_config('app.usuario_id', :'u_enc', false);
select prueba.esperar_error($$update formacion.queja_apelacion set estado = 'resuelta', respuesta = 'Se mantiene'$$, 'distinto del instructor', 'Formación: el instructor no resuelve la apelación de su propio curso');
select set_config('app.usuario_id', '1', false);
update formacion.queja_apelacion set estado = 'resuelta', respuesta = 'Se repite la práctica con otro evaluador';
insert into formacion.encuesta (curso_id, satisfaccion, utilidad, instructor) select id, 5, 4, 5 from formacion.curso where codigo = 'BIO-AVI';
select prueba.ok((select satisfaccion = 5 and aprobados = 1 from formacion.v_satisfaccion where codigo = 'BIO-AVI'), 'Formación: seguimiento de satisfacción y aprobación por curso');
select prueba.esperar_error($$insert into cumplimiento.expediente (norma_id) select id from cumplimiento.norma where codigo = 'ISO_21001'$$, 'iso_21001', 'Formación: el expediente ISO 21001 queda cargado y apagado');

-- 20. Proyectos (PMBOK 8)
insert into proyectos.proyecto (codigo, nombre, objetivo, iniciativa_id, enfoque, patrocinador_id, director_id, presupuesto, inicio_plan, fin_plan)
values ('PRY-GAL-500', 'Galpón para 500 gallinas', 'Producir huevo para el canal HORECA con granja biosegura certificada', :ini, 'hibrido', :u_fam, :u_enc, 30000000, '2026-11-02', '2027-01-31');
select id as pry from proyectos.proyecto \gset
insert into proyectos.interesado (proyecto_id, nombre, interes, influencia) values (:pry, 'ICA', 4, 5), (:pry, 'Vecino de la vereda', 2, 2);
select prueba.ok((select string_agg(estrategia, ',' order by nombre) = 'gestionar_de_cerca,monitorear' from proyectos.interesado), 'Proyectos: estrategia de cada interesado según interés e influencia');
select prueba.esperar_error(format($$update proyectos.proyecto set estado = 'aprobado' where id = %s$$, :pry), 'patrocinador', 'Proyectos: el proyecto lo aprueba su patrocinador');
select set_config('app.usuario_id', :'u_fam', false);
update proyectos.proyecto set estado = 'aprobado' where id = :pry;
select set_config('app.usuario_id', '1', false);
select prueba.ok((select count(*) = 1 and min(presupuesto) = 30000000 from proyectos.linea_base where proyecto_id = :pry), 'Proyectos: al aprobar nace la línea base 1');
insert into proyectos.elemento_edt (proyecto_id, codigo, nombre, es_entregable, criterio_aceptacion) values (:pry, '1', 'Galpón construido', true, 'Inspección del ICA sin hallazgos críticos');
insert into proyectos.actividad (proyecto_id, codigo, nombre, duracion_dias, costo_plan, es_hito) values
 (:pry, 'A', 'Diseño y permisos', 5, 5000000, false), (:pry, 'B', 'Compra de materiales', 3, 3000000, false), (:pry, 'C', 'Construcción', 7, 7000000, false),
 (:pry, 'D', 'Instalación de bebederos y luz', 2, 2000000, false), (:pry, 'E', 'Galpón listo', 0, 0, true);
insert into proyectos.dependencia (predecesora_id, sucesora_id)
select p.id, s.id from proyectos.actividad p, proyectos.actividad s, (values ('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'D'), ('D', 'E')) x(a, b) where p.codigo = x.a and s.codigo = x.b;
select prueba.esperar_error($$insert into proyectos.dependencia (predecesora_id, sucesora_id) select (select id from proyectos.actividad where codigo = 'D'), (select id from proyectos.actividad where codigo = 'A')$$,
  'ciclo', 'Proyectos: el cronograma no admite ciclos');
select prueba.ok(proyectos.calcular_ruta_critica(:pry) = 14, 'Proyectos: duración de 14 días por la ruta crítica');
select prueba.ok((select string_agg(codigo, '' order by codigo) = 'ACDE' from proyectos.actividad where critica) and (select holgura = 4 from proyectos.actividad where codigo = 'B'),
  'Proyectos: ruta crítica A-C-D-E y holgura de 4 días en compras');
update proyectos.actividad set avance_pct = 100, costo_real = 6000000 where codigo = 'A';
update proyectos.actividad set avance_pct = 50, costo_real = 3000000 where codigo = 'C';
select prueba.ok(proyectos.calcular_valor_ganado(:pry, '2026-11-10') = 0.9444, 'Proyectos: CPI = EV 8,5 M / AC 9 M = 0,94 (gasta más de lo planeado)');
select prueba.ok((select spi = 0.7727 and pv = 11000000 from proyectos.medicion_valor_ganado), 'Proyectos: SPI = EV 8,5 M / PV 11 M = 0,77 (va atrasado)');
insert into proyectos.solicitud_cambio (proyecto_id, descripcion, solicitada_por, impacto_dias, impacto_costo) values (:pry, 'Agregar bodega de concentrado', :u_enc, 10, 2000000);
select set_config('app.usuario_id', :'u_enc', false);
select prueba.esperar_error($$update proyectos.solicitud_cambio set estado = 'aprobada'$$, 'no lo aprueba', 'Proyectos: quien pide el cambio no lo aprueba');
select set_config('app.usuario_id', :'u_fam', false);
update proyectos.solicitud_cambio set estado = 'aprobada';
select set_config('app.usuario_id', '1', false);
select prueba.ok((select presupuesto = 32000000 and fin_plan = '2027-02-10' from proyectos.proyecto where id = :pry) and (select count(*) = 2 from proyectos.linea_base),
  'Proyectos: el cambio aprobado crea la línea base 2 con 32 M y 10 días más');
select prueba.esperar_error($$update proyectos.linea_base set presupuesto = 1$$, 'solo inserción', 'Proyectos: una línea base no se edita');
update proyectos.proyecto set estado = 'en_curso' where id = :pry;
select prueba.esperar_error(format($$update proyectos.proyecto set estado = 'cerrado' where id = %s$$, :pry), 'entregables sin aceptar', 'Proyectos: no se cierra con entregables sin aceptar');
select prueba.esperar_error($$update proyectos.elemento_edt set estado = 'aceptado'$$, 'terminado', 'Proyectos: solo se acepta un entregable terminado');
update proyectos.elemento_edt set estado = 'terminado';
update proyectos.elemento_edt set estado = 'aceptado';
select prueba.esperar_error(format($$update proyectos.proyecto set estado = 'cerrado' where id = %s$$, :pry), 'lecciones aprendidas', 'Proyectos: no se cierra sin lecciones aprendidas');
insert into proyectos.registro (proyecto_id, tipo, descripcion) values (:pry, 'leccion_aprendida', 'Pedir los materiales antes de terminar el diseño');
update proyectos.proyecto set estado = 'cerrado' where id = :pry;
select prueba.ok((select area_enfoque = 'cierre' and fin_real is not null from proyectos.proyecto where id = :pry), 'Proyectos: cerrado con entregables aceptados y lecciones');
select prueba.ok((select cpi = 0.9444 and avance_ponderado_pct is not null from proyectos.v_tablero where id = :pry), 'Proyectos: tablero con avance y CPI');

-- 21. Análisis financiero vertical, horizontal y fuentes y usos
select prueba.ok((select valor_b = 10000000 and vertical_b_pct = 35.09 from finanzas.analisis_vertical_horizontal('2026-09-01', '2026-09-30', date_trunc('month', current_date)::date, current_date) where cuenta = '1105'),
  'Finanzas: análisis vertical: la caja pesa 35,09 % del activo');
select prueba.ok((select clasificacion = 'uso' from finanzas.fuentes_usos('2026-09-30', current_date) where cuenta = '1105')
                 and (select clasificacion = 'fuente' from finanzas.fuentes_usos('2026-09-30', current_date) where cuenta = '3105'), 'Finanzas: fuentes y usos: más caja es uso, más capital es fuente');

-- 22. Aislamiento entre fincas de los módulos nuevos
select set_config('app.predio_id', '2', false);
select prueba.ok((select count(*) from personal.tarea) = 0 and (select count(*) from nomina.liquidacion) = 0 and (select count(*) from crm.prospecto) = 0
                 and (select count(*) from estrategia.iniciativa) = 0 and (select count(*) from agenda.visita) = 0 and (select count(*) from proyectos.proyecto) = 0
                 and (select count(*) from personal.turno) = 0, 'RLS: otra finca no ve tareas, nómina, prospectos, iniciativas, visitas, proyectos ni turnos');
select set_config('app.predio_id', '1', false);

reset role;
select 'TODAS LAS PRUEBAS PASARON' as resultado;
