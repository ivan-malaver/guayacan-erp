// Rutas del módulo «Agenda y portería» (prefijo AGD). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /agenda, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /agenda
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Agenda y portería",
      casos: [{"id": "AGD-01", "nombre": "Configurar recursos agendables", "fase": 3, "funcion": null}, {"id": "AGD-02", "nombre": "Agendar una cita en un recurso", "fase": 3, "funcion": null}, {"id": "AGD-03", "nombre": "Programar y aprobar una visita", "fase": 2, "funcion": null}, {"id": "AGD-04", "nombre": "Registrar entradas y salidas en portería", "fase": 2, "funcion": null}, {"id": "AGD-05", "nombre": "Consultar quién está en la finca", "fase": 2, "funcion": null}, {"id": "AGD-06", "nombre": "Consultar la agenda del día", "fase": 2, "funcion": null}],
    },
  },
];
