"""Diagramas UML estructurales generados del modelo de datos v5.

- clases/CL_<modulo>.mmd (+ .svg, .png): diagrama de clases por módulo (Mermaid) con atributos, multiplicidades
  y las clases de otros módulos a las que apunta, agrupadas aparte.
- paquetes/PK_dependencias.dot (+ .svg, .png): diagrama de paquetes con las dependencias entre esquemas (llaves foráneas).
Uso: python3 gen_estructura.py <generador del modelo> <destino>
"""
import collections
import os
import subprocess
import sys

sys.path.insert(0, sys.argv[1])
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelo import ESQUEMAS, GLOBALES, T  # noqa: E402
from catalogo import MODULOS, PREFIJO  # noqa: E402

DEST = sys.argv[2]
for d in ('clases', 'paquetes'):
    os.makedirs(os.path.join(DEST, d), exist_ok=True)
COMUNES = {'id', 'predio_id', 'id_cliente', 'capturado_en', 'dispositivo_captura_id', 'creado_en', 'actualizado_en'}
MAX_ATR = 12
MMDC_CFG = os.path.join(DEST, 'mermaid.json')
open(MMDC_CFG, 'w').write('{"theme":"neutral","themeVariables":{"fontFamily":"DejaVu Sans","fontSize":"14px"},'
                          '"class":{"useMaxWidth":false},"flowchart":{"useMaxWidth":false},"sequence":{"useMaxWidth":false}}')


def tipo_corto(t):
    """Nombre corto y en español de un tipo de columna para mostrar en el diagrama de clases (ref, enum, texto...)."""
    if t.startswith('fk:'):
        return 'ref ' + t[3:].split('.')[1]
    if t.startswith('enum:'):
        return 'enum'
    for a, b in (('varchar', 'texto'), ('numeric', 'decimal'), ('timestamptz', 'momento'), ('char(64)', 'huella')):
        if t.startswith(a):
            return b
    return t.split(' ')[0].replace('[]', ' lista')


def nombre_clase(full):
    """Nombre válido para Mermaid de una tabla: 'esquema.tabla' → 'esquema__tabla'."""
    return full.replace('.', '__')


def partes(modulo, maximo=9):
    """Divide un módulo grande en grupos de tablas conectadas por llaves foráneas (para que el diagrama se lea)."""
    tablas = [t for t in T if t[0] == modulo]
    nombres = [f'{t[0]}.{t[1]}' for t in tablas]
    if len(tablas) <= maximo + 2:
        return [nombres]
    vecinos = collections.defaultdict(set)
    for t in tablas:
        full = f'{t[0]}.{t[1]}'
        for c in t[4]:
            if c[1].startswith('fk:') and c[1][3:] in nombres and c[1][3:] != full and c[1][3:] != 'nucleo.usuario':
                vecinos[full].add(c[1][3:])
                vecinos[c[1][3:]].add(full)
    pendientes, grupos = list(nombres), []
    while pendientes:
        semilla = max(pendientes, key=lambda n: len(vecinos[n] & set(pendientes)))
        grupo, cola = [], [semilla]
        while cola and len(grupo) < maximo:
            n = cola.pop(0)
            if n in grupo or n not in pendientes:
                continue
            grupo.append(n)
            cola += sorted(vecinos[n] - set(grupo), key=lambda v: -len(vecinos[v]))
        for n in grupo:
            pendientes.remove(n)
        grupos.append(grupo)
    # une grupos sueltos pequeños
    final = []
    for g in grupos:
        if final and len(g) <= 2 and len(final[-1]) + len(g) <= maximo + 2:
            final[-1] += g
        else:
            final.append(g)
    return final


def medida_svg(ruta):
    """Lee el ancho y alto de un SVG (atributo viewBox) para decidir si el diagrama quedó demasiado ancho."""
    import re
    txt = open(ruta, encoding='utf-8').read(4000)
    m = re.search(r'viewBox="[-0-9.]+ [-0-9.]+ ([0-9.]+) ([0-9.]+)"', txt)
    return (float(m.group(1)), float(m.group(2))) if m else (1600, 1200)


def dibujar(base, lineas_sin_dir):
    """Dibuja el diagrama de clases de arriba a abajo; si queda más del doble de ancho que de alto, lo repite de izquierda a derecha."""
    for direccion in ('TB', 'LR'):
        L = ['classDiagram', f'  direction {direccion}'] + lineas_sin_dir
        open(base + '.mmd', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        subprocess.run(['mmdc', '-q', '-i', base + '.mmd', '-o', base + '.svg', '-c', MMDC_CFG, '-b', 'white'], check=True, capture_output=True)
        w, h = medida_svg(base + '.svg')
        if w <= 2.0 * h or direccion == 'LR':
            break
        w2, h2 = w, h
    ancho = int(min(max(w, 600), 2600)) + 40
    subprocess.run(['mmdc', '-q', '-i', base + '.mmd', '-o', base + '.png', '-c', MMDC_CFG, '-b', 'white', '-w', str(ancho), '-s', '1'],
                   check=True, capture_output=True)
    return w, h


def clases(modulo):
    """Genera los diagramas de clases de un módulo (en partes si es grande), con atributos, relaciones y clases externas."""
    salida = []
    grupos = partes(modulo)
    info = {f'{t[0]}.{t[1]}': t for t in T}
    for n, grupo in enumerate(grupos, 1):
        propias = set(grupo)
        L, rel, externas = [], [], set()
        for full in grupo:
            esq, tab, fase, desc, cols, extras, aud = info[full]
            L.append(f'  class {nombre_clase(full)}["{tab}"] {{')
            L.append('    <<compartida>>' if full in GLOBALES else f'    <<por finca · fase {fase}>>')
            visibles = [c for c in cols if c[0] not in COMUNES]
            for c in visibles[:MAX_ATR]:
                req = '' if 'not null' in c[2] else '?'
                L.append(f'    +{c[0]}{req} : {tipo_corto(c[1])}')
            if len(visibles) > MAX_ATR:
                L.append(f'    +… {len(visibles) - MAX_ATR} campos más')
            L.append('  }')
            for c in cols:
                if not c[1].startswith('fk:'):
                    continue
                dest = c[1][3:]
                if dest == 'nucleo.usuario' and modulo not in ('nucleo', 'seguridad'):
                    continue  # quién hizo algo: se deja como atributo para no saturar el diagrama
                if dest == full:
                    rel.append(f'  {nombre_clase(full)} "*" --> "0..1" {nombre_clase(full)} : {c[0]}')
                    continue
                if dest not in propias:
                    externas.add(dest)
                mult = '1' if 'not null' in c[2] else '0..1'
                uno = '"0..1"' if 'unique' in c[2] else '"*"'
                rel.append(f'  {nombre_clase(full)} {uno} --> "{mult}" {nombre_clase(dest)} : {c[0]}')
        porm = collections.defaultdict(list)
        for e in sorted(externas):
            porm[e.split('.')[0] if e.split('.')[0] != modulo else f'{modulo}_otra_parte'].append(e)
        for m, lista in porm.items():
            L.append(f'  namespace {m} {{')
            for e in lista:
                L.append(f'    class {nombre_clase(e)}["{e}"]')
            L.append('  }')
        L += rel
        for e in externas:
            L.append(f'  style {nombre_clase(e)} fill:#F3F4F6,stroke:#9CA3AF,stroke-dasharray:4 3')
        sufijo = f'_{n}' if len(grupos) > 1 else ''
        base = os.path.join(DEST, 'clases', f'CL_{PREFIJO[modulo]}_{modulo}{sufijo}')
        w, h = dibujar(base, L)
        salida.append((os.path.basename(base), len(grupo), int(w), int(h)))
    return salida


def paquetes():
    """Genera el diagrama de paquetes: una flecha de un esquema a otro por cada grupo de llaves foráneas entre ellos."""
    dep = collections.Counter()
    for esq, tab, fase, desc, cols, extras, aud in T:
        for c in cols:
            if c[1].startswith('fk:'):
                d = c[1][3:].split('.')[0]
                if d != esq:
                    dep[(esq, d)] += 1
    capas = [
        ('Plataforma', ['nucleo', 'seguridad', 'terceros', 'documental']),
        ('Operación de campo', ['produccion', 'riego', 'iot', 'ambiental', 'personal', 'activos', 'agenda']),
        ('Abastecimiento y ventas', ['inventario', 'compras', 'comercial', 'crm', 'redes', 'turismo']),
        ('Personas y conocimiento', ['formacion', 'nomina', 'cumplimiento', 'seguros']),
        ('Dinero, estrategia e IA', ['finanzas', 'estrategia', 'proyectos', 'ia']),
    ]
    L = ['digraph P {', 'graph [rankdir=TB, fontname="DejaVu Sans", nodesep=0.35, ranksep=0.9, pad=0.3, bgcolor=white, compound=true, '
         'label="Paquetes de GuayacanERP y sus dependencias (llaves foráneas entre esquemas; el número es cuántas)", labelloc=t, fontsize=16];',
         'node [fontname="DejaVu Sans", shape=tab, style=filled, fillcolor="#EAF3EE", color="#2E6B4F", fontsize=12];',
         'edge [fontname="DejaVu Sans", color="#9CA3AF", arrowhead=vee, style=dashed, fontsize=9, fontcolor="#6B7280"];']
    for i, (nom, mods) in enumerate(capas):
        L.append(f'subgraph cluster_{i} {{ label="{nom}"; style=rounded; color="#C7CCD1"; fontsize=12; fontcolor="#1F2933";')
        for m in mods:
            n = sum(1 for t in T if t[0] == m)
            L.append(f'  "{m}" [label="{m}\\n{MODULOS[m]}\\n{n} tablas"];')
        L.append('}')
    for (a, b), n in sorted(dep.items()):
        peso = 2 if n >= 5 else 1
        col = '#4B5563' if b in ('nucleo', 'terceros') else '#9CA3AF'
        L.append(f'"{a}" -> "{b}" [xlabel="{n}", penwidth={peso}, color="{col}"];')
    L.append('}')
    base = os.path.join(DEST, 'paquetes', 'PK_dependencias')
    open(base + '.dot', 'w', encoding='utf-8').write('\n'.join(L))
    subprocess.run(['dot', '-Tsvg', base + '.dot', '-o', base + '.svg'], check=True)
    subprocess.run(['dot', '-Gdpi=120', '-Tpng', base + '.dot', '-o', base + '.png'], check=True)
    return dep


if __name__ == '__main__':
    dep = paquetes()
    print('dependencias entre paquetes:', len(dep))
    for m in (sys.argv[3:] or ESQUEMAS):
        print(clases(m))
