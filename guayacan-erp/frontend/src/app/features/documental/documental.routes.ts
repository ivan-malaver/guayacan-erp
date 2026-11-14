// Rutas del módulo «Gestión documental» (prefijo DOC). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /documental, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /documental
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Gestión documental",
      casos: [{"id": "DOC-01", "nombre": "Publicar un documento con versión aprobada", "fase": 1, "funcion": null}, {"id": "DOC-02", "nombre": "Vincular documentos y vigilar vencimientos", "fase": 1, "funcion": null}, {"id": "DOC-03", "nombre": "Consultar documentos vigentes", "fase": 1, "funcion": null}],
    },
  },
];
