-- GuayacanERP · Migración 012 · Vistas que respetan la finca de la sesión
-- Estas 15 vistas de la v5 se crearon sin security_invoker: corrían con los permisos de su dueño (postgres), que se
-- salta la seguridad por filas, y mezclaban datos de todas las fincas. Con security_invoker = true respetan la seguridad
-- por filas de quien consulta, como las vistas de la v4 (comercial.v_cartera) y adopcion.v_tablero (migración 010).
-- La más urgente: cumplimiento.v_granja_biosegura, que PRO-01 consulta al ingresar cada lote, sumaba las aves de todas
-- las fincas y fallaba («más de una fila») en cuanto dos fincas tuvieran expediente ICA_GAB.
-- Para bases cargadas con esquema_postgresql.sql anterior. Una base nueva no la necesita: el esquema ya trae el cambio.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/012_vistas_por_finca.sql
\set ON_ERROR_STOP 1
begin;

alter view agenda.v_agenda_dia set (security_invoker = true);
alter view agenda.v_en_sitio set (security_invoker = true);
alter view crm.v_campanas set (security_invoker = true);
alter view crm.v_embudo set (security_invoker = true);
alter view crm.v_proyeccion_ventas set (security_invoker = true);
alter view cumplimiento.v_granja_biosegura set (security_invoker = true);
alter view documental.v_vigentes set (security_invoker = true);
alter view estrategia.v_matriz_lineas set (security_invoker = true);
alter view estrategia.v_retorno_iniciativas set (security_invoker = true);
alter view formacion.v_satisfaccion set (security_invoker = true);
alter view personal.v_carga_semanal set (security_invoker = true);
alter view personal.v_productividad set (security_invoker = true);
alter view proyectos.v_tablero set (security_invoker = true);
alter view seguridad.v_tablero set (security_invoker = true);
alter view seguros.v_por_vencer set (security_invoker = true);

commit;
