# App `comercial` (VTA)

Precios con vigencia, propuestas de precio, pedidos, facturas, pagos y entregas.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| VTA-01 | Gestionar listas y precios con vigencia | 1 | Administrador | CRUD |
| VTA-02 | Proponer y aprobar un cambio de precio | 1 | Administrador | `POST /api/v1/comercial/propuestas-precio/{id}/aprobar/` |
| VTA-03 | Tomar y confirmar un pedido | 1 | Vendedor, Cliente | `POST /api/v1/comercial/pedidos/{id}/confirmar/` |
| VTA-04 | Vender en la finca o en la feria sin conexión | 2 | Vendedor | CRUD |
| VTA-05 | Despachar y entregar un pedido | 1 | Operario de campo, Vendedor | `POST /api/v1/comercial/pedidos/{id}/despachar/` |
| VTA-06 | Facturar electrónicamente | 1 | Tareas programadas | `POST /api/v1/comercial/pedidos/{id}/facturar/` |
| VTA-07 | Registrar y confirmar un pago | 1 | Vendedor, Contador | `POST /api/v1/comercial/pagos/{id}/confirmar/`<br>`POST /api/v1/pagos/webhook/` |
| VTA-08 | Vender a crédito y controlar la cartera | 2 · `venta_credito` | Contador, Vendedor | `GET /api/v1/comercial/cartera/` |
| VTA-09 | Generar pedidos recurrentes | 2 · `pedidos_recurrentes` | Tareas programadas, Vendedor | CRUD |
| VTA-10 | Registrar una permuta | 2 · `permuta` | Contador | CRUD |
| VTA-11 | Consultar la trazabilidad de un lote | 1 | Cliente, Administrador | `GET /api/v1/publico/trazabilidad/{codigo}/` |
| VTA-12 | Retirar un lote del mercado | 1 | Administrador | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `comercial.lista_precios` | `ListaPrecios` | `/api/v1/comercial/listas-precios/` | Lista de precios por canal o tipo de cliente (público, tiendas, restaurantes, mayoristas). |
| `comercial.precio_producto` | `PrecioProducto` | `/api/v1/comercial/precios-producto/` | Precio de un producto en una lista, con vigencia. Nunca se edita un precio: se cierra el vigente y se crea uno nuevo, así el historial queda completo. |
| `comercial.propuesta_precio` | `PropuestaPrecio` | `/api/v1/comercial/propuestas-precio/` | Cambio de precio sugerido por el agente analista de mercados. Solo se aplica cuando el administrador lo aprueba. |
| `comercial.pedido` | `Pedido` | `/api/v1/comercial/pedidos/` | Solicitud de compra de un cliente por cualquier canal; puede crearla una persona o un agente. |
| `comercial.pedido_detalle` | `PedidoDetalle` | `/api/v1/comercial/pedidos/{id}/lineas/` | Línea del pedido. El precio queda congelado al confirmar: un cambio de precio posterior no la afecta. |
| `comercial.factura` | `Factura` | `/api/v1/comercial/facturas/` | Factura electrónica (o documento equivalente) generada por regla fija, no por la IA, y validada por la DIAN. |
| `comercial.pago` | `Pago` | `/api/v1/comercial/pagos/` | Dinero recibido por un pedido o factura. |
| `comercial.entrega` | `Entrega` | `/api/v1/comercial/entregas/` | Despacho de un pedido. |
| `comercial.reserva_lote` | `ReservaLote` | `/api/v1/comercial/reservas-lote/` | Qué lotes se reservaron para cada línea de pedido, escogidos en orden FEFO; una línea puede tomar de varios lotes. |
| `comercial.retiro_lote` | `RetiroLote` | `/api/v1/comercial/retiros-lote/` | Retiro de un lote del mercado (recall): se bloquea el lote y se avisa a cada cliente que lo recibió. |
| `comercial.retiro_aviso` | `RetiroAviso` | `/api/v1/comercial/retiros-aviso/` | Cliente que recibió un lote retirado: cuánto recibió, cuándo se le avisó y cuánto devolvió. |
| `comercial.pedido_recurrente` | `PedidoRecurrente` | `/api/v1/comercial/pedidos-recurrente/` | Pedido que se repite (tienda, restaurante, hotel); cada día la tarea crea en borrador los que tocan para que un vendedor los confirme. |
| `comercial.pedido_recurrente_detalle` | `PedidoRecurrenteDetalle` | `/api/v1/comercial/pedidos-recurrente-detalle/` | Productos y cantidades del pedido recurrente. |
| `comercial.permuta` | `Permuta` | `/api/v1/comercial/permutas/` | Trueque formal: una venta (factura) y una compra (documento soporte) que se compensan; requiere la función permuta activa. El pago con mano de obra no se admite. |
| `comercial.huella_trazabilidad` | `HuellaTrazabilidad` | `/api/v1/comercial/huellas-trazabilidad/` | Cadena de huellas SHA-256 de los hechos de trazabilidad de los lotes: cada huella incluye la anterior, así cualquier alteración se detecta. Lista para anclarse en una red blockchain si un comprador lo exige. |

## Reglas de la base que protegen esta app

- `comercial.abrir_retiro()`
- `comercial.actualizar_mora()`
- `comercial.aplicar_pago()`
- `comercial.aplicar_permuta()`
- `comercial.aplicar_propuesta_precio()`
- `comercial.confirmar_pedido()`
- `comercial.despachar_pedido()`
- `comercial.generar_pedidos_recurrentes()`
- `comercial.preparar_factura()`
- `comercial.v_cartera`
- `comercial.v_trazabilidad_lote`
- `comercial.verificar_cadena_huellas()`
- `inventario.puede_venderse()`
- `inventario.reservar_fefo()`
- `precio nunca se edita: se cierra y se crea`
- `regla fija, no IA`
- `un agente no confirma pagos`

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
