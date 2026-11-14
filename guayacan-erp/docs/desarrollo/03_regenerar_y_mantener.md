# Regenerar modelos, diagramas y trazabilidad

Todo lo generado sale de tres fuentes: `specs/modelo-datos/generador/modelo.py` (tablas v5),
`specs/modelo-datos/generador/modelo_apendice_a.py` (las 8 tablas del Apéndice A, adopción) y
`docs/uml/fuentes/catalogo.py` (actores, requerimientos y los 192 casos de uso, incluidos ADO-01 a ADO-15).

| Si cambia… | Ejecute (desde la raíz del repositorio) | Qué se actualiza |
| --- | --- | --- |
| Una tabla o columna | `python specs/modelo-datos/generador/generar.py .` y luego `python -I docs/uml/fuentes/gen_apps.py specs/modelo-datos/generador docs/uml/fuentes generado/apps_nuevas` | Esquema SQL, diccionario y, en `generado/apps_nuevas`, los `models.py` nuevos: copie solo `models.py` a cada app |
| Una regla de negocio | Edite `reglas_negocio.sql`, regenere el esquema y corra las tres baterías de pruebas (`scripts/cargar_base.ps1 -Pruebas`) | Esquema SQL |
| Un caso de uso | Edite `catalogo.py`, luego `gen_casos_uso.py`, `python -I docs/uml/fuentes/gen_frontend.py docs/uml/fuentes frontend` y la pestaña del documento técnico | Diagramas de casos de uso, rutas de Angular, README de la app |
| Un diagrama de clases | `python -I docs/uml/fuentes/gen_estructura.py specs/modelo-datos/generador docs/uml` | `docs/uml/clases/` y `docs/uml/paquetes/` |
| Secuencias, estados o actividades | Edite y ejecute `gen_comportamiento.py docs/uml` | `docs/uml/secuencia`, `estados`, `actividad` |

Los diagramas necesitan Graphviz (`dot`) y Mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`).

**No regenere completa una app que ya empezó a construir**: `services.py`, `urls.py` y las pruebas generadas son un
punto de partida; después de editarlos son suyos.
