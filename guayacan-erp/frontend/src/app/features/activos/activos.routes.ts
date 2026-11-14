// Rutas del módulo «Activos y mantenimiento» (prefijo ACT). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /activos, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /activos
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Activos y mantenimiento",
      casos: [{"id": "ACT-01", "nombre": "Registrar un activo con su hoja de vida", "fase": 2, "funcion": null}, {"id": "ACT-02", "nombre": "Registrar el uso de un activo", "fase": 2, "funcion": null}, {"id": "ACT-03", "nombre": "Generar y cerrar órdenes de mantenimiento", "fase": 2, "funcion": null}, {"id": "ACT-04", "nombre": "Depreciar los activos del mes", "fase": 2, "funcion": null}, {"id": "ACT-05", "nombre": "Asignar un equipo a un trabajador", "fase": 2, "funcion": null}],
    },
  },
];
