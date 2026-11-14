-- Prepara la base para Django DESPUÉS de cargar esquema_postgresql.sql, datos_iniciales.sql y apendice_a_adopcion.sql.
--
-- Qué hace:
--   1. Crea el usuario guayacan_api con el que entra la API. Es miembro del rol guayacan_app, que no es
--      superusuario ni tiene BYPASSRLS: así la seguridad por filas aplica siempre a la API.
--   2. Crea el esquema «django» para las tablas internas de Django (contenttypes y auth) y le da permisos a la API.
--
-- Uso (la clave es la misma que POSTGRES_API_CLAVE del archivo .env):
--   psql -U postgres -d guayacan -v ON_ERROR_STOP=1 -v clave_api="<clave>" -f backend/sql/preparar_api.sql

-- Detenerse ante el primer error
\set ON_ERROR_STOP 1

-- Crea el usuario solo si no existe. format(... %L ...) pone la clave entre comillas de forma segura y \gexec
-- ejecuta el texto que devuelve la consulta como una sentencia SQL.
select format('create role guayacan_api login password %L in role guayacan_app', :'clave_api')
where not exists (select 1 from pg_roles where rolname = 'guayacan_api') \gexec

-- Esquema de las tablas internas de Django
create schema if not exists django;
grant usage on schema django to guayacan_app;
-- Las tablas y secuencias que cree Django en ese esquema quedarán con permisos para la API
alter default privileges in schema django grant select, insert, update, delete on tables to guayacan_app;
alter default privileges in schema django grant usage, select on sequences to guayacan_app;

select 'Usuario guayacan_api y esquema django listos' as resultado;
