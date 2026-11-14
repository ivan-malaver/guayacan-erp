# App `cumplimiento` (CUM)

Normas (granja avícola biosegura, BPA, GLOBALG.A.P.), requisitos, expediente, evidencias, auditorías y acciones correctivas.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| CUM-01 | Cargar normas y requisitos | 1 | Administrador | CRUD |
| CUM-02 | Abrir un expediente de cumplimiento | 1 | Administrador | CRUD |
| CUM-03 | Evaluar el expediente contra su evidencia | 1 | Tareas programadas | `POST /api/v1/cumplimiento/expedientes/{id}/evaluar/` |
| CUM-04 | Adjuntar evidencias a un requisito | 1 | Encargado de finca | CRUD |
| CUM-05 | Registrar una auditoría externa y sus no conformidades | 2 | Administrador | `GET /api/v1/cumplimiento/expedientes/{id}/paquete-auditor/` |
| CUM-06 | Ejecutar y verificar acciones correctivas | 2 | Encargado de finca, Administrador | CRUD |
| CUM-07 | Vigilar la obligación de granja avícola biosegura | 1 | Tareas programadas, Administrador | `GET /api/v1/cumplimiento/granja-biosegura/` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `cumplimiento.norma` | `Norma` | `/api/v1/cumplimiento/normas/` | Norma o certificación (granja avícola biosegura ICA 3651/2014, BPA ICA 30021/2017, GLOBALG.A.P. IFA v6). Catálogo compartido. |
| `cumplimiento.requisito` | `Requisito` | `/api/v1/cumplimiento/requisitos/` | Requisito de una norma con el tipo de evidencia y, si aplica, la regla que la revisa sola. |
| `cumplimiento.expediente` | `Expediente` | `/api/v1/cumplimiento/expedientes/` | Expediente de la finca ante una norma (incluye el registro sanitario de predio avícola, RSPA). |
| `cumplimiento.evaluacion_requisito` | `EvaluacionRequisito` | `/api/v1/cumplimiento/evaluaciones-requisito/` | Estado de cada requisito en el expediente. Con evidencia vencida pasa solo a no cumple. |
| `cumplimiento.evidencia_requisito` | `EvidenciaRequisito` | `/api/v1/cumplimiento/evidencias-requisito/` | Prueba de un requisito: un documento o un registro del sistema, con su vencimiento. |
| `cumplimiento.auditoria_externa` | `AuditoriaExterna` | `/api/v1/cumplimiento/auditorias-externas/` | Auditoría interna o externa programada, con aviso previo y resultado. |
| `cumplimiento.no_conformidad` | `NoConformidad` | `/api/v1/cumplimiento/no-conformidades/` | Hallazgo; no se cierra sin acciones verificadas y sin quien verifique. |
| `cumplimiento.accion_correctiva` | `AccionCorrectiva` | `/api/v1/cumplimiento/acciones-correctivas/` | Acción para corregir una no conformidad, con responsable, plazo y verificación; se asigna como tarea. |

## Reglas de la base que protegen esta app

- `cumplimiento.cerrar_no_conformidad()`
- `cumplimiento.evaluar_expediente()`
- `cumplimiento.v_granja_biosegura`
- `cumplimiento.validar_expediente()`
- `cumplimiento.verificar_accion()`

## Archivos de esta carpeta

| Archivo | Qué hace |
| --- | --- |
| `apps.py` | Registra la app en Django |
| `models.py` | Una clase por tabla (generado; no editar) |
| `serializers.py` | Convierte filas en JSON y valida el JSON recibido |
| `views.py` | Endpoints CRUD de cada tabla |
| `urls.py` | Rutas: acciones de los casos de uso (501 mientras se construyen) y CRUD |
| `services.py` | Una función por caso de uso, vacía, con los pasos para construirla |
| `tests/test_casos_de_uso.py` | Una prueba por caso de uso, marcada como pendiente |

## Cómo trabajar aquí

1. Lea la especificación del caso de uso en el documento técnico (pestaña de su grupo) o en `docs/casos-de-uso/`.
2. Quite el `skip` de su prueba en `tests/test_casos_de_uso.py` y escriba el flujo principal y los alternos.
3. Implemente la función de `services.py`; no repita en Python las reglas que ya están en la base.
4. Reemplace la ruta `PorConstruir` de `urls.py` por la vista real.
