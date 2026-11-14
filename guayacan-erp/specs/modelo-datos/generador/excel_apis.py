"""GuayacanERP · Mapa de APIs y modelos: qué tabla va en qué API (Django monolito o FastAPI), con modelos, campos y endpoints."""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from modelo import ESQUEMAS, T, GLOBALES, CAPTURA, AUDITADAS
import mongo

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(BASE, '..')
OUT = os.path.join(BASE, '..', '..', '..', 'docs', 'manuales', 'GuayacanERP_Mapa_de_APIs_y_Modelos_v5.xlsx')
INFO = {f'{t[0]}.{t[1]}': t for t in T}
OPER = set(INFO) - GLOBALES
filas = list(csv.DictReader(open(os.path.join(REPO, 'diccionario_postgresql.csv'), encoding='utf-8-sig')))
COMUNES = {'id', 'predio_id', 'id_cliente', 'capturado_en', 'dispositivo_captura_id', 'creado_en', 'actualizado_en'}

# Orden de construcción manual de las apps Django (las llaves hacia apps posteriores se agregan en una migración después)
ORDEN = ['nucleo', 'seguridad', 'terceros', 'inventario', 'produccion', 'riego', 'comercial', 'compras', 'finanzas', 'ia', 'redes', 'turismo', 'iot', 'ambiental',
         'documental', 'formacion', 'personal', 'activos', 'nomina', 'cumplimiento', 'seguros', 'crm', 'estrategia', 'agenda', 'proyectos']


def camel(nombre):
    """Convierte nombre_con_guiones a NombreConGuiones (nombre del modelo de Django)."""
    return ''.join(p.capitalize() for p in nombre.split('_'))


def plural(p):
    """Pluraliza una palabra en español para armar el recurso REST (lote → lotes, raiz → raices)."""
    irregular = {'analisis': 'analisis', 'ia': 'ia', 'iot': 'iot', 'por': 'por', 'de': 'de'}
    if p in irregular:
        return irregular[p]
    if p.endswith('z'):
        return p[:-1] + 'ces'
    if p[-1] in 'aeiou':
        return p + 's'
    return p + 'es'


RECURSO = {  # nombres de recurso REST especiales (en plural, con guion)
    'personal.cuadrilla_miembro': 'cuadrillas/{cuadrilla_id}/miembros', 'personal.paso_tarea': 'tareas/{tarea_id}/pasos',
    'personal.evidencia_tarea': 'tareas/{tarea_id}/evidencias', 'personal.patron_turno_detalle': 'patrones-turno/{patron_id}/dias',
    'nomina.liquidacion_detalle': 'liquidaciones/{liquidacion_id}/detalles', 'activos.repuesto_orden': 'ordenes-trabajo/{orden_id}/repuestos',
    'finanzas.presupuesto_detalle': 'presupuestos/{presupuesto_id}/detalles', 'estrategia.flujo_proyecto': 'evaluaciones-proyecto/{evaluacion_id}/flujos',
    'proyectos.dependencia': 'actividades/{actividad_id}/dependencias', 'documental.version_documento': 'documentos/{documento_id}/versiones',
    'comercial.pedido_detalle': 'pedidos/{pedido_id}/lineas', 'compras.orden_compra_detalle': 'ordenes-compra/{orden_id}/lineas',
    'inventario.conteo_detalle': 'conteos/{conteo_id}/detalles', 'finanzas.movimiento_contable': 'comprobantes/{comprobante_id}/movimientos',
    'inventario.conteo_fisico': 'conteos', 'nucleo.usuario_rol': 'usuarios/{usuario_id}/roles', 'nucleo.rol_permiso': 'roles/{rol_id}/permisos',
    'ia.agente_herramienta': 'agentes/{agente_id}/herramientas', 'produccion.calidad_agua_estanque': 'calidad-agua',
    'iot.regla_automatizacion': 'reglas', 'iot.comando_actuador': 'comandos', 'comercial.propuesta_precio': 'propuestas-precio',
    'ia.solicitud_aprobacion': 'solicitudes-aprobacion', 'redes.politica_canal': 'politicas-canal', 'redes.mensaje_saliente': 'mensajes-salientes',
    'nucleo.dispositivo_captura': 'dispositivos-captura', 'terceros.consentimiento_datos': 'consentimientos', 'ia.consumo_ia': 'consumos',
}


def recurso(full):
    """Nombre del recurso REST de una tabla: 'produccion.lote_animal' → 'lotes-animal' (o el especial definido en RECURSO)."""
    if full in RECURSO:
        return RECURSO[full]
    partes = full.split('.')[1].split('_')
    partes[0] = plural(partes[0])
    return '-'.join(partes)


def campo_django(r, full):
    """Traduce una columna SQL al campo de modelo Django."""
    t, nombre, nulo = r['tipo'], r['campo'], r['admite_vacio'] == 'sí'
    args = []
    ref = r['referencia']
    vals = r['restricciones'].split('valores: ')[1] if 'valores: ' in r['restricciones'] else ''
    if nombre == 'id':
        return 'BigAutoField(primary_key=True)', 'Heredado de ModeloBase'
    if ref:
        if ref == 'redes.politica_canal':
            k = "models.ForeignKey('redes.PoliticaCanal', to_field='plataforma', db_column='plataforma', on_delete=models.PROTECT)"
        else:
            app, tab = ref.split('.')
            destino = 'settings.AUTH_USER_MODEL' if ref == 'nucleo.usuario' else f"'{app}.{camel(tab)}'"
            rel = f", related_name='+'" if ref in ('nucleo.usuario', 'ia.agente', 'nucleo.dispositivo_captura') else ''
            k = f"models.ForeignKey({destino}, db_column='{nombre}', on_delete=models.PROTECT{rel}"
            k += ', null=True, blank=True)' if nulo else ')'
            if full in OPER and ref in OPER:
                return k, 'Llave compuesta (predio_id, campo) creada con RunSQL en la migración'
        return k, ''
    if vals:
        n = max(len(v) for v in vals.split(', '))
        args = [f'max_length={max(20, n)}', f'choices={camel(nombre)}.choices']
        base = 'CharField'
        nota = f'TextChoices {camel(nombre)}: ' + vals
    else:
        nota = ''
        m = re.match(r'(\w+(?: \w+)?)(?:\(([^)]*)\))?', t)
        sql, par = m.group(1), m.group(2)
        if sql == 'varchar' or sql == 'char':
            base, args = 'CharField', [f'max_length={par}']
        elif sql == 'text':
            base = 'TextField'
        elif sql == 'citext':
            base, args, nota = 'EmailField', ['max_length=254'], 'Columna citext: correo sin distinguir mayúsculas'
        elif sql == 'numeric':
            d, s = par.split(',')
            base, args = 'DecimalField', [f'max_digits={d}', f'decimal_places={s}']
        elif sql == 'integer':
            base = 'IntegerField'
        elif sql == 'smallint':
            base = 'SmallIntegerField'
        elif sql == 'bigint':
            base = 'BigIntegerField'
        elif sql == 'boolean':
            base = 'BooleanField'
        elif sql == 'date':
            base = 'DateField'
        elif sql == 'timestamptz':
            base = 'DateTimeField'
        elif sql == 'jsonb':
            base = 'JSONField'
        elif sql == 'inet':
            base = 'GenericIPAddressField'
        elif sql == 'uuid':
            base = 'UUIDField'
        elif sql == 'double precision':
            base = 'FloatField'
        elif sql == 'geometry':
            g, srid = par.split(',')
            base, args, nota = f'{g.strip()}Field', [f'srid={srid.strip()}'], 'django.contrib.gis (GeoDjango + PostGIS)'
        elif sql == 'vector':
            base, args, nota = 'VectorField', [f'dimensions={par}'], 'pgvector.django'
        else:
            base = 'TextField'
    if 'único' in r['restricciones'] and full not in OPER:
        args.append('unique=True')
    if 'único por finca' in r['restricciones']:
        nota = (nota + '; ' if nota else '') + f"UniqueConstraint(fields=['predio', '{nombre}'])"
    d = r['valor_por_defecto']
    if d and d not in ('identidad', 'predio de la sesión'):
        if d == 'now()':
            args.append('default=timezone.now')
        elif d in ('true', 'false'):
            args.append(f'default={d.capitalize()}')
        elif re.fullmatch(r'-?\d+(\.\d+)?', d):
            args.append(f'default={d}')
        else:
            args.append(f"default='{d}'")
    if nulo:
        args += ['null=True', 'blank=True']
    prefijo = 'models.' if base not in ('VectorField',) else ''
    return f"{prefijo}{base}({', '.join(args)})", nota


def operaciones(full):
    """Operaciones REST permitidas y notas por tabla."""
    solo_lectura = {'nucleo.auditoria': 'Solo lectura: la base la llena con el disparador de auditoría',
                    'comercial.reserva_lote': 'Solo lectura: la crea la acción confirmar del pedido'}
    interna = {'nucleo.evento_salida': 'Interna: la escribe la base y la lee Celery (patrón outbox); sin endpoint',
               'nucleo.webhook_entrega': 'Interna: la escribe el despachador de webhooks (Celery)',
               'seguridad.intento_acceso': 'Interna: la escribe seguridad.registrar_intento() en cada inicio de sesión',
               'seguridad.sesion_usuario': 'Interna: la crea el inicio de sesión; se revoca con la acción revocar',
               'ia.fragmento_conocimiento': 'Interna: la genera la acción indexar del documento; la búsqueda va por la acción buscar'}
    solo_crear = {'inventario.movimiento_inventario': 'Inmutable: se crea, nunca se edita; las correcciones son ajustes',
                  'inventario.lectura_codigo': 'Se crea al escanear', 'inventario.pesaje': 'Se crea al pesar',
                  'redes.mensaje_saliente': 'La crea el conector de canales (FastAPI) con token de servicio',
                  'ia.consumo_ia': 'La alimenta el servicio de agentes (FastAPI) con token de servicio',
                  'ia.evaluacion_respuesta': 'La crean el cliente (desde FastAPI) o el administrador',
                  'nucleo.sincronizacion': 'La crea el endpoint de sincronización de la PWA', 'iot.lectura': 'La sube el servicio IoT en lotes',
                  'iot.comando_actuador': 'Se crea una orden; su estado lo actualiza el servicio IoT',
                  'comercial.precio_producto': 'Crear solo el precio inicial (administrador); los cambios van por propuestas',
                  'ia.solicitud_aprobacion': 'La crean los agentes por MCP; se resuelve con las acciones aprobar o rechazar',
                  'comercial.propuesta_precio': 'La crea el analista de mercados por MCP; se resuelve con aprobar o rechazar',
                  'agenda.registro_acceso': 'Inmutable: lo crea la portería (PWA sin conexión)', 'seguridad.ejecucion_prueba': 'La sube el CI al terminar cada corrida',
                  'finanzas.reporte_indicadores': 'Inmutable: se crea con la autorización del titular', 'finanzas.aplicacion_anticipo': 'Inmutable',
                  'proyectos.linea_base': 'La crea la aprobación del proyecto o de un cambio', 'proyectos.medicion_valor_ganado': 'La crea la acción valor-ganado'}
    sin_borrar = {'comercial.pedido': 'No se borra: se cancela con la acción cancelar', 'comercial.factura': 'No se edita ni se borra: la emite la regla DIAN',
                  'comercial.pago': 'No se borra: se reversa', 'inventario.lote_inventario': 'Cantidades de solo lectura; no se borra',
                  'finanzas.comprobante': 'Solo se borra en borrador; se contabiliza o anula con acciones', 'terceros.consentimiento_datos': 'No se borra: se revoca (revocado_en)',
                  'finanzas.periodo_contable': 'Se cierra con la acción cerrar',
                  'personal.tarea': 'No se borra: se cancela; aprobada no se edita', 'nomina.periodo_nomina': 'Se cierra con la acción cerrar (dos personas)',
                  'nomina.pago_nomina': 'No se borra; se aprueba y se marca pagado con acciones', 'seguridad.alerta_seguridad': 'Solo se registra su atención',
                  'agenda.visita': 'Se aprueba, rechaza o cancela; no se borra', 'proyectos.proyecto': 'Cambia de estado con acciones; no se borra'}
    if full in interna:
        return '—', interna[full]
    if full in solo_lectura:
        return 'GET', solo_lectura[full]
    if full in solo_crear:
        return 'GET, POST', solo_crear[full]
    if full in sin_borrar:
        return 'GET, POST, PATCH', sin_borrar[full]
    if full in GLOBALES:
        return 'GET, POST, PATCH', 'Catálogo compartido: escritura solo para el administrador del sistema'
    return 'GET, POST, PATCH, DELETE', ''


ROLES = {'nucleo': 'administrador', 'terceros': 'administrador, vendedor', 'produccion': 'operario_granja, administrador',
         'riego': 'operario_granja, administrador', 'inventario': 'operario_granja, vendedor, administrador', 'comercial': 'vendedor, administrador, cliente (sus pedidos)',
         'compras': 'administrador', 'finanzas': 'contador, administrador', 'ia': 'administrador', 'redes': 'administrador',
         'turismo': 'vendedor, administrador', 'iot': 'administrador, operario_granja', 'ambiental': 'administrador, operario_granja',
         'seguridad': 'administrador (atender alertas), sistema (inicio de sesión)', 'documental': 'administrador, encargado_finca',
         'formacion': 'instructor, estudiante, operario_granja, administrador', 'personal': 'encargado_finca, operario_granja, familia',
         'activos': 'encargado_finca, operario_granja', 'nomina': 'contador, familia (cierre y pagos)', 'cumplimiento': 'encargado_finca, administrador',
         'seguros': 'administrador, familia', 'crm': 'vendedor, administrador', 'estrategia': 'familia, administrador', 'agenda': 'porteria, encargado_finca, vendedor',
         'proyectos': 'director del proyecto, patrocinador (familia)'}

# ------------------------------------------------------------------------------------ estilos
F = 'Arial'
VERDE, AZUL = '1F4E3D', '1F3864'
f_tit, f_sub = Font(name=F, size=16, bold=True, color=VERDE), Font(name=F, size=10, italic=True, color='595959')
f_head, f_txt, f_bold = Font(name=F, size=10, bold=True, color='FFFFFF'), Font(name=F, size=10), Font(name=F, size=10, bold=True)
f_mono = Font(name='Consolas', size=9)
thin = Side(style='thin', color='BFBFBF'); borde = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap, center = Alignment(wrap_text=True, vertical='top'), Alignment(horizontal='center', vertical='top', wrap_text=True)
fill_dj, fill_fa, fill_desc = PatternFill('solid', fgColor='D9EAD3'), PatternFill('solid', fgColor='DDEBF7'), PatternFill('solid', fgColor='EEF5EA')


def hoja(wb, nombre, cols, anchos, titulo=None, color=VERDE):
    """Crea una hoja con título opcional y encabezados de color; devuelve la hoja y la fila donde empiezan los datos."""
    ws = wb.create_sheet(nombre)
    fila = 1
    if titulo:
        ws['A1'] = titulo; ws['A1'].font = f_tit; fila = 3
    for j, (c, w) in enumerate(zip(cols, anchos), 1):
        cell = ws.cell(fila, j, c)
        cell.font, cell.fill, cell.alignment, cell.border = f_head, PatternFill('solid', fgColor=color), center, borde
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.sheet_properties.tabColor = color
    return ws, fila


def fila_datos(ws, r, vals, mono=(), centro=()):
    """Escribe una fila de datos; las columnas en «mono» van en letra de código y las de «centro» centradas."""
    for j, v in enumerate(vals, 1):
        c = ws.cell(r, j, v)
        c.font = f_mono if j in mono else f_txt
        c.alignment = center if j in centro else wrap
        c.border = borde


def tabla_excel(ws, nombre, fila_ini, ncols, nfilas):
    """Convierte un rango en una «Tabla» de Excel (con filtros y filas rayadas) para poder ordenar y filtrar."""
    t = Table(displayName=nombre, ref=f'A{fila_ini}:{get_column_letter(ncols)}{fila_ini + nfilas}')
    t.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
    ws.add_table(t)


wb = Workbook()

# ------------------------------------------------------------------------------------ 1. Portada y servicios
ws = wb.active; ws.title = 'Servicios'
ws.sheet_view.showGridLines = False
ws['A1'] = 'GuayacanERP · Mapa de APIs, modelos y endpoints'; ws['A1'].font = f_tit
ws['A2'] = 'Qué construye cada API, en qué framework y con qué datos. Versión 5 del modelo (operación integral de la finca) · 2026-10-27'; ws['A2'].font = f_sub
cols = ['API / servicio', 'Framework', 'Tipo de arquitectura', 'Es dueño de', 'Base de datos', 'Prefijo de URL', 'Puerto local', 'Fase', 'Para qué sirve']
for j, (c, w) in enumerate(zip(cols, [24, 22, 24, 40, 22, 18, 10, 7, 60]), 1):
    cell = ws.cell(4, j, c); cell.font, cell.fill, cell.alignment, cell.border = f_head, PatternFill('solid', fgColor=VERDE), center, borde
    ws.column_dimensions[get_column_letter(j)].width = w
servicios = [
    ('Núcleo ERP (el monolito)', 'Django + Django REST Framework', f'Monolito modular: un solo proyecto, {len(ORDEN)} apps', f'Las {len(T)} tablas de PostgreSQL (una app por esquema)', 'PostgreSQL (+ PostGIS, pgvector)', '/api/v1/', 8000, '1-4', 'Toda la lógica de negocio: producción, inventario, ventas, compras, contabilidad, usuarios, aprobaciones. Es la única API que escribe en PostgreSQL.'),
    ('Tareas en segundo plano', 'Celery + Celery Beat (parte del proyecto Django)', 'Mismo código del monolito, otro proceso', 'Ninguna tabla propia: usa los modelos Django', 'PostgreSQL y Redis', '—', '—', '1', 'Publicar eventos outbox, marcar vencidos, informes, facturación DIAN, tareas programadas de los analistas.'),
    ('Servicio de agentes y canales', 'FastAPI + LangGraph + LiteLLM', 'Servicio independiente (microservicio)', 'Las 8 colecciones de MongoDB; sesiones en Redis', 'MongoDB y Redis', '/agentes/', 8100, '1-2', 'Webhooks de WhatsApp, Instagram, Messenger y TikTok, chat web, orquestador y 14 agentes. Lee y propone en el ERP solo por API (herramientas MCP).'),
    ('Servidor MCP de herramientas', 'FastAPI (SDK MCP de Python) dentro del servicio de agentes', 'Adaptador entre agentes y ERP', 'Ninguna tabla: traduce cada herramienta a un endpoint del ERP', '—', '/mcp', 8100, '1', 'Expone a los agentes las 25 herramientas (consultar_catalogo, proponer_precio, ...) con token de servicio de permisos mínimos.'),
    ('Servicio IoT de riego', 'FastAPI + cliente MQTT', 'Servicio independiente', 'Escribe lecturas en TimescaleDB y estados por API del ERP', 'TimescaleDB', '/iot/', 8200, '4', 'Recibe lo que sube la pasarela local, entrega reglas aprobadas y órdenes a las válvulas.'),
    ('Frontend (panel, tienda y PWA)', 'Angular', 'Aplicación cliente independiente', 'Nada en servidor: datos sin conexión en IndexedDB del celular', 'IndexedDB (Dexie)', '/', 4200, '1', 'Consume /api/v1/ (ERP) y /agentes/ (chat web y bandeja de conversaciones).')]
for i, s in enumerate(servicios, 5):
    fila_datos(ws, i, s, centro=(7, 8))
    for j in range(1, 10):
        ws.cell(i, j).fill = fill_dj if 'Django' in s[1] or 'Celery' in s[1] else (fill_fa if 'FastAPI' in s[1] else PatternFill())
r = 5 + len(servicios) + 1
notas = ['Django = el monolito. Son lo mismo: el núcleo ERP es un único proyecto Django dividido en 25 apps (monolito modular). Todas las tablas de PostgreSQL pertenecen a ese monolito.',
         'FastAPI = servicios aparte. No tienen tablas en PostgreSQL: el de agentes es dueño de MongoDB y el de IoT de TimescaleDB. Cuando necesitan datos del negocio, llaman a la API del ERP.',
         'Regla de oro: un dato tiene un solo dueño. Ningún servicio FastAPI escribe directo en PostgreSQL; si lo hiciera, se saltaría las reglas, la auditoría y la seguridad por finca.',
         'Verde = Django (monolito) · Azul = FastAPI. Las demás hojas siguen el mismo código de color.']
for n in notas:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
    c = ws.cell(r, 1, n); c.font = f_bold if n.startswith('Django') else f_txt; c.alignment = wrap; c.fill = fill_desc
    ws.row_dimensions[r].height = 30; r += 1

# ------------------------------------------------------------------------------------ 2. Apps Django
ws, h = hoja(wb, 'Django apps', ['Orden', 'App Django', 'Esquema SQL', 'Tablas', 'Modelos (clases)', 'Depende de', 'Llaves a apps posteriores (migración aparte)', 'Roles que la usan', 'Fase'],
             [7, 14, 13, 8, 60, 26, 50, 30, 7], f'Monolito Django · {len(ORDEN)} apps en orden de construcción')
r = h + 1
for i, app in enumerate(ORDEN, 1):
    tabs = [t for t in T if t[0] == app]
    deps, despues = set(), []
    for fr in filas:
        if fr['esquema'] == app and fr['referencia'] and fr['campo'] != 'predio_id':
            dest = fr['referencia'].split('.')[0]
            if dest == app:
                continue
            if ORDEN.index(dest) < ORDEN.index(app):
                deps.add(dest)
            else:
                despues.append(f"{fr['tabla']}.{fr['campo']} → {fr['referencia']}")
    if app != 'nucleo':
        deps.add('nucleo')
    fila_datos(ws, r, [i, app, app, len(tabs), ', '.join(camel(t[1]) for t in tabs), ', '.join(sorted(deps, key=ORDEN.index)) or '—',
                       '; '.join(despues) or '—', ROLES[app], ', '.join(sorted({str(t[2]) for t in tabs}))], mono=(2, 3), centro=(1, 4, 9))
    r += 1
tabla_excel(ws, 'Apps', h, 9, len(ORDEN))
ws.freeze_panes = f'C{h + 1}'

# ------------------------------------------------------------------------------------ 3. Modelos Django (tablas)
ws, h = hoja(wb, 'Django modelos', ['App', 'Modelo (clase)', 'db_table', 'Hereda de', 'Endpoint REST', 'Operaciones', 'Seguridad', 'Fase', 'Qué guarda'],
             [12, 26, 34, 40, 44, 22, 34, 7, 70], 'Modelos Django: una clase por tabla')
r = h + 1
for app in ORDEN:
    for t in [x for x in T if x[0] == app]:
        full = f'{t[0]}.{t[1]}'
        hereda = ['ModeloBase']
        if full in OPER:
            hereda = ['ModeloPorFinca']
        if full in CAPTURA:
            hereda.append('CapturableSinConexion')
        if full == 'nucleo.usuario':
            hereda = ['AbstractBaseUser', 'PermissionsMixin']
        if not t[6]:
            hereda = ['models.Model (sin fechas de auditoría)'] if full not in OPER else ['ModeloPorFinca (sin fechas)']
        ops, nota = operaciones(full)
        seg = ('RLS por finca' if full in OPER else 'Catálogo compartido') + (' · auditada' if full in AUDITADAS else '')
        url = '— (interna)' if ops == '—' else f'/api/v1/{app}/{recurso(full)}/'
        fila_datos(ws, r, [app, camel(t[1]), f"db_table = '{t[0]}\"\".\"\"{t[1]}'".replace('\"\"', '"'), ', '.join(hereda), url, ops, seg, t[2], t[3] + (f' · {nota}' if nota else '')], mono=(2, 3, 5), centro=(8,))
        r += 1
tabla_excel(ws, 'Modelos', h, 9, len(T))
ws.freeze_panes = f'C{h + 1}'

# ------------------------------------------------------------------------------------ 4. Campos Django
ws, h = hoja(wb, 'Django campos', ['App', 'Modelo', 'Campo (atributo)', 'Columna SQL', 'Tipo SQL', 'Campo Django', 'Obligatorio', 'Nota de implementación', 'verbose_name / help_text'],
             [11, 24, 26, 26, 18, 70, 10, 46, 60], 'Propiedades de cada modelo Django (campo por campo)')
r = h + 1
n = 0
for app in ORDEN:
    for t in [x for x in T if x[0] == app]:
        full = f'{t[0]}.{t[1]}'
        for fr in [x for x in filas if x['esquema'] == app and x['tabla'] == t[1]]:
            if fr['campo'] in COMUNES and fr['campo'] != 'id' and not (fr['campo'] == 'dispositivo_captura_id' and full not in CAPTURA) and not (fr['campo'] == 'predio_id' and full not in OPER):
                continue
            if fr['campo'] == 'id':
                continue
            dj, nota = campo_django(fr, full)
            atributo = fr['campo'][:-3] if fr['campo'].endswith('_id') and fr['referencia'] else fr['campo']
            if fr['campo'] in ('aprobado_por', 'registrado_por', 'revisado_por', 'resuelto_por', 'solicitado_por', 'confirmado_por', 'cerrado_por', 'asignado_a', 'plataforma'):
                atributo = fr['campo']
            if full == 'nucleo.usuario' and fr['campo'] == 'contrasena_hash':
                dj, nota = "password = models.CharField(max_length=255, db_column='contrasena_hash')", 'Campo de AbstractBaseUser renombrado a la columna en español'
                atributo = 'password'
            if full == 'nucleo.usuario' and fr['campo'] == 'ultimo_ingreso':
                dj, nota, atributo = "last_login = models.DateTimeField(null=True, blank=True, db_column='ultimo_ingreso')", 'Campo de AbstractBaseUser', 'last_login'
            fila_datos(ws, r, [app, camel(t[1]), atributo, fr['campo'], fr['tipo'], dj, 'Sí' if fr['admite_vacio'] == 'no' else 'No', nota, fr['significado']],
                       mono=(2, 3, 4, 5, 6), centro=(7,))
            r += 1; n += 1
tabla_excel(ws, 'CamposDjango', h, 9, n)
ws.freeze_panes = f'D{h + 1}'
r += 1
base_txt = ['Clases base (app nucleo/modelos_base.py), de donde heredan los modelos para no repetir campos:',
            'ModeloBase: creado_en = DateTimeField(auto_now_add=True) · actualizado_en = DateTimeField(auto_now=True) · class Meta: abstract = True',
            "ModeloPorFinca(ModeloBase): predio = ForeignKey('nucleo.Predio', db_column='predio_id', on_delete=PROTECT, editable=False) · el valor lo pone la base con la sesión (RLS)",
            "CapturableSinConexion: id_cliente = UUIDField(unique=True, null=True) · capturado_en = DateTimeField(null=True) · dispositivo_captura = ForeignKey('nucleo.DispositivoCaptura', null=True)",
            'Las llaves compuestas (predio_id, campo) y las reglas en SQL (disparadores, funciones, vistas, RLS) se crean con migrations.RunSQL leyendo reglas_negocio.sql: Django no las genera solo.']
for txt in base_txt:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
    c = ws.cell(r, 1, txt); c.font = f_bold if txt.startswith('Clases') else f_mono; c.alignment = wrap; c.fill = fill_desc; r += 1

# ------------------------------------------------------------------------------------ 5. Endpoints Django
ws, h = hoja(wb, 'Django endpoints', ['App', 'Método', 'URL', 'Qué hace', 'Tabla o función', 'Quién lo usa', 'Fase'],
             [12, 9, 58, 70, 40, 34, 7], 'Endpoints del monolito Django (/api/v1/)')
eps = []
# autenticación y transversales
eps += [('nucleo', 'GET', '/api/salud/', 'Comprueba que el ERP y la base responden', '—', 'Docker, monitoreo', 1),
        ('nucleo', 'POST', '/api/v1/auth/token/', 'Inicia sesión y entrega JWT de acceso y de refresco', 'nucleo.usuario', 'Todos', 1),
        ('nucleo', 'POST', '/api/v1/auth/token/refrescar/', 'Renueva el JWT con rotación del token de refresco', '—', 'Todos', 1),
        ('nucleo', 'GET', '/api/v1/auth/yo/', 'Datos del usuario y su rol en la finca activa', 'nucleo.usuario, nucleo.usuario_rol', 'Todos', 1),
        ('nucleo', 'GET', '/api/v1/auth/mis-fincas/', 'Fincas a las que puede entrar el usuario', 'nucleo.predios_del_usuario()', 'Todos', 1),
        ('nucleo', 'POST', '/api/v1/auth/cambiar-finca/', 'Cambia la finca activa (nuevo JWT con predio_id)', 'nucleo.usuario_rol', 'Todos', 1),
        ('nucleo', 'GET', '/api/v1/nucleo/parametros/vigentes/', 'Parámetros vigentes hoy (nacionales y de la finca)', 'nucleo.parametro', 'Todos', 1),
        ('nucleo', 'POST', '/api/v1/sincronizacion/', 'Recibe el lote de registros capturados sin conexión; idempotente por id_cliente; responde por registro', '17 tablas de captura + nucleo.sincronizacion', 'PWA de campo', 1),
        ('nucleo', 'GET', '/api/v1/sincronizacion/cambios/?desde=', 'Cambios del servidor para el caché del celular (catálogo, lotes, precios)', 'Varias', 'PWA de campo', 1)]
for app in ORDEN:
    for t in [x for x in T if x[0] == app]:
        full = f'{t[0]}.{t[1]}'
        ops, nota = operaciones(full)
        if ops == '—':
            continue
        base = f'/api/v1/{app}/{recurso(full)}/'
        roles = 'administrador del sistema' if full in GLOBALES and 'POST' in ops else ROLES[app]
        if 'GET' in ops:
            eps.append((app, 'GET', base, f'Lista {t[1]} con filtros, orden y paginación', full, ROLES[app], t[2]))
            eps.append((app, 'GET', base + '{id}/', f'Detalle de un registro de {t[1]}', full, ROLES[app], t[2]))
        if 'POST' in ops:
            eps.append((app, 'POST', base, f'Crea un registro de {t[1]}' + (f' · {nota}' if nota else ''), full, roles, t[2]))
        if 'PATCH' in ops:
            eps.append((app, 'PATCH', base + '{id}/', f'Modifica campos de {t[1]}', full, roles, t[2]))
        if 'DELETE' in ops:
            eps.append((app, 'DELETE', base + '{id}/', f'Elimina (o desactiva) un registro de {t[1]}', full, roles, t[2]))
acciones = [
    ('inventario', 'GET', '/api/v1/inventario/alertas-vencimiento/', 'Semáforo de vencimiento con precio de liquidación', 'inventario.v_alertas_vencimiento', 'vendedor, administrador, agentes (MCP)', 1),
    ('inventario', 'POST', '/api/v1/inventario/lotes/{id}/etiquetas/', 'Genera e imprime la etiqueta Code 128 o QR del lote', 'inventario.etiqueta', 'operario_granja', 1),
    ('inventario', 'POST', '/api/v1/inventario/escanear/', 'Resuelve un código leído: lote, vencimiento, acción sugerida', 'inventario.lectura_codigo', 'operario_granja, vendedor', 1),
    ('inventario', 'POST', '/api/v1/inventario/conteos/{id}/ajustar/', 'Genera los ajustes de las diferencias del conteo', 'inventario.movimiento_inventario', 'administrador', 1),
    ('comercial', 'GET', '/api/v1/comercial/catalogo/', 'Catálogo vendible hoy con precio vigente, sin costos', 'comercial.v_catalogo_disponible', 'cliente, vendedor, agentes (MCP)', 1),
    ('comercial', 'POST', '/api/v1/comercial/pedidos/{id}/confirmar/', 'Valida precio vigente, reserva FEFO y calcula totales', 'comercial.confirmar_pedido()', 'vendedor', 1),
    ('comercial', 'POST', '/api/v1/comercial/pedidos/{id}/despachar/', 'Convierte las reservas en salidas de venta', 'comercial.despachar_pedido()', 'vendedor, operario_granja', 1),
    ('comercial', 'POST', '/api/v1/comercial/pedidos/{id}/cancelar/', 'Libera las reservas de un pedido que no ha salido', 'comercial.cancelar_pedido()', 'vendedor, administrador', 1),
    ('comercial', 'POST', '/api/v1/comercial/pedidos/{id}/facturar/', 'Emite la factura electrónica por la regla DIAN (tarea Celery)', 'comercial.factura', 'vendedor, contador', 1),
    ('comercial', 'POST', '/api/v1/comercial/pagos/{id}/confirmar/', 'Una persona verifica el ingreso del dinero', 'comercial.pago', 'administrador, contador', 1),
    ('comercial', 'POST', '/api/v1/comercial/propuestas-precio/{id}/aprobar/', 'Aprueba y aplica el precio (lo vendido no cambia)', 'comercial.aplicar_propuesta_precio()', 'administrador', 1),
    ('comercial', 'POST', '/api/v1/comercial/propuestas-precio/{id}/rechazar/', 'Rechaza con motivo (queda como aprendizaje del agente)', 'comercial.propuesta_precio', 'administrador', 1),
    ('finanzas', 'POST', '/api/v1/finanzas/comprobantes/{id}/contabilizar/', 'Contabiliza si débitos = créditos y el periodo está abierto', 'finanzas.validar_cuadre()', 'contador', 1),
    ('finanzas', 'POST', '/api/v1/finanzas/comprobantes/{id}/anular/', 'Anula con motivo un comprobante contabilizado', 'finanzas.proteger_comprobante()', 'contador', 1),
    ('finanzas', 'POST', '/api/v1/finanzas/periodos-contables/{id}/cerrar/', 'Cierra el mes contable', 'finanzas.periodo_contable', 'contador', 1),
    ('ia', 'POST', '/api/v1/ia/solicitudes-aprobacion/{id}/aprobar/', 'Aprueba la acción que pidió un agente y la ejecuta con la regla del ERP', 'ia.solicitud_aprobacion', 'administrador', 1),
    ('ia', 'POST', '/api/v1/ia/solicitudes-aprobacion/{id}/rechazar/', 'Rechaza con motivo', 'ia.solicitud_aprobacion', 'administrador', 1),
    ('ia', 'POST', '/api/v1/ia/documentos-conocimiento/{id}/indexar/', 'Divide el documento en fragmentos y calcula sus vectores', 'ia.fragmento_conocimiento', 'administrador (tarea Celery)', 1),
    ('ia', 'GET', '/api/v1/ia/conocimiento/buscar/?q=', 'Búsqueda por significado en la base de conocimiento (pgvector)', 'ia.fragmento_conocimiento', 'agentes (MCP)', 1),
    ('ia', 'GET', '/api/v1/ia/indicadores/?desde=&hasta=', 'Indicadores de producción, ventas y costos por centro de costo', 'Varias (consultas de lectura)', 'administrador, agentes (MCP)', 1),
    ('redes', 'POST', '/api/v1/redes/verificar-envio/', 'Decide si un mensaje puede salir (ventana, plantilla, consentimiento, tope)', 'redes.verificar_envio()', 'servicio de agentes (FastAPI)', 1),
    ('redes', 'POST', '/api/v1/redes/publicaciones/{id}/aprobar/', 'Aprueba una publicación redactada por el gestor de redes', 'redes.publicacion', 'administrador', 2),
    ('redes', 'POST', '/api/v1/redes/plantillas-mensaje/{id}/enviar-a-meta/', 'Envía la plantilla a revisión de Meta', 'redes.plantilla_mensaje', 'administrador', 1),
    ('terceros', 'GET', '/api/v1/terceros/terceros/{id}/exportar-datos/', 'Exporta los datos personales del titular (Ley 1581)', 'terceros.* y MongoDB (vía FastAPI)', 'administrador', 1),
    ('terceros', 'POST', '/api/v1/terceros/terceros/{id}/suprimir-datos/', 'Suprime o anonimiza los datos personales a pedido del titular', 'terceros.* y MongoDB (vía FastAPI)', 'administrador', 1),
    ('terceros', 'POST', '/api/v1/terceros/consentimientos/{id}/revocar/', 'Revoca una autorización (llena revocado_en)', 'terceros.consentimiento_datos', 'administrador, cliente', 1),
    ('iot', 'POST', '/api/v1/iot/reglas/{id}/activar/', 'Una persona activa una regla de riego (nacen inactivas)', 'iot.regla_automatizacion', 'administrador', 4),
    ('nucleo', 'POST', '/api/v1/nucleo/funcionalidades/{codigo}/activar/', 'Enciende una función en la finca (crédito, permuta, cámaras…); queda quién y cuándo', 'nucleo.funcionalidad', 'administrador', 1),
    ('nucleo', 'POST', '/api/v1/nucleo/notas-voz/{id}/confirmar/', 'El operario confirma lo interpretado de su nota de voz y se crea el registro', 'nucleo.nota_voz', 'operario_granja', 2),
    ('inventario', 'POST', '/api/v1/inventario/bloqueos-lote/{id}/decidir/', 'Una persona libera o descarta un lote bloqueado', 'inventario.aplicar_bloqueo()', 'administrador', 2),
    ('inventario', 'POST', '/api/v1/inventario/excursiones-temperatura/', 'El servicio IoT reporta una excursión; la regla bloquea los lotes si supera la tolerancia', 'inventario.evaluar_excursion()', 'servicio IoT (FastAPI)', 2),
    ('comercial', 'GET', '/api/v1/comercial/lotes/{id}/trazabilidad/', 'Origen del lote y clientes que lo recibieron', 'comercial.v_trazabilidad_lote', 'administrador', 1),
    ('comercial', 'POST', '/api/v1/comercial/lotes/{id}/retirar/', 'Abre el retiro: bloquea el lote y crea los avisos a clientes', 'comercial.abrir_retiro()', 'administrador', 1),
    ('comercial', 'GET', '/api/v1/comercial/trazabilidad/verificar/', 'Verifica la cadena de huellas SHA-256', 'comercial.verificar_cadena_huellas()', 'administrador, compradores autorizados', 1),
    ('comercial', 'GET', '/api/v1/comercial/cartera/', 'Saldo por factura y edad de la deuda', 'comercial.v_cartera', 'contador, administrador', 2),
    ('comercial', 'POST', '/api/v1/comercial/pedidos-recurrentes/generar/', 'Crea en borrador los pedidos recurrentes del día (tarea Celery)', 'comercial.generar_pedidos_recurrentes()', 'tarea programada', 2),
    ('comercial', 'POST', '/api/v1/comercial/pagos/webhook/{pasarela}/', 'Recibe la confirmación firmada de Wompi, Mercado Pago, ePayco o PayU (idempotente)', 'comercial.pago', 'pasarela de pago', 2),
    ('produccion', 'GET', '/api/v1/produccion/categorias-huevo/clasificar/?peso_g=', 'Categoría del huevo según el peso leído en la báscula', 'produccion.clasificar_por_peso()', 'operario_granja', 1),
    ('redes', 'POST', '/api/v1/redes/piezas-audiovisuales/{id}/aprobar/', 'Aprueba un video o time-lapse (verifica autorizaciones de imagen)', 'redes.validar_pieza()', 'administrador', 2),
    ('iot', 'POST', '/api/v1/iot/zonas-seguridad/{id}/estado/', 'Arma, desarma o pone en modo noche o mantenimiento', 'iot.cambiar_estado_alarma()', 'administrador', 4),
    ('iot', 'POST', '/api/v1/iot/eventos-seguridad/{id}/atender/', 'Registra quién atendió el evento y qué encontró', 'iot.evento_seguridad', 'administrador, operario_granja', 4),
    ('ambiental', 'GET', '/api/v1/ambiental/indicadores/?mes=', 'Indicadores ambientales con CO₂ estimado y su fuente', 'ambiental.v_indicadores', 'administrador, gestor de redes (MCP)', 2),
    ('seguridad', 'POST', '/api/v1/auth/doble-factor/verificar/', 'Segundo paso del inicio de sesión (TOTP o llave de acceso)', 'seguridad.factor_autenticacion, sesion_usuario', 'Todos', 1),
    ('seguridad', 'POST', '/api/v1/seguridad/sesiones/{id}/revocar/', 'Revoca una sesión o todas las de un usuario', 'seguridad.revocar_sesiones()', 'administrador', 1),
    ('seguridad', 'GET', '/api/v1/seguridad/tablero/', 'Alertas, bloqueos, accesos fallidos, incidentes, pruebas y copias', 'seguridad.v_tablero', 'administrador', 1),
    ('seguridad', 'POST', '/api/v1/seguridad/bloqueos/{id}/levantar/', 'Una persona levanta un bloqueo', 'seguridad.bloqueo', 'administrador', 1),
    ('personal', 'POST', '/api/v1/personal/tareas/generar-dia/', 'Crea las tareas del día desde el plan de labores (tarea Celery)', 'personal.generar_tareas_del_dia()', 'tarea programada', 2),
    ('personal', 'POST', '/api/v1/personal/tareas/{id}/aprobar/', 'Aprueba o devuelve una tarea terminada', 'personal.validar_tarea()', 'encargado_finca, responsable del área', 2),
    ('personal', 'POST', '/api/v1/personal/cronogramas/{id}/generar/', 'Genera los turnos desde los patrones', 'personal.generar_turnos()', 'encargado_finca', 2),
    ('personal', 'GET', '/api/v1/personal/cronogramas/{id}/huecos/', 'Horas sin la cobertura mínima', 'personal.huecos_cobertura()', 'encargado_finca', 2),
    ('personal', 'POST', '/api/v1/personal/cronogramas/{id}/publicar/', 'Publica el cronograma si cumple jornada, descanso y cobertura', 'personal.publicar_cronograma()', 'encargado_finca', 2),
    ('nomina', 'POST', '/api/v1/nomina/periodos/{id}/prenomina/', 'Reúne salario, auxilio, jornales y destajo', 'nomina.preparar_prenomina()', 'contador, encargado_finca', 2),
    ('nomina', 'POST', '/api/v1/nomina/periodos/{id}/liquidar/', 'Liquida devengado, deducciones, neto y prestaciones', 'nomina.liquidar()', 'contador', 2),
    ('nomina', 'POST', '/api/v1/nomina/periodos/{id}/cerrar/', 'Cierra con dos personas y comprobante contabilizado', 'nomina.proteger_periodo()', 'familia, contador', 2),
    ('nomina', 'GET', '/api/v1/nomina/periodos/{id}/pila/', 'Genera el archivo de la planilla PILA', 'nomina.planilla_pila', 'contador', 2),
    ('nomina', 'GET', '/api/v1/nomina/periodos/{id}/exportar/?formato=', 'Exporta la nómina para el programa del contador', 'nomina.exportacion_nomina', 'contador', 2),
    ('formacion', 'POST', '/api/v1/formacion/sesiones-presenciales/{id}/certificar/', 'Emite los certificados de los asistentes', 'formacion.certificar_sesion()', 'instructor', 2),
    ('activos', 'POST', '/api/v1/activos/ordenes-trabajo/generar/', 'Crea las órdenes de mantenimiento vencidas (tarea Celery)', 'activos.generar_ordenes_trabajo()', 'tarea programada', 2),
    ('activos', 'POST', '/api/v1/activos/depreciar/?mes=', 'Calcula la depreciación del mes', 'activos.depreciar_mes()', 'contador', 2),
    ('documental', 'GET', '/api/v1/documental/vigentes/', 'Documentos con su versión aprobada y vencimiento', 'documental.v_vigentes', 'todos, agentes (MCP)', 1),
    ('cumplimiento', 'POST', '/api/v1/cumplimiento/expedientes/{id}/evaluar/', 'Revisa los requisitos contra su evidencia', 'cumplimiento.evaluar_expediente()', 'encargado_finca', 1),
    ('cumplimiento', 'GET', '/api/v1/cumplimiento/granja-biosegura/', 'Alerta de 200 aves sin certificado ICA', 'cumplimiento.v_granja_biosegura', 'administrador', 1),
    ('cumplimiento', 'GET', '/api/v1/cumplimiento/expedientes/{id}/paquete-auditor/', 'Exporta requisitos con su evidencia vigente', 'cumplimiento.*', 'administrador', 2),
    ('finanzas', 'GET', '/api/v1/finanzas/estado-resultados/?desde=&hasta=&centro=', 'Estado de resultados por costeo variable', 'finanzas.estado_resultados()', 'contador, familia, agentes (MCP)', 2),
    ('finanzas', 'GET', '/api/v1/finanzas/balance/?hasta=', 'Balance general', 'finanzas.balance_general()', 'contador, familia', 2),
    ('finanzas', 'GET', '/api/v1/finanzas/analisis/?a=&b=', 'Análisis vertical y horizontal', 'finanzas.analisis_vertical_horizontal()', 'contador, familia', 2),
    ('finanzas', 'GET', '/api/v1/finanzas/fuentes-usos/?a=&b=', 'Estado de fuentes y usos', 'finanzas.fuentes_usos()', 'contador, familia', 2),
    ('finanzas', 'POST', '/api/v1/finanzas/indicadores/calcular/', 'Calcula indicadores con semáforo', 'finanzas.calcular_indicadores()', 'contador (tarea mensual)', 2),
    ('finanzas', 'GET', '/api/v1/finanzas/palancas/?q=&p=&cv=&cf=&i=', 'Punto de equilibrio y grados de palanca', 'finanzas.palancas()', 'familia, estratega (MCP)', 2),
    ('estrategia', 'POST', '/api/v1/estrategia/evaluaciones-proyecto/{id}/calcular/', 'VPN, TIR, ROI, recuperación y palancas', 'estrategia.evaluar_proyecto()', 'familia, estratega (MCP)', 2),
    ('estrategia', 'GET', '/api/v1/estrategia/retorno/', 'Retorno proyectado contra real de cada iniciativa', 'estrategia.v_retorno_iniciativas', 'familia', 2),
    ('estrategia', 'GET', '/api/v1/estrategia/lineas/', 'Ingreso, margen y utilidad de cada sección', 'estrategia.v_matriz_lineas', 'familia', 2),
    ('crm', 'POST', '/api/v1/crm/captura/{formulario}/', 'Formulario público de captura con autorización de datos (web o QR en feria)', 'crm.prospecto, terceros.consentimiento_datos', 'público', 2),
    ('crm', 'POST', '/api/v1/crm/prospectos/{id}/calificar/', 'Recalcula el puntaje', 'crm.calificar()', 'vendedor', 2),
    ('crm', 'POST', '/api/v1/crm/prospectos/{id}/convertir/', 'Convierte en tercero y cliente', 'crm.convertir_prospecto()', 'vendedor', 2),
    ('crm', 'GET', '/api/v1/crm/embudo/', 'Embudo, campañas y proyección de ventas', 'crm.v_embudo, v_campanas, v_proyeccion_ventas', 'vendedor, familia', 2),
    ('agenda', 'GET', '/api/v1/agenda/dia/?fecha=', 'Agenda unificada: citas, visitas y turnos', 'agenda.v_agenda_dia', 'encargado_finca, porteria', 3),
    ('agenda', 'GET', '/api/v1/agenda/recursos/{id}/disponible/?desde=&hasta=', 'Disponibilidad de una cabaña o recurso', 'agenda.recurso_libre()', 'vendedor, cliente, guía virtual (MCP)', 3),
    ('agenda', 'POST', '/api/v1/agenda/visitas/{id}/aprobar/', 'Aprueba la visita (declaración de bioseguridad)', 'agenda.validar_visita()', 'encargado_finca', 2),
    ('agenda', 'POST', '/api/v1/agenda/visitas/{id}/pase/', 'Emite el pase QR', 'agenda.emitir_pase()', 'encargado_finca', 2),
    ('agenda', 'GET', '/api/v1/agenda/en-sitio/', 'Quién y qué vehículo está dentro ahora', 'agenda.v_en_sitio', 'porteria, administrador', 2),
    ('proyectos', 'POST', '/api/v1/proyectos/proyectos/{id}/aprobar/', 'El patrocinador aprueba el acta y nace la línea base', 'proyectos.validar_proyecto()', 'patrocinador', 2),
    ('proyectos', 'POST', '/api/v1/proyectos/proyectos/{id}/ruta-critica/', 'Calcula la ruta crítica', 'proyectos.calcular_ruta_critica()', 'director del proyecto', 2),
    ('proyectos', 'POST', '/api/v1/proyectos/proyectos/{id}/valor-ganado/?corte=', 'Mide PV, EV, AC, CPI y SPI', 'proyectos.calcular_valor_ganado()', 'director del proyecto', 2),
    ('proyectos', 'POST', '/api/v1/proyectos/solicitudes-cambio/{id}/decidir/', 'Aprueba o rechaza el cambio', 'proyectos.decidir_cambio()', 'patrocinador, comité', 2),
    ('proyectos', 'GET', '/api/v1/proyectos/tablero/', 'Tablero de proyectos', 'proyectos.v_tablero', 'familia, director', 2),
    ('iot', 'POST', '/api/v1/iot/misiones-robot/{id}/aprobar/', 'Una persona aprueba la misión de dron o robot', 'iot.validar_mision()', 'administrador', 4),
    ('nucleo', 'GET', '/api/b2b/v1/catalogo/', 'API B2B con llave del cliente: catálogo vendible', 'comercial.v_catalogo_disponible', 'clientes HORECA', 3),
    ('nucleo', 'POST', '/api/b2b/v1/pedidos/', 'API B2B: pedido en borrador del cliente', 'comercial.pedido', 'clientes HORECA', 3)]
eps += acciones
r = h + 1
for e in eps:
    fila_datos(ws, r, e, mono=(3, 5), centro=(2, 7)); r += 1
tabla_excel(ws, 'EndpointsDjango', h, 7, len(eps))
ws.freeze_panes = f'C{h + 1}'

# ------------------------------------------------------------------------------------ 6. FastAPI endpoints
ws, h = hoja(wb, 'FastAPI endpoints', ['Servicio', 'Método', 'URL', 'Qué hace', 'Datos que usa', 'Quién lo llama', 'Fase'],
             [16, 9, 52, 70, 44, 30, 7], 'Endpoints de los servicios FastAPI', color=AZUL)
fa = [
    ('agentes', 'GET', '/agentes/salud', 'Comprueba el servicio, MongoDB, Redis y el proveedor de IA', '—', 'Docker, monitoreo', 1),
    ('agentes', 'GET', '/agentes/webhooks/whatsapp', 'Verificación del webhook (hub.challenge de Meta)', '—', 'Meta', 1),
    ('agentes', 'POST', '/agentes/webhooks/whatsapp', 'Recibe mensajes y estados de entrega de WhatsApp; verifica la firma X-Hub-Signature-256', 'conversaciones, mensajes', 'Meta', 1),
    ('agentes', 'GET/POST', '/agentes/webhooks/instagram', 'Verificación y mensajes directos, comentarios y menciones de Instagram', 'conversaciones, mensajes, eventos_redes', 'Meta', 2),
    ('agentes', 'GET/POST', '/agentes/webhooks/messenger', 'Verificación y mensajes de Messenger', 'conversaciones, mensajes', 'Meta', 2),
    ('agentes', 'POST', '/agentes/webhooks/tiktok', 'Mensajes de TikTok recibidos por el proveedor (Infobip o respond.io)', 'conversaciones, mensajes', 'Proveedor de TikTok', 2),
    ('agentes', 'WS', '/agentes/chat/web', 'Chat de la página web en tiempo real (WebSocket)', 'conversaciones, mensajes', 'Frontend Angular', 1),
    ('agentes', 'POST', '/agentes/chat/web/mensajes', 'Alternativa HTTP al WebSocket para enviar un mensaje', 'conversaciones, mensajes', 'Frontend Angular', 1),
    ('agentes', 'GET', '/agentes/conversaciones', 'Bandeja de conversaciones con filtros (canal, estado, escaladas)', 'conversaciones', 'Panel del administrador', 1),
    ('agentes', 'GET', '/agentes/conversaciones/{id}/mensajes', 'Historial de una conversación', 'mensajes', 'Panel del administrador', 1),
    ('agentes', 'POST', '/agentes/conversaciones/{id}/tomar', 'Una persona toma la conversación; el agente deja de responder', 'conversaciones; ERP ia.escalamiento', 'Panel del administrador', 1),
    ('agentes', 'POST', '/agentes/conversaciones/{id}/responder', 'Respuesta de una persona (usa la extensión de 7 días donde aplica)', 'mensajes; ERP redes.verificar_envio', 'Panel del administrador', 1),
    ('agentes', 'POST', '/agentes/conversaciones/{id}/devolver-al-agente', 'Devuelve la conversación al agente', 'conversaciones', 'Panel del administrador', 1),
    ('agentes', 'POST', '/agentes/conversaciones/{id}/cerrar', 'Cierra la conversación y guarda el resumen', 'conversaciones', 'Panel, agentes', 1),
    ('agentes', 'POST', '/agentes/mensajes/{id}/calificar', 'Calificación de una respuesta (se guarda en el ERP)', 'ERP ia.evaluacion_respuesta', 'Cliente, administrador', 1),
    ('agentes', 'POST', '/agentes/tareas/{agente}/ejecutar', 'Ejecuta a demanda un agente analista (mercados, negocio, contable)', 'bitacora_agentes, informes_mercado', 'Administrador, Celery Beat', 1),
    ('agentes', 'GET', '/agentes/ejecuciones', 'Bitácora de ejecuciones de los agentes (costo, tiempo, herramientas)', 'bitacora_agentes', 'Panel del administrador', 1),
    ('agentes', 'GET', '/agentes/informes-mercado', 'Informes del analista de mercados', 'informes_mercado', 'Panel del administrador', 1),
    ('agentes', 'GET', '/agentes/tendencias', 'Temas, preguntas frecuentes y productos más consultados', 'tendencias', 'Panel del administrador', 2),
    ('agentes', 'GET', '/agentes/clientes/{tercero_id}/perfil-interes', 'Perfil de intereses (solo con consentimiento vigente)', 'perfiles_interes', 'Panel, vendedor personalizado', 2),
    ('agentes', 'DELETE', '/agentes/clientes/{tercero_id}/datos', 'Borra conversaciones, mensajes y perfil del titular (Ley 1581)', 'conversaciones, mensajes, perfiles_interes', 'ERP (supresión de datos)', 1),
    ('agentes', 'POST', '/mcp', 'Servidor MCP (HTTP transmitible): lista y ejecuta las herramientas de los agentes', 'Ver hoja Herramientas MCP', 'Agentes (internos)', 1),
    ('agentes', 'Consumidor', 'Redis Stream guayacan:eventos (grupo agentes)', 'Lee pedido.confirmado, precio.aplicado, etc. y actualiza perfiles e historial', 'perfiles_interes, conversaciones', 'Celery (outbox del ERP)', 1),
    ('iot', 'GET', '/iot/salud', 'Estado del servicio y última sincronización de cada pasarela', '—', 'Monitoreo', 4),
    ('iot', 'POST', '/iot/pasarelas/{codigo}/lecturas', 'Recibe en lote las lecturas guardadas por la pasarela (idempotente por sensor y medido_en)', 'TimescaleDB iot.lectura', 'Pasarela local', 4),
    ('iot', 'GET', '/iot/pasarelas/{codigo}/reglas', 'Reglas activas y su versión para bajar a la finca', 'ERP iot.regla_automatizacion', 'Pasarela local', 4),
    ('iot', 'POST', '/iot/pasarelas/{codigo}/reglas/{id}/desplegada', 'Confirma la versión instalada (desplegada_version)', 'ERP iot.regla_automatizacion', 'Pasarela local', 4),
    ('iot', 'POST', '/iot/comandos', 'Orden manual a una válvula con vencimiento', 'ERP iot.comando_actuador', 'Panel, PWA', 4),
    ('iot', 'POST', '/iot/pasarelas/{codigo}/eventos', 'Sube eventos de riego y estados de actuadores', 'ERP riego.evento_riego, iot.actuador', 'Pasarela local', 4),
    ('iot', 'MQTT', 'guayacan/{finca}/riego/{valvula}/estado · /orden', 'Tópicos del broker local (pasarela ↔ nodos ESP32)', '—', 'Nodos y pasarela', 4)]
r = h + 1
for e in fa:
    fila_datos(ws, r, e, mono=(3,), centro=(2, 7)); r += 1
tabla_excel(ws, 'EndpointsFastAPI', h, 7, len(fa))
ws.freeze_panes = f'C{h + 1}'

# ------------------------------------------------------------------------------------ 7. FastAPI modelos (MongoDB / Pydantic)
ws, h = hoja(wb, 'FastAPI modelos', ['Colección MongoDB', 'Modelo Pydantic', 'Campo', 'Tipo BSON', 'Tipo Python (Pydantic)', 'Obligatorio', 'Significado'],
             [20, 22, 28, 11, 44, 10, 70], 'Modelos del servicio de agentes: colecciones de MongoDB y su modelo Pydantic', color=AZUL)
mfilas = list(csv.DictReader(open(os.path.join(REPO, 'diccionario_mongodb.csv'), encoding='utf-8-sig')))
SINGULAR = {'conversaciones': 'Conversacion', 'mensajes': 'Mensaje', 'perfiles_interes': 'PerfilInteres', 'eventos_redes': 'EventoRed', 'metricas_redes': 'MetricaRed', 'bitacora_agentes': 'EjecucionAgente', 'informes_mercado': 'InformeMercado', 'tendencias': 'Tendencia'}
TIPO = {'string': 'str', 'long': 'int', 'int': 'int', 'double': 'float', 'bool': 'bool', 'date': 'datetime', 'array': 'list', 'object': 'dict', 'objectId': 'ObjectIdStr'}
r = h + 1
for m in mfilas:
    py = f"Literal[{', '.join(repr(v) for v in m['valores'].split(', '))}]" if m['valores'] else TIPO.get(m['tipo'], 'str')
    if m['campo'] == '_id':
        py = "ObjectIdStr = Field(alias='_id')"
    if m['obligatorio'] == 'no' and m['campo'] != '_id':
        py = f'{py} | None = None'
    fila_datos(ws, r, [m['coleccion'], SINGULAR[m['coleccion']], m['campo'], m['tipo'], py,
                       'Sí' if m['obligatorio'] == 'sí' else 'No', m['significado']], mono=(1, 2, 3, 5), centro=(4, 6))
    r += 1
tabla_excel(ws, 'ModelosMongo', h, 7, len(mfilas))
ws.freeze_panes = f'D{h + 1}'
r += 1
for txt in ['Conexión: PyMongo asíncrono (AsyncMongoClient). Motor quedó en desuso en 2025 a favor de la API asíncrona de PyMongo.',
            'Cada consulta del repositorio agrega predio_id: MongoDB no tiene seguridad por filas como PostgreSQL.',
            'ObjectIdStr = Annotated[str, BeforeValidator(str)] convierte el ObjectId de MongoDB en texto para la API.']:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
    c = ws.cell(r, 1, txt); c.font = f_txt; c.alignment = wrap; c.fill = PatternFill('solid', fgColor='DDEBF7'); r += 1

# ------------------------------------------------------------------------------------ 8. Herramientas MCP
ws, h = hoja(wb, 'Herramientas MCP', ['Herramienta', 'Tipo', '¿Aprobación?', 'Endpoint del ERP que llama', 'Agentes que la usan'],
             [28, 12, 13, 60, 60], 'Puente FastAPI → Django: cada herramienta de los agentes llama un endpoint del monolito', color=AZUL)
herr = [('consultar_catalogo', 'lectura', 'No', 'GET /api/v1/comercial/catalogo/'),
        ('consultar_pedido', 'lectura', 'No', 'GET /api/v1/comercial/pedidos/?numero='),
        ('crear_pedido_borrador', 'escritura', 'No', 'POST /api/v1/comercial/pedidos/ + POST /api/v1/comercial/pedidos/{id}/lineas/ (estado borrador)'),
        ('buscar_conocimiento', 'lectura', 'No', 'GET /api/v1/ia/conocimiento/buscar/?q='),
        ('consultar_perfil_interes', 'lectura', 'No', 'Interna del servicio de agentes (MongoDB) tras verificar GET /api/v1/terceros/consentimientos/?tercero='),
        ('consultar_precios_mercado', 'lectura', 'No', 'GET /api/v1/compras/precios-mercado/ y /api/v1/compras/cotizaciones-proveedor/'),
        ('proponer_precio', 'propuesta', 'Sí', 'POST /api/v1/comercial/propuestas-precio/ (crea también la solicitud de aprobación)'),
        ('proponer_publicacion', 'propuesta', 'Sí', 'POST /api/v1/redes/publicaciones/ (estado propuesta)'),
        ('responder_comentario', 'escritura', 'No', 'Interna (API de Meta) tras POST /api/v1/redes/verificar-envio/'),
        ('consultar_indicadores', 'lectura', 'No', 'GET /api/v1/ia/indicadores/'),
        ('crear_recomendacion', 'propuesta', 'No', 'POST /api/v1/ia/recomendaciones/'),
        ('consultar_contabilidad', 'lectura', 'No', 'GET /api/v1/finanzas/comprobantes/ y /api/v1/finanzas/periodos-contables/'),
        ('escalar_a_humano', 'escritura', 'No', 'POST /api/v1/ia/escalamientos/ + estado de la conversación en MongoDB'),
        ('consultar_vencimientos', 'lectura', 'No', 'GET /api/v1/inventario/alertas-vencimiento/'),
        ('consultar_politica_canal', 'lectura', 'No', 'GET /api/v1/redes/politicas-canal/{plataforma}/'),
        ('proponer_tareas', 'propuesta', 'No', 'POST /api/v1/personal/tareas/ (origen agente, sin asignar)'),
        ('consultar_cronograma', 'lectura', 'No', 'GET /api/v1/personal/turnos/ y /api/v1/personal/cronogramas/{id}/huecos/'),
        ('diagnosticar_imagen', 'propuesta', 'No', 'POST /api/v1/ia/diagnosticos-imagen/ (lo confirma una persona)'),
        ('consultar_documentos_aprobados', 'lectura', 'No', 'GET /api/v1/documental/vigentes/?uso_agentes=true'),
        ('consultar_estados_financieros', 'lectura', 'No', 'GET /api/v1/finanzas/estado-resultados/, /balance/, /analisis/'),
        ('proponer_iniciativa', 'propuesta', 'No', 'POST /api/v1/estrategia/iniciativas/ (estado idea)'),
        ('evaluar_proyecto', 'lectura', 'No', 'POST /api/v1/estrategia/evaluaciones-proyecto/{id}/calcular/'),
        ('consultar_alertas_seguridad', 'lectura', 'No', 'GET /api/v1/seguridad/tablero/'),
        ('consultar_prospectos', 'lectura', 'No', 'GET /api/v1/crm/embudo/'),
        ('consultar_proyecto', 'lectura', 'No', 'GET /api/v1/proyectos/tablero/ y /api/v1/proyectos/actividades/?proyecto=')]
uso = {}
for linea in '\n'.join(b.split(';')[0] for b in open(os.path.join(REPO, 'datos_iniciales.sql')).read().split("insert into ia.agente_herramienta")[1:]).split('\n'):
    for a, hh in re.findall(r"\('(\w+)', '(\w+)'\)", linea):
        uso.setdefault(hh, []).append(a)
r = h + 1
for nm, tp, ap, ep in herr:
    fila_datos(ws, r, [nm, tp, ap, ep, ', '.join(uso.get(nm, []))], mono=(1, 4), centro=(2, 3)); r += 1
tabla_excel(ws, 'Herramientas', h, 5, len(herr))

# ------------------------------------------------------------------------------------ 9. Ruta de construcción manual
ws, h = hoja(wb, 'Ruta manual', ['Paso', 'API', 'Qué construir', 'Tablas o colecciones', 'Qué aprende', 'Cómo verificar'],
             [6, 14, 52, 46, 46, 46], 'Ruta para construir la aplicación a mano, de cero, en orden')
pasos = [
 ('Django', 'Proyecto Django, configuración por variables de entorno, conexión a PostgreSQL en Docker, endpoint /api/salud/', '—', 'Estructura de un proyecto, settings, Docker Compose', 'curl http://localhost:8000/api/salud/ responde 200'),
 ('Django', 'App nucleo: modelos base (ModeloBase, ModeloPorFinca, CapturableSinConexion), usuario personalizado, roles, permisos', 'usuario, rol, permiso, rol_permiso, usuario_rol, predio, zona, parametro', 'AUTH_USER_MODEL, clases abstractas, migraciones', 'python manage.py migrate sin errores; crear superusuario'),
 ('Django', 'Autenticación JWT y finca activa: middleware que fija app.predio_id y app.usuario_id en cada transacción', 'usuario_rol', 'SimpleJWT, middleware, SET LOCAL en PostgreSQL', 'Con dos fincas, cada usuario solo ve la suya'),
 ('Django', 'Migración RunSQL con las reglas de la base: RLS, auditoría, rol guayacan_app', 'auditoria, evento_salida', 'Lo que Django no genera solo; seguridad en la base', 'Correr la sección RLS de pruebas_reglas_v4.sql'),
 ('Django', 'App terceros y app inventario con serializers y ViewSets', 'tercero, cliente, consentimiento_datos, producto, lote_inventario, movimiento_inventario, bodega', 'ModelSerializer, ViewSet, routers, filtros, campos de solo lectura', 'Crear un lote y ver su movimiento de entrada'),
 ('Django', 'Kardex, vencimiento y FEFO en la base; endpoints de alertas y escaneo', 'lote_inventario, movimiento_inventario, etiqueta, lectura_codigo, pesaje', 'Reglas en SQL vs. en Python; transacciones', 'Pruebas de kardex y FEFO de pruebas_reglas_v4.sql'),
 ('Django', 'App produccion y riego (registro diario)', 'lote_animal, registro_postura, registro_alimentacion, siembra, cosecha, evento_riego…', 'Relaciones, validaciones de negocio', 'Registrar la postura de un día desde la API'),
 ('Django', 'App comercial: pedidos, acciones confirmar, despachar y cancelar; catálogo', 'pedido, pedido_detalle, reserva_lote, precio_producto, propuesta_precio, factura, pago', '@action en DRF, llamada a funciones SQL', 'Pedido de 60 cubetas reserva 50 + 10 por FEFO'),
 ('Django', 'Endpoint de sincronización para la PWA', f'{len(CAPTURA)} tablas de captura, sincronizacion', 'Idempotencia, procesamiento por lotes', 'Enviar dos veces el mismo id_cliente: se aplica una vez'),
 ('Angular', 'PWA de campo: service worker, IndexedDB con Dexie, cola de pendientes, lector de código y báscula', '—', 'Aplicaciones sin conexión, Web Bluetooth, BarcodeDetector', 'Registrar en modo avión y ver que sube al volver la señal'),
 ('Django', 'App compras, finanzas (cuadre contable) y Celery (outbox, vencidos)', 'orden_compra, cotizacion_proveedor, precio_mercado, comprobante, movimiento_contable, periodo_contable', 'Tareas en segundo plano, disparadores diferidos', 'Comprobante descuadrado no se contabiliza'),
 ('Django', 'App ia y redes: agentes, herramientas, aprobaciones, conocimiento, políticas de canal, plantillas', 'agente, herramienta, solicitud_aprobacion, documento_conocimiento, politica_canal, plantilla_mensaje, mensaje_saliente, regla_conversacion, escalamiento', 'pgvector, modelado de permisos para IA', 'verificar-envio responde bloqueado a las 30 h sin plantilla'),
 ('FastAPI', 'Servicio de agentes: proyecto FastAPI, conexión a MongoDB y Redis, /agentes/salud', 'conversaciones, mensajes', 'async/await, Pydantic, inyección de dependencias', 'GET /agentes/salud responde 200'),
 ('FastAPI', 'Chat web por WebSocket y webhook de WhatsApp con verificación de firma', 'conversaciones, mensajes', 'WebSocket, seguridad de webhooks', 'Mensaje de prueba de Meta llega y se guarda'),
 ('FastAPI', 'Servidor MCP y primer agente (orquestador + asesor) con guardia de dominio', 'bitacora_agentes', 'Agentes con herramientas, MCP, LiteLLM', 'Pregunta ajena a la finca recibe la cortesía y oferta de persona'),
 ('FastAPI', 'Analista de mercados con propuesta de precio y aprobación en el ERP', 'informes_mercado', 'Flujos con aprobación humana (LangGraph)', 'La propuesta aparece en la bandeja y al aprobar cambia el catálogo'),
 ('FastAPI', 'Fase 2: Instagram, Messenger, TikTok, perfiles de interés y tendencias', 'eventos_redes, metricas_redes, perfiles_interes, tendencias', 'Integraciones con varias plataformas', 'Ventanas y topes de cada canal respetados'),
 ('Django', 'Fase 2: cadena de frío, bloqueos, cartera, permuta, pedidos recurrentes y funciones por finca', 'bodega, vehiculo, excursion_temperatura, bloqueo_lote, factura, pago, permuta, pedido_recurrente, funcionalidad', 'Feature flags, Specification, State, Saga simple', 'Pruebas 10, 13, 14 y 15 de pruebas_reglas_v4.sql'),
 ('FastAPI', 'Fase 2: notas de voz y piezas audiovisuales (FFmpeg) con aprobación', 'nota_voz, pieza_audiovisual, mensajes (audio)', 'Procesamiento de audio y video en segundo plano', 'Una pieza con personas sin autorización no se aprueba'),
 ('FastAPI', 'Fase 4: servicio IoT, pasarela local y nodos ESP32', 'iot.* y TimescaleDB', 'MQTT, sistemas en el borde', 'Riego automático funciona con el internet desconectado'),
 ('FastAPI', 'Fase 4: seguridad perimetral y cámaras en la pasarela (reglas locales, clips, avisos push y SMS)', 'zona_seguridad, evento_seguridad, camara, clip_video, credencial_acceso', 'Patrón State, Observer por MQTT, retención de datos', 'Con internet desconectado, una intrusión suena la sirena y queda el evento'),
 ('Django', 'v5 · App seguridad: doble factor, detector de ataques, señuelos, alertas, pruebas y copias', 'seguridad.*', 'Autenticación fuerte, detección por reglas, OWASP', 'Sección 11 de pruebas_reglas_v5.sql'),
 ('Django', 'v5 · Apps documental, formacion y personal: documentos, cursos, habilitaciones, tareas, áreas, cronogramas 24/7', 'documental.*, formacion.*, personal.*', 'Reglas de asignación, patrones de turno, cobertura', 'Secciones 1, 2, 5 y 16 de pruebas_reglas_v5.sql'),
 ('Django', 'v5 · Apps activos y nomina: mantenimiento, depreciación, prenómina, liquidación y pagos con doble aprobación', 'activos.*, nomina.*', 'Inmutabilidad, segregación de funciones', 'Secciones 3 y 4 de pruebas_reglas_v5.sql'),
 ('Django', 'v5 · Apps cumplimiento y seguros: granja biosegura, BPA, ISO 21001, pólizas y avisos', 'cumplimiento.*, seguros.*', 'Evidencia automática, vencimientos', 'Secciones 6, 7 y 19 de pruebas_reglas_v5.sql'),
 ('Django', 'v5 · Finanzas ampliadas y estrategia: costos, presupuesto, estados, indicadores, palancas, VPN, TIR y reinversión', 'finanzas.*, estrategia.*', 'Matemática financiera en SQL, costeo variable', 'Secciones 9, 10 y 21 de pruebas_reglas_v5.sql'),
 ('Django', 'v5 · Apps crm, agenda y proyectos: prospectos, cabañas, visitas, portería, PMBOK 8', 'crm.*, agenda.*, proyectos.*', 'Restricciones de exclusión, CPM, valor ganado', 'Secciones 13, 17, 18 y 20 de pruebas_reglas_v5.sql'),
 ('FastAPI', 'v5 · Agentes Agrónomo, Coordinador, Instructor, Estratega, Vigía de seguridad y Asistente de proyectos', 'bitacora_agentes', 'Agentes que solo proponen; herramientas de lectura', 'Ningún agente aprueba (pruebas con app.agente_id)')]
r = h + 1
for i, p in enumerate(pasos, 1):
    fila_datos(ws, r, [i] + list(p), centro=(1, 2))
    for j in range(1, 7):
        ws.cell(r, j).fill = fill_dj if p[0] == 'Django' else (fill_fa if p[0] == 'FastAPI' else PatternFill('solid', fgColor='FCE4D6'))
    r += 1

for w in wb.worksheets:
    w.page_setup.orientation = 'landscape'; w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 0
    w.sheet_properties.pageSetUpPr.fitToPage = True
    w.oddFooter.center.text = 'GuayacanERP · Mapa de APIs y modelos · &A · Página &P de &N'; w.oddFooter.center.size = 8
wb.save(OUT)
print(OUT, 'campos django', n, 'endpoints django', len(eps), 'fastapi', len(fa))
