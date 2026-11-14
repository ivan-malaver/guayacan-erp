// Guardia de rutas: decide si la persona puede entrar a una pantalla protegida.
//
// CÓMO DECIDE
// 1. Si ya hay sesión (token de acceso en memoria): pasa.
// 2. Si no, pero hay token de refresco guardado (p. ej. el operario cerró y volvió a abrir la PWA en el campo):
//    lo renueva, recarga la lista de fincas y pasa. Así no tiene que escribir la contraseña cada vez.
// 3. Si no hay nada: lo envía a /ingreso.
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { FincaService } from '../finca/finca.service';
import { SesionService } from './sesion.service';

export const sesionGuard: CanActivateFn = async () => {
  const sesion = inject(SesionService);
  const finca = inject(FincaService);
  const router = inject(Router);
  if (sesion.activa()) {
    return true;
  }
  if (await sesion.refrescar()) {
    // Sin señal la carga falla; se ignora el error y se conserva la finca guardada en el celular
    await finca.cargar().catch(() => undefined);
    return true;
  }
  // Devolver un UrlTree le dice al enrutador «en vez de entrar aquí, ve a /ingreso»
  return router.createUrlTree(['/ingreso']);
};
