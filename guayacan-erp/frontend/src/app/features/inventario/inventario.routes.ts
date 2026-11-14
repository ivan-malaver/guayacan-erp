// Rutas del módulo «Inventario y cadena de frío» (prefijo INV). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /inventario, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /inventario
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Inventario y cadena de frío",
      casos: [{"id": "INV-01", "nombre": "Gestionar productos, unidades y bodegas", "fase": 1, "funcion": null}, {"id": "INV-02", "nombre": "Recibir un lote en bodega y etiquetarlo", "fase": 1, "funcion": null}, {"id": "INV-03", "nombre": "Escanear un código y pesar con báscula", "fase": 1, "funcion": null}, {"id": "INV-04", "nombre": "Registrar merma, ajuste o traslado", "fase": 1, "funcion": null}, {"id": "INV-05", "nombre": "Hacer un conteo físico", "fase": 1, "funcion": null}, {"id": "INV-06", "nombre": "Vigilar vencimientos y liquidar", "fase": 1, "funcion": null}, {"id": "INV-07", "nombre": "Vigilar la cadena de frío y decidir sobre un lote bloqueado", "fase": 2, "funcion": "cadena_frio_finca"}],
    },
  },
];
