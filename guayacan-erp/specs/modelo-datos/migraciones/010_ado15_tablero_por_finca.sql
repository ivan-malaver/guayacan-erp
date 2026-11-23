-- GuayacanERP · Migración 010 · ADO-15: el tablero de adopción muestra solo la finca de la sesión
-- adopcion.v_tablero se creó sin security_invoker: corría con los permisos de su dueño (postgres), que se salta la
-- seguridad por filas, y sumaba los bienes y las cuotas de todas las fincas. Con security_invoker = true respeta la
-- seguridad por filas de quien consulta, como las vistas del núcleo (inventario.v_alertas_vencimiento, comercial.v_cartera).
-- Para bases cargadas con apendice_a_adopcion.sql anterior. Una base nueva no la necesita: el apéndice ya trae el cambio.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/010_ado15_tablero_por_finca.sql
\set ON_ERROR_STOP 1
begin;

alter view adopcion.v_tablero set (security_invoker = true);

commit;
