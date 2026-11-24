// Tablero de adopción (caso de uso ADO-15): cifras de la finca por tipo de plan, para la familia y el administrador.
//
// DE DÓNDE SALEN LOS DATOS: GET /api/v1/adopcion/tablero/ lee la vista adopcion.v_tablero, que solo ve la finca de la
// sesión (la finca la manda el interceptor en la cabecera X-Predio). El servidor exige el permiso adopcion.ver_tablero:
// el adoptante con cuenta recibe 403. Si la función «adopcion» está apagada en la finca, responde 422.
import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import { mensajeDeError } from '../../core/errores/errores';

/** Una fila de adopcion.v_tablero: un tipo de plan (frutal, maderable, ovino...). */
export interface FilaTablero {
  tipo: string;
  bienes_con_dueno: number;
  en_readopcion: number;
  disponibles: number;
  cuotas_mes: number; // suma de las cuotas mensuales de los contratos activos
  costo_cuidado_mes: number; // costo de cuidado estimado de esos bienes
}

/** Pesos colombianos sin decimales: 25000 -> «$ 25.000». */
export function pesos(valor: number | string): string {
  return Number(valor).toLocaleString('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 });
}

@Component({
  selector: 'gy-tablero-adopcion',
  imports: [RouterLink],
  template: `
    <h1>Tablero de adopción</h1>
    <p><a routerLink="..">← Casos de uso de adopción</a></p>
    @if (cargando()) {
      <p>Cargando…</p>
    } @else if (error()) {
      <p class="error" role="alert">{{ error() }}</p>
    } @else if (filas().length === 0) {
      <p class="nota">Esta finca todavía no tiene planes de adopción.</p>
    } @else {
      <table>
        <thead>
          <tr>
            <th scope="col">Tipo</th>
            <th scope="col">Con dueño</th>
            <th scope="col">En readopción</th>
            <th scope="col">Disponibles</th>
            <th scope="col">Cuotas del mes</th>
            <th scope="col">Costo de cuidado</th>
          </tr>
        </thead>
        <tbody>
          @for (f of filas(); track f.tipo) {
            <tr>
              <th scope="row">{{ f.tipo }}</th>
              <td>{{ f.bienes_con_dueno }}</td>
              <td>{{ f.en_readopcion }}</td>
              <td>{{ f.disponibles }}</td>
              <td>{{ pesos(f.cuotas_mes) }}</td>
              <td>{{ pesos(f.costo_cuidado_mes) }}</td>
            </tr>
          }
        </tbody>
      </table>
    }
  `,
  styles: `
    table { border-collapse: collapse; width: 100%; }
    th, td { padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--gy-borde); text-align: right; }
    th:first-child, td:first-child { text-align: left; }
    thead th { color: var(--gy-texto-suave); font-weight: 600; }
    .nota { color: var(--gy-texto-suave); }
    .error { color: var(--gy-alerta); }
  `,
})
export class TableroComponent {
  private readonly http = inject(HttpClient);
  readonly filas = signal<FilaTablero[]>([]);
  readonly cargando = signal(true);
  readonly error = signal<string | null>(null);
  readonly pesos = pesos;

  constructor() {
    void this.cargar();
  }

  /** Pide el tablero; si el servidor lo niega (403) o la función está apagada (422), muestra el motivo. */
  async cargar(): Promise<void> {
    this.cargando.set(true);
    this.error.set(null);
    try {
      this.filas.set(await firstValueFrom(this.http.get<FilaTablero[]>(`${environment.api}/adopcion/tablero/`)));
    } catch (e) {
      this.error.set(mensajeDeError(e));
    } finally {
      this.cargando.set(false);
    }
  }
}
