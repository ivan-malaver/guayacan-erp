// Rutas del módulo «Adopción de árboles y animales» (prefijo ADO). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /adopcion, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /adopcion
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Adopción de árboles y animales",
      casos: [{"id": "ADO-01", "nombre": "Configurar catálogo y sitios", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-02", "nombre": "Comprar un árbol o un animal", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-03", "nombre": "Sembrar en persona", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-04", "nombre": "Sembrar por un trabajador y enviar el video", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-05", "nombre": "Cobrar y pagar la cuota mensual", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-06", "nombre": "Seguir mi árbol o mi animal", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-07", "nombre": "Detectar abandono y poner en readopción", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-08", "nombre": "Readoptar", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-09", "nombre": "Registrar y vender productos del bien", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-10", "nombre": "Liquidar productos con el 5 %", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-11", "nombre": "Decidir en la madurez: mantener o liquidar", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-12", "nombre": "Talar o sacrificar y liquidar", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-13", "nombre": "Reponer un bien muerto en garantía", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-14", "nombre": "Ceder o regalar la adopción", "fase": 3, "funcion": "adopcion"}, {"id": "ADO-15", "nombre": "Consultar el tablero de adopción", "fase": 3, "funcion": "adopcion"}],
    },
  },
];
