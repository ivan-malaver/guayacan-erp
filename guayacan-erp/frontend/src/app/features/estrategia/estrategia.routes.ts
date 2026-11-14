// Rutas del módulo «Estrategia de negocio» (prefijo EST). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /estrategia, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /estrategia
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Estrategia de negocio",
      casos: [{"id": "EST-01", "nombre": "Mantener las líneas de negocio y la matriz DOFA", "fase": 2, "funcion": null}, {"id": "EST-02", "nombre": "Registrar un estudio de mercado", "fase": 2, "funcion": null}, {"id": "EST-03", "nombre": "Proponer una iniciativa de crecimiento", "fase": 2, "funcion": null}, {"id": "EST-04", "nombre": "Evaluar financieramente una iniciativa", "fase": 2, "funcion": null}, {"id": "EST-05", "nombre": "Aprobar una iniciativa", "fase": 2, "funcion": null}, {"id": "EST-06", "nombre": "Reinvertir utilidades de una línea", "fase": 2, "funcion": null}, {"id": "EST-07", "nombre": "Seguir el retorno de las iniciativas", "fase": 2, "funcion": null}, {"id": "EST-08", "nombre": "Definir objetivos y metas del cuadro de mando", "fase": 2, "funcion": null}],
    },
  },
];
