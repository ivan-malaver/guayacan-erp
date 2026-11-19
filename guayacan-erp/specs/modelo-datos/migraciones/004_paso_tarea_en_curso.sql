-- GuayacanERP · Migración 004 · NUC-05 / PER-05: un paso solo se marca en una tarea en curso
-- Para bases cargadas con esquema_postgresql.sql anterior. Una base nueva no la necesita: el esquema ya trae la regla.
-- Vale igual para la API y para la sincronización sin conexión (que no pasa por los servicios).
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/004_paso_tarea_en_curso.sql
\set ON_ERROR_STOP 1
begin;

-- Mismo cuerpo que en generador/reglas_negocio.sql (de donde sale esquema_postgresql.sql)
create or replace function personal.validar_paso_tarea() returns trigger language plpgsql as $$
declare v_estado text;
begin
  select estado into v_estado from personal.tarea where id = new.tarea_id;
  if tg_op = 'UPDATE' and v_estado in ('aprobada', 'cancelada') then
    raise exception 'La tarea % está %: sus pasos no se editan', new.tarea_id, v_estado;
  end if;
  if new.hecho and (tg_op = 'INSERT' or not old.hecho) then
    if v_estado <> 'en_curso' then
      raise exception 'Solo se marcan pasos de una tarea en curso (la tarea % está %)', new.tarea_id, v_estado;
    end if;
    new.hecho_en := coalesce(new.hecho_en, now());
  end if;
  return new;
end $$;
drop trigger if exists tg_paso_tarea_validar on personal.paso_tarea;
create trigger tg_paso_tarea_validar before insert or update on personal.paso_tarea for each row execute function personal.validar_paso_tarea();

commit;
