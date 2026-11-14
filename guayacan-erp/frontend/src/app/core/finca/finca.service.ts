// Servicio de finca actual (caso de uso NUC-03).
//
// POR QUÉ EXISTE: una misma persona puede trabajar en varias fincas (predios). Todo lo que hace se registra en
// la finca elegida. El id de la finca viaja en la cabecera X-Predio de cada petición (ver auth.interceptor.ts)
// y la base de datos solo deja ver y modificar los datos de esa finca (seguridad por filas, RLS).
//
// La finca elegida se recuerda en el celular para que al reabrir la app siga en la misma.
import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';

/** Una finca a la que la persona tiene acceso, con su rol en ella. */
export interface Finca {
  predio_id: number;
  nombre: string;
  rol: string; // p. ej. 'administrador', 'operario'
}

const CLAVE = 'guayacan.finca'; // nombre en localStorage

@Injectable({ providedIn: 'root' })
export class FincaService {
  private readonly http = inject(HttpClient);
  readonly actual = signal<number | null>(leer()); // id de la finca elegida
  readonly disponibles = signal<Finca[]>([]); // fincas para el selector de la barra

  /** Pide al servidor las fincas de la persona; si la guardada ya no es válida, elige la primera. */
  async cargar(): Promise<void> {
    this.disponibles.set(await firstValueFrom(this.http.get<Finca[]>(`${environment.api}/nucleo/mis-fincas/`)));
    const actual = this.actual();
    if (actual === null || !this.disponibles().some((f) => f.predio_id === actual)) {
      // «?.» y «??»: si no hay ninguna finca, queda en null sin fallar
      this.elegir(this.disponibles()[0]?.predio_id ?? null);
    }
  }

  /** Cambia la finca actual y la recuerda en el dispositivo. */
  elegir(predio: number | null): void {
    this.actual.set(predio);
    try {
      if (predio === null) {
        localStorage.removeItem(CLAVE);
      } else {
        localStorage.setItem(CLAVE, String(predio));
      }
    } catch {
      // Almacenamiento bloqueado: la finca vive solo en memoria
    }
  }
}

/** Lee la finca guardada al abrir la aplicación. */
function leer(): number | null {
  try {
    const v = localStorage.getItem(CLAVE);
    return v ? Number(v) : null;
  } catch {
    return null;
  }
}
