// Rutas del módulo «Riego» (prefijo RIE). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /riego, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /riego
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Riego",
      casos: [{"id": "RIE-01", "nombre": "Configurar fuentes, tanques, sistemas y válvulas", "fase": 1, "funcion": null}, {"id": "RIE-02", "nombre": "Registrar un riego manual", "fase": 1, "funcion": null}, {"id": "RIE-03", "nombre": "Regar automáticamente por reglas", "fase": 4, "funcion": "riego_automatico"}],
    },
  },
];
