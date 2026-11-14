"""Diccionario de datos de GuayacanERP v5 en Excel, para el manual técnico."""
import csv, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from modelo import ESQUEMAS, T, GLOBALES, CAPTURA, AUDITADAS
import mongo

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(BASE, '..')
OUT = os.path.join(BASE, '..', '..', '..', 'docs', 'manuales', 'GuayacanERP_Diccionario_de_Datos_v5.xlsx')
import re as _re
PRUEBAS, _suite = [], ''
for l in open(os.path.join(BASE, '..', '..', 'casos-prueba', 'resultado_pruebas_v5.log'), encoding='utf-8'):
    if l.startswith('== '):
        _suite = 'v4 (regresión)' if 'v4' in l else 'v5'
    elif l.startswith('OK  '):
        PRUEBAS.append((_suite, _re.sub(r' -> ".*', '', l[4:]).strip()))

F = 'Arial'
VERDE, VERDE2, VERDE3, GRIS = '1F4E3D', 'D9EAD3', 'EEF5EA', 'F2F2F2'
f_tit = Font(name=F, size=16, bold=True, color=VERDE)
f_sub = Font(name=F, size=11, italic=True, color='595959')
f_head = Font(name=F, size=10, bold=True, color='FFFFFF')
f_tab = Font(name=F, size=11, bold=True, color=VERDE)
f_txt = Font(name=F, size=10)
f_bold = Font(name=F, size=10, bold=True)
f_mono = Font(name='Consolas', size=10)
f_link = Font(name=F, size=10, color='0563C1', underline='single')
fill_head = PatternFill('solid', fgColor=VERDE)
fill_tab = PatternFill('solid', fgColor=VERDE2)
fill_desc = PatternFill('solid', fgColor=VERDE3)
fill_gris = PatternFill('solid', fgColor=GRIS)
thin = Side(style='thin', color='BFBFBF')
borde = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical='top')
center = Alignment(horizontal='center', vertical='top', wrap_text=True)

filas = list(csv.DictReader(open(os.path.join(REPO, 'diccionario_postgresql.csv'), encoding='utf-8-sig')))
info = {f'{t[0]}.{t[1]}': t for t in T}
OPER = set(info) - GLOBALES


def llave(r):
    """Marcas de llave de una columna: PK (llave primaria), FK (foránea) y UQ (única)."""
    k = []
    if r['campo'] == 'id':
        k.append('PK')
    if r['referencia']:
        k.append('FK')
    if 'único' in r['restricciones']:
        k.append('UQ')
    return ', '.join(k)


def valores(r):
    """Valores permitidos de una columna con lista cerrada (CHECK), tomados del texto de restricciones."""
    return r['restricciones'].split('valores: ')[1] if 'valores: ' in r['restricciones'] else ''


def obligatorio(r):
    """Sí si la columna no admite vacío (NOT NULL); No en otro caso."""
    return 'Sí' if r['admite_vacio'] == 'no' else 'No'


def ambito(full):
    """Si la tabla es por finca (seguridad por filas) o un catálogo compartido entre fincas."""
    return 'Por finca (RLS)' if full in OPER else 'Catálogo compartido'


def encabezado(ws, fila, cols, anchos=None):
    """Escribe la fila de encabezados con su estilo y, si se dan, los anchos de columna."""
    for j, c in enumerate(cols, 1):
        cell = ws.cell(fila, j, c)
        cell.font, cell.fill, cell.alignment, cell.border = f_head, fill_head, center, borde
    if anchos:
        for j, w in enumerate(anchos, 1):
            ws.column_dimensions[get_column_letter(j)].width = w


def celda(ws, fila, col, val, font=f_txt, align=wrap, fill=None):
    """Escribe una celda con fuente, alineación, borde y relleno opcional; devuelve la celda."""
    c = ws.cell(fila, col, val)
    c.font, c.alignment, c.border = font, align, borde
    if fill:
        c.fill = fill
    return c


wb = Workbook()

# ------------------------------------------------------------------ Portada
ws = wb.active
ws.title = 'Portada'
ws.sheet_view.showGridLines = False
ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 34
ws.column_dimensions['C'].width = 70
ws['B2'] = 'GuayacanERP · Diccionario de datos'
ws['B2'].font = f_tit
ws['B3'] = 'Manual técnico · Modelo de datos versión 5 (operación integral de la finca) · PostgreSQL 18 + MongoDB'
ws['B3'].font = f_sub
datos = [('Proyecto', 'Plataforma ERP + CRM + IA de la finca El Guayacán de los Malaver (Pueblo Nuevo, Nilo, Cundinamarca)'),
         ('Versión del modelo', '5.0'), ('Fecha', '2026-10-27'), ('Autor', 'Iván Malaver Fierro'),
         ('Fuente', 'Generado desde specs/modelo-datos/generador/modelo.py; coincide con esquema_postgresql.sql'),
         ('Verificación', f'Esquema y datos iniciales cargados sin errores; {len(PRUEBAS)} pruebas de reglas de negocio aprobadas (ver hoja Pruebas). Probado en PostgreSQL 16 con PostGIS y pgvector sustituidos; destino de producción PostgreSQL 18'),
         ('Decisiones', 'Lo que espera equipo, trámite o decisión (nómina electrónica, BPA, GLOBALG.A.P., dron, robot, API B2B, seguro paramétrico, crédito, permuta, frío) está construido y apagado; se enciende en la hoja Funciones por finca. Ver docs/adr/0006')]
r = 5
for k, v in datos:
    celda(ws, r, 2, k, f_bold, fill=fill_desc); celda(ws, r, 3, v); r += 1
r += 1
ws.cell(r, 2, 'Resumen').font = f_tab; r += 1
resumen = [('Esquemas de PostgreSQL', f"=COUNTA('Índice de tablas'!B:B)-COUNTIF('Índice de tablas'!B:B,\"Esquema\")-(COUNTA('Índice de tablas'!B:B)-COUNTIF('Índice de tablas'!B:B,\"Esquema\")-{len(ESQUEMAS)})", 'Áreas del sistema'),
           ('Tablas de PostgreSQL', "=COUNTA('Índice de tablas'!C:C)-1", 'Ver hoja Índice de tablas'),
           ('Campos de PostgreSQL', "=COUNTA('Diccionario completo'!E:E)-1", 'Ver hoja Diccionario completo'),
           ('Tablas por finca (con seguridad por filas)', "=COUNTIF('Índice de tablas'!E:E,\"Por finca (RLS)\")", 'Llevan predio_id'),
           ('Tablas con captura sin conexión', "=COUNTIF('Índice de tablas'!F:F,\"Sí\")", 'Llevan id_cliente, capturado_en, dispositivo_captura_id'),
           ('Tablas con auditoría automática', "=COUNTIF('Índice de tablas'!G:G,\"Sí\")", 'Disparador nucleo.auditar()'),
           ('Llaves foráneas en la base', "=COUNTA('Relaciones'!A:A)-1-COUNTIF('Relaciones'!E:E,\"Referencia lógica*\")", 'Más 1 referencia lógica; ver hoja Relaciones'),
           ('Colecciones de MongoDB', "=COUNTA('MongoDB colecciones'!A:A)-1", 'Ver hojas MongoDB'),
           ('Campos de MongoDB', "=COUNTA('MongoDB campos'!C:C)-1", 'Incluye _id y predio_id')]
resumen[0] = ('Esquemas de PostgreSQL', len(ESQUEMAS), 'Áreas del sistema (nucleo, terceros, produccion, ...)')
for k, v, n in resumen:
    celda(ws, r, 2, k, f_bold, fill=fill_desc); c = celda(ws, r, 3, v, align=Alignment(horizontal='left', vertical='top'))
    ws.cell(r, 4, n).font = f_sub; r += 1
ws.column_dimensions['D'].width = 50
r += 1
ws.cell(r, 2, 'Contenido del libro').font = f_tab; r += 1
hojas = [('Convenciones', 'Abreviaturas, tipos de dato y reglas de nombres'), ('Índice de tablas', f'Las {len(T)} tablas con su fase, ámbito y enlace a su ficha'), ('Cambios v5', 'Tablas nuevas y modificadas frente a la versión 4'), ('Cambios v4', 'Tablas nuevas y modificadas frente a la versión 2'), ('Funciones por finca', 'Interruptores: qué está encendido y qué espera equipo o decisión'), ('Pruebas', 'Pruebas automáticas de las reglas y su resultado'),
         ('Hojas por esquema', 'Una hoja por esquema: cada tabla en un bloque con todos sus campos'),
         ('Diccionario completo', 'Todos los campos en una sola tabla con filtros'), ('Relaciones', 'Todas las llaves foráneas: origen, destino y tipo'),
         ('Reglas de negocio', 'Funciones, disparadores, vistas y políticas de seguridad de la base'),
         ('MongoDB colecciones', 'Las 8 colecciones con su propósito y borrado automático'), ('MongoDB campos', 'Campos de cada colección')]
for k, v in hojas:
    c = celda(ws, r, 2, k, f_bold)
    if k != 'Hojas por esquema':
        c.hyperlink = f"#'{k}'!A1"; c.font = Font(name=F, size=10, bold=True, color='0563C1', underline='single')
    celda(ws, r, 3, v); r += 1

# ------------------------------------------------------------------ Convenciones
ws = wb.create_sheet('Convenciones')
ws.sheet_view.showGridLines = False
ws['A1'] = 'Convenciones del diccionario'; ws['A1'].font = f_tit
encabezado(ws, 3, ['Término', 'Significado'], [28, 100])
conv = [('PK', 'Llave primaria: identifica cada registro (siempre el campo id, número consecutivo generado por la base)'),
        ('FK', 'Llave foránea: el campo apunta al id de otra tabla (columna Referencia)'),
        ('UQ', 'Valor único; en tablas por finca es único dentro de la misma finca (unique con predio_id)'),
        ('Obligatorio', 'Sí = NOT NULL, el campo no puede quedar vacío'),
        ('Por finca (RLS)', 'La tabla lleva predio_id y la seguridad por filas de PostgreSQL solo deja ver y escribir los datos de la finca de la sesión'),
        ('Catálogo compartido', 'Tabla común a todas las fincas (usuarios, roles, especies, cultivos, unidades, PUC, herramientas de IA, políticas de canal)'),
        ('Captura sin conexión', 'La app de campo puede crear estos registros sin señal; llevan id_cliente (UUIDv7), capturado_en y dispositivo_captura_id'),
        ('Auditada', 'Cada inserción, cambio o borrado queda en nucleo.auditoria con usuario, agente y campos modificados'),
        ('Llave compuesta', 'Entre tablas por finca la llave foránea es (predio_id, campo) → (predio_id, id): una finca no puede apuntar a datos de otra'),
        ('text (lista)', 'Texto que solo acepta los valores de la columna Valores permitidos (CHECK en la base, choices en Django)'),
        ('numeric(14,2)', 'Dinero en pesos colombianos con dos decimales'),
        ('timestamptz', 'Fecha y hora con zona horaria'),
        ('jsonb', 'Datos JSON estructurados (evidencias, cargas de eventos, condiciones)'),
        ('citext', 'Texto que no distingue mayúsculas (correos)'),
        ('geometry(..., 9377)', 'Geometría PostGIS en el sistema oficial de coordenadas de Colombia CTM12 (EPSG 9377)'),
        ('vector(1024)', 'Vector semántico (pgvector) para la búsqueda por significado de los agentes de IA'),
        ('Nombres', 'Tablas y campos en español, minúscula y guion bajo; tabla en singular; llaves foráneas <tabla>_id; fechas fecha_<hecho> o <hecho>_en'),
        ('Fase', '1 núcleo y campo · 2 comercio, frío y redes · 3 turismo y escala · 4 finca conectada (riego, seguridad, cámaras)'),
        ('Particionada', 'Tabla dividida por mes (nucleo.auditoria, iot.lectura); la aplicación solo la consulta por la tabla madre'),
        ('Función por finca', 'Interruptor en nucleo.funcionalidad; si está apagada, la regla rechaza la operación con un mensaje claro')]
for i, (k, v) in enumerate(conv, 4):
    celda(ws, i, 1, k, f_bold, fill=fill_desc); celda(ws, i, 2, v)

# ------------------------------------------------------------------ Hojas por esquema (fichas)
ubic = {}
hoja_de = {}
for esq, desc in ESQUEMAS.items():
    ws = wb.create_sheet(esq)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 5
    for col, w in zip('BCDEFGHI', [31, 16, 11, 16, 9, 36, 32, 60]):
        ws.column_dimensions[col].width = w
    ws['A1'] = f'Esquema {esq}'; ws['A1'].font = f_tit
    ws['A2'] = desc; ws['A2'].font = f_sub
    c = ws['I1']; c.value = '← Volver al índice'; c.hyperlink = "#'Índice de tablas'!A1"; c.font = f_link
    r = 4
    for t in [x for x in T if x[0] == esq]:
        full = f'{t[0]}.{t[1]}'
        ubic[full] = r; hoja_de[full] = esq
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
        marcas = [ambito(full), f'Fase {t[2]}'] + (['Captura sin conexión'] if full in CAPTURA else []) + (['Auditada'] if full in AUDITADAS else [])
        c = ws.cell(r, 1, f'{full}   ·   ' + '  ·  '.join(marcas)); c.font = f_tab; c.fill = fill_tab
        for j in range(1, 10):
            ws.cell(r, j).border = borde
        r += 1
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
        c = ws.cell(r, 1, t[3]); c.font = f_txt; c.alignment = wrap; c.fill = fill_desc
        ws.row_dimensions[r].height = 30 if len(t[3]) > 120 else 18
        r += 1
        for j, h in enumerate(['N°', 'Campo', 'Tipo de dato', 'Obligatorio', 'Valor por defecto', 'Llave', 'Referencia', 'Valores permitidos', 'Significado'], 1):
            cc = ws.cell(r, j, h); cc.font, cc.fill, cc.alignment, cc.border = f_head, fill_head, center, borde
        r += 1
        n = 0
        for fr in [x for x in filas if f"{x['esquema']}.{x['tabla']}" == full]:
            n += 1
            vals = [n, fr['campo'], fr['tipo'], obligatorio(fr), fr['valor_por_defecto'], llave(fr), fr['referencia'], valores(fr), fr['significado']]
            for j, v in enumerate(vals, 1):
                cc = celda(ws, r, j, v, f_mono if j in (2, 7) else f_txt, center if j in (1, 4, 6) else wrap)
                if n % 2 == 0:
                    cc.fill = fill_gris
            r += 1
        r += 2
    ws.freeze_panes = 'A4'
    ws.page_setup.orientation = 'landscape'; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

# ------------------------------------------------------------------ Índice de tablas
ws = wb.create_sheet('Índice de tablas', 2)
ws.sheet_view.showGridLines = False
cols = ['N°', 'Esquema', 'Tabla', 'Fase', 'Ámbito', 'Captura sin conexión', 'Auditada', 'Campos', 'Descripción', 'Ficha']
encabezado(ws, 1, cols, [5, 13, 34, 6, 20, 11, 10, 9, 80, 12])
T_ORD = sorted(T, key=lambda x: list(ESQUEMAS).index(x[0]))
for i, t in enumerate(T_ORD, 2):
    full = f'{t[0]}.{t[1]}'
    vals = [i - 1, t[0], full, t[2], ambito(full), 'Sí' if full in CAPTURA else 'No', 'Sí' if full in AUDITADAS else 'No',
            f"=COUNTIFS('Diccionario completo'!$A:$A,B{i},'Diccionario completo'!$B:$B,MID(C{i},LEN(B{i})+2,100))", t[3], 'Ver ficha']
    for j, v in enumerate(vals, 1):
        c = celda(ws, i, j, v, f_mono if j == 3 else f_txt, center if j in (1, 4, 6, 7, 8) else wrap)
        if i % 2 == 1:
            c.fill = fill_gris
    c = ws.cell(i, 10); c.hyperlink = f"#'{hoja_de[full]}'!A{ubic[full]}"; c.font = f_link
ws.freeze_panes = 'D2'
ws.auto_filter.ref = f'A1:J{len(T) + 1}'

# ------------------------------------------------------------------ Diccionario completo
ws = wb.create_sheet('Diccionario completo', 3)
cols = ['Esquema', 'Tabla', 'Fase', 'N°', 'Campo', 'Tipo de dato', 'Obligatorio', 'Valor por defecto', 'Llave', 'Referencia', 'Valores permitidos', 'Significado', 'Ámbito']
encabezado(ws, 1, cols, [12, 26, 6, 5, 26, 16, 11, 16, 8, 28, 34, 70, 20])
cont = {}
for i, fr in enumerate(filas, 2):
    key = (fr['esquema'], fr['tabla']); cont[key] = cont.get(key, 0) + 1
    full = f"{fr['esquema']}.{fr['tabla']}"
    vals = [fr['esquema'], fr['tabla'], int(fr['fase'].split()[-1]), cont[key], fr['campo'], fr['tipo'], obligatorio(fr), fr['valor_por_defecto'],
            llave(fr), fr['referencia'], valores(fr), fr['significado'], ambito(full)]
    for j, v in enumerate(vals, 1):
        celda(ws, i, j, v, f_mono if j in (2, 5, 10) else f_txt, center if j in (3, 4, 7, 9) else wrap)
tab = Table(displayName='Diccionario', ref=f'A1:M{len(filas) + 1}')
tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
ws.add_table(tab)
ws.freeze_panes = 'F2'

# ------------------------------------------------------------------ Relaciones
ws = wb.create_sheet('Relaciones', 4)
cols = ['Tabla origen', 'Campo', 'Tabla destino', 'Campo destino', 'Tipo de llave', 'Obligatoria', 'Significado']
encabezado(ws, 1, cols, [32, 26, 32, 14, 30, 11, 60])
r = 2
for fr in filas:
    if not fr['referencia']:
        continue
    full = f"{fr['esquema']}.{fr['tabla']}"
    destino = fr['referencia']
    if full == 'nucleo.auditoria' and fr['campo'] == 'predio_id':
        dcampo, tipo = 'id', 'Referencia lógica (sin llave, la auditoría no se bloquea)'
    elif destino == 'redes.politica_canal':
        dcampo, tipo = 'plataforma', 'Simple por código'
    elif full in OPER and destino in OPER:
        dcampo, tipo = 'predio_id, id', 'Compuesta por finca (predio_id, campo)'
    else:
        dcampo, tipo = 'id', 'Simple'
    for j, v in enumerate([full, fr['campo'], destino, dcampo, tipo, obligatorio(fr), fr['significado']], 1):
        celda(ws, r, j, v, f_mono if j in (1, 2, 3, 4) else f_txt, center if j == 6 else wrap)
    r += 1
tab = Table(displayName='Relaciones', ref=f'A1:G{r - 1}')
tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
ws.add_table(tab)
ws.freeze_panes = 'B2'

# ------------------------------------------------------------------ Reglas de negocio
ws = wb.create_sheet('Reglas de negocio', 5)
cols = ['Objeto', 'Tipo', 'Se aplica a', 'Qué hace', 'Probado']
encabezado(ws, 1, cols, [42, 22, 34, 90, 10])
reglas = [
 ('nucleo.predio_actual()', 'Función', 'Toda la base', 'Devuelve la finca de la sesión (app.predio_id); base de la seguridad por filas y valor por defecto de predio_id', 'Sí'),
 ('nucleo.usuario_actual() / agente_actual()', 'Función', 'Auditoría y reglas', 'Devuelven el usuario y el agente de IA de la sesión (app.usuario_id, app.agente_id)', 'Sí'),
 ('aislamiento_predio', 'Política RLS', f'{len(OPER) - 0} tablas por finca', 'Solo deja leer y escribir filas cuyo predio_id es la finca de la sesión (FORCE ROW LEVEL SECURITY)', 'Sí'),
 ('leer_parametro / escribir_parametro', 'Política RLS', 'nucleo.parametro', 'Lee parámetros nacionales (predio_id vacío) y los de la finca; solo escribe los de la finca', 'Sí'),
 ('leer_auditoria / registrar_auditoria', 'Política RLS', 'nucleo.auditoria', 'Cada finca ve solo su auditoría; cualquier operación puede registrar', 'Sí'),
 ('guayacan_app', 'Rol', 'Conexión de la API', 'Rol sin superusuario ni BYPASSRLS; no puede borrar ni editar la auditoría', 'Sí'),
 ('nucleo.marcar_actualizado()', 'Disparador BEFORE UPDATE', 'Tablas con actualizado_en', 'Pone la fecha y hora de la última modificación', 'Sí'),
 ('nucleo.auditar()', 'Disparador AFTER', f'{len(AUDITADAS)} tablas auditadas', 'Registra crear, actualizar o eliminar con solo los campos que cambiaron, el usuario y el agente', 'Sí'),
 ('nucleo.impedir_cambio()', 'Disparador BEFORE', 'auditoria, movimiento_inventario, permuta, cambio_estado_alarma', 'Las hace de solo inserción: no se editan ni se borran', 'Sí'),
 ('nucleo.predios_del_usuario(usuario)', 'Función', 'Inicio de sesión', 'Lista las fincas y roles de un usuario para escoger finca', 'No'),
 ('inventario.estimar_vencimiento()', 'Disparador BEFORE', 'inventario.lote_inventario', 'Calcula fecha_vencimiento (producción + vida útil según almacenamiento) y fecha_limite_venta (vencimiento − margen)', 'Sí'),
 ('inventario.proteger_cantidades()', 'Disparador BEFORE', 'inventario.lote_inventario', 'Impide editar cantidades a mano; solo el kardex las cambia', 'Sí'),
 ('inventario.entrada_inicial()', 'Disparador AFTER INSERT', 'inventario.lote_inventario', 'Crea el movimiento de entrada del lote nuevo', 'Sí'),
 ('inventario.aplicar_movimiento()', 'Disparador AFTER INSERT', 'inventario.movimiento_inventario', 'Aplica el movimiento al lote con bloqueo de fila; rechaza existencias negativas, ventas de lotes vencidos y mermas sin causa', 'Sí'),
 ('inventario.reservar_fefo(detalle)', 'Función', 'comercial.pedido_detalle', 'Reserva por lotes en orden de vencimiento (FEFO), sin tomar lotes pasados de su fecha límite; todo o nada', 'Sí'),
 ('comercial.confirmar_pedido(pedido)', 'Función', 'comercial.pedido', 'Verifica que el precio siga vigente, reserva FEFO, calcula totales y publica el evento pedido.confirmado', 'Sí'),
 ('comercial.despachar_pedido(pedido)', 'Función', 'comercial.pedido', 'Convierte las reservas en salidas de venta', 'Sí'),
 ('comercial.cancelar_pedido(pedido)', 'Función', 'comercial.pedido', 'Libera las reservas de un pedido que aún no sale de la finca', 'No'),
 ('inventario.marcar_vencidos()', 'Función (tarea diaria)', 'inventario.lote_inventario', 'Marca como vencidos los lotes pasados de su fecha de vencimiento', 'Sí'),
 ('inventario.v_alertas_vencimiento', 'Vista', 'Panel y vendedor virtual', 'Semáforo verde, amarillo o rojo por lote, acción sugerida y precio de liquidación aprobado', 'Sí'),
 ('comercial.v_catalogo_disponible', 'Vista', 'Agentes de venta', 'Catálogo con precio vigente y cantidad vendible hoy, sin costos', 'Sí'),
 ('ux_precio_vigente', 'Índice único', 'comercial.precio_producto', 'Un solo precio vigente por producto y lista en cada finca', 'Sí'),
 ('comercial.aplicar_propuesta_precio(propuesta)', 'Función', 'comercial.propuesta_precio', 'Aplica un precio aprobado: cierra el vigente, crea el nuevo y publica precio.aplicado; lo vendido conserva su precio', 'Sí'),
 ('finanzas.periodo_abierto(predio, fecha)', 'Función', 'finanzas.periodo_contable', 'Indica si el mes contable está abierto', 'Sí'),
 ('finanzas.proteger_comprobante()', 'Disparador BEFORE', 'finanzas.comprobante', 'Exige periodo abierto; un comprobante contabilizado solo se anula con motivo; registra contabilizado_en', 'Sí'),
 ('finanzas.validar_cuadre()', 'Disparador diferido', 'finanzas.comprobante', 'Al confirmar la transacción exige débitos = créditos, al menos dos líneas y total mayor que cero', 'Sí'),
 ('finanzas.proteger_movimiento()', 'Disparador BEFORE', 'finanzas.movimiento_contable', 'Impide cambiar líneas de comprobantes contabilizados o anulados', 'Sí'),
 ('redes.verificar_envio(...)', 'Función', 'Conector de canales', 'Decide si un mensaje puede salir: ventana del canal, extensión para persona, plantilla aprobada, consentimiento y tope de mensajes', 'Sí'),
 ('ix_fragmento_vector', 'Índice HNSW (pgvector)', 'ia.fragmento_conocimiento', 'Búsqueda por significado en la base de conocimiento de los agentes', 'No (requiere pgvector)'),
 ('nucleo.funcion_activa(codigo) / exigir_funcion(codigo)', 'Función', 'Reglas con interruptor', 'Indican o exigen que una función esté encendida en la finca de la sesión', 'Sí'),
 ('nucleo.crear_particion_mensual / mantener_particiones', 'Función (tarea mensual)', 'auditoria, iot.lectura', 'Crea las particiones de los próximos meses sin permisos directos para la API', 'Sí'),
 ('inventario.puede_venderse(lote)', 'Función (Specification)', 'Reserva FEFO y catálogo', 'Disponible, con existencias, antes de la fecha límite y sin bloqueo abierto', 'Sí'),
 ('inventario.aplicar_bloqueo()', 'Disparador BEFORE', 'inventario.bloqueo_lote', 'Bloquea el lote; solo una persona lo libera o descarta (descartar registra la merma); deja huella', 'Sí'),
 ('inventario.evaluar_excursion()', 'Disparador BEFORE', 'inventario.excursion_temperatura', 'Si el tiempo fuera de rango supera la tolerancia, bloquea los lotes perecederos de la nevera o del vehículo en ruta', 'Sí'),
 ('comercial.v_trazabilidad_lote', 'Vista', 'Retiro de lotes', 'Origen de un lote y clientes y pedidos que lo recibieron', 'Sí'),
 ('comercial.abrir_retiro(lote, motivo)', 'Función', 'comercial.retiro_lote', 'Bloquea el lote y crea un aviso por cada cliente que lo recibió', 'Sí'),
 ('comercial.registrar_huella / verificar_cadena_huellas', 'Función', 'comercial.huella_trazabilidad', 'Cadena SHA-256 de hechos de trazabilidad, lista para anclarse en blockchain', 'Sí'),
 ('produccion.clasificar_por_peso(peso)', 'Función', 'produccion.categoria_huevo', 'Devuelve la categoría del huevo según los rangos vigentes', 'Sí'),
 ('produccion.validar_clasificacion()', 'Disparador AFTER', 'produccion.clasificacion_postura', 'La clasificación no supera los huevos buenos; visión solo con su función encendida', 'Sí'),
 ('comercial.preparar_factura() / aplicar_pago()', 'Disparador BEFORE', 'factura, pago', 'Saldo y vencimiento de la factura; los pagos confirmados bajan el saldo; un agente no confirma pagos', 'Sí'),
 ('comercial.v_cartera / actualizar_mora()', 'Vista y tarea diaria', 'Cartera', 'Edad de la deuda y bloqueo por mora', 'Sí'),
 ('comercial.confirmar_pedido (crédito)', 'Función', 'comercial.pedido', 'A crédito exige la función venta_credito, cliente sin mora y cupo disponible', 'Sí'),
 ('comercial.aplicar_permuta()', 'Disparador BEFORE', 'comercial.permuta', 'Exige la función permuta, no supera saldos y genera el pago de compensación', 'Sí'),
 ('comercial.generar_pedidos_recurrentes(fecha)', 'Función (tarea diaria)', 'comercial.pedido_recurrente', 'Crea en borrador los pedidos del día y avanza la próxima fecha', 'Sí'),
 ('redes.validar_pieza()', 'Disparador BEFORE', 'redes.pieza_audiovisual', 'Solo una persona aprueba; si aparecen personas, todas deben tener autorización de imagen', 'Sí'),
 ('iot.preparar_clip() / depurar_clips()', 'Disparador y tarea diaria', 'iot.clip_video', 'Fecha de borrado según la retención de la cámara; borra los vencidos salvo los elegidos para redes', 'Sí'),
 ('iot.validar_camara()', 'Disparador BEFORE', 'iot.camara', 'La cámara térmica exige su función encendida', 'Sí'),
 ('iot.cambiar_estado_alarma(zona, estado, origen)', 'Función (State)', 'iot.zona_seguridad', 'Solo transiciones válidas, con historial; el estado no se edita directo', 'Sí'),
 ('iot.validar_actuador()', 'Disparador BEFORE', 'iot.actuador', 'Una cerradura en un paso de personas debe abrir sin energía', 'Sí'),
 ('iot.proteger_evento_seguridad()', 'Disparador BEFORE', 'iot.evento_seguridad', 'El evento no se altera; solo se registra su atención', 'Sí'),
 ('iot.validar_credencial() / terceros.revocar_biometria()', 'Disparadores', 'iot.credencial_acceso', 'Rostro solo con función encendida y autorización expresa de biometría; al revocarla se apaga', 'Sí'),
 ('ambiental.v_indicadores', 'Vista', 'Indicadores ambientales', 'Totales del mes y CO₂ estimado con factor y fuente; sin fuente no calcula', 'Sí')]
for i, rg in enumerate(reglas, 2):
    for j, v in enumerate(rg, 1):
        celda(ws, i, j, v, f_mono if j == 1 else f_txt, center if j == 5 else wrap)
tab = Table(displayName='Reglas', ref=f'A1:E{len(reglas) + 1}')
tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
ws.add_table(tab)
ws.freeze_panes = 'B2'

# ------------------------------------------------------------------ Cambios v4
NUEVAS = ['nucleo.funcionalidad', 'nucleo.nota_voz', 'produccion.categoria_huevo', 'produccion.clasificacion_postura', 'produccion.registro_bioseguridad',
          'produccion.produccion_abono', 'inventario.vehiculo', 'inventario.excursion_temperatura', 'inventario.bloqueo_lote', 'comercial.retiro_lote',
          'comercial.retiro_aviso', 'comercial.pedido_recurrente', 'comercial.pedido_recurrente_detalle', 'comercial.permuta', 'comercial.huella_trazabilidad',
          'compras.documento_soporte', 'ia.modelo_pronostico', 'ia.pronostico_demanda', 'redes.pieza_audiovisual', 'redes.pieza_persona',
          'turismo.bloqueo_calendario', 'iot.zona_seguridad', 'iot.cambio_estado_alarma', 'iot.credencial_acceso', 'iot.camara', 'iot.evento_seguridad',
          'iot.clip_video', 'ambiental.factor_emision', 'ambiental.registro_ambiental']
CAMBIOS = [('nucleo.predio', '+ es_practica (finca de práctica del modo aprendiz)'), ('nucleo.zona', '+ modelo_3d_url (gemelo digital listo)'),
           ('nucleo.auditoria', 'Particionada por mes'), ('terceros.consentimiento_datos', 'finalidad + biometria_acceso'),
           ('terceros.cliente', '+ dias_plazo, bloqueado_por_mora; segmento + hotel'),
           ('produccion.registro_postura', 'huevos_aaa, huevos_aa, huevos_a → huevos_recogidos; la clasificación pasa a clasificacion_postura'),
           ('inventario.bodega', '+ refrigerada, sensor_temperatura_id, temperatura_min_c, temperatura_max_c, minutos_tolerancia'),
           ('comercial.pedido', '+ forma_pago, pedido_recurrente_id'), ('comercial.factura', '+ fecha_vencimiento, saldo'),
           ('comercial.pago', 'medio + pasarela, compensacion_permuta; + proveedor_pasarela, id_transaccion_pasarela'),
           ('comercial.entrega', '+ vehiculo_id'), ('turismo.reserva', '+ valor_deposito, checkin_en, checkout_en'),
           ('iot.dispositivo', 'tipo + registrador_temperatura, camara, camara_termica, lector_acceso, central_alarma'),
           ('iot.sensor', 'magnitud + movimiento, puerta, rotura_vidrio, humo, gas, amoniaco, presencia_termica'),
           ('iot.actuador', 'tipo + sirena, reflector, cerradura, cortina, extractor; + zona_seguridad_id, modo_falla'),
           ('iot.lectura', 'Particionada por mes'), ('Nuevo esquema ambiental', 'Mediciones ambientales y factores de emisión')]
ws = wb.create_sheet('Cambios v4', 3)
ws.sheet_view.showGridLines = False
encabezado(ws, 1, ['Cambio', 'Tabla', 'Fase', 'Detalle'], [14, 36, 6, 100])
r = 2
for full in NUEVAS:
    t = info[full]
    for j, v in enumerate(['Nueva', full, t[2], t[3]], 1):
        celda(ws, r, j, v, f_mono if j == 2 else f_txt, center if j in (1, 3) else wrap)
    r += 1
for full, det in CAMBIOS:
    for j, v in enumerate(['Modificada', full, info[full][2] if full in info else '', det], 1):
        celda(ws, r, j, v, f_mono if j == 2 else f_txt, center if j in (1, 3) else wrap)
    r += 1
tab = Table(displayName='CambiosV4', ref=f'A1:D{r - 1}'); tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True); ws.add_table(tab)
ws.freeze_panes = 'C2'


# ------------------------------------------------------------------ Cambios v5
NUEVOS_ESQ = ['personal', 'nomina', 'formacion', 'activos', 'documental', 'cumplimiento', 'seguros', 'seguridad', 'crm', 'estrategia', 'agenda', 'proyectos']
NUEVAS5 = [f'{t[0]}.{t[1]}' for t in T if t[0] in NUEVOS_ESQ] + ['ia.diagnostico_imagen', 'ia.escenario', 'ia.decision', 'finanzas.clasificacion_costo',
          'finanzas.actividad_costo', 'finanzas.asignacion_costo', 'finanzas.costo_estandar', 'finanzas.presupuesto', 'finanzas.premisa_presupuesto',
          'finanzas.presupuesto_detalle', 'finanzas.estado_financiero', 'finanzas.indicador', 'finanzas.valor_indicador', 'finanzas.anticipo_proveedor',
          'finanzas.aplicacion_anticipo', 'finanzas.reporte_indicadores', 'iot.mision_robot', 'iot.prioridad_carga', 'nucleo.llave_api',
          'nucleo.webhook_suscripcion', 'nucleo.webhook_entrega']
CAMBIOS5 = [('nucleo.predio', '+ regimen_tributario (por definir con el contador), empleador_tercero_id'),
            ('terceros.empleado', '+ forma_pago (salario, jornal, destajo, mixto), valor_jornal, ruta_aprendizaje'),
            ('produccion.labor_cultural', '+ metodo (manual, mecánico, robot, dron), tarea_id, mision_robot_id; robot o dron exigen misión'),
            ('finanzas.valor_indicador', 'semáforo + sin_meta'),
            ('finanzas.indicador', 'grupo + proyecto'),
            ('turismo.reserva', 'Sincroniza la agenda de la cabaña (sin cruces), valida capacidad y crea la tarea de limpieza al salir'),
            ('turismo.bloqueo_calendario', 'Ocupa la agenda de la cabaña')]
ws = wb.create_sheet('Cambios v5', 3)
ws.sheet_view.showGridLines = False
encabezado(ws, 1, ['Cambio', 'Tabla', 'Fase', 'Detalle'], [14, 36, 6, 100])
r = 2
for full in NUEVAS5:
    t = info[full]
    for j, v in enumerate(['Nueva', full, t[2], t[3]], 1):
        celda(ws, r, j, v, f_mono if j == 2 else f_txt, center if j in (1, 3) else wrap)
    r += 1
for full, det in CAMBIOS5:
    for j, v in enumerate(['Modificada', full, info[full][2] if full in info else '', det], 1):
        celda(ws, r, j, v, f_mono if j == 2 else f_txt, center if j in (1, 3) else wrap)
    r += 1
tab = Table(displayName='CambiosV5', ref=f'A1:D{r - 1}'); tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True); ws.add_table(tab)
ws.freeze_panes = 'C2'

# Reglas v5 al final de la hoja de reglas
ws = wb['Reglas de negocio']
reglas5 = [
 ('nucleo.parametro_valor / tiene_permiso / exigir_persona', 'Funciones', 'Reglas v5', 'Parámetro vigente de la finca o nacional; permiso del usuario por rol; corta la acción si la sesión es de un agente (la IA propone, una persona decide)', 'Sí'),
 ('personal.validar_tarea()', 'Disparador BEFORE', 'personal.tarea', 'Solo asigna a quien está disponible y habilitado; el agente propone sin asignar; aprueba una persona con permiso y nunca su propia tarea; aprobada no se edita', 'Sí'),
 ('personal.generar_tareas_del_dia(fecha)', 'Función (tarea diaria)', 'personal.plantilla_tarea', 'Crea las tareas del día desde el plan de labores con su lista de chequeo, sin duplicar', 'Sí'),
 ('personal.calcular_jornada() / v_productividad', 'Disparador y vista', 'personal.jornada, tarea', 'Horas desde el carné QR o NFC; jornada aprobada no se edita; productividad contra el estándar', 'Sí'),
 ('nomina.preparar_prenomina(periodo)', 'Función', 'nomina.novedad', 'Salario de contratos, auxilio de transporte, jornales y destajo de tareas y jornadas aprobadas', 'Sí'),
 ('nomina.validar_novedad()', 'Disparador BEFORE', 'nomina.novedad', 'El salario de un contrato nunca depende de tareas; solo tareas y jornadas aprobadas pagan', 'Sí'),
 ('nomina.liquidar(periodo)', 'Función', 'nomina.liquidacion', 'Devengado, aportes del trabajador, neto y provisión de prestaciones con tarifas de nucleo.parametro', 'Sí'),
 ('nomina.proteger_periodo() / proteger_detalle_periodo()', 'Disparadores', 'Periodo y sus datos', 'Cierre con dos personas, nunca por agente y con comprobante contabilizado; cerrado no se edita (nota de ajuste)', 'Sí'),
 ('nomina.validar_pago() / marcar_pagada()', 'Disparadores', 'nomina.pago_nomina', 'Quien prepara no aprueba, nadie aprueba su propio pago, segunda aprobación sobre el monto, no supera el neto', 'Sí'),
 ('nomina.validar_documento_electronico()', 'Disparador BEFORE', 'documento_nomina_electronica', 'Exige la función nomina_electronica y el régimen tributario definido', 'Sí'),
 ('formacion.validar_inscripcion / emitir_certificado / certificar_sesion', 'Disparadores y funciones', 'Formación', 'Aprobar con la nota mínima o asistir a la sesión presencial emite certificado y habilitación', 'Sí'),
 ('formacion.actualizar_habilitaciones() / esta_habilitado()', 'Función (tarea diaria)', 'formacion.habilitacion', 'Un certificado vencido retira la habilitación', 'Sí'),
 ('activos.generar_ordenes_trabajo() / cerrar_orden() / depreciar_mes()', 'Funciones y disparador', 'Activos', 'Orden y tarea al vencer el plan por horas, km o días; al cerrar reinicia el plan; depreciación en línea recta', 'Sí'),
 ('documental.validar_version() / obsoletar_anteriores() / documento_para_agente()', 'Disparadores y función', 'Documental', 'Una sola versión aprobada vigente; aprobada no cambia su archivo; los agentes leen solo lo aprobado, vigente y autorizado', 'Sí'),
 ('cumplimiento.evaluar_expediente(expediente)', 'Función (tarea diaria)', 'Cumplimiento', 'Revisa cada requisito contra habilitaciones, documentos vigentes y registros recientes; lo vencido pasa a no cumple', 'Sí'),
 ('cumplimiento.cerrar_no_conformidad() / verificar_accion()', 'Disparadores', 'No conformidades', 'No se cierra sin acciones hechas y verificadas por una persona', 'Sí'),
 ('cumplimiento.v_granja_biosegura', 'Vista', 'ICA 3651 de 2014', 'Alerta cuando hay 200 aves o más de postura o levante sin certificado', 'Sí'),
 ('seguros.preparar_poliza / validar_aviso / vigilar_indice / v_por_vencer', 'Disparadores, función y vista', 'Seguros', 'Valor subsidiado, aviso antes de vencer, paramétrico con su función, sin reclamación automática', 'Sí'),
 ('ia.validar_diagnostico() / validar_decision()', 'Disparadores', 'IA', 'El diagnóstico por foto lo confirma una persona; una decisión la toma una persona y no se cambia', 'Sí'),
 ('finanzas.aplicar_anticipo() / preparar_anticipo()', 'Disparadores', 'Anticipos', 'Se descuenta al mismo proveedor y nunca queda negativo', 'Sí'),
 ('finanzas.validar_clasificacion() / validar_presupuesto_detalle()', 'Disparadores', 'Costos y presupuesto', 'Semivariable con su parte fija; base cero con justificación; presupuesto aprobado no cambia', 'Sí'),
 ('finanzas.saldo / estado_resultados / balance_general', 'Funciones', 'Contabilidad', 'Estado de resultados por costeo variable y balance que cuadra, total o por centro de costo', 'Sí'),
 ('finanzas.palancas / calcular_indicadores / distribuir_costos', 'Funciones', 'Indicadores', 'Punto de equilibrio, margen de seguridad, GPO, GPF, GPT; liquidez, endeudamiento, rentabilidad, EVA, Z de Altman; costeo ABC', 'Sí (ABC no)'),
 ('finanzas.validar_reporte_indicadores()', 'Disparador BEFORE', 'Indicadores para crédito', 'Función encendida, autorización de una persona, sin costos ni datos personales y con huella SHA-256', 'Sí'),
 ('estrategia.vpn / tir / evaluar_proyecto', 'Funciones', 'Evaluación de proyectos', 'VPN a la tasa de oportunidad, TIR, ROI, recuperación, equilibrio, margen de seguridad y palancas', 'Sí'),
 ('estrategia.validar_iniciativa() / validar_reinversion()', 'Disparadores', 'Iniciativas y reinversión', 'El agente solo propone; se aprueba con evaluación calculada; se reinvierte solo de líneas con utilidad y hasta el tope', 'Sí'),
 ('estrategia.v_retorno_iniciativas / v_matriz_lineas', 'Vistas', 'Tablero estratégico', 'Retorno proyectado contra real; ingreso, margen y utilidad de cada sección de la finca', 'Sí'),
 ('seguridad.registrar_intento(...)', 'Función (detector)', 'Inicio de sesión', 'Bloquea cuenta por fuerza bruta, IP por relleno de credenciales y a quien toque un señuelo; crea la alerta', 'Sí'),
 ('seguridad.validar_sesion() / requiere_doble_factor()', 'Disparador y función', 'seguridad.sesion_usuario', 'Doble factor para administrador y contador; cuenta o IP bloqueada no entra; sesión máxima de 12 horas', 'Sí'),
 ('seguridad.vigilar_privilegios() / vigilar_exportaciones()', 'Disparadores', 'Roles, permisos y auditoría', 'Alerta al dar roles críticos, cambiar permisos, volverse superusuario o exportar en masa', 'Sí'),
 ('seguridad.proteger_alerta() / revisar_copias() / v_tablero', 'Disparador, función y vista', 'Monitoreo', 'Alertas que no se alteran ni se borran; aviso sin copia diaria o sin prueba de restauración; tablero', 'Sí'),
 ('crm.validar_prospecto / validar_interaccion / calificar / convertir_prospecto', 'Disparadores y funciones', 'CRM', 'Datos de personas solo con autorización; no se contacta sin ella; puntaje; conversión a cliente', 'Sí'),
 ('iot.validar_mision() / cargas_a_cortar()', 'Disparador y función', 'Robótica y energía', 'Misión aprobada por una persona; dron registrado, con piloto, póliza y 122 m; robot sin personas; cortes de carga por prioridad', 'Sí'),
 ('personal.validar_turno() / turno_rango()', 'Disparador y función', 'personal.turno', 'Turnos que cruzan la medianoche; sin cruces, con descanso mínimo entre turnos, jornada máxima diaria y sin ausencias', 'Sí'),
 ('personal.generar_turnos(cronograma) / huecos_cobertura(cronograma)', 'Funciones', 'Cronograma 24/7', 'Turnos desde patrones semanales o cíclicos con desfase; horas sin la cobertura mínima del área', 'Sí'),
 ('personal.publicar_cronograma()', 'Disparador BEFORE', 'personal.cronograma', 'Se publica con jornada semanal máxima más extras, un día de descanso cada 7 y sin huecos de cobertura', 'Sí'),
 ('personal.validar_area_tarea() / es_responsable_area()', 'Disparador y función', 'Áreas de responsabilidad', 'La tarea de un área va a un miembro del área; su responsable la puede aprobar', 'Sí'),
 ('agenda.preparar_cita() + exclusión GiST', 'Disparador y restricción', 'agenda.cita', 'Calendario de cada recurso sin cruces, contando el tiempo de limpieza o alistamiento', 'Sí'),
 ('turismo.validar_reserva / sincronizar_agenda / sincronizar_bloqueo', 'Disparadores', 'Cabañas', 'Capacidad, reserva y bloqueos en la agenda sin cruces; tarea de limpieza al salir el huésped', 'Sí'),
 ('agenda.validar_visita() / emitir_pase()', 'Disparador y función', 'agenda.visita', 'Aprobación por una persona, declaración de bioseguridad para el galpón y pase QR con huella', 'Sí'),
 ('agenda.validar_acceso() / v_en_sitio', 'Disparador y vista', 'agenda.registro_acceso', 'Horario, placa y desinfección; el carné abre y cierra la jornada; quién está dentro ahora', 'Sí'),
 ('formacion.validar_queja() / v_satisfaccion', 'Disparador y vista', 'Formación (ISO 21001)', 'Plazo de respuesta, resuelve alguien distinto del instructor; satisfacción y aprobación por curso', 'Sí'),
 ('proyectos.validar_proyecto / linea_base_inicial / aceptar_entregable', 'Disparadores', 'Proyectos (PMBOK 8)', 'Aprueba el patrocinador con acta completa; nace la línea base; se cierra con entregables aceptados y lecciones', 'Sí'),
 ('proyectos.validar_dependencia() / calcular_ruta_critica()', 'Disparador y función', 'Cronograma del proyecto', 'Sin ciclos; CPM con FC, CC, FF y CF, holguras y ruta crítica', 'Sí'),
 ('proyectos.decidir_cambio / nueva_linea_base / calcular_valor_ganado / v_tablero', 'Disparadores, función y vista', 'Control del proyecto', 'El cambio lo aprueba otra persona y crea nueva línea base; PV, EV, AC, CPI, SPI, EAC; tablero', 'Sí'),
 ('finanzas.analisis_vertical_horizontal / fuentes_usos', 'Funciones', 'Análisis financiero', 'Peso de cada cuenta, variación entre periodos y estado de fuentes y usos', 'Sí'),
 ('nucleo.validar_llave_api / autenticar_llave_api / validar_webhook', 'Disparadores y función', 'Integraciones', 'API B2B y webhooks con su función; llave solo para clientes; la llave señuelo bloquea la IP', 'Sí')]
r0 = ws.max_row + 1
for i, rg in enumerate(reglas5, r0):
    for j, v in enumerate(rg, 1):
        celda(ws, i, j, v, f_mono if j == 1 else f_txt, center if j == 5 else wrap)
ws.tables['Reglas'].ref = f'A1:E{ws.max_row}'

# ------------------------------------------------------------------ Funciones por finca
import re as _re2
semilla = open(os.path.join(REPO, 'datos_iniciales.sql'), encoding='utf-8').read()
funcs = []
for bloque in semilla.split('insert into nucleo.funcionalidad')[1:]:
    funcs += _re2.findall(r"\('([a-z_0-9]+)', '([^']*)', (\d), (null|'[^']*'), (true|false)\)", bloque.split(';\n', 1)[0])
ws = wb.create_sheet('Funciones por finca')
ws.sheet_view.showGridLines = False
ws['A1'] = 'Funciones por finca (nucleo.funcionalidad)'; ws['A1'].font = f_tit
ws['A2'] = 'Lo que espera equipo o una decisión queda construido y apagado; se enciende sin desplegar otra versión.'; ws['A2'].font = f_sub
encabezado(ws, 4, ['Código', 'Qué habilita', 'Fase', 'Equipo o requisito previo', 'Estado inicial'], [26, 70, 6, 46, 14])
for i, (cod, desc, fase, eq, act) in enumerate(funcs, 5):
    for j, v in enumerate([cod, desc, int(fase), eq.strip("'") if eq != 'null' else '—', 'Encendida' if act == 'true' else 'Apagada'], 1):
        celda(ws, i, j, v, f_mono if j == 1 else f_txt, center if j in (3, 5) else wrap)
tab = Table(displayName='Funciones', ref=f'A4:E{len(funcs) + 4}'); tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True); ws.add_table(tab)

# ------------------------------------------------------------------ Pruebas
ws = wb.create_sheet('Pruebas')
ws.sheet_view.showGridLines = False
ws['A1'] = 'Pruebas automáticas de las reglas de negocio (specs/casos-prueba/pruebas_reglas_v4.sql y pruebas_reglas_v5.sql)'; ws['A1'].font = f_tit
ws['A2'] = 'Se ejecutan con el rol guayacan_app, que no puede saltarse la seguridad por filas, sobre una base nueva con el esquema y los datos iniciales.'; ws['A2'].font = f_sub
encabezado(ws, 4, ['N°', 'Suite', 'Área', 'Qué se prueba', 'Resultado'], [6, 16, 22, 100, 12])
for i, (suite, p) in enumerate(PRUEBAS, 5):
    area, _, que = p.partition(': ')
    for j, v in enumerate([i - 4, suite, area, que, 'Aprobada'], 1):
        celda(ws, i, j, v, f_txt, center if j in (1, 2, 5) else wrap)
tab = Table(displayName='Pruebas', ref=f'A4:E{len(PRUEBAS) + 4}'); tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True); ws.add_table(tab)
ws.freeze_panes = 'A5'

# ------------------------------------------------------------------ MongoDB
ws = wb.create_sheet('MongoDB colecciones')
cols = ['Colección', 'Fase', 'Qué guarda', 'Borrado automático', 'Índices']
encabezado(ws, 1, cols, [22, 6, 80, 16, 60])
for i, (nombre, fase, desc, campos, idx, ttl) in enumerate(mongo.C, 2):
    ind = '; '.join(', '.join(f'{k} {"↑" if v == 1 else "↓"}' for k, v in ({'predio_id': 1, **x}).items()) for x in idx)
    for j, v in enumerate([nombre, fase, desc, f'{ttl} días' if ttl else 'No', ind], 1):
        celda(ws, i, j, v, f_mono if j == 1 else f_txt, center if j in (2, 4) else wrap)
tab = Table(displayName='Colecciones', ref=f'A1:E{len(mongo.C) + 1}')
tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
ws.add_table(tab)

ws = wb.create_sheet('MongoDB campos')
mfilas = list(csv.DictReader(open(os.path.join(REPO, 'diccionario_mongodb.csv'), encoding='utf-8-sig')))
cols = ['Colección', 'Fase', 'Campo', 'Tipo', 'Obligatorio', 'Valores permitidos', 'Significado']
encabezado(ws, 1, cols, [22, 8, 30, 11, 11, 40, 80])
for i, m in enumerate(mfilas, 2):
    for j, v in enumerate([m['coleccion'], m['fase'], m['campo'], m['tipo'], m['obligatorio'].capitalize(), m['valores'], m['significado']], 1):
        celda(ws, i, j, v, f_mono if j in (1, 3) else f_txt, center if j in (2, 4, 5) else wrap)
tab = Table(displayName='CamposMongo', ref=f'A1:G{len(mfilas) + 1}')
tab.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
ws.add_table(tab)
ws.freeze_panes = 'D2'

# Orden de hojas: Portada, Convenciones, Índice, Diccionario, Relaciones, Reglas, esquemas..., Mongo
orden = ['Portada', 'Convenciones', 'Índice de tablas', 'Cambios v5', 'Cambios v4', 'Funciones por finca', 'Diccionario completo', 'Relaciones', 'Reglas de negocio', 'Pruebas'] + list(ESQUEMAS) + ['MongoDB colecciones', 'MongoDB campos']
wb._sheets = [wb[n] for n in orden]
for n in list(ESQUEMAS):
    wb[n].sheet_properties.tabColor = '93C47D'
for n in ['Índice de tablas', 'Cambios v5', 'Cambios v4', 'Funciones por finca', 'Diccionario completo', 'Relaciones', 'Reglas de negocio', 'Pruebas']:
    wb[n].sheet_properties.tabColor = VERDE
for w in wb.worksheets:
    w.page_setup.orientation = 'landscape'; w.page_setup.paperSize = w.PAPERSIZE_LETTER
    w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 0; w.sheet_properties.pageSetUpPr.fitToPage = True
    w.print_options.horizontalCentered = True
    w.page_margins.left = w.page_margins.right = 0.4
    w.oddFooter.center.text = 'GuayacanERP · Diccionario de datos v5 · &A · Página &P de &N'
    w.oddFooter.center.size = 8
for n in ['Índice de tablas', 'Diccionario completo', 'Relaciones', 'Reglas de negocio', 'MongoDB colecciones', 'MongoDB campos']:
    wb[n].print_title_rows = '1:1'
wb.active = 0
wb.save(OUT)
print(OUT, len(filas), 'campos', len(mfilas), 'campos mongo')
