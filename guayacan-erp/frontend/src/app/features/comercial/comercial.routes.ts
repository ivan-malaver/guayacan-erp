// Rutas del módulo «Ventas» (prefijo VTA). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /comercial, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /comercial
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Ventas",
      casos: [{"id": "VTA-01", "nombre": "Gestionar listas y precios con vigencia", "fase": 1, "funcion": null}, {"id": "VTA-02", "nombre": "Proponer y aprobar un cambio de precio", "fase": 1, "funcion": null}, {"id": "VTA-03", "nombre": "Tomar y confirmar un pedido", "fase": 1, "funcion": null}, {"id": "VTA-04", "nombre": "Vender en la finca o en la feria sin conexión", "fase": 2, "funcion": null}, {"id": "VTA-05", "nombre": "Despachar y entregar un pedido", "fase": 1, "funcion": null}, {"id": "VTA-06", "nombre": "Facturar electrónicamente", "fase": 1, "funcion": null}, {"id": "VTA-07", "nombre": "Registrar y confirmar un pago", "fase": 1, "funcion": null}, {"id": "VTA-08", "nombre": "Vender a crédito y controlar la cartera", "fase": 2, "funcion": "venta_credito"}, {"id": "VTA-09", "nombre": "Generar pedidos recurrentes", "fase": 2, "funcion": "pedidos_recurrentes"}, {"id": "VTA-10", "nombre": "Registrar una permuta", "fase": 2, "funcion": "permuta"}, {"id": "VTA-11", "nombre": "Consultar la trazabilidad de un lote", "fase": 1, "funcion": null}, {"id": "VTA-12", "nombre": "Retirar un lote del mercado", "fase": 1, "funcion": null}],
    },
  },
];
