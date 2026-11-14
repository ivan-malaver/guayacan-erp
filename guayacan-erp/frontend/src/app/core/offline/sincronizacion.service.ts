// Servicio de captura y sincronización sin conexión (caso de uso NUC-05, sección 10.4 del documento técnico).
//
// CÓMO FUNCIONA
// 1. capturar(): guarda el registro en el celular (IndexedDB) con un UUIDv7 nuevo. No necesita señal.
// 2. sincronizar(): cuando hay señal (al volver la conexión y cada minuto), sube los pendientes en lotes de
//    hasta 200, agrupados por finca, a POST /api/v1/sincronizacion/lote/.
// 3. El servidor responde por cada registro:
//    - 'creado' o 'repetido' → se borra de la cola (repetido = ya había llegado antes; no se duplica gracias al UUID).
//    - 'rechazado'           → queda en la cola con el mensaje de la regla para que la persona lo corrija.
import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FincaService } from '../finca/finca.service';
import { baseLocal, RegistroPendiente } from './cola.db';
import { uuidv7 } from './uuidv7';

/** Resultado del servidor para cada registro enviado (backend/guayacan/sincronizacion.py). */
interface Resultado {
  tabla: string;
  id_cliente: string;
  estado: 'creado' | 'repetido' | 'rechazado';
  id?: number; // id asignado por la base cuando se creó
  detalle?: unknown; // motivo del rechazo
}

const TAMANO_LOTE = 200; // máximo de registros por envío (el backend acepta el mismo límite)

@Injectable({ providedIn: 'root' })
export class SincronizacionService {
  private readonly http = inject(HttpClient);
  private readonly finca = inject(FincaService);
  readonly pendientes = signal(0); // contador visible en la pantalla de inicio
  readonly rechazados = signal(0);
  private enCurso = false; // evita dos sincronizaciones al mismo tiempo

  constructor() {
    // Al volver la señal, sincroniza de inmediato; además, cada 60 segundos por si acaso
    window.addEventListener('online', () => void this.sincronizar());
    setInterval(() => void this.sincronizar(), 60_000);
    void this.contar(); // «void» indica que no se espera la promesa a propósito
  }

  /** Guarda un registro en la cola local. Devuelve su id_cliente (útil para seguirle la pista). */
  async capturar(tabla: string, datos: Record<string, unknown>): Promise<string> {
    const predio = this.finca.actual();
    if (predio === null) {
      throw new Error('Elija una finca antes de capturar');
    }
    const registro: RegistroPendiente = {
      id_cliente: uuidv7(),
      tabla,
      capturado_en: new Date().toISOString(),
      predio_id: predio,
      datos,
      estado: 'pendiente',
      intentos: 0,
    };
    await baseLocal.cola.add(registro);
    await this.contar();
    // Si hay señal, intenta enviarlo ya (sin esperar a que termine)
    if (navigator.onLine) {
      void this.sincronizar();
    }
    return registro.id_cliente;
  }

  /** Sube los pendientes por finca y por lotes. Si falla la red, lo pendiente sigue en la cola para la próxima. */
  async sincronizar(): Promise<void> {
    if (this.enCurso || !navigator.onLine) {
      return;
    }
    this.enCurso = true;
    try {
      // Fincas que tienen algo pendiente (Set = lista sin repetidos)
      const fincas = new Set((await baseLocal.cola.where('estado').equals('pendiente').toArray()).map((r) => r.predio_id));
      for (const predio of fincas) {
        let lote = await baseLocal.cola.where('estado').equals('pendiente').filter((r) => r.predio_id === predio).limit(TAMANO_LOTE).toArray();
        while (lote.length > 0) {
          const respuesta = await firstValueFrom(
            this.http.post<{ resultados: Resultado[] }>(
              `${environment.api}/sincronizacion/lote/`,
              // Solo se envían los campos que el servidor necesita
              { registros: lote.map(({ tabla, id_cliente, capturado_en, datos }) => ({ tabla, id_cliente, capturado_en, datos })) },
              // Cada lote va con SU finca, aunque la persona tenga elegida otra en este momento
              { headers: { 'X-Predio': String(predio) } },
            ),
          );
          await this.aplicar(respuesta.resultados);
          // Si el lote vino incompleto, ya no queda nada más de esta finca
          if (lote.length < TAMANO_LOTE) {
            break;
          }
          lote = await baseLocal.cola.where('estado').equals('pendiente').filter((r) => r.predio_id === predio).limit(TAMANO_LOTE).toArray();
        }
      }
    } finally {
      this.enCurso = false;
      await this.contar();
    }
  }

  /** Aplica la respuesta del servidor a la cola local, todo dentro de una transacción (todo o nada). */
  private async aplicar(resultados: Resultado[]): Promise<void> {
    await baseLocal.transaction('rw', baseLocal.cola, async () => {
      for (const r of resultados) {
        if (r.estado === 'rechazado') {
          await baseLocal.cola.update(r.id_cliente, { estado: 'rechazado', detalle: r.detalle });
        } else {
          await baseLocal.cola.delete(r.id_cliente);
        }
      }
    });
  }

  /** Actualiza los contadores de pendientes y rechazados. */
  private async contar(): Promise<void> {
    this.pendientes.set(await baseLocal.cola.where('estado').equals('pendiente').count());
    this.rechazados.set(await baseLocal.cola.where('estado').equals('rechazado').count());
  }
}
