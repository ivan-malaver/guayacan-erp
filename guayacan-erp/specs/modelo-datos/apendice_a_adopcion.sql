-- GuayacanERP · Apéndice A · Esquema adopcion (árboles y animales adoptados por turistas)
-- Se carga DESPUÉS de esquema_postgresql.sql y datos_iniciales.sql de la v5. PostgreSQL 18 (probado también en 16).
-- Modelo: VENTA de un bien identificado (árbol o animal) + CONTRATO de cuidado mensual. La finca no promete rendimientos
-- ni recompra; si el bien produce o se liquida, se le entrega al dueño lo neto menos la comisión de administración (5 %).
-- Convenciones v5: predio_id con RLS, llaves compuestas (predio_id, id), auditoría, reglas en la base, "la IA propone y una persona decide".
\set ON_ERROR_STOP 1

create schema if not exists adopcion;
comment on schema adopcion is 'Adopción de árboles y animales: catálogo, sitios de siembra, bienes, contratos de compra y cuidado, cuotas, seguimiento, productos, liquidaciones y saldo del adoptante';

-- ============================================================================ 1. Cambios mínimos a la v5
alter table terceros.consentimiento_datos drop constraint ck_consentimiento_datos_finalidad;
alter table terceros.consentimiento_datos add constraint ck_consentimiento_datos_finalidad check (finalidad in
  ('atencion_pedidos', 'publicidad', 'personalizacion_ofertas', 'analitica', 'imagen_redes', 'biometria_acceso', 'seguimiento_adopcion'));
alter table terceros.tercero add column if not exists es_adoptante boolean not null default false;
comment on column terceros.tercero.es_adoptante is 'Compró o readoptó un árbol o animal (apéndice A)';
-- ADO-02: pagos de prueba con la pasarela simulada (guayacan/pasarela.py) mientras se conecta Wompi
alter table comercial.pago drop constraint ck_pago_proveedor_pasarela;
alter table comercial.pago add constraint ck_pago_proveedor_pasarela check (proveedor_pasarela in
  ('wompi', 'mercado_pago', 'epayco', 'payu', 'simulada'));

insert into produccion.cultivo (codigo, nombre_comun, nombre_cientifico, tipo_ciclo, dias_a_primera_cosecha) values
 ('mango', 'Mango', 'Mangifera indica', 'perenne', 1460),
 ('citrico', 'Cítricos (naranja, mandarina, limón)', 'Citrus spp.', 'perenne', 1095),
 ('guayacan', 'Guayacán rosado', 'Tabebuia rosea', 'perenne', null),
 ('cedro', 'Cedro', 'Cedrela odorata', 'perenne', null),
 ('nogal', 'Nogal cafetero', 'Cordia alliodora', 'perenne', null)
on conflict (codigo) do nothing;

-- ============================================================================ 2. Tablas
create table adopcion.plan (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    tipo text not null constraint ck_plan_tipo check (tipo in ('frutal', 'maderable', 'ovino', 'caprino', 'ave')),
    cultivo_id bigint references produccion.cultivo(id),
    especie_id bigint references produccion.especie(id),
    precio_compra numeric(14,2) not null check (precio_compra > 0),
    precio_readopcion numeric(14,2) not null check (precio_readopcion >= 0),
    cuota_mensual numeric(14,2) not null check (cuota_mensual > 0),
    costo_bien numeric(14,2) not null check (costo_bien >= 0),
    costo_cuidado_mensual numeric(14,2) not null check (costo_cuidado_mensual >= 0),
    meses_madurez smallint not null check (meses_madurez > 0),
    garantia_meses smallint not null default 12,
    requiere_permiso text not null default 'ninguno' constraint ck_plan_requiere_permiso check (requiere_permiso in ('ninguno', 'tala_car', 'remision_ica', 'planta_beneficio')),
    descripcion text,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id), unique (predio_id, codigo),
    check ((tipo in ('frutal', 'maderable')) = (cultivo_id is not null)),
    check ((tipo in ('ovino', 'caprino', 'ave')) = (especie_id is not null))
);
comment on table adopcion.plan is 'Catálogo de lo que se puede adoptar, con precio, cuota mensual, costos estimados (para el margen) y edad de madurez';

create table adopcion.sitio (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_id bigint not null,
    codigo varchar(20) not null,
    tipo text not null constraint ck_sitio_tipo check (tipo in ('hoyo_siembra', 'corral', 'galpon')),
    latitud numeric(9,6), longitud numeric(9,6),
    estado text not null default 'libre' constraint ck_sitio_estado check (estado in ('libre', 'reservado', 'ocupado', 'inhabilitado')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id), unique (predio_id, codigo),
    foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id)
);
comment on table adopcion.sitio is 'Lugar asignado por la administración: hoyo de siembra en un lote o cupo en corral o galpón';

create table adopcion.bien (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    plan_id bigint not null,
    sitio_id bigint,
    animal_id bigint,
    fecha_inicio date,
    estado text not null default 'disponible' constraint ck_bien_estado check (estado in
      ('disponible', 'reservado', 'activo', 'en_readopcion', 'maduro', 'liquidado', 'muerto')),
    nombre_dado varchar(60),
    reemplaza_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id), unique (predio_id, codigo),
    foreign key (predio_id, plan_id) references adopcion.plan(predio_id, id),
    foreign key (predio_id, sitio_id) references adopcion.sitio(predio_id, id),
    foreign key (predio_id, animal_id) references produccion.animal(predio_id, id),
    foreign key (predio_id, reemplaza_id) references adopcion.bien(predio_id, id)
);
comment on table adopcion.bien is 'El árbol o el animal concreto, con su código QR, sitio y estado de vida';
create unique index ux_bien_sitio_vivo on adopcion.bien (predio_id, sitio_id) where estado not in ('liquidado', 'muerto') and sitio_id is not null;

create table adopcion.contrato (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    numero varchar(20) not null,
    bien_id bigint not null,
    adoptante_id bigint not null,
    tipo text not null constraint ck_contrato_tipo check (tipo in ('compra', 'readopcion', 'cesion')),
    fecha date not null default current_date,
    precio numeric(14,2) not null check (precio >= 0),
    cuota_mensual numeric(14,2) not null check (cuota_mensual > 0),
    modalidad_siembra text not null default 'no_aplica' constraint ck_contrato_modalidad check (modalidad_siembra in ('propia', 'trabajador', 'no_aplica')),
    consentimiento_id bigint,
    estado text not null default 'activo' constraint ck_contrato_estado check (estado in ('pendiente_pago', 'activo', 'cancelado', 'terminado_abandono', 'terminado_liquidacion', 'cedido', 'terminado_muerte')),
    decision_madurez text constraint ck_contrato_decision check (decision_madurez in ('mantener', 'liquidar')),
    decidido_en timestamptz,
    terminado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id), unique (predio_id, numero),
    foreign key (predio_id, bien_id) references adopcion.bien(predio_id, id),
    foreign key (predio_id, adoptante_id) references terceros.tercero(predio_id, id),
    foreign key (predio_id, consentimiento_id) references terceros.consentimiento_datos(predio_id, id)
);
comment on table adopcion.contrato is 'Compraventa del bien + servicio de cuidado mensual. Un bien vivo tiene a lo sumo un contrato activo';
create unique index ux_contrato_activo on adopcion.contrato (predio_id, bien_id) where estado = 'activo';

create table adopcion.cuota (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    contrato_id bigint not null,
    periodo date not null,
    valor numeric(14,2) not null check (valor > 0),
    vence_en date not null,
    estado text not null default 'pendiente' constraint ck_cuota_estado check (estado in ('pendiente', 'pagada', 'compensada', 'anulada')),
    pago_id bigint,
    pagada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id), unique (predio_id, contrato_id, periodo),
    check (periodo = date_trunc('month', periodo)::date),
    foreign key (predio_id, contrato_id) references adopcion.contrato(predio_id, id),
    foreign key (predio_id, pago_id) references comercial.pago(predio_id, id)
);
comment on table adopcion.cuota is 'Cuota mensual de cuidado; se paga con la pasarela o se compensa con el saldo a favor del adoptante';

create table adopcion.seguimiento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    bien_id bigint not null,
    tipo text not null constraint ck_seguimiento_tipo check (tipo in ('siembra', 'video_siembra', 'foto', 'visita', 'sanidad', 'medicion', 'muerte', 'reposicion', 'aviso_mora')),
    fecha timestamptz not null default now(),
    descripcion text,
    evidencia_url varchar(300),
    tarea_id bigint,
    enviado_al_adoptante boolean not null default false,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    foreign key (predio_id, bien_id) references adopcion.bien(predio_id, id),
    foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id),
    foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id)
);
comment on table adopcion.seguimiento is 'Bitácora que ve el adoptante: siembra, video, fotos, sanidad, mediciones. Se captura sin conexión';

create table adopcion.liquidacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    contrato_id bigint not null,
    tipo text not null constraint ck_liquidacion_tipo check (tipo in ('productos', 'tala', 'sacrificio', 'venta_en_pie')),
    periodo_desde date, periodo_hasta date,
    ingresos numeric(14,2) not null default 0 check (ingresos >= 0),
    gastos numeric(14,2) not null default 0 check (gastos >= 0),
    utilidad_neta numeric(14,2),
    comision_pct numeric(5,2),
    comision numeric(14,2),
    abono_adoptante numeric(14,2),
    soporte_documento_id bigint,
    estado text not null default 'borrador' constraint ck_liquidacion_estado check (estado in ('borrador', 'aprobada', 'anulada')),
    aprobada_por bigint, aprobada_en timestamptz,
    detalle jsonb not null default '[]',
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    foreign key (predio_id, contrato_id) references adopcion.contrato(predio_id, id),
    foreign key (predio_id, soporte_documento_id) references documental.documento(predio_id, id)
);
comment on table adopcion.liquidacion is 'Lo que produjo o rindió el bien: ingresos menos gastos directos = utilidad neta; la finca cobra el % de administración solo si hay utilidad';

create table adopcion.movimiento_saldo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    adoptante_id bigint not null,
    tipo text not null constraint ck_mov_tipo check (tipo in ('abono_liquidacion', 'compensacion_cuota', 'pago_al_adoptante')),
    valor numeric(14,2) not null check (valor > 0),
    liquidacion_id bigint,
    cuota_id bigint,
    referencia varchar(80),
    fecha timestamptz not null default now(),
    creado_en timestamptz not null default now(),
    unique (predio_id, id),
    foreign key (predio_id, adoptante_id) references terceros.tercero(predio_id, id),
    foreign key (predio_id, liquidacion_id) references adopcion.liquidacion(predio_id, id),
    foreign key (predio_id, cuota_id) references adopcion.cuota(predio_id, id)
);
comment on table adopcion.movimiento_saldo is 'Cuenta del adoptante (solo inserción): abonos de liquidaciones, cuotas compensadas y pagos. No genera intereses ni se invierte';

create table adopcion.enlace_adoptante (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    contrato_id bigint not null,
    token_hash char(64) not null,
    vence_en timestamptz not null,
    revocado_en timestamptz,
    ultimo_uso_en timestamptz,
    emitido_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id), unique (predio_id, token_hash),
    foreign key (predio_id, contrato_id) references adopcion.contrato(predio_id, id),
    foreign key (emitido_por) references nucleo.usuario(id)
);
comment on table adopcion.enlace_adoptante is 'Enlace personal con que el adoptante sin cuenta sigue su bien (ADO-06): la base guarda solo la huella SHA-256 del código; sirve mientras no venza, no se revoque y el contrato siga activo';

-- RLS, actualizado_en y auditoría con las convenciones de la v5
do $$ declare t text; begin
  foreach t in array array['plan', 'sitio', 'bien', 'contrato', 'cuota', 'seguimiento', 'liquidacion', 'movimiento_saldo', 'enlace_adoptante'] loop
    execute format('alter table adopcion.%I enable row level security; alter table adopcion.%I force row level security;', t, t);
    execute format('create policy aislamiento_predio on adopcion.%I using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());', t);
    if t <> 'movimiento_saldo' then
      execute format('create trigger tg_%s_actualizado before update on adopcion.%I for each row execute function nucleo.marcar_actualizado();', t, t);
    end if;
    execute format('create trigger tg_%s_auditoria after insert or update or delete on adopcion.%I for each row execute function nucleo.auditar();', t, t);
  end loop;
end $$;
create trigger tg_movimiento_saldo_inmutable before update or delete on adopcion.movimiento_saldo for each row execute function nucleo.impedir_cambio();

-- ============================================================================ 3. Reglas de negocio
create or replace function adopcion.saldo(p_adoptante bigint) returns numeric language sql stable as $$
  select coalesce(sum(case when tipo = 'abono_liquidacion' then valor else -valor end), 0)
  from adopcion.movimiento_saldo where adoptante_id = p_adoptante $$;
comment on function adopcion.saldo(bigint) is 'Saldo a favor del adoptante (abonos menos cuotas compensadas y pagos)';

create or replace function adopcion.validar_movimiento() returns trigger language plpgsql as $$
begin
  if new.tipo <> 'abono_liquidacion' and adopcion.saldo(new.adoptante_id) < new.valor then
    raise exception 'Saldo insuficiente del adoptante: tiene %, se intentan descontar %', adopcion.saldo(new.adoptante_id), new.valor;
  end if;
  if new.tipo = 'pago_al_adoptante' then perform nucleo.exigir_persona('pagar saldos a adoptantes'); end if;
  return new;
end $$;
create trigger tg_movimiento_saldo_validar before insert on adopcion.movimiento_saldo for each row execute function adopcion.validar_movimiento();

create or replace function adopcion.validar_contrato() returns trigger language plpgsql as $$
declare b adopcion.bien; p adopcion.plan; v_ok boolean; v_activa boolean;
begin
  perform nucleo.exigir_funcion('adopcion');
  select * into b from adopcion.bien where id = new.bien_id;
  select * into p from adopcion.plan where id = b.plan_id;
  -- ADO-02: un contrato nace pendiente de pago y se activa cuando la pasarela confirma; solo entonces toma el bien
  v_activa := new.estado = 'activo' and (tg_op = 'INSERT' or old.estado = 'pendiente_pago');
  if tg_op = 'UPDATE' and old.estado = 'pendiente_pago' and new.estado is distinct from old.estado then
    if new.estado not in ('activo', 'cancelado') then
      raise exception 'El contrato % está pendiente de pago: solo se activa o se cancela', old.numero; end if;
    if new.estado = 'cancelado' then new.terminado_en := now(); end if;
  end if;
  if tg_op = 'INSERT' and new.estado not in ('activo', 'pendiente_pago') then
    raise exception 'Un contrato nace activo o pendiente de pago'; end if;
  if tg_op = 'INSERT' or v_activa then
    -- Al activar se revisa otra vez: otro adoptante pudo pagar primero el mismo bien
    if new.tipo = 'compra' and b.estado <> 'disponible' then
      raise exception 'El bien % no está disponible para compra (estado %)', b.codigo, b.estado; end if;
    if new.tipo = 'readopcion' and b.estado <> 'en_readopcion' then
      raise exception 'El bien % no está en readopción', b.codigo; end if;
    if new.tipo = 'cesion' and b.estado not in ('activo', 'maduro') then
      raise exception 'Solo se cede un bien vivo con contrato'; end if;
    if new.modalidad_siembra <> 'no_aplica' and p.tipo not in ('frutal', 'maderable') then
      raise exception 'La modalidad de siembra solo aplica a árboles'; end if;
    if p.tipo in ('frutal', 'maderable') and new.tipo = 'compra' and new.modalidad_siembra = 'no_aplica' then
      raise exception 'Indique si el adoptante siembra el árbol en persona o lo siembra un trabajador'; end if;
    if new.modalidad_siembra = 'trabajador' then
      select exists (select 1 from terceros.consentimiento_datos c where c.id = new.consentimiento_id and c.tercero_id = new.adoptante_id
                     and c.finalidad = 'seguimiento_adopcion' and c.otorgado and c.revocado_en is null) into v_ok;
      if not v_ok then raise exception 'Para enviar el video de siembra se necesita la autorización de datos del adoptante (seguimiento_adopcion)'; end if;
    end if;
    if v_activa then
      update terceros.tercero set es_adoptante = true where id = new.adoptante_id and not es_adoptante;
      update adopcion.bien set estado = case when new.tipo = 'cesion' then estado
                                             when p.tipo in ('frutal', 'maderable') and new.tipo = 'compra' then 'reservado' else 'activo' end,
                               fecha_inicio = coalesce(fecha_inicio, case when p.tipo in ('ovino', 'caprino', 'ave') then new.fecha end)
      where id = new.bien_id;
    end if;
  elsif tg_op = 'UPDATE' and old.estado <> 'pendiente_pago' then
    if old.estado <> 'activo' and new.estado is distinct from old.estado then
      raise exception 'El contrato % ya terminó (%)', old.numero, old.estado; end if;
    if new.decision_madurez is distinct from old.decision_madurez then
      if b.estado <> 'maduro' then raise exception 'El bien todavía no llega a su madurez'; end if;
      perform nucleo.exigir_persona('decidir sobre un bien adoptado');
      new.decidido_en := now();
    end if;
    if new.estado <> 'activo' and old.estado = 'activo' then new.terminado_en := now(); end if;
  end if;
  return new;
end $$;
create trigger tg_contrato_validar before insert or update on adopcion.contrato for each row execute function adopcion.validar_contrato();

create or replace function adopcion.cancelar_pendientes_pago(p_horas integer default 48) returns integer language sql as $$
  with c as (update adopcion.contrato set estado = 'cancelado'
             where estado = 'pendiente_pago' and creado_en < now() - make_interval(hours => p_horas) returning 1)
  select count(*)::integer from c $$;
comment on function adopcion.cancelar_pendientes_pago(integer) is 'Cancela los contratos que no se pagaron en p_horas (quedan para trazabilidad; el bien nunca se reservó). Prevista para una tarea programada';

create or replace function adopcion.ceder_previo() returns trigger language plpgsql as $$
begin  -- al ceder, el contrato anterior queda cedido antes de que entre el nuevo (índice de un activo por bien)
  if new.tipo = 'cesion' then
    update adopcion.contrato set estado = 'cedido' where bien_id = new.bien_id and estado = 'activo';
  end if;
  return new;
end $$;
create trigger tg_contrato_a_ceder before insert on adopcion.contrato for each row execute function adopcion.ceder_previo();

create or replace function adopcion.registrar_siembra(p_bien bigint, p_fecha date, p_tarea bigint default null, p_video varchar default null)
returns void language plpgsql as $$
declare c adopcion.contrato;
begin
  select * into c from adopcion.contrato where bien_id = p_bien and estado = 'activo';
  if c.id is null then raise exception 'El árbol no tiene contrato activo'; end if;
  if c.modalidad_siembra = 'trabajador' and p_video is null then
    raise exception 'La siembra por un trabajador exige el video para el adoptante'; end if;
  update adopcion.bien set estado = 'activo', fecha_inicio = p_fecha where id = p_bien and estado = 'reservado';
  if not found then raise exception 'El árbol % no está reservado para sembrar', p_bien; end if;
  update adopcion.sitio set estado = 'ocupado' where id = (select sitio_id from adopcion.bien where id = p_bien);
  insert into adopcion.seguimiento (bien_id, tipo, fecha, descripcion, evidencia_url, tarea_id)
  values (p_bien, case when p_video is null then 'siembra' else 'video_siembra' end, p_fecha,
          case c.modalidad_siembra when 'propia' then 'Sembrado por su dueño en la finca' else 'Sembrado por el equipo de la finca' end, p_video, p_tarea);
  insert into nucleo.evento_salida (tipo_evento, entidad, entidad_id, carga)
  values ('adopcion.sembrado', 'adopcion.bien', p_bien, jsonb_build_object('contrato', c.numero, 'video', p_video));
end $$;
comment on function adopcion.registrar_siembra(bigint, date, bigint, varchar) is 'Siembra del árbol adoptado: en persona o por un trabajador con video obligatorio; el agente de redes lo envía al adoptante';

create or replace function adopcion.generar_cuotas(p_mes date default current_date) returns integer language plpgsql as $$
declare v_n integer; v_mes date := date_trunc('month', p_mes)::date;
begin
  perform nucleo.exigir_funcion('adopcion');
  insert into adopcion.cuota (contrato_id, periodo, valor, vence_en)
  select c.id, v_mes, c.cuota_mensual, (v_mes + interval '9 days')::date
  from adopcion.contrato c join adopcion.bien b on b.id = c.bien_id
  where c.estado = 'activo' and b.estado in ('activo', 'maduro') and c.fecha < v_mes  -- el precio de compra cubre el primer mes
  on conflict (predio_id, contrato_id, periodo) do nothing;
  get diagnostics v_n = row_count;
  -- Compensa con el saldo a favor, del más antiguo al más reciente
  perform adopcion.compensar_cuotas();
  return v_n;
end $$;
comment on function adopcion.generar_cuotas(date) is 'Tarea mensual (día 1): una cuota por contrato activo; idempotente. Después compensa con saldos a favor';

create or replace function adopcion.compensar_cuotas() returns integer language plpgsql as $$
declare r record; v_n integer := 0;
begin
  for r in select q.id, q.valor, c.adoptante_id from adopcion.cuota q join adopcion.contrato c on c.id = q.contrato_id
           where q.estado = 'pendiente' order by q.periodo, q.id loop
    if adopcion.saldo(r.adoptante_id) >= r.valor then
      insert into adopcion.movimiento_saldo (adoptante_id, tipo, valor, cuota_id) values (r.adoptante_id, 'compensacion_cuota', r.valor, r.id);
      update adopcion.cuota set estado = 'compensada', pagada_en = now() where id = r.id;
      v_n := v_n + 1;
    end if;
  end loop;
  return v_n;
end $$;

create or replace function adopcion.marcar_abandono(p_fecha date default current_date) returns integer language plpgsql as $$
declare r record; v_n integer := 0; v_seg bigint;
  v_meses integer := coalesce(nucleo.parametro_valor('meses_abandono_adopcion', p_fecha), 3)::integer;
  v_gracia integer := coalesce(nucleo.parametro_valor('dias_gracia_abandono', p_fecha), 15)::integer;
begin
  perform nucleo.exigir_funcion('adopcion');
  for r in select c.id, c.numero, c.bien_id, count(*) as vencidas, max(q.vence_en) as ultima_vencida,
                  (array_agg(q.vence_en order by q.vence_en))[v_meses] as vence_ultimo_aviso,
                  (array_agg(q.id order by q.vence_en))[1] as cuota_mas_antigua
           from adopcion.contrato c join adopcion.cuota q on q.contrato_id = c.id
           where c.estado = 'activo' and q.estado = 'pendiente' and q.vence_en < p_fecha
           group by c.id loop
    -- Un aviso por cada cuota que se vence (no uno por día): sale al adoptante por el outbox (WhatsApp o correo)
    if not exists (select 1 from adopcion.seguimiento s where s.bien_id = r.bien_id and s.tipo = 'aviso_mora'
                   and s.fecha::date > r.ultima_vencida) then
      insert into adopcion.seguimiento (bien_id, tipo, fecha, descripcion)
      values (r.bien_id, 'aviso_mora', p_fecha, format('Cuotas vencidas: %s de %s antes de pasar a readopción', r.vencidas, v_meses))
      returning id into v_seg;
      insert into nucleo.evento_salida (tipo_evento, entidad, entidad_id, carga)
      values ('adopcion.aviso_mora', 'adopcion.contrato', r.id, jsonb_build_object('contrato', r.numero, 'bien_id', r.bien_id,
              'seguimiento_id', v_seg, 'cuotas_vencidas', r.vencidas, 'faltan', greatest(v_meses - r.vencidas, 0),
              'cuota_mas_antigua', r.cuota_mas_antigua, 'dias_gracia', v_gracia));
    end if;
    -- Nunca sin aviso previo: el aviso de la última cuota permitida debe estar entregado hace al menos v_gracia días
    if r.vencidas >= v_meses and exists (select 1 from adopcion.seguimiento s where s.bien_id = r.bien_id and s.tipo = 'aviso_mora'
           and s.enviado_al_adoptante and s.fecha::date > r.vence_ultimo_aviso and s.fecha::date <= p_fecha - v_gracia) then
      update adopcion.contrato set estado = 'terminado_abandono' where id = r.id;
      update adopcion.cuota set estado = 'anulada' where contrato_id = r.id and estado = 'pendiente';
      update adopcion.bien set estado = 'en_readopcion' where id = r.bien_id;
      insert into nucleo.evento_salida (tipo_evento, entidad, entidad_id, carga)
      values ('adopcion.abandonado', 'adopcion.contrato', r.id, jsonb_build_object('contrato', r.numero, 'cuotas_vencidas', r.vencidas));
      v_n := v_n + 1;
    end if;
  end loop;
  return v_n;
end $$;
comment on function adopcion.marcar_abandono(date) is 'Tarea diaria: un aviso por cada cuota que se vence (evento adopcion.aviso_mora); con N cuotas vencidas (meses_abandono_adopcion, 3) y el último aviso entregado hace dias_gracia_abandono días (15), el contrato termina sin reembolso y el bien pasa a readopción. El cuidado nunca se suspende (Ley 1774 de 2016)';

create or replace function adopcion.marcar_madurez(p_fecha date default current_date) returns integer language plpgsql as $$
declare v_n integer;
begin
  update adopcion.bien b set estado = 'maduro' from adopcion.plan p
  where p.id = b.plan_id and b.estado = 'activo' and b.fecha_inicio + make_interval(months => p.meses_madurez) <= p_fecha;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
comment on function adopcion.marcar_madurez(date) is 'Tarea mensual: el bien que cumplió su edad de madurez pasa a maduro y se le pide al dueño decidir: mantener o liquidar';

create or replace function adopcion.validar_liquidacion() returns trigger language plpgsql as $$
declare c adopcion.contrato; p adopcion.plan; b adopcion.bien; v_pct numeric;
begin
  if tg_op = 'UPDATE' and old.estado <> 'borrador' then raise exception 'La liquidación % ya fue %', old.id, old.estado; end if;
  select * into c from adopcion.contrato where id = new.contrato_id;
  select * into b from adopcion.bien where id = c.bien_id;
  select * into p from adopcion.plan where id = b.plan_id;
  if new.tipo in ('tala', 'sacrificio', 'venta_en_pie') then
    if c.decision_madurez is distinct from 'liquidar' then raise exception 'El dueño no ha decidido liquidar el bien %', b.codigo; end if;
    if new.tipo = 'tala' and p.tipo <> 'maderable' and p.tipo <> 'frutal' then raise exception 'Solo se talan árboles'; end if;
    if new.tipo = 'sacrificio' and p.tipo not in ('ovino', 'caprino', 'ave') then raise exception 'Solo se sacrifican animales'; end if;
  end if;
  v_pct := coalesce(nucleo.parametro_valor('comision_adopcion_pct', coalesce(new.periodo_hasta, current_date)), 5);
  new.utilidad_neta := new.ingresos - new.gastos;
  new.comision_pct := v_pct;
  new.comision := round(greatest(new.utilidad_neta, 0) * v_pct / 100, 0);
  new.abono_adoptante := greatest(new.utilidad_neta, 0) - new.comision;
  if new.estado = 'aprobada' then
    perform nucleo.exigir_persona('aprobar liquidaciones de adopción');
    if new.tipo in ('tala', 'sacrificio') and p.requiere_permiso <> 'ninguno' and new.soporte_documento_id is null then
      raise exception 'Para liquidar por % se exige el soporte (%): permiso de tala, remisión ICA o certificado de la planta de beneficio', new.tipo, p.requiere_permiso;
    end if;
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual()); new.aprobada_en := now();
  end if;
  return new;
end $$;
create trigger tg_liquidacion_validar before insert or update on adopcion.liquidacion for each row execute function adopcion.validar_liquidacion();

create or replace function adopcion.aplicar_liquidacion() returns trigger language plpgsql as $$
declare c adopcion.contrato;
begin
  if new.estado = 'aprobada' and (tg_op = 'INSERT' or old.estado = 'borrador') then
    select * into c from adopcion.contrato where id = new.contrato_id;
    if new.abono_adoptante > 0 then
      insert into adopcion.movimiento_saldo (adoptante_id, tipo, valor, liquidacion_id) values (c.adoptante_id, 'abono_liquidacion', new.abono_adoptante, new.id);
    end if;
    if new.tipo <> 'productos' then
      update adopcion.contrato set estado = 'terminado_liquidacion' where id = c.id;
      update adopcion.bien set estado = 'liquidado' where id = c.bien_id;
      update adopcion.sitio set estado = 'libre' where id = (select sitio_id from adopcion.bien where id = c.bien_id);
    end if;
    insert into nucleo.evento_salida (tipo_evento, entidad, entidad_id, carga)
    values ('adopcion.liquidado', 'adopcion.liquidacion', new.id, jsonb_build_object('utilidad', new.utilidad_neta, 'comision', new.comision, 'abono', new.abono_adoptante));
    perform adopcion.compensar_cuotas();
  end if;
  return null;
end $$;
create trigger tg_liquidacion_aplicar after insert or update on adopcion.liquidacion for each row execute function adopcion.aplicar_liquidacion();

create or replace function adopcion.registrar_muerte(p_bien bigint, p_fecha date, p_causa text) returns bigint language plpgsql as $$
declare b adopcion.bien; p adopcion.plan; c adopcion.contrato; v_nuevo bigint; v_mora boolean;
begin
  perform nucleo.exigir_persona('registrar la muerte de un bien adoptado');
  select * into b from adopcion.bien where id = p_bien;
  select * into p from adopcion.plan where id = b.plan_id;
  select * into c from adopcion.contrato where bien_id = p_bien and estado = 'activo';
  update adopcion.bien set estado = 'muerto' where id = p_bien;
  insert into adopcion.seguimiento (bien_id, tipo, fecha, descripcion) values (p_bien, 'muerte', p_fecha, p_causa);
  if c.id is null then return null; end if;
  select exists (select 1 from adopcion.cuota where contrato_id = c.id and estado = 'pendiente' and vence_en < p_fecha) into v_mora;
  if b.fecha_inicio is not null and p_fecha <= b.fecha_inicio + make_interval(months => p.garantia_meses) and not v_mora then
    -- Garantía: se repone sin costo un bien equivalente en el mismo sitio y el contrato sigue con el nuevo
    insert into adopcion.bien (codigo, plan_id, sitio_id, fecha_inicio, estado, nombre_dado, reemplaza_id)
    values (b.codigo || '-R', b.plan_id, b.sitio_id, p_fecha, 'activo', b.nombre_dado, b.id) returning id into v_nuevo;
    update adopcion.contrato set bien_id = v_nuevo where id = c.id;
    insert into adopcion.seguimiento (bien_id, tipo, fecha, descripcion) values (v_nuevo, 'reposicion', p_fecha, 'Reposición en garantía de ' || b.codigo);
    return v_nuevo;
  end if;
  update adopcion.contrato set estado = 'terminado_muerte' where id = c.id;
  update adopcion.cuota set estado = 'anulada' where contrato_id = c.id and estado = 'pendiente' and periodo > p_fecha;
  update adopcion.sitio set estado = 'libre' where id = b.sitio_id;
  return null;
end $$;
comment on function adopcion.registrar_muerte(bigint, date, text) is 'Muerte del bien: dentro de la garantía y al día se repone gratis; si no, el contrato termina sin cuotas futuras';

create or replace view adopcion.v_tablero as
select p.tipo,
       count(*) filter (where b.estado in ('activo', 'maduro', 'reservado')) as bienes_con_dueno,
       count(*) filter (where b.estado = 'en_readopcion') as en_readopcion,
       count(*) filter (where b.estado = 'disponible') as disponibles,
       (select coalesce(sum(c.cuota_mensual), 0) from adopcion.contrato c join adopcion.bien b2 on b2.id = c.bien_id
         join adopcion.plan p2 on p2.id = b2.plan_id where c.estado = 'activo' and p2.tipo = p.tipo) as cuotas_mes,
       (select coalesce(sum(p2.costo_cuidado_mensual), 0) from adopcion.contrato c join adopcion.bien b2 on b2.id = c.bien_id
         join adopcion.plan p2 on p2.id = b2.plan_id where c.estado = 'activo' and p2.tipo = p.tipo) as costo_cuidado_mes
from adopcion.bien b join adopcion.plan p on p.id = b.plan_id group by p.tipo;
comment on view adopcion.v_tablero is 'Tablero: bienes por estado, ingreso mensual por cuotas y costo de cuidado estimado, por tipo';

grant usage on schema adopcion to guayacan_app;
grant select, insert, update, delete on all tables in schema adopcion to guayacan_app;
revoke update, delete on adopcion.movimiento_saldo from guayacan_app;
grant execute on all functions in schema adopcion to guayacan_app;

-- ============================================================================ 4. Datos iniciales (por finca)
insert into nucleo.funcionalidad (predio_id, codigo, descripcion, fase, requiere_equipo, activa)
select id, 'adopcion', 'Adopción de árboles y animales por turistas (apéndice A)', 3, 'Revisión jurídica del contrato y concepto del contador sobre IVA', false
from nucleo.predio on conflict (predio_id, codigo) do nothing;
insert into nucleo.parametro (predio_id, clave, valor, tipo_dato, vigente_desde, descripcion) values
 (null, 'comision_adopcion_pct', '5', 'porcentaje', '2026-10-30', 'Comisión de administración sobre la utilidad neta de cada liquidación de un bien adoptado'),
 (null, 'meses_abandono_adopcion', '3', 'entero', '2026-10-30', 'Cuotas vencidas tras las cuales el bien pasa a readopción'),
 (null, 'dias_gracia_abandono', '15', 'entero', '2026-10-30', 'Días desde el último aviso de mora entregado antes de pasar el bien a readopción');
