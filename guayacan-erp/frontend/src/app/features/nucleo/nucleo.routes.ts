// Rutas del módulo «Núcleo de la plataforma» (prefijo NUC). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /nucleo, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /nucleo
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "Núcleo de la plataforma",
      casos: [{"id": "NUC-01", "nombre": "Configurar la finca, sus zonas y el mapa", "fase": 1, "funcion": null}, {"id": "NUC-02", "nombre": "Gestionar usuarios, roles y permisos", "fase": 1, "funcion": null}, {"id": "NUC-03", "nombre": "Administrar parámetros con vigencia", "fase": 1, "funcion": null}, {"id": "NUC-04", "nombre": "Encender o apagar una función de la finca", "fase": 1, "funcion": null}, {"id": "NUC-05", "nombre": "Sincronizar registros capturados sin conexión", "fase": 1, "funcion": null}, {"id": "NUC-06", "nombre": "Consultar la auditoría de cambios", "fase": 1, "funcion": null}, {"id": "NUC-07", "nombre": "Registrar una nota de voz en campo y confirmarla", "fase": 2, "funcion": "notas_voz"}, {"id": "NUC-08", "nombre": "Practicar en la finca de aprendizaje", "fase": 1, "funcion": "modo_aprendiz"}, {"id": "NUC-09", "nombre": "Publicar los eventos de integración", "fase": 1, "funcion": null}, {"id": "NUC-10", "nombre": "Administrar llaves de API B2B y webhooks", "fase": 3, "funcion": "api_b2b"}],
    },
  },
];
