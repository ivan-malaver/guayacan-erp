// Rutas del módulo «Personal, tareas y turnos» (prefijo PER). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /personal, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /personal
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Personal, tareas y turnos",
      casos: [{"id": "PER-01", "nombre": "Configurar áreas de responsabilidad y matriz RACI", "fase": 1, "funcion": null}, {"id": "PER-02", "nombre": "Definir el plan de labores", "fase": 1, "funcion": null}, {"id": "PER-03", "nombre": "Generar las tareas del día", "fase": 1, "funcion": null}, {"id": "PER-04", "nombre": "Asignar una tarea", "fase": 1, "funcion": null}, {"id": "PER-05", "nombre": "Ejecutar una tarea con evidencia", "fase": 1, "funcion": null}, {"id": "PER-06", "nombre": "Aprobar o devolver una tarea", "fase": 1, "funcion": null}, {"id": "PER-07", "nombre": "Armar y publicar el cronograma de turnos", "fase": 2, "funcion": null}, {"id": "PER-08", "nombre": "Registrar disponibilidad y ausencias", "fase": 2, "funcion": null}, {"id": "PER-09", "nombre": "Registrar la jornada con el carné", "fase": 1, "funcion": null}, {"id": "PER-10", "nombre": "Organizar cuadrillas", "fase": 1, "funcion": null}],
    },
  },
];
