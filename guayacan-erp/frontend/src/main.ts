// Punto de entrada del frontend: es lo primero que ejecuta el navegador.
// Arranca el componente raíz (App) con la configuración global (rutas, HTTP, service worker).
import { bootstrapApplication } from '@angular/platform-browser';

import { App } from './app/app';
import { appConfig } from './app/app.config';

// Si algo falla al arrancar, el error se muestra en la consola del navegador (F12)
bootstrapApplication(App, appConfig).catch((err) => console.error(err));
