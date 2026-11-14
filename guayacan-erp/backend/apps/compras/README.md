# App `compras` (CMP)

Órdenes de compra, cotizaciones de proveedores y precios de mercado de referencia.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| CMP-01 | Registrar cotizaciones y precios de mercado | 1 | Administrador | CRUD |
| CMP-02 | Crear y aprobar una orden de compra | 1 | Administrador | `POST /api/v1/compras/ordenes-compra/{id}/aprobar/` |
| CMP-03 | Recibir una compra en bodega | 1 | Operario de campo | `POST /api/v1/compras/ordenes-compra/{id}/recibir/` |
| CMP-04 | Emitir un documento soporte electrónico | 1 | Contador | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `compras.orden_compra` | `OrdenCompra` | `/api/v1/compras/ordenes-compra/` | Compra a un proveedor. |
| `compras.orden_compra_detalle` | `OrdenCompraDetalle` | `/api/v1/compras/ordenes-compra/{id}/lineas/` | Línea de la orden de compra. |
| `compras.cotizacion_proveedor` | `CotizacionProveedor` | `/api/v1/compras/cotizaciones-proveedor/` | Precio ofrecido por un proveedor para un insumo, registrado por una persona o por el agente de mercados. |
| `compras.precio_mercado` | `PrecioMercado` | `/api/v1/compras/precios-mercado/` | Precio de referencia de un producto en un mercado (SIPSA-DANE, Corabastos, Fenavi), usado por el agente analista. |
| `compras.documento_soporte` | `DocumentoSoporte` | `/api/v1/compras/documentos-soporte/` | Documento soporte electrónico de la DIAN para compras a quien no factura (campesinos, permutas). |

## Reglas de la base que protegen esta app

- `inventario.entrada_inicial()`

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
