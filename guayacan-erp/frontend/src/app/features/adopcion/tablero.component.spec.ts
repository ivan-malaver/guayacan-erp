// Prueba de humo del tablero de adopción (ADO-15). Se corre con:  npm test
// HttpTestingController hace de servidor: la prueba decide qué responde GET /adopcion/tablero/.
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { environment } from '../../../environments/environment';
import { pesos, TableroComponent } from './tablero.component';

describe('TableroComponent (ADO-15)', () => {
  let servidor: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideZonelessChangeDetection(), provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    servidor = TestBed.inject(HttpTestingController);
  });

  afterEach(() => servidor.verify()); // ninguna petición quedó sin responder

  /** Crea la pantalla, responde la petición del tablero y devuelve el texto que ve la persona. */
  async function mostrar(respuesta: object, estado = 200): Promise<string> {
    const pantalla = TestBed.createComponent(TableroComponent);
    const peticion = servidor.expectOne(`${environment.api}/adopcion/tablero/`);
    expect(peticion.request.method).toBe('GET');
    peticion.flush(respuesta, { status: estado, statusText: estado === 200 ? 'OK' : 'Error' });
    await pantalla.whenStable();
    pantalla.detectChanges();
    return (pantalla.nativeElement as HTMLElement).textContent ?? '';
  }

  it('muestra una fila por tipo con las cuotas en pesos', async () => {
    const texto = await mostrar([{ tipo: 'frutal', bienes_con_dueno: 1, en_readopcion: 0, disponibles: 2, cuotas_mes: 25000, costo_cuidado_mes: 9000 }]);
    expect(texto).toContain('frutal');
    expect(texto).toContain(pesos(25000));
    expect(texto).toContain(pesos(9000));
  });

  it('sin permiso (403, rol cliente) explica que no tiene permiso', async () => {
    const texto = await mostrar({ detail: 'Necesita el permiso adopcion.ver_tablero' }, 403);
    expect(texto).toContain('No tiene permiso');
  });

  it('con la función apagada (422) muestra el motivo de la base', async () => {
    const texto = await mostrar({ codigo: 'regla_negocio', detalle: 'La función adopcion no está activa en esta finca' }, 422);
    expect(texto).toContain('La función adopcion no está activa');
  });

  it('una finca sin planes muestra el aviso', async () => {
    expect(await mostrar([])).toContain('todavía no tiene planes');
  });

  it('formatea pesos colombianos sin decimales', () => {
    expect(pesos(25000)).toMatch(/25\.000/);
  });
});
