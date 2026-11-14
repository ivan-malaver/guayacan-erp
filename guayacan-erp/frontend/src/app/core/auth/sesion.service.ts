// Servicio de sesión (caso de uso SEG-01): inicia, renueva y cierra la sesión de la persona.
//
// LOS DOS TOKENS (JWT)
// - Acceso: dura poco (minutos). Vive solo en memoria; si alguien roba el celular y abre la app, no queda escrito.
// - Refresco: dura más (días). Se guarda en el almacenamiento local del navegador para que el operario
//   no tenga que ingresar cada vez que abre la PWA en el campo. Con él se pide un token de acceso nuevo.
//
// @Injectable({ providedIn: 'root' }): Angular crea UNA sola instancia para toda la aplicación.
import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Finca, FincaService } from '../finca/finca.service';

/** Forma de la respuesta del backend al iniciar sesión (POST /api/v1/auth/token/). */
interface RespuestaIngreso {
  acceso: string;
  refresco: string;
  predio_id: number | null; // finca por defecto de la persona
  fincas: Finca[]; // fincas a las que tiene acceso
}

// Nombre con el que se guarda el token de refresco en localStorage
const CLAVE = 'guayacan.sesion';

@Injectable({ providedIn: 'root' })
export class SesionService {
  private readonly http = inject(HttpClient);
  private readonly finca = inject(FincaService);
  readonly acceso = signal<string | null>(null);
  private refresco: string | null = leer();
  // computed(): señal derivada; se recalcula sola cuando cambia «acceso»
  readonly activa = computed(() => this.acceso() !== null);

  /** Envía correo y contraseña; guarda los tokens y las fincas que devuelve el servidor. */
  async ingresar(correo: string, contrasena: string): Promise<void> {
    // firstValueFrom convierte la respuesta HTTP (Observable) en una promesa para poder usar await
    const r = await firstValueFrom(this.http.post<RespuestaIngreso>(`${environment.api}/auth/token/`, { correo, contrasena }));
    this.acceso.set(r.acceso);
    this.guardarRefresco(r.refresco);
    this.finca.disponibles.set(r.fincas);
    this.finca.elegir(r.predio_id);
  }

  /** Pide un token de acceso nuevo con el de refresco. Devuelve true si lo logró. */
  async refrescar(): Promise<boolean> {
    if (!this.refresco) {
      return false;
    }
    try {
      // Esta ruta la atiende SimpleJWT, por eso los nombres van en inglés (access, refresh)
      const r = await firstValueFrom(this.http.post<{ access: string; refresh?: string }>(`${environment.api}/auth/token/refrescar/`, { refresh: this.refresco }));
      this.acceso.set(r.access);
      // Si el servidor rota el token de refresco, se guarda el nuevo
      if (r.refresh) {
        this.guardarRefresco(r.refresh);
      }
      return true;
    } catch {
      // Refresco vencido o revocado: se cierra la sesión y tocará ingresar de nuevo
      this.salir();
      return false;
    }
  }

  /** Cierra la sesión en este dispositivo. */
  salir(): void {
    this.acceso.set(null);
    this.guardarRefresco(null);
  }

  private guardarRefresco(valor: string | null): void {
    this.refresco = valor;
    try {
      if (valor) {
        localStorage.setItem(CLAVE, valor);
      } else {
        localStorage.removeItem(CLAVE);
      }
    } catch {
      // Almacenamiento bloqueado (modo privado, por ejemplo): la sesión dura lo que dure la pestaña
    }
  }
}

/** Lee el token de refresco guardado al abrir la aplicación. */
function leer(): string | null {
  try {
    return localStorage.getItem(CLAVE);
  } catch {
    return null;
  }
}
