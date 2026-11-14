// Prueba unitaria del generador UUIDv7. Se corre con:  npm test
// describe() agrupa pruebas; it() es una prueba; expect() comprueba un resultado.
import { uuidv7 } from './uuidv7';

describe('uuidv7', () => {
  it('tiene versión 7, variante RFC y orden por tiempo', () => {
    // Dos identificadores con un milisegundo de diferencia
    const a = uuidv7(1_700_000_000_000);
    const b = uuidv7(1_700_000_000_001);
    // El formato debe cumplir la norma (el «7» de versión y la variante 8, 9, a o b)
    expect(a).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    // El más reciente debe quedar después al ordenar como texto
    expect(a < b).toBeTrue();
  });
});
