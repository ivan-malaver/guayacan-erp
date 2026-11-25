-- GuayacanERP · Migración 014 · VTA-03: permiso para confirmar y cancelar pedidos
-- Confirmar reserva inventario y congela precios: lo hace una persona con rol vendedor o administrador (un agente solo
-- deja el pedido en borrador). La API lo exige con requiere('comercial.confirmar_pedido').
-- Para bases cargadas con datos_iniciales.sql anterior. Una base nueva no la necesita: los datos iniciales ya traen el permiso.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/014_vta03_permiso_confirmar_pedido.sql
\set ON_ERROR_STOP 1
begin;

insert into nucleo.permiso (codigo, nombre, modulo)
select 'comercial.confirmar_pedido', 'Confirmar y cancelar pedidos', 'comercial'
where not exists (select 1 from nucleo.permiso where codigo = 'comercial.confirmar_pedido');

insert into nucleo.rol_permiso (rol_id, permiso_id)
select r.id, p.id from nucleo.rol r join nucleo.permiso p on p.codigo = 'comercial.confirmar_pedido'
where r.codigo in ('administrador', 'vendedor')
  and not exists (select 1 from nucleo.rol_permiso rp where rp.rol_id = r.id and rp.permiso_id = p.id);

commit;
