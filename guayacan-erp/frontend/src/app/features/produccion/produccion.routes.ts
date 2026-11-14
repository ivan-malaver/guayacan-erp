// Rutas del módulo «Producción animal y agrícola» (prefijo PRO). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /produccion, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /produccion
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Producción animal y agrícola",
      casos: [{"id": "PRO-01", "nombre": "Registrar el ingreso de un lote de animales", "fase": 1, "funcion": null}, {"id": "PRO-02", "nombre": "Registrar la postura diaria y clasificar el huevo", "fase": 1, "funcion": null}, {"id": "PRO-03", "nombre": "Registrar alimentación, pesajes y eventos sanitarios", "fase": 1, "funcion": null}, {"id": "PRO-04", "nombre": "Registrar eventos reproductivos de ovinos y caprinos", "fase": 1, "funcion": null}, {"id": "PRO-05", "nombre": "Registrar una siembra y sus labores culturales", "fase": 1, "funcion": null}, {"id": "PRO-06", "nombre": "Registrar una cosecha y su destino", "fase": 1, "funcion": null}, {"id": "PRO-07", "nombre": "Registrar un análisis de suelo y su recomendación", "fase": 1, "funcion": null}, {"id": "PRO-08", "nombre": "Registrar bioseguridad e inocuidad", "fase": 1, "funcion": null}, {"id": "PRO-09", "nombre": "Producir abono en lombricultivo o compostera", "fase": 1, "funcion": null}, {"id": "PRO-10", "nombre": "Medir la calidad del agua de los estanques", "fase": 1, "funcion": null}],
    },
  },
];
