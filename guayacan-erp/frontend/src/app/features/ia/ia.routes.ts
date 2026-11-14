// Rutas del módulo «Inteligencia artificial» (prefijo IA). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /ia, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /ia
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Inteligencia artificial",
      casos: [{"id": "IA-01", "nombre": "Configurar un agente y sus herramientas", "fase": 1, "funcion": null}, {"id": "IA-02", "nombre": "Resolver la bandeja de aprobaciones", "fase": 1, "funcion": null}, {"id": "IA-03", "nombre": "Alimentar la base de conocimiento", "fase": 1, "funcion": null}, {"id": "IA-04", "nombre": "Recibir y seguir recomendaciones de mejora", "fase": 1, "funcion": null}, {"id": "IA-05", "nombre": "Evaluar las respuestas de los agentes", "fase": 1, "funcion": null}, {"id": "IA-06", "nombre": "Controlar el consumo y el costo de la IA", "fase": 1, "funcion": null}, {"id": "IA-07", "nombre": "Pronosticar la demanda", "fase": 3, "funcion": "pronostico_demanda"}, {"id": "IA-08", "nombre": "Diagnosticar una foto de campo", "fase": 2, "funcion": "diagnostico_imagen"}, {"id": "IA-09", "nombre": "Simular un escenario y registrar la decisión", "fase": 2, "funcion": null}],
    },
  },
];
