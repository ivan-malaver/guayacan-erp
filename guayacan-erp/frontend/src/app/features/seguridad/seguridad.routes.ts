// Rutas del módulo «Seguridad informática» (prefijo SEG). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /seguridad, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /seguridad
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Seguridad informática",
      casos: [{"id": "SEG-01", "nombre": "Iniciar sesión con doble factor", "fase": 1, "funcion": null}, {"id": "SEG-02", "nombre": "Inscribir el segundo factor y recuperar la contraseña", "fase": 1, "funcion": null}, {"id": "SEG-03", "nombre": "Detectar y bloquear ataques de acceso", "fase": 1, "funcion": null}, {"id": "SEG-04", "nombre": "Atender una alerta o un incidente de seguridad", "fase": 1, "funcion": null}, {"id": "SEG-05", "nombre": "Revocar sesiones y levantar bloqueos", "fase": 1, "funcion": null}, {"id": "SEG-06", "nombre": "Registrar una corrida de pruebas", "fase": 1, "funcion": null}, {"id": "SEG-07", "nombre": "Verificar copias de seguridad y restauraciones", "fase": 1, "funcion": null}],
    },
  },
];
