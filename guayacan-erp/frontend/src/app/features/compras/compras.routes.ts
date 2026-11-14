// Rutas del módulo «Compras» (prefijo CMP). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /compras, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /compras
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Compras",
      casos: [{"id": "CMP-01", "nombre": "Registrar cotizaciones y precios de mercado", "fase": 1, "funcion": null}, {"id": "CMP-02", "nombre": "Crear y aprobar una orden de compra", "fase": 1, "funcion": null}, {"id": "CMP-03", "nombre": "Recibir una compra en bodega", "fase": 1, "funcion": null}, {"id": "CMP-04", "nombre": "Emitir un documento soporte electrónico", "fase": 1, "funcion": null}],
    },
  },
];
