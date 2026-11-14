// Rutas del módulo «Ambiental» (prefijo AMB). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /ambiental, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /ambiental
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Ambiental",
      casos: [{"id": "AMB-01", "nombre": "Registrar mediciones ambientales", "fase": 2, "funcion": null}, {"id": "AMB-02", "nombre": "Mantener factores de emisión con su fuente", "fase": 2, "funcion": null}, {"id": "AMB-03", "nombre": "Consultar indicadores ambientales y CO₂ estimado", "fase": 2, "funcion": null}],
    },
  },
];
