# App `nucleo` (NUC)

Usuarios, roles, permisos, parámetros con vigencia, auditoría, predio y zonas, eventos de integración.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| NUC-01 | Configurar la finca, sus zonas y el mapa | 1 | Administrador | `GET /api/v1/nucleo/zonas/?formato=geojson` |
| NUC-02 | Gestionar usuarios, roles y permisos | 1 | Administrador | CRUD |
| NUC-03 | Administrar parámetros con vigencia | 1 | Administrador, Contador | CRUD |
| NUC-04 | Encender o apagar una función de la finca | 1 | Administrador | CRUD |
| NUC-05 | Sincronizar registros capturados sin conexión | 1 | Operario de campo, Vendedor | `POST /api/v1/sincronizacion/lote/` |
| NUC-06 | Consultar la auditoría de cambios | 1 | Administrador, Contador, Auditor externo | `GET /api/v1/nucleo/auditoria/?tabla=&registro=` |
| NUC-07 | Registrar una nota de voz en campo y confirmarla | 2 · `notas_voz` | Operario de campo | `POST /api/v1/nucleo/notas-voz/{id}/confirmar/` |
| NUC-08 | Practicar en la finca de aprendizaje | 1 · `modo_aprendiz` | Estudiante, Instructor | CRUD |
| NUC-09 | Publicar los eventos de integración | 1 | Tareas programadas | CRUD |
| NUC-10 | Administrar llaves de API B2B y webhooks | 3 · `api_b2b` | Administrador | `GET /api/b2b/v1/catalogo/`<br>`POST /api/b2b/v1/pedidos/` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `nucleo.usuario` | `Usuario` | `/api/v1/nucleo/usuarios/` | Persona que entra al sistema (administrador, operario, contador, cliente con cuenta). Reemplaza el usuario de Django (AUTH_USER_MODEL). |
| `nucleo.rol` | `Rol` | `/api/v1/nucleo/roles/` | Conjunto de permisos que se asigna a usuarios o agentes (administrador, operario de granja, contador, vendedor). |
| `nucleo.permiso` | `Permiso` | `/api/v1/nucleo/permisos/` | Acción concreta que se puede autorizar, por módulo (ej. comercial.aprobar_precio). |
| `nucleo.rol_permiso` | `RolPermiso` | `/api/v1/nucleo/roles/{id}/permisos/` | Qué permisos tiene cada rol (relación muchos a muchos). |
| `nucleo.usuario_rol` | `UsuarioRol` | `/api/v1/nucleo/usuarios/{id}/roles/` | Qué roles tiene cada usuario en cada finca (un usuario puede trabajar en varias fincas con roles distintos). |
| `nucleo.parametro` | `Parametro` | `/api/v1/nucleo/parametros/` | Valores de negocio que cambian con el tiempo (IVA, salario mínimo, tarifa de domicilio, margen mínimo). Nunca van fijos en el código. |
| `nucleo.auditoria` | `Auditoria` | `/api/v1/nucleo/auditoria/` | Registro inalterable de cada cambio importante: quién (persona o agente), qué, cuándo y cómo estaba antes. Particionada por mes. |
| `nucleo.evento_salida` | `EventoSalida` | `/api/v1/nucleo/eventos-salida/` | Bandeja de salida (patrón outbox): cada hecho de negocio se escribe aquí en la misma transacción y luego se publica a MongoDB, a los agentes y a otros servicios. |
| `nucleo.predio` | `Predio` | `/api/v1/nucleo/predios/` | Finca o terreno donde opera el sistema (permite replicarlo en otras fincas). |
| `nucleo.zona` | `Zona` | `/api/v1/nucleo/zonas/` | Área dentro del predio con un uso (galpón, aprisco, estanque, lote de cultivo, potrero, bodega, ronda hídrica). |
| `nucleo.dispositivo_captura` | `DispositivoCaptura` | `/api/v1/nucleo/dispositivos-captura/` | Equipo con el que se capturan datos: celulares con la app, lectores de código de barras, básculas e impresoras de etiquetas. |
| `nucleo.sincronizacion` | `Sincronizacion` | `/api/v1/nucleo/sincronizaciones/` | Cada sincronización de la app sin conexión: cuántos registros subió, cuántos se rechazaron y por qué. |
| `nucleo.funcionalidad` | `Funcionalidad` | `/api/v1/nucleo/funcionalidades/` | Interruptor de funciones por finca (feature flag): lo que aún no tiene equipo o decisión queda construido y apagado, y se enciende sin desplegar otra versión. |
| `nucleo.nota_voz` | `NotaVoz` | `/api/v1/nucleo/notas-voz/` | Nota de voz grabada en campo sin conexión; se transcribe al sincronizar y el operario confirma lo interpretado antes de crear el registro. |
| `nucleo.llave_api` | `LlaveApi` | `/api/v1/nucleo/llaves-api/` | Llave de un cliente B2B (HORECA) para la API: guarda solo su huella, con alcances, límite de peticiones y vencimiento. Se enciende con api_b2b. |
| `nucleo.webhook_suscripcion` | `WebhookSuscripcion` | `/api/v1/nucleo/webhooks-suscripcion/` | Sistema externo (comprador, logística) que recibe eventos firmados del outbox: pedido confirmado, lote despachado, factura emitida. |
| `nucleo.webhook_entrega` | `WebhookEntrega` | `/api/v1/nucleo/webhooks-entrega/` | Intento de entrega de un evento a un webhook, con reintentos. |

## Reglas de la base que protegen esta app

- `ON CONFLICT (predio_id, id_cliente) DO NOTHING`
- `nucleo.auditar()`
- `nucleo.autenticar_llave_api()`
- `nucleo.exigir_funcion()`
- `nucleo.parametro_texto()`
- `nucleo.parametro_valor()`
- `nucleo.predio_actual()`
- `nucleo.predios_del_usuario()`
- `nucleo.tiene_permiso()`
- `nucleo.validar_llave_api()`
- `nucleo.validar_webhook()`
- `patrón outbox`
- `seguridad.vigilar_privilegios()`

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
