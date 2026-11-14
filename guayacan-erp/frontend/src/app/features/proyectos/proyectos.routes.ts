// Rutas del módulo «Proyectos (PMBOK 8)» (prefijo PRY). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /proyectos, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /proyectos
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Proyectos (PMBOK 8)",
      casos: [{"id": "PRY-01", "nombre": "Constituir un proyecto", "fase": 2, "funcion": null}, {"id": "PRY-02", "nombre": "Aprobar un proyecto", "fase": 2, "funcion": null}, {"id": "PRY-03", "nombre": "Planificar el alcance y el cronograma", "fase": 2, "funcion": null}, {"id": "PRY-04", "nombre": "Calcular la ruta crítica", "fase": 2, "funcion": null}, {"id": "PRY-05", "nombre": "Gestionar interesados y riesgos", "fase": 2, "funcion": null}, {"id": "PRY-06", "nombre": "Registrar avance y medir el valor ganado", "fase": 2, "funcion": null}, {"id": "PRY-07", "nombre": "Solicitar y decidir un cambio", "fase": 2, "funcion": null}, {"id": "PRY-08", "nombre": "Aceptar entregables y cerrar el proyecto", "fase": 2, "funcion": null}, {"id": "PRY-09", "nombre": "Planear y cerrar una iteración", "fase": 2, "funcion": null}],
    },
  },
];
