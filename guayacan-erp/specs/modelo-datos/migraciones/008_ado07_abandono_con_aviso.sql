-- GuayacanERP · Migración 008 · ADO-07: nunca abandono sin aviso entregado
-- Un aviso por cada cuota que se vence (evento adopcion.aviso_mora, no uno por día) y abandono solo con el aviso de la
-- tercera cuota confirmado como entregado hace 15 días o más (parámetro dias_gracia_abandono).
-- Para bases cargadas con apendice_a_adopcion.sql anterior. Una base nueva no la necesita: el apéndice ya trae los cambios.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/008_ado07_abandono_con_aviso.sql
\set ON_ERROR_STOP 1
begin;

insert into nucleo.parametro (predio_id, clave, valor, tipo_dato, vigente_desde, descripcion) values
 (null, 'dias_gracia_abandono', '15', 'entero', '2026-10-30', 'Días desde el último aviso de mora entregado antes de pasar el bien a readopción')
on conflict do nothing;

-- Mismo cuerpo que en apendice_a_adopcion.sql
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

commit;
