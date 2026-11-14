// Componente raíz: el «marco» que envuelve todas las pantallas de la aplicación.
//
// QUÉ MUESTRA
// - Una barra superior (solo con sesión iniciada) con la marca, el selector de finca y el estado de conexión.
// - Debajo, <router-outlet />: el hueco donde Angular pinta la pantalla de la ruta actual.
//
// CONCEPTOS
// - signal(): una variable «reactiva». Cuando cambia su valor, Angular repinta lo que la usa, sin más código.
// - inject(): pide a Angular una instancia de un servicio (inyección de dependencias).
// - @if / @for: bloques de control de la plantilla (mostrar si..., repetir por cada...).
import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

import { SesionService } from './core/auth/sesion.service';
import { FincaService } from './core/finca/finca.service';

@Component({
  selector: 'gy-raiz', // etiqueta HTML que lo invoca en index.html
  imports: [RouterOutlet, RouterLink],
  template: `
    @if (sesion.activa()) {
      <header class="barra">
        <a routerLink="/" class="marca">El Guayacán</a>
        <!-- Selector de finca: al cambiarlo, todas las peticiones siguientes van con la nueva finca (X-Predio) -->
        <select aria-label="Finca" [value]="finca.actual() ?? ''" (change)="cambiar($event)">
          @for (f of finca.disponibles(); track f.predio_id) {
            <option [value]="f.predio_id">{{ f.nombre }}</option>
          }
        </select>
        <!-- Aviso de conexión: en el campo es clave saber si lo capturado ya se envió -->
        <span class="conexion" [class.fuera]="!enLinea()">{{ enLinea() ? 'En línea' : 'Sin conexión' }}</span>
      </header>
    }
    <main class="contenido"><router-outlet /></main>
  `,
  styles: `
    .barra { display: flex; align-items: center; gap: 1rem; padding: 0.5rem 1rem; background: var(--gy-primario); color: #fff; flex-wrap: wrap; }
    .marca { color: #fff; font-weight: 700; text-decoration: none; }
    select { min-height: 2.5rem; }
    .conexion { margin-left: auto; font-size: 0.875rem; }
    .conexion.fuera { color: #ffd27a; font-weight: 600; }
    .contenido { padding: 1rem; max-width: 72rem; margin: 0 auto; }
  `,
})
export class App {
  readonly sesion = inject(SesionService);
  readonly finca = inject(FincaService);
  // Estado de conexión del navegador; arranca con el valor actual
  readonly enLinea = signal(navigator.onLine);

  constructor() {
    // El navegador avisa cuando se pierde o vuelve la señal; se actualiza la señal y la barra se repinta sola
    window.addEventListener('online', () => this.enLinea.set(true));
    window.addEventListener('offline', () => this.enLinea.set(false));
  }

  /** Se ejecuta al elegir otra finca en el selector. */
  cambiar(evento: Event): void {
    // El valor del <select> llega como texto; se convierte a número (predio_id)
    this.finca.elegir(Number((evento.target as HTMLSelectElement).value));
  }
}
