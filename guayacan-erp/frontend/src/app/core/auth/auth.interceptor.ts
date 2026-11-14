// Interceptor HTTP: un «filtro» por el que pasa cada petición que hace la aplicación antes de salir al servidor.
//
// QUÉ HACE
// 1. Si la petición va a nuestra API, le agrega dos cabeceras:
//    - Authorization: Bearer <token>  → quién es la persona (el backend lo valida con JWT).
//    - X-Predio: <id de la finca>     → en qué finca trabaja (el backend fija app.predio_id y la seguridad
//      por filas de PostgreSQL solo deja ver los datos de esa finca).
// 2. Si el servidor responde 401 (token vencido), intenta renovar el token UNA vez y repite la petición.
//
// POR QUÉ: así ninguna pantalla tiene que acordarse de poner el token ni la finca; se hace en un solo lugar.
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, from, switchMap, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FincaService } from '../finca/finca.service';
import { SesionService } from './sesion.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // Peticiones a otros sitios, o al propio inicio de sesión, salen sin tocar
  if (!req.url.startsWith(environment.api) || req.url.includes('/auth/token')) {
    return next(req);
  }
  const sesion = inject(SesionService);
  const finca = inject(FincaService);

  // Arma una copia de la petición con las cabeceras (las peticiones de Angular no se modifican, se clonan)
  const preparar = () => {
    let headers = req.headers;
    const token = sesion.acceso();
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    const predio = finca.actual();
    // Si la petición ya trae X-Predio (p. ej. la sincronización de otra finca), se respeta
    if (predio !== null && !headers.has('X-Predio')) {
      headers = headers.set('X-Predio', String(predio));
    }
    return req.clone({ headers });
  };

  return next(preparar()).pipe(
    catchError((err: unknown) => {
      // 401 = no autorizado: el token de acceso venció. Se intenta refrescar y, si se logra, se repite la petición
      if (err instanceof HttpErrorResponse && err.status === 401) {
        return from(sesion.refrescar()).pipe(switchMap((ok) => (ok ? next(preparar()) : throwError(() => err))));
      }
      // Cualquier otro error sigue su camino hacia la pantalla que hizo la petición
      return throwError(() => err);
    }),
  );
};
