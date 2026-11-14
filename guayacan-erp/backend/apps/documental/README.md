# App `documental` (DOC)

Documentos con versiones, aprobación, vencimiento y vínculos; los agentes solo leen la versión aprobada y vigente.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| DOC-01 | Publicar un documento con versión aprobada | 1 | Encargado de finca, Administrador | CRUD |
| DOC-02 | Vincular documentos y vigilar vencimientos | 1 | Tareas programadas, Encargado de finca | `GET /api/v1/documental/vigentes/` |
| DOC-03 | Consultar documentos vigentes | 1 | Usuario autenticado | `GET /api/v1/documental/vigentes/` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `documental.documento` | `Documento` | `/api/v1/documental/documentos/` | Papel que la finca no puede perder: permisos, registros ICA, RUT, contratos, protocolos, manuales, evidencias. Con datos personales sigue la Ley 1581. |
| `documental.version_documento` | `VersionDocumento` | `/api/v1/documental/documentos/{id}/versiones/` | Versión de un documento con su archivo, huella, aprobación y vigencia; solo una aprobada vigente a la vez. |
| `documental.vinculo_documento` | `VinculoDocumento` | `/api/v1/documental/vinculos-documento/` | Une un documento con cualquier registro (un lote, una póliza, un activo, una no conformidad). |

## Reglas de la base que protegen esta app

- `documental.documento_para_agente()`
- `documental.obsoletar_anteriores()`
- `documental.v_vigentes`
- `documental.validar_version()`

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
