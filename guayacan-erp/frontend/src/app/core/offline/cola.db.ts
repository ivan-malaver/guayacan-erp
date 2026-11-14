// Base de datos local del celular (IndexedDB, manejada con la librería Dexie).
//
// PARA QUÉ: en el campo muchas veces no hay señal. Lo que el operario captura (posturas, pesajes, siembras...)
// se guarda aquí primero y se sube al servidor cuando vuelve la conexión (sincronizacion.service.ts).
//
// QUÉ GUARDA
// - cola:      los registros pendientes de enviar (o rechazados por el servidor, para corregirlos).
// - catalogos: copias de listas que se necesitan sin señal (lotes, productos, animales...).
import Dexie, { Table } from 'dexie';

/** Un registro capturado sin conexión, esperando subir a POST /api/v1/sincronizacion/lote/. */
export interface RegistroPendiente {
  id_cliente: string; // UUIDv7 generado en el celular: llave de la cola y garantía de que no se duplica en el servidor
  tabla: string; // tabla destino, p. ej. 'produccion.registro_postura' (debe estar permitida en backend/guayacan/captura.py)
  capturado_en: string; // fecha y hora ISO 8601 con la zona horaria del celular
  predio_id: number; // finca en la que se capturó
  datos: Record<string, unknown>; // las columnas del registro
  estado: 'pendiente' | 'rechazado';
  detalle?: unknown; // mensaje de la regla si el servidor lo rechazó
  intentos: number; // cuántas veces se ha intentado enviar
}

/** Definición de la base local. Si cambia la estructura, suba el número de version() y Dexie migra sola. */
export class BaseLocal extends Dexie {
  // El «!» le dice a TypeScript que Dexie llena estas propiedades al construir la base
  cola!: Table<RegistroPendiente, string>;
  catalogos!: Table<{ clave: string; datos: unknown; guardado_en: string }, string>;

  constructor() {
    super('guayacan'); // nombre de la base en el navegador
    this.version(1).stores({
      // El primer campo es la llave; los demás son índices para buscar rápido
      cola: 'id_cliente, estado, tabla, capturado_en',
      catalogos: 'clave',
    });
  }
}

// Instancia única que usa toda la aplicación
export const baseLocal = new BaseLocal();
