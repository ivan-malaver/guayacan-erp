-- GuayacanERP · Migración 013 · ADO-12: liquidación por dos personas y con soporte válido
-- 1. Una liquidación nace en borrador y la aprueba una persona distinta de quien la registró (columna registrada_por).
-- 2. La venta en pie también exige el soporte del plan (remisión ICA de un animal vivo, permiso de tala de un árbol en pie).
-- 3. El soporte debe ser un documento de tipo permiso o certificado, con entidad emisora y número.
-- 4. Permiso adopcion.aprobar_liquidacion para administrador y familia (la API lo exige al aprobar).
-- Para bases cargadas con apendice_a_adopcion.sql anterior. Una base nueva no la necesita: el apéndice ya trae los cambios.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/013_ado12_liquidacion_dos_personas.sql
\set ON_ERROR_STOP 1
begin;

alter table adopcion.liquidacion add column if not exists registrada_por bigint;
comment on column adopcion.liquidacion.registrada_por is 'Persona que registró el borrador (no puede aprobarla)';

-- Mismo cuerpo que en apendice_a_adopcion.sql
create or replace function adopcion.validar_liquidacion() returns trigger language plpgsql as $$
declare c adopcion.contrato; p adopcion.plan; b adopcion.bien; d documental.documento; v_pct numeric;
begin
  if tg_op = 'UPDATE' and old.estado <> 'borrador' then raise exception 'La liquidación % ya fue %', old.id, old.estado; end if;
  -- Dos personas (ADO-12): quien registra el borrador no lo aprueba
  if tg_op = 'INSERT' then
    new.registrada_por := nucleo.usuario_actual();
    if new.estado <> 'borrador' then raise exception 'Una liquidación nace en borrador: la aprueba después otra persona'; end if;
  else
    new.registrada_por := old.registrada_por;
  end if;
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
    if nucleo.usuario_actual() is null or nucleo.usuario_actual() = new.registrada_por then
      raise exception 'La liquidación % la aprueba una persona distinta de quien la registró', new.id;
    end if;
    -- La venta en pie también mueve el bien (remisión ICA de un animal vivo, permiso de tala de un árbol en pie)
    if new.tipo in ('tala', 'sacrificio', 'venta_en_pie') and p.requiere_permiso <> 'ninguno' then
      if new.soporte_documento_id is null then
        raise exception 'Para liquidar por % se exige el soporte (%): permiso de tala, remisión ICA o certificado de la planta de beneficio', new.tipo, p.requiere_permiso;
      end if;
      select * into d from documental.documento where id = new.soporte_documento_id;
      if d.id is null or d.tipo not in ('permiso', 'certificado') or d.entidad_emisora is null or d.numero is null then
        raise exception 'El soporte % debe ser un permiso o certificado con entidad emisora y número', d.codigo;
      end if;
    end if;
    new.aprobada_por := nucleo.usuario_actual(); new.aprobada_en := now();
  end if;
  return new;
end $$;

insert into nucleo.permiso (codigo, nombre, modulo)
select 'adopcion.aprobar_liquidacion', 'Aprobar liquidaciones de adopción', 'adopcion'
where not exists (select 1 from nucleo.permiso where codigo = 'adopcion.aprobar_liquidacion');
insert into nucleo.rol_permiso (rol_id, permiso_id)
select r.id, p.id from nucleo.rol r join nucleo.permiso p on p.codigo = 'adopcion.aprobar_liquidacion'
where r.codigo in ('administrador', 'familia')
  and not exists (select 1 from nucleo.rol_permiso rp where rp.rol_id = r.id and rp.permiso_id = p.id);

commit;
