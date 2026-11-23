-- GuayacanERP · Migración 009 · ADO-13: la muerte de un bien sin dueño libera su sitio
-- adopcion.registrar_muerte() terminaba antes de liberar el sitio cuando el bien no tenía contrato activo (disponible o
-- en readopción), y aceptaba registrar dos veces la muerte de un bien ya muerto o liquidado.
-- Para bases cargadas con apendice_a_adopcion.sql anterior. Una base nueva no la necesita: el apéndice ya trae los cambios.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/009_ado13_muerte_libera_sitio.sql
\set ON_ERROR_STOP 1
begin;

-- Mismo cuerpo que en apendice_a_adopcion.sql
create or replace function adopcion.registrar_muerte(p_bien bigint, p_fecha date, p_causa text) returns bigint language plpgsql as $$
declare b adopcion.bien; p adopcion.plan; c adopcion.contrato; v_nuevo bigint; v_mora boolean;
begin
  perform nucleo.exigir_persona('registrar la muerte de un bien adoptado');
  select * into b from adopcion.bien where id = p_bien;
  select * into p from adopcion.plan where id = b.plan_id;
  select * into c from adopcion.contrato where bien_id = p_bien and estado = 'activo';
  if b.estado in ('muerto', 'liquidado') then raise exception 'El bien % ya está %', b.codigo, b.estado; end if;
  update adopcion.bien set estado = 'muerto' where id = p_bien;
  insert into adopcion.seguimiento (bien_id, tipo, fecha, descripcion) values (p_bien, 'muerte', p_fecha, p_causa);
  if c.id is null then  -- sin dueño (disponible o en readopción): solo se libera el sitio
    update adopcion.sitio set estado = 'libre' where id = b.sitio_id;
    return null;
  end if;
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

commit;
