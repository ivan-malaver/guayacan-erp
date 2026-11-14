# Informe de verificación del paquete v5.2 final (31 de octubre de 2026)

| Comprobación | Resultado |
| --- | --- |
| Pruebas de reglas en la base (PostgreSQL 16 de prueba, con `scripts/cargar_base.sh --pruebas`) | 339 de 339: v5 (215), regresión v4 (90) y Apéndice A (34), cada batería en una base nueva |
| Carga de la base de trabajo con el script | Esquema + datos + Apéndice A + `preparar_api.sql`; el usuario `guayacan_api` ve las 254 tablas |
| Python (backend, servicios, generadores) | Todo compila; `ruff check` sin errores en backend, agentes e IoT |
| Comentarios | Los cambios de comentarios no alteraron el código: se comparó el árbol sintáctico (AST) antes y después |
| TypeScript (45 archivos del frontend) | Sin errores de sintaxis |
| JSON, YAML y TOML | Válidos (package.json, angular.json, tsconfig, ngsw-config, manifest, docker-compose, ci.yml, pyproject) |
| Coherencia entre capas | 26 módulos iguales en el catálogo, los esquemas SQL, `ESQUEMAS` de Django, `backend/apps` y `frontend/features` |
| Manuales | Diccionario, mapa de APIs, trazabilidad y Word regenerados con los valores permitidos correctos del Apéndice A |
| Integridad | `huellas.json` con la huella SHA-256 de cada archivo; `python verificar.py` la comprueba |

## Lo que falta comprobar en su PC (o en la CI de GitHub)

El entorno donde se armó el paquete no tiene acceso a PyPI ni a npm, así que no se pudieron instalar las librerías.
Por eso quedan pendientes, y son lo primero que hará al seguir `INSTALAR.md`:

1. `pip install -e ".[dev]"`, `python manage.py check`, `python manage.py migrate --database=admin` y `pytest`.
2. `npm install`, `npm run build` y `npm test`.
3. La base en PostgreSQL 18 con PostGIS (aquí se probó en PostgreSQL 16 con una versión equivalente del esquema).

Si algo falla en esos pasos, copie el mensaje completo del error: casi siempre indica el archivo y la línea.
