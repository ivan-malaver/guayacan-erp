-- ============================================================================
-- GuayacanERP · Reglas de negocio en la base de datos (escritas a mano)
-- El generador inserta la primera parte antes de crear las tablas y la segunda después.
-- ============================================================================

-- Sesión: la API fija estos valores al inicio de cada transacción:
--   select set_config('app.predio_id', '<id>', true), set_config('app.usuario_id', '<id>', true),
--          set_config('app.agente_id', '<id o vacío>', true);
create or replace function nucleo.predio_actual() returns bigint language sql stable as
$$ select nullif(current_setting('app.predio_id', true), '')::bigint $$;
create or replace function nucleo.usuario_actual() returns bigint language sql stable as
$$ select nullif(current_setting('app.usuario_id', true), '')::bigint $$;
create or replace function nucleo.agente_actual() returns bigint language sql stable as
$$ select nullif(current_setting('app.agente_id', true), '')::bigint $$;
comment on function nucleo.predio_actual() is 'Finca de la sesión; base de la seguridad por filas';

create or replace function nucleo.marcar_actualizado() returns trigger language plpgsql as
$$ begin new.actualizado_en := now(); return new; end $$;

-- Particiones mensuales (auditoría y lecturas IoT): una tarea mensual crea las siguientes con nucleo.mantener_particiones()
create or replace function nucleo.crear_particion_mensual(p_tabla text, p_mes date) returns text language plpgsql as $$
declare v_ini date := date_trunc('month', p_mes)::date; v_fin date := (date_trunc('month', p_mes) + interval '1 month')::date;
        v_nombre text := p_tabla || '_' || to_char(date_trunc('month', p_mes), 'YYYYMM');
begin
  if to_regclass(v_nombre) is null then
    execute format('create table %s partition of %s for values from (%L) to (%L)', v_nombre, p_tabla, v_ini, v_fin);
    if exists (select 1 from pg_roles where rolname = 'guayacan_app') then
      execute format('revoke all on %s from guayacan_app', v_nombre);
    end if;
  end if;
  return v_nombre;
end $$;
comment on function nucleo.crear_particion_mensual(text, date) is 'Crea la partición de un mes; la aplicación solo accede por la tabla madre, así la seguridad por filas siempre aplica';

-- @@ DESPUES_DE_TABLAS @@

-- ============================================================================
-- 1. Auditoría automática (tablas sensibles). Guarda solo los campos que cambiaron.
-- ============================================================================
create or replace function nucleo.auditar() returns trigger language plpgsql security definer set search_path = pg_catalog, nucleo as $$
declare
  v_antes jsonb := case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) end;
  v_despues jsonb := case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) end;
  v_fila jsonb := case when tg_op = 'DELETE' then to_jsonb(old) else to_jsonb(new) end;
  v_clave text;
begin
  if tg_op = 'UPDATE' then
    for v_clave in select key from jsonb_each(v_despues) loop
      if v_antes -> v_clave is not distinct from v_despues -> v_clave then
        v_antes := v_antes - v_clave; v_despues := v_despues - v_clave;
      end if;
    end loop;
    v_antes := v_antes - 'actualizado_en'; v_despues := v_despues - 'actualizado_en';
    if v_despues = '{}'::jsonb then return null; end if;
  end if;
  insert into nucleo.auditoria (predio_id, esquema_tabla, registro_id, accion, datos_antes, datos_despues, usuario_id, agente_id)
  values (coalesce((v_fila ->> 'predio_id')::bigint, nucleo.predio_actual()),
          tg_table_schema || '.' || tg_table_name, (v_fila ->> 'id')::bigint,
          case tg_op when 'INSERT' then 'crear' when 'UPDATE' then 'actualizar' else 'eliminar' end,
          v_antes, v_despues, nucleo.usuario_actual(), nucleo.agente_actual());
  return null;
end $$;
comment on function nucleo.auditar() is 'Disparador genérico de auditoría: quién (usuario o agente de la sesión), qué tabla, qué registro y qué campos cambiaron';

create or replace function nucleo.impedir_cambio() returns trigger language plpgsql as
$$ begin raise exception 'La tabla % es de solo inserción', tg_table_name; end $$;
create trigger tg_auditoria_inmutable before update or delete on nucleo.auditoria for each row execute function nucleo.impedir_cambio();

-- Fincas a las que puede entrar un usuario (para elegir finca al iniciar sesión; salta la RLS a propósito)
create or replace function nucleo.predios_del_usuario(p_usuario bigint)
returns table (predio_id bigint, nombre varchar, rol varchar) language sql stable security definer set search_path = pg_catalog, nucleo as $$
  select p.id, p.nombre, r.codigo from nucleo.usuario_rol ur join nucleo.predio p on p.id = ur.predio_id join nucleo.rol r on r.id = ur.rol_id
  where ur.usuario_id = p_usuario order by p.nombre $$;

-- ============================================================================
-- 2. Inventario perecedero: vencimiento estimado, kardex como única fuente, FEFO
-- ============================================================================
-- 2.1 Estimar vencimiento y fecha límite de venta
create or replace function inventario.estimar_vencimiento() returns trigger language plpgsql as $$
declare v_prod record; v_dias smallint;
begin
  select perecedero, vida_util_ambiente_dias, vida_util_refrigerado_dias, dias_margen_venta into v_prod
  from inventario.producto where id = new.producto_id;
  if new.origen_vencimiento = 'estimado' then
    v_dias := case new.condicion_almacenamiento when 'refrigerado' then coalesce(v_prod.vida_util_refrigerado_dias, v_prod.vida_util_ambiente_dias)
                                                 else v_prod.vida_util_ambiente_dias end;
    new.fecha_vencimiento := case when v_prod.perecedero and v_dias is not null then new.fecha_produccion + v_dias end;
  elsif new.fecha_vencimiento is null then
    raise exception 'Lote %: con vencimiento % debe indicar la fecha de vencimiento', new.codigo_lote, new.origen_vencimiento;
  end if;
  new.fecha_limite_venta := new.fecha_vencimiento - coalesce(v_prod.dias_margen_venta, 0);
  return new;
end $$;
create trigger tg_lote_vencimiento before insert or update of fecha_produccion, condicion_almacenamiento, origen_vencimiento, fecha_vencimiento
  on inventario.lote_inventario for each row execute function inventario.estimar_vencimiento();

-- 2.2 Las cantidades del lote solo las cambia el kardex
create or replace function inventario.proteger_cantidades() returns trigger language plpgsql as $$
begin
  if coalesce(current_setting('guayacan.desde_kardex', true), '') <> 'si' then
    if tg_op = 'INSERT' then
      new.cantidad_disponible := 0; new.cantidad_reservada := 0;
    elsif new.cantidad_disponible is distinct from old.cantidad_disponible or new.cantidad_reservada is distinct from old.cantidad_reservada then
      raise exception 'Las cantidades del lote % solo cambian con un movimiento de inventario', old.codigo_lote;
    end if;
  end if;
  return new;
end $$;
create trigger tg_lote_proteger before insert or update on inventario.lote_inventario for each row execute function inventario.proteger_cantidades();

create or replace function inventario.entrada_inicial() returns trigger language plpgsql as $$
begin
  insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
  values (new.predio_id, new.id, 'entrada', new.cantidad_inicial, new.costo_unitario, coalesce(new.origen_tabla, 'lote_inventario'), coalesce(new.origen_id, new.id), nucleo.usuario_actual());
  return null;
end $$;
create trigger tg_lote_entrada after insert on inventario.lote_inventario for each row execute function inventario.entrada_inicial();

-- 2.3 Aplicar cada movimiento al lote (con bloqueo de fila: dos reservas simultáneas no pueden tomar el mismo producto)
create or replace function inventario.aplicar_movimiento() returns trigger language plpgsql as $$
declare v_lote record; v_disp numeric; v_res numeric;
begin
  if new.cantidad <= 0 then raise exception 'La cantidad del movimiento debe ser positiva'; end if;
  if new.tipo = 'merma' and new.causa_merma is null then raise exception 'Toda merma debe indicar su causa'; end if;
  select * into v_lote from inventario.lote_inventario where id = new.lote_inventario_id for update;
  v_disp := v_lote.cantidad_disponible; v_res := v_lote.cantidad_reservada;
  case new.tipo
    when 'entrada', 'ajuste_entrada', 'traslado_entrada' then v_disp := v_disp + new.cantidad;
    when 'reserva' then v_disp := v_disp - new.cantidad; v_res := v_res + new.cantidad;
    when 'liberacion' then v_res := v_res - new.cantidad; v_disp := v_disp + new.cantidad;
    when 'salida_venta' then v_res := v_res - new.cantidad;
    else v_disp := v_disp - new.cantidad;  -- consumo_interno, merma, ajuste_salida, traslado_salida
  end case;
  if v_disp < 0 or v_res < 0 then
    raise exception 'Inventario insuficiente en el lote %: disponible %, reservado %, se pidió % (%)',
      v_lote.codigo_lote, v_lote.cantidad_disponible, v_lote.cantidad_reservada, new.cantidad, new.tipo;
  end if;
  if new.tipo in ('reserva', 'salida_venta') and v_lote.estado in ('vencido', 'bloqueado') then
    raise exception 'El lote % está % y no se puede vender', v_lote.codigo_lote, v_lote.estado;
  end if;
  perform set_config('guayacan.desde_kardex', 'si', true);
  update inventario.lote_inventario set cantidad_disponible = v_disp, cantidad_reservada = v_res,
    estado = case when v_disp + v_res = 0 and estado = 'disponible' then 'agotado'
                  when v_disp + v_res > 0 and estado = 'agotado' then 'disponible' else estado end
  where id = new.lote_inventario_id;
  perform set_config('guayacan.desde_kardex', 'no', true);
  return null;
end $$;
create trigger tg_movimiento_aplicar after insert on inventario.movimiento_inventario for each row execute function inventario.aplicar_movimiento();
create trigger tg_movimiento_inmutable before update or delete on inventario.movimiento_inventario for each row execute function nucleo.impedir_cambio();
comment on function inventario.aplicar_movimiento() is 'Kardex: único camino para cambiar existencias; las correcciones se hacen con ajuste_entrada o ajuste_salida, nunca editando';

-- 2.3b Especificación única: ¿se puede vender este lote? (la usan la reserva FEFO, el catálogo y el escaneo)
create or replace function inventario.puede_venderse(l inventario.lote_inventario) returns boolean language sql stable as $$
  select l.estado = 'disponible' and l.cantidad_disponible > 0
     and (l.fecha_limite_venta is null or l.fecha_limite_venta >= current_date)
     and not exists (select 1 from inventario.bloqueo_lote b where b.lote_inventario_id = l.id and b.decision = 'pendiente') $$;
comment on function inventario.puede_venderse(inventario.lote_inventario) is 'Patrón Specification: disponible, con existencias, antes de su fecha límite de venta y sin bloqueo abierto';

-- 2.4 Reservar en orden FEFO (primero lo que vence primero); no toma lotes pasados de su fecha límite de venta
create or replace function inventario.reservar_fefo(p_detalle bigint) returns numeric language plpgsql as $$
declare d record; r record; v_pend numeric; v_tomar numeric;
begin
  select pd.*, p.metodo_salida, p.nombre as producto into d
  from comercial.pedido_detalle pd join inventario.producto p on p.id = pd.producto_id where pd.id = p_detalle;
  v_pend := d.cantidad;
  for r in select l.id, l.cantidad_disponible, l.costo_unitario from inventario.lote_inventario l
           where l.producto_id = d.producto_id and inventario.puede_venderse(l)
           order by case when d.metodo_salida = 'fefo' then l.fecha_vencimiento end nulls last, l.fecha_produccion, l.id
           for update skip locked loop
    v_tomar := least(v_pend, r.cantidad_disponible);
    insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
    values (d.predio_id, r.id, 'reserva', v_tomar, r.costo_unitario, 'pedido_detalle', p_detalle, nucleo.usuario_actual());
    insert into comercial.reserva_lote (predio_id, pedido_detalle_id, lote_inventario_id, cantidad) values (d.predio_id, p_detalle, r.id, v_tomar);
    v_pend := v_pend - v_tomar;
    exit when v_pend = 0;
  end loop;
  if v_pend > 0 then
    raise exception 'Inventario insuficiente de %: faltan % para la línea %', d.producto, v_pend, p_detalle;
  end if;
  return d.cantidad;
end $$;

-- 2.5 Confirmar, despachar y cancelar pedidos
create or replace function comercial.confirmar_pedido(p_pedido bigint) returns void language plpgsql as $$
declare d record; v_ped record; v_cli record; v_total numeric; v_cartera numeric;
begin
  select * into v_ped from comercial.pedido where id = p_pedido for update;
  if v_ped.estado <> 'borrador' then raise exception 'El pedido % está % y no se puede confirmar', v_ped.numero, v_ped.estado; end if;
  if v_ped.forma_pago = 'credito' then
    perform nucleo.exigir_funcion('venta_credito');
    select * into v_cli from terceros.cliente where id = v_ped.cliente_id;
    if v_cli.bloqueado_por_mora then raise exception 'El cliente tiene facturas vencidas: no puede comprar a crédito'; end if;
  end if;
  for d in select pd.id, pp.vigente_hasta from comercial.pedido_detalle pd join comercial.precio_producto pp on pp.id = pd.precio_producto_id
           where pd.pedido_id = p_pedido loop
    if d.vigente_hasta is not null then
      raise exception 'El precio de la línea % cambió después de crear el pedido; actualícelo antes de confirmar', d.id;
    end if;
    perform inventario.reservar_fefo(d.id);
  end loop;
  update comercial.pedido p set estado = 'confirmado',
    subtotal = t.sub, descuento = t.des, impuestos = t.iva, total = t.sub - t.des + t.iva + p.valor_domicilio
  from (select coalesce(sum(cantidad * precio_unitario), 0) sub, coalesce(sum(descuento), 0) des,
               coalesce(sum(round((cantidad * precio_unitario - descuento) * tarifa_iva / 100, 2)), 0) iva
        from comercial.pedido_detalle where pedido_id = p_pedido) t
  where p.id = p_pedido
  returning p.total into v_total;
  if v_ped.forma_pago = 'credito' then
    select coalesce(sum(saldo), 0) into v_cartera from comercial.factura where cliente_id = v_ped.cliente_id and saldo > 0;
    if v_cartera + v_total > v_cli.cupo_credito then
      raise exception 'Cupo de crédito insuficiente: cartera %, pedido %, cupo %', v_cartera, v_total, v_cli.cupo_credito;
    end if;
  end if;
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (v_ped.predio_id, 'pedido.confirmado', 'comercial.pedido', p_pedido, jsonb_build_object('numero', v_ped.numero, 'cliente_id', v_ped.cliente_id));
end $$;

create or replace function comercial.despachar_pedido(p_pedido bigint) returns void language plpgsql as $$
declare r record;
begin
  for r in select rl.* , l.costo_unitario from comercial.reserva_lote rl join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id
           join inventario.lote_inventario l on l.id = rl.lote_inventario_id
           where pd.pedido_id = p_pedido and rl.estado = 'reservada' loop
    insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
    values (r.predio_id, r.lote_inventario_id, 'salida_venta', r.cantidad, r.costo_unitario, 'pedido', p_pedido, nucleo.usuario_actual());
    update comercial.reserva_lote set estado = 'despachada' where id = r.id;
  end loop;
  update comercial.pedido set estado = 'despachado' where id = p_pedido and estado in ('confirmado', 'en_preparacion');
  if not found then raise exception 'El pedido % no está confirmado', p_pedido; end if;
end $$;

create or replace function comercial.cancelar_pedido(p_pedido bigint) returns void language plpgsql as $$
declare r record;
begin
  for r in select rl.*, l.costo_unitario from comercial.reserva_lote rl join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id
           join inventario.lote_inventario l on l.id = rl.lote_inventario_id
           where pd.pedido_id = p_pedido and rl.estado = 'reservada' loop
    insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
    values (r.predio_id, r.lote_inventario_id, 'liberacion', r.cantidad, r.costo_unitario, 'pedido', p_pedido, nucleo.usuario_actual());
    update comercial.reserva_lote set estado = 'liberada' where id = r.id;
  end loop;
  update comercial.pedido set estado = 'cancelado' where id = p_pedido and estado not in ('despachado', 'entregado');
  if not found then raise exception 'El pedido % ya salió de la finca; use una devolución', p_pedido; end if;
end $$;

-- 2.6 Tarea diaria (Celery Beat): marcar vencidos. La merma la registra una persona tras revisar el producto.
create or replace function inventario.marcar_vencidos() returns integer language plpgsql as $$
declare n integer;
begin
  update inventario.lote_inventario set estado = 'vencido'
  where estado = 'disponible' and fecha_vencimiento < current_date and cantidad_disponible + cantidad_reservada > 0;
  get diagnostics n = row_count;
  return n;
end $$;

-- 2.7 Alertas de vencimiento (semáforo) con precio de liquidación según la política aprobada por el administrador
create view inventario.v_alertas_vencimiento with (security_invoker = true) as
select l.predio_id, l.id as lote_inventario_id, l.codigo_lote, p.id as producto_id, p.sku, p.nombre as producto,
       l.cantidad_disponible, l.fecha_produccion, l.fecha_vencimiento, l.fecha_limite_venta,
       l.fecha_limite_venta - current_date as dias_para_limite,
       case when l.fecha_limite_venta < current_date then 'rojo'
            when l.fecha_limite_venta - current_date <= p.dias_alerta_venta then 'amarillo' else 'verde' end as semaforo,
       case when l.fecha_limite_venta < current_date then 'no vender: revisar y registrar merma, autoconsumo o alimento animal'
            when l.fecha_limite_venta - current_date <= p.dias_alerta_venta then 'vender primero: ofrecer a clientes frecuentes con precio de liquidación'
            else 'normal' end as accion_sugerida,
       pp.precio_unitario as precio_vigente,
       case when l.fecha_limite_venta >= current_date and l.fecha_limite_venta - current_date <= p.dias_alerta_venta
            then round(pp.precio_unitario * (1 - coalesce((select par.valor::numeric from nucleo.parametro par
                   where par.clave = 'descuento_por_vencer_pct' and (par.predio_id = l.predio_id or par.predio_id is null)
                     and par.vigente_desde <= current_date and (par.vigente_hasta is null or par.vigente_hasta >= current_date)
                   order by par.predio_id nulls last, par.vigente_desde desc limit 1), 0) / 100), 0) end as precio_liquidacion
from inventario.lote_inventario l
join inventario.producto p on p.id = l.producto_id and p.perecedero
left join comercial.lista_precios lp on lp.predio_id = l.predio_id and lp.codigo = 'PUBLICO'
left join comercial.precio_producto pp on pp.producto_id = p.id and pp.lista_precios_id = lp.id and pp.vigente_hasta is null
where l.estado = 'disponible' and l.cantidad_disponible > 0;
comment on view inventario.v_alertas_vencimiento is 'Lotes perecederos con días para su fecha límite de venta, semáforo, acción sugerida y precio de liquidación; la consultan el panel y el vendedor virtual';

-- Catálogo para los agentes: solo lo que se puede vender hoy (sin costos)
create view comercial.v_catalogo_disponible with (security_invoker = true) as
select p.predio_id, p.id as producto_id, p.sku, p.nombre, p.descripcion, u.codigo as unidad, lp.codigo as lista, pp.precio_unitario,
       coalesce(sum(l.cantidad_disponible) filter (where inventario.puede_venderse(l)), 0) as cantidad_disponible,
       min(l.fecha_limite_venta) filter (where inventario.puede_venderse(l)) as proxima_fecha_limite
from inventario.producto p
join inventario.unidad_medida u on u.id = p.unidad_id
join comercial.precio_producto pp on pp.producto_id = p.id and pp.vigente_hasta is null
join comercial.lista_precios lp on lp.id = pp.lista_precios_id
left join inventario.lote_inventario l on l.producto_id = p.id
where p.se_vende and p.activo
group by p.predio_id, p.id, p.sku, p.nombre, p.descripcion, u.codigo, lp.codigo, pp.precio_unitario;

-- ============================================================================
-- 3. Precios
-- ============================================================================
create unique index ux_precio_vigente on comercial.precio_producto (predio_id, producto_id, lista_precios_id) where vigente_hasta is null;

create or replace function comercial.aplicar_propuesta_precio(p_propuesta bigint) returns bigint language plpgsql as $$
declare v record; v_nuevo bigint;
begin
  select * into v from comercial.propuesta_precio where id = p_propuesta and estado = 'aprobada' for update;
  if not found then raise exception 'La propuesta % no existe o no está aprobada', p_propuesta; end if;
  update comercial.precio_producto set vigente_hasta = now()
   where producto_id = v.producto_id and lista_precios_id = v.lista_precios_id and vigente_hasta is null;
  insert into comercial.precio_producto (predio_id, lista_precios_id, producto_id, precio_unitario, vigente_desde, propuesta_precio_id, aprobado_por)
  values (v.predio_id, v.lista_precios_id, v.producto_id, v.precio_propuesto, now(), v.id, coalesce(v.revisado_por, nucleo.usuario_actual()))
  returning id into v_nuevo;
  update comercial.propuesta_precio set estado = 'aplicada', aplicada_en = now() where id = v.id;
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (v.predio_id, 'precio.aplicado', 'comercial.precio_producto', v_nuevo, jsonb_build_object('producto_id', v.producto_id, 'precio', v.precio_propuesto));
  return v_nuevo;
end $$;
comment on function comercial.aplicar_propuesta_precio(bigint) is 'Aplica una propuesta aprobada: cierra el precio vigente y crea el nuevo. Lo confirmado, reservado o facturado conserva su precio congelado en pedido_detalle';

-- ============================================================================
-- 4. Contabilidad: cuadre, periodos e inmutabilidad
-- ============================================================================
create or replace function finanzas.periodo_abierto(p_predio bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from finanzas.periodo_contable where predio_id = p_predio and anio = extract(year from p_fecha)
                 and mes = extract(month from p_fecha) and estado = 'abierto') $$;

create or replace function finanzas.proteger_comprobante() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then
    if old.estado <> 'borrador' then raise exception 'El comprobante % no se puede borrar; anúlelo', old.numero; end if;
    return old;
  end if;
  if tg_op = 'UPDATE' and old.estado = 'anulado' then raise exception 'El comprobante % está anulado', old.numero; end if;
  if tg_op = 'UPDATE' and old.estado = 'contabilizado' then
    if new.estado <> 'anulado' or new.motivo_anulacion is null then
      raise exception 'El comprobante % está contabilizado: solo se puede anular indicando el motivo', old.numero;
    end if;
    if (to_jsonb(new) - array['estado', 'motivo_anulacion', 'actualizado_en']) <> (to_jsonb(old) - array['estado', 'motivo_anulacion', 'actualizado_en']) then
      raise exception 'Solo se pueden cambiar el estado y el motivo de anulación de un comprobante contabilizado';
    end if;
  end if;
  if new.estado in ('contabilizado', 'anulado') and not finanzas.periodo_abierto(new.predio_id, new.fecha) then
    raise exception 'El periodo %-% está cerrado o no existe', extract(year from new.fecha), extract(month from new.fecha);
  end if;
  if new.estado = 'contabilizado' and (tg_op = 'INSERT' or old.estado = 'borrador') then
    new.contabilizado_en := now(); new.aprobado_por := coalesce(new.aprobado_por, nucleo.usuario_actual());
  end if;
  return new;
end $$;
create trigger tg_comprobante_proteger before insert or update or delete on finanzas.comprobante for each row execute function finanzas.proteger_comprobante();

-- Débitos = créditos: se revisa al confirmar la transacción (diferido), así se pueden insertar todas las líneas primero
create or replace function finanzas.validar_cuadre() returns trigger language plpgsql as $$
declare v_deb numeric; v_cred numeric; v_n integer;
begin
  if new.estado <> 'contabilizado' then return null; end if;
  select coalesce(sum(debito), 0), coalesce(sum(credito), 0), count(*) into v_deb, v_cred, v_n
  from finanzas.movimiento_contable where comprobante_id = new.id;
  if v_n < 2 or v_deb <> v_cred or v_deb = 0 then
    raise exception 'Comprobante % descuadrado: débitos %, créditos %, líneas %', new.numero, v_deb, v_cred, v_n;
  end if;
  return null;
end $$;
create constraint trigger tg_comprobante_cuadre after insert or update on finanzas.comprobante
  deferrable initially deferred for each row execute function finanzas.validar_cuadre();

create or replace function finanzas.proteger_movimiento() returns trigger language plpgsql as $$
declare v_estado text;
begin
  select estado into v_estado from finanzas.comprobante where id = coalesce(new.comprobante_id, old.comprobante_id);
  if v_estado <> 'borrador' then
    raise exception 'El comprobante está %: sus movimientos no se pueden cambiar (use una nota contable)', v_estado;
  end if;
  return coalesce(new, old);
end $$;
create trigger tg_movimiento_contable_proteger before insert or update or delete on finanzas.movimiento_contable
  for each row execute function finanzas.proteger_movimiento();

-- ============================================================================
-- 5. Canales: ¿se puede enviar este mensaje? (regla fija que consulta el conector antes de cada envío)
-- ============================================================================
create or replace function redes.verificar_envio(p_cuenta_red bigint, p_tercero bigint, p_ultimo_mensaje_cliente timestamptz,
  p_desde_anuncio boolean, p_autor text, p_plantilla bigint default null) returns text language plpgsql stable as $$
declare pc record; v_horas integer; v_dentro boolean; v_pl record; v_enviados integer;
begin
  select pol.* into pc from redes.cuenta_red cr join redes.politica_canal pol on pol.plataforma = cr.plataforma where cr.id = p_cuenta_red;
  if not found or not pc.disponible then return 'bloqueado: canal no disponible'; end if;
  v_horas := pc.ventana_horas;
  if p_desde_anuncio and pc.ventana_anuncio_horas is not null then v_horas := greatest(v_horas, pc.ventana_anuncio_horas); end if;
  if p_autor = 'humano' and pc.ventana_agente_humano_horas is not null then v_horas := greatest(v_horas, pc.ventana_agente_humano_horas); end if;
  v_dentro := v_horas is null or (p_ultimo_mensaje_cliente is not null and now() <= p_ultimo_mensaje_cliente + make_interval(hours => v_horas));
  if p_plantilla is not null then
    select * into v_pl from redes.plantilla_mensaje where id = p_plantilla and cuenta_red_id = p_cuenta_red;
    if not found or v_pl.estado_meta <> 'aprobada' then return 'bloqueado: plantilla no aprobada por el canal'; end if;
    if not exists (select 1 from terceros.consentimiento_datos c where c.tercero_id = p_tercero and c.finalidad = v_pl.finalidad_requerida
                   and c.otorgado and c.revocado_en is null) then
      return 'bloqueado: el cliente no ha autorizado ' || v_pl.finalidad_requerida;
    end if;
    return 'permitido: plantilla';
  end if;
  if not v_dentro then
    return case when pc.requiere_plantilla_fuera_ventana then 'bloqueado: fuera de la ventana; solo con plantilla aprobada'
                else 'bloqueado: fuera de la ventana; el canal no permite escribir hasta que el cliente vuelva a escribir' end;
  end if;
  if pc.max_mensajes_por_ventana is not null then
    select count(*) into v_enviados from redes.mensaje_saliente
    where cuenta_red_id = p_cuenta_red and tercero_id = p_tercero and enviado_en >= p_ultimo_mensaje_cliente and estado_entrega <> 'bloqueado_por_regla';
    if v_enviados >= pc.max_mensajes_por_ventana then return 'bloqueado: se alcanzó el tope de mensajes de la ventana'; end if;
  end if;
  return 'permitido: servicio';
end $$;
comment on function redes.verificar_envio(bigint, bigint, timestamptz, boolean, text, bigint) is 'Aplica las reglas del canal (ventana, extensión para agente humano, plantillas, consentimiento, tope de mensajes) antes de enviar';

-- ============================================================================
-- 7. Funciones por finca (feature flags): lo que espera equipo o decisión queda construido y apagado
-- ============================================================================
create or replace function nucleo.funcion_activa(p_codigo text) returns boolean language sql stable as $$
  select coalesce((select activa from nucleo.funcionalidad where codigo = p_codigo and predio_id = nucleo.predio_actual()), false) $$;
create or replace function nucleo.exigir_funcion(p_codigo text) returns void language plpgsql stable as $$
begin
  if not nucleo.funcion_activa(p_codigo) then raise exception 'La función % no está activa en esta finca', p_codigo; end if;
end $$;
create or replace function nucleo.registrar_activacion() returns trigger language plpgsql as $$
begin
  if new.activa and (tg_op = 'INSERT' or not old.activa) then
    new.activada_en := now(); new.activada_por := coalesce(new.activada_por, nucleo.usuario_actual());
  end if;
  return new;
end $$;
create trigger tg_funcionalidad_activacion before insert or update on nucleo.funcionalidad for each row execute function nucleo.registrar_activacion();

create or replace function nucleo.mantener_particiones(p_meses integer default 3) returns integer language plpgsql as $$
declare m integer;
begin
  for m in 0 .. p_meses loop
    perform nucleo.crear_particion_mensual('nucleo.auditoria', (current_date + make_interval(months => m))::date);
    perform nucleo.crear_particion_mensual('iot.lectura', (current_date + make_interval(months => m))::date);
  end loop;
  return p_meses + 1;
end $$;

-- ============================================================================
-- 8. Trazabilidad: cadena de huellas, bloqueos, cadena de frío y retiro de lotes
-- ============================================================================
create or replace function comercial.registrar_huella(p_predio bigint, p_lote bigint, p_hecho text, p_contenido jsonb) returns char(64)
language plpgsql as $$
declare v_ant char(64); v_hash char(64);
begin
  perform pg_advisory_xact_lock(hashtext('huella_trazabilidad'), p_predio::integer);
  select hash into v_ant from comercial.huella_trazabilidad where predio_id = p_predio order by id desc limit 1;
  v_hash := encode(sha256(convert_to(coalesce(v_ant, '') || p_contenido::text, 'UTF8')), 'hex');
  insert into comercial.huella_trazabilidad (predio_id, lote_inventario_id, hecho, contenido, hash_anterior, hash)
  values (p_predio, p_lote, p_hecho, p_contenido, v_ant, v_hash);
  return v_hash;
end $$;
comment on function comercial.registrar_huella(bigint, bigint, text, jsonb) is 'Agrega un eslabón a la cadena SHA-256 de la finca; lista para anclarse en una red externa con el adaptador RegistroExterno';

create or replace function comercial.verificar_cadena_huellas()
returns table (huella_id bigint, hecho text, valida boolean) language sql stable as $$
  select id, hecho,
         hash = encode(sha256(convert_to(coalesce(lag(hash) over w, '') || contenido::text, 'UTF8')), 'hex')
         and hash_anterior is not distinct from lag(hash) over w
  from comercial.huella_trazabilidad window w as (partition by predio_id order by id) order by id $$;

create or replace function comercial.proteger_huella() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' or (to_jsonb(new) - array['anclaje_red', 'anclaje_transaccion', 'anclado_en'])
                         <> (to_jsonb(old) - array['anclaje_red', 'anclaje_transaccion', 'anclado_en']) then
    raise exception 'La cadena de huellas es de solo inserción; solo se registra su anclaje';
  end if;
  return new;
end $$;
create trigger tg_huella_proteger before update or delete on comercial.huella_trazabilidad for each row execute function comercial.proteger_huella();

create or replace function inventario.huella_lote_creado() returns trigger language plpgsql as $$
begin
  perform comercial.registrar_huella(new.predio_id, new.id, 'lote_creado', jsonb_build_object('codigo_lote', new.codigo_lote,
    'producto_id', new.producto_id, 'origen', new.origen, 'fecha_produccion', new.fecha_produccion, 'fecha_vencimiento', new.fecha_vencimiento,
    'cantidad', new.cantidad_inicial));
  return null;
end $$;
create trigger tg_lote_huella after insert on inventario.lote_inventario for each row execute function inventario.huella_lote_creado();

create or replace function comercial.huella_despacho() returns trigger language plpgsql as $$
begin
  if new.estado = 'despachada' and old.estado <> 'despachada' then
    perform comercial.registrar_huella(new.predio_id, new.lote_inventario_id, 'despachado', jsonb_build_object('pedido_detalle_id', new.pedido_detalle_id,
      'cantidad', new.cantidad, 'cliente_id', (select p.cliente_id from comercial.pedido_detalle pd join comercial.pedido p on p.id = pd.pedido_id
                                              where pd.id = new.pedido_detalle_id)));
  end if;
  return null;
end $$;
create trigger tg_reserva_huella after update on comercial.reserva_lote for each row execute function comercial.huella_despacho();

-- 8.1 Bloqueo de lotes: lo pone una regla o una persona; solo una persona lo libera o lo descarta
create or replace function inventario.aplicar_bloqueo() returns trigger language plpgsql as $$
declare v_lote record;
begin
  select * into v_lote from inventario.lote_inventario where id = new.lote_inventario_id for update;
  if tg_op = 'INSERT' then
    if new.decision <> 'pendiente' then raise exception 'Un bloqueo nace pendiente'; end if;
    update inventario.lote_inventario set estado = 'bloqueado' where id = new.lote_inventario_id and estado in ('disponible', 'agotado');
    insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
    values (new.predio_id, 'lote.bloqueado', 'inventario.lote_inventario', new.lote_inventario_id, jsonb_build_object('motivo', new.motivo, 'codigo_lote', v_lote.codigo_lote));
    perform comercial.registrar_huella(new.predio_id, new.lote_inventario_id, 'bloqueado', jsonb_build_object('motivo', new.motivo, 'origen', new.origen_tabla));
    return new;
  end if;
  if old.decision <> 'pendiente' then raise exception 'El bloqueo % ya fue decidido', old.id; end if;
  if new.decision = 'pendiente' then return new; end if;
  if nucleo.agente_actual() is not null then raise exception 'Solo una persona decide sobre un lote bloqueado'; end if;
  new.decidido_por := coalesce(new.decidido_por, nucleo.usuario_actual());
  if new.decidido_por is null then raise exception 'La decisión sobre el lote % debe tener responsable', v_lote.codigo_lote; end if;
  new.decidido_en := now();
  if new.decision = 'liberado' then
    if not exists (select 1 from inventario.bloqueo_lote where lote_inventario_id = new.lote_inventario_id and decision = 'pendiente' and id <> new.id) then
      update inventario.lote_inventario set estado = case when fecha_vencimiento < current_date then 'vencido'
                                                         when cantidad_disponible + cantidad_reservada = 0 then 'agotado' else 'disponible' end
      where id = new.lote_inventario_id and estado = 'bloqueado';
    end if;
  else
    if v_lote.cantidad_disponible > 0 then
      insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, causa_merma, costo_unitario, documento_tipo, documento_id, usuario_id)
      values (new.predio_id, new.lote_inventario_id, 'merma', v_lote.cantidad_disponible, 'calidad', v_lote.costo_unitario, 'bloqueo_lote', new.id, new.decidido_por);
    end if;
  end if;
  perform comercial.registrar_huella(new.predio_id, new.lote_inventario_id, new.decision, jsonb_build_object('bloqueo_id', new.id, 'decidido_por', new.decidido_por));
  return new;
end $$;
create trigger tg_bloqueo_aplicar before insert or update on inventario.bloqueo_lote for each row execute function inventario.aplicar_bloqueo();

-- 8.2 Cadena de frío: una excursión que supera la tolerancia bloquea los lotes perecederos de la nevera o del vehículo en ruta
create or replace function inventario.evaluar_excursion() returns trigger language plpgsql as $$
declare v_tol integer; r record; n integer := 0;
begin
  if new.bodega_id is not null then select minutos_tolerancia into v_tol from inventario.bodega where id = new.bodega_id;
  else select minutos_tolerancia into v_tol from inventario.vehiculo where id = new.vehiculo_id; end if;
  if new.minutos_fuera <= v_tol or new.lotes_bloqueados > 0 then return new; end if;
  for r in select l.id from inventario.lote_inventario l join inventario.producto p on p.id = l.producto_id
           where p.perecedero and l.estado in ('disponible', 'agotado') and l.cantidad_disponible + l.cantidad_reservada > 0
             and (l.bodega_id = new.bodega_id
                  or l.id in (select rl.lote_inventario_id from comercial.entrega e
                              join comercial.pedido_detalle pd on pd.pedido_id = e.pedido_id
                              join comercial.reserva_lote rl on rl.pedido_detalle_id = pd.id
                              where e.vehiculo_id = new.vehiculo_id and e.estado = 'en_ruta')) loop
    insert into inventario.bloqueo_lote (predio_id, lote_inventario_id, motivo, origen_tabla, origen_id)
    values (new.predio_id, r.id, 'cadena_frio', 'excursion_temperatura', new.id);
    n := n + 1;
  end loop;
  new.lotes_bloqueados := n;
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (new.predio_id, 'temperatura.fuera_de_rango', 'inventario.excursion_temperatura', new.id,
          jsonb_build_object('minutos_fuera', new.minutos_fuera, 'temperatura', new.temperatura_extrema_c, 'lotes_bloqueados', n));
  return new;
end $$;
create trigger tg_excursion_evaluar before insert or update on inventario.excursion_temperatura for each row execute function inventario.evaluar_excursion();

-- 8.3 Trazabilidad y retiro (recall)
create view comercial.v_trazabilidad_lote with (security_invoker = true) as
select l.predio_id, l.id as lote_inventario_id, l.codigo_lote, p.nombre as producto, l.origen, l.origen_tabla, l.origen_id,
       l.fecha_produccion, l.fecha_vencimiento, l.estado as estado_lote, ped.id as pedido_id, ped.numero as pedido, ped.estado as estado_pedido,
       c.id as cliente_id, coalesce(t.razon_social, concat_ws(' ', t.nombres, t.apellidos)) as cliente, t.whatsapp, rl.cantidad, rl.estado as estado_reserva
from inventario.lote_inventario l
join inventario.producto p on p.id = l.producto_id
left join comercial.reserva_lote rl on rl.lote_inventario_id = l.id and rl.estado <> 'liberada'
left join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id
left join comercial.pedido ped on ped.id = pd.pedido_id
left join terceros.cliente c on c.id = ped.cliente_id
left join terceros.tercero t on t.id = c.tercero_id;
comment on view comercial.v_trazabilidad_lote is 'De dónde salió un lote y a qué clientes y pedidos llegó';

create or replace function comercial.abrir_retiro(p_lote bigint, p_motivo text) returns bigint language plpgsql as $$
declare v_id bigint; v_predio bigint;
begin
  select predio_id into v_predio from inventario.lote_inventario where id = p_lote;
  if not found then raise exception 'El lote % no existe', p_lote; end if;
  insert into comercial.retiro_lote (predio_id, lote_inventario_id, motivo, abierto_por) values (v_predio, p_lote, p_motivo, nucleo.usuario_actual())
  returning id into v_id;
  insert into inventario.bloqueo_lote (predio_id, lote_inventario_id, motivo, origen_tabla, origen_id) values (v_predio, p_lote, 'retiro', 'retiro_lote', v_id);
  insert into comercial.retiro_aviso (predio_id, retiro_lote_id, cliente_id, pedido_id, cantidad)
  select v_predio, v_id, ped.cliente_id, ped.id, sum(rl.cantidad) from comercial.reserva_lote rl
  join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id join comercial.pedido ped on ped.id = pd.pedido_id
  where rl.lote_inventario_id = p_lote and rl.estado = 'despachada' group by ped.cliente_id, ped.id;
  perform comercial.registrar_huella(v_predio, p_lote, 'retirado', jsonb_build_object('retiro_id', v_id, 'motivo', p_motivo));
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (v_predio, 'lote.retirado', 'comercial.retiro_lote', v_id, jsonb_build_object('lote_id', p_lote));
  return v_id;
end $$;
comment on function comercial.abrir_retiro(bigint, text) is 'Retiro de un lote: lo bloquea y crea un aviso por cada cliente que lo recibió';

-- ============================================================================
-- 9. Producción: clasificación del huevo por peso
-- ============================================================================
create or replace function produccion.clasificar_por_peso(p_peso_g numeric, p_fecha date default current_date) returns varchar language sql stable as $$
  select c.codigo from produccion.categoria_huevo c
  where c.vigente_desde = (select max(vigente_desde) from produccion.categoria_huevo where vigente_desde <= p_fecha)
    and p_peso_g >= c.peso_min_g and (c.peso_max_g is null or p_peso_g < c.peso_max_g)
  order by c.peso_min_g desc limit 1 $$;

create or replace function produccion.validar_clasificacion() returns trigger language plpgsql as $$
declare v_buenos integer; v_suma integer;
begin
  if new.metodo = 'vision' then perform nucleo.exigir_funcion('vision_artificial'); end if;
  select huevos_recogidos - huevos_rotos into v_buenos from produccion.registro_postura where id = new.registro_postura_id;
  select coalesce(sum(cantidad), 0) into v_suma from produccion.clasificacion_postura where registro_postura_id = new.registro_postura_id;
  if v_suma > v_buenos then raise exception 'La clasificación suma % huevos y solo hay % buenos', v_suma, v_buenos; end if;
  return null;
end $$;
create trigger tg_clasificacion_validar after insert or update on produccion.clasificacion_postura for each row execute function produccion.validar_clasificacion();

-- ============================================================================
-- 10. Cartera, pagos, permuta y pedidos recurrentes (cartera y permuta se encienden con su función)
-- ============================================================================
create or replace function comercial.preparar_factura() returns trigger language plpgsql as $$
declare v_plazo smallint;
begin
  select dias_plazo into v_plazo from terceros.cliente where id = new.cliente_id;
  new.saldo := new.total;
  new.fecha_vencimiento := coalesce(new.fecha_vencimiento, new.fecha_emision::date + case when new.forma_pago = 'credito' then coalesce(v_plazo, 0) else 0 end);
  return new;
end $$;
create trigger tg_factura_preparar before insert on comercial.factura for each row execute function comercial.preparar_factura();

create or replace function comercial.aplicar_pago() returns trigger language plpgsql as $$
declare v_delta numeric := 0;
begin
  if new.estado = 'confirmado' and nucleo.agente_actual() is not null then raise exception 'Un agente no puede confirmar pagos'; end if;
  if new.medio = 'pasarela' and new.proveedor_pasarela is null then raise exception 'Indique la pasarela de pago'; end if;
  if new.factura_id is null then return new; end if;
  if new.estado = 'confirmado' and (tg_op = 'INSERT' or old.estado <> 'confirmado') then v_delta := -new.valor;
  elsif tg_op = 'UPDATE' and old.estado = 'confirmado' and new.estado <> 'confirmado' then v_delta := old.valor; end if;
  if v_delta <> 0 then
    update comercial.factura set saldo = saldo + v_delta where id = new.factura_id;
    if (select saldo from comercial.factura where id = new.factura_id) < 0 then raise exception 'El pago supera el saldo de la factura'; end if;
  end if;
  return new;
end $$;
create trigger tg_pago_aplicar before insert or update on comercial.pago for each row execute function comercial.aplicar_pago();

create view comercial.v_cartera with (security_invoker = true) as
select f.predio_id, f.cliente_id, coalesce(t.razon_social, concat_ws(' ', t.nombres, t.apellidos)) as cliente, f.id as factura_id,
       f.prefijo || '-' || f.numero as factura, f.fecha_emision::date as fecha_emision, f.fecha_vencimiento, f.total, f.saldo,
       greatest(current_date - f.fecha_vencimiento, 0) as dias_mora,
       case when current_date <= f.fecha_vencimiento then 'al_dia' when current_date - f.fecha_vencimiento <= 30 then '1_30'
            when current_date - f.fecha_vencimiento <= 60 then '31_60' when current_date - f.fecha_vencimiento <= 90 then '61_90' else 'mas_90' end as edad
from comercial.factura f join terceros.cliente c on c.id = f.cliente_id join terceros.tercero t on t.id = c.tercero_id
where f.saldo > 0 and f.estado_dian <> 'rechazada';
comment on view comercial.v_cartera is 'Saldo por factura y edad de la deuda; base de la mora y del cupo';

create or replace function comercial.actualizar_mora() returns integer language plpgsql as $$
declare n integer;
begin
  update terceros.cliente c set bloqueado_por_mora = exists (select 1 from comercial.factura f where f.cliente_id = c.id and f.saldo > 0
                                                             and f.fecha_vencimiento < current_date)
  where bloqueado_por_mora is distinct from exists (select 1 from comercial.factura f where f.cliente_id = c.id and f.saldo > 0
                                                    and f.fecha_vencimiento < current_date);
  get diagnostics n = row_count;
  return n;
end $$;

create or replace function comercial.aplicar_permuta() returns trigger language plpgsql as $$
declare v_fac record; v_ds record; v_usado numeric;
begin
  perform nucleo.exigir_funcion('permuta');
  select * into v_fac from comercial.factura where id = new.factura_id for update;
  select * into v_ds from compras.documento_soporte where id = new.documento_soporte_id for update;
  select coalesce(sum(valor_compensado), 0) into v_usado from comercial.permuta where documento_soporte_id = new.documento_soporte_id;
  if new.valor_compensado > v_fac.saldo or v_usado + new.valor_compensado > v_ds.total then
    raise exception 'La permuta (%) supera el saldo de la factura (%) o lo disponible del documento soporte (%)', new.valor_compensado, v_fac.saldo, v_ds.total - v_usado;
  end if;
  new.registrado_por := coalesce(new.registrado_por, nucleo.usuario_actual());
  insert into comercial.pago (predio_id, factura_id, fecha, valor, medio, referencia, estado, confirmado_por)
  values (new.predio_id, new.factura_id, now(), new.valor_compensado, 'compensacion_permuta', 'DS ' || v_ds.prefijo || '-' || v_ds.numero, 'confirmado', new.registrado_por);
  return new;
end $$;
create trigger tg_permuta_aplicar before insert on comercial.permuta for each row execute function comercial.aplicar_permuta();
create trigger tg_permuta_inmutable before update or delete on comercial.permuta for each row execute function nucleo.impedir_cambio();

create or replace function comercial.generar_pedidos_recurrentes(p_fecha date default current_date) returns integer language plpgsql as $$
declare r record; d record; v_ped bigint; v_lista bigint; v_precio record; n integer := 0;
begin
  if not nucleo.funcion_activa('pedidos_recurrentes') then return 0; end if;
  for r in select pr.*, c.lista_precios_id from comercial.pedido_recurrente pr join terceros.cliente c on c.id = pr.cliente_id
           where pr.activo and pr.proxima_fecha <= p_fecha for update of pr loop
    v_lista := coalesce(r.lista_precios_id, (select id from comercial.lista_precios where codigo = 'PUBLICO'));
    insert into comercial.pedido (predio_id, numero, cliente_id, canal, forma_pago, pedido_recurrente_id, fecha_entrega_programada)
    values (r.predio_id, 'REC-' || r.id || '-' || to_char(r.proxima_fecha, 'YYYYMMDD'), r.cliente_id, r.canal, r.forma_pago, r.id, r.proxima_fecha)
    returning id into v_ped;
    for d in select rd.*, p.tarifa_iva from comercial.pedido_recurrente_detalle rd join inventario.producto p on p.id = rd.producto_id
             where rd.pedido_recurrente_id = r.id loop
      select * into v_precio from comercial.precio_producto where producto_id = d.producto_id and lista_precios_id = v_lista and vigente_hasta is null;
      if not found then raise exception 'El producto % no tiene precio vigente para el pedido recurrente %', d.producto_id, r.id; end if;
      insert into comercial.pedido_detalle (predio_id, pedido_id, producto_id, cantidad, precio_producto_id, precio_unitario, tarifa_iva, total_linea)
      values (r.predio_id, v_ped, d.producto_id, d.cantidad, v_precio.id, v_precio.precio_unitario, d.tarifa_iva, d.cantidad * v_precio.precio_unitario);
    end loop;
    update comercial.pedido_recurrente set proxima_fecha = (proxima_fecha + case frecuencia when 'semanal' then interval '7 days'
                                                            when 'quincenal' then interval '15 days' else interval '1 month' end)::date
    where id = r.id;
    n := n + 1;
  end loop;
  return n;
end $$;
comment on function comercial.generar_pedidos_recurrentes(date) is 'Tarea diaria: crea en borrador los pedidos recurrentes que tocan; un vendedor los confirma';

-- ============================================================================
-- 11. Audiovisual: consentimiento de imagen, aprobación humana y retención de clips
-- ============================================================================
create or replace function redes.validar_pieza() returns trigger language plpgsql as $$
declare v_faltan text;
begin
  if new.estado in ('aprobada', 'publicada') and (tg_op = 'INSERT' or old.estado not in ('aprobada', 'publicada')) then
    if nucleo.agente_actual() is not null then raise exception 'Solo una persona aprueba contenido para redes'; end if;
    new.aprobado_por := coalesce(new.aprobado_por, nucleo.usuario_actual());
    if new.aprobado_por is null then raise exception 'La aprobación debe tener responsable'; end if;
    if new.personas_identificables then
      if not exists (select 1 from redes.pieza_persona where pieza_audiovisual_id = new.id) then
        raise exception 'La pieza muestra personas: registre quiénes aparecen';
      end if;
      select string_agg(coalesce(t.razon_social, concat_ws(' ', t.nombres, t.apellidos)), ', ') into v_faltan
      from redes.pieza_persona pp join terceros.tercero t on t.id = pp.tercero_id
      where pp.pieza_audiovisual_id = new.id and not exists (select 1 from terceros.consentimiento_datos c where c.tercero_id = pp.tercero_id
            and c.finalidad = 'imagen_redes' and c.otorgado and c.revocado_en is null);
      if v_faltan is not null then raise exception 'Falta autorización de imagen de: %', v_faltan; end if;
    end if;
  end if;
  return new;
end $$;
create trigger tg_pieza_validar before insert or update on redes.pieza_audiovisual for each row execute function redes.validar_pieza();

create or replace function iot.preparar_clip() returns trigger language plpgsql as $$
begin
  if new.retener_hasta is null then
    new.retener_hasta := new.inicio::date + (select retencion_dias from iot.camara where id = new.camara_id);
  end if;
  return new;
end $$;
create trigger tg_clip_preparar before insert on iot.clip_video for each row execute function iot.preparar_clip();

create or replace function iot.depurar_clips() returns integer language plpgsql as $$
declare n integer;
begin
  update iot.clip_video set borrado_en = now() where borrado_en is null and not para_redes and retener_hasta < current_date;
  get diagnostics n = row_count;
  return n;
end $$;
comment on function iot.depurar_clips() is 'Tarea diaria: marca para borrar los clips vencidos; el servicio IoT borra el archivo';

create or replace function iot.validar_camara() returns trigger language plpgsql as $$
begin
  if new.tipo = 'termica' then perform nucleo.exigir_funcion('camara_termica'); end if;
  return new;
end $$;
create trigger tg_camara_validar before insert or update of tipo on iot.camara for each row execute function iot.validar_camara();

-- ============================================================================
-- 12. Seguridad perimetral: estados de la alarma, cerraduras seguras y credenciales
-- ============================================================================
create or replace function iot.cambiar_estado_alarma(p_zona bigint, p_nuevo text, p_origen text) returns void language plpgsql as $$
declare v_zona record;
begin
  select * into v_zona from iot.zona_seguridad where id = p_zona for update;
  if not found then raise exception 'La zona de seguridad % no existe', p_zona; end if;
  if (v_zona.estado_alarma, p_nuevo) not in (('desarmado', 'armado'), ('desarmado', 'noche'), ('desarmado', 'mantenimiento'),
       ('armado', 'desarmado'), ('armado', 'noche'), ('noche', 'desarmado'), ('noche', 'armado'), ('mantenimiento', 'desarmado')) then
    raise exception 'Cambio de alarma no permitido: % a %', v_zona.estado_alarma, p_nuevo;
  end if;
  perform set_config('guayacan.desde_alarma', 'si', true);
  update iot.zona_seguridad set estado_alarma = p_nuevo where id = p_zona;
  perform set_config('guayacan.desde_alarma', 'no', true);
  insert into iot.cambio_estado_alarma (predio_id, zona_seguridad_id, estado_anterior, estado_nuevo, origen, usuario_id)
  values (v_zona.predio_id, p_zona, v_zona.estado_alarma, p_nuevo, p_origen, nucleo.usuario_actual());
end $$;
comment on function iot.cambiar_estado_alarma(bigint, text, text) is 'Patrón State: solo transiciones válidas (mantenimiento solo desde desarmado), con historial';

create or replace function iot.proteger_estado_alarma() returns trigger language plpgsql as $$
begin
  if new.estado_alarma is distinct from old.estado_alarma and coalesce(current_setting('guayacan.desde_alarma', true), '') <> 'si' then
    raise exception 'El estado de la alarma solo cambia con iot.cambiar_estado_alarma';
  end if;
  return new;
end $$;
create trigger tg_zona_seguridad_estado before update on iot.zona_seguridad for each row execute function iot.proteger_estado_alarma();
create trigger tg_cambio_alarma_inmutable before update or delete on iot.cambio_estado_alarma for each row execute function nucleo.impedir_cambio();

create or replace function iot.validar_actuador() returns trigger language plpgsql as $$
begin
  if new.tipo = 'cerradura' then
    if new.zona_seguridad_id is null then raise exception 'Una cerradura debe pertenecer a una zona de seguridad'; end if;
    if new.modo_falla <> 'abre_sin_energia' and (select paso_personas from iot.zona_seguridad where id = new.zona_seguridad_id) then
      raise exception 'La cerradura % está en un paso de personas: debe abrir sin energía', new.codigo;
    end if;
  end if;
  return new;
end $$;
create trigger tg_actuador_validar before insert or update on iot.actuador for each row execute function iot.validar_actuador();

create or replace function iot.proteger_evento_seguridad() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' or (to_jsonb(new) - array['atendido_por', 'atendido_en', 'nota_atencion', 'actualizado_en'])
                         <> (to_jsonb(old) - array['atendido_por', 'atendido_en', 'nota_atencion', 'actualizado_en']) then
    raise exception 'Un evento de seguridad no se modifica; solo se registra su atención';
  end if;
  return new;
end $$;
create trigger tg_evento_seguridad_proteger before update or delete on iot.evento_seguridad for each row execute function iot.proteger_evento_seguridad();

create or replace function iot.validar_credencial() returns trigger language plpgsql as $$
begin
  if new.metodo = 'facial' and new.activa then
    perform nucleo.exigir_funcion('reconocimiento_facial');
    if not exists (select 1 from terceros.consentimiento_datos c where c.id = new.consentimiento_id and c.tercero_id = new.tercero_id
                   and c.finalidad = 'biometria_acceso' and c.otorgado and c.revocado_en is null) then
      raise exception 'El acceso facial exige autorización expresa y vigente de biometría de la misma persona; use PIN o tarjeta';
    end if;
  end if;
  return new;
end $$;
create trigger tg_credencial_validar before insert or update on iot.credencial_acceso for each row execute function iot.validar_credencial();

create or replace function terceros.revocar_biometria() returns trigger language plpgsql as $$
begin
  if new.finalidad = 'biometria_acceso' and new.revocado_en is not null and old.revocado_en is null then
    update iot.credencial_acceso set activa = false where consentimiento_id = new.id and metodo = 'facial';
  end if;
  return null;
end $$;
create trigger tg_consentimiento_biometria after update on terceros.consentimiento_datos for each row execute function terceros.revocar_biometria();

-- ============================================================================
-- 13. Indicadores ambientales (CO₂ siempre "estimado" y con su fuente)
-- ============================================================================
create view ambiental.v_indicadores with (security_invoker = true) as
select r.predio_id, date_trunc('month', r.fecha)::date as mes, r.magnitud, sum(r.cantidad) as cantidad,
       f.factor_kgco2e, round(sum(r.cantidad) * f.factor_kgco2e, 2) as kgco2e_estimado, f.fuente
from ambiental.registro_ambiental r
left join lateral (select fe.factor_kgco2e, fe.fuente from ambiental.factor_emision fe
                   where fe.magnitud = r.magnitud and fe.vigente_desde <= r.fecha order by fe.vigente_desde desc limit 1) f on true
group by r.predio_id, date_trunc('month', r.fecha), r.magnitud, f.factor_kgco2e, f.fuente;
comment on view ambiental.v_indicadores is 'Totales del mes y CO₂ equivalente estimado con el factor y la fuente a la vista';

-- ============================================================================
-- 14. Apoyos comunes v5: parámetros vigentes, permisos y "solo personas"
-- ============================================================================
create or replace function nucleo.parametro_valor(p_clave text, p_fecha date default current_date) returns numeric language sql stable as $$
  select par.valor::numeric from nucleo.parametro par
  where par.clave = p_clave and (par.predio_id = nucleo.predio_actual() or par.predio_id is null)
    and par.vigente_desde <= p_fecha and (par.vigente_hasta is null or par.vigente_hasta >= p_fecha)
  order by par.predio_id nulls last, par.vigente_desde desc limit 1 $$;
comment on function nucleo.parametro_valor(text, date) is 'Valor numérico vigente de un parámetro: primero el de la finca, si no el nacional';

create or replace function nucleo.tiene_permiso(p_usuario bigint, p_permiso text) returns boolean language sql stable as $$
  select coalesce((select es_superusuario from nucleo.usuario where id = p_usuario), false)
      or exists (select 1 from nucleo.usuario_rol ur join nucleo.rol_permiso rp on rp.rol_id = ur.rol_id
                 join nucleo.permiso pe on pe.id = rp.permiso_id where ur.usuario_id = p_usuario and pe.codigo = p_permiso) $$;

create or replace function nucleo.exigir_persona(p_accion text) returns void language plpgsql stable as $$
begin
  if nucleo.agente_actual() is not null then raise exception 'Un agente de IA no puede %: lo hace una persona', p_accion; end if;
  if nucleo.usuario_actual() is null then raise exception 'Para % se necesita un usuario identificado', p_accion; end if;
end $$;
comment on function nucleo.exigir_persona(text) is 'La IA propone y una persona decide: corta la acción si la sesión es de un agente';

create or replace function nucleo.tercero_de_usuario(p_usuario bigint) returns bigint language sql stable as $$
  select tercero_id from nucleo.usuario where id = p_usuario $$;

-- ============================================================================
-- 15. Personal: disponibilidad, habilitación, aprobación y plan de labores
-- ============================================================================
create or replace function personal.empleado_disponible(p_empleado bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from terceros.empleado e where e.id = p_empleado and e.fecha_ingreso <= p_fecha
                 and (e.fecha_retiro is null or e.fecha_retiro >= p_fecha))
     and not exists (select 1 from personal.ausencia a where a.empleado_id = p_empleado and p_fecha between a.desde and a.hasta) $$;

create or replace function formacion.esta_habilitado(p_tercero bigint, p_competencia bigint, p_fecha date default current_date)
returns boolean language sql stable as $$
  select exists (select 1 from formacion.habilitacion h where h.tercero_id = p_tercero and h.competencia_id = p_competencia
                 and h.activa and h.desde <= p_fecha and (h.hasta is null or h.hasta >= p_fecha)) $$;

create or replace function personal.validar_tarea() returns trigger language plpgsql as $$
declare v_comp bigint; v_ter bigint; v_emp record;
begin
  if tg_op = 'UPDATE' and old.estado in ('aprobada', 'cancelada') then
    raise exception 'La tarea % está %: no se edita', old.id, old.estado;
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
  if new.estado = 'terminada' and (tg_op = 'INSERT' or old.estado <> 'terminada') then new.terminada_en := coalesce(new.terminada_en, now()); end if;
  if new.estado in ('aprobada', 'devuelta') and (tg_op = 'INSERT' or old.estado <> new.estado) then
    perform nucleo.exigir_persona('aprobar o devolver tareas');
    if tg_op = 'INSERT' or old.estado <> 'terminada' then raise exception 'Solo se aprueba o devuelve una tarea terminada'; end if;
    new.aprobado_por := coalesce(new.aprobado_por, nucleo.usuario_actual());
    if not nucleo.tiene_permiso(new.aprobado_por, 'personal.aprobar_tarea')
       and not (new.area_id is not null and personal.es_responsable_area(new.aprobado_por, new.area_id, new.fecha)) then
      raise exception 'El usuario % no tiene el permiso personal.aprobar_tarea ni es responsable del área', new.aprobado_por;
    end if;
    if new.empleado_id is not null and nucleo.tercero_de_usuario(new.aprobado_por) = (select tercero_id from terceros.empleado where id = new.empleado_id) then
      raise exception 'Nadie aprueba su propia tarea';
    end if;
    if new.estado = 'devuelta' and new.comentario_revision is null then raise exception 'Para devolver una tarea hay que decir por qué'; end if;
    new.aprobado_en := now();
  end if;
  return new;
end $$;
create trigger tg_tarea_validar before insert or update on personal.tarea for each row execute function personal.validar_tarea();

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
create trigger tg_paso_tarea_validar before insert or update on personal.paso_tarea for each row execute function personal.validar_paso_tarea();
create trigger tg_tarea_no_borrar before delete on personal.tarea for each row execute function nucleo.impedir_cambio();

create or replace function personal.generar_tareas_del_dia(p_fecha date default current_date) returns integer language plpgsql as $$
declare v_n integer := 0; r record; v_tarea bigint;
begin
  for r in select * from personal.plantilla_tarea p where p.activa and (
             p.recurrencia = 'diaria'
          or (p.recurrencia = 'semanal' and extract(isodow from p_fecha)::smallint = any(p.dias_semana))
          or (p.recurrencia = 'mensual' and extract(day from p_fecha) = 1))
          and not exists (select 1 from personal.tarea t where t.plantilla_tarea_id = p.id and t.fecha = p_fecha) loop
    insert into personal.tarea (plantilla_tarea_id, titulo, proceso, fecha, hora_limite, prioridad, zona_id, origen)
    values (r.id, r.nombre, r.proceso, p_fecha, case when r.hora_limite is not null then (p_fecha + r.hora_limite)::timestamptz end,
            r.prioridad, r.zona_id, 'plan') returning id into v_tarea;
    insert into personal.paso_tarea (tarea_id, orden, descripcion)
    select v_tarea, x.ord::smallint, x.paso #>> '{}' from jsonb_array_elements(coalesce(r.pasos, '[]')) with ordinality x(paso, ord);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function personal.generar_tareas_del_dia(date) is 'Tarea diaria (Celery Beat): crea las tareas del día desde el plan de labores, sin asignar; el encargado asigna';

create or replace function personal.calcular_jornada() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and old.aprobada_en is not null then raise exception 'La jornada % ya fue aprobada: no se edita', old.id; end if;
  if new.salida is not null and new.horas is null then new.horas := round(extract(epoch from new.salida - new.entrada) / 3600.0, 2); end if;
  if new.aprobada_por is not null and new.aprobada_en is null then
    perform nucleo.exigir_persona('aprobar jornadas'); new.aprobada_en := now();
  end if;
  return new;
end $$;
create trigger tg_jornada_calcular before insert or update on personal.jornada for each row execute function personal.calcular_jornada();

create or replace view personal.v_productividad as
select t.empleado_id, t.plantilla_tarea_id, date_trunc('month', t.fecha)::date as mes, count(*) as tareas_aprobadas,
       sum(t.cantidad) as cantidad, round(sum(t.cantidad) / nullif(sum(extract(epoch from t.terminada_en - t.iniciada_en)) / 3600, 0), 2) as cantidad_por_hora,
       round(avg(extract(epoch from t.terminada_en - t.iniciada_en) / 60) / nullif(max(p.duracion_estimada_min), 0) * 100, 1) as pct_tiempo_vs_estandar
from personal.tarea t left join personal.plantilla_tarea p on p.id = t.plantilla_tarea_id
where t.estado = 'aprobada' group by 1, 2, 3;

-- ============================================================================
-- 16. Nómina: prenómina, liquidación, periodo inmutable y pagos con doble aprobación
-- ============================================================================
create or replace function nomina.proteger_periodo() returns trigger language plpgsql as $$
declare v_estado_comp text;
begin
  if tg_op = 'DELETE' then
    if old.estado <> 'abierto' then raise exception 'El periodo % no se puede borrar', old.codigo; end if;
    return old;
  end if;
  if old.estado in ('cerrado', 'anulado') then
    raise exception 'El periodo % está %: no se edita; las correcciones van como nota de ajuste', old.codigo, old.estado;
  end if;
  if new.estado = 'cerrado' then
    perform nucleo.exigir_persona('cerrar la nómina');
    new.cerrado_por := coalesce(new.cerrado_por, nucleo.usuario_actual());
    if new.aprobado_por is null or new.aprobado_por = new.cerrado_por then
      raise exception 'El cierre de nómina necesita dos personas distintas (cierra % y aprueba %)', new.cerrado_por, new.aprobado_por;
    end if;
    if not exists (select 1 from nomina.liquidacion where periodo_id = new.id) then raise exception 'El periodo % no tiene liquidaciones', new.codigo; end if;
    select estado into v_estado_comp from finanzas.comprobante where id = new.comprobante_id;
    if v_estado_comp is distinct from 'contabilizado' then
      raise exception 'El cierre necesita su comprobante de causación contabilizado (cuadrado)';
    end if;
    update nomina.liquidacion set estado = 'aprobada' where periodo_id = new.id and estado = 'borrador';
    new.cerrado_en := now();
  end if;
  return new;
end $$;
create trigger tg_periodo_nomina_proteger before update or delete on nomina.periodo_nomina for each row execute function nomina.proteger_periodo();

create or replace function nomina.proteger_detalle_periodo() returns trigger language plpgsql as $$
declare v_periodo bigint; v_estado text; v_reg record;
begin
  v_reg := coalesce(new, old);
  if tg_table_name = 'liquidacion_detalle' then
    select l.periodo_id into v_periodo from nomina.liquidacion l where l.id = v_reg.liquidacion_id;
  else
    v_periodo := v_reg.periodo_id;
  end if;
  select estado into v_estado from nomina.periodo_nomina where id = v_periodo;
  if v_estado in ('cerrado', 'anulado') then
    if tg_table_name = 'liquidacion' and tg_op = 'UPDATE'
       and (to_jsonb(new) - array['estado', 'actualizado_en']) = (to_jsonb(old) - array['estado', 'actualizado_en']) then
      return new;  -- solo el paso a "pagada"
    end if;
    raise exception 'El periodo de nómina está %: no se cambian sus datos', v_estado;
  end if;
  return coalesce(new, old);
end $$;
create trigger tg_novedad_periodo before insert or update or delete on nomina.novedad for each row execute function nomina.proteger_detalle_periodo();
create trigger tg_liquidacion_periodo before insert or update or delete on nomina.liquidacion for each row execute function nomina.proteger_detalle_periodo();
create trigger tg_liquidacion_detalle_periodo before insert or update or delete on nomina.liquidacion_detalle for each row execute function nomina.proteger_detalle_periodo();
create trigger tg_provision_periodo before insert or update or delete on nomina.provision_prestacion for each row execute function nomina.proteger_detalle_periodo();

create or replace function nomina.validar_novedad() returns trigger language plpgsql as $$
declare v_base text; v_pago text; v_estado text;
begin
  select base into v_base from nomina.concepto_nomina where id = new.concepto_id;
  if v_base = 'salario' and new.origen in ('tarea', 'jornada') then
    raise exception 'El salario de un contrato no depende de que se aprueben tareas: las tareas solo pagan jornales y destajo';
  end if;
  if new.origen = 'tarea' then
    select t.estado, p.forma_pago into v_estado, v_pago from personal.tarea t left join personal.plantilla_tarea p on p.id = t.plantilla_tarea_id where t.id = new.tarea_id;
    if v_estado is distinct from 'aprobada' then raise exception 'Solo una tarea aprobada genera pago'; end if;
    if coalesce(v_pago, 'ninguna') = 'ninguna' then raise exception 'La tarea % no paga jornal ni destajo', new.tarea_id; end if;
  end if;
  if new.origen = 'jornada' and not exists (select 1 from personal.jornada where id = new.jornada_id and aprobada_en is not null) then
    raise exception 'Solo una jornada aprobada genera pago';
  end if;
  new.valor := coalesce(new.valor, round(new.cantidad * new.valor_unitario, 0));
  return new;
end $$;
create trigger tg_novedad_validar before insert or update on nomina.novedad for each row execute function nomina.validar_novedad();

create or replace function nomina.concepto(p_codigo text) returns bigint language sql stable as $$
  select id from nomina.concepto_nomina where codigo = p_codigo and activo $$;

create or replace function nomina.preparar_prenomina(p_periodo bigint) returns integer language plpgsql as $$
declare v_p nomina.periodo_nomina; v_n integer := 0; v_k integer; v_smmlv numeric; v_aux numeric;
begin
  select * into v_p from nomina.periodo_nomina where id = p_periodo for update;
  if v_p.estado not in ('abierto', 'prenomina') then raise exception 'El periodo % está %', v_p.codigo, v_p.estado; end if;
  v_smmlv := nucleo.parametro_valor('salario_minimo', v_p.hasta);
  v_aux := nucleo.parametro_valor('auxilio_transporte', v_p.hasta);
  -- a) Salario fijo de los contratos (no depende de tareas); días calendario comerciales (máximo 30)
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, valor, origen)
  select p_periodo, e.id, nomina.concepto('SALARIO'), d.dias, round(e.salario_base / 30, 2), round(e.salario_base / 30 * d.dias, 0), 'contrato'
  from terceros.empleado e
  cross join lateral (select least(30, (least(v_p.hasta, coalesce(e.fecha_retiro, v_p.hasta)) - greatest(v_p.desde, e.fecha_ingreso) + 1))::numeric as dias) d
  where e.forma_pago in ('salario', 'mixto') and e.salario_base > 0 and d.dias > 0
    and not exists (select 1 from nomina.novedad n where n.periodo_id = p_periodo and n.empleado_id = e.id and n.origen = 'contrato');
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  -- Auxilio de transporte a quien gana hasta dos salarios mínimos
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, valor, origen, observacion)
  select p_periodo, n.empleado_id, nomina.concepto('AUX_TRANSPORTE'), n.cantidad, round(v_aux / 30, 2), round(v_aux / 30 * n.cantidad, 0), 'contrato', 'Auxilio de transporte'
  from nomina.novedad n join terceros.empleado e on e.id = n.empleado_id
  where n.periodo_id = p_periodo and n.concepto_id = nomina.concepto('SALARIO') and e.salario_base <= 2 * v_smmlv
    and not exists (select 1 from nomina.novedad x where x.periodo_id = p_periodo and x.empleado_id = n.empleado_id and x.concepto_id = nomina.concepto('AUX_TRANSPORTE'));
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  -- b) Jornales y destajo de tareas aprobadas del periodo
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, origen, tarea_id)
  select p_periodo, t.empleado_id, nomina.concepto(case p.forma_pago when 'jornal' then 'JORNAL' else 'DESTAJO' end),
         case p.forma_pago when 'jornal' then 1 else coalesce(t.cantidad, 0) end, p.valor_unitario, 'tarea', t.id
  from personal.tarea t join personal.plantilla_tarea p on p.id = t.plantilla_tarea_id
  where t.estado = 'aprobada' and t.empleado_id is not null and t.fecha between v_p.desde and v_p.hasta and p.forma_pago in ('jornal', 'destajo')
  on conflict do nothing;
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  -- c) Jornadas aprobadas de jornaleros sin tarea
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, origen, jornada_id)
  select p_periodo, j.empleado_id, nomina.concepto('JORNAL'), 1, e.valor_jornal, 'jornada', j.id
  from personal.jornada j join terceros.empleado e on e.id = j.empleado_id
  where j.aprobada_en is not null and j.fecha between v_p.desde and v_p.hasta and e.forma_pago in ('jornal', 'mixto') and e.valor_jornal > 0
  on conflict do nothing;
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  update nomina.periodo_nomina set estado = 'prenomina', preparado_por = coalesce(preparado_por, nucleo.usuario_actual()) where id = p_periodo;
  return v_n;
end $$;
comment on function nomina.preparar_prenomina(bigint) is 'Reúne el periodo: salario de los contratos, auxilio de transporte, jornales y destajo de tareas aprobadas y jornadas aprobadas. El encargado la revisa antes de cerrar';

create or replace function nomina.liquidar(p_periodo bigint) returns integer language plpgsql as $$
declare v_p nomina.periodo_nomina; r record; v_liq bigint; v_base numeric; v_ded numeric; v_n integer := 0; v_aux numeric;
begin
  select * into v_p from nomina.periodo_nomina where id = p_periodo;
  if v_p.estado <> 'prenomina' then raise exception 'Primero prepare la prenómina del periodo %', v_p.codigo; end if;
  delete from nomina.liquidacion_detalle where liquidacion_id in (select id from nomina.liquidacion where periodo_id = p_periodo);
  delete from nomina.provision_prestacion where periodo_id = p_periodo;
  delete from nomina.liquidacion where periodo_id = p_periodo;
  for r in select distinct n.empleado_id, e.forma_pago from nomina.novedad n join terceros.empleado e on e.id = n.empleado_id where n.periodo_id = p_periodo loop
    insert into nomina.liquidacion (periodo_id, empleado_id) values (p_periodo, r.empleado_id) returning id into v_liq;
    insert into nomina.liquidacion_detalle (liquidacion_id, concepto_id, cantidad, valor)
    select v_liq, n.concepto_id, sum(n.cantidad), sum(n.valor) from nomina.novedad n where n.periodo_id = p_periodo and n.empleado_id = r.empleado_id group by n.concepto_id;
    select coalesce(sum(d.valor), 0) into v_base from nomina.liquidacion_detalle d join nomina.concepto_nomina c on c.id = d.concepto_id
    where d.liquidacion_id = v_liq and c.tipo = 'devengado' and c.constitutivo_salario;
    select coalesce(sum(d.valor), 0) into v_aux from nomina.liquidacion_detalle d where d.liquidacion_id = v_liq and d.concepto_id = nomina.concepto('AUX_TRANSPORTE');
    -- Aportes del trabajador a salud y pensión (tarifas en nucleo.parametro)
    insert into nomina.liquidacion_detalle (liquidacion_id, concepto_id, cantidad, valor)
    select v_liq, nomina.concepto(c.cod), 1, round(v_base * nucleo.parametro_valor(c.par, v_p.hasta) / 100, 0)
    from (values ('SALUD_EMP', 'aporte_salud_empleado_pct'), ('PENSION_EMP', 'aporte_pension_empleado_pct')) c(cod, par)
    where v_base > 0 and nomina.concepto(c.cod) is not null;
    select coalesce(sum(case c.tipo when 'devengado' then d.valor end), 0), coalesce(sum(case c.tipo when 'deduccion' then d.valor end), 0)
      into v_base, v_ded
    from nomina.liquidacion_detalle d join nomina.concepto_nomina c on c.id = d.concepto_id where d.liquidacion_id = v_liq;
    update nomina.liquidacion set total_devengado = v_base, total_deducciones = v_ded, neto = v_base - v_ded where id = v_liq;
    -- Provisión de prestaciones para contratos (cesantías y prima incluyen el auxilio de transporte; vacaciones no)
    if r.forma_pago in ('salario', 'mixto') then
      insert into nomina.provision_prestacion (periodo_id, empleado_id, tipo, base, valor)
      select p_periodo, r.empleado_id, x.tipo, x.base, round(x.base * nucleo.parametro_valor(x.par, v_p.hasta) / 100, 0)
      from (select 'cesantias' tipo, v_base base, 'provision_cesantias_pct' par union all
            select 'intereses_cesantias', v_base, 'provision_intereses_cesantias_pct' union all
            select 'prima', v_base, 'provision_prima_pct' union all
            select 'vacaciones', v_base - v_aux, 'provision_vacaciones_pct') x
      where nucleo.parametro_valor(x.par, v_p.hasta) is not null;
    end if;
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function nomina.liquidar(bigint) is 'Liquida la prenómina: devengado, aportes del trabajador, neto y provisión de prestaciones, con tarifas de nucleo.parametro (se configuran con el contador)';

create or replace function nomina.validar_pago() returns trigger language plpgsql as $$
declare v_emp_ter bigint; v_neto numeric; v_pagado numeric; v_umbral numeric;
begin
  if tg_op = 'UPDATE' and old.pagado_en is not null then raise exception 'El pago % ya se hizo: no se edita', old.id; end if;
  select e.tercero_id, l.neto into v_emp_ter, v_neto from nomina.liquidacion l join terceros.empleado e on e.id = l.empleado_id where l.id = new.liquidacion_id;
  select coalesce(sum(valor), 0) into v_pagado from nomina.pago_nomina where liquidacion_id = new.liquidacion_id and id is distinct from new.id;
  if v_pagado + new.valor > v_neto then raise exception 'El pago supera el neto de la liquidación (% de %)', v_pagado + new.valor, v_neto; end if;
  if nucleo.tercero_de_usuario(new.preparado_por) = v_emp_ter then raise exception 'Nadie prepara su propio pago'; end if;
  if (tg_op = 'INSERT' and new.aprobado_por is not null) or (tg_op = 'UPDATE' and new.aprobado_por is distinct from old.aprobado_por)
     or (tg_op = 'INSERT' and new.segunda_aprobacion_por is not null) or (tg_op = 'UPDATE' and new.segunda_aprobacion_por is distinct from old.segunda_aprobacion_por) then
    perform nucleo.exigir_persona('aprobar pagos');
  end if;
  if new.aprobado_por is not null then
    if new.aprobado_por = new.preparado_por then raise exception 'Quien prepara el pago no lo aprueba'; end if;
    if nucleo.tercero_de_usuario(new.aprobado_por) = v_emp_ter then raise exception 'Nadie aprueba su propio pago'; end if;
  end if;
  if new.segunda_aprobacion_por is not null and (new.segunda_aprobacion_por in (new.preparado_por, new.aprobado_por)
     or nucleo.tercero_de_usuario(new.segunda_aprobacion_por) = v_emp_ter) then
    raise exception 'La segunda aprobación la da una tercera persona distinta';
  end if;
  if new.pagado_en is not null then
    perform nucleo.exigir_persona('registrar pagos');
    if new.aprobado_por is null then raise exception 'El pago no está aprobado'; end if;
    v_umbral := nucleo.parametro_valor('monto_doble_aprobacion');
    if v_umbral is not null and new.valor > v_umbral and new.segunda_aprobacion_por is null then
      raise exception 'Pagos mayores a % necesitan segunda aprobación', v_umbral;
    end if;
  end if;
  return new;
end $$;
create trigger tg_pago_nomina_validar before insert or update on nomina.pago_nomina for each row execute function nomina.validar_pago();
create trigger tg_pago_nomina_no_borrar before delete on nomina.pago_nomina for each row execute function nucleo.impedir_cambio();

create or replace function nomina.marcar_pagada() returns trigger language plpgsql as $$
begin
  if new.pagado_en is not null and (select coalesce(sum(valor), 0) from nomina.pago_nomina where liquidacion_id = new.liquidacion_id and pagado_en is not null)
       >= (select neto from nomina.liquidacion where id = new.liquidacion_id) then
    update nomina.liquidacion set estado = 'pagada' where id = new.liquidacion_id;
  end if;
  return null;
end $$;
create trigger tg_pago_nomina_pagada after insert or update on nomina.pago_nomina for each row execute function nomina.marcar_pagada();

create or replace function nomina.validar_documento_electronico() returns trigger language plpgsql as $$
begin
  perform nucleo.exigir_funcion('nomina_electronica');
  if (select regimen_tributario from nucleo.predio where id = nucleo.predio_actual()) = 'por_definir' then
    raise exception 'Defina el régimen tributario del empleador antes de transmitir nómina electrónica';
  end if;
  return new;
end $$;
create trigger tg_documento_nomina_validar before insert on nomina.documento_nomina_electronica for each row execute function nomina.validar_documento_electronico();

-- ============================================================================
-- 17. Formación: aprobar un curso emite certificado y habilita; al vencer se retira
-- ============================================================================
create or replace function formacion.validar_curso() returns trigger language plpgsql as $$
begin
  if new.origen = 'moodle' then perform nucleo.exigir_funcion('cursos_externos'); end if;
  return new;
end $$;
create trigger tg_curso_validar before insert or update on formacion.curso for each row execute function formacion.validar_curso();

create or replace function formacion.emitir_certificado(p_tercero bigint, p_competencia bigint, p_nota numeric, p_inscripcion bigint, p_sesion bigint)
returns bigint language plpgsql as $$
declare v_meses smallint; v_id bigint;
begin
  select vigencia_meses into v_meses from formacion.competencia where id = p_competencia;
  insert into formacion.certificado (tercero_id, competencia_id, inscripcion_id, sesion_id, emitido_en, vence_en, nota, codigo_verificacion)
  values (p_tercero, p_competencia, p_inscripcion, p_sesion, current_date,
          case when v_meses is not null then (current_date + make_interval(months => v_meses))::date end, p_nota,
          upper(substr(md5(random()::text || clock_timestamp()::text), 1, 12)))
  returning id into v_id;
  return v_id;
end $$;

create or replace function formacion.validar_inscripcion() returns trigger language plpgsql as $$
declare v_min numeric;
begin
  if new.estado = 'aprobado' and (tg_op = 'INSERT' or old.estado <> 'aprobado') then
    select nota_minima into v_min from formacion.curso where id = new.curso_id;
    if new.nota is null or new.nota < v_min then raise exception 'Nota % menor que la mínima % para aprobar', new.nota, v_min; end if;
    new.aprobado_en := coalesce(new.aprobado_en, current_date);
  end if;
  return new;
end $$;
create trigger tg_inscripcion_validar before insert or update on formacion.inscripcion for each row execute function formacion.validar_inscripcion();

create or replace function formacion.certificar_inscripcion() returns trigger language plpgsql as $$
declare v_comp bigint;
begin
  if new.estado = 'aprobado' and (tg_op = 'INSERT' or old.estado <> 'aprobado') then
    select competencia_id into v_comp from formacion.curso where id = new.curso_id;
    if v_comp is not null then perform formacion.emitir_certificado(new.tercero_id, v_comp, new.nota, new.id, null); end if;
  end if;
  return null;
end $$;
create trigger tg_inscripcion_certificar after insert or update on formacion.inscripcion for each row execute function formacion.certificar_inscripcion();

create or replace function formacion.certificar_sesion(p_sesion bigint) returns integer language plpgsql as $$
declare v_comp bigint; v_min numeric; r record; v_n integer := 0;
begin
  select c.competencia_id, c.nota_minima into v_comp, v_min from formacion.sesion_presencial s join formacion.curso c on c.id = s.curso_id where s.id = p_sesion;
  if v_comp is null then return 0; end if;
  for r in select a.* from formacion.asistencia a where a.sesion_id = p_sesion and a.asistio and (a.nota is null or a.nota >= v_min)
             and not exists (select 1 from formacion.certificado c where c.sesion_id = p_sesion and c.tercero_id = a.tercero_id) loop
    perform formacion.emitir_certificado(r.tercero_id, v_comp, r.nota, null, p_sesion);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function formacion.certificar_sesion(bigint) is 'La asistencia a una sesión presencial cuenta igual que un curso virtual: emite los certificados';

create or replace function formacion.habilitar_desde_certificado() returns trigger language plpgsql as $$
begin
  insert into formacion.habilitacion (tercero_id, competencia_id, certificado_id, desde, hasta)
  values (new.tercero_id, new.competencia_id, new.id, new.emitido_en, new.vence_en);
  return null;
end $$;
create trigger tg_certificado_habilitar after insert on formacion.certificado for each row execute function formacion.habilitar_desde_certificado();

create or replace function formacion.actualizar_habilitaciones(p_fecha date default current_date) returns integer language plpgsql as $$
declare v_n integer;
begin
  update formacion.habilitacion set activa = false, retirada_en = now() where activa and hasta is not null and hasta < p_fecha;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
comment on function formacion.actualizar_habilitaciones(date) is 'Tarea diaria: un certificado vencido retira la habilitación (la regla de asignación ya la ignora desde el día siguiente al vencimiento)';

-- ============================================================================
-- 18. Activos: uso, órdenes de trabajo automáticas y depreciación
-- ============================================================================
create or replace function activos.sumar_uso() returns trigger language plpgsql as $$
begin
  update activos.activo set horometro = horometro + new.horas, odometro = odometro + new.km where id = new.activo_id;
  return null;
end $$;
create trigger tg_uso_activo_sumar after insert on activos.uso_activo for each row execute function activos.sumar_uso();

create or replace function activos.generar_ordenes_trabajo(p_fecha date default current_date) returns integer language plpgsql as $$
declare r record; v_tarea bigint; v_n integer := 0;
begin
  for r in select pm.*, a.nombre as activo_nombre, a.horometro, a.odometro from activos.plan_mantenimiento pm join activos.activo a on a.id = pm.activo_id
           where pm.activo and a.estado <> 'dado_de_baja'
             and ((pm.frecuencia_tipo = 'horas' and a.horometro - pm.ultima_lectura >= pm.frecuencia_valor)
               or (pm.frecuencia_tipo = 'km' and a.odometro - pm.ultima_lectura >= pm.frecuencia_valor)
               or (pm.frecuencia_tipo = 'dias' and coalesce(pm.ultima_fecha, a.fecha_compra, p_fecha) + pm.frecuencia_valor::integer <= p_fecha))
             and not exists (select 1 from activos.orden_trabajo o where o.plan_id = pm.id and o.estado in ('abierta', 'en_curso')) loop
    insert into personal.tarea (titulo, proceso, fecha, activo_id, origen, prioridad)
    values (r.nombre || ' · ' || r.activo_nombre, 'mantenimiento', p_fecha, r.activo_id, 'orden_trabajo', 'alta') returning id into v_tarea;
    insert into activos.orden_trabajo (activo_id, plan_id, tipo, descripcion, tarea_id)
    values (r.activo_id, r.id, r.tipo, r.nombre, v_tarea);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function activos.generar_ordenes_trabajo(date) is 'Tarea diaria: crea la orden de trabajo y su tarea cuando el plan vence por horas, kilómetros o días';

create or replace function activos.cerrar_orden() returns trigger language plpgsql as $$
declare v_lect numeric; v_tipo text;
begin
  if old.estado in ('cerrada', 'cancelada') then raise exception 'La orden % ya está %', old.id, old.estado; end if;
  if new.estado = 'cerrada' then
    new.cerrada_en := now();
    select case pm.frecuencia_tipo when 'km' then a.odometro else a.horometro end, pm.frecuencia_tipo into v_lect, v_tipo
    from activos.plan_mantenimiento pm join activos.activo a on a.id = pm.activo_id where pm.id = new.plan_id;
    update activos.plan_mantenimiento set ultima_lectura = coalesce(new.lectura_cierre, v_lect, 0), ultima_fecha = current_date where id = new.plan_id;
  end if;
  return new;
end $$;
create trigger tg_orden_trabajo_cerrar before update on activos.orden_trabajo for each row execute function activos.cerrar_orden();

create or replace function activos.depreciar_mes(p_mes date) returns integer language plpgsql as $$
declare v_mes date := date_trunc('month', p_mes)::date; v_n integer;
begin
  insert into activos.depreciacion (activo_id, mes, valor, acumulada)
  select a.id, v_mes, x.cuota, coalesce(prev.acum, 0) + x.cuota
  from activos.activo a
  left join lateral (select sum(d.valor) acum from activos.depreciacion d where d.activo_id = a.id and d.mes < v_mes) prev on true
  cross join lateral (select least(round((a.valor_compra - a.valor_residual) / a.vida_util_meses, 0),
                                   a.valor_compra - a.valor_residual - coalesce(prev.acum, 0)) as cuota) x
  where a.metodo_depreciacion = 'linea_recta' and a.valor_compra > 0 and a.vida_util_meses > 0 and a.estado <> 'dado_de_baja'
    and a.fecha_compra < v_mes + interval '1 month' and x.cuota > 0
  on conflict do nothing;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
comment on function activos.depreciar_mes(date) is 'Depreciación en línea recta del mes; se detiene al llegar al valor residual';

-- ============================================================================
-- 19. Documental: una sola versión aprobada vigente y lectura de los agentes
-- ============================================================================
create or replace function documental.validar_version() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and old.estado in ('aprobada', 'obsoleta') and (new.archivo_url <> old.archivo_url or new.hash_sha256 <> old.hash_sha256) then
    raise exception 'Una versión aprobada no cambia su archivo: cree una versión nueva';
  end if;
  if tg_op = 'UPDATE' and old.estado = 'obsoleta' and new.estado <> 'obsoleta' then raise exception 'Una versión obsoleta no vuelve a estar vigente'; end if;
  if new.estado = 'aprobada' and (tg_op = 'INSERT' or old.estado <> 'aprobada') then
    perform nucleo.exigir_persona('aprobar documentos');
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
    new.aprobada_en := now(); new.vigente_desde := coalesce(new.vigente_desde, current_date);
  end if;
  return new;
end $$;
create trigger tg_version_documento_validar before insert or update on documental.version_documento for each row execute function documental.validar_version();

create or replace function documental.obsoletar_anteriores() returns trigger language plpgsql as $$
begin
  if new.estado = 'aprobada' then
    update documental.version_documento set estado = 'obsoleta' where documento_id = new.documento_id and id <> new.id and estado = 'aprobada';
  end if;
  return null;
end $$;
create trigger tg_version_documento_obsoletar after insert or update of estado on documental.version_documento
  for each row execute function documental.obsoletar_anteriores();

create or replace view documental.v_vigentes as
select d.id as documento_id, d.codigo, d.titulo, d.tipo, d.uso_agentes, v.id as version_id, v.version, v.archivo_url, v.vigente_desde, v.vence_en,
       case when v.vence_en is null then 'vigente' when v.vence_en < current_date then 'vencido'
            when v.vence_en - v.avisar_dias <= current_date then 'por_vencer' else 'vigente' end as situacion
from documental.documento d join documental.version_documento v on v.documento_id = d.id and v.estado = 'aprobada';

create or replace function documental.documento_para_agente(p_documento bigint) returns varchar language plpgsql stable as $$
declare v record;
begin
  select * into v from documental.v_vigentes where documento_id = p_documento;
  if v is null or not v.uso_agentes or v.situacion = 'vencido' then
    raise exception 'El documento % no está aprobado, vigente y autorizado para agentes', p_documento;
  end if;
  return v.archivo_url;
end $$;
comment on function documental.documento_para_agente(bigint) is 'Los agentes (Instructor, Agrónomo) solo leen la versión aprobada y vigente de documentos autorizados';

-- ============================================================================
-- 20. Cumplimiento: evidencia automática, vencimientos y cierre de no conformidades
-- ============================================================================
create or replace function cumplimiento.validar_expediente() returns trigger language plpgsql as $$
declare v_funcion text;
begin
  select funcion_codigo into v_funcion from cumplimiento.norma where id = new.norma_id;
  if v_funcion is not null then perform nucleo.exigir_funcion(v_funcion); end if;
  return new;
end $$;
create trigger tg_expediente_validar before insert on cumplimiento.expediente for each row execute function cumplimiento.validar_expediente();

create or replace function cumplimiento.evaluar_expediente(p_expediente bigint) returns integer language plpgsql as $$
declare r record; v_ok boolean; v_vence date; v_tipo text; v_val text; v_no integer;
begin
  insert into cumplimiento.evaluacion_requisito (expediente_id, requisito_id)
  select p_expediente, q.id from cumplimiento.requisito q join cumplimiento.expediente e on e.norma_id = q.norma_id
  where e.id = p_expediente on conflict do nothing;
  for r in select ev.id, q.regla_evidencia, q.vigencia_dias from cumplimiento.evaluacion_requisito ev
           join cumplimiento.requisito q on q.id = ev.requisito_id where ev.expediente_id = p_expediente loop
    v_ok := null; v_vence := null;
    if r.regla_evidencia is not null then
      v_tipo := split_part(r.regla_evidencia, ':', 1); v_val := split_part(r.regla_evidencia, ':', 2);
      if v_tipo = 'competencia' then
        select count(*) > 0, min(h.hasta) into v_ok, v_vence from formacion.habilitacion h join formacion.competencia c on c.id = h.competencia_id
        where c.codigo = v_val and h.activa and (h.hasta is null or h.hasta >= current_date);
      elsif v_tipo = 'documento' then
        select count(*) > 0, min(vence_en) into v_ok, v_vence from documental.v_vigentes where tipo = v_val and situacion <> 'vencido';
      elsif v_tipo = 'registro' and to_regclass(v_val) is not null then
        execute format('select count(*) > 0 from %s where creado_en >= now() - make_interval(days => %s)', v_val, coalesce(r.vigencia_dias, 365)) into v_ok;
      end if;
    end if;
    -- Evidencias cargadas a mano: si todas vencieron, el requisito deja de cumplirse
    if v_ok is null and exists (select 1 from cumplimiento.evidencia_requisito where evaluacion_id = r.id) then
      select bool_or(vence_en is null or vence_en >= current_date), min(vence_en) filter (where vence_en >= current_date) into v_ok, v_vence
      from cumplimiento.evidencia_requisito where evaluacion_id = r.id;
    end if;
    if v_ok is not null then
      update cumplimiento.evaluacion_requisito set estado = case when v_ok then 'cumple' else 'no_cumple' end, origen = 'automatica',
             evaluado_en = now(), vence_en = v_vence where id = r.id and estado <> 'no_aplica';
    end if;
  end loop;
  select count(*) into v_no from cumplimiento.evaluacion_requisito where expediente_id = p_expediente and estado <> 'cumple' and estado <> 'no_aplica';
  return v_no;
end $$;
comment on function cumplimiento.evaluar_expediente(bigint) is 'Tarea diaria: revisa cada requisito contra su evidencia (habilitaciones, documentos vigentes, registros recientes); lo vencido pasa a no cumple. Devuelve cuántos faltan';

create or replace function cumplimiento.cerrar_no_conformidad() returns trigger language plpgsql as $$
begin
  if old.estado = 'cerrada' then raise exception 'La no conformidad % ya está cerrada', old.id; end if;
  if new.estado = 'cerrada' then
    perform nucleo.exigir_persona('cerrar no conformidades');
    if new.verificacion is null then raise exception 'Para cerrar una no conformidad hay que registrar la verificación'; end if;
    if not exists (select 1 from cumplimiento.accion_correctiva where no_conformidad_id = new.id and estado = 'verificada')
       or exists (select 1 from cumplimiento.accion_correctiva where no_conformidad_id = new.id and estado in ('pendiente', 'hecha')) then
      raise exception 'Una no conformidad no se cierra sin todas sus acciones correctivas verificadas';
    end if;
    new.cerrada_por := coalesce(new.cerrada_por, nucleo.usuario_actual()); new.cerrada_en := now();
  end if;
  return new;
end $$;
create trigger tg_no_conformidad_cerrar before update on cumplimiento.no_conformidad for each row execute function cumplimiento.cerrar_no_conformidad();

create or replace function cumplimiento.verificar_accion() returns trigger language plpgsql as $$
begin
  if new.estado = 'verificada' and old.estado <> 'verificada' then
    perform nucleo.exigir_persona('verificar acciones correctivas');
    new.verificada_por := coalesce(new.verificada_por, nucleo.usuario_actual()); new.verificada_en := now();
    if old.estado <> 'hecha' then raise exception 'Solo se verifica una acción hecha'; end if;
  end if;
  return new;
end $$;
create trigger tg_accion_correctiva_verificar before update on cumplimiento.accion_correctiva for each row execute function cumplimiento.verificar_accion();

create or replace view cumplimiento.v_granja_biosegura as
select (select coalesce(sum(l.cantidad_actual), 0) from produccion.lote_animal l join produccion.especie e on e.id = l.especie_id
        where e.grupo = 'ave' and l.estado = 'activo' and l.proposito in ('postura', 'cria')) as aves_postura_levante,
       200 as umbral_obligatorio,
       (select x.estado from cumplimiento.expediente x join cumplimiento.norma n on n.id = x.norma_id where n.codigo = 'ICA_GAB') as estado_expediente,
       (select x.rspa_numero from cumplimiento.expediente x join cumplimiento.norma n on n.id = x.norma_id where n.codigo = 'ICA_GAB') as rspa,
       case when (select coalesce(sum(l.cantidad_actual), 0) from produccion.lote_animal l join produccion.especie e on e.id = l.especie_id
                  where e.grupo = 'ave' and l.estado = 'activo' and l.proposito in ('postura', 'cria')) >= 200
             and coalesce((select x.estado from cumplimiento.expediente x join cumplimiento.norma n on n.id = x.norma_id where n.codigo = 'ICA_GAB'), '') <> 'certificado'
            then 'alerta: 200 aves o más sin certificado de granja avícola biosegura' else 'en regla' end as situacion;
comment on view cumplimiento.v_granja_biosegura is 'Resolución ICA 3651 de 2014: postura o levante desde 200 aves exige certificado de granja avícola biosegura';

-- ============================================================================
-- 21. Seguros: subsidio, avisos de siniestro revisados por una persona e índice paramétrico
-- ============================================================================
create or replace function seguros.preparar_poliza() returns trigger language plpgsql as $$
begin
  if new.valor_subsidiado = 0 and new.incentivo_pct > 0 then new.valor_subsidiado := round(new.prima * new.incentivo_pct / 100, 0); end if;
  if new.tipo = 'parametrico' then perform nucleo.exigir_funcion('seguro_parametrico'); end if;
  return new;
end $$;
create trigger tg_poliza_preparar before insert or update on seguros.poliza for each row execute function seguros.preparar_poliza();

create or replace view seguros.v_por_vencer as
select p.id, p.numero, p.tipo, p.hasta, p.hasta - current_date as dias_para_vencer
from seguros.poliza p where p.estado = 'vigente' and p.hasta - p.avisar_dias <= current_date;

create or replace function seguros.validar_aviso() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' and (new.indice_id is not null or (select tipo from seguros.poliza where id = new.poliza_id) = 'parametrico') then
    perform nucleo.exigir_funcion('seguro_parametrico');
    if new.serie_datos is null then raise exception 'Un aviso paramétrico guarda la serie de datos usada como evidencia'; end if;
  end if;
  if tg_op = 'UPDATE' and new.estado <> old.estado then
    if new.estado = 'revisado' then
      perform nucleo.exigir_persona('revisar avisos de siniestro');
      new.revisado_por := coalesce(new.revisado_por, nucleo.usuario_actual());
    elsif new.estado = 'enviado' then
      perform nucleo.exigir_persona('enviar avisos de siniestro');
      if old.estado <> 'revisado' then raise exception 'No hay reclamación automática: el aviso se revisa antes de enviarlo'; end if;
      new.enviado_en := now();
    end if;
  end if;
  return new;
end $$;
create trigger tg_aviso_siniestro_validar before insert or update on seguros.aviso_siniestro for each row execute function seguros.validar_aviso();

create or replace function seguros.vigilar_indice(p_indice bigint, p_hasta date default current_date) returns bigint language plpgsql as $$
declare i seguros.indice_poliza; v_valor numeric; v_serie jsonb; v_id bigint;
begin
  perform nucleo.exigir_funcion('seguro_parametrico');
  select * into i from seguros.indice_poliza where id = p_indice;
  if i.sensor_id is null then return null; end if;
  select case when i.variable in ('lluvia_mm', 'dias_secos') then sum(v) else avg(v) end,
         jsonb_agg(jsonb_build_object('dia', d, 'valor', round(v::numeric, 2)) order by d)
    into v_valor, v_serie
  from (select date_trunc('day', medido_en)::date d,
               case when i.variable = 'lluvia_mm' then sum(valor) when i.variable = 'dias_secos' then case when sum(valor) < 1 then 1 else 0 end else avg(valor) end v
        from iot.lectura where sensor_id = i.sensor_id and medido_en >= p_hasta - i.ventana_dias and medido_en < p_hasta + 1 group by 1) x;
  if v_valor is null or not ((i.comparador = 'mayor' and v_valor > i.umbral) or (i.comparador = 'menor' and v_valor < i.umbral)) then return null; end if;
  insert into seguros.aviso_siniestro (poliza_id, indice_id, detectado_en, descripcion, serie_datos)
  values (i.poliza_id, i.id, now(), format('La estación propia marca %s = %s en %s días (umbral %s %s). Verificar con la fuente oficial: %s',
          i.variable, round(v_valor, 1), i.ventana_dias, i.comparador, i.umbral, i.fuente_oficial), v_serie)
  returning id into v_id;
  return v_id;
end $$;
comment on function seguros.vigilar_indice(bigint, date) is 'Compara la estación de la finca con el índice de la póliza; si parece cumplirse, deja un aviso en borrador para que una persona lo revise. El pago lo define el índice oficial de la aseguradora';

-- ============================================================================
-- 22. IA y finanzas ampliadas: diagnóstico revisado, anticipos, costos, estados financieros e indicadores
-- ============================================================================
create or replace function ia.validar_diagnostico() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then perform nucleo.exigir_funcion('diagnostico_imagen'); return new; end if;
  if old.estado <> 'pendiente' then raise exception 'El diagnóstico % ya fue revisado', old.id; end if;
  if new.estado <> 'pendiente' then
    perform nucleo.exigir_persona('confirmar diagnósticos');
    new.revisado_por := coalesce(new.revisado_por, nucleo.usuario_actual()); new.revisado_en := now();
    if new.estado = 'confirmado' then new.diagnostico_final := coalesce(new.diagnostico_final, new.diagnostico_propuesto); end if;
    if new.estado = 'corregido' and new.diagnostico_final is null then raise exception 'Al corregir indique el diagnóstico final'; end if;
  end if;
  return new;
end $$;
create trigger tg_diagnostico_validar before insert or update on ia.diagnostico_imagen for each row execute function ia.validar_diagnostico();

create or replace function ia.validar_decision() returns trigger language plpgsql as $$
begin
  if new.opcion_elegida is not null and (tg_op = 'INSERT' or old.opcion_elegida is null) then
    perform nucleo.exigir_persona('tomar decisiones');
    new.decidido_por := coalesce(new.decidido_por, nucleo.usuario_actual()); new.decidido_en := now();
  end if;
  if tg_op = 'UPDATE' and old.opcion_elegida is not null and new.opcion_elegida is distinct from old.opcion_elegida then
    raise exception 'Una decisión tomada no se cambia: registre una decisión nueva';
  end if;
  return new;
end $$;
create trigger tg_decision_validar before insert or update on ia.decision for each row execute function ia.validar_decision();

create or replace function finanzas.preparar_anticipo() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then new.saldo := new.valor; end if;
  if new.saldo = 0 and new.estado = 'abierto' then new.estado := 'aplicado'; end if;
  return new;
end $$;
create trigger tg_anticipo_preparar before insert or update on finanzas.anticipo_proveedor for each row execute function finanzas.preparar_anticipo();

create or replace function finanzas.aplicar_anticipo() returns trigger language plpgsql as $$
declare a finanzas.anticipo_proveedor;
begin
  select * into a from finanzas.anticipo_proveedor where id = new.anticipo_id for update;
  if a.estado <> 'abierto' then raise exception 'El anticipo % está %', a.id, a.estado; end if;
  if (select proveedor_id from compras.orden_compra where id = new.orden_compra_id) <> a.proveedor_id then
    raise exception 'El anticipo es de otro proveedor';
  end if;
  if new.valor > a.saldo then raise exception 'El anticipo solo tiene saldo de % (se intentó descontar %)', a.saldo, new.valor; end if;
  update finanzas.anticipo_proveedor set saldo = saldo - new.valor where id = a.id;
  return new;
end $$;
create trigger tg_aplicacion_anticipo before insert on finanzas.aplicacion_anticipo for each row execute function finanzas.aplicar_anticipo();
create trigger tg_aplicacion_anticipo_inmutable before update or delete on finanzas.aplicacion_anticipo for each row execute function nucleo.impedir_cambio();

create or replace function finanzas.validar_clasificacion() returns trigger language plpgsql as $$
begin
  if new.comportamiento = 'semivariable' and new.parte_fija_pct is null then raise exception 'Un costo semivariable necesita su parte fija (%%)'; end if;
  if new.comportamiento in ('fijo', 'variable') then new.parte_fija_pct := case new.comportamiento when 'fijo' then 100 else 0 end; end if;
  return new;
end $$;
create trigger tg_clasificacion_costo_validar before insert or update on finanzas.clasificacion_costo for each row execute function finanzas.validar_clasificacion();

create or replace function finanzas.validar_presupuesto_detalle() returns trigger language plpgsql as $$
declare p finanzas.presupuesto;
begin
  select * into p from finanzas.presupuesto where id = coalesce(new.presupuesto_id, old.presupuesto_id);
  if p.estado <> 'borrador' then raise exception 'El presupuesto % está %: no se cambian sus rubros (cree una versión nueva)', p.nombre, p.estado; end if;
  if tg_op <> 'DELETE' and p.base_cero and new.justificacion is null then raise exception 'En presupuesto base cero cada rubro se justifica'; end if;
  return coalesce(new, old);
end $$;
create trigger tg_presupuesto_detalle_validar before insert or update or delete on finanzas.presupuesto_detalle for each row execute function finanzas.validar_presupuesto_detalle();

-- Saldos por cuenta (PUC colombiano: 1 activo, 2 pasivo, 3 patrimonio, 4 ingresos, 5 gastos, 6 costo de ventas, 7 costo de producción)
create or replace function finanzas.saldo(p_prefijo text, p_desde date, p_hasta date, p_centro bigint default null) returns numeric language sql stable as $$
  select coalesce(sum(case when left(c.codigo, 1) in ('1', '5', '6', '7') then m.debito - m.credito else m.credito - m.debito end), 0)
  from finanzas.movimiento_contable m join finanzas.comprobante k on k.id = m.comprobante_id join finanzas.cuenta_contable c on c.id = m.cuenta_id
  where k.estado = 'contabilizado' and c.codigo like p_prefijo || '%' and k.fecha between coalesce(p_desde, '1900-01-01') and p_hasta
    and (p_centro is null or m.centro_costo_id = p_centro) $$;
comment on function finanzas.saldo(text, date, date, bigint) is 'Saldo de las cuentas que empiezan por el prefijo según la naturaleza de su clase (así la depreciación acumulada resta del activo); sin fecha inicial = acumulado (balance)';

create or replace function finanzas.costo_por_comportamiento(p_desde date, p_hasta date, p_variable boolean, p_centro bigint default null)
returns numeric language sql stable as $$
  select coalesce(sum((m.debito - m.credito) * case when p_variable then 1 - coalesce(cc.parte_fija_pct, 100) / 100 else coalesce(cc.parte_fija_pct, 100) / 100 end), 0)
  from finanzas.movimiento_contable m join finanzas.comprobante k on k.id = m.comprobante_id join finanzas.cuenta_contable c on c.id = m.cuenta_id
  left join finanzas.clasificacion_costo cc on cc.cuenta_id = c.id
  where k.estado = 'contabilizado' and k.fecha between p_desde and p_hasta and left(c.codigo, 1) in ('5', '6')
    and c.codigo not like '53%' and c.codigo not like '54%' and (p_centro is null or m.centro_costo_id = p_centro) $$;
comment on function finanzas.costo_por_comportamiento(date, date, boolean, bigint) is 'Costos y gastos operacionales variables o fijos según su clasificación; lo no clasificado se trata como fijo (prudente)';

create or replace function finanzas.estado_resultados(p_desde date, p_hasta date, p_centro bigint default null) returns jsonb language plpgsql stable as $$
declare v_ing numeric; v_var numeric; v_fij numeric; v_mc numeric; v_uo numeric; v_noi numeric; v_noe numeric; v_int numeric; v_tx numeric; v_un numeric; v_dep numeric;
begin
  v_ing := finanzas.saldo('41', p_desde, p_hasta, p_centro);
  v_var := finanzas.costo_por_comportamiento(p_desde, p_hasta, true, p_centro);
  v_fij := finanzas.costo_por_comportamiento(p_desde, p_hasta, false, p_centro);
  v_mc := v_ing - v_var; v_uo := v_mc - v_fij;
  v_noi := finanzas.saldo('42', p_desde, p_hasta, p_centro);
  v_noe := finanzas.saldo('53', p_desde, p_hasta, p_centro);
  v_int := finanzas.saldo('5305', p_desde, p_hasta, p_centro);
  v_tx := finanzas.saldo('54', p_desde, p_hasta, p_centro);
  v_dep := finanzas.saldo('5160', p_desde, p_hasta, p_centro) + finanzas.saldo('5260', p_desde, p_hasta, p_centro);
  v_un := v_uo + v_noi - v_noe - v_tx;
  return jsonb_build_object('ingresos_operacionales', v_ing, 'costos_gastos_variables', v_var, 'margen_contribucion', v_mc,
    'costos_gastos_fijos', v_fij, 'utilidad_operacional', v_uo, 'ingresos_no_operacionales', v_noi, 'gastos_no_operacionales', v_noe,
    'intereses', v_int, 'utilidad_antes_impuestos', v_uo + v_noi - v_noe, 'impuestos', v_tx, 'utilidad_neta', v_un,
    'depreciacion', v_dep, 'ebitda', v_uo + v_dep,
    'costo_ventas', finanzas.saldo('6', p_desde, p_hasta, p_centro), 'utilidad_bruta', v_ing - finanzas.saldo('6', p_desde, p_hasta, p_centro));
end $$;
comment on function finanzas.estado_resultados(date, date, bigint) is 'Estado de resultados por costeo variable (margen de contribución, utilidad operacional, neta y EBITDA), total o por centro de costo';

create or replace function finanzas.balance_general(p_hasta date) returns jsonb language plpgsql stable as $$
declare v jsonb; v_ac numeric; v_anc numeric; v_pc numeric; v_pt numeric; v_pat numeric; v_res numeric;
begin
  -- La clase 7 (costos de producción) se trata como producción en proceso hasta trasladarse al inventario
  v_ac := finanzas.saldo('11', null, p_hasta) + finanzas.saldo('12', null, p_hasta) + finanzas.saldo('13', null, p_hasta) + finanzas.saldo('14', null, p_hasta)
        + finanzas.saldo('7', null, p_hasta);
  v_anc := finanzas.saldo('15', null, p_hasta) + finanzas.saldo('16', null, p_hasta) + finanzas.saldo('17', null, p_hasta) + finanzas.saldo('18', null, p_hasta) + finanzas.saldo('19', null, p_hasta);
  v_pt := finanzas.saldo('2', null, p_hasta);
  v_pc := v_pt - finanzas.saldo('27', null, p_hasta) - finanzas.saldo('29', null, p_hasta);
  v_res := finanzas.saldo('4', null, p_hasta) - finanzas.saldo('5', null, p_hasta) - finanzas.saldo('6', null, p_hasta);
  v_pat := finanzas.saldo('3', null, p_hasta) + v_res;
  return jsonb_build_object('disponible', finanzas.saldo('11', null, p_hasta), 'deudores', finanzas.saldo('13', null, p_hasta),
    'inventarios', finanzas.saldo('14', null, p_hasta), 'activo_corriente', v_ac, 'activo_no_corriente', v_anc, 'activo_total', v_ac + v_anc,
    'obligaciones_financieras', finanzas.saldo('21', null, p_hasta), 'pasivo_corriente', v_pc, 'pasivo_total', v_pt,
    'patrimonio', v_pat, 'resultado_ejercicio', v_res, 'utilidades_retenidas', finanzas.saldo('37', null, p_hasta),
    'cuadra', (v_ac + v_anc) = (v_pt + v_pat));
end $$;
comment on function finanzas.balance_general(date) is 'Balance general a una fecha: activo = pasivo + patrimonio (el resultado del ejercicio entra al patrimonio)';

create or replace function finanzas.palancas(p_unidades numeric, p_precio numeric, p_cv_unitario numeric, p_costos_fijos numeric, p_intereses numeric default 0)
returns table (margen_contribucion numeric, utilidad_operacional numeric, punto_equilibrio_unidades numeric, margen_seguridad_pct numeric,
               gpo numeric, gpf numeric, gpt numeric) language sql immutable as $$
  select mc, uo, case when p_precio > p_cv_unitario then round(p_costos_fijos / (p_precio - p_cv_unitario), 2) end,
         case when p_unidades > 0 and p_precio > p_cv_unitario then round((p_unidades - p_costos_fijos / (p_precio - p_cv_unitario)) / p_unidades * 100, 2) end,
         case when uo <> 0 then round(mc / uo, 4) end,
         case when uo - p_intereses <> 0 then round(uo / (uo - p_intereses), 4) end,
         case when uo - p_intereses <> 0 then round(mc / (uo - p_intereses), 4) end
  from (select p_unidades * (p_precio - p_cv_unitario) mc, p_unidades * (p_precio - p_cv_unitario) - p_costos_fijos uo) x $$;
comment on function finanzas.palancas(numeric, numeric, numeric, numeric, numeric) is 'Modelo costo-volumen-utilidad y teoría de las palancas: PE = CF/(P-CV), margen de seguridad, GPO = MC/UO, GPF = UO/(UO-I), GPT = GPO×GPF';

create or replace function finanzas.distribuir_costos(p_mes date) returns integer language plpgsql as $$
declare v_mes date := date_trunc('month', p_mes)::date; v_n integer;
begin
  update finanzas.asignacion_costo ac set valor_asignado = round(x.costo * ac.cantidad_inductor / nullif(x.total_inductor, 0), 0)
  from (select a.id actividad_id, sum(ac2.cantidad_inductor) total_inductor,
               finanzas.saldo('5', v_mes, (v_mes + interval '1 month - 1 day')::date, a.centro_costo_id)
             + finanzas.saldo('7', v_mes, (v_mes + interval '1 month - 1 day')::date, a.centro_costo_id) costo
        from finanzas.actividad_costo a join finanzas.asignacion_costo ac2 on ac2.actividad_id = a.id and ac2.mes = v_mes group by a.id, a.centro_costo_id) x
  where ac.actividad_id = x.actividad_id and ac.mes = v_mes;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
comment on function finanzas.distribuir_costos(date) is 'Costeo basado en actividades: reparte el costo del centro de servicio de cada actividad según el inductor consumido por cada línea';

create or replace function finanzas.calcular_indicadores(p_desde date, p_hasta date) returns integer language plpgsql as $$
declare er jsonb := finanzas.estado_resultados(p_desde, p_hasta); bg jsonb := finanzas.balance_general(p_hasta);
        v_dias numeric := p_hasta - p_desde + 1; v jsonb; r record; v_meta numeric; v_n integer := 0; v_sem text;
        ing numeric; uo numeric; un numeric; mc numeric; intr numeric; tot_act numeric; pat numeric; pt numeric; ac numeric; pc numeric;
        kc numeric := nucleo.parametro_valor('costo_capital_anual_pct', p_hasta); tx numeric := nucleo.parametro_valor('tarifa_renta_pct', p_hasta);
begin
  ing := (er->>'ingresos_operacionales')::numeric; uo := (er->>'utilidad_operacional')::numeric; un := (er->>'utilidad_neta')::numeric;
  mc := (er->>'margen_contribucion')::numeric; intr := (er->>'intereses')::numeric;
  tot_act := (bg->>'activo_total')::numeric; pat := (bg->>'patrimonio')::numeric; pt := (bg->>'pasivo_total')::numeric;
  ac := (bg->>'activo_corriente')::numeric; pc := (bg->>'pasivo_corriente')::numeric;
  v := jsonb_build_object(
    'capital_trabajo', ac - pc,
    'razon_corriente', ac / nullif(pc, 0),
    'prueba_acida', (ac - (bg->>'inventarios')::numeric) / nullif(pc, 0),
    'endeudamiento', pt / nullif(tot_act, 0) * 100,
    'apalancamiento', tot_act / nullif(pat, 0),
    'cobertura_intereses', uo / nullif(intr, 0),
    'margen_bruto', (er->>'utilidad_bruta')::numeric / nullif(ing, 0) * 100,
    'margen_operacional', uo / nullif(ing, 0) * 100,
    'margen_neto', un / nullif(ing, 0) * 100,
    'ebitda', (er->>'ebitda')::numeric,
    'rsa', un / nullif(tot_act, 0) * 100,
    'rsp', un / nullif(pat, 0) * 100,
    'rotacion_activos', ing / nullif(tot_act, 0),
    'dias_cartera', (bg->>'deudores')::numeric / nullif(ing, 0) * v_dias,
    'dias_inventario', (bg->>'inventarios')::numeric / nullif((er->>'costo_ventas')::numeric, 0) * v_dias,
    'gpo', mc / nullif(uo, 0),
    'gpf', uo / nullif(uo - intr, 0),
    'gpt', mc / nullif(uo - intr, 0),
    'punto_equilibrio_pesos', (er->>'costos_gastos_fijos')::numeric / nullif(mc / nullif(ing, 0), 0),
    'margen_seguridad', (ing - (er->>'costos_gastos_fijos')::numeric / nullif(mc / nullif(ing, 0), 0)) / nullif(ing, 0) * 100,
    'eva', case when kc is not null then uo * (1 - coalesce(tx, 0) / 100) - (pat + (bg->>'obligaciones_financieras')::numeric) * kc / 100 * v_dias / 365 end,
    'altman_z2', 6.56 * (ac - pc) / nullif(tot_act, 0) + 3.26 * (bg->>'utilidades_retenidas')::numeric / nullif(tot_act, 0)
               + 6.72 * uo / nullif(tot_act, 0) + 1.05 * pat / nullif(pt, 0));
  for r in select i.id, i.codigo, i.sentido from finanzas.indicador i where v ? i.codigo loop
    select o.meta into v_meta from estrategia.objetivo o where o.indicador_id = r.id order by o.fecha_meta desc nulls last limit 1;
    v_sem := case when v->>r.codigo is null then 'sin_dato' when v_meta is null then 'sin_meta'
                  when r.sentido = 'mayor_mejor' then case when (v->>r.codigo)::numeric >= v_meta then 'verde' when (v->>r.codigo)::numeric >= v_meta * 0.9 then 'amarillo' else 'rojo' end
                  when r.sentido = 'menor_mejor' then case when (v->>r.codigo)::numeric <= v_meta then 'verde' when (v->>r.codigo)::numeric <= v_meta * 1.1 then 'amarillo' else 'rojo' end
                  else 'sin_meta' end;
    insert into finanzas.valor_indicador (indicador_id, desde, hasta, valor, meta, semaforo)
    values (r.id, p_desde, p_hasta, round((v->>r.codigo)::numeric, 4), v_meta, v_sem);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function finanzas.calcular_indicadores(date, date) is 'Calcula los indicadores financieros del periodo desde la contabilidad (liquidez, endeudamiento, rentabilidad, actividad, palancas, EVA, Z de Altman para empresas no manufactureras) con semáforo contra la meta';

create or replace function finanzas.validar_reporte_indicadores() returns trigger language plpgsql as $$
begin
  perform nucleo.exigir_funcion('indicadores_credito');
  perform nucleo.exigir_persona('autorizar el envío de indicadores');
  if new.contenido ?| array['costo', 'costos', 'costo_unitario', 'salario', 'telefono', 'correo', 'documento', 'numero_documento', 'clientes'] then
    raise exception 'El informe de indicadores no lleva costos ni datos personales';
  end if;
  new.hash_sha256 := encode(sha256(convert_to(new.contenido::text, 'UTF8')), 'hex');
  return new;
end $$;
create trigger tg_reporte_indicadores_validar before insert on finanzas.reporte_indicadores for each row execute function finanzas.validar_reporte_indicadores();
create trigger tg_reporte_indicadores_inmutable before update or delete on finanzas.reporte_indicadores for each row execute function nucleo.impedir_cambio();

-- ============================================================================
-- 23. Robótica, energía e integraciones externas (todas encendidas por función)
-- ============================================================================
create or replace function iot.validar_mision() returns trigger language plpgsql as $$
declare v_tipo_activo text; v_reg text;
begin
  select tipo, registro_aerocivil into v_tipo_activo, v_reg from activos.activo where id = new.activo_id;
  if tg_op = 'INSERT' then
    if new.tipo = 'dron_monitoreo' then
      perform nucleo.exigir_funcion('dron_monitoreo');
      if v_tipo_activo <> 'dron' then raise exception 'La misión de dron necesita un activo tipo dron'; end if;
    else
      perform nucleo.exigir_funcion('robot_campo');
      if v_tipo_activo <> 'robot' then raise exception 'La misión de robot necesita un activo tipo robot'; end if;
    end if;
    return new;
  end if;
  if old.estado in ('terminada', 'abortada') then raise exception 'La misión % ya terminó', old.id; end if;
  if new.estado = 'aprobada' and old.estado = 'propuesta' then
    perform nucleo.exigir_persona('aprobar misiones de robots o drones');
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
  end if;
  if new.estado = 'en_curso' and old.estado <> 'en_curso' then
    if old.estado <> 'aprobada' then raise exception 'Una misión solo arranca aprobada por una persona'; end if;
    if new.tipo = 'dron_monitoreo' then
      if v_reg is null then raise exception 'El dron no tiene registro ante la Aerocivil (RAC 100)'; end if;
      if new.piloto_id is null then raise exception 'El vuelo necesita piloto'; end if;
      if coalesce(new.altura_max_m, 999) > 122 then raise exception 'RAC 100: la altura máxima es 122 m'; end if;
      if not exists (select 1 from seguros.poliza p where p.id = new.poliza_id and p.estado = 'vigente' and current_date between p.desde and p.hasta
                     and p.tipo in ('responsabilidad_civil', 'dron')) then
        raise exception 'El vuelo necesita póliza de responsabilidad civil vigente';
      end if;
    else
      if not new.zona_sin_personas or not new.parada_emergencia_probada then
        raise exception 'El robot solo opera en una zona sin personas y con la parada de emergencia probada';
      end if;
    end if;
    new.inicio := coalesce(new.inicio, now());
  end if;
  if new.estado in ('terminada', 'abortada') then new.fin := coalesce(new.fin, now()); end if;
  return new;
end $$;
create trigger tg_mision_robot_validar before insert or update on iot.mision_robot for each row execute function iot.validar_mision();

create or replace function iot.cargas_a_cortar(p_bateria_pct numeric) returns table (actuador_id bigint, prioridad smallint) language sql stable as $$
  select actuador_id, prioridad from iot.prioridad_carga where not esencial and corte_bateria_pct is not null and p_bateria_pct <= corte_bateria_pct
  order by prioridad desc $$;
comment on function iot.cargas_a_cortar(numeric) is 'Con batería baja, cargas no esenciales a cortar de la menos a la más importante; alarma, nevera y agua de animales nunca se cortan';

create or replace function nucleo.validar_llave_api() returns trigger language plpgsql as $$
begin
  if new.activa then
    perform nucleo.exigir_funcion('api_b2b');
    if new.vence_en <= current_date then raise exception 'La llave está vencida'; end if;
    if not exists (select 1 from terceros.cliente where tercero_id = new.tercero_id) then raise exception 'Solo un cliente tiene llave de la API B2B'; end if;
    if not new.alcances <@ array['catalogo:leer', 'pedidos:leer', 'pedidos:crear'] then raise exception 'Alcance no permitido en la API B2B'; end if;
  end if;
  return new;
end $$;
create trigger tg_llave_api_validar before insert or update on nucleo.llave_api for each row execute function nucleo.validar_llave_api();

create or replace function nucleo.autenticar_llave_api(p_prefijo text, p_hash text, p_ip inet) returns bigint language plpgsql as $$
declare v nucleo.llave_api;
begin
  if exists (select 1 from seguridad.senuelo where tipo = 'llave_api' and valor = p_prefijo and activo) then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, ip, predio_id, detalle)
    values ('senuelo', 'critica', 'api', p_ip, nucleo.predio_actual(), jsonb_build_object('llave', p_prefijo));
    insert into seguridad.bloqueo (tipo, ip, motivo, hasta) values ('ip', p_ip::cidr, 'Usó una llave señuelo', now() + interval '24 hours');
    return null;
  end if;
  select * into v from nucleo.llave_api where prefijo = p_prefijo and hash_llave = p_hash and activa and vence_en > current_date;
  if v.id is null then return null; end if;
  update nucleo.llave_api set ultimo_uso = now() where id = v.id;
  return v.tercero_id;
end $$;

create or replace function nucleo.validar_webhook() returns trigger language plpgsql as $$
begin
  if new.activa then perform nucleo.exigir_funcion('webhooks_salientes'); end if;
  if new.fallos_seguidos >= 10 then new.activa := false; end if;
  return new;
end $$;
create trigger tg_webhook_validar before insert or update on nucleo.webhook_suscripcion for each row execute function nucleo.validar_webhook();

-- ============================================================================
-- 24. Seguridad informática: detector de ataques, señuelos, doble factor y alertas
-- ============================================================================
create or replace function seguridad.regla(p_codigo text) returns seguridad.regla_deteccion language sql stable as $$
  select * from seguridad.regla_deteccion where codigo = p_codigo and activa $$;

create or replace function seguridad.ip_bloqueada(p_ip inet) returns boolean language sql stable as $$
  select exists (select 1 from seguridad.bloqueo where tipo = 'ip' and p_ip <<= ip and levantado_por is null and (hasta is null or hasta > now())) $$;
create or replace function seguridad.cuenta_bloqueada(p_usuario bigint) returns boolean language sql stable as $$
  select exists (select 1 from seguridad.bloqueo where tipo = 'cuenta' and usuario_id = p_usuario and levantado_por is null and (hasta is null or hasta > now())) $$;

create or replace function seguridad.registrar_intento(p_correo text, p_ip inet, p_exito boolean, p_motivo text default null, p_agente_usuario text default null)
returns text language plpgsql as $$
declare v_usr bigint; r seguridad.regla_deteccion; v_n integer;
begin
  if seguridad.ip_bloqueada(p_ip) then
    insert into seguridad.intento_acceso (correo, ip, exito, motivo_fallo, agente_usuario) values (p_correo, p_ip, false, 'ip_bloqueada', p_agente_usuario);
    return 'ip_bloqueada';
  end if;
  if exists (select 1 from seguridad.senuelo where tipo = 'cuenta' and lower(valor) = lower(p_correo) and activo) then
    insert into seguridad.intento_acceso (correo, ip, exito, motivo_fallo, agente_usuario) values (p_correo, p_ip, false, 'senuelo', p_agente_usuario);
    r := seguridad.regla('senuelo');
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, ip, detalle)
    values ('senuelo', 'critica', 'app', r.id, p_ip, jsonb_build_object('correo', p_correo));
    insert into seguridad.bloqueo (tipo, ip, regla_id, motivo, hasta)
    values ('ip', p_ip::cidr, r.id, 'Intentó entrar con una cuenta señuelo', now() + make_interval(mins => coalesce(r.bloqueo_min, 1440)));
    return 'senuelo';
  end if;
  select id into v_usr from nucleo.usuario where correo = p_correo;
  if v_usr is not null and seguridad.cuenta_bloqueada(v_usr) then
    insert into seguridad.intento_acceso (correo, usuario_id, ip, exito, motivo_fallo, agente_usuario) values (p_correo, v_usr, p_ip, false, 'cuenta_bloqueada', p_agente_usuario);
    return 'cuenta_bloqueada';
  end if;
  insert into seguridad.intento_acceso (correo, usuario_id, ip, exito, motivo_fallo, agente_usuario)
  values (p_correo, v_usr, p_ip, p_exito, case when not p_exito then coalesce(p_motivo, case when v_usr is null then 'usuario_inexistente' else 'contrasena' end) end, p_agente_usuario);
  if p_exito then return 'permitido'; end if;
  -- Fuerza bruta contra una cuenta
  r := seguridad.regla('fuerza_bruta_cuenta');
  if r.id is not null and v_usr is not null then
    select count(*) into v_n from seguridad.intento_acceso where correo = p_correo and not exito and ocurrido_en > now() - make_interval(mins => r.ventana_min);
    if v_n >= r.umbral then
      insert into seguridad.bloqueo (tipo, usuario_id, regla_id, motivo, hasta) values ('cuenta', v_usr, r.id, format('%s intentos fallidos en %s minutos', v_n, r.ventana_min), now() + make_interval(mins => r.bloqueo_min));
      insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, usuario_id, ip, detalle)
      values ('fuerza_bruta', r.severidad, 'app', r.id, v_usr, p_ip, jsonb_build_object('intentos', v_n));
      return 'cuenta_bloqueada_ahora';
    end if;
  end if;
  -- Relleno de credenciales: muchas cuentas distintas desde la misma IP
  r := seguridad.regla('relleno_credenciales');
  if r.id is not null then
    select count(distinct correo) into v_n from seguridad.intento_acceso where ip = p_ip and not exito and ocurrido_en > now() - make_interval(mins => r.ventana_min);
    if v_n >= r.umbral then
      insert into seguridad.bloqueo (tipo, ip, regla_id, motivo, hasta) values ('ip', p_ip::cidr, r.id, format('%s cuentas distintas fallidas en %s minutos', v_n, r.ventana_min), now() + make_interval(mins => r.bloqueo_min));
      insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, ip, detalle)
      values ('relleno_credenciales', r.severidad, 'app', r.id, p_ip, jsonb_build_object('cuentas', v_n));
      return 'ip_bloqueada_ahora';
    end if;
  end if;
  return 'rechazado';
end $$;
comment on function seguridad.registrar_intento(text, inet, boolean, text, text) is 'Detector de ataques: registra el intento, bloquea IPs y cuentas por fuerza bruta, relleno de credenciales o señuelos, y crea la alerta. La API lo llama en cada inicio de sesión';

create or replace function seguridad.requiere_doble_factor(p_usuario bigint) returns boolean language sql stable security definer set search_path = pg_catalog, nucleo as $$
  select exists (select 1 from nucleo.usuario_rol ur join nucleo.rol r on r.id = ur.rol_id where ur.usuario_id = p_usuario and r.codigo in ('administrador', 'contador'))
      or coalesce((select es_superusuario from nucleo.usuario where id = p_usuario), false) $$;
comment on function seguridad.requiere_doble_factor(bigint) is 'Administrador, contador y superusuario entran siempre con doble factor (mira los roles de todas las fincas)';

create or replace function seguridad.validar_sesion() returns trigger language plpgsql as $$
begin
  if seguridad.cuenta_bloqueada(new.usuario_id) then raise exception 'La cuenta % está bloqueada', new.usuario_id; end if;
  if seguridad.ip_bloqueada(new.ip) then raise exception 'La IP % está bloqueada', new.ip; end if;
  if seguridad.requiere_doble_factor(new.usuario_id) and new.metodo not in ('doble_factor', 'llave_acceso') then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, usuario_id, ip) values ('sesion_sin_doble_factor', 'alta', 'base_datos', new.usuario_id, new.ip);
    raise exception 'Este usuario debe entrar con doble factor';
  end if;
  if new.vence_en > new.iniciada_en + interval '12 hours' then raise exception 'Una sesión dura como máximo 12 horas'; end if;
  return new;
end $$;
create trigger tg_sesion_validar before insert on seguridad.sesion_usuario for each row execute function seguridad.validar_sesion();

create or replace function seguridad.revocar_sesiones(p_usuario bigint, p_motivo text) returns integer language plpgsql as $$
declare v_n integer;
begin
  update seguridad.sesion_usuario set revocada_en = now(), motivo_revocacion = p_motivo where usuario_id = p_usuario and revocada_en is null and vence_en > now();
  get diagnostics v_n = row_count;
  return v_n;
end $$;

create or replace function seguridad.vigilar_privilegios() returns trigger language plpgsql as $$
declare v_rol text;
begin
  if tg_table_name = 'usuario_rol' then
    select codigo into v_rol from nucleo.rol where id = new.rol_id;
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, usuario_id, predio_id, detalle)
    values ('escalada_privilegios', case when v_rol in ('administrador', 'contador') then 'alta' else 'baja' end, 'base_datos', new.usuario_id, new.predio_id,
            jsonb_build_object('rol', v_rol, 'otorgado_por', nucleo.usuario_actual(), 'agente', nucleo.agente_actual()));
  elsif tg_table_name = 'rol_permiso' then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, detalle)
    values ('cambio_permisos', 'media', 'base_datos', jsonb_build_object('operacion', tg_op, 'rol_id', coalesce(new.rol_id, old.rol_id),
            'permiso_id', coalesce(new.permiso_id, old.permiso_id), 'por', nucleo.usuario_actual()));
  elsif tg_table_name = 'usuario' and new.es_superusuario and not old.es_superusuario then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, usuario_id, detalle)
    values ('escalada_privilegios', 'critica', 'base_datos', new.id, jsonb_build_object('superusuario', true, 'por', nucleo.usuario_actual()));
  end if;
  return null;
end $$;
create trigger tg_usuario_rol_vigilar after insert on nucleo.usuario_rol for each row execute function seguridad.vigilar_privilegios();
create trigger tg_rol_permiso_vigilar after insert or delete on nucleo.rol_permiso for each row execute function seguridad.vigilar_privilegios();
create trigger tg_usuario_vigilar after update of es_superusuario on nucleo.usuario for each row execute function seguridad.vigilar_privilegios();

create or replace function seguridad.vigilar_exportaciones() returns trigger language plpgsql as $$
declare r seguridad.regla_deteccion; v_n integer;
begin
  if new.accion <> 'exportar' or new.usuario_id is null then return null; end if;
  r := seguridad.regla('exportacion_masiva');
  if r.id is null then return null; end if;
  select count(*) into v_n from nucleo.auditoria where accion = 'exportar' and usuario_id = new.usuario_id and ocurrido_en > now() - make_interval(mins => r.ventana_min);
  if v_n >= r.umbral and not exists (select 1 from seguridad.alerta_seguridad a where a.tipo = 'exportacion_masiva' and a.usuario_id = new.usuario_id
                                       and a.ocurrido_en > now() - make_interval(mins => r.ventana_min)) then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, usuario_id, predio_id, detalle)
    values ('exportacion_masiva', r.severidad, 'base_datos', r.id, new.usuario_id, new.predio_id, jsonb_build_object('exportaciones', v_n, 'minutos', r.ventana_min));
    if r.respuesta = 'revocar_sesiones' then perform seguridad.revocar_sesiones(new.usuario_id, 'Exportación masiva'); end if;
  end if;
  return null;
end $$;
create trigger tg_auditoria_exportaciones after insert on nucleo.auditoria for each row execute function seguridad.vigilar_exportaciones();

create or replace function seguridad.proteger_alerta() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then raise exception 'Las alertas de seguridad no se borran'; end if;
  if (to_jsonb(new) - array['estado', 'atendida_por', 'incidente_id', 'actualizado_en']) <> (to_jsonb(old) - array['estado', 'atendida_por', 'incidente_id', 'actualizado_en']) then
    raise exception 'De una alerta solo se registra su atención';
  end if;
  if new.estado <> old.estado then new.atendida_por := coalesce(new.atendida_por, nucleo.usuario_actual()); end if;
  return new;
end $$;
create trigger tg_alerta_proteger before update or delete on seguridad.alerta_seguridad for each row execute function seguridad.proteger_alerta();
create trigger tg_intento_inmutable before update or delete on seguridad.intento_acceso for each row execute function nucleo.impedir_cambio();
create trigger tg_ejecucion_prueba_inmutable before update or delete on seguridad.ejecucion_prueba for each row execute function nucleo.impedir_cambio();

create or replace function seguridad.revisar_copias() returns integer language plpgsql as $$
declare v_n integer := 0;
begin
  if not exists (select 1 from seguridad.copia_seguridad where alcance = 'postgresql' and exitosa and inicio > now() - interval '26 hours') then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, detalle) values ('copia_fallida', 'alta', 'monitoreo', '{"motivo": "sin copia exitosa de PostgreSQL en 26 horas"}');
    v_n := v_n + 1;
  end if;
  if not exists (select 1 from seguridad.copia_seguridad where restauracion_probada_en > now() - interval '35 days') then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, detalle) values ('copia_fallida', 'media', 'monitoreo', '{"motivo": "sin prueba de restauración en 35 días"}');
    v_n := v_n + 1;
  end if;
  return v_n;
end $$;
comment on function seguridad.revisar_copias() is 'Tarea diaria: alerta si no hubo copia cifrada exitosa en 26 horas o si no se probó una restauración en el último mes';

create or replace view seguridad.v_tablero as
select (select count(*) from seguridad.alerta_seguridad where ocurrido_en > now() - interval '24 hours') as alertas_24h,
       (select count(*) from seguridad.alerta_seguridad where estado = 'nueva' and severidad in ('alta', 'critica')) as alertas_graves_sin_atender,
       (select count(*) from seguridad.bloqueo where levantado_por is null and (hasta is null or hasta > now())) as bloqueos_activos,
       (select count(*) from seguridad.intento_acceso where not exito and ocurrido_en > now() - interval '24 hours') as accesos_fallidos_24h,
       (select count(*) from seguridad.incidente where estado <> 'cerrado') as incidentes_abiertos,
       (select max(ejecutada_en) from seguridad.ejecucion_prueba where fallidas = 0) as ultima_prueba_limpia,
       (select max(restauracion_probada_en) from seguridad.copia_seguridad) as ultima_restauracion_probada;

-- ============================================================================
-- 25. CRM: captura con autorización, calificación, conversión y embudo
-- ============================================================================
create or replace function crm.consentimiento_vigente(p_consentimiento bigint) returns boolean language sql stable as $$
  select exists (select 1 from terceros.consentimiento_datos where id = p_consentimiento and otorgado and revocado_en is null) $$;

create or replace function crm.validar_prospecto() returns trigger language plpgsql as $$
begin
  if new.tipo = 'persona' and (new.telefono is not null or new.correo is not null) and not crm.consentimiento_vigente(new.consentimiento_id) then
    raise exception 'Los datos de contacto de una persona solo se guardan con su autorización (Ley 1581)';
  end if;
  if new.etapa = 'ganado' and not exists (select 1 from terceros.cliente where tercero_id = new.tercero_id) then
    raise exception 'Para ganar el prospecto conviértalo en cliente (crm.convertir_prospecto)';
  end if;
  if new.etapa = 'perdido' and new.motivo_perdida is null then raise exception 'Registre por qué se perdió el prospecto'; end if;
  return new;
end $$;
create trigger tg_prospecto_validar before insert or update on crm.prospecto for each row execute function crm.validar_prospecto();

create or replace function crm.validar_interaccion() returns trigger language plpgsql as $$
declare p crm.prospecto;
begin
  if new.prospecto_id is not null and new.tipo in ('llamada', 'whatsapp', 'correo') then
    select * into p from crm.prospecto where id = new.prospecto_id;
    if p.tipo = 'persona' and not crm.consentimiento_vigente(p.consentimiento_id) then
      raise exception 'No se contacta a una persona sin su autorización vigente';
    end if;
    if p.tipo = 'empresa' and p.telefono is null and p.correo is null
       and not exists (select 1 from crm.contacto_empresa c where c.prospecto_id = p.id and crm.consentimiento_vigente(c.consentimiento_id)) then
      raise exception 'La empresa no tiene un canal de contacto autorizado';
    end if;
  end if;
  if new.prospecto_id is not null then
    update crm.prospecto set etapa = 'contactado' where id = new.prospecto_id and etapa = 'nuevo';
  end if;
  return new;
end $$;
create trigger tg_interaccion_validar before insert on crm.interaccion for each row execute function crm.validar_interaccion();

create or replace function crm.calificar(p_prospecto bigint) returns smallint language plpgsql as $$
declare p crm.prospecto; v integer := 0; v_ref numeric := coalesce(nucleo.parametro_valor('volumen_referencia_prospecto'), 1000000);
begin
  select * into p from crm.prospecto where id = p_prospecto;
  if crm.consentimiento_vigente(p.consentimiento_id) or p.tipo = 'empresa' then v := v + 20; end if;
  if p.sector in ('restaurante', 'hotel', 'supermercado', 'distribuidor', 'casino', 'colegio', 'exportador') then v := v + 20; end if;
  v := v + least(30, round(coalesce(p.volumen_estimado_mes, 0) / v_ref * 30))::integer;
  if exists (select 1 from crm.interaccion i where i.prospecto_id = p.id and i.fecha > now() - interval '30 days') then v := v + 15; end if;
  if p.etapa in ('calificado', 'propuesta', 'negociacion') then v := v + 15; end if;
  update crm.prospecto set puntaje = least(v, 100) where id = p_prospecto;
  return least(v, 100);
end $$;
comment on function crm.calificar(bigint) is 'Puntaje simple y explicable: autorización, sector, volumen estimado, contacto reciente y etapa';

create or replace function crm.convertir_prospecto(p_prospecto bigint, p_segmento text) returns bigint language plpgsql as $$
declare p crm.prospecto; v_ter bigint;
begin
  select * into p from crm.prospecto where id = p_prospecto for update;
  v_ter := p.tercero_id;
  -- Una persona con autorización ya tiene tercero desde la captura (la autorización se guarda a nombre del titular)
  if v_ter is null then
    insert into terceros.tercero (tipo_persona, tipo_documento, numero_documento, nombres, razon_social, correo, telefono, es_cliente)
    values (case p.tipo when 'empresa' then 'juridica' else 'natural' end, case when p.nit is not null then 'NIT' end, p.nit,
            case when p.tipo = 'persona' then p.nombre end, case when p.tipo = 'empresa' then p.nombre end, p.correo, p.telefono, true)
    returning id into v_ter;
  else
    update terceros.tercero set es_cliente = true where id = v_ter;
  end if;
  insert into terceros.cliente (tercero_id, segmento) values (v_ter, p_segmento) on conflict do nothing;
  update crm.prospecto set tercero_id = v_ter, etapa = 'ganado' where id = p_prospecto;
  return v_ter;
end $$;
comment on function crm.convertir_prospecto(bigint, text) is 'Convierte el prospecto en tercero y cliente (si ya tenía tercero por su autorización, lo reutiliza)';

create or replace view crm.v_embudo as
select etapa, count(*) as prospectos, sum(volumen_estimado_mes) as volumen_estimado_mes, round(avg(puntaje), 1) as puntaje_promedio
from crm.prospecto group by etapa;

create or replace view crm.v_campanas as
select c.id, c.nombre, c.canal, c.costo_real, count(p.id) as prospectos, count(p.id) filter (where p.etapa = 'ganado') as clientes_ganados,
       round(c.costo_real / nullif(count(p.id), 0), 0) as costo_por_prospecto,
       round(c.costo_real / nullif(count(p.id) filter (where p.etapa = 'ganado'), 0), 0) as costo_por_cliente
from crm.campana c left join crm.prospecto p on p.campana_id = c.id group by c.id;

create or replace view crm.v_proyeccion_ventas as
select date_trunc('month', cierre_estimado)::date as mes, count(*) as oportunidades, sum(valor_estimado) as valor_total,
       round(sum(valor_estimado * probabilidad_pct / 100.0), 0) as valor_ponderado
from crm.oportunidad where estado = 'abierta' group by 1;

-- ============================================================================
-- 26. Estrategia: evaluación de proyectos (VPN, TIR, ROI, palancas) y reinversión de utilidades
-- ============================================================================
create or replace function estrategia.vpn(p_tasa_periodo numeric, p_flujos numeric[]) returns numeric language sql immutable as $$
  select round(sum(f / power(1 + p_tasa_periodo, t - 1)), 2) from unnest(p_flujos) with ordinality x(f, t) $$;
comment on function estrategia.vpn(numeric, numeric[]) is 'Valor presente neto; el primer flujo es el periodo 0 (inversión)';

create or replace function estrategia.tir(p_flujos numeric[]) returns numeric language plpgsql immutable as $$
declare lo numeric := -0.99; hi numeric := 10; mid numeric; f_lo numeric; f_mid numeric; i integer;
begin
  f_lo := estrategia.vpn(lo, p_flujos);
  if sign(f_lo) = sign(estrategia.vpn(hi, p_flujos)) then return null; end if;
  for i in 1 .. 200 loop
    mid := (lo + hi) / 2; f_mid := (select sum(f / power(1 + mid, t - 1)) from unnest(p_flujos) with ordinality x(f, t));
    if abs(f_mid) < 0.01 then exit; end if;
    if sign(f_mid) = sign(f_lo) then lo := mid; f_lo := f_mid; else hi := mid; end if;
  end loop;
  return round(mid, 6);
end $$;
comment on function estrategia.tir(numeric[]) is 'Tasa interna de retorno por periodo (bisección); vacía si los flujos no cambian de signo';

create or replace function estrategia.evaluar_proyecto(p_evaluacion bigint) returns numeric language plpgsql as $$
declare e estrategia.evaluacion_proyecto; v_flujos numeric[]; v_tm numeric; v_tir numeric; v_acum numeric := 0; v_rec smallint; v_net numeric; pl record; i integer;
begin
  select * into e from estrategia.evaluacion_proyecto where id = p_evaluacion;
  if not exists (select 1 from estrategia.flujo_proyecto where evaluacion_id = e.id) then
    if e.precio_unitario is null or e.unidades_mes is null then raise exception 'Cargue los flujos o los datos de precio, costo y volumen'; end if;
    insert into estrategia.flujo_proyecto (evaluacion_id, mes, inversion) values (e.id, 0, e.inversion_inicial);
    insert into estrategia.flujo_proyecto (evaluacion_id, mes, ingresos, egresos)
    select e.id, m, e.precio_unitario * e.unidades_mes, coalesce(e.costo_variable_unitario, 0) * e.unidades_mes + coalesce(e.costos_fijos_mes, 0) + e.intereses_mes
    from generate_series(1, e.horizonte_meses) m;
  end if;
  select array_agg(ingresos - egresos - inversion order by mes) into v_flujos from estrategia.flujo_proyecto where evaluacion_id = e.id;
  v_tm := power(1 + e.tasa_descuento_anual, 1.0 / 12) - 1;
  v_tir := estrategia.tir(v_flujos);
  for i in 1 .. array_length(v_flujos, 1) loop
    v_acum := v_acum + v_flujos[i];
    if v_rec is null and i > 1 and v_acum >= 0 then v_rec := i - 1; end if;
  end loop;
  v_net := v_acum;
  select * into pl from finanzas.palancas(e.unidades_mes, e.precio_unitario, coalesce(e.costo_variable_unitario, 0), coalesce(e.costos_fijos_mes, 0), e.intereses_mes);
  update estrategia.evaluacion_proyecto set
    vpn = estrategia.vpn(v_tm, v_flujos),
    tir_anual = case when v_tir is not null then round(power(1 + v_tir, 12) - 1, 4) end,
    roi_pct = case when e.inversion_inicial > 0 then round(v_net / e.inversion_inicial * 100, 2) end,
    recuperacion_meses = v_rec, punto_equilibrio_unidades = pl.punto_equilibrio_unidades, margen_seguridad_pct = pl.margen_seguridad_pct,
    gpo = pl.gpo, gpf = pl.gpf, gpt = pl.gpt, calculado_en = now()
  where id = e.id;
  return estrategia.vpn(v_tm, v_flujos);
end $$;
comment on function estrategia.evaluar_proyecto(bigint) is 'Calcula VPN (a la tasa de oportunidad), TIR anual, ROI neto, meses de recuperación, punto de equilibrio, margen de seguridad y grados de palanca de una iniciativa';

create or replace function estrategia.validar_iniciativa() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' and nucleo.agente_actual() is not null then
    new.agente_id := coalesce(new.agente_id, nucleo.agente_actual());
    if new.estado <> 'idea' then raise exception 'Un agente solo propone ideas'; end if;
  end if;
  if new.estado in ('aprobada', 'piloto', 'escalada') and (tg_op = 'INSERT' or old.estado not in ('aprobada', 'piloto', 'escalada')) then
    perform nucleo.exigir_persona('aprobar iniciativas de negocio');
    if not exists (select 1 from estrategia.evaluacion_proyecto where iniciativa_id = new.id and calculado_en is not null) then
      raise exception 'Una iniciativa se aprueba con su evaluación financiera calculada (VPN, TIR, ROI)';
    end if;
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual()); new.aprobada_en := now();
  end if;
  return new;
end $$;
create trigger tg_iniciativa_validar before insert or update on estrategia.iniciativa for each row execute function estrategia.validar_iniciativa();

create or replace function estrategia.utilidad_linea(p_linea bigint, p_anio integer, p_mes integer) returns numeric language plpgsql stable as $$
declare v_cc bigint; v_desde date := make_date(p_anio, p_mes, 1);
begin
  select centro_costo_id into v_cc from estrategia.linea_negocio where id = p_linea;
  if v_cc is null then raise exception 'La línea % no tiene centro de costo', p_linea; end if;
  return (finanzas.estado_resultados(v_desde, (v_desde + interval '1 month - 1 day')::date, v_cc)->>'utilidad_neta')::numeric;
end $$;
comment on function estrategia.utilidad_linea(bigint, integer, integer) is 'Utilidad neta de una línea en un mes, tomada de la contabilidad por centro de costo';

create or replace function estrategia.validar_reinversion() returns trigger language plpgsql as $$
declare v_tope numeric := coalesce(nucleo.parametro_valor('tope_reinversion_pct'), 30); v_usado numeric; v_estado text;
begin
  if tg_op = 'UPDATE' and old.estado in ('ejecutada', 'cancelada') then raise exception 'La reinversión % ya está %', old.id, old.estado; end if;
  new.utilidad_linea := estrategia.utilidad_linea(new.linea_origen_id, new.anio, new.mes);
  if new.utilidad_linea <= 0 then raise exception 'No se reinvierte desde una línea con pérdida o sin utilidad en %-%', new.anio, new.mes; end if;
  select coalesce(sum(valor), 0) into v_usado from estrategia.reinversion
  where linea_origen_id = new.linea_origen_id and anio = new.anio and mes = new.mes and estado <> 'cancelada' and id is distinct from new.id;
  if new.estado <> 'cancelada' and v_usado + new.valor > round(new.utilidad_linea * v_tope / 100, 0) then
    raise exception 'La reinversión supera el tope: % %% de la utilidad (% de %)', v_tope, v_usado + new.valor, new.utilidad_linea;
  end if;
  if new.estado in ('aprobada', 'ejecutada') and (tg_op = 'INSERT' or old.estado = 'propuesta') then
    perform nucleo.exigir_persona('aprobar reinversiones');
    select estado into v_estado from estrategia.iniciativa where id = new.iniciativa_id;
    if v_estado not in ('aprobada', 'piloto', 'escalada') then raise exception 'Solo se reinvierte en una iniciativa aprobada'; end if;
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
  end if;
  return new;
end $$;
create trigger tg_reinversion_validar before insert or update on estrategia.reinversion for each row execute function estrategia.validar_reinversion();

create or replace view estrategia.v_retorno_iniciativas as
select i.id, i.titulo, i.ansoff, i.palanca, i.estado, ev.inversion_inicial, ev.vpn, ev.tir_anual, ev.roi_pct as roi_proyectado_pct,
       (select coalesce(sum(valor), 0) from estrategia.reinversion r where r.iniciativa_id = i.id and r.estado in ('aprobada', 'ejecutada')) as reinvertido,
       s.ingresos, s.egresos, s.meses,
       case when ev.inversion_inicial > 0 and s.meses > 0 then round((s.ingresos - s.egresos - ev.inversion_inicial) / ev.inversion_inicial * 100, 2) end as roi_real_pct
from estrategia.iniciativa i
left join lateral (select * from estrategia.evaluacion_proyecto e where e.iniciativa_id = i.id order by e.version desc limit 1) ev on true
left join lateral (select coalesce(sum(ingresos_reales), 0) ingresos, coalesce(sum(egresos_reales), 0) egresos, count(*) meses
                   from estrategia.seguimiento_iniciativa where iniciativa_id = i.id) s on true;
comment on view estrategia.v_retorno_iniciativas is 'Retorno proyectado contra real de cada iniciativa y cuánto se le ha reinvertido';

create or replace view estrategia.v_matriz_lineas as
select l.id, l.codigo, l.nombre, l.estado, l.palanca_dominante,
       (finanzas.estado_resultados(date_trunc('year', current_date)::date, current_date, l.centro_costo_id)->>'ingresos_operacionales')::numeric as ingresos_anio,
       (finanzas.estado_resultados(date_trunc('year', current_date)::date, current_date, l.centro_costo_id)->>'margen_contribucion')::numeric as margen_contribucion_anio,
       (finanzas.estado_resultados(date_trunc('year', current_date)::date, current_date, l.centro_costo_id)->>'utilidad_neta')::numeric as utilidad_anio
from estrategia.linea_negocio l where l.centro_costo_id is not null;
comment on view estrategia.v_matriz_lineas is 'Cada sección de la finca con su ingreso, margen de contribución y utilidad del año: muestra qué líneas generan recursos para reinvertir y cuáles están subsidiadas';

-- ============================================================================
-- 27. Áreas de responsabilidad y cronograma de trabajo flexible 24/7
-- ============================================================================
create or replace function nucleo.parametro_texto(p_clave text, p_fecha date default current_date) returns text language sql stable as $$
  select par.valor from nucleo.parametro par
  where par.clave = p_clave and (par.predio_id = nucleo.predio_actual() or par.predio_id is null)
    and par.vigente_desde <= p_fecha and (par.vigente_hasta is null or par.vigente_hasta >= p_fecha)
  order by par.predio_id nulls last, par.vigente_desde desc limit 1 $$;

create or replace function personal.es_miembro_area(p_empleado bigint, p_area bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from personal.miembro_area m where m.empleado_id = p_empleado and m.area_id = p_area
                 and m.desde <= p_fecha and (m.hasta is null or m.hasta >= p_fecha)) $$;
create or replace function personal.es_responsable_area(p_usuario bigint, p_area bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from personal.miembro_area m join terceros.empleado e on e.id = m.empleado_id
                 where m.area_id = p_area and m.es_responsable and e.tercero_id = nucleo.tercero_de_usuario(p_usuario)
                   and m.desde <= p_fecha and (m.hasta is null or m.hasta >= p_fecha)) $$;

create or replace function personal.turno_rango(p_fecha date, p_inicio time, p_fin time) returns tsrange language sql immutable as $$
  select tsrange(p_fecha + p_inicio, case when p_fin <= p_inicio then p_fecha + 1 + p_fin else p_fecha + p_fin end) $$;
comment on function personal.turno_rango(date, time, time) is 'Rango real del turno: si la salida es menor o igual a la entrada, termina al día siguiente (turnos de noche)';

create or replace function personal.validar_turno() returns trigger language plpgsql as $$
declare v_desc numeric := coalesce(nucleo.parametro_valor('descanso_minimo_entre_turnos_horas'), 10);
        v_max numeric := coalesce(nucleo.parametro_valor('jornada_maxima_diaria_horas'), 11); v_r tsrange; v_otro record;
begin
  if new.tipo = 'descanso' then new.horas := 0; return new; end if;
  v_r := personal.turno_rango(new.fecha, new.hora_inicio, new.hora_fin);
  new.horas := round(extract(epoch from upper(v_r) - lower(v_r)) / 3600.0, 2);
  if new.horas > v_max then raise exception 'El turno de % horas supera la jornada máxima diaria de % horas', new.horas, v_max; end if;
  if exists (select 1 from personal.ausencia a where a.empleado_id = new.empleado_id and new.fecha between a.desde and a.hasta) then
    raise exception 'El trabajador % tiene una ausencia el %', new.empleado_id, new.fecha;
  end if;
  for v_otro in select t.* from personal.turno t where t.empleado_id = new.empleado_id and t.id is distinct from new.id and t.tipo <> 'descanso'
                  and t.fecha between new.fecha - 2 and new.fecha + 2 loop
    if personal.turno_rango(v_otro.fecha, v_otro.hora_inicio, v_otro.hora_fin) && v_r then
      raise exception 'El turno se cruza con otro del mismo trabajador el %', v_otro.fecha;
    end if;
    if extract(epoch from greatest(lower(v_r) - upper(personal.turno_rango(v_otro.fecha, v_otro.hora_inicio, v_otro.hora_fin)),
                                   lower(personal.turno_rango(v_otro.fecha, v_otro.hora_inicio, v_otro.hora_fin)) - upper(v_r))) / 3600.0 < v_desc then
      raise exception 'Entre dos turnos debe haber al menos % horas de descanso', v_desc;
    end if;
  end loop;
  return new;
end $$;
create trigger tg_turno_validar before insert or update on personal.turno for each row execute function personal.validar_turno();

-- Disponible = vinculado, sin ausencia y sin turno de descanso ese día
create or replace function personal.empleado_disponible(p_empleado bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from terceros.empleado e where e.id = p_empleado and e.fecha_ingreso <= p_fecha
                 and (e.fecha_retiro is null or e.fecha_retiro >= p_fecha))
     and not exists (select 1 from personal.ausencia a where a.empleado_id = p_empleado and p_fecha between a.desde and a.hasta)
     and not exists (select 1 from personal.turno t where t.empleado_id = p_empleado and t.fecha = p_fecha and t.tipo = 'descanso') $$;

create or replace function personal.validar_area_tarea() returns trigger language plpgsql as $$
declare v_fuera bigint;
begin
  if new.area_id is null and new.plantilla_tarea_id is not null then
    select area_id into new.area_id from personal.plantilla_tarea where id = new.plantilla_tarea_id;
  end if;
  if new.area_id is not null and new.empleado_id is not null
     and (tg_op = 'INSERT' or new.empleado_id is distinct from old.empleado_id or new.area_id is distinct from old.area_id)
     and not personal.es_miembro_area(new.empleado_id, new.area_id, new.fecha) then
    raise exception 'El trabajador % no pertenece al área de responsabilidad de la tarea', new.empleado_id;
  end if;
  -- Una cuadrilla cumple la regla del área si cada miembro vigente ese día la cumple
  if new.area_id is not null and new.cuadrilla_id is not null
     and (tg_op = 'INSERT' or new.cuadrilla_id is distinct from old.cuadrilla_id or new.area_id is distinct from old.area_id or new.fecha <> old.fecha) then
    select m.empleado_id into v_fuera from personal.cuadrilla_miembro m
    where m.cuadrilla_id = new.cuadrilla_id and m.desde <= new.fecha and (m.hasta is null or m.hasta >= new.fecha)
      and not personal.es_miembro_area(m.empleado_id, new.area_id, new.fecha) limit 1;
    if v_fuera is not null then
      raise exception 'El trabajador % de la cuadrilla no pertenece al área de responsabilidad de la tarea', v_fuera;
    end if;
  end if;
  return new;
end $$;
create trigger tg_tarea_area before insert or update on personal.tarea for each row execute function personal.validar_area_tarea();

create or replace function personal.generar_turnos(p_cronograma bigint) returns integer language plpgsql as $$
declare c personal.cronograma; a record; d date; v_dia smallint; det record; v_n integer := 0; v_k integer;
begin
  select * into c from personal.cronograma where id = p_cronograma;
  if c.estado <> 'borrador' then raise exception 'El cronograma % está %: los turnos se generan en borrador', c.nombre, c.estado; end if;
  for a in select ap.*, p.tipo as tipo_patron, p.ciclo_dias from personal.asignacion_patron ap join personal.patron_turno p on p.id = ap.patron_id
           where ap.cronograma_id = p_cronograma and p.tipo <> 'flexible' loop
    d := c.desde;
    while d <= c.hasta loop
      v_dia := case when a.tipo_patron = 'semanal' then extract(isodow from d)::smallint
                    else (((d - c.desde) + a.desfase_dias) % a.ciclo_dias + 1)::smallint end;
      for det in select * from personal.patron_turno_detalle where patron_id = a.patron_id and dia_ciclo = v_dia loop
        if det.tipo <> 'descanso' and exists (select 1 from personal.ausencia x where x.empleado_id = a.empleado_id and d between x.desde and x.hasta) then
          continue;
        end if;
        insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin, tipo, area_id, cronograma_id)
        values (a.empleado_id, d, coalesce(det.hora_inicio, '00:00'), coalesce(det.hora_fin, '00:00'), det.tipo, c.area_id, c.id)
        on conflict do nothing;
        get diagnostics v_k = row_count; v_n := v_n + v_k;
      end loop;
      d := d + 1;
    end loop;
  end loop;
  return v_n;
end $$;
comment on function personal.generar_turnos(bigint) is 'Arma los turnos del cronograma desde los patrones (semanal: días y horas elegidos; cíclico: rotación 24/7 con desfase por persona). Después se ajustan a mano';

create or replace function personal.huecos_cobertura(p_cronograma bigint)
returns table (fecha date, hora time, requeridas integer, programadas integer) language sql stable as $$
  with c as (select * from personal.cronograma where id = p_cronograma),
  franjas as (
    select d::date as fecha, (h || ':00')::time as hora, max(r.personas_min) as requeridas
    from c, generate_series(c.desde, c.hasta, interval '1 day') d, generate_series(0, 23) h, personal.requerimiento_cobertura r
    where r.area_id = c.area_id and (r.dia_semana is null or r.dia_semana = extract(isodow from d))
      and (h || ':00')::time >= r.hora_inicio and (h || ':00')::time < r.hora_fin
    group by 1, 2)
  select f.fecha, f.hora, f.requeridas,
         (select count(distinct t.empleado_id) from personal.turno t, c where t.area_id = c.area_id and t.tipo <> 'descanso'
            and t.fecha between f.fecha - 1 and f.fecha and personal.turno_rango(t.fecha, t.hora_inicio, t.hora_fin) @> (f.fecha + f.hora))::integer
  from franjas f
  where f.requeridas > (select count(distinct t.empleado_id) from personal.turno t, c where t.area_id = c.area_id and t.tipo <> 'descanso'
            and t.fecha between f.fecha - 1 and f.fecha and personal.turno_rango(t.fecha, t.hora_inicio, t.hora_fin) @> (f.fecha + f.hora))
  order by 1, 2 $$;
comment on function personal.huecos_cobertura(bigint) is 'Horas del cronograma en que hay menos personas que las requeridas por el área (sirve para la operación 24/7)';

create or replace view personal.v_carga_semanal as
select t.empleado_id, date_trunc('week', t.fecha)::date as semana, sum(t.horas) as horas,
       count(*) filter (where t.tipo <> 'descanso') as dias_trabajados,
       sum(t.horas) filter (where extract(isodow from t.fecha) = 7) as horas_domingo,
       count(*) filter (where t.tipo = 'nocturno') as turnos_nocturnos
from personal.turno t group by 1, 2;
comment on view personal.v_carga_semanal is 'Horas por semana (lunes a domingo), días trabajados, horas en domingo y turnos de noche: base de recargos y del control de jornada';

create or replace function personal.publicar_cronograma() returns trigger language plpgsql as $$
declare v_max numeric; v_extra numeric; r record; v_hueco record;
begin
  if old.estado = 'cerrado' then raise exception 'El cronograma % está cerrado', old.nombre; end if;
  if new.estado = 'publicado' and old.estado = 'borrador' then
    perform nucleo.exigir_persona('publicar cronogramas');
    v_max := coalesce(nucleo.parametro_valor('jornada_maxima_semanal_horas', new.desde), 42);
    v_extra := coalesce(nucleo.parametro_valor('horas_extra_max_semana', new.desde), 12);
    for r in select t.empleado_id, date_trunc('week', t.fecha)::date semana, sum(t.horas) horas
             from personal.turno t where t.cronograma_id = new.id group by 1, 2 having sum(t.horas) > v_max + v_extra loop
      raise exception 'El trabajador % tendría % horas la semana del % (máximo % + % extra)', r.empleado_id, r.horas, r.semana, v_max, v_extra;
    end loop;
    for r in select t.empleado_id, d::date dia from personal.turno t, generate_series(new.desde, new.hasta - 6, interval '1 day') d
             where t.cronograma_id = new.id and t.tipo <> 'descanso' and t.fecha between d::date and d::date + 6
             group by 1, 2 having count(distinct t.fecha) = 7 loop
      raise exception 'El trabajador % no tendría día de descanso en los 7 días desde el %', r.empleado_id, r.dia;
    end loop;
    select * into v_hueco from personal.huecos_cobertura(new.id) limit 1;
    if v_hueco.fecha is not null and not new.permitir_huecos then
      raise exception 'Falta cobertura: el % a las % hay % de % personas requeridas', v_hueco.fecha, v_hueco.hora, v_hueco.programadas, v_hueco.requeridas;
    end if;
    new.publicado_por := nucleo.usuario_actual(); new.publicado_en := now();
  end if;
  return new;
end $$;
create trigger tg_cronograma_publicar before update on personal.cronograma for each row execute function personal.publicar_cronograma();

-- ============================================================================
-- 28. Agenda: calendario sin cruces, cabañas, visitas e ingresos y salidas
-- ============================================================================
create or replace function agenda.preparar_cita() returns trigger language plpgsql as $$
declare v_prep smallint; v_activo boolean;
begin
  select minutos_preparacion, activo into v_prep, v_activo from agenda.recurso where id = new.recurso_id;
  if not v_activo and new.estado in ('tentativa', 'confirmada') then raise exception 'El recurso no está activo'; end if;
  new.fin_con_preparacion := new.fin + make_interval(mins => coalesce(v_prep, 0));
  return new;
end $$;
create trigger tg_cita_preparar before insert or update on agenda.cita for each row execute function agenda.preparar_cita();

create or replace function agenda.recurso_libre(p_recurso bigint, p_inicio timestamptz, p_fin timestamptz) returns boolean language sql stable as $$
  select not exists (select 1 from agenda.cita c where c.recurso_id = p_recurso and c.estado in ('tentativa', 'confirmada')
                     and tstzrange(c.inicio, c.fin_con_preparacion) && tstzrange(p_inicio, p_fin)) $$;

create or replace function turismo.validar_reserva() returns trigger language plpgsql as $$
declare v_cap smallint;
begin
  if new.alojamiento_id is not null then
    select capacidad_personas into v_cap from turismo.alojamiento where id = new.alojamiento_id;
    if new.personas > v_cap then raise exception 'La cabaña admite % personas y la reserva es para %', v_cap, new.personas; end if;
  end if;
  if new.fecha_fin = new.fecha_inicio and new.alojamiento_id is not null then raise exception 'Una reserva de cabaña es de al menos una noche'; end if;
  return new;
end $$;
create trigger tg_reserva_validar before insert or update on turismo.reserva for each row execute function turismo.validar_reserva();

create or replace function turismo.sincronizar_agenda() returns trigger language plpgsql as $$
declare v_rec bigint; v_in time := coalesce(nucleo.parametro_texto('hora_checkin'), '15:00')::time; v_out time := coalesce(nucleo.parametro_texto('hora_checkout'), '12:00')::time;
        v_area bigint;
begin
  if new.alojamiento_id is null then return null; end if;
  select id into v_rec from agenda.recurso where alojamiento_id = new.alojamiento_id;
  if v_rec is null then return null; end if;
  if new.estado in ('confirmada', 'pagada') then
    begin
      if exists (select 1 from agenda.cita where reserva_id = new.id) then
        update agenda.cita set inicio = new.fecha_inicio + v_in, fin = new.fecha_fin + v_out, estado = 'confirmada' where reserva_id = new.id;
      else
        insert into agenda.cita (recurso_id, titulo, tipo, inicio, fin, reserva_id)
        values (v_rec, 'Reserva ' || new.codigo, 'reserva_turistica', new.fecha_inicio + v_in, new.fecha_fin + v_out, new.id);
      end if;
    exception when exclusion_violation then
      raise exception 'La cabaña ya está ocupada o bloqueada entre el % y el % (incluye el tiempo de limpieza)', new.fecha_inicio, new.fecha_fin;
    end;
  elsif new.estado = 'cancelada' then
    update agenda.cita set estado = 'cancelada' where reserva_id = new.id;
  elsif new.estado = 'cumplida' then
    update agenda.cita set estado = 'cumplida' where reserva_id = new.id;
  end if;
  if new.checkout_en is not null and (tg_op = 'INSERT' or old.checkout_en is null) then
    select id into v_area from personal.area_responsabilidad where codigo = 'AR-TURISMO';
    insert into personal.tarea (titulo, proceso, fecha, area_id, origen, prioridad)
    select 'Limpieza y alistamiento · ' || a.nombre, 'turismo', new.checkout_en::date, v_area, 'agenda', 'alta' from turismo.alojamiento a where a.id = new.alojamiento_id;
  end if;
  return null;
end $$;
create trigger tg_reserva_agenda after insert or update on turismo.reserva for each row execute function turismo.sincronizar_agenda();

create or replace function turismo.sincronizar_bloqueo() returns trigger language plpgsql as $$
declare v_rec bigint;
begin
  if tg_op = 'DELETE' then
    update agenda.cita set estado = 'cancelada' where bloqueo_id = old.id; return old;
  end if;
  select id into v_rec from agenda.recurso where alojamiento_id = new.alojamiento_id;
  if v_rec is null then return new; end if;
  begin
    insert into agenda.cita (recurso_id, titulo, tipo, inicio, fin, bloqueo_id)
    values (v_rec, new.motivo, 'bloqueo', new.desde::timestamptz, (new.hasta + 1)::timestamptz, new.id);
  exception when exclusion_violation then
    raise exception 'El bloqueo choca con una reserva o cita de la cabaña';
  end;
  return new;
end $$;
create trigger tg_bloqueo_agenda after insert on turismo.bloqueo_calendario for each row execute function turismo.sincronizar_bloqueo();
create trigger tg_bloqueo_agenda_borrar before delete on turismo.bloqueo_calendario for each row execute function turismo.sincronizar_bloqueo();

create or replace function agenda.validar_visita() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and old.estado in ('salio', 'rechazada', 'cancelada', 'no_llego') and new.estado <> old.estado then
    raise exception 'La visita % ya está %', old.id, old.estado;
  end if;
  if new.estado = 'aprobada' and (tg_op = 'INSERT' or old.estado = 'solicitada') then
    perform nucleo.exigir_persona('aprobar visitas');
    if new.requiere_bioseguridad and new.contacto_aves_reciente is distinct from false then
      raise exception 'Bioseguridad: quien entra al galpón declara no haber tenido contacto con otras aves en las últimas % horas',
        coalesce(nucleo.parametro_valor('cuarentena_aves_horas'), 72);
    end if;
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
  end if;
  if new.estado = 'rechazada' and new.motivo_rechazo is null then raise exception 'Registre el motivo del rechazo'; end if;
  return new;
end $$;
create trigger tg_visita_validar before insert or update on agenda.visita for each row execute function agenda.validar_visita();

create or replace function agenda.emitir_pase(p_visita bigint) returns text language plpgsql as $$
declare v_codigo text := upper(substr(encode(sha256(convert_to(random()::text || clock_timestamp()::text || p_visita::text, 'UTF8')), 'hex'), 1, 12));
begin
  if (select estado from agenda.visita where id = p_visita) <> 'aprobada' then raise exception 'Solo una visita aprobada recibe pase'; end if;
  update agenda.visita set pase_hash = encode(sha256(convert_to(v_codigo, 'UTF8')), 'hex') where id = p_visita;
  return v_codigo;
end $$;
comment on function agenda.emitir_pase(bigint) is 'Genera el código del pase (se envía al visitante como QR); la base guarda solo su huella';

create or replace function agenda.validar_acceso() returns trigger language plpgsql as $$
declare v agenda.visita; v_tol integer := coalesce(nucleo.parametro_valor('tolerancia_visita_min'), 60)::integer; v_clave text; v_jor bigint;
begin
  new.registrado_por := coalesce(new.registrado_por, nucleo.usuario_actual());
  if new.visita_id is not null then
    select * into v from agenda.visita where id = new.visita_id for update;
    if new.sentido = 'entrada' then
      if v.estado <> 'aprobada' then raise exception 'La visita no está aprobada (estado %)', v.estado; end if;
      if new.ocurrido_en < v.ingreso_programado - make_interval(mins => v_tol) or new.ocurrido_en > v.salida_programada then
        raise exception 'La visita llega fuera del horario programado';
      end if;
      if v.requiere_bioseguridad and not new.desinfeccion then raise exception 'Bioseguridad: la entrada al galpón exige desinfección de personas y vehículos'; end if;
      if new.tipo = 'vehiculo' and v.vehiculo_placa is not null and upper(coalesce(new.placa, '')) <> upper(v.vehiculo_placa) then
        raise exception 'La placa % no corresponde a la visita programada (%)', new.placa, v.vehiculo_placa;
      end if;
      update agenda.visita set estado = 'en_sitio' where id = v.id;
    else
      if v.estado <> 'en_sitio' then raise exception 'La visita no ha entrado'; end if;
      update agenda.visita set estado = 'salio' where id = v.id;
    end if;
  elsif new.empleado_id is not null then
    select id into v_jor from personal.jornada where empleado_id = new.empleado_id and fecha >= new.ocurrido_en::date - 1 and salida is null order by entrada desc limit 1;
    if new.sentido = 'entrada' then
      if v_jor is null then
        insert into personal.jornada (empleado_id, fecha, entrada, metodo_registro)
        values (new.empleado_id, new.ocurrido_en::date, new.ocurrido_en, case new.metodo when 'carne_qr' then 'qr' when 'carne_nfc' then 'nfc' else 'manual' end);
      end if;
    else
      if v_jor is null then raise exception 'No hay entrada abierta del trabajador %', new.empleado_id; end if;
      update personal.jornada set salida = new.ocurrido_en where id = v_jor;
    end if;
  elsif new.sentido = 'salida' then
    v_clave := upper(coalesce(new.placa, new.nombre));
    if not exists (select 1 from agenda.registro_acceso r where r.sentido = 'entrada' and upper(coalesce(r.placa, r.nombre)) = v_clave
                   and r.ocurrido_en::date = new.ocurrido_en::date and r.ocurrido_en < new.ocurrido_en) then
      raise exception 'No hay una entrada registrada hoy para %', v_clave;
    end if;
  end if;
  return new;
end $$;
create trigger tg_registro_acceso_validar before insert on agenda.registro_acceso for each row execute function agenda.validar_acceso();
create trigger tg_registro_acceso_inmutable before update or delete on agenda.registro_acceso for each row execute function nucleo.impedir_cambio();

create or replace view agenda.v_en_sitio as
with ultimos as (
  select distinct on (coalesce('V' || r.visita_id, 'E' || r.empleado_id, 'N' || upper(coalesce(r.placa, r.nombre))))
         r.*, coalesce('V' || r.visita_id, 'E' || r.empleado_id, 'N' || upper(coalesce(r.placa, r.nombre))) as clave
  from agenda.registro_acceso r where r.ocurrido_en > now() - interval '24 hours'
  order by coalesce('V' || r.visita_id, 'E' || r.empleado_id, 'N' || upper(coalesce(r.placa, r.nombre))), r.ocurrido_en desc)
select u.clave, u.tipo, u.visita_id, u.empleado_id, coalesce(v.nombre, u.nombre) as nombre, coalesce(u.placa, v.vehiculo_placa) as placa,
       v.zona_destino_id, u.ocurrido_en as entro_en
from ultimos u left join agenda.visita v on v.id = u.visita_id where u.sentido = 'entrada';
comment on view agenda.v_en_sitio is 'Quién y qué vehículo está dentro de la finca ahora (emergencias, robots en zonas sin personas, cierre de portería)';

create or replace view agenda.v_agenda_dia as
select 'cita' as clase, c.id, r.nombre as recurso, c.titulo, c.tipo, c.inicio, c.fin, c.estado from agenda.cita c join agenda.recurso r on r.id = c.recurso_id
union all
select 'visita', v.id, coalesce(z.nombre, 'Portería'), v.nombre || ' · ' || v.motivo, v.tipo, v.ingreso_programado, v.salida_programada, v.estado
from agenda.visita v left join nucleo.zona z on z.id = v.zona_destino_id
union all
select 'turno', t.id, coalesce(a.nombre, 'Sin área'), 'Turno trabajador ' || t.empleado_id, t.tipo, (t.fecha + t.hora_inicio)::timestamptz,
       upper(personal.turno_rango(t.fecha, t.hora_inicio, t.hora_fin))::timestamptz, 'programado'
from personal.turno t left join personal.area_responsabilidad a on a.id = t.area_id where t.tipo <> 'descanso';
comment on view agenda.v_agenda_dia is 'Agenda unificada: citas de recursos (cabañas, equipos), visitas programadas y turnos de trabajo';

-- ============================================================================
-- 29. Formación como organización educativa (ISO 21001): quejas, apelaciones y satisfacción
-- ============================================================================
create or replace function formacion.validar_queja() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    new.responder_antes := coalesce(new.responder_antes, new.presentada_en + coalesce(nucleo.parametro_valor('dias_respuesta_queja'), 15)::integer);
  end if;
  if new.estado in ('resuelta', 'rechazada') and (tg_op = 'INSERT' or old.estado not in ('resuelta', 'rechazada')) then
    perform nucleo.exigir_persona('resolver quejas y apelaciones');
    new.resuelta_por := coalesce(new.resuelta_por, nucleo.usuario_actual());
    if new.respuesta is null then raise exception 'Registre la respuesta'; end if;
    if exists (select 1 from formacion.sesion_presencial s where s.curso_id = new.curso_id and s.instructor_id = nucleo.tercero_de_usuario(new.resuelta_por)) then
      raise exception 'La queja o apelación la resuelve alguien distinto del instructor del curso';
    end if;
  end if;
  return new;
end $$;
create trigger tg_queja_validar before insert or update on formacion.queja_apelacion for each row execute function formacion.validar_queja();

create or replace view formacion.v_satisfaccion as
select c.id as curso_id, c.codigo, c.nombre, count(e.id) as respuestas, round(avg(e.satisfaccion), 2) as satisfaccion, round(avg(e.utilidad), 2) as utilidad,
       round(avg(e.instructor), 2) as instructor,
       (select count(*) from formacion.inscripcion i where i.curso_id = c.id and i.estado = 'aprobado') as aprobados,
       (select count(*) from formacion.inscripcion i where i.curso_id = c.id) as inscritos
from formacion.curso c left join formacion.encuesta e on e.curso_id = c.id group by c.id;
comment on view formacion.v_satisfaccion is 'Seguimiento de la formación: satisfacción, utilidad, instructor y tasa de aprobación por curso';

-- ============================================================================
-- 30. Proyectos (PMBOK 8): aprobación, línea base, ruta crítica, cambios, valor ganado y cierre
-- ============================================================================
create or replace function proyectos.clasificar_interesado() returns trigger language plpgsql as $$
begin
  new.estrategia := case when new.influencia >= 3 and new.interes >= 3 then 'gestionar_de_cerca' when new.influencia >= 3 then 'mantener_satisfecho'
                         when new.interes >= 3 then 'mantener_informado' else 'monitorear' end;
  return new;
end $$;
create trigger tg_interesado_clasificar before insert or update on proyectos.interesado for each row execute function proyectos.clasificar_interesado();

create or replace function proyectos.validar_proyecto() returns trigger language plpgsql as $$
declare v_ini text;
begin
  if tg_op = 'UPDATE' and old.estado in ('cerrado', 'cancelado') then raise exception 'El proyecto % está %', old.codigo, old.estado; end if;
  if tg_op = 'UPDATE' and new.estado <> old.estado then
    if new.estado = 'aprobado' then
      perform nucleo.exigir_persona('aprobar proyectos');
      if new.patrocinador_id is null or new.director_id is null or new.presupuesto is null or new.fin_plan is null or new.inicio_plan is null then
        raise exception 'El acta de constitución necesita patrocinador, director, presupuesto y fechas';
      end if;
      if nucleo.usuario_actual() <> new.patrocinador_id then raise exception 'El proyecto lo aprueba su patrocinador'; end if;
      if new.iniciativa_id is not null then
        select estado into v_ini from estrategia.iniciativa where id = new.iniciativa_id;
        if v_ini not in ('aprobada', 'piloto', 'escalada') then raise exception 'La iniciativa de negocio del proyecto no está aprobada'; end if;
      end if;
      new.aprobado_por := nucleo.usuario_actual(); new.aprobado_en := now(); new.area_enfoque := 'planificacion';
    elsif new.estado = 'en_curso' then
      if old.estado not in ('aprobado', 'suspendido') then raise exception 'Un proyecto empieza después de aprobado'; end if;
      new.inicio_real := coalesce(new.inicio_real, current_date); new.area_enfoque := 'ejecucion';
    elsif new.estado = 'cerrado' then
      perform nucleo.exigir_persona('cerrar proyectos');
      if exists (select 1 from proyectos.elemento_edt where proyecto_id = new.id and es_entregable and estado <> 'aceptado') then
        raise exception 'No se cierra: hay entregables sin aceptar';
      end if;
      if not exists (select 1 from proyectos.registro where proyecto_id = new.id and tipo = 'leccion_aprendida') then
        raise exception 'No se cierra sin registrar lecciones aprendidas';
      end if;
      new.fin_real := coalesce(new.fin_real, current_date); new.area_enfoque := 'cierre';
    end if;
  end if;
  return new;
end $$;
create trigger tg_proyecto_validar before update on proyectos.proyecto for each row execute function proyectos.validar_proyecto();

create or replace function proyectos.linea_base_inicial() returns trigger language plpgsql as $$
begin
  if new.estado = 'aprobado' and old.estado = 'propuesto' then
    insert into proyectos.linea_base (proyecto_id, version, presupuesto, fin_plan, alcance, aprobada_por)
    values (new.id, 1, new.presupuesto, new.fin_plan, new.objetivo, new.aprobado_por);
  end if;
  return null;
end $$;
create trigger tg_proyecto_linea_base after update on proyectos.proyecto for each row execute function proyectos.linea_base_inicial();
create trigger tg_linea_base_inmutable before update or delete on proyectos.linea_base for each row execute function nucleo.impedir_cambio();

create or replace function proyectos.aceptar_entregable() returns trigger language plpgsql as $$
begin
  if new.estado = 'aceptado' and old.estado <> 'aceptado' then
    perform nucleo.exigir_persona('aceptar entregables');
    if old.estado <> 'terminado' then raise exception 'Solo se acepta un entregable terminado'; end if;
    new.aceptado_por := coalesce(new.aceptado_por, nucleo.usuario_actual()); new.aceptado_en := now();
  end if;
  return new;
end $$;
create trigger tg_elemento_edt_aceptar before update on proyectos.elemento_edt for each row execute function proyectos.aceptar_entregable();

create or replace function proyectos.validar_dependencia() returns trigger language plpgsql as $$
begin
  if (select proyecto_id from proyectos.actividad where id = new.predecesora_id) <> (select proyecto_id from proyectos.actividad where id = new.sucesora_id) then
    raise exception 'Las dos actividades deben ser del mismo proyecto';
  end if;
  if exists (with recursive camino(id) as (select new.sucesora_id union select d.sucesora_id from proyectos.dependencia d join camino c on d.predecesora_id = c.id)
             select 1 from camino where id = new.predecesora_id) then
    raise exception 'La dependencia crea un ciclo en el cronograma';
  end if;
  return new;
end $$;
create trigger tg_dependencia_validar before insert or update on proyectos.dependencia for each row execute function proyectos.validar_dependencia();

create or replace function proyectos.avance_actividad() returns trigger language plpgsql as $$
begin
  if new.avance_pct > 0 then new.inicio_real := coalesce(new.inicio_real, current_date); end if;
  if new.avance_pct = 100 then new.fin_real := coalesce(new.fin_real, current_date); end if;
  return new;
end $$;
create trigger tg_actividad_avance before insert or update of avance_pct on proyectos.actividad for each row execute function proyectos.avance_actividad();

create or replace function proyectos.calcular_ruta_critica(p_proyecto bigint) returns integer language plpgsql as $$
declare v_n integer; v_fin integer; v_ini date; i integer;
begin
  select count(*) into v_n from proyectos.actividad where proyecto_id = p_proyecto;
  update proyectos.actividad set inicio_temprano = 0, fin_temprano = duracion_dias where proyecto_id = p_proyecto;
  for i in 1 .. v_n loop  -- pasada hacia adelante (relajación hasta estabilizar)
    update proyectos.actividad a set inicio_temprano = x.es, fin_temprano = x.es + a.duracion_dias
    from (select s.id, greatest(0, max(case d.tipo when 'FC' then p.fin_temprano + d.desfase_dias when 'CC' then p.inicio_temprano + d.desfase_dias
                                                   when 'FF' then p.fin_temprano + d.desfase_dias - s.duracion_dias else p.inicio_temprano + d.desfase_dias - s.duracion_dias end)) es
          from proyectos.actividad s join proyectos.dependencia d on d.sucesora_id = s.id join proyectos.actividad p on p.id = d.predecesora_id
          where s.proyecto_id = p_proyecto group by s.id) x
    where a.id = x.id and a.inicio_temprano <> x.es;
    exit when not found;
  end loop;
  select max(fin_temprano) into v_fin from proyectos.actividad where proyecto_id = p_proyecto;
  update proyectos.actividad set fin_tardio = v_fin, inicio_tardio = v_fin - duracion_dias where proyecto_id = p_proyecto;
  for i in 1 .. v_n loop  -- pasada hacia atrás
    update proyectos.actividad a set fin_tardio = x.lf, inicio_tardio = x.lf - a.duracion_dias
    from (select p.id, least(v_fin, min(case d.tipo when 'FC' then s.inicio_tardio - d.desfase_dias when 'CC' then s.inicio_tardio - d.desfase_dias + p.duracion_dias
                                                   when 'FF' then s.fin_tardio - d.desfase_dias else s.fin_tardio - d.desfase_dias + p.duracion_dias end)) lf
          from proyectos.actividad p join proyectos.dependencia d on d.predecesora_id = p.id join proyectos.actividad s on s.id = d.sucesora_id
          where p.proyecto_id = p_proyecto group by p.id) x
    where a.id = x.id and a.fin_tardio <> x.lf;
    exit when not found;
  end loop;
  select inicio_plan into v_ini from proyectos.proyecto where id = p_proyecto;
  update proyectos.actividad set holgura = inicio_tardio - inicio_temprano, critica = (inicio_tardio - inicio_temprano = 0),
         inicio_plan = case when v_ini is not null then v_ini + inicio_temprano end, fin_plan = case when v_ini is not null then v_ini + fin_temprano end
  where proyecto_id = p_proyecto;
  return v_fin;
end $$;
comment on function proyectos.calcular_ruta_critica(bigint) is 'Método de la ruta crítica (CPM) con relaciones FC, CC, FF y CF: inicio y fin tempranos y tardíos, holgura y actividades críticas; devuelve la duración en días';

create or replace function proyectos.decidir_cambio() returns trigger language plpgsql as $$
begin
  if old.estado <> 'propuesta' and new.estado <> old.estado then raise exception 'La solicitud de cambio ya fue decidida'; end if;
  if new.estado in ('aprobada', 'rechazada') and old.estado = 'propuesta' then
    perform nucleo.exigir_persona('decidir cambios');
    new.decidida_por := coalesce(new.decidida_por, nucleo.usuario_actual()); new.decidida_en := now();
    if new.decidida_por = new.solicitada_por then raise exception 'Quien pide el cambio no lo aprueba'; end if;
  end if;
  return new;
end $$;
create trigger tg_solicitud_cambio_decidir before update on proyectos.solicitud_cambio for each row execute function proyectos.decidir_cambio();

create or replace function proyectos.nueva_linea_base() returns trigger language plpgsql as $$
declare lb proyectos.linea_base;
begin
  if new.estado = 'aprobada' and old.estado = 'propuesta' then
    select * into lb from proyectos.linea_base where proyecto_id = new.proyecto_id order by version desc limit 1;
    if lb.id is null then raise exception 'El proyecto no tiene línea base: apruébelo primero'; end if;
    insert into proyectos.linea_base (proyecto_id, version, presupuesto, fin_plan, alcance, solicitud_cambio_id, aprobada_por)
    values (new.proyecto_id, lb.version + 1, lb.presupuesto + new.impacto_costo, lb.fin_plan + new.impacto_dias,
            lb.alcance || coalesce(E'\n' || new.impacto_alcance, ''), new.id, new.decidida_por);
    update proyectos.proyecto set presupuesto = lb.presupuesto + new.impacto_costo, fin_plan = lb.fin_plan + new.impacto_dias where id = new.proyecto_id;
  end if;
  return null;
end $$;
create trigger tg_solicitud_cambio_linea_base after update on proyectos.solicitud_cambio for each row execute function proyectos.nueva_linea_base();

create or replace function proyectos.calcular_valor_ganado(p_proyecto bigint, p_fecha date default current_date) returns numeric language plpgsql as $$
declare v_bac numeric; v_pv numeric; v_ev numeric; v_ac numeric; v_cpi numeric; v_spi numeric; v_eac numeric;
begin
  select presupuesto into v_bac from proyectos.proyecto where id = p_proyecto;
  select coalesce(sum(costo_plan * case when inicio_plan is null or p_fecha < inicio_plan then 0 when p_fecha >= fin_plan then 1
                                        else (p_fecha - inicio_plan)::numeric / nullif(fin_plan - inicio_plan, 0) end), 0),
         coalesce(sum(costo_plan * avance_pct / 100), 0), coalesce(sum(costo_real), 0)
    into v_pv, v_ev, v_ac from proyectos.actividad where proyecto_id = p_proyecto;
  v_cpi := round(v_ev / nullif(v_ac, 0), 4); v_spi := round(v_ev / nullif(v_pv, 0), 4); v_eac := round(v_bac / nullif(v_cpi, 0), 0);
  insert into proyectos.medicion_valor_ganado (proyecto_id, fecha_corte, pv, ev, ac, cpi, spi, eac, etc, vac)
  values (p_proyecto, p_fecha, round(v_pv, 0), round(v_ev, 0), v_ac, v_cpi, v_spi, v_eac, v_eac - v_ac, v_bac - v_eac)
  on conflict (predio_id, proyecto_id, fecha_corte) do update set pv = excluded.pv, ev = excluded.ev, ac = excluded.ac, cpi = excluded.cpi,
     spi = excluded.spi, eac = excluded.eac, etc = excluded.etc, vac = excluded.vac;
  return v_cpi;
end $$;
comment on function proyectos.calcular_valor_ganado(bigint, date) is 'Valor ganado a una fecha de corte: PV (plan lineal por actividad), EV (avance × costo plan), AC, CPI, SPI, EAC = BAC/CPI, ETC y VAC';

create or replace view proyectos.v_tablero as
select p.id, p.codigo, p.nombre, p.estado, p.area_enfoque, p.enfoque, p.presupuesto, p.fin_plan,
       round(sum(a.costo_plan * a.avance_pct) / nullif(sum(a.costo_plan), 0), 1) as avance_ponderado_pct,
       (select m.cpi from proyectos.medicion_valor_ganado m where m.proyecto_id = p.id order by m.fecha_corte desc limit 1) as cpi,
       (select m.spi from proyectos.medicion_valor_ganado m where m.proyecto_id = p.id order by m.fecha_corte desc limit 1) as spi,
       (select count(*) from proyectos.riesgo r where r.proyecto_id = p.id and r.severidad >= 15 and r.estado <> 'cerrado') as riesgos_altos,
       (select count(*) from proyectos.solicitud_cambio c where c.proyecto_id = p.id and c.estado = 'propuesta') as cambios_pendientes,
       count(a.id) filter (where a.critica and a.avance_pct < 100 and a.fin_plan < current_date) as criticas_atrasadas
from proyectos.proyecto p left join proyectos.actividad a on a.proyecto_id = p.id group by p.id;
comment on view proyectos.v_tablero is 'Tablero de proyectos: avance, CPI, SPI, riesgos altos, cambios por decidir y actividades críticas atrasadas';

-- ============================================================================
-- 31. Análisis financiero: vertical, horizontal y fuentes y usos
-- ============================================================================
create or replace function finanzas.analisis_vertical_horizontal(p_desde_a date, p_hasta_a date, p_desde_b date, p_hasta_b date)
returns table (cuenta varchar, nombre varchar, clase text, valor_a numeric, valor_b numeric, variacion numeric, variacion_pct numeric,
               vertical_a_pct numeric, vertical_b_pct numeric) language sql stable as $$
  with base as (
    select c.codigo, c.nombre, left(c.codigo, 1) clase,
           case when left(c.codigo, 1) in ('1', '2', '3') then finanzas.saldo(c.codigo, null, p_hasta_a) else finanzas.saldo(c.codigo, p_desde_a, p_hasta_a) end a,
           case when left(c.codigo, 1) in ('1', '2', '3') then finanzas.saldo(c.codigo, null, p_hasta_b) else finanzas.saldo(c.codigo, p_desde_b, p_hasta_b) end b
    from finanzas.cuenta_contable c where c.acepta_movimiento),
  tot as (select (finanzas.balance_general(p_hasta_a)->>'activo_total')::numeric ata, (finanzas.balance_general(p_hasta_b)->>'activo_total')::numeric atb,
                 finanzas.saldo('41', p_desde_a, p_hasta_a) va, finanzas.saldo('41', p_desde_b, p_hasta_b) vb)
  select b.codigo, b.nombre, b.clase, b.a, b.b, b.b - b.a, round((b.b - b.a) / nullif(abs(b.a), 0) * 100, 2),
         round(b.a / nullif(case when b.clase in ('1', '2', '3') then t.ata else t.va end, 0) * 100, 2),
         round(b.b / nullif(case when b.clase in ('1', '2', '3') then t.atb else t.vb end, 0) * 100, 2)
  from base b, tot t where b.a <> 0 or b.b <> 0 order by b.codigo $$;
comment on function finanzas.analisis_vertical_horizontal(date, date, date, date) is 'Análisis vertical (peso de cada cuenta sobre el activo total o las ventas) y horizontal (variación absoluta y relativa entre dos periodos)';

create or replace function finanzas.fuentes_usos(p_fecha_a date, p_fecha_b date)
returns table (cuenta varchar, nombre varchar, variacion numeric, clasificacion text) language sql stable as $$
  select c.codigo, c.nombre, x.var,
         case when left(c.codigo, 1) = '1' then case when x.var > 0 then 'uso' else 'fuente' end
              else case when x.var > 0 then 'fuente' else 'uso' end end
  from finanzas.cuenta_contable c
  cross join lateral (select finanzas.saldo(c.codigo, null, p_fecha_b) - finanzas.saldo(c.codigo, null, p_fecha_a) var) x
  where c.acepta_movimiento and left(c.codigo, 1) in ('1', '2', '3') and x.var <> 0 order by 4, 1 $$;
comment on function finanzas.fuentes_usos(date, date) is 'Estado de fuentes y usos: aumento de activo o disminución de pasivo y patrimonio = uso; lo contrario = fuente';

-- ============================================================================
-- 6. Índice semántico y rol de la aplicación
-- ============================================================================
create index ix_fragmento_vector on ia.fragmento_conocimiento using hnsw (vector vector_cosine_ops);

do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'guayacan_app') then
    create role guayacan_app nologin nosuperuser nobypassrls;
  end if;
end $$;
grant usage on schema nucleo, terceros, produccion, riego, inventario, comercial, compras, finanzas, ia, redes, turismo, iot, ambiental, personal, nomina, formacion, activos, documental, cumplimiento, seguros, seguridad, crm, estrategia, agenda, proyectos to guayacan_app;
grant select, insert, update, delete on all tables in schema nucleo, terceros, produccion, riego, inventario, comercial, compras, finanzas, ia, redes, turismo, iot, ambiental, personal, nomina, formacion, activos, documental, cumplimiento, seguros, seguridad, crm, estrategia, agenda, proyectos to guayacan_app;
revoke update, delete on nucleo.auditoria, comercial.huella_trazabilidad, iot.cambio_estado_alarma from guayacan_app;
grant update (anclaje_red, anclaje_transaccion, anclado_en) on comercial.huella_trazabilidad to guayacan_app;
grant execute on all functions in schema nucleo, terceros, produccion, inventario, comercial, finanzas, ia, redes, iot, ambiental,
  personal, nomina, formacion, activos, documental, cumplimiento, seguros, seguridad, crm, estrategia, agenda, proyectos to guayacan_app;
-- Seguridad: los registros de acceso, alertas y pruebas son de solo inserción para la API (la atención de alertas va por columnas)
revoke update, delete on seguridad.intento_acceso, seguridad.ejecucion_prueba, finanzas.reporte_indicadores, finanzas.aplicacion_anticipo from guayacan_app;
revoke update, delete on seguridad.alerta_seguridad from guayacan_app;
grant update (estado, atendida_por, incidente_id, actualizado_en) on seguridad.alerta_seguridad to guayacan_app;
revoke delete on seguridad.copia_seguridad, seguridad.sesion_usuario, seguridad.bloqueo, nomina.pago_nomina, personal.tarea from guayacan_app;
-- Las particiones solo se consultan por la tabla madre (así aplica la seguridad por filas)
do $$ declare r record; begin
  for r in select c.oid::regclass as t from pg_class c where c.relispartition and c.relkind in ('r', 'p') loop
    execute format('revoke all on %s from guayacan_app', r.t);
  end loop;
end $$;
comment on role guayacan_app is 'Rol de la API: sin superusuario ni BYPASSRLS, así la seguridad por filas siempre aplica';
