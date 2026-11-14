// Página provisional de un módulo: lista sus casos de uso que están por construir.
//
// CÓMO RECIBE LOS DATOS: cada archivo features/<modulo>/<modulo>.routes.ts le pasa, en «data», el título
// y la lista de casos de uso. Esta pantalla los lee de la ruta activa (ActivatedRoute) y los muestra.
// Cuando se construya un caso de uso, su pantalla real reemplaza o complementa a esta.
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs';

/** Un caso de uso tal como viene del catálogo. */
interface Caso {
  id: string; // p. ej. 'ADO-02'
  nombre: string;
  fase: number; // fase del plan de desarrollo en que se construye
  funcion: string | null; // bandera de función que lo activa (p. ej. 'adopcion'), si la tiene
}

@Component({
  selector: 'gy-modulo-pendiente',
  template: `
    <h1>{{ datos()?.titulo }}</h1>
    <p class="nota">Casos de uso de este módulo. Cada uno se construye con su especificación del documento técnico.</p>
    <ul class="casos">
      @for (c of datos()?.casos ?? []; track c.id) {
        <li>
          <span class="id">{{ c.id }}</span>
          <span>{{ c.nombre }}</span>
          <span class="fase">Fase {{ c.fase }}@if (c.funcion) { · {{ c.funcion }} }</span>
        </li>
      }
    </ul>
  `,
  styles: `
    .nota { color: var(--gy-texto-suave); }
    .casos { list-style: none; padding: 0; display: grid; gap: 0.5rem; }
    .casos li { display: grid; grid-template-columns: 5.5rem 1fr auto; gap: 0.75rem; padding: 0.75rem; border: 1px solid var(--gy-borde); border-radius: 8px; }
    .id { font-weight: 600; color: var(--gy-primario); }
    .fase { color: var(--gy-texto-suave); font-size: 0.875rem; }
  `,
})
export class ModuloPendienteComponent {
  // toSignal convierte el flujo de datos de la ruta (Observable) en una señal que la plantilla puede leer
  readonly datos = toSignal(inject(ActivatedRoute).data.pipe(map((d) => d as { titulo: string; casos: Caso[] })));
}
