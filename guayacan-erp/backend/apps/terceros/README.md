# App `terceros` (TER)

Personas y empresas con las que se relaciona la finca: clientes, proveedores, empleados y su consentimiento de datos.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| TER-01 | Registrar un tercero (persona o empresa) | 1 | Vendedor, Contador, Administrador | CRUD |
| TER-02 | Registrar y revocar una autorización de datos | 1 | Cliente, Vendedor | CRUD |
| TER-03 | Atender una solicitud del titular de datos | 1 | Titular de datos | `GET /api/v1/terceros/{id}/datos-personales/` |
| TER-04 | Gestionar clientes, proveedores y empleados | 1 | Administrador, Contador, Vendedor | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `terceros.tercero` | `Tercero` | `/api/v1/terceros/terceros/` | Toda persona natural o jurídica con la que se relaciona la finca. Un mismo tercero puede ser cliente, proveedor y empleado a la vez. |
| `terceros.consentimiento_datos` | `ConsentimientoDatos` | `/api/v1/terceros/consentimientos/` | Autorización de tratamiento de datos personales (Ley 1581 de 2012) por finalidad. Sin consentimiento vigente los agentes no personalizan ni envían publicidad. |
| `terceros.cliente` | `Cliente` | `/api/v1/terceros/clientes/` | Datos comerciales del tercero que compra. |
| `terceros.proveedor` | `Proveedor` | `/api/v1/terceros/proveedores/` | Datos de compra del tercero que vende insumos o servicios. |
| `terceros.empleado` | `Empleado` | `/api/v1/terceros/empleados/` | Persona que trabaja en la finca, con su forma de vinculación. |

## Reglas de la base que protegen esta app

- `crm.consentimiento_vigente()`
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
