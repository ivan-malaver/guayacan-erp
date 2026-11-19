-- GuayacanERP · Migración 006 · PER-06: aprobar sin permiso o la propia tarea responde 403; la cuadrilla tampoco se aprueba a sí misma
-- Para bases cargadas con esquema_postgresql.sql anterior. Una base nueva no la necesita: el esquema ya trae estos cambios.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/006_per06_aprobar_tarea.sql
\set ON_ERROR_STOP 1
begin;

-- Mismo cuerpo que en generador/reglas_negocio.sql (de donde sale esquema_postgresql.sql)
create or replace function personal.validar_tarea() returns trigger language plpgsql as $$
declare v_comp bigint; v_ter bigint; v_emp record;
begin
  if tg_op = 'UPDATE' and old.estado in ('aprobada', 'cancelada') then
    raise exception 'La tarea % está %: no se edita', old.id, old.estado;
  end if;
  -- PER-05: iniciar o terminar la tarea lo hace quien la ejecuta; vale también para la sincronización sin conexión
  if new.estado in ('en_curso', 'terminada') and (tg_op = 'INSERT' or old.estado is distinct from new.estado)
     and nucleo.usuario_actual() is not null
     and not personal.puede_ejecutar_tarea(nucleo.usuario_actual(), new.empleado_id, new.cuadrilla_id, new.fecha) then
    raise exception 'Solo el trabajador asignado, su cuadrilla o quien asigna tareas puede iniciar o terminar la tarea %', new.id
      using errcode = '42501';
  end if;
  if nucleo.agente_actual() is not null and (new.empleado_id is not null or new.cuadrilla_id is not null)
     and (tg_op = 'INSERT' or new.empleado_id is distinct from old.empleado_id or new.cuadrilla_id is distinct from old.cuadrilla_id) then
    raise exception 'Un agente propone tareas pero no las asigna: la asignación la hace el encargado';
  end if;
  select competencia_id into v_comp from personal.plantilla_tarea where id = new.plantilla_tarea_id;
  if new.empleado_id is not null and (tg_op = 'INSERT' or new.empleado_id is distinct from old.empleado_id or new.fecha <> old.fecha) then
    if not personal.empleado_disponible(new.empleado_id, new.fecha) then
      raise exception 'El trabajador % no está disponible el % (retirado o con ausencia)', new.empleado_id, new.fecha;
    end if;
    select tercero_id into v_ter from terceros.empleado where id = new.empleado_id;
    if v_comp is not null and not formacion.esta_habilitado(v_ter, v_comp, new.fecha) then
      raise exception 'El trabajador % no está habilitado para esta tarea (falta el curso o el certificado venció)', new.empleado_id;
    end if;
  end if;
  if new.cuadrilla_id is not null and (tg_op = 'INSERT' or new.cuadrilla_id is distinct from old.cuadrilla_id or new.fecha <> old.fecha) then
    for v_emp in select e.id, e.tercero_id from personal.cuadrilla_miembro m join terceros.empleado e on e.id = m.empleado_id
                 where m.cuadrilla_id = new.cuadrilla_id and m.desde <= new.fecha and (m.hasta is null or m.hasta >= new.fecha) loop
      if v_comp is not null and not formacion.esta_habilitado(v_emp.tercero_id, v_comp, new.fecha) then
        raise exception 'El trabajador % de la cuadrilla no está habilitado para esta tarea', v_emp.id;
      end if;
      if not personal.empleado_disponible(v_emp.id, new.fecha) then
        raise exception 'El trabajador % de la cuadrilla no está disponible el % (retirado o con ausencia)', v_emp.id, new.fecha;
      end if;
    end loop;
  end if;
  if new.estado = 'en_curso' and (tg_op = 'INSERT' or old.estado <> 'en_curso') then new.iniciada_en := coalesce(new.iniciada_en, now()); end if;
  if new.estado = 'terminada' and (tg_op = 'INSERT' or old.estado <> 'terminada') then
    new.terminada_en := coalesce(new.terminada_en, now());
    -- PER-05: aviso al aprobador (PER-06) desde la base, así sale igual con conexión o por la sincronización
    insert into nucleo.evento_salida (tipo_evento, entidad, entidad_id, carga) values ('personal.tarea_terminada', 'personal.tarea', new.id,
      jsonb_build_object('titulo', new.titulo, 'empleado_id', new.empleado_id, 'cuadrilla_id', new.cuadrilla_id, 'area_id', new.area_id, 'cantidad', new.cantidad));
  end if;
  if new.estado in ('aprobada', 'devuelta') and (tg_op = 'INSERT' or old.estado <> new.estado) then
    perform nucleo.exigir_persona('aprobar o devolver tareas');
    if tg_op = 'INSERT' or old.estado <> 'terminada' then raise exception 'Solo se aprueba o devuelve una tarea terminada'; end if;
    new.aprobado_por := coalesce(new.aprobado_por, nucleo.usuario_actual());
    -- PER-06: sin permiso o sobre su propia tarea es un problema de permisos: SQLSTATE 42501 (la API responde 403)
    if not nucleo.tiene_permiso(new.aprobado_por, 'personal.aprobar_tarea')
       and not (new.area_id is not null and personal.es_responsable_area(new.aprobado_por, new.area_id, new.fecha)) then
      raise exception 'El usuario % no tiene el permiso personal.aprobar_tarea ni es responsable del área', new.aprobado_por
        using errcode = '42501';
    end if;
    -- Su propia tarea: la asignada a él o a una cuadrilla de la que era miembro ese día
    if exists (select 1 from terceros.empleado e
               where e.tercero_id = nucleo.tercero_de_usuario(new.aprobado_por)
                 and (e.id = new.empleado_id
                      or exists (select 1 from personal.cuadrilla_miembro m where m.cuadrilla_id = new.cuadrilla_id and m.empleado_id = e.id
                                 and m.desde <= new.fecha and (m.hasta is null or m.hasta >= new.fecha)))) then
      raise exception 'Nadie aprueba su propia tarea' using errcode = '42501';
    end if;
    if new.estado = 'devuelta' and new.comentario_revision is null then raise exception 'Para devolver una tarea hay que decir por qué'; end if;
    new.aprobado_en := now();
  end if;
  return new;
end $$;

commit;
