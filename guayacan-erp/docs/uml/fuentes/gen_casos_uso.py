"""Genera los diagramas UML de casos de uso (Graphviz) desde catalogo.py.

Salida: <destino>/casos-uso/CU_<modulo>.dot, .svg y .png, más el diagrama de actores.
Uso: python3 gen_casos_uso.py <destino>
"""
import os
import subprocess
import sys
import textwrap

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalogo import ACTORES, CU, HUMANOS, MODULOS, PREFIJO, por_modulo  # noqa: E402

DEST = os.path.join(sys.argv[1], 'casos-uso')
os.makedirs(DEST, exist_ok=True)
FUENTE = 'DejaVu Sans'
VERDE, TINTA, GRIS, IA = '#2E6B4F', '#1F2933', '#6B7280', '#7A4E9C'


def figura(ruta, color=TINTA):
    """Monigote UML de actor (PNG transparente)."""
    w, h = 60, 96
    im = Image.new('RGBA', (w, h), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((20, 4, 40, 24), outline=color, width=3)
    d.line((30, 24, 30, 58), fill=color, width=3)
    d.line((12, 36, 48, 36), fill=color, width=3)
    d.line((30, 58, 14, 88), fill=color, width=3)
    d.line((30, 58, 46, 88), fill=color, width=3)
    im.save(ruta)


ICONO = os.path.join(DEST, 'actor.png')
figura(ICONO)


def envolver(texto, ancho=26):
    """Parte un texto largo en líneas de máximo «ancho» caracteres (salto de línea de Graphviz) para que quepa en el dibujo."""
    return '\\n'.join(textwrap.wrap(texto, ancho))


def nodo_actor(cod):
    """Nodo Graphviz de un actor: figura de persona para humanos, caja punteada para agentes de IA y caja para sistemas."""
    nombre = ACTORES[cod]
    if cod in HUMANOS:
        return (f'"{cod}" [shape=none, image="{ICONO}", imagescale=false, imagepos=tc, labelloc=b, height=1.45, width=1.2, '
                f'label="{envolver(nombre, 16)}", fontsize=11, fontcolor="{TINTA}"];')
    if cod.startswith('AG_'):
        return (f'"{cod}" [shape=box, style="rounded,dashed", color="{IA}", fontcolor="{IA}", fontsize=10.5, '
                f'label="«agente IA»\\n{envolver(nombre.replace(" (IA)", ""), 18)}"];')
    return (f'"{cod}" [shape=box, color="{GRIS}", fontcolor="{TINTA}", fontsize=10.5, '
            f'label="«sistema»\\n{envolver(nombre, 18)}"];')


def caso(c, externo=False):
    """Nodo Graphviz de un caso de uso (elipse). Punteado si depende de una función por finca o si es de otro módulo."""
    flag = f'\\n[función {c["flag"]}]' if c['flag'] else ''
    if externo:
        return (f'"{c["id"]}" [shape=ellipse, style="dashed", color="{GRIS}", fontcolor="{GRIS}", fontsize=10, '
                f'label="{c["id"]}\\n{envolver(c["nombre"], 22)}\\n({MODULOS[c["modulo"]]})"];')
    estilo = 'filled' if not c['flag'] else 'filled,dashed'
    return (f'"{c["id"]}" [shape=ellipse, style="{estilo}", fillcolor="#EAF3EE", color="{VERDE}", fontcolor="{TINTA}", fontsize=10.5, '
            f'label="{c["id"]}\\n{envolver(c["nombre"])}{flag}"];')


def diagrama(modulo):
    """Dibuja el diagrama de casos de uso de un módulo: actores a la izquierda/derecha, casos al centro e include/extend."""
    casos = por_modulo(modulo)
    ids = {c['id'] for c in casos}
    todos = {c['id']: c for c in CU}
    prim, sec = [], []
    for c in casos:
        for a in c['actores']:
            if a not in prim:
                prim.append(a)
    for c in casos:
        for a in c['secundarios']:
            if a not in sec and a not in prim:
                sec.append(a)
    externos = []
    for c in casos:
        for r in c['inc']:
            if r not in ids and r not in externos:
                externos.append(r)
        for r in c['ext']:
            if r not in ids and r not in externos:
                externos.append(r)
    for c in CU:  # casos de otros módulos que extienden o incluyen a los de este
        if c['modulo'] != modulo:
            for r in c['ext']:
                pass
    L = ['digraph G {', f'graph [rankdir=LR, fontname="{FUENTE}", nodesep=0.28, ranksep=0.9, pad=0.3, bgcolor=white, '
         f'label="Casos de uso · {MODULOS[modulo]} ({PREFIJO[modulo]})", labelloc=t, fontsize=16, fontcolor="{TINTA}"];',
         f'node [fontname="{FUENTE}"]; edge [fontname="{FUENTE}", color="{GRIS}", arrowhead=none, penwidth=1.1];']
    L.append('{rank=source; ' + ' '.join(f'"{a}";' for a in prim) + '}')
    for a in prim:
        L.append(nodo_actor(a))
    L.append(f'subgraph cluster_sistema {{ label="GuayacanERP · {MODULOS[modulo]}"; fontsize=13; fontcolor="{VERDE}"; '
             f'color="{VERDE}"; penwidth=1.4; style=rounded; margin=18;')
    for c in casos:
        L.append('  ' + caso(c))
    L.append('}')
    if externos:
        L.append(f'subgraph cluster_otros {{ label="Casos de otros módulos"; fontsize=11; fontcolor="{GRIS}"; color="#C7CCD1"; style="rounded,dashed";')
        for r in externos:
            L.append('  ' + caso(todos[r], externo=True))
        L.append('}')
    if sec:
        L.append('{rank=sink; ' + ' '.join(f'"{a}";' for a in sec) + '}')
        for a in sec:
            L.append(nodo_actor(a))
    for c in casos:
        for a in c['actores']:
            L.append(f'"{a}" -> "{c["id"]}";')
        for a in c['secundarios']:
            L.append(f'"{c["id"]}" -> "{a}" [style=solid];')
        for r in c['inc']:
            k = 'true' if r not in ids else 'false'
            L.append(f'"{c["id"]}" -> "{r}" [style=dashed, arrowhead=vee, xlabel="«include»", fontsize=9.5, fontcolor="{GRIS}", constraint={k}];')
        for r in c['ext']:
            k = 'true' if r not in ids else 'false'
            if k == 'true':
                L.append(f'"{c["id"]}" -> "{r}" [style=dashed, arrowhead=none, arrowtail=vee, dir=back, xlabel="«extend»", fontsize=9.5, fontcolor="{GRIS}"];')
            else:
                L.append(f'"{r}" -> "{c["id"]}" [style=dashed, arrowhead=vee, xlabel="«extend»", fontsize=9.5, fontcolor="{GRIS}", constraint=false];')
    L.append('}')
    base = os.path.join(DEST, f'CU_{PREFIJO[modulo]}_{modulo}')
    open(base + '.dot', 'w', encoding='utf-8').write('\n'.join(L))
    for fmt in ('svg', 'png'):
        args = ['dot', f'-T{fmt}', base + '.dot', '-o', f'{base}.{fmt}']
        if fmt == 'png':
            args.insert(1, '-Gdpi=130')
        subprocess.run(args, check=True)
    return base


def _render(base, L):
    """Guarda la fuente .dot y la convierte a .svg y .png con el programa dot de Graphviz."""
    open(base + '.dot', 'w', encoding='utf-8').write('\n'.join(L))
    subprocess.run(['dot', '-Tsvg', base + '.dot', '-o', base + '.svg'], check=True)
    subprocess.run(['dot', '-Gdpi=130', '-Tpng', base + '.dot', '-o', base + '.png'], check=True)


def actores():
    """Actores humanos (generalización) y agentes de IA, en dos diagramas."""
    cab = lambda t: ['digraph A {', f'graph [rankdir=BT, fontname="{FUENTE}", nodesep=0.22, ranksep=0.8, pad=0.3, bgcolor=white, '
                     f'label="{t}", labelloc=t, fontsize=16, fontcolor="{TINTA}"];',
                     f'node [fontname="{FUENTE}"]; edge [color="{GRIS}", arrowhead=empty, penwidth=1.1];']
    L = cab('Actores humanos: todos heredan de Usuario autenticado; los de la derecha no tienen cuenta')
    personas = ['ADM', 'FAM', 'ENC', 'OPE', 'VEN', 'CON', 'CLI', 'POR', 'INS', 'EST', 'DIR']
    for a in ['USR', 'PAT'] + personas:
        L.append(nodo_actor(a))
    for a in personas:
        L.append(f'"{a}" -> "USR";')
    L.append('"PAT" -> "FAM";')
    L.append('subgraph cluster_sin {label="Sin cuenta en el sistema"; fontsize=12; color="#9CA3AF"; style="rounded,dashed";')
    for a in ['PRO', 'VIS', 'AUD', 'TIT', 'OPR']:
        L.append('  ' + nodo_actor(a))
    L.append('}')
    L.append('{rank=same; "USR"; "PRO"; "VIS"; "AUD"; "TIT"; "OPR";}')
    L.append('}')
    _render(os.path.join(DEST, 'CU_00_actores'), L)
    L = cab('Agentes de IA: actores secundarios que proponen; una persona decide')
    L.append(f'"AGT" [shape=box, style="rounded,dashed", color="{IA}", fontcolor="{IA}", fontsize=11, label="«agente IA»\\nAgente (propone, no decide)"];')
    ags = [k for k in ACTORES if k.startswith('AG_')]
    for a in ags:
        L.append(nodo_actor(a))
    for n, a in enumerate(ags):
        if n < 7:
            L.append(f'"{a}" -> "AGT" [color="{IA}"];')
        else:
            L.append(f'"{a}" -> "{ags[n - 7]}" [style=invis];')
            L.append(f'"{a}" -> "AGT" [color="{IA}", constraint=false];')
    L.append('}')
    _render(os.path.join(DEST, 'CU_00_agentes'), L)


if __name__ == '__main__':
    actores()
    for m in MODULOS:
        print(diagrama(m))
