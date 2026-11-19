-- GuayacanERP · Migración 002 · AGD-04: correcciones en portería (4b)
-- Para bases cargadas con esquema_postgresql.sql anterior. Una base nueva no la necesita: el esquema ya trae estas columnas.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/002_agd04_registro_acceso_correccion.sql
\set ON_ERROR_STOP 1
begin;

-- Los registros de acceso no se editan: un error de digitación se corrige con un registro nuevo que dice cuál corrige
alter table agenda.registro_acceso add column if not exists observacion varchar(200);
alter table agenda.registro_acceso add column if not exists corrige_id bigint;
alter table agenda.registro_acceso drop constraint if exists fk_registro_acceso_corrige_id;
alter table agenda.registro_acceso add constraint fk_registro_acceso_corrige_id foreign key (predio_id, corrige_id) references agenda.registro_acceso(predio_id, id);
create index if not exists ix_registro_acceso_corrige_id on agenda.registro_acceso (corrige_id);
comment on column agenda.registro_acceso.observacion is 'Novedad o motivo de la corrección (los registros no se editan: se corrige con uno nuevo)';
comment on column agenda.registro_acceso.corrige_id is 'Registro que este corrige (error de digitación)';

commit;
