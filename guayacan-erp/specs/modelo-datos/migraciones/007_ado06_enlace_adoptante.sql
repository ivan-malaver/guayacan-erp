-- GuayacanERP · Migración 007 · ADO-06: enlace personal del adoptante sin cuenta
-- Para bases cargadas con apendice_a_adopcion.sql anterior. Una base nueva no la necesita: el apéndice ya trae la tabla.
-- Se puede correr más de una vez.  psql -d guayacan -v ON_ERROR_STOP=1 -f specs/modelo-datos/migraciones/007_ado06_enlace_adoptante.sql
\set ON_ERROR_STOP 1
begin;

create table if not exists adopcion.enlace_adoptante (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    contrato_id bigint not null,
    token_hash char(64) not null,
    vence_en timestamptz not null,
    revocado_en timestamptz,
    ultimo_uso_en timestamptz,
    emitido_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id), unique (predio_id, token_hash),
    foreign key (predio_id, contrato_id) references adopcion.contrato(predio_id, id),
    foreign key (emitido_por) references nucleo.usuario(id)
);
comment on table adopcion.enlace_adoptante is 'Enlace personal con que el adoptante sin cuenta sigue su bien (ADO-06): la base guarda solo la huella SHA-256 del código; sirve mientras no venza, no se revoque y el contrato siga activo';

-- Las mismas convenciones del apéndice: seguridad por filas, actualizado_en y auditoría
alter table adopcion.enlace_adoptante enable row level security;
alter table adopcion.enlace_adoptante force row level security;
drop policy if exists aislamiento_predio on adopcion.enlace_adoptante;
create policy aislamiento_predio on adopcion.enlace_adoptante using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());
drop trigger if exists tg_enlace_adoptante_actualizado on adopcion.enlace_adoptante;
create trigger tg_enlace_adoptante_actualizado before update on adopcion.enlace_adoptante for each row execute function nucleo.marcar_actualizado();
drop trigger if exists tg_enlace_adoptante_auditoria on adopcion.enlace_adoptante;
create trigger tg_enlace_adoptante_auditoria after insert or update or delete on adopcion.enlace_adoptante for each row execute function nucleo.auditar();
grant select, insert, update, delete on adopcion.enlace_adoptante to guayacan_app;

commit;
