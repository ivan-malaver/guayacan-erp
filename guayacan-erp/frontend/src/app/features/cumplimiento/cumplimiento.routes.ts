// Rutas del módulo «Cumplimiento y certificaciones» (prefijo CUM). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /cumplimiento, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /cumplimiento
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Cumplimiento y certificaciones",
      casos: [{"id": "CUM-01", "nombre": "Cargar normas y requisitos", "fase": 1, "funcion": null}, {"id": "CUM-02", "nombre": "Abrir un expediente de cumplimiento", "fase": 1, "funcion": null}, {"id": "CUM-03", "nombre": "Evaluar el expediente contra su evidencia", "fase": 1, "funcion": null}, {"id": "CUM-04", "nombre": "Adjuntar evidencias a un requisito", "fase": 1, "funcion": null}, {"id": "CUM-05", "nombre": "Registrar una auditoría externa y sus no conformidades", "fase": 2, "funcion": null}, {"id": "CUM-06", "nombre": "Ejecutar y verificar acciones correctivas", "fase": 2, "funcion": null}, {"id": "CUM-07", "nombre": "Vigilar la obligación de granja avícola biosegura", "fase": 1, "funcion": null}],
    },
  },
];
