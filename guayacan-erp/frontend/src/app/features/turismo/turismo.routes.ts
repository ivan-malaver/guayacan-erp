// Rutas del módulo «Turismo» (prefijo TUR). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /turismo, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /turismo
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Turismo",
      casos: [{"id": "TUR-01", "nombre": "Gestionar alojamientos y planes turísticos", "fase": 3, "funcion": null}, {"id": "TUR-02", "nombre": "Reservar una cabaña o un plan", "fase": 3, "funcion": null}, {"id": "TUR-03", "nombre": "Pagar anticipadamente una reserva", "fase": 3, "funcion": null}, {"id": "TUR-04", "nombre": "Hacer check-in y check-out de huéspedes", "fase": 3, "funcion": null}, {"id": "TUR-05", "nombre": "Atender la solicitud de un grupo", "fase": 3, "funcion": null}, {"id": "TUR-06", "nombre": "Bloquear fechas del calendario", "fase": 3, "funcion": null}],
    },
  },
];
