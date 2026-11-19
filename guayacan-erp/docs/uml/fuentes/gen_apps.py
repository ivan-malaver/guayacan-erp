"""Generador de las 26 apps de Django del backend (25 de la v5 + adopcion del Apéndice A).

Qué hace: lee las tablas (specs/modelo-datos/generador/modelo.py y modelo_apendice_a.py) y los casos de uso
(docs/uml/fuentes/catalogo.py) y escribe, por cada esquema de PostgreSQL, una carpeta backend/apps/<esquema>/ con:
  apps.py, models.py, serializers.py, views.py, urls.py, services.py, tests/ y README.md.

Por qué existe: son 254 tablas y 192 casos de uso. Escribir a mano sus modelos y rutas sería lento y daría
errores; generarlos garantiza que Django coincida exactamente con la base de datos. Todo lo generado viene
comentado en español para que alguien con conocimientos básicos entienda qué hace cada línea y para qué.

Qué NO hace: no escribe lógica de negocio. Los servicios quedan vacíos (NotImplementedError) y las acciones de
los casos de uso responden 501 «por construir» hasta que alguien las programe.

Cuidado: si regenera, se sobrescriben los archivos generados. El código que usted escriba a mano en services.py,
views.py o urls.py se perdería: genere solo al iniciar o cuando cambie el modelo, y haga commit antes.

Uso (desde esta carpeta):
    python3 -I gen_apps.py ../../../specs/modelo-datos/generador . ../../../backend"""
import os
import re
import sys
import textwrap

GEN, UML, DEST = sys.argv[1:4]
sys.path.insert(0, GEN)
sys.path.insert(0, UML)
from modelo import ESQUEMAS, T, GLOBALES, CAPTURA  # noqa: E402
import catalogo as C  # noqa: E402
from fichas import ruta, ESPECIAL  # noqa: E402

# Apéndice A: las tablas de adopción viven en un archivo aparte para no tocar modelo.py de la v5
try:
    from modelo_apendice_a import CAPTURA_A, ESQUEMAS_A, T_A  # noqa: E402
except ImportError:  # sin apéndice, se generan solo las 25 apps de la v5
    CAPTURA_A, ESQUEMAS_A, T_A = set(), {}, []
ESQUEMAS = {**ESQUEMAS, **ESQUEMAS_A}  # nombre del esquema -> descripción
T = list(T) + list(T_A)                # todas las tablas: (esquema, tabla, fase, descripción, columnas, extras, auditada)
CAPTURA = set(CAPTURA) | set(CAPTURA_A)  # tablas que se capturan sin conexión en la app de campo
# AGD-04: la jornada nace solo en portería (agenda.validar_acceso), con conexión; sincronizarla aparte la duplicaría.
# TODO(PER): revisar si la app de campo necesita capturar la jornada sin conexión al construir los casos de Personal
CAPTURA -= {'personal.jornada'}

NOMBRES = {f'{t[0]}.{t[1]}' for t in T}
OPERATIVAS = NOMBRES - GLOBALES

# Acciones que fijan las especificaciones además de las del catálogo (endpoint, caso de uso)
EXTRA = [
    ('GET /api/v1/nucleo/mis-fincas/', 'NUC-03'),
    ('POST /api/v1/iot/lecturas/lote/', 'IOT-02'),
    ('POST /api/v1/iot/eventos-seguridad/{id}/atender/', 'IOT-05'),
    ('POST /api/v1/terceros/consentimientos/{id}/revocar/', 'TER-02'),
    ('POST /api/v1/terceros/terceros/{id}/anonimizar/', 'TER-03'),
    ('GET /api/v1/publico/certificados/{codigo}/', 'FOR-05'),
    ('POST /api/v1/turismo/reservas/{id}/pagar/', 'TUR-03'),
    ('POST /api/v1/turismo/reservas/{id}/check-in/', 'TUR-04'),
    ('POST /api/v1/turismo/reservas/{id}/check-out/', 'TUR-04'),
    ('POST /api/v1/turismo/solicitudes-grupo/', 'TUR-05'),
    ('POST /api/v1/personal/tareas/{id}/devolver/', 'PER-03'),
    ('POST /api/v1/personal/jornadas/{id}/aprobar/', 'PER-06'),
    ('POST /api/v1/nomina/periodos/{id}/transmitir/', 'NOM-08'),
    ('POST /api/v1/redes/mensajes-salientes/verificar/', 'RED-03'),
    ('POST /api/v1/ia/escalamientos/{id}/tomar/', 'RED-02'),
    ('POST /api/v1/compras/documentos-soporte/{id}/transmitir/', 'CMP-04'),
    ('POST /api/v1/finanzas/comprobantes/{id}/contabilizar/', 'FIN-02'),
    ('POST /api/v1/finanzas/comprobantes/{id}/anular/', 'FIN-03'),
    ('POST /api/v1/finanzas/presupuestos/{id}/aprobar/', 'FIN-06'),
    ('POST /api/v1/estrategia/iniciativas/{id}/aprobar/', 'EST-05'),
    ('POST /api/v1/proyectos/elementos-edt/{id}/aceptar/', 'PRY-08'),
    ('POST /api/v1/proyectos/proyectos/{id}/cerrar/', 'PRY-08'),
    ('POST /api/v1/seguros/avisos-siniestro/{id}/revisar/', 'SGR-03'),
    ('POST /api/v1/seguros/avisos-siniestro/{id}/enviar/', 'SGR-03'),
    ('POST /api/v1/cumplimiento/acciones-correctivas/{id}/verificar/', 'CUM-06'),
    ('POST /api/v1/cumplimiento/no-conformidades/{id}/cerrar/', 'CUM-06'),
    ('POST /api/v1/ia/solicitudes-aprobacion/{id}/rechazar/', 'IA-02'),
    ('POST /api/v1/ia/diagnosticos-imagen/{id}/revisar/', 'IA-08'),
]
# Acciones que ya implementa el núcleo transversal (no se generan como pendientes)
IMPLEMENTADAS = {'GET /api/v1/nucleo/mis-fincas/', 'POST /api/v1/sincronizacion/lote/', 'POST /api/v1/auth/token/'}


def camel(s):
    """Convierte nombre_con_guiones a NombreConGuiones (nombre de clase de Python): 'lote_animal' → 'LoteAnimal'."""
    return ''.join(p.capitalize() for p in s.split('_'))


def slug(s, n=5):
    """Convierte un texto en un identificador corto: minúsculas, sin tildes ni palabras vacías, máximo n palabras."""
    s = s.lower()
    for a, b in zip('áéíóúñü', 'aeiouna'):
        s = s.replace(a, b)
    vacias = {'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una', 'y', 'o', 'a', 'en', 'por', 'con', 'su', 'sus', 'al'}
    palabras = [p for p in re.findall(r'[a-z0-9]+', s) if p not in vacias]
    return '_'.join(palabras[:n])


def lit(v):
    """Escribe un valor de Python como texto de código (comillas incluidas) para pegarlo en un archivo generado."""
    return repr(v)


def default_de(rest):
    """Extrae el valor por defecto de la definición SQL de una columna y lo traduce a Django (o None si no tiene)."""
    m = re.search(r"default ('[^']*'(?:::\w+)?|[^ ]+)", rest)
    if not m:
        return None
    d = m.group(1)
    if '::' in d:  # valor con conversión de tipo, p. ej. '[]'::jsonb: lo calcula la base
        return f"sql({lit(d)})"
    if d.startswith("'"):
        return lit(d.strip("'"))
    if d in ('true', 'false'):
        return 'True' if d == 'true' else 'False'
    if re.fullmatch(r'-?\d+(\.\d+)?', d):
        return d
    if d == 'now()':
        return 'Now()'
    return f"sql({lit(d)})"


def campo(tabla_full, nombre, tipo, rest, sig):
    """Devuelve (nombre_python, código del campo)."""
    nulo = 'not null' not in rest
    kw = []
    dd = default_de(rest)
    if dd:
        kw.append(f'db_default={dd}')
    if nulo:
        kw.append('null=True, blank=True')
    if 'unique' in rest and tabla_full not in OPERATIVAS:
        kw.append('unique=True')  # en tablas por finca lo único es (predio_id, campo) y lo garantiza la base
    kw.append(f'db_comment={lit(sig)}')
    extra = ', '.join(kw)
    if tipo.startswith('fk:') or tipo.startswith('fk_codigo:'):
        ref = tipo.split(':', 1)[1]
        app, tab = ref.split('.')
        destino = f'{app}.{camel(tab)}'
        py = nombre[:-3] if nombre.endswith('_id') else nombre
        to_field = ", to_field='plataforma'" if tipo.startswith('fk_codigo:') else ''
        return py, (f"models.ForeignKey({lit(destino)}, models.DO_NOTHING{to_field}, db_column={lit(nombre)}, "
                    f"related_name='+', db_constraint=False, {extra})")
    if tipo.startswith('enum:'):
        vals = tipo[5:].split(',')
        ch = ', '.join(f'({lit(v)}, {lit(v)})' for v in vals)
        return nombre, f'models.CharField(max_length={max(len(v) for v in vals)}, choices=[{ch}], {extra})'
    m = re.fullmatch(r'(varchar|char)\((\d+)\)', tipo)
    if m:
        return nombre, f'models.CharField(max_length={m.group(2)}, {extra})'
    m = re.fullmatch(r'numeric\((\d+),(\d+)\)', tipo)
    if m:
        return nombre, f'models.DecimalField(max_digits={m.group(1)}, decimal_places={m.group(2)}, {extra})'
    m = re.fullmatch(r'geometry\((\w+), (\d+)\)', tipo)
    if m:
        return nombre, f'Geometria(tipo={lit(m.group(1))}, srid={m.group(2)}, {extra})'
    m = re.fullmatch(r'vector\((\d+)\)', tipo)
    if m:
        return nombre, f'VectorField(dimensions={m.group(1)}, {extra})'
    if tipo.startswith('smallint generated always as'):
        expr = re.search(r'as \((.*)\) stored', tipo).group(1)
        a, b = [x.strip() for x in expr.split('*')]
        return nombre, (f"models.GeneratedField(expression=models.F({lit(a)}) * models.F({lit(b)}), "
                        f"output_field=models.SmallIntegerField(), db_persist=True, db_comment={lit(sig)})")
    simple = {
        'text': 'models.TextField', 'date': 'models.DateField', 'timestamptz': 'models.DateTimeField',
        'time': 'models.TimeField', 'boolean': 'models.BooleanField', 'smallint': 'models.SmallIntegerField',
        'integer': 'models.IntegerField', 'bigint': 'models.BigIntegerField', 'jsonb': 'models.JSONField',
        'inet': 'models.GenericIPAddressField', 'double precision': 'models.FloatField',
        'citext': 'models.EmailField' if 'correo' in nombre else 'models.TextField',
    }
    if tipo in simple:
        pre = 'max_length=254, ' if simple[tipo] == 'models.EmailField' else ''
        return nombre, f'{simple[tipo]}({pre}{extra})'
    if tipo == 'dinero':
        return nombre, f'models.DecimalField(max_digits=14, decimal_places=2, {extra})'
    if tipo == 'cidr':
        return nombre, f'models.CharField(max_length=43, {extra})'
    m = re.fullmatch(r'(text|smallint|bigint)\[\]', tipo)
    if m:
        base = {'text': 'models.TextField()', 'smallint': 'models.SmallIntegerField()', 'bigint': 'models.BigIntegerField()'}[m.group(1)]
        return nombre, f'ArrayField({base}, {extra})'
    raise SystemExit(f'Tipo sin traducir: {tabla_full}.{nombre} {tipo}')


def modelo(esq, tab, desc, cols, aud):
    """Devuelve (nombre de la clase, código Python comentado del modelo de una tabla)."""
    full = f'{esq}.{tab}'
    clase = camel(tab)
    ambito = 'por finca (seguridad por filas)' if full in OPERATIVAS else 'catálogo compartido entre fincas'
    raya = '# ' + '=' * 110
    lineas = [raya, f'# Tabla {full}  ·  {ambito}  ·  API: {ruta(full)}', raya,
              f'class {clase}(models.Model):', f'    """{desc}"""', '',
              '    # Llave primaria: número consecutivo que asigna PostgreSQL (identity)',
              "    id = models.BigAutoField(primary_key=True, db_comment='Identificador interno')"]
    usados = {'id'}
    if full in OPERATIVAS:
        lineas.append('    # Finca dueña del registro. La pone la base con nucleo.predio_actual() según la sesión; la API nunca la recibe')
        lineas.append("    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', "
                      "db_constraint=False, editable=False, db_default=sql('nucleo.predio_actual()'), "
                      "db_comment='Finca dueña del registro; la pone la base según la sesión (RLS)')")
        usados.add('predio')
    elif full == 'nucleo.parametro':
        lineas.append('    # Vacío = parámetro nacional (vale para todas las fincas); con valor = solo para esa finca')
        lineas.append("    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', "
                      "db_constraint=False, null=True, blank=True, db_comment='Vacío = parámetro nacional')")
        usados.add('predio')
    elif full == 'nucleo.auditoria':
        lineas.append('    # Finca en la que ocurrió el cambio auditado')
        lineas.append("    predio = models.ForeignKey('nucleo.Predio', models.DO_NOTHING, db_column='predio_id', related_name='+', "
                      "db_constraint=False, null=True, editable=False, db_default=sql('nucleo.predio_actual()'), "
                      "db_comment='Finca en la que ocurrió el cambio')")
        usados.add('predio')
    propias = [c for c in cols if c[0] != 'predio_id']
    if propias:
        lineas.append('    # Columnas propias de la tabla (db_comment explica cada una; también está en el diccionario de datos)')
    for nombre, tipo, rest, sig in propias:
        py, cod = campo(full, nombre, tipo, rest, sig)
        if py in usados:
            py = py + '_ref'
        usados.add(py)
        lineas.append(f'    {py} = {cod}')
    if full in CAPTURA:
        lineas += ['    # Captura sin conexión: el celular genera id_cliente (UUIDv7); si el mismo registro llega dos veces,',
                   '    # la base lo detecta por este campo único y no lo duplica (ver guayacan/sincronizacion.py)',
                   "    id_cliente = models.UUIDField(null=True, blank=True, unique=True, db_comment='UUIDv7 del celular (sincronización idempotente)')",
                   "    capturado_en = models.DateTimeField(null=True, blank=True, db_comment='Momento de la captura en el dispositivo')",
                   "    dispositivo_captura = models.ForeignKey('nucleo.DispositivoCaptura', models.DO_NOTHING, db_column='dispositivo_captura_id', "
                   "related_name='+', db_constraint=False, null=True, blank=True, db_comment='Dispositivo con que se capturó')"]
    if aud:
        lineas += ['    # Fechas de control: las pone la base (el disparador nucleo.marcar_actualizado() renueva actualizado_en)',
                   "    creado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Creación del registro')",
                   "    actualizado_en = models.DateTimeField(db_default=Now(), editable=False, db_comment='Última modificación (la pone la base)')"]
    lineas += ['', '    class Meta:',
               '        # managed = False: Django NO crea, cambia ni borra esta tabla; la crea el SQL de specs/modelo-datos',
               '        managed = False',
               f'        # Nombre real en PostgreSQL: esquema "{esq}", tabla "{tab}" (las comillas separan esquema y tabla)',
               f"        db_table = '{esq}\".\"{tab}'",
               '        # Comentario de la tabla, el mismo que tiene la base',
               f'        db_table_comment = {lit(desc)}', '']
    return clase, '\n'.join(lineas)


def ruta_relativa(full):
    """Ruta REST de una tabla sin el prefijo /api/v1/<esquema>/, para el archivo urls.py de la app."""
    return ruta(full).split('/', 4)[4].rstrip('/')  # p. ej. 'lotes-animal' o 'tareas/{id}/pasos'


def path_django(p):
    """Convierte {id} o {pk} en <int:id> y otros {param} en <str:param>, el formato de rutas de Django."""
    p = re.sub(r'\{(id|pk)\}', '<int:id>', p)
    return re.sub(r'\{(\w+)\}', r'<str:\1>', p)


# ----------------------------------------------------------------------------- acciones por app
casos = {c['id']: c for m in C.MODULOS for c in C.por_modulo(m)}
acciones = []  # (metodo, ruta completa sin consulta, cu)
for c in casos.values():
    for a in c['acciones']:
        acciones.append((a, c['id']))
acciones += EXTRA
por_app, transversales = {}, []
vistos = set()
for a, cu in acciones:
    if a in IMPLEMENTADAS:
        continue
    metodo, _, p = a.partition(' ')
    p = p.split('?')[0]
    if (metodo, p) in vistos:
        continue
    vistos.add((metodo, p))
    m = re.match(r'/api/v1/(\w+)/(.*)$', p)
    if m and m.group(1) in ESQUEMAS:
        por_app.setdefault(m.group(1), []).append((metodo, m.group(2), cu, a))
    else:
        transversales.append((metodo, p, cu, a))

CAB_MODELOS = '''"""Modelos del esquema {esq}: {desc}.

QUÉ ES ESTE ARCHIVO
Cada clase representa una tabla de PostgreSQL del esquema «{esq}». Django usa estas clases para leer y escribir
filas sin escribir SQL a mano: models.<Clase>.objects.filter(...), .create(...), etc.

CÓMO SE CREÓ
Lo generó docs/uml/fuentes/gen_apps.py a partir de specs/modelo-datos/generador/modelo.py (y modelo_apendice_a.py).
No lo edite a mano: si cambia una tabla, cambie el modelo y vuelva a generar.

POR QUÉ managed = False
La base de datos la crea specs/modelo-datos/esquema_postgresql.sql (y apendice_a_adopcion.sql), con sus reglas,
seguridad por filas y auditoría. Django solo la usa; nunca crea, altera ni borra estas tablas (no hay migraciones).

CÓMO LEER UN CAMPO
  models.CharField(max_length=20)      texto corto de máximo 20 caracteres (varchar)
  models.TextField()                   texto largo (text)
  models.DecimalField(14, 2)           número con decimales exactos, p. ej. dinero (numeric)
  models.DateField / DateTimeField     fecha / fecha y hora con zona horaria (date / timestamptz)
  models.BooleanField                  sí o no (boolean)
  models.ForeignKey('app.Clase', ...)  llave foránea: el valor es el id de una fila de otra tabla
  choices=[...]                        lista cerrada de valores; la base los valida con un CHECK
  null=True, blank=True                el dato puede quedar vacío
  db_default=...                       valor que pone la base si no se envía (Django no lo manda en el INSERT)
  db_comment='...'                     significado del dato (queda como comentario en PostgreSQL)
Opciones de las llaves foráneas:
  models.DO_NOTHING      Django no borra en cascada: la base decide (y en este sistema casi nada se borra)
  db_constraint=False    la llave real ya existe en la base (a veces compuesta con predio_id); Django no la recrea
  related_name='+'       no se crea el acceso inverso desde la otra tabla (evita choques de nombres entre 26 apps)
"""
# ArrayField, Now, VectorField, Geometria y sql se importan siempre porque algunos esquemas los usan;
# «noqa: F401» le dice al revisor de estilo (ruff) que no avise si en este esquema en particular no se usan.
from django.contrib.postgres.fields import ArrayField  # noqa: F401  (listas de PostgreSQL, p. ej. text[])
from django.db import models
from django.db.models.functions import Now  # noqa: F401  (fecha y hora actual calculada por la base)
from pgvector.django import VectorField  # noqa: F401  (vectores para búsquedas semánticas de la IA)

from guayacan.db import Geometria, sql  # noqa: F401  (columnas de mapas sin GeoDjango y valores calculados por SQL)


'''


def generar_app(esq):
    """Escribe todos los archivos de la app de un esquema. Devuelve (número de tablas, número de casos de uso)."""
    tablas = [t for t in T if t[0] == esq]
    base = os.path.join(DEST, 'apps', esq)
    os.makedirs(os.path.join(base, 'tests'), exist_ok=True)
    cus = C.por_modulo(esq)
    pref = C.PREFIJO[esq]
    desc = ESQUEMAS[esq]
    # ------------------------------------------------------------------------------------------ __init__.py y apps.py
    open(os.path.join(base, '__init__.py'), 'w').write(f'"""App {esq}: {desc}."""\n')
    open(os.path.join(base, 'apps.py'), 'w').write(textwrap.dedent(f'''\
        """Registro de la app «{esq}» en Django.

        Django trata cada carpeta de backend/apps/ como una «app». Esta clase le dice cómo se llama el paquete,
        con qué etiqueta corta se nombran sus modelos (p. ej. '{esq}.Modelo') y qué nombre mostrar.
        La lista de apps activas está en config/settings/base.py (ESQUEMAS e INSTALLED_APPS)."""
        from django.apps import AppConfig


        class {camel(esq)}Config(AppConfig):
            # Ruta del paquete Python: la carpeta backend/apps/{esq}
            name = 'apps.{esq}'
            # Etiqueta corta; otras apps la usan en sus llaves foráneas, p. ej. '{esq}.Modelo'
            label = '{esq}'
            # Nombre en español que muestran las herramientas de Django
            verbose_name = {lit(desc)}
            # Tipo de llave primaria por defecto (entero grande, igual que las tablas de PostgreSQL)
            default_auto_field = 'django.db.models.BigAutoField'
        '''))
    # ------------------------------------------------------------------------------------------ models.py
    clases = []
    cuerpo = [CAB_MODELOS.format(esq=esq, desc=desc)]
    if esq == 'nucleo':
        cuerpo.append('# El usuario se escribió a mano (apps/nucleo/usuario.py) porque Django necesita métodos especiales para\n'
                      '# iniciar sesión; aquí solo se importa para que Django lo encuentre como nucleo.Usuario.\n'
                      'from .usuario import Usuario, UsuarioManager  # noqa: E402,F401\n\n\n')
    for esq_, tab, fase, desc_t, cols, extras, aud in tablas:
        if f'{esq}.{tab}' == 'nucleo.usuario':
            clases.append(('Usuario', tab))
            continue
        clase, cod = modelo(esq, tab, desc_t, cols, aud)
        clases.append((clase, tab))
        cuerpo.append(cod + '\n\n')
    open(os.path.join(base, 'models.py'), 'w').write(''.join(cuerpo).rstrip() + '\n')
    # ------------------------------------------------------------------------------------------ serializers.py
    s = [f'"""Serializers del esquema {esq}: convierten los modelos en JSON y el JSON recibido en datos validados.',
         '',
         'QUÉ HACE UN SERIALIZER',
         '1. Al responder: toma una fila (objeto del modelo) y la convierte en JSON para el frontend.',
         '2. Al recibir (POST, PUT, PATCH): revisa que el JSON traiga los campos obligatorios, con el tipo correcto y',
         '   valores permitidos, antes de enviarlo a la base. La base vuelve a validar las reglas de negocio.',
         '',
         'Generado por docs/uml/fuentes/gen_apps.py. Un caso de uso que necesite otros campos crea su propio serializer',
         'aquí mismo, debajo de los generados."""',
         'from rest_framework import serializers', '', 'from . import models', '',
         '# Campos que pone la base (identificador, finca, fechas de control): el usuario puede verlos pero no enviarlos',
         "SOLO_LECTURA = ('id', 'predio', 'creado_en', 'actualizado_en')", '']
    for clase, tab in clases:
        if clase == 'Usuario':
            s += ['', '# Usuario: nunca se devuelve la contraseña (ni siquiera cifrada)',
                  'class UsuarioSerializer(serializers.ModelSerializer):', '    class Meta:', '        model = models.Usuario',
                  "        exclude = ('password',)  # todos los campos menos la contraseña",
                  "        read_only_fields = ('id', 'last_login', 'creado_en', 'actualizado_en')", '']
            continue
        s += ['', f'# {esq}.{tab} <-> JSON en {ruta(esq + "." + tab)}',
              f'class {clase}Serializer(serializers.ModelSerializer):', '    class Meta:',
              f'        model = models.{clase}  # tabla que representa',
              "        fields = '__all__'  # expone todas sus columnas",
              '        read_only_fields = SOLO_LECTURA  # las que pone la base no se aceptan del usuario', '']
    open(os.path.join(base, 'serializers.py'), 'w').write('\n'.join(s).rstrip() + '\n')
    # ------------------------------------------------------------------------------------------ views.py
    v = [f'"""Vistas (endpoints CRUD) del esquema {esq}.',
         '',
         'QUÉ HACE UNA VISTA',
         'Recibe la petición HTTP, usa el serializer para validar o convertir los datos y responde. Cada clase de abajo',
         'es un «ViewSet»: una sola clase atiende varias rutas de la misma tabla.',
         '',
         'QUÉ OPERACIONES OFRECE (heredadas de guayacan.vistas.VistaModelo)',
         '  GET    /recurso/        lista paginada (50 por página; ?pagina=2&tamano=100)',
         '  GET    /recurso/{id}/   detalle de un registro',
         '  POST   /recurso/        crear',
         '  PUT o PATCH /recurso/{id}/   modificar todo o una parte',
         '  No hay DELETE: en GuayacanERP los registros se desactivan, se anulan o se cierran, no se borran.',
         '',
         'La seguridad no se programa aquí: el middleware fija la finca y el usuario, y PostgreSQL solo deja ver y',
         'cambiar lo de esa finca. Las acciones de los casos de uso (aprobar, confirmar, liquidar...) están en urls.py.',
         'Generado por docs/uml/fuentes/gen_apps.py."""',
         'from guayacan.vistas import VistaModelo', '', 'from . import models, serializers', '']
    for clase, tab in clases:
        v += ['', f'# CRUD de {esq}.{tab} en {ruta(esq + "." + tab)}',
              f'class {clase}ViewSet(VistaModelo):',
              f'    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)',
              f'    queryset = models.{clase}.objects.all()',
              f'    # Cómo se convierten y validan los datos',
              f'    serializer_class = serializers.{clase}Serializer', '']
    open(os.path.join(base, 'views.py'), 'w').write('\n'.join(v).rstrip() + '\n')
    # ------------------------------------------------------------------------------------------ urls.py
    nombres_cu = {c['id']: c['nombre'] for c in C.CU}
    u = [f'"""Rutas de /api/v1/{esq}/ (cómo una dirección web llega a su vista).',
         '',
         'ORDEN',
         '1. Primero las acciones de los casos de uso. Mientras no se construyan usan PorConstruir, que responde',
         '   501 con el código del caso de uso: el frontend y la documentación OpenAPI ya las conocen.',
         '2. Después las rutas anidadas (hijos de un registro, p. ej. las líneas de un pedido), si las hay.',
         '3. Al final el CRUD de cada tabla, que registra el «router» de Django REST Framework.',
         '',
         'CÓMO CONSTRUIR UNA ACCIÓN: escriba la vista real (o un método @action en views.py) y reemplace aquí',
         'PorConstruir por esa vista. Generado por docs/uml/fuentes/gen_apps.py."""',
         'from django.urls import include, path', 'from rest_framework.routers import DefaultRouter', '',
         'from guayacan.vistas import PorConstruir, PorConstruirPublico  # noqa: F401', '', 'from . import views', '',
         '# El router crea las rutas de lista (/recurso/) y detalle (/recurso/<id>/) de cada ViewSet',
         'router = DefaultRouter()']
    anidadas = []
    rutas_crud = set()
    for clase, tab in clases:
        full = f'{esq}.{tab}'
        r = ruta_relativa(full)
        if '{id}' in r:
            padre_ruta, hija = r.split('/{id}/')
            padre = next((x for x in NOMBRES if x.startswith(esq + '.') and ruta_relativa(x) == padre_ruta), None)
            fk = next((c[0] for t in tablas if t[1] == tab for c in t[4] if c[1] == f'fk:{padre}'), None)
            anidadas.append((padre_ruta, hija, clase, fk[:-3] if fk and fk.endswith('_id') else fk))
        else:
            rutas_crud.add(r)
            u.append(f"router.register({lit(r)}, views.{clase}ViewSet, basename={lit(esq + '-' + r)})  # tabla {full}")
    u += ['', 'urlpatterns = [']
    acciones_app = [x for x in por_app.get(esq, []) if x[1].rstrip('/') not in rutas_crud]
    if acciones_app:
        u.append('    # --- Acciones de los casos de uso (responden 501 «por construir» hasta que se programen)')
    for metodo, p, cu, original in acciones_app:
        rel = p.rstrip('/')
        vista = 'PorConstruirPublico' if p.startswith('captura/') else 'PorConstruir'
        sesion = ' (pública, sin sesión)' if vista == 'PorConstruirPublico' else ''
        u.append(f'    # {cu} · {nombres_cu.get(cu, "")}: {metodo} /api/v1/{esq}/{p}{sesion}')
        u.append(f"    path({lit(path_django(p))}, {vista}.as_view(caso_de_uso={lit(cu)}, metodo={lit(metodo)}), "
                 f"name={lit(cu.lower() + '-' + slug(rel.replace('/', ' '), 6).replace('_', '-'))}),")
    if anidadas:
        u.append('    # --- Rutas anidadas: los hijos de un registro; el padre llega en la ruta y se fija al crear')
    for padre_ruta, hija, clase, fk in anidadas:
        u.append(f"    path({lit(padre_ruta + '/<int:padre>/' + hija + '/')}, "
                 f"views.{clase}ViewSet.as_view({{'get': 'list', 'post': 'create'}}, campo_padre={lit(fk)}), "
                 f"name={lit(esq + '-' + hija + '-lista')}),")
        u.append(f"    path({lit(padre_ruta + '/<int:padre>/' + hija + '/<int:pk>/')}, "
                 f"views.{clase}ViewSet.as_view({{'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}}, campo_padre={lit(fk)}), "
                 f"name={lit(esq + '-' + hija + '-detalle')}),")
    u += ['    # --- CRUD de las tablas (al final, para que las acciones de arriba tengan prioridad)',
          "    path('', include(router.urls)),", ']']
    open(os.path.join(base, 'urls.py'), 'w').write('\n'.join(u) + '\n')
    # ------------------------------------------------------------------------------------------ services.py
    sv = [f'"""Casos de uso del esquema {esq}: una función por caso de uso.',
          '',
          'POR QUÉ UNA CAPA DE SERVICIOS',
          'Las vistas solo reciben y responden. La operación de negocio vive aquí para poder llamarla desde la API,',
          'desde una tarea programada (Celery) o desde una prueba, siempre de la misma manera.',
          '',
          'PATRÓN PARA CONSTRUIR CADA FUNCIÓN (ejemplo completo en docs/desarrollo/02_construir_un_caso_de_uso.md)',
          '1. with transaction.atomic():  todo o nada; si algo falla no queda nada a medias.',
          '2. Llamar la función de PostgreSQL que aplica la regla (están listadas en «Reglas en la base»).',
          '   No repita la regla en Python: la base ya la valida y está probada.',
          '3. Si la base rechaza, lanza un error con el mensaje en español; guayacan/errores.py lo convierte en',
          '   una respuesta 422 o 409 para el usuario. No hace falta capturarlo aquí.',
          '4. publicar(...) un evento si otros módulos o los agentes deben enterarse (patrón outbox).',
          '5. Devolver el objeto o los datos que mostrará la respuesta.',
          '',
          'Cada función está vacía (NotImplementedError) y su documentación resume la especificación.',
          'Especificación completa: documento técnico (pestaña de casos de uso) y docs/casos-de-uso/."""',
          '# transaction y publicar aún no se usan (las funciones están vacías); «noqa» evita el aviso del revisor',
          'from django.db import transaction  # noqa: F401', '', 'from guayacan.eventos import publicar  # noqa: F401', '']
    for c in cus:
        fn = c['id'].lower().replace('-', '_') + '_' + slug(c['nombre'])
        doc = [f'{c["id"]} · {c["nombre"]}', '',
               f'Actores: {", ".join(C.ACTORES[a] for a in c["actores"])}' + (f'; secundarios: {", ".join(C.ACTORES[a] for a in c["secundarios"])}' if c['secundarios'] else ''),
               f'Fase {c["fase"]}' + (f' · función {c["flag"]}' if c['flag'] else ''),
               'Tablas: ' + ', '.join(c['tablas']) if c['tablas'] else 'Tablas: ninguna propia',
               'Reglas en la base: ' + (', '.join(c['reglas']) if c['reglas'] else 'formato y permisos de DRF'),
               'Endpoints: ' + ('; '.join(c['acciones']) if c['acciones'] else 'CRUD de sus tablas'),
               'Requerimientos: ' + ', '.join(c['rf']),
               '',
               'Parámetros: usuario (quien hace la petición) y **datos (lo que validó el serializer).']
        guia = [f'    # Por construir. Pasos sugeridos para {c["id"]}:',
                '    # 1. with transaction.atomic():']
        if c['flag']:
            guia.append(f"    # 2. La función «{c['flag']}» debe estar encendida en la finca (la base lo exige con nucleo.exigir_funcion)")
        if c['reglas']:
            guia.append(f'    # 3. Llamar a la base: {", ".join(c["reglas"][:3])}')
        else:
            guia.append('    # 3. Guardar con el serializer (el CRUD ya lo hace) o con models.<Clase>.objects.create(...)')
        guia += [f"    # 4. publicar('{esq}.<hecho>', '<esquema.tabla>', id, {{...}}) si otros módulos deben enterarse",
                 '    # 5. Devolver el resultado para la respuesta']
        sv += ['', f'def {fn}(*, usuario, **datos):', '    """' + '\n'.join(('    ' + x) if x else '' for x in doc).lstrip() + '\n    """',
               *guia,
               f"    raise NotImplementedError({lit(c['id'] + ': por construir')})", '']
    open(os.path.join(base, 'services.py'), 'w').write('\n'.join(sv).rstrip() + '\n')
    # ------------------------------------------------------------------------------------------ tests
    open(os.path.join(base, 'tests', '__init__.py'), 'w').write(f'"""Pruebas de la app {esq}."""\n')
    ts = [f'"""Pruebas de aceptación de los casos de uso de {esq}.',
          '',
          'Cada función es la prueba del flujo principal de un caso de uso. Están marcadas con @pytest.mark.skip',
          '(«saltar») porque el caso aún no está construido. Al construirlo:',
          '1. Quite la línea @pytest.mark.skip.',
          '2. Escriba la prueba del flujo principal y agregue una por cada flujo alterno de la especificación.',
          '3. Corra pytest desde la carpeta backend (necesita la base cargada; ver INSTALAR.md)."""',
          'import pytest', '']
    for c in cus:
        ts += ['', f"@pytest.mark.skip(reason={lit(c['id'] + ': por construir')})",
               f"def test_{c['id'].lower().replace('-', '_')}_{slug(c['nombre'])}_flujo_principal():",
               f'    """{c["id"]} · {c["nombre"]}"""', '']
    open(os.path.join(base, 'tests', 'test_casos_de_uso.py'), 'w').write('\n'.join(ts).rstrip() + '\n')
    # ------------------------------------------------------------------------------------------ README.md
    rd = [f'# App `{esq}` ({pref})', '', desc + '.', '', '## Casos de uso', '',
          '| ID | Caso de uso | Fase | Actores | Endpoints de acción |', '| --- | --- | --- | --- | --- |']
    for c in cus:
        acc = '<br>'.join(f'`{a}`' for a in c['acciones']) or 'CRUD'
        fl = f' · `{c["flag"]}`' if c['flag'] else ''
        rd.append(f'| {c["id"]} | {c["nombre"]} | {c["fase"]}{fl} | {", ".join(C.ACTORES[a] for a in c["actores"])} | {acc} |')
    rd += ['', '## Tablas', '', '| Tabla | Modelo | Ruta CRUD | Qué guarda |', '| --- | --- | --- | --- |']
    for esq_, tab, fase, desc_t, cols, extras, aud in tablas:
        rd.append(f'| `{esq}.{tab}` | `{camel(tab) if tab != "usuario" or esq != "nucleo" else "Usuario"}` | `{ruta(esq + "." + tab)}` | {desc_t} |')
    reglas = sorted({r for c in cus for r in c['reglas']})
    rd += ['', '## Reglas de la base que protegen esta app', '']
    rd += [f'- `{r}`' for r in reglas] or ['- Solo validación de formato y permisos de DRF']
    rd += ['', '## Archivos de esta carpeta', '',
           '| Archivo | Qué hace |', '| --- | --- |',
           '| `apps.py` | Registra la app en Django |',
           '| `models.py` | Una clase por tabla (generado; no editar) |',
           '| `serializers.py` | Convierte filas en JSON y valida el JSON recibido |',
           '| `views.py` | Endpoints CRUD de cada tabla |',
           '| `urls.py` | Rutas: acciones de los casos de uso (501 mientras se construyen) y CRUD |',
           '| `services.py` | Una función por caso de uso, vacía, con los pasos para construirla |',
           '| `tests/test_casos_de_uso.py` | Una prueba por caso de uso, marcada como pendiente |',
           '', '## Cómo trabajar aquí', '',
           '1. Lea la especificación del caso de uso en el documento técnico (pestaña de su grupo) o en `docs/casos-de-uso/`.',
           '2. Quite el `skip` de su prueba en `tests/test_casos_de_uso.py` y escriba el flujo principal y los alternos.',
           '3. Implemente la función de `services.py`; no repita en Python las reglas que ya están en la base.',
           '4. Reemplace la ruta `PorConstruir` de `urls.py` por la vista real.', '']
    open(os.path.join(base, 'README.md'), 'w').write('\n'.join(rd))
    return len(tablas), len(cus)


# ---------------------------------------------------------------------------------------------- programa principal
tot_t = tot_c = 0
for esq in ESQUEMAS:
    a, b = generar_app(esq)
    tot_t += a
    tot_c += b
# Lista blanca de la sincronización sin conexión: solo estas tablas se aceptan en POST /api/v1/sincronizacion/lote/
with open(os.path.join(DEST, 'guayacan', 'captura.py'), 'w') as f:
    f.write('"""Tablas que la app de campo puede capturar sin conexión (tienen la columna id_cliente).\n\n'
            'Para qué sirve: guayacan/sincronizacion.py solo acepta registros de estas tablas, así nadie puede usar la\n'
            'sincronización para escribir en otras. Generado por docs/uml/fuentes/gen_apps.py desde modelo.py y\n'
            'modelo_apendice_a.py: no lo edite a mano."""\n\n'
            '# frozenset: conjunto que no se puede modificar mientras corre el programa\n')
    f.write('TABLAS_CAPTURA = frozenset({\n' + ''.join(f"    '{t}',\n" for t in sorted(CAPTURA)) + '})\n')
print(f'{len(ESQUEMAS)} apps, {tot_t} tablas, {tot_c} casos de uso, {sum(len(v) for v in por_app.values())} acciones de app, '
      f'{len(transversales)} transversales (en guayacan/urls.py, escritas a mano)')
