"""Generador de las rutas del frontend Angular a partir del catálogo de casos de uso (catalogo.py).

QUÉ HACE
Por cada módulo del catálogo (26, incluida la adopción del Apéndice A) escribe:
  - frontend/src/app/features/<modulo>/<modulo>.routes.ts : la ruta del módulo con la lista de sus casos de uso.
  - frontend/src/app/app.routes.ts                          : el mapa general de rutas (todas perezosas).
  - frontend/src/app/shared/modulos.ts                      : la lista de módulos que muestra el menú de inicio.

POR QUÉ SE GENERA
Así el frontend y el backend siempre muestran los mismos módulos y casos de uso. Si cambia el catálogo,
se vuelve a correr este script en lugar de editar 28 archivos a mano.

USO (desde la raíz del repositorio):
    python -I docs/uml/fuentes/gen_frontend.py docs/uml/fuentes frontend

CUIDADO: sobrescribe los archivos *.routes.ts. Cuando un módulo ya tenga pantallas construidas a mano, quítelo
de la generación (o copie sus rutas antes) para no perder el trabajo.
"""
import json
import os
import sys

# El primer argumento es la carpeta donde vive catalogo.py; se agrega a la ruta de importación
sys.path.insert(0, sys.argv[1])
import catalogo as C  # noqa: E402  (se importa después de ajustar sys.path a propósito)

FE = sys.argv[2]  # carpeta raíz del frontend
rutas = []        # líneas de app.routes.ts, una por módulo


def js(valor):
    """Convierte un valor de Python a texto JSON válido en TypeScript, conservando tildes y eñes."""
    return json.dumps(valor, ensure_ascii=False)


for m, titulo in C.MODULOS.items():
    # Casos de uso del módulo: código, nombre, fase del plan y función (bandera) que lo activa
    casos = [{'id': c['id'], 'nombre': c['nombre'], 'fase': c['fase'], 'funcion': c['flag']} for c in C.por_modulo(m)]
    d = os.path.join(FE, 'src', 'app', 'features', m)
    os.makedirs(d, exist_ok=True)
    nombre = titulo if isinstance(titulo, str) else m
    with open(os.path.join(d, f'{m}.routes.ts'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"""// Rutas del módulo «{nombre}» (prefijo {C.PREFIJO[m]}). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /{m}, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   {{ path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }}
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import {{ Routes }} from '@angular/router';

import {{ ModuloPendienteComponent }} from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {{
    path: '', // ruta raíz del módulo: /{m}
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {{
      titulo: {js(nombre)},
      casos: {js(casos)},
    }},
  }},
];
""")
    rutas.append(f"      {{ path: '{m}', title: {js(nombre)}, loadChildren: () => import('./features/{m}/{m}.routes').then((r) => r.RUTAS) }},")

with open(os.path.join(FE, 'src', 'app', 'app.routes.ts'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(f"""// Mapa general de rutas de la aplicación. ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// CÓMO FUNCIONA
// - /ingreso es pública (pantalla de inicio de sesión).
// - Todo lo demás cuelga de una ruta protegida por sesionGuard: si no hay sesión, envía a /ingreso.
// - Cada módulo usa loadChildren (carga perezosa): su código se descarga solo cuando alguien entra,
//   así la aplicación abre rápido aunque tenga {len(rutas)} módulos.
// - '**' captura cualquier dirección desconocida y devuelve al inicio.
import {{ Routes }} from '@angular/router';

import {{ IngresoComponent }} from './core/auth/ingreso.component';
import {{ sesionGuard }} from './core/auth/sesion.guard';
import {{ InicioComponent }} from './shared/inicio.component';

export const routes: Routes = [
  {{ path: 'ingreso', component: IngresoComponent, title: 'Ingreso' }},
  {{
    path: '',
    canActivate: [sesionGuard], // exige sesión iniciada para todo lo de abajo
    children: [
      {{ path: '', component: InicioComponent, title: 'Inicio' }},
""" + '\n'.join(rutas) + """
    ],
  },
  { path: '**', redirectTo: '' },
];
""")

with open(os.path.join(FE, 'src', 'app', 'shared', 'modulos.ts'), 'w', encoding='utf-8', newline='\n') as f:
    lista = [{'ruta': m, 'titulo': t if isinstance(t, str) else m, 'prefijo': C.PREFIJO[m]} for m, t in C.MODULOS.items()]
    f.write('// Módulos que muestra el menú de inicio. ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.\n'
            '// ruta: dirección en la aplicación; titulo: nombre visible; prefijo: código de sus casos de uso.\n'
            '// «as const» le dice a TypeScript que la lista no cambia, así detecta errores de escritura en las rutas.\n'
            'export const MODULOS = ' + json.dumps(lista, ensure_ascii=False, indent=2) + ' as const;\n')

print(len(rutas), 'módulos')
