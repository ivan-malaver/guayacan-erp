-- GuayacanERP · Migración 001 · ADO-02: contrato pendiente de pago y pasarela simulada
-- Para bases ya cargadas con apendice_a_adopcion.sql anterior. Una base nueva no la necesita: el apéndice ya trae estos cambios.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/001_ado02_contrato_pendiente_pago.sql
\set ON_ERROR_STOP 1
begin;

-- Pagos de prueba con la pasarela simulada (guayacan/pasarela.py) mientras se conecta Wompi
alter table comercial.pago drop constraint if exists ck_pago_proveedor_pasarela;
alter table comercial.pago add constraint ck_pago_proveedor_pasarela check (proveedor_pasarela in
  ('wompi', 'mercado_pago', 'epayco', 'payu', 'simulada'));

-- El contrato nace pendiente de pago; se activa al confirmar o se cancela
alter table adopcion.contrato drop constraint if exists ck_contrato_estado;
alter table adopcion.contrato add constraint ck_contrato_estado check (estado in
  ('pendiente_pago', 'activo', 'cancelado', 'terminado_abandono', 'terminado_liquidacion', 'cedido', 'terminado_muerte'));

-- Mismo cuerpo que en apendice_a_adopcion.sql
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

create or replace function adopcion.cancelar_pendientes_pago(p_horas integer default 48) returns integer language sql as $$
  with c as (update adopcion.contrato set estado = 'cancelado'
             where estado = 'pendiente_pago' and creado_en < now() - make_interval(hours => p_horas) returning 1)
  select count(*)::integer from c $$;
comment on function adopcion.cancelar_pendientes_pago(integer) is 'Cancela los contratos que no se pagaron en p_horas (quedan para trazabilidad; el bien nunca se reservó). Prevista para una tarea programada';

commit;
