// Pantalla de inicio: estado de la sincronización y el menú con los módulos.
//
// - Arriba: cuántos registros capturados sin señal faltan por enviar y cuántos rechazó el servidor.
// - Abajo: una tarjeta por módulo (la lista sale de modulos.ts, generado desde el catálogo de casos de uso).
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { SincronizacionService } from '../core/offline/sincronizacion.service';
import { MODULOS } from './modulos';

@Component({
  selector: 'gy-inicio',
  imports: [RouterLink],
  template: `
    <section class="estado">
      <span>Pendientes por enviar: {{ sync.pendientes() }}</span>
      @if (sync.rechazados() > 0) {
        <span class="alerta">Rechazados por corregir: {{ sync.rechazados() }}</span>
      }
    </section>
    <nav class="modulos">
      <!-- track m.ruta: Angular usa la ruta para saber qué tarjeta es cuál y no repintarlas todas -->
      @for (m of modulos; track m.ruta) {
        <a [routerLink]="['/', m.ruta]"><strong>{{ m.prefijo }}</strong> {{ m.titulo }}</a>
      }
    </nav>
  `,
  styles: `
    .estado { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
    .alerta { color: var(--gy-alerta); font-weight: 600; }
    /* Rejilla que se adapta: tantas columnas como quepan de al menos 14rem (en celular, una sola) */
    .modulos { display: grid; grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr)); gap: 0.75rem; }
    .modulos a { padding: 1rem; border: 1px solid var(--gy-borde); border-radius: 8px; text-decoration: none; color: inherit; min-height: 3rem; }
  `,
})
export class InicioComponent {
  readonly sync = inject(SincronizacionService);
  readonly modulos = MODULOS;
}
