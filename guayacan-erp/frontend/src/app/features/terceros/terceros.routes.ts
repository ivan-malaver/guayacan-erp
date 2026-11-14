// Rutas del módulo «Terceros y datos personales» (prefijo TER). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /terceros, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /terceros
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Terceros y datos personales",
      casos: [{"id": "TER-01", "nombre": "Registrar un tercero (persona o empresa)", "fase": 1, "funcion": null}, {"id": "TER-02", "nombre": "Registrar y revocar una autorización de datos", "fase": 1, "funcion": null}, {"id": "TER-03", "nombre": "Atender una solicitud del titular de datos", "fase": 1, "funcion": null}, {"id": "TER-04", "nombre": "Gestionar clientes, proveedores y empleados", "fase": 1, "funcion": null}],
    },
  },
];
