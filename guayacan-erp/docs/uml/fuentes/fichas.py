"""Imprime la cabecera (tabla de datos) de cada caso de uso de un módulo, generada del catálogo.
Uso: python3 fichas.py <modulo> [blobs.txt]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalogo import ACTORES, MODULOS, PREFIJO, REQUERIMIENTOS, por_modulo  # noqa: E402


def plural(p):
    """Pluraliza una palabra en español para armar rutas REST (lote → lotes, raiz → raices); algunas no cambian."""
    irregular = {'analisis': 'analisis', 'ia': 'ia', 'iot': 'iot', 'por': 'por', 'de': 'de', 'webhook': 'webhooks', 'auditoria': 'auditoria'}
    if p in irregular:
        return irregular[p]
    if p.endswith('z'):
        return p[:-1] + 'ces'
    if p[-1] in 'aeiou':
        return p + 's'
    return p + 'es'


ESPECIAL = {'personal.paso_tarea': 'tareas/{id}/pasos', 'personal.evidencia_tarea': 'tareas/{id}/evidencias',
            'comercial.pedido_detalle': 'pedidos/{id}/lineas', 'compras.orden_compra_detalle': 'ordenes-compra/{id}/lineas',
            'inventario.conteo_detalle': 'conteos/{id}/detalles', 'finanzas.movimiento_contable': 'comprobantes/{id}/movimientos',
            'inventario.conteo_fisico': 'conteos', 'nucleo.usuario_rol': 'usuarios/{id}/roles', 'nucleo.rol_permiso': 'roles/{id}/permisos',
            'ia.agente_herramienta': 'agentes/{id}/herramientas', 'produccion.calidad_agua_estanque': 'calidad-agua',
            'iot.regla_automatizacion': 'reglas', 'iot.comando_actuador': 'comandos', 'comercial.propuesta_precio': 'propuestas-precio',
            'ia.solicitud_aprobacion': 'solicitudes-aprobacion', 'redes.politica_canal': 'politicas-canal',
            'redes.mensaje_saliente': 'mensajes-salientes', 'nucleo.dispositivo_captura': 'dispositivos-captura',
            'terceros.consentimiento_datos': 'consentimientos', 'ia.consumo_ia': 'consumos', 'nomina.liquidacion_detalle': 'liquidaciones/{id}/detalles',
            'personal.patron_turno_detalle': 'patrones-turno/{id}/dias', 'proyectos.dependencia': 'actividades/{id}/dependencias',
            'documental.version_documento': 'documentos/{id}/versiones', 'finanzas.presupuesto_detalle': 'presupuestos/{id}/detalles',
            'cumplimiento.no_conformidad': 'no-conformidades', 'cumplimiento.accion_correctiva': 'acciones-correctivas',
            'cumplimiento.auditoria_externa': 'auditorias-externas', 'seguros.bien_asegurado': 'bienes-asegurados',
            'estrategia.flujo_proyecto': 'evaluaciones-proyecto/{id}/flujos', 'activos.repuesto_orden': 'ordenes-trabajo/{id}/repuestos'}


def ruta(full):
    """Ruta REST de una tabla: 'produccion.lote_animal' → '/api/v1/produccion/lotes-animal/' (o la especial si la hay)."""
    if full in ESPECIAL:
        r = ESPECIAL[full]
    else:
        partes = full.split('.')[1].split('_')
        partes[0] = plural(partes[0])
        r = '-'.join(partes)
    return f'/api/v1/{full.split(".")[0]}/{r}/'


def nombres(cods):
    """Convierte códigos de actores en sus nombres legibles, separados por coma."""
    return ', '.join(ACTORES[a] for a in cods) if cods else 'ninguno'


def cabecera(c):
    """Arma la tabla de datos (ficha) de un caso de uso en Markdown: actores, fase, función, API, reglas y pruebas."""
    encendidas = {'modo_aprendiz'}
    flag = (f'función `{c["flag"]}` ({"encendida" if c["flag"] in encendidas else "apagada"} al instalar)') if c['flag'] else 'siempre activa'
    acciones = list(c['acciones'])
    crud = [ruta(t) for t in c['tablas'] if t.split('.')[0] == c['modulo']][:3]
    api = '; '.join(f'`{a}`' for a in acciones + [f'CRUD {r}' for r in crud if not any(r in a for a in acciones)]) or 'sin endpoint propio'
    reglas = ', '.join(f'`{r}`' if '(' in r or r.count('.') == 1 else r for r in c['reglas']) or 'validación de formato y permisos de DRF'
    pruebas = ', '.join(p.replace(':', ' ') for p in c['pruebas']) or 'pendiente: escribir la prueba al construir'
    rel = []
    if c['inc']:
        rel.append('incluye ' + ', '.join(c['inc']))
    if c['ext']:
        rel.append('lo extiende ' + ', '.join(c['ext']))
    filas = [('Actores', f'Primario: {nombres(c["actores"])}. Secundarios: {nombres(c["secundarios"])}'),
             ('Fase y función', f'Fase {c["fase"]} · {flag}'),
             ('Relaciones', '; '.join(rel) if rel else 'ninguna'),
             ('Reglas en la base', reglas),
             ('Datos', ', '.join(f'`{t}`' for t in c['tablas']) or 'cálculo sin tablas propias'),
             ('API', api),
             ('Pruebas', pruebas),
             ('Requerimientos', ', '.join(f'{r} {REQUERIMIENTOS[r][0].lower() + REQUERIMIENTOS[r][1:]}' for r in c['rf']))]
    return '\n'.join(['| Campo | Detalle |', '| --- | --- |'] + [f'| {a} | {b} |' for a, b in filas])


if __name__ == '__main__':
    m = sys.argv[1]
    for c in por_modulo(m):
        print(f'### {c["id"]} · {c["nombre"]}\n')
        print(cabecera(c))
        print()
