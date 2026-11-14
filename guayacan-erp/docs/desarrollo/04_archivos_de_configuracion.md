# Archivos de configuración explicados

El formato JSON no admite comentarios (un `//` rompe el archivo), por eso los JSON del proyecto se explican aquí.
Los demás archivos de configuración (`.yml`, `.toml`, `Dockerfile`, `.env.ejemplo`, `.gitignore`) llevan sus
comentarios dentro. Excepción: `.vscode/*.json` sí los admite porque VS Code usa un JSON ampliado (JSONC).

## Raíz del repositorio

| Archivo | Para qué sirve |
| --- | --- |
| `.gitignore` | Lo que Git no sube: `.env`, entornos virtuales, `node_modules`, bases locales, compilados, `entregables/` |
| `.gitattributes` | Guarda todos los textos con fin de línea LF (los `.sql` y `.sh` fallan con CRLF de Windows) |
| `.env.ejemplo` | Plantilla de variables de entorno; se copia como `.env` (que nunca se sube) |
| `docker-compose.yml` | Contenedores de desarrollo: PostgreSQL, MongoDB, Redis y, con perfiles, la app y el puente IoT |
| `.github/workflows/ci.yml` | Integración continua: pruebas de la base, backend, servicios y frontend en cada cambio |
| `scripts/cargar_base.ps1` / `.sh` | Carga la base y corre las 339 pruebas de reglas |
| `.vscode/settings.json` | Intérprete de Python del backend, pytest, Ruff, finales de línea y carpetas ocultas |
| `.vscode/extensions.json` | Extensiones que VS Code recomienda instalar al abrir el proyecto |
| `huellas.json` + `verificar.py` | Huella SHA-256 de cada archivo del paquete para comprobar que nada se dañó al copiar |

## Backend y servicios (Python)

| Archivo | Para qué sirve |
| --- | --- |
| `backend/pyproject.toml` | Librerías del backend, configuración de pytest y Ruff (comentado línea por línea) |
| `backend/config/settings/base.py`, `dev.py`, `test.py`, `prod.py` | Ajustes de Django comunes y por entorno |
| `servicios/*/pyproject.toml` | Librerías de cada servicio FastAPI |

## Frontend (Angular)

### `package.json`

Describe el proyecto de Node: nombre, comandos y librerías.

| Parte | Explicación |
| --- | --- |
| `scripts.start` | `ng serve --proxy-config proxy.conf.json`: servidor de desarrollo en el puerto 4200 que reenvía `/api` a Django |
| `scripts.build` | `ng build`: compila la versión de producción en `dist/` |
| `scripts.test` | `ng test --watch=false --browsers=ChromeHeadless`: corre las pruebas una vez en Chrome sin ventana |
| `dependencies` | Lo que va dentro de la app: Angular (`core`, `common`, `router`, `forms`, `service-worker`), Angular Material y CDK (componentes visuales), Dexie (IndexedDB), RxJS (flujos de datos) y tslib |
| `devDependencies` | Solo para programar: CLI y compilador de Angular, TypeScript, Karma y Jasmine (pruebas) |
| `^20.3.0` | «20.3.0 o cualquier 20.x más nueva»; `~7.8.1` es «7.8.x más nueva». Las exactas quedan en `package-lock.json` |

### `angular.json`

Configuración del espacio de trabajo de Angular.

| Clave | Explicación |
| --- | --- |
| `prefix: "gy"` | Prefijo de las etiquetas de los componentes (`gy-raiz`, `gy-inicio`...) |
| `build.options.browser` | Archivo de arranque: `src/main.ts` |
| `build.options.assets` | Copia tal cual la carpeta `public/` (íconos y manifiesto) |
| `build.options.serviceWorker` | Activa el service worker de la PWA con las reglas de `ngsw-config.json` |
| `configurations.production.budgets` | Límites de tamaño: avisa si el código inicial pasa de 600 kB y falla si pasa de 1,2 MB (importa en celulares con mala señal) |
| `outputHashing: "all"` | Pone una huella en el nombre de cada archivo compilado para que el navegador no use versiones viejas |
| `configurations.development.fileReplacements` | En desarrollo cambia `environment.ts` por `environment.development.ts` |
| `serve.defaultConfiguration` | `npm start` usa la configuración de desarrollo |
| `test.builder` | Pruebas con Karma |

### `tsconfig.json`, `tsconfig.app.json`, `tsconfig.spec.json`

Opciones del compilador de TypeScript.

| Opción | Explicación |
| --- | --- |
| `strict: true` | Revisión estricta de tipos: detecta antes de ejecutar errores como usar algo que puede ser `null` |
| `noImplicitReturns`, `noFallthroughCasesInSwitch` | Exige que toda función devuelva valor en todos sus caminos y que cada `case` termine |
| `noPropertyAccessFromIndexSignature` | Obliga a escribir `obj['clave']` para propiedades dinámicas, así se notan |
| `target: "ES2022"` | Versión de JavaScript que se genera (la entienden los navegadores actuales) |
| `angularCompilerOptions.strictTemplates` | Revisa los tipos también dentro de las plantillas HTML |
| `tsconfig.app.json` | Compila `src/**/*.ts` sin las pruebas |
| `tsconfig.spec.json` | Compila solo las pruebas (`*.spec.ts`) con los tipos de Jasmine |

### `ngsw-config.json` (service worker)

Qué guarda la PWA en el celular para abrir sin internet.

| Grupo | Explicación |
| --- | --- |
| `assetGroups.app` (`prefetch`) | Descarga al instalar: `index.html`, manifiesto, `.js` y `.css`. La app abre aunque no haya señal |
| `assetGroups.recursos` (`lazy`) | Imágenes y fuentes: se guardan la primera vez que se usan |
| `dataGroups.catalogos` | Respuestas de la API de productos, zonas, especies y fincas. Estrategia `freshness`: intenta la red y, si no responde en 4 segundos, usa la copia guardada (máximo 7 días y 200 respuestas) |

Las capturas de campo no pasan por aquí: van a la cola de IndexedDB (`core/offline`).

### `proxy.conf.json`

En desarrollo, todo lo que empiece por `/api` lo reenvía a `http://localhost:8000` (Django). Así el navegador cree
que todo viene del mismo sitio y no hay que configurar CORS para el puerto 4200. `changeOrigin` cambia la cabecera
Host para que Django acepte la petición.

### `public/manifest.webmanifest`

Lo que el celular usa al «instalar» la PWA: nombre largo y corto, idioma `es-CO`, dirección de inicio, modo
`standalone` (se abre sin barra del navegador, como una app), colores y los íconos de 192 y 512 px (`maskable`
permite que Android recorte el ícono en círculo).

## Cómo leer los archivos SQL

| Archivo | Cómo está documentado |
| --- | --- |
| `specs/modelo-datos/esquema_postgresql.sql` | Generado: no se edita a mano. Cada esquema, tabla y columna lleva su `comment on ... is '...'` (más de 3.300), así la explicación queda guardada dentro de la base. En psql, `\d+ produccion.lote_animal` la muestra; en VS Code, la extensión de PostgreSQL también |
| `specs/modelo-datos/generador/reglas_negocio.sql` | Las reglas escritas a mano (funciones y disparadores), con un comentario por bloque que dice qué regla cumple. Se copia dentro del esquema al generarlo |
| `specs/modelo-datos/apendice_a_adopcion.sql` | Encabezado con el modelo de negocio, secciones numeradas y `comment on` en sus tablas |
| `specs/casos-prueba/*.sql` | Cada prueba lleva su nombre en español (`prueba.ok(condición, 'qué se comprueba')`); al correrla, cada línea `OK` dice qué regla pasó y una `FALLA` dice cuál se rompió |
| `backend/sql/preparar_api.sql` | Comentado paso a paso: usuario de la API, permisos y esquema `django` |

Para modificar una tabla: cambie `modelo.py` (o `modelo_apendice_a.py`), regenere con `generar.py` y vuelva a correr
las pruebas (ver `03_regenerar_y_mantener.md`). Nunca edite el esquema generado directamente.
