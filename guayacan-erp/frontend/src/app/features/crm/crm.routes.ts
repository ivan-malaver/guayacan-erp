// Rutas del módulo «Clientes potenciales (CRM)» (prefijo CRM). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /crm, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /crm
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Clientes potenciales (CRM)",
      casos: [{"id": "CRM-01", "nombre": "Capturar un posible cliente con autorización", "fase": 2, "funcion": null}, {"id": "CRM-02", "nombre": "Gestionar segmentos y campañas", "fase": 2, "funcion": null}, {"id": "CRM-03", "nombre": "Registrar interacciones y avanzar el embudo", "fase": 2, "funcion": null}, {"id": "CRM-04", "nombre": "Calificar los prospectos", "fase": 2, "funcion": null}, {"id": "CRM-05", "nombre": "Convertir un prospecto en cliente", "fase": 2, "funcion": null}, {"id": "CRM-06", "nombre": "Gestionar oportunidades y proyectar ventas", "fase": 2, "funcion": null}],
    },
  },
];
