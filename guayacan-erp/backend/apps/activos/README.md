# App `activos` (ACT)

Hoja de vida de equipos, planes y órdenes de mantenimiento, uso, repuestos y depreciación.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| ACT-01 | Registrar un activo con su hoja de vida | 2 | Administrador | CRUD |
| ACT-02 | Registrar el uso de un activo | 2 | Operario de campo | CRUD |
| ACT-03 | Generar y cerrar órdenes de mantenimiento | 2 | Tareas programadas, Encargado de finca, Operario de campo | `POST /api/v1/activos/ordenes-trabajo/generar/` |
| ACT-04 | Depreciar los activos del mes | 2 | Tareas programadas, Contador | `POST /api/v1/activos/depreciar/?mes=` |
| ACT-05 | Asignar un equipo a un trabajador | 2 | Encargado de finca | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `activos.activo` | `Activo` | `/api/v1/activos/activos/` | Hoja de vida de cada equipo de la finca (camioneta, motocultor, guadañas, bombas, paneles, dron, robot). |
| `activos.plan_mantenimiento` | `PlanMantenimiento` | `/api/v1/activos/planes-mantenimiento/` | Mantenimiento por horas de uso, kilómetros o días (cambio de aceite, afilado, revisión de la bomba). |
| `activos.orden_trabajo` | `OrdenTrabajo` | `/api/v1/activos/ordenes-trabajo/` | Orden de mantenimiento: la crea sola la regla al vencer el plan y se asigna como tarea; descuenta repuestos del inventario. |
| `activos.repuesto_orden` | `RepuestoOrden` | `/api/v1/activos/ordenes-trabajo/{id}/repuestos/` | Repuesto usado en una orden de trabajo (sale del kardex). |
| `activos.uso_activo` | `UsoActivo` | `/api/v1/activos/usos-activo/` | Uso de un equipo: horas, kilómetros y combustible, cargados al centro de costo que lo usó. |
| `activos.depreciacion` | `Depreciacion` | `/api/v1/activos/depreciaciones/` | Depreciación mensual de cada activo (alimenta la contabilidad y el costo por línea). |

## Reglas de la base que protegen esta app

- `activos.cerrar_orden()`
- `activos.depreciar_mes()`
- `activos.generar_ordenes_trabajo()`
- `activos.sumar_uso()`

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
