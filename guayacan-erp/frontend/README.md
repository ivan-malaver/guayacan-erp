# Frontend · Angular PWA

Una sola aplicación para el campo (celular, sin conexión) y el panel administrativo. Angular 20 con componentes
independientes, señales, detección de cambios sin zone.js, service worker e IndexedDB (Dexie).

## Arranque

```
cd frontend
npm install          (la primera vez; después suba package-lock.json y use npm ci)
npm start            (http://localhost:4200; /api va al backend por proxy.conf.json)
npm test
npm run build        (producción, con service worker)
```

## Estructura

| Carpeta | Qué tiene |
| --- | --- |
| `src/app/core/auth/` | Sesión (token en memoria, refresco guardado), interceptor que agrega `Authorization` y `X-Predio`, guardia, pantalla de ingreso |
| `src/app/core/finca/` | Finca actual y selector (NUC-03) |
| `src/app/core/offline/` | `uuidv7.ts`, cola en IndexedDB (`cola.db.ts`) y `SincronizacionService` (NUC-05) |
| `src/app/core/errores/` | Mensaje para la persona a partir de la respuesta de la API |
| `src/app/features/<módulo>/` | Un módulo perezoso por esquema (26, incluida adopción), generado desde el catálogo de casos de uso |
| `src/app/shared/` | Inicio, página provisional de módulo y lista de módulos |

## Capturar sin conexión

```ts
const sync = inject(SincronizacionService);
await sync.capturar('produccion.registro_postura', { lote_animal: 12, fecha: '2026-10-28', huevos_buenos: 410 });
```

El registro queda en la cola con su UUIDv7 y sube solo cuando hay señal. Si la base lo rechaza, queda marcado con
el mensaje de la regla para que la persona lo corrija. Solo se pueden capturar así las tablas de
`backend/guayacan/captura.py`.

## Convenciones

- Pantallas de campo: botones de 48 px o más, una tarea por pantalla, funcionan con una mano y con guantes.
- Textos en español de Colombia con los términos de la finca.
- Cada pantalla nueva nombra su caso de uso en un comentario y en el nombre de la rama.
- Las versiones de `package.json` son mínimas; la primera instalación fija las exactas en `package-lock.json`.
- Los archivos `.json` de configuración no admiten comentarios; están explicados en `docs/desarrollo/04_archivos_de_configuracion.md`.
