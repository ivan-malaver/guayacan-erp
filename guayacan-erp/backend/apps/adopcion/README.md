# App `adopcion` (ADO)

Adopción de árboles y animales: catálogo, sitios, bienes, contratos de compra y cuidado, cuotas, seguimiento, liquidaciones y saldo del adoptante.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| ADO-01 | Configurar catálogo y sitios | 3 · `adopcion` | Administrador | CRUD |
| ADO-02 | Comprar un árbol o un animal | 3 · `adopcion` | Adoptante | CRUD |
| ADO-03 | Sembrar en persona | 3 · `adopcion` | Adoptante | `POST /api/v1/adopcion/bienes/{id}/siembra/` |
| ADO-04 | Sembrar por un trabajador y enviar el video | 3 · `adopcion` | Operario de campo | `POST /api/v1/adopcion/bienes/{id}/siembra/` |
| ADO-05 | Cobrar y pagar la cuota mensual | 3 · `adopcion` | Tareas programadas | `POST /api/v1/adopcion/cuotas/{id}/pagar/` |
| ADO-06 | Seguir mi árbol o mi animal | 3 · `adopcion` | Adoptante | `GET /api/v1/adopcion/mis-bienes/`<br>`GET /api/v1/adopcion/mis-bienes/{id}/seguimiento/` |
| ADO-07 | Detectar abandono y poner en readopción | 3 · `adopcion` | Tareas programadas | `POST /api/v1/adopcion/seguimientos/{id}/marcar-enviado/` |
| ADO-08 | Readoptar | 3 · `adopcion` | Adoptante | CRUD |
| ADO-09 | Registrar y vender productos del bien | 3 · `adopcion` | Operario de campo | CRUD |
| ADO-10 | Liquidar productos con el 5 % | 3 · `adopcion` | Administrador | `POST /api/v1/adopcion/liquidaciones/{id}/aprobar/`<br>`POST /api/v1/adopcion/adoptantes/{id}/pagar-saldo/` |
| ADO-11 | Decidir en la madurez: mantener o liquidar | 3 · `adopcion` | Adoptante | `POST /api/v1/adopcion/contratos/{id}/decision/` |
| ADO-12 | Talar o sacrificar y liquidar | 3 · `adopcion` | Administrador | CRUD |
| ADO-13 | Reponer un bien muerto en garantía | 3 · `adopcion` | Encargado de finca | `POST /api/v1/adopcion/bienes/{id}/muerte/` |
| ADO-14 | Ceder o regalar la adopción | 3 · `adopcion` | Adoptante | `POST /api/v1/adopcion/contratos/{id}/ceder/` |
| ADO-15 | Consultar el tablero de adopción | 3 · `adopcion` | Familia | `GET /api/v1/adopcion/tablero/` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `adopcion.plan` | `Plan` | `/api/v1/adopcion/planes/` | Catálogo de lo que se puede adoptar, con precio de compra y de readopción, cuota mensual, costos estimados (para el margen), meses de madurez, garantía y permiso que exige su liquidación. |
| `adopcion.sitio` | `Sitio` | `/api/v1/adopcion/sitios/` | Lugar asignado por la administración: hoyo de siembra en un lote o cupo en corral o galpón, con coordenadas. |
| `adopcion.bien` | `Bien` | `/api/v1/adopcion/bienes/` | El árbol o el animal concreto que se vende, con su código, sitio, estado de vida y el bien al que reemplaza si fue repuesto en garantía. |
| `adopcion.contrato` | `Contrato` | `/api/v1/adopcion/contratos/` | Compraventa del bien más servicio de cuidado mensual. Un bien vivo tiene a lo sumo un contrato activo; guarda la modalidad de siembra y la decisión en la madurez. |
| `adopcion.cuota` | `Cuota` | `/api/v1/adopcion/cuotas/` | Cuota mensual de cuidado; vence el día 10, se paga por la pasarela o se compensa con el saldo a favor del adoptante. |
| `adopcion.seguimiento` | `Seguimiento` | `/api/v1/adopcion/seguimientos/` | Bitácora que ve el adoptante: siembra, video, fotos, visitas, sanidad, mediciones, muerte, reposición y avisos de mora. Se captura sin conexión. |
| `adopcion.liquidacion` | `Liquidacion` | `/api/v1/adopcion/liquidaciones/` | Venta de productos o liquidación final (tala, sacrificio, venta en pie): ingresos menos gastos = utilidad neta; la finca cobra el % de administración solo si hay utilidad. |
| `adopcion.movimiento_saldo` | `MovimientoSaldo` | `/api/v1/adopcion/movimientos-saldo/` | Cuenta del adoptante, solo inserción: abonos de liquidaciones, cuotas compensadas y pagos al adoptante. No genera intereses ni se invierte. |

## Reglas de la base que protegen esta app

- `adopcion.aplicar_liquidacion()`
- `adopcion.compensar_cuotas()`
- `adopcion.generar_cuotas()`
- `adopcion.marcar_abandono()`
- `adopcion.marcar_madurez()`
- `adopcion.registrar_muerte()`
- `adopcion.registrar_siembra()`
- `adopcion.saldo()`
- `adopcion.v_tablero`
- `adopcion.validar_contrato()`
- `adopcion.validar_liquidacion()`
- `comercial.preparar_factura()`
- `nucleo.exigir_funcion()`
- `redes.verificar_envio()`

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
