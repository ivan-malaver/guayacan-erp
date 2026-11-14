// Rutas del módulo «Formación» (prefijo FOR). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /formacion, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /formacion
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Formación",
      casos: [{"id": "FOR-01", "nombre": "Diseñar un curso con lecciones y evaluación", "fase": 2, "funcion": null}, {"id": "FOR-02", "nombre": "Tomar un curso virtual", "fase": 2, "funcion": null}, {"id": "FOR-03", "nombre": "Dictar una sesión presencial y registrar asistencia", "fase": 2, "funcion": null}, {"id": "FOR-04", "nombre": "Emitir certificados y habilitaciones", "fase": 2, "funcion": null}, {"id": "FOR-05", "nombre": "Retirar habilitaciones vencidas", "fase": 2, "funcion": null}, {"id": "FOR-06", "nombre": "Detectar necesidades de formación", "fase": 2, "funcion": null}, {"id": "FOR-07", "nombre": "Responder la encuesta de un curso", "fase": 2, "funcion": null}, {"id": "FOR-08", "nombre": "Presentar y resolver una queja o apelación", "fase": 2, "funcion": null}, {"id": "FOR-09", "nombre": "Preguntar al Instructor virtual", "fase": 2, "funcion": null}],
    },
  },
];
