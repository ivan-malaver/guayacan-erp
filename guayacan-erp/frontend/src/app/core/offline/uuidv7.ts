// Generador de UUIDv7 (norma RFC 9562).
//
// QUÉ ES: un identificador único de 128 bits que se puede crear en el celular SIN preguntarle al servidor.
// Los primeros 48 bits son la hora en milisegundos y el resto es aleatorio. Por eso:
// - Es único: dos celulares nunca generan el mismo (la parte aleatoria lo hace prácticamente imposible).
// - Es ordenable por tiempo: los más nuevos quedan después (bueno para los índices de PostgreSQL).
// La base lo guarda en la columna id_cliente de las tablas con captura sin conexión y así no hay duplicados.
//
// Formato de salida: xxxxxxxx-xxxx-7xxx-[89ab]xxx-xxxxxxxxxxxx (hexadecimal).
export function uuidv7(ahora: number = Date.now()): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes); // 16 bytes aleatorios seguros del navegador
  // Se escriben los 6 primeros bytes con los milisegundos (de derecha a izquierda)
  let ms = ahora;
  for (let i = 5; i >= 0; i--) {
    bytes[i] = ms % 256;
    ms = Math.floor(ms / 256);
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x70; // marca la versión 7 en el byte 6
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // marca la variante RFC 4122 en el byte 8
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
