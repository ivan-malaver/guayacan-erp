# App `seguros` (SGR)

Pólizas, bienes asegurados, índices de seguros paramétricos y avisos de siniestro con evidencia.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| SGR-01 | Registrar una póliza y sus bienes asegurados | 2 | Administrador | CRUD |
| SGR-02 | Avisar pólizas próximas a vencer | 2 | Tareas programadas | CRUD |
| SGR-03 | Registrar y enviar un aviso de siniestro | 2 | Encargado de finca, Administrador | CRUD |
| SGR-04 | Vigilar el índice de una póliza paramétrica | 2 · `seguro_parametrico` | Tareas programadas | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `seguros.poliza` | `Poliza` | `/api/v1/seguros/polizas/` | Póliza (cultivo, animales, equipos, responsabilidad civil del dron, paramétrico) con vigencia, prima, suma asegurada e incentivo de Finagro. |
| `seguros.bien_asegurado` | `BienAsegurado` | `/api/v1/seguros/bienes-asegurados/` | Lo que cubre la póliza: un activo, una siembra, un lote de animales o una zona. |
| `seguros.indice_poliza` | `IndicePoliza` | `/api/v1/seguros/indices-poliza/` | Regla del índice de un seguro paramétrico; la decide la aseguradora con su fuente, no los sensores de la finca. |
| `seguros.aviso_siniestro` | `AvisoSiniestro` | `/api/v1/seguros/avisos-siniestro/` | Aviso de posible siniestro con la serie de datos como evidencia. No hay reclamación automática: una persona lo revisa y lo envía. |

## Reglas de la base que protegen esta app

- `seguros.preparar_poliza()`
- `seguros.v_por_vencer`
- `seguros.validar_aviso()`
- `seguros.vigilar_indice()`

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
