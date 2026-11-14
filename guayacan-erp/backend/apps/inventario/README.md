# App `inventario` (INV)

Catálogo de productos, bodegas, lotes de inventario y kardex de movimientos.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| INV-01 | Gestionar productos, unidades y bodegas | 1 | Administrador | CRUD |
| INV-02 | Recibir un lote en bodega y etiquetarlo | 1 | Operario de campo | CRUD |
| INV-03 | Escanear un código y pesar con báscula | 1 | Operario de campo, Vendedor | CRUD |
| INV-04 | Registrar merma, ajuste o traslado | 1 | Operario de campo, Encargado de finca | CRUD |
| INV-05 | Hacer un conteo físico | 1 | Operario de campo, Encargado de finca | CRUD |
| INV-06 | Vigilar vencimientos y liquidar | 1 | Tareas programadas, Vendedor | `GET /api/v1/inventario/alertas-vencimiento/` |
| INV-07 | Vigilar la cadena de frío y decidir sobre un lote bloqueado | 2 · `cadena_frio_finca` | Encargado de finca | `POST /api/v1/inventario/bloqueos-lote/{id}/decidir/` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `inventario.unidad_medida` | `UnidadMedida` | `/api/v1/inventario/unidades-medida/` | Unidades (kg, cubeta, unidad, bulto, litro) y su conversión a la unidad base. |
| `inventario.categoria_producto` | `CategoriaProducto` | `/api/v1/inventario/categorias-producto/` | Agrupación jerárquica de productos (huevo, carne en pie, granos, insumos, medicamentos). |
| `inventario.producto` | `Producto` | `/api/v1/inventario/productos/` | Todo lo que se vende, se compra o se produce: cubeta de huevo, kg de tilapia, bulto de concentrado. |
| `inventario.bodega` | `Bodega` | `/api/v1/inventario/bodegas/` | Lugar físico donde se guarda inventario. |
| `inventario.lote_inventario` | `LoteInventario` | `/api/v1/inventario/lotes-inventario/` | Existencia concreta de un producto con fecha, origen y vencimiento. Sus cantidades solo las cambia el kardex (movimiento_inventario); la salida sigue el orden FEFO: primero lo que vence primero. |
| `inventario.movimiento_inventario` | `MovimientoInventario` | `/api/v1/inventario/movimientos-inventario/` | Kardex: cada entrada, salida, ajuste, traslado o merma, con el documento que lo causó. |
| `inventario.etiqueta` | `Etiqueta` | `/api/v1/inventario/etiquetas/` | Código de barras o QR impreso para un lote. Interno (Code 128 o QR) o GS1-128 si la finca obtiene códigos GS1. |
| `inventario.lectura_codigo` | `LecturaCodigo` | `/api/v1/inventario/lecturas-codigo/` | Cada escaneo de un código: qué se leyó, con qué equipo, para qué y qué resultado tuvo. |
| `inventario.pesaje` | `Pesaje` | `/api/v1/inventario/pesajes/` | Lectura de una báscula digital, automática o digitada, con tara y estabilidad. |
| `inventario.conteo_fisico` | `ConteoFisico` | `/api/v1/inventario/conteos/` | Inventario físico de una bodega: se escanea lo que hay y se compara con el sistema. |
| `inventario.conteo_detalle` | `ConteoDetalle` | `/api/v1/inventario/conteos/{id}/detalles/` | Resultado del conteo por lote. |
| `inventario.vehiculo` | `Vehiculo` | `/api/v1/inventario/vehiculos/` | Vehículo de entregas (camioneta, motocarro) y su registrador de temperatura. |
| `inventario.excursion_temperatura` | `ExcursionTemperatura` | `/api/v1/inventario/excursiones-temperatura/` | Periodo en que una nevera o un vehículo estuvo fuera de su rango de temperatura; si supera la tolerancia, bloquea los lotes perecederos. |
| `inventario.bloqueo_lote` | `BloqueoLote` | `/api/v1/inventario/bloqueos-lote/` | Bloqueo de un lote y su decisión: lo pone una regla o una persona; liberarlo o descartarlo siempre lo decide una persona. |

## Reglas de la base que protegen esta app

- `inventario.aplicar_bloqueo()`
- `inventario.aplicar_movimiento()`
- `inventario.entrada_inicial()`
- `inventario.estimar_vencimiento()`
- `inventario.evaluar_excursion()`
- `inventario.marcar_vencidos()`
- `inventario.proteger_cantidades()`
- `inventario.v_alertas_vencimiento`
- `peso no estable no vende`

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
