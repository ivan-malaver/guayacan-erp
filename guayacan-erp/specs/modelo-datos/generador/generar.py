"""GuayacanERP · Generador v5. Desde modelo.py produce: esquema SQL (con multi-finca, RLS, captura sin conexión y
auditoría), diccionario CSV/Markdown y diagramas ER. Las reglas de negocio escritas a mano están en reglas_negocio.sql.
Uso: python generar.py <carpeta_raiz_del_repo>"""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelo import ESQUEMAS, T, GLOBALES, CAPTURA, AUDITADAS

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
os.makedirs(f'{OUT}/specs/modelo-datos', exist_ok=True)
os.makedirs(f'{OUT}/docs/diagramas', exist_ok=True)
FASE = {1: 'Fase 1', 2: 'Fase 2', 3: 'Fase 3', 4: 'Fase 4'}
NOMBRES = {f'{t[0]}.{t[1]}' for t in T}
OPERATIVAS = NOMBRES - GLOBALES
COMUNES = ['id', 'predio_id', 'id_cliente', 'capturado_en', 'dispositivo_captura_id', 'creado_en', 'actualizado_en']


def sqltype(t):
    """Traduce la notación de tipos de modelo.py al tipo de PostgreSQL (fk: → bigint, enum: → text, dinero → numeric(14,2)...)."""
    if t.startswith('fk:'):
        return 'bigint'
    if t.startswith('fk_codigo:'):
        return 'varchar(20)'
    if t.startswith('enum:'):
        return 'text'
    if t == 'dinero':
        return 'numeric(14,2)'
    return t


def q(s):
    """Pone un texto entre comillas simples para SQL, duplicando las comillas internas (evita romper la sentencia)."""
    return "'" + s.replace("'", "''") + "'"


ddl, fks, idx, com, rls, aud = [], [], [], [], [], []
dic = []


def coment(full, col, sig):
    """Agrega la sentencia «comment on column» con el significado de la columna (queda documentado dentro de la base)."""
    com.append(f'comment on column {full}.{col} is {q(sig)};')


def fila(esq, tab, fase, col, tipo, nulo, defecto, restr, ref, sig):
    """Agrega una fila al diccionario de datos (CSV y Markdown)."""
    dic.append([esq, tab, FASE[fase], col, tipo, nulo, defecto, restr, ref, sig])


for esq, tab, fase, desc, cols, extras, aud_cols in T:
    full = f'{esq}.{tab}'
    oper = full in OPERATIVAS
    part = next((e[len('partition by range ('):-1] for e in extras if e.startswith('partition by range')), None)
    lines = ['    id bigint generated always as identity' + ('' if part else ' primary key')]
    com.append(f'comment on table {full} is {q(desc)};')
    coment(full, 'id', 'Identificador interno (número consecutivo generado por la base de datos)')
    fila(esq, tab, fase, 'id', 'bigint', 'no', 'identidad', 'llave primaria', '', 'Identificador interno (número consecutivo generado por la base de datos)')
    tcons = []
    if oper:
        lines.append('    predio_id bigint not null default nucleo.predio_actual()')
        s = 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas'
        coment(full, 'predio_id', s)
        fila(esq, tab, fase, 'predio_id', 'bigint', 'no', 'predio de la sesión', 'RLS', 'nucleo.predio', s)
        fks.append(f'alter table {full} add constraint fk_{tab}_predio foreign key (predio_id) references nucleo.predio(id);')
        if not part:
            tcons.append('unique (predio_id, id)')
        rls.append(f'alter table {full} enable row level security;\nalter table {full} force row level security;\n'
                   f'create policy aislamiento_predio on {full} using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());')
    elif full == 'nucleo.parametro':
        lines.append('    predio_id bigint')
        s = 'Finca a la que aplica; vacío = parámetro nacional para todas las fincas (ej. salario mínimo)'
        coment(full, 'predio_id', s)
        fila(esq, tab, fase, 'predio_id', 'bigint', 'sí', '', 'RLS', 'nucleo.predio', s)
        fks.append('alter table nucleo.parametro add constraint fk_parametro_predio foreign key (predio_id) references nucleo.predio(id);')
        rls.append('alter table nucleo.parametro enable row level security;\nalter table nucleo.parametro force row level security;\n'
                   'create policy leer_parametro on nucleo.parametro for select using (predio_id is null or predio_id = nucleo.predio_actual());\n'
                   'create policy escribir_parametro on nucleo.parametro for all using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());')
    elif full == 'nucleo.auditoria':
        lines.append('    predio_id bigint default nucleo.predio_actual()')
        s = 'Finca en la que ocurrió el cambio (vacío para catálogos compartidos)'
        coment(full, 'predio_id', s)
        fila(esq, tab, fase, 'predio_id', 'bigint', 'sí', 'predio de la sesión', 'RLS', 'nucleo.predio', s)
        rls.append('alter table nucleo.auditoria enable row level security;\nalter table nucleo.auditoria force row level security;\n'
                   'create policy leer_auditoria on nucleo.auditoria for select using (predio_id = nucleo.predio_actual());\n'
                   'create policy registrar_auditoria on nucleo.auditoria for insert with check (true);')
    elif full == 'nucleo.predio':
        rls.append('alter table nucleo.predio enable row level security;\nalter table nucleo.predio force row level security;\n'
                   'create policy ver_predio_actual on nucleo.predio using (id = nucleo.predio_actual());')
    for nombre, t, rest, sig in cols:
        if oper and nombre == 'predio_id':
            continue  # lo agrega el generador
        st = sqltype(t)
        r = rest
        if oper and 'unique' in r:
            r = r.replace('unique', '').replace('  ', ' ').strip()
            tcons.append(f'unique (predio_id, {nombre})')
        piece = f'    {nombre} {st}' + ((' ' + r) if r else '')
        valores = ''
        if t.startswith('enum:'):
            vals = t[5:].split(',')
            valores = ', '.join(vals)
            piece += f" constraint ck_{tab}_{nombre} check ({nombre} in ({', '.join(q(v) for v in vals)}))"
        lines.append(piece)
        ref = ''
        if t.startswith('fk:'):
            ref = t[3:]
            if oper and ref in OPERATIVAS:
                fks.append(f'alter table {full} add constraint fk_{tab}_{nombre} foreign key (predio_id, {nombre}) references {ref}(predio_id, id);')
            else:
                fks.append(f'alter table {full} add constraint fk_{tab}_{nombre} foreign key ({nombre}) references {ref}(id);')
            idx.append(f'create index ix_{tab}_{nombre} on {full} ({nombre});')
        if t.startswith('fk_codigo:'):
            ref = t[10:]
            fks.append(f'alter table {full} add constraint fk_{tab}_{nombre} foreign key ({nombre}) references {ref}(plataforma);')
        coment(full, nombre, sig + (' (valores: ' + valores + ')' if valores else ''))
        nulo = 'no' if 'not null' in rest else 'sí'
        defecto = re.search(r"default ('[^']*'|[^ ]+)", rest)
        defecto = defecto.group(1).strip("'") if defecto else ''
        otras = ', '.join(x for x in ['único por finca' if (oper and 'unique' in rest) else ('único' if 'unique' in rest else ''),
                                      ('valores: ' + valores) if valores else ''] if x)
        fila(esq, tab, fase, nombre, st if not t.startswith('enum:') else 'text (lista)', nulo, defecto, otras, ref, sig)
    if full in CAPTURA:
        lines += ['    id_cliente uuid unique', '    capturado_en timestamptz', '    dispositivo_captura_id bigint']
        extra = [('id_cliente', 'uuid', 'sí', '', 'único', '', 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)'),
                 ('capturado_en', 'timestamptz', 'sí', '', '', '', 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)'),
                 ('dispositivo_captura_id', 'bigint', 'sí', '', '', 'nucleo.dispositivo_captura', 'Celular, lector o báscula con que se capturó')]
        for c, ty, nu, de, re_, rf, s in extra:
            coment(full, c, s)
            fila(esq, tab, fase, c, ty, nu, de, re_, rf, s)
        fks.append(f'alter table {full} add constraint fk_{tab}_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);')
    if aud_cols:
        lines.append('    creado_en timestamptz not null default now()')
        lines.append('    actualizado_en timestamptz not null default now()')
        for c, s in (('creado_en', 'Fecha y hora de creación del registro'), ('actualizado_en', 'Fecha y hora de la última modificación')):
            coment(full, c, s)
            fila(esq, tab, fase, c, 'timestamptz', 'no', 'now()', '', '', s)
    if part:
        tcons.insert(0, f'primary key (id, {part})')
    for e in extras:
        if e.startswith('partition by'):
            continue
        if e.startswith('index on'):
            cols_i = e[len('index on '):]
            nm = 'ix_' + tab + '_' + re.sub(r'\W+', '_', cols_i).strip('_')
            if oper and not cols_i.startswith('(predio_id'):
                cols_i = '(predio_id, ' + cols_i[1:]
            idx.append(f'create index {nm} on {full} {cols_i};')
        elif e.startswith('unique (') and oper:
            tcons.append(e if e.startswith('unique (predio_id') else 'unique (predio_id, ' + e[len('unique ('):])
        elif e.startswith('unique (') and full == 'nucleo.parametro':
            tcons.append('unique nulls not distinct (predio_id, ' + e[len('unique ('):])
        else:
            tcons.append(e)
    lines += ['    ' + c for c in tcons]
    ddl.append(f'create table {full} (\n' + ',\n'.join(lines) + '\n)' + (f' partition by range ({part});' if part else ';'))
    if part:
        ddl.append(f"create table {full}_por_defecto partition of {full} default;\n"
                   f"select nucleo.crear_particion_mensual('{full}', (make_date(2026, 10, 1) + make_interval(months => m))::date) from generate_series(0, 14) m;")
    if full in AUDITADAS:
        aud.append(f'create trigger tg_{tab}_auditoria after insert or update or delete on {full} for each row execute function nucleo.auditar();')

reglas = open(os.path.join(AQUI, 'reglas_negocio.sql')).read()
pre, post = reglas.split('-- @@ DESPUES_DE_TABLAS @@')
head = ['-- GuayacanERP · Esquema PostgreSQL v5 para PostgreSQL 18 (generado desde modelo.py + reglas_negocio.sql; no editar a mano)',
        '-- Multi-finca con seguridad por filas, captura sin conexión idempotente, auditoría automática,',
        '-- kardex como única fuente de existencias, vencimiento estimado y salida FEFO, cuadre contable,',
        '-- cadena de frío, retiro de lotes, cartera, permuta, seguridad perimetral, cámaras y funciones por finca;',
        '-- v5: personal y cronogramas 24/7, nómina, formación, activos, documental, cumplimiento, seguros, agenda, proyectos,',
        '-- seguridad informática, CRM, estrategia y finanzas (costos, estados, indicadores, palancas).',
        'create extension if not exists citext;', 'create extension if not exists btree_gist;', 'create extension if not exists postgis;', 'create extension if not exists vector;', '']
for e, d in ESQUEMAS.items():
    head.append(f'create schema if not exists {e};')
    head.append(f'comment on schema {e} is {q(d)};')
upd = ['-- Mantener actualizado_en']
for esq, tab, fase, desc, cols, extras, a in T:
    if a:
        upd.append(f'create trigger tg_{tab}_actualizado before update on {esq}.{tab} for each row execute function nucleo.marcar_actualizado();')
sql = ('\n'.join(head) + '\n\n' + pre + '\n\n' + '\n\n'.join(ddl) + '\n\n-- Llaves foráneas (compuestas con predio_id entre tablas operativas)\n' + '\n'.join(fks) +
       '\n\n-- Índices\n' + '\n'.join(idx) + '\n\n' + '\n'.join(upd) + '\n\n-- Seguridad por filas (RLS): cada finca solo ve lo suyo\n' + '\n\n'.join(rls) +
       '\n\n' + post + '\n\n-- Auditoría automática en tablas sensibles\n' + '\n'.join(aud) + '\n\n-- Comentarios (diccionario dentro de la base)\n' + '\n'.join(com) + '\n')
open(f'{OUT}/specs/modelo-datos/esquema_postgresql.sql', 'w').write(sql)

hdr = ['esquema', 'tabla', 'fase', 'campo', 'tipo', 'admite_vacio', 'valor_por_defecto', 'restricciones', 'referencia', 'significado']
with open(f'{OUT}/specs/modelo-datos/diccionario_postgresql.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(dic)


def marcas(full):
    """Etiquetas de una tabla para el diccionario: por finca o catálogo compartido, captura sin conexión, auditada..."""
    m = []
    if full in OPERATIVAS:
        m.append('por finca')
    elif full in GLOBALES:
        m.append('catálogo compartido')
    if full in CAPTURA:
        m.append('captura sin conexión')
    if full in AUDITADAS:
        m.append('auditada')
    return ' · '.join(m)


md = ['# Diccionario de datos · PostgreSQL (v5)', '',
      'Las tablas no repiten los campos comunes; están descritos una sola vez en "Campos comunes". El CSV trae todos los campos de todas las tablas.', '',
      '## Campos comunes', '', '| Campo | Dónde está | Significado |', '| --- | --- | --- |',
      '| `id` | Todas | Identificador interno consecutivo |',
      '| `predio_id` | Tablas marcadas "por finca" | Finca dueña del registro; lo llena la base según la sesión y la seguridad por filas (RLS) impide ver o tocar otras fincas |',
      '| `id_cliente` | Tablas marcadas "captura sin conexión" | UUIDv7 generado en el celular; si el mismo registro llega dos veces, se ignora |',
      '| `capturado_en` | Tablas marcadas "captura sin conexión" | Momento en que se registró en el celular |',
      '| `dispositivo_captura_id` | Tablas marcadas "captura sin conexión" | Equipo con que se capturó (`nucleo.dispositivo_captura`) |',
      '| `creado_en`, `actualizado_en` | Casi todas | Fecha y hora de creación y de última modificación |', '']
for e, d in ESQUEMAS.items():
    tabs = [t for t in T if t[0] == e]
    md += [f'## Esquema `{e}`', '', d + '.', '']
    for esq, tab, fase, desc, cols, extras, a in tabs:
        full = f'{esq}.{tab}'
        md += [f'### `{full}` · {FASE[fase]} · {marcas(full)}', '', desc, '', '| Campo | Tipo | Vacío | Referencia | Significado |', '| --- | --- | --- | --- | --- |']
        for r in dic:
            if r[0] == esq and r[1] == tab and not (r[3] in COMUNES and (r[3] != 'dispositivo_captura_id' or full in CAPTURA)):
                sig = r[9] + (f' · valores: {r[7].split("valores: ")[1]}' if 'valores: ' in r[7] else '')
                md.append(f'| `{r[3]}` | {r[4]} | {r[5]} | {("`" + r[8] + "`") if r[8] else ""} | {sig} |')
        md.append('')
open(f'{OUT}/specs/modelo-datos/diccionario_postgresql.md', 'w').write('\n'.join(md))

# Diagramas ER por esquema
for e in ESQUEMAS:
    tabs = [t for t in T if t[0] == e]
    names = {f'{x[0]}.{x[1]}' for x in tabs}
    lines, rel, stubs = ['erDiagram'], set(), set()
    for esq, tab, fase, desc, cols, extras, a in tabs:
        lines.append(f'    {tab} {{')
        lines.append('        bigint id PK')
        if f'{esq}.{tab}' in OPERATIVAS:
            lines.append('        bigint predio_id FK')
        for n, t, rest, sig in cols:
            typ = 'bigint' if t.startswith('fk:') else ('lista' if t.startswith('enum:') else re.sub(r'\(.*', '', sqltype(t)).replace(' ', '_'))
            lines.append(f'        {typ} {n}{" FK" if t.startswith(("fk:", "fk_codigo:")) else ""}')
        lines.append('    }')
        for n, t, rest, sig in cols:
            if t.startswith(('fk:', 'fk_codigo:')):
                tgt = t.split(':', 1)[1]
                tgtname = tgt.split('.')[1] if tgt in names else tgt.replace('.', '_')
                if tgt not in names:
                    stubs.add(tgtname)
                card = '||--o|' if 'unique' in rest else '||--o{'
                rel.add(f'    {tgtname} {card} {tab} : "{n}"')
    for s in sorted(stubs):
        lines.append(f'    {s} {{\n        bigint id PK\n    }}')
    lines += sorted(rel)
    open(f'{OUT}/docs/diagramas/er_{e}.mmd', 'w').write('\n'.join(lines) + '\n')
print(len(T), 'tablas', len(dic), 'campos', len(OPERATIVAS), 'por finca', len(rls), 'políticas RLS', len(aud), 'auditadas')
