// Configuración global de la aplicación: qué servicios de Angular se activan al arrancar (los «proveedores»).
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, isDevMode, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideServiceWorker } from '@angular/service-worker';

import { routes } from './app.routes';
import { authInterceptor } from './core/auth/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    // Captura los errores no controlados del navegador y los muestra en la consola
    provideBrowserGlobalErrorListeners(),
    // Modo «sin zone.js»: Angular repinta solo cuando cambian las señales (más liviano en celulares)
    provideZonelessChangeDetection(),
    // Rutas de la aplicación; withComponentInputBinding pasa los parámetros de la URL como entradas del componente
    provideRouter(routes, withComponentInputBinding()),
    // Cliente HTTP con el interceptor que agrega el token y la finca a cada petición
    provideHttpClient(withInterceptors([authInterceptor])),
    // Service worker de la PWA: guarda la aplicación en el celular para abrirla sin internet.
    // Solo en producción (en desarrollo estorbaría al recargar); se registra 30 s después de que la app se estabiliza.
    provideServiceWorker('ngsw-worker.js', { enabled: !isDevMode(), registrationStrategy: 'registerWhenStable:30000' }),
  ],
};
