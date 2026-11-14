// Rutas del módulo «IoT, seguridad perimetral y robótica» (prefijo IOT). ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// QUÉ HACE: cuando la persona entra a /iot, Angular carga este archivo (carga perezosa) y muestra la pantalla
// ModuloPendienteComponent con la lista de casos de uso del módulo que aún están por construir.
//
// CÓMO AMPLIARLO: al construir un caso de uso, agregue una ruta hija con su componente, por ejemplo
//   { path: 'lotes', loadComponent: () => import('./lotes.component').then((c) => c.LotesComponent) }
// Las pantallas de campo deben funcionar sin conexión (guardar en la cola local, ver core/offline).
import { Routes } from '@angular/router';

import { ModuloPendienteComponent } from '../../shared/modulo-pendiente.component';

export const RUTAS: Routes = [
  {
    path: '', // ruta raíz del módulo: /iot
    component: ModuloPendienteComponent,
    // «data» viaja a la pantalla: el título y los casos de uso que lista
    data: {
      titulo: "IoT, seguridad perimetral y robótica",
      casos: [{"id": "IOT-01", "nombre": "Registrar dispositivos, sensores y actuadores", "fase": 4, "funcion": null}, {"id": "IOT-02", "nombre": "Recibir lecturas de sensores", "fase": 4, "funcion": null}, {"id": "IOT-03", "nombre": "Accionar un actuador a mano", "fase": 4, "funcion": null}, {"id": "IOT-04", "nombre": "Armar y desarmar la alarma por zonas", "fase": 4, "funcion": "seguridad_perimetral"}, {"id": "IOT-05", "nombre": "Atender un evento de seguridad perimetral", "fase": 4, "funcion": "seguridad_perimetral"}, {"id": "IOT-06", "nombre": "Gestionar credenciales de acceso a puertas", "fase": 4, "funcion": null}, {"id": "IOT-07", "nombre": "Conservar o depurar clips de cámaras", "fase": 4, "funcion": "camaras"}, {"id": "IOT-08", "nombre": "Planear y ejecutar una misión de dron o robot", "fase": 4, "funcion": "dron_monitoreo"}, {"id": "IOT-09", "nombre": "Cortar cargas con batería baja", "fase": 4, "funcion": null}],
    },
  },
];
