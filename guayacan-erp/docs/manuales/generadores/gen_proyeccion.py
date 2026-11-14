"""Proyección y márgenes del módulo de adopción (apéndice A). Todas las cifras calculadas con fórmulas."""
import sys

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

OUT = sys.argv[1]
F = 'Arial'
VERDE = '2E6B4F'
AZUL = Font(name=F, size=10, color='0000FF')
NEGRO = Font(name=F, size=10)
NEG_B = Font(name=F, size=10, bold=True)
VERDE_F = Font(name=F, size=10, color='008000')
CAB = Font(name=F, size=10, bold=True, color='FFFFFF')
FILL_CAB = PatternFill('solid', fgColor=VERDE)
FILL_IN = PatternFill('solid', fgColor='FFF2CC')
FILL_TOT = PatternFill('solid', fgColor='E5F0EA')
fino = Side(style='thin', color='B7C9BF')
BORDE = Border(top=fino, bottom=fino, left=fino, right=fino)
PESOS = '$#,##0;($#,##0);-'
PCT = '0.0%;(0.0%);-'
NUM = '#,##0;(#,##0);-'

wb = Workbook()


def titulo(ws, texto, sub=None):
    """Escribe el título de la hoja (A1) y, si se da, un subtítulo en A2."""
    ws['A1'] = texto
    ws['A1'].font = Font(name=F, size=14, bold=True, color=VERDE)
    if sub:
        ws['A2'] = sub
        ws['A2'].font = Font(name=F, size=9, italic=True, color='4B5563')


def cabecera(ws, fila, textos, col=1):
    """Escribe una fila de encabezados con estilo a partir de la columna indicada."""
    for i, t in enumerate(textos):
        c = ws.cell(fila, col + i, t)
        c.font, c.fill, c.border = CAB, FILL_CAB, BORDE
        c.alignment = Alignment(wrap_text=True, vertical='center', horizontal='center')


def celda(ws, ref, valor, fmt=None, entrada=False, fuente=None, nota=None, negrita=False):
    """Escribe una celda con formato. entrada=True la pinta en azul con fondo (supuesto que el usuario puede cambiar)."""
    c = ws[ref]
    c.value = valor
    c.font = AZUL if entrada else (fuente or (NEG_B if negrita else NEGRO))
    if entrada:
        c.fill = FILL_IN
    if fmt:
        c.number_format = fmt
    c.border = BORDE
    if nota:
        c.comment = Comment(nota, 'GuayacanERP')
    return c


# ----------------------------------------------------------------------------- Supuestos
S = wb.active
S.title = 'Supuestos'
titulo(S, 'Supuestos generales · módulo de adopción', 'Celdas amarillas con texto azul = entradas editables. Todo lo demás se calcula. Pesos colombianos (COP) de 2026.')
cabecera(S, 4, ['Supuesto', 'Valor', 'Fuente o justificación'])
SUP = [
    ('IVA sobre servicios (cuota de cuidado y comisión)', 0.19, PCT, 'Estatuto Tributario: tarifa general 19 %. El contador confirma si el cuidado de bienes de terceros se factura con IVA; la venta de plántulas y animales vivos se modela sin IVA (excluida)'),
    ('Costo de la pasarela de pagos (% del recaudo)', 0.035, PCT, 'Supuesto: comisión típica de pasarelas en Colombia (~2,7 % a 3,5 % más IVA y valor fijo). Ajustar al contrato con Wompi u otra'),
    ('Comisión de administración sobre la utilidad neta', 0.05, PCT, 'Decisión de la familia (5 %); parámetro comision_adopcion_pct'),
    ('Meses de mora para pasar a readopción', 3, NUM, 'Decisión de la familia; parámetro meses_abandono_adopcion'),
    ('Tasa anual de abandono (escenario base)', 0.20, PCT, 'Supuesto conservador: 1 de cada 5 adoptantes deja de pagar en el año'),
    ('Parte de los abandonos que se readopta en el año', 0.60, PCT, 'Supuesto'),
    ('Crecimiento anual de nuevas adopciones', 0.35, PCT, 'Supuesto ligado al crecimiento del turismo de la finca (fase 3)'),
    ('Mercadeo y contenido (% de los ingresos)', 0.08, PCT, 'Supuesto: pauta en redes, edición de videos, placas y certificados'),
    ('Coordinación de adopciones (fracción de un salario mínimo)', 0.25, '0.00', 'Una persona del equipo dedica 1/4 de su tiempo'),
    ('Salario mínimo mensual 2026', 1750905, PESOS, 'Decreto del Gobierno nacional para 2026; ya cargado en nucleo.parametro (salario_minimo)'),
    ('Factor prestacional y seguridad social', 1.52, '0.00', 'Supuesto: prestaciones, aportes y parafiscales sobre el salario'),
    ('Plataforma, almacenamiento de videos e IA (anual)', 1800000, PESOS, 'Supuesto: parte del VPS, MinIO y consumo de IA del módulo'),
    ('Tasa de oportunidad anual (VPN)', 0.15, PCT, 'Parámetro costo_capital_anual_pct de la v5'),
    ('Precio del huevo AA en la finca (unidad)', 650, PESOS, 'Cubeta AA de 30 a $19.500 en comercial.precio_producto de la v5'),
    ('Huevos por gallina adoptada al mes', 24, NUM, 'Supuesto: 80 % de postura promedio en su vida productiva'),
    ('Precio del ovino o caprino en pie (kg)', 11500, PESOS, 'Precio de la finca en comercial.precio_producto (COR-PIE y CAB-PIE)'),
    ('Peso al destete de una cría (kg)', 18, NUM, 'Supuesto para ovinos de pelo y caprinos mestizos'),
    ('Crías al año por hembra reproductora', 1.5, '0.0', 'Supuesto: partos cada 8 meses con 1,1 crías'),
    ('Precio del aguacate en la finca (kg)', 5000, PESOS, 'Supuesto por debajo de Corabastos (≈ $8.400/kg, SIPSA mayo de 2026) por flete e intermediación'),
    ('Tasa de cambio EUR/COP (referencia)', 4500, PESOS, 'Supuesto solo para comparar con CrowdFarming; actualice con la TRM del día'),
]
FILA = {}
for i, (n, v, fmt, fuente) in enumerate(SUP, start=5):
    celda(S, f'A{i}', n)
    celda(S, f'B{i}', v, fmt, entrada=True)
    celda(S, f'C{i}', fuente)
    S[f'C{i}'].alignment = Alignment(wrap_text=True, vertical='top')
    FILA[n] = i
S.column_dimensions['A'].width = 52
S.column_dimensions['B'].width = 16
S.column_dimensions['C'].width = 95


def sup(nombre, abs_=True):
    """Referencia absoluta a un supuesto de la hoja Supuestos por su nombre (p. ej. Supuestos!$B$7), para usar en fórmulas."""
    return f"Supuestos!$B${FILA[nombre]}"


IVA, PAS, COM = sup('IVA sobre servicios (cuota de cuidado y comisión)'), sup('Costo de la pasarela de pagos (% del recaudo)'), sup('Comisión de administración sobre la utilidad neta')
MORA = sup('Meses de mora para pasar a readopción')

# ----------------------------------------------------------------------------- Escenarios
E = wb.create_sheet('Escenarios')
titulo(E, 'Escenarios', 'Cambie el escenario activo (1 = pesimista, 2 = base, 3 = optimista). La proyección lo toma de aquí.')
celda(E, 'A4', 'Escenario activo')
celda(E, 'B4', 2, NUM, entrada=True)
cabecera(E, 6, ['Variable', 'Pesimista', 'Base', 'Optimista', 'Activo'])
ESC = [
    ('Multiplicador de volumen', 0.6, 1.0, 1.4, '0.00'),
    ('Tasa anual de abandono', 0.35, f'={sup("Tasa anual de abandono (escenario base)")}', 0.12, PCT),
    ('Parte que se readopta', 0.40, f'={sup("Parte de los abandonos que se readopta en el año")}', 0.75, PCT),
    ('Crecimiento anual', 0.15, f'={sup("Crecimiento anual de nuevas adopciones")}', 0.50, PCT),
]
for i, (n, a, b, c, fmt) in enumerate(ESC, start=7):
    celda(E, f'A{i}', n)
    celda(E, f'B{i}', a, fmt, entrada=True)
    celda(E, f'C{i}', b, fmt, fuente=VERDE_F if isinstance(b, str) else None, entrada=not isinstance(b, str))
    celda(E, f'D{i}', c, fmt, entrada=True)
    celda(E, f'E{i}', f'=INDEX(B{i}:D{i},1,$B$4)', fmt, negrita=True)
for col, w in zip('ABCDE', (30, 12, 12, 12, 12)):
    E.column_dimensions[col].width = w
VOL, ABA, READ, CREC = 'Escenarios!$E$7', 'Escenarios!$E$8', 'Escenarios!$E$9', 'Escenarios!$E$10'

# ----------------------------------------------------------------------------- Planes y márgenes unitarios
P = wb.create_sheet('Margen por adopción')
titulo(P, 'Precios, costos y margen de una adopción', 'Precios al adoptante con IVA incluido donde aplica. Costos estimados por la finca (validar con la contabilidad de costos, FIN-05).')
cols = ['Plan', 'Tipo', 'Precio de compra', 'Precio de readopción', 'Cuota mensual (IVA incl.)', 'Costo del bien y la siembra',
        'Costo de cuidado mensual', 'Meses de madurez', 'Capacidad (cupos)', 'Nuevas adopciones año 1 (base)',
        'Margen en la compra', 'Margen % compra', 'Cuota neta (sin IVA ni pasarela)', 'Margen mensual del cuidado', 'Margen % cuidado',
        'Margen del primer año por adopción', 'Margen % primer año', 'Meses para recuperar el costo del bien',
        'Salidas anuales por fin de vida', 'Años hasta producir', 'Utilidad anual liquidable por bien (del dueño)']
cabecera(P, 4, cols)
PLANES = [
    ('Frutal injertado (aguacate, mango, cítrico, cacao)', 'frutal', 150000, 60000, 25000, 56000, 9000, 48, 270, 60,
     'Plántula injertada $6.200 (vivero Eco Yuma), ahoyado, cal, abono y tutor $18.000, placa con QR $15.000, siembra 0,15 jornal $12.000, video $5.000', 0, 4, 105000),
    ('Maderable nativo (guayacán, cedro, nogal)', 'maderable', 180000, 60000, 15000, 45000, 5000, 180, 120, 25,
     'Plántula $8.000, insumos $12.000, placa $15.000, siembra $10.000. Referencia: un guayacán rosado sin siembra cuesta $102.000 (Sembramos)', 0, 99, 0),
    ('Gallina ponedora (huevos del dueño)', 'ave', 60000, 25000, 20000, 40000, 13000, 18, 150, 40,
     'Polla lista para postura $25.000 a $40.000 (referencia de mercado 2025) más anillo y placa. Cuidado: 3,5 kg de concentrado al mes y mano de obra', 0.67, 0, '=Supuestos!$B$19*12*Supuestos!$B$18*0.95'),
    ('Cordera de pelo reproductora (crías del dueño)', 'ovino', 380000, 150000, 45000, 250000, 26000, 12, 25, 8,
     'Cordera de 20 kg a $11.500/kg (precio de la finca) más arete, registro y vacunas. Cuidado: sal, desparasitación, veterinario y mano de obra', 0.10, 1, '=Supuestos!$B$22*Supuestos!$B$21*Supuestos!$B$20*0.85'),
    ('Cabrita mestiza reproductora (crías del dueño)', 'caprino', 420000, 160000, 45000, 280000, 26000, 12, 20, 6,
     'Cabrita mestiza Saanen o Nubia; mismo esquema que la cordera', 0.10, 1, '=Supuestos!$B$22*Supuestos!$B$21*Supuestos!$B$20*0.85'),
]
for i, (n, t, pc, pr, cu, cb, cc, mm, cap, n1, nota, sal, rez, util) in enumerate(PLANES, start=5):
    celda(P, f'A{i}', n)
    celda(P, f'B{i}', t)
    celda(P, f'C{i}', pc, PESOS, entrada=True)
    celda(P, f'D{i}', pr, PESOS, entrada=True)
    celda(P, f'E{i}', cu, PESOS, entrada=True)
    celda(P, f'F{i}', cb, PESOS, entrada=True, nota=nota)
    celda(P, f'G{i}', cc, PESOS, entrada=True)
    celda(P, f'H{i}', mm, NUM, entrada=True)
    celda(P, f'I{i}', cap, NUM, entrada=True)
    celda(P, f'J{i}', n1, NUM, entrada=True)
    celda(P, f'K{i}', f'=C{i}*(1-{PAS})-F{i}', PESOS)
    celda(P, f'L{i}', f'=IF(C{i}=0,0,K{i}/C{i})', PCT)
    celda(P, f'M{i}', f'=E{i}/(1+{IVA})-E{i}*{PAS}', PESOS)
    celda(P, f'N{i}', f'=M{i}-G{i}', PESOS)
    celda(P, f'O{i}', f'=IF(M{i}=0,0,N{i}/M{i})', PCT)
    celda(P, f'P{i}', f'=K{i}+N{i}*11', PESOS, negrita=True)
    celda(P, f'Q{i}', f'=IF((C{i}*(1-{PAS})+M{i}*11)=0,0,P{i}/(C{i}*(1-{PAS})+M{i}*11))', PCT, negrita=True)
    celda(P, f'R{i}', f'=IF(N{i}<=0,"no recupera",IF(K{i}>=0,0,ROUNDUP(-K{i}/N{i},0)))', NUM)
    celda(P, f'S{i}', sal, PCT, entrada=True)
    celda(P, f'T{i}', rez, NUM, entrada=True, nota='99 = no produce dentro de los 5 años (maderable)')
    celda(P, f'U{i}', util, PESOS, entrada=not isinstance(util, str), fuente=VERDE_F if isinstance(util, str) else None,
          nota='Frutal: 30 kg en el año 4 a $5.000 menos 30 % de cosecha y venta. Gallina: huevos menos 5 % de empaque y venta. Ovino y caprino: crías al destete menos 15 % de gastos')
NP = len(PLANES)
U = 4 + NP  # última fila de planes
for c, w in zip(range(1, 22), (42, 10, 13, 13, 13, 14, 13, 10, 10, 12, 13, 10, 14, 13, 10, 15, 11, 13, 11, 10, 15)):
    P.column_dimensions[L(c)].width = w
P.row_dimensions[4].height = 58
r = U + 2
celda(P, f'A{r}', 'Comparación con la referencia internacional', negrita=True)
celda(P, f'A{r+1}', 'CrowdFarming: adopción de un olivo, € al año (incluye 5 L de aceite)')
celda(P, f'B{r+1}', 78, '#,##0', entrada=True, nota='naranjasdelcarmen.com/crowdfarming-adopt-an-olive-tree (consultado 30-oct-2026)')
celda(P, f'A{r+2}', 'Equivalente en pesos al año')
celda(P, f'B{r+2}', f'=B{r+1}*{sup("Tasa de cambio EUR/COP (referencia)")}', PESOS)
celda(P, f'A{r+3}', 'Frutal de El Guayacán: cuotas de un año')
celda(P, f'B{r+3}', '=E5*12', PESOS)
celda(P, f'A{r+4}', 'Diferencia: el frutal cuesta menos que el olivo de referencia en')
celda(P, f'B{r+4}', f'=IF(B{r+2}=0,0,1-B{r+3}/B{r+2})', PCT, negrita=True)

# ----------------------------------------------------------------------------- Proyección
Y = wb.create_sheet('Proyección 5 años')
titulo(Y, 'Proyección anual 2027-2031 (inicio con la fase 3)', 'Escenario según la hoja Escenarios. Pesos constantes de 2026, antes de impuesto de renta. Ingresos sin IVA y netos de pasarela.')
ANIOS = ['2027', '2028', '2029', '2030', '2031']
COLS = ['C', 'D', 'E', 'F', 'G']
cabecera(Y, 4, ['Concepto', 'Plan'] + ANIOS + ['Total 5 años'])
M_ = "'Margen por adopción'!"
fila = 5
BLOQUE = {}
CONCEPTOS = ['Activos al inicio', 'Nuevas adopciones', 'Abandonos', 'Readopciones', 'Salidas por fin de vida', 'Activos al cierre',
             'Activos promedio', 'Ingresos por compras y readopciones', 'Ingresos por cuidado', 'Comisión del 5 % sobre liquidaciones',
             'Costo de los bienes y la siembra', 'Costo del cuidado', 'Margen de contribución']
for i, plan in enumerate(PLANES):
    p = 5 + i
    celda(Y, f'A{fila}', plan[0], negrita=True)
    Y[f'A{fila}'].fill = FILL_TOT
    fila += 1
    r = {c: fila + k for k, c in enumerate(CONCEPTOS)}
    BLOQUE[i] = r
    for c in CONCEPTOS:
        fmt = NUM if c in CONCEPTOS[:7] else PESOS
        celda(Y, f'A{r[c]}', c, negrita=(c == 'Margen de contribución'))
        celda(Y, f'B{r[c]}', plan[1])
        for j, col in enumerate(COLS):
            pc = COLS[j - 1] if j else None
            f = {
                'Activos al inicio': '=0' if j == 0 else f'={pc}{r["Activos al cierre"]}',
                'Nuevas adopciones': f'=MAX(0,MIN(ROUND({M_}$J${p}*{VOL}*(1+{CREC})^{j},0),{M_}$I${p}-{col}{r["Activos al inicio"]}))',
                'Abandonos': f'=ROUND({col}{r["Activos al inicio"]}*{ABA},0)',
                'Readopciones': f'=ROUND({col}{r["Abandonos"]}*{READ},0)',
                'Salidas por fin de vida': f'=ROUND(({col}{r["Activos al inicio"]}+{col}{r["Nuevas adopciones"]}/2)*{M_}$S${p},0)',
                'Activos al cierre': f'={col}{r["Activos al inicio"]}+{col}{r["Nuevas adopciones"]}-{col}{r["Abandonos"]}+{col}{r["Readopciones"]}-{col}{r["Salidas por fin de vida"]}',
                'Activos promedio': f'=({col}{r["Activos al inicio"]}+{col}{r["Activos al cierre"]})/2',
                'Ingresos por compras y readopciones': f'=({col}{r["Nuevas adopciones"]}*{M_}$C${p}+{col}{r["Readopciones"]}*{M_}$D${p})*(1-{PAS})',
                'Ingresos por cuidado': f'=MAX(0,{col}{r["Activos promedio"]}*12-{col}{r["Abandonos"]}*{MORA})*{M_}$M${p}',
                'Comisión del 5 % sobre liquidaciones': (
                    f'=IF({M_}$T${p}=0,{col}{r["Activos promedio"]},IF({j}<{M_}$T${p},0,OFFSET({col}{r["Activos al cierre"]},0,-{M_}$T${p})))'
                    f'*{M_}$U${p}*{COM}/(1+{IVA})'),
                'Costo de los bienes y la siembra': f'={col}{r["Nuevas adopciones"]}*{M_}$F${p}',
                'Costo del cuidado': f'={col}{r["Activos promedio"]}*12*{M_}$G${p}',
                'Margen de contribución': f'={col}{r["Ingresos por compras y readopciones"]}+{col}{r["Ingresos por cuidado"]}+{col}{r["Comisión del 5 % sobre liquidaciones"]}-{col}{r["Costo de los bienes y la siembra"]}-{col}{r["Costo del cuidado"]}',
            }[c]
            celda(Y, f'{col}{r[c]}', f, fmt, negrita=(c == 'Margen de contribución'))
        if fmt == PESOS:
            celda(Y, f'H{r[c]}', f'=SUM(C{r[c]}:G{r[c]})', PESOS, negrita=(c == 'Margen de contribución'))
        elif c == 'Nuevas adopciones' or c == 'Readopciones' or c == 'Abandonos':
            celda(Y, f'H{r[c]}', f'=SUM(C{r[c]}:G{r[c]})', NUM)
    fila = r['Margen de contribución'] + 2

# Consolidado
celda(Y, f'A{fila}', 'Consolidado del módulo', negrita=True)
Y[f'A{fila}'].fill = FILL_TOT
fila += 1
TOT = {}


def suma(concepto, col):
    """Fórmula que suma un concepto a través de todos los bloques de productos en la columna dada."""
    return '=' + '+'.join(f'{col}{BLOQUE[i][concepto]}' for i in range(NP))


filas_cons = [
    ('Adoptantes activos al cierre', lambda col: suma('Activos al cierre', col), NUM),
    ('Ingresos totales', lambda col: '=' + '+'.join(f'{col}{BLOQUE[i][c]}' for i in range(NP) for c in ('Ingresos por compras y readopciones', 'Ingresos por cuidado', 'Comisión del 5 % sobre liquidaciones')), PESOS),
    ('   de los cuales, comisión del 5 %', lambda col: suma('Comisión del 5 % sobre liquidaciones', col), PESOS),
    ('Costos variables (bienes y cuidado)', lambda col: '=' + '+'.join(f'{col}{BLOQUE[i][c]}' for i in range(NP) for c in ('Costo de los bienes y la siembra', 'Costo del cuidado')), PESOS),
    ('Margen de contribución', lambda col: f'={col}{{ING}}-{col}{{CV}}', PESOS),
    ('Margen de contribución %', lambda col: f'=IF({col}{{ING}}=0,0,{col}{{MC}}/{col}{{ING}})', PCT),
    ('Mercadeo y contenido', lambda col: f'={col}{{ING}}*{sup("Mercadeo y contenido (% de los ingresos)")}', PESOS),
    ('Coordinación de adopciones', lambda col: f'={sup("Salario mínimo mensual 2026")}*{sup("Factor prestacional y seguridad social")}*{sup("Coordinación de adopciones (fracción de un salario mínimo)")}*12', PESOS),
    ('Plataforma, videos e IA', lambda col: f'={sup("Plataforma, almacenamiento de videos e IA (anual)")}', PESOS),
    ('Utilidad operacional (antes de renta)', lambda col: f'={col}{{MC}}-{col}{{MER}}-{col}{{COO}}-{col}{{PLA}}', PESOS),
    ('Margen operacional %', lambda col: f'=IF({col}{{ING}}=0,0,{col}{{UO}}/{col}{{ING}})', PCT),
]
claves = {'Ingresos totales': 'ING', 'Costos variables (bienes y cuidado)': 'CV', 'Margen de contribución': 'MC', 'Mercadeo y contenido': 'MER',
          'Coordinación de adopciones': 'COO', 'Plataforma, videos e IA': 'PLA', 'Utilidad operacional (antes de renta)': 'UO'}
pos = {}
for k, (n, fn, fmt) in enumerate(filas_cons):
    pos[claves.get(n, n)] = fila + k
for k, (n, fn, fmt) in enumerate(filas_cons):
    rr = fila + k
    neg = n in ('Ingresos totales', 'Margen de contribución', 'Utilidad operacional (antes de renta)', 'Margen operacional %')
    celda(Y, f'A{rr}', n, negrita=neg)
    for col in COLS:
        txt = fn(col)
        for kk, v in pos.items():
            txt = txt.replace('{' + kk + '}', str(v))
        celda(Y, f'{col}{rr}', txt, fmt, negrita=neg)
    if fmt == PESOS:
        celda(Y, f'H{rr}', f'=SUM(C{rr}:G{rr})', PESOS, negrita=neg)
    elif fmt == PCT and n.startswith('Margen'):
        num = pos['MC'] if 'contribución' in n else pos['UO']
        celda(Y, f'H{rr}', f'=IF(H{pos["ING"]}=0,0,H{num}/H{pos["ING"]})', PCT, negrita=neg)
    TOT[n] = rr
fila += len(filas_cons) + 1

# Inversión y evaluación
celda(Y, f'A{fila}', 'Inversión inicial y evaluación (2026 = año 0)', negrita=True)
Y[f'A{fila}'].fill = FILL_TOT
fila += 1
INV = [('Desarrollo del módulo (2 sprints del equipo, valorado)', 8000000), ('Cámara y estabilizador para videos', 1500000),
       ('Vivero de espera, señalización y placas iniciales', 2500000), ('Adecuación de corrales y galpón para adoptados', 3000000)]
ini = fila
for n, v in INV:
    celda(Y, f'A{fila}', n)
    celda(Y, f'B{fila}', v, PESOS, entrada=True)
    fila += 1
celda(Y, f'A{fila}', 'Inversión inicial total', negrita=True)
celda(Y, f'B{fila}', f'=SUM(B{ini}:B{fila-1})', PESOS, negrita=True)
r_inv = fila
fila += 2
cabecera(Y, fila, ['Flujo', '2026'] + ANIOS + [''])
fila += 1
celda(Y, f'A{fila}', 'Flujo de caja operativo', negrita=True)
celda(Y, f'B{fila}', f'=-B{r_inv}', PESOS)
for col in COLS:
    celda(Y, f'{col}{fila}', f'={col}{TOT["Utilidad operacional (antes de renta)"]}', PESOS)
r_fl = fila
fila += 1
celda(Y, f'A{fila}', 'Flujo acumulado')
celda(Y, f'B{fila}', f'=B{r_fl}', PESOS)
for j, col in enumerate(COLS):
    pc = 'B' if j == 0 else COLS[j - 1]
    celda(Y, f'{col}{fila}', f'={pc}{fila}+{col}{r_fl}', PESOS)
r_ac = fila
fila += 2
celda(Y, f'A{fila}', 'VPN a la tasa de oportunidad', negrita=True)
celda(Y, f'B{fila}', f'=B{r_fl}+NPV({sup("Tasa de oportunidad anual (VPN)")},C{r_fl}:G{r_fl})', PESOS, negrita=True)
r_vpn = fila
fila += 1
celda(Y, f'A{fila}', 'TIR del módulo', negrita=True)
celda(Y, f'B{fila}', f'=IFERROR(IRR(B{r_fl}:G{r_fl}),"sin TIR")', PCT, negrita=True)
r_tir = fila
fila += 1
celda(Y, f'A{fila}', 'Año en que se recupera la inversión', negrita=True)
celda(Y, f'B{fila}', f'=IFERROR(INDEX($C$4:$G$4,MATCH(TRUE,INDEX(C{r_ac}:G{r_ac}>=0,0),0)),"después de 2031")', NUM, negrita=True)
r_pay = fila
Y.column_dimensions['A'].width = 44
Y.column_dimensions['B'].width = 14
for col in COLS + ['H']:
    Y.column_dimensions[col].width = 14
Y.freeze_panes = 'C5'

# ----------------------------------------------------------------------------- Visión del adoptante
A = wb.create_sheet('Visión del adoptante')
titulo(A, 'Lo que paga y lo que recibe el adoptante en su primer año completo de producción',
       'No es una inversión: la finca no promete rendimientos. Esta hoja sirve para fijar precios justos y explicar el producto con honestidad.')
cabecera(A, 4, ['Plan', 'Compra', 'Cuotas del año (11 meses)', 'Pago total del año', 'Utilidad liquidable del bien', 'Comisión de la finca',
                'Abono al adoptante', 'Costo neto para el adoptante', 'Costo neto mensual'])
for i in range(NP):
    rr, p = 5 + i, 5 + i
    celda(A, f'A{rr}', f'={M_}A{p}', fuente=VERDE_F)
    celda(A, f'B{rr}', f'={M_}C{p}', PESOS, fuente=VERDE_F)
    celda(A, f'C{rr}', f'={M_}E{p}*11', PESOS)
    celda(A, f'D{rr}', f'=B{rr}+C{rr}', PESOS)
    celda(A, f'E{rr}', f'={M_}U{p}', PESOS, fuente=VERDE_F)
    celda(A, f'F{rr}', f'=ROUND(MAX(E{rr},0)*{COM},0)', PESOS)
    celda(A, f'G{rr}', f'=MAX(E{rr},0)-F{rr}', PESOS)
    celda(A, f'H{rr}', f'=D{rr}-G{rr}', PESOS, negrita=True)
    celda(A, f'I{rr}', f'=H{rr}/12', PESOS, negrita=True)
celda(A, f'A{6+NP}', 'Frutal: la utilidad empieza en el año 4. Maderable: el valor llega con la tala, después de 15 años. En los animales, la utilidad son los huevos o las crías del año.')
A[f'A{6+NP}'].font = Font(name=F, size=9, italic=True)
for c, w in zip('ABCDEFGHI', (42, 13, 15, 15, 16, 14, 14, 16, 14)):
    A.column_dimensions[c].width = w
A.row_dimensions[4].height = 45

# ----------------------------------------------------------------------------- Ejemplos de liquidación
X = wb.create_sheet('Ejemplos de liquidación')
titulo(X, 'Ejemplos de liquidación con la comisión del 5 %', 'Utilidad neta = ingresos − gastos directos del evento. La comisión solo se cobra si hay utilidad (adopcion.validar_liquidacion).')
cabecera(X, 4, ['Caso', 'Cantidad', 'Precio unitario', 'Ingresos', 'Gastos directos', 'Detalle de gastos', 'Utilidad neta', 'Comisión 5 %', 'Abono al adoptante'])
EJ = [
    ('Cordera sacrificada a los 13 meses (45 kg en pie)', 45, f'={sup("Precio del ovino o caprino en pie (kg)")}', 95000, 'Transporte $35.000 y planta de beneficio autorizada $60.000'),
    ('Dos crías vendidas al destete (18 kg c/u)', 36, f'={sup("Precio del ovino o caprino en pie (kg)")}', 62100, '15 %: vacunas, arete y venta'),
    ('Huevos de una gallina en un trimestre', f'={sup("Huevos por gallina adoptada al mes")}*3', f'={sup("Precio del huevo AA en la finca (unidad)")}', '=ROUND(D7*0.05,0)', '5 %: empaque y venta'),
    ('Cosecha de un aguacate en su año 5 (60 kg)', 60, f'={sup("Precio del aguacate en la finca (kg)")}', 90000, 'Recolección, selección y transporte (30 %)'),
    ('Tala de un guayacán a los 15 años (0,6 m³)', 0.6, 700000, 260000, 'Permiso de la CAR o remisión ICA, motosierrista y transporte. Precio del m³ en pie: supuesto a validar con aserríos de la zona'),
    ('Cosecha de un frutal con pérdida (año malo)', 20, f'={sup("Precio del aguacate en la finca (kg)")}', 110000, 'Plaga y transporte: sin utilidad, sin comisión'),
]
for k, (n, q, pu, g, det) in enumerate(EJ, start=5):
    celda(X, f'A{k}', n)
    celda(X, f'B{k}', q, '#,##0.0', entrada=not str(q).startswith('='))
    celda(X, f'C{k}', pu, PESOS, entrada=not str(pu).startswith('='), fuente=VERDE_F if str(pu).startswith('=') else None)
    celda(X, f'D{k}', f'=ROUND(B{k}*C{k},0)', PESOS)
    celda(X, f'E{k}', g, PESOS, entrada=not str(g).startswith('='))
    celda(X, f'F{k}', det)
    celda(X, f'G{k}', f'=D{k}-E{k}', PESOS)
    celda(X, f'H{k}', f'=ROUND(MAX(G{k},0)*{COM},0)', PESOS, negrita=True)
    celda(X, f'I{k}', f'=MAX(G{k},0)-H{k}', PESOS, negrita=True)
for c, w in zip('ABCDEFGHI', (44, 10, 13, 13, 13, 60, 13, 13, 14)):
    X.column_dimensions[c].width = w

# ----------------------------------------------------------------------------- Fuentes
R = wb.create_sheet('Fuentes')
titulo(R, 'Fuentes y referencias')
fuentes = [
    ('CrowdFarming / Naranjas del Carmen: adopción de un olivo, 78 € al año con 5 L de aceite; reposición si muere antes de 25 años', 'https://naranjasdelcarmen.com/crowdfarming-adopt-an-olive-tree'),
    ('Sembramos: árbol de guayacán rosado $102.000 (sin siembra ni seguimiento)', 'https://sembramos.com.co/arbol-guayacan-rosado.html'),
    ('Eco Yuma: plántulas frutales injertadas $5.100 a $6.200 (pedido mínimo 100)', 'https://tienda.ecoyuma.com.co/plantulas-frutales/89-aguacate-injertado.html'),
    ('Pollos Santa Mónica: pollitas $3.500-$6.000; gallinas listas para postura $25.000-$40.000 (marzo de 2025)', 'https://www.pollos-santa-monica.com/gallinas-ponedoras-precio-en-colombia/'),
    ('AvoHass: aguacate Hass en Corabastos ≈ $8.400/kg (SIPSA, mayo de 2026)', 'https://avo-hass.com/guias/precio-aguacate-hass-colombia/'),
    ('Selina Wamucii: cacao en grano en finca ≈ $30.605/kg (mayo de 2026)', 'https://www.selinawamucii.com/insights/prices/colombia/cocoa-beans/'),
    ('Superfinanciera: captación masiva y habitual, Decreto 1981 de 1988', 'https://www.superfinanciera.gov.co/publicaciones/18706'),
    ('Minambiente: concepto sobre aprovechamiento de árboles aislados en predio privado (Decreto 1076 de 2015)', 'https://www.minambiente.gov.co/wp-content/uploads/2024/09/concep_240126_001642-TRAMITE-PERMISO-APROVECHAMIENTO-FORESTAL-ARBOLES-AISLADOS-EN-PREDIO-PRIVADO.pdf'),
    ('Datos de la finca: precios, salario mínimo 2026 y tasa de oportunidad en datos_iniciales.sql de la v5', 'specs/modelo-datos/datos_iniciales.sql'),
]
for k, (t, u) in enumerate(fuentes, start=3):
    R[f'A{k}'] = t
    R[f'B{k}'] = u
    R[f'A{k}'].font = R[f'B{k}'].font = NEGRO
R.column_dimensions['A'].width = 110
R.column_dimensions['B'].width = 90

wb.move_sheet('Proyección 5 años', offset=-3)
wb.save(OUT)
print('ok', r_vpn, r_tir, r_pay, TOT)
