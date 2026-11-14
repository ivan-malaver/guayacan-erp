// Rutas del módulo «Seguros» (prefijo SGR). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /seguros, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /seguros
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Seguros",
      casos: [{"id": "SGR-01", "nombre": "Registrar una póliza y sus bienes asegurados", "fase": 2, "funcion": null}, {"id": "SGR-02", "nombre": "Avisar pólizas próximas a vencer", "fase": 2, "funcion": null}, {"id": "SGR-03", "nombre": "Registrar y enviar un aviso de siniestro", "fase": 2, "funcion": null}, {"id": "SGR-04", "nombre": "Vigilar el índice de una póliza paramétrica", "fase": 2, "funcion": "seguro_parametrico"}],
    },
  },
];
