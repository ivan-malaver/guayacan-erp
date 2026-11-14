// Traducción de errores: convierte la respuesta de error del servidor en un mensaje claro para la persona.
//
// De dónde vienen los errores: el backend (backend/guayacan/errores.py) convierte cada regla que rompe la base
// de datos (SQLSTATE de PostgreSQL) en una respuesta HTTP con un JSON { codigo, detalle, ... }.
// Este archivo decide qué texto mostrar.
import { HttpErrorResponse } from '@angular/common/http';

/** Respuesta de error de la API. Los campos con «?» son opcionales. */
export interface ErrorApi {
  codigo: string; // p. ej. 'sin_permiso', 'duplicado', 'cruce', 'por_construir'
  detalle?: string; // mensaje de la regla de la base (ya en español)
  caso_de_uso?: string; // código del caso de uso cuando la función está por construir (501)
  campo?: string; // columna afectada, si aplica
  restriccion?: string; // nombre de la restricción de la base que falló
}

/** Devuelve el mensaje para la persona: el de la regla cuando lo hay; si no, uno general según el código. */
export function mensajeDeError(err: unknown): string {
  if (!(err instanceof HttpErrorResponse)) {
    return 'Ocurrió un error inesperado.';
  }
  // Estado 0 = la petición ni siquiera llegó al servidor (sin conexión)
  if (err.status === 0) {
    return 'Sin conexión. Lo capturado queda guardado y se enviará al volver la señal.';
  }
  const cuerpo = err.error as Partial<ErrorApi> | null;
  // «?.» (encadenamiento opcional): si cuerpo es null no falla, simplemente da undefined
  if (cuerpo?.detalle) {
    return cuerpo.detalle;
  }
  switch (cuerpo?.codigo) {
    case 'sin_permiso':
      return 'No tiene permiso para hacer esto en esta finca.';
    case 'duplicado':
      return 'Ese registro ya existe.';
    case 'cruce':
      return 'Se cruza con otra reserva o turno.';
    case 'por_construir':
      return `Esta función (${cuerpo.caso_de_uso}) todavía no está disponible.`;
    default:
      return 'No se pudo completar la operación.';
  }
}
