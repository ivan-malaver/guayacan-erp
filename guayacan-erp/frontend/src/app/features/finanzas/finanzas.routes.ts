// Rutas del módulo «Finanzas y contabilidad» (prefijo FIN). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /finanzas, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /finanzas
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Finanzas y contabilidad",
      casos: [{"id": "FIN-01", "nombre": "Configurar el plan de cuentas y los centros de costo", "fase": 1, "funcion": null}, {"id": "FIN-02", "nombre": "Contabilizar un comprobante", "fase": 1, "funcion": null}, {"id": "FIN-03", "nombre": "Anular un comprobante o registrar una nota", "fase": 1, "funcion": null}, {"id": "FIN-04", "nombre": "Cerrar el periodo contable", "fase": 1, "funcion": null}, {"id": "FIN-05", "nombre": "Clasificar costos y distribuirlos por actividades", "fase": 2, "funcion": null}, {"id": "FIN-06", "nombre": "Elaborar y aprobar el presupuesto maestro", "fase": 2, "funcion": null}, {"id": "FIN-07", "nombre": "Generar los estados financieros", "fase": 2, "funcion": null}, {"id": "FIN-08", "nombre": "Calcular indicadores y consultar el tablero", "fase": 2, "funcion": null}, {"id": "FIN-09", "nombre": "Analizar estados: vertical, horizontal, fuentes y usos", "fase": 2, "funcion": null}, {"id": "FIN-10", "nombre": "Calcular punto de equilibrio y palancas", "fase": 2, "funcion": null}, {"id": "FIN-11", "nombre": "Gestionar anticipos a proveedores", "fase": 2, "funcion": null}, {"id": "FIN-12", "nombre": "Emitir un informe de indicadores para crédito", "fase": 3, "funcion": "indicadores_credito"}],
    },
  },
];
