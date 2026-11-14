// Rutas del módulo «Nómina» (prefijo NOM). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /nomina, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /nomina
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Nómina",
      casos: [{"id": "NOM-01", "nombre": "Configurar conceptos y tarifas de nómina", "fase": 2, "funcion": null}, {"id": "NOM-02", "nombre": "Preparar la prenómina", "fase": 2, "funcion": null}, {"id": "NOM-03", "nombre": "Registrar novedades manuales", "fase": 2, "funcion": null}, {"id": "NOM-04", "nombre": "Liquidar la nómina", "fase": 2, "funcion": null}, {"id": "NOM-05", "nombre": "Cerrar el periodo de nómina", "fase": 2, "funcion": null}, {"id": "NOM-06", "nombre": "Preparar y aprobar los pagos de nómina", "fase": 2, "funcion": null}, {"id": "NOM-07", "nombre": "Generar la PILA y exportar al contador", "fase": 2, "funcion": null}, {"id": "NOM-08", "nombre": "Transmitir la nómina electrónica", "fase": 2, "funcion": "nomina_electronica"}],
    },
  },
];
