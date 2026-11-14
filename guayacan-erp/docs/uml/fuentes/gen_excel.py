"""Genera el Excel de trazabilidad (GuayacanERP_Trazabilidad_v5.2.xlsx) desde el catálogo de casos de uso.

QUÉ HACE: hojas de casos de uso, actores, requerimientos y matrices (requerimiento × caso, caso × tabla) con
fórmulas COUNTIF para que los totales se recalculen si edita el Excel.
PARA QUÉ: demostrar que cada requerimiento tiene casos de uso, tablas, reglas, API y pruebas que lo cumplen.
USO: python -I docs/uml/fuentes/gen_excel.py docs/uml/fuentes <archivo_salida.xlsx>
"""
import sys,os,re
sys.path.insert(0,sys.argv[1])
import catalogo as C
from fichas import ruta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
OUT=sys.argv[2]; BACK=sys.argv[3]
F='Arial'; VERDE='2E6B4F'
cab=Font(name=F,bold=True,color='FFFFFF'); fill=PatternFill('solid',fgColor=VERDE)
norm=Font(name=F,size=9); fino=Side(style='thin',color='B7C9BF'); borde=Border(top=fino,bottom=fino,left=fino,right=fino)
wb=Workbook()
def hoja(nombre, cols, filas, anchos, primero=False):
    """Crea una hoja de Excel con encabezado verde, filas con bordes y texto ajustado, y los anchos de columna dados."""
    ws=wb.active if primero else wb.create_sheet()
    ws.title=nombre; ws.append(cols)
    for c in ws[1]: c.font=cab; c.fill=fill; c.alignment=Alignment(wrap_text=True,vertical='center')
    for f in filas: ws.append(f)
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font=norm; c.alignment=Alignment(wrap_text=True,vertical='top'); c.border=borde
    for i,w in enumerate(anchos,1): ws.column_dimensions[get_column_letter(i)].width=w
    ws.freeze_panes='B2'; ws.auto_filter.ref=ws.dimensions
    return ws
# Leeme
ws=wb.active; ws.title='Leeme'
txt=['GuayacanERP · Trazabilidad v5.1 (29 de octubre de 2026)','',
 'Generado desde docs/uml/fuentes/catalogo.py y backend/apps/*/urls.py. No se edita a mano: si cambia un caso de uso, regenere con docs/uml/fuentes/gen_excel.py.','',
 'Hojas:','Casos de uso: los 177 con actores, requerimientos, tablas, reglas en la base, endpoints, pruebas y relaciones.',
 'Requerimientos: RF, RNF y RQ con el número de casos de uso que los cubren (fórmula). Cero = lo cubren la arquitectura y las convenciones.',
 'Resumen por módulo: casos de uso por fase y cuántos tienen prueba (fórmulas sobre la hoja Casos de uso).',
 'Endpoints: rutas de acción del esqueleto y su estado (501 por construir o ya implementada).',
 'Actores: cuántos casos de uso tiene cada actor como primario y como secundario (fórmulas).']
for t in txt: ws.append([t])
ws['A1'].font=Font(name=F,bold=True,size=14,color=VERDE)
for r in ws.iter_rows(min_row=2):
    for c in r: c.font=Font(name=F,size=10)
ws.column_dimensions['A'].width=130
cus=[c for m in C.MODULOS for c in C.por_modulo(m)]
filas=[]
for c in cus:
    filas.append([c['id'],c['nombre'],C.MODULOS[c['modulo']],C.PREFIJO[c['modulo']],c['fase'],c['flag'] or 'siempre activa',
      '; '.join(C.ACTORES[a] for a in c['actores']), '; '.join(C.ACTORES[a] for a in c['secundarios']) or '—',
      ', '.join(c['rf']), '\n'.join(c['tablas']), '\n'.join(c['reglas']) or 'formato y permisos de DRF',
      '\n'.join(c['acciones']) or 'CRUD: '+', '.join(ruta(t) for t in c['tablas'] if t.split('.')[0]==c['modulo'])[:300],
      ', '.join(p.replace(':',' ') for p in c['pruebas']) or 'pendiente', ', '.join(c['inc']) or '—', ', '.join(c['ext']) or '—',
      'Sí' if c['pruebas'] else 'No'])
hoja('Casos de uso',['ID','Caso de uso','Módulo','Prefijo','Fase','Función','Actores primarios','Actores secundarios','Requerimientos','Tablas','Reglas en la base','Endpoints','Pruebas existentes','Incluye','Extendido por','¿Tiene prueba?'],filas,[9,38,24,8,6,18,26,26,18,30,34,40,22,12,12,10])
n=len(filas)+1
req=[[k,v,f'=COUNTIF(\'Casos de uso\'!$I$2:$I${n},"*"&A{i}&"*")'] for i,(k,v) in enumerate(C.REQUERIMIENTOS.items(),start=2)]
w=hoja('Requerimientos',['ID','Requerimiento','Casos de uso que lo cubren'],req,[10,60,16])
w.append([]); w.append(['','Total requerimientos sin caso de uso (cubiertos por arquitectura)',f'=COUNTIF(C2:C{len(req)+1},0)'])
for c in w[w.max_row]: c.font=Font(name=F,bold=True,size=9)
mods=[[C.PREFIJO[m],t]+[f'=COUNTIFS(\'Casos de uso\'!$D$2:$D${n},$A{i},\'Casos de uso\'!$E$2:$E${n},{f})' for f in (1,2,3,4)]+[f'=SUM(C{i}:F{i})',f'=COUNTIFS(\'Casos de uso\'!$D$2:$D${n},$A{i},\'Casos de uso\'!$P$2:$P${n},"Sí")',f'=IF(G{i}=0,0,H{i}/G{i})'] for i,(m,t) in enumerate(C.MODULOS.items(),start=2)]
w=hoja('Resumen por módulo',['Prefijo','Módulo','Fase 1','Fase 2','Fase 3','Fase 4','Total','Con prueba','% con prueba'],mods,[9,32,8,8,8,8,8,10,12])
k=len(mods)+2
w.append(['','Total']+[f'=SUM({get_column_letter(j)}2:{get_column_letter(j)}{k-1})' for j in range(3,9)]+[f'=IF(G{k}=0,0,H{k}/G{k})'])
for c in w[k]: c.font=Font(name=F,bold=True,size=9)
for r in range(2,k+1): w[f'I{r}'].number_format='0.0%'
# endpoints from generated urls
eps=[]
for app in sorted(os.listdir(os.path.join(BACK,'apps'))):
    p=os.path.join(BACK,'apps',app,'urls.py')
    if not os.path.exists(p): continue
    for m in re.finditer(r"path\('([^']+)', PorConstruir(?:Publico)?\.as_view\(caso_de_uso='([^']+)', metodo='(\w+)'\)",open(p).read()):
        eps.append([m.group(3),f'/api/v1/{app}/'+m.group(1),m.group(2),app,'501 · por construir'])
for m in re.finditer(r"path\('([^']+)', (\w+)\.as_view\((?:caso_de_uso='([^']+)', metodo='(\w+)')?",open(os.path.join(BACK,'guayacan','urls.py')).read()):
    estado='501 · por construir' if m.group(2).startswith('PorConstruir') else 'implementado en el esqueleto'
    eps.append([m.group(4) or ('POST' if 'token' in m.group(1) or 'lote' in m.group(1) else 'GET'),'/api/v1/'+m.group(1),m.group(3) or {'auth/token/':'SEG-01','auth/token/refrescar/':'SEG-01','nucleo/mis-fincas/':'NUC-03','sincronizacion/lote/':'NUC-05'}.get(m.group(1),'—'),'guayacan',estado])
eps+= [['GET','/api/b2b/v1/catalogo/','NUC-10','guayacan','501 · por construir'],['POST','/api/b2b/v1/pedidos/','NUC-10','guayacan','501 · por construir'],
       ['GET/POST','/canales/{canal}/webhook (servicio de agentes)','RED-01','servicios/agentes','verificación y firma implementadas; orquestación por construir'],
       ['POST','/agentes/instructor/preguntar (servicio de agentes)','FOR-09','servicios/agentes','501 · por construir'],
       ['POST','/lecturas/lote (puente IoT)','IOT-02','servicios/iot','reenvío implementado']]
hoja('Endpoints',['Método','Ruta','Caso de uso','App o servicio','Estado en el esqueleto'],eps,[9,60,11,18,34])
act=[]
for i,(k,v) in enumerate(C.ACTORES.items(),start=2):
    tipo='Agente de IA' if k.startswith('AG_') else ('Persona' if k in C.HUMANOS else 'Sistema externo')
    def exacto(col):
        """Fórmula COUNTIF que cuenta un código exacto dentro de listas «a; b; c» de la hoja Casos de uso (sin confundir RQ-1 con RQ-10)."""
        rg=f"'Casos de uso'!${col}$2:${col}${n}"
        return f'=COUNTIF({rg},A{i})+COUNTIF({rg},A{i}&"; *")+COUNTIF({rg},"*; "&A{i})+COUNTIF({rg},"*; "&A{i}&"; *")'
    act.append([v,tipo,exacto('G'),exacto('H')])
hoja('Actores',['Actor','Tipo','Casos como primario','Casos como secundario'],act,[34,16,16,18])
wb.save(OUT); print('ok',len(filas),len(eps))
