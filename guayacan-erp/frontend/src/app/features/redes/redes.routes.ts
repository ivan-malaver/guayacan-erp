// Rutas del módulo «Canales y redes sociales» (prefijo RED). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /redes, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /redes
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Canales y redes sociales",
      casos: [{"id": "RED-01", "nombre": "Atender el mensaje de un cliente por un canal", "fase": 1, "funcion": null}, {"id": "RED-02", "nombre": "Escalar una conversación a una persona", "fase": 1, "funcion": null}, {"id": "RED-03", "nombre": "Enviar un mensaje saliente dentro de las reglas del canal", "fase": 1, "funcion": null}, {"id": "RED-04", "nombre": "Proponer y aprobar una publicación", "fase": 2, "funcion": null}, {"id": "RED-05", "nombre": "Producir una pieza audiovisual con autorización de imagen", "fase": 2, "funcion": "videos_promocionales"}, {"id": "RED-06", "nombre": "Mantener plantillas y políticas de canal", "fase": 1, "funcion": null}],
    },
  },
];
