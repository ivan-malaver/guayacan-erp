-- GuayacanERP · Migración 011 · ADO-15: permiso para ver el tablero de adopción
-- El tablero muestra las cifras del negocio (cuotas del mes, costo de cuidado): lo ven la familia y el administrador,
-- no el adoptante con cuenta (rol cliente). La API lo exige con requiere('adopcion.ver_tablero').
-- Para bases cargadas con apendice_a_adopcion.sql anterior. Una base nueva no la necesita: el apéndice ya trae el permiso.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/011_ado15_permiso_tablero.sql
\set ON_ERROR_STOP 1
begin;

insert into nucleo.permiso (codigo, nombre, modulo)
select 'adopcion.ver_tablero', 'Ver el tablero de adopción', 'adopcion'
where not exists (select 1 from nucleo.permiso where codigo = 'adopcion.ver_tablero');

insert into nucleo.rol_permiso (rol_id, permiso_id)
select r.id, p.id from nucleo.rol r join nucleo.permiso p on p.codigo = 'adopcion.ver_tablero'
where r.codigo in ('administrador', 'familia')
  and not exists (select 1 from nucleo.rol_permiso rp where rp.rol_id = r.id and rp.permiso_id = p.id);

commit;
