// Pantalla de ingreso (caso de uso SEG-01): correo y contraseña.
// El doble factor para administrador y contador está por construir (SEG-02).
//
// CONCEPTOS
// - Formulario reactivo (FormBuilder): el formulario y sus validaciones se definen en el código, no en el HTML.
//   «nonNullable» hace que los campos nunca queden en null, siempre texto (vacío si se borra).
// - [formGroup], formControlName: enlazan cada <input> con su campo del formulario.
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { mensajeDeError } from '../errores/errores';
import { SesionService } from './sesion.service';

@Component({
  selector: 'gy-ingreso',
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="ingresar()" class="ingreso">
      <h1>GuayacanERP</h1>
      <!-- autocomplete ayuda a que el navegador recuerde el usuario y la contraseña -->
      <label>Correo <input type="email" formControlName="correo" autocomplete="username" /></label>
      <label>Contraseña <input type="password" formControlName="contrasena" autocomplete="current-password" /></label>
      @if (error()) {
        <!-- role="alert" hace que los lectores de pantalla lean el error en voz alta -->
        <p class="error" role="alert">{{ error() }}</p>
      }
      <!-- El botón se desactiva si faltan datos o si ya se está enviando (evita doble clic) -->
      <button type="submit" [disabled]="form.invalid || enviando()">Ingresar</button>
    </form>
  `,
  styles: `
    .ingreso { max-width: 22rem; margin: 3rem auto; display: grid; gap: 1rem; }
    label { display: grid; gap: 0.25rem; }
    input, button { min-height: 3rem; font-size: 1rem; }
    .error { color: var(--gy-alerta); }
  `,
})
export class IngresoComponent {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  // Campos del formulario con sus reglas: correo obligatorio y con formato válido; contraseña obligatoria
  readonly form = inject(FormBuilder).nonNullable.group({
    correo: ['', [Validators.required, Validators.email]],
    contrasena: ['', Validators.required],
  });
  readonly error = signal<string | null>(null); // mensaje de error visible (o null)
  readonly enviando = signal(false); // true mientras se espera la respuesta del servidor

  /** Envía las credenciales; si son válidas, lleva al inicio; si no, muestra el motivo. */
  async ingresar(): Promise<void> {
    this.enviando.set(true);
    this.error.set(null);
    try {
      const { correo, contrasena } = this.form.getRawValue();
      await this.sesion.ingresar(correo, contrasena);
      await this.router.navigateByUrl('/');
    } catch (e) {
      // Traduce el error del servidor a un mensaje entendible (core/errores/errores.ts)
      this.error.set(mensajeDeError(e));
    } finally {
      // «finally» se ejecuta siempre, haya error o no: vuelve a habilitar el botón
      this.enviando.set(false);
    }
  }
}
