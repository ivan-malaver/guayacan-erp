# App `agenda` (AGD)

Recursos agendables (cabañas, salón, vehículos, equipos), calendario sin cruces, visitas programadas e ingresos y salidas de personas y vehículos.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| AGD-01 | Configurar recursos agendables | 3 | Administrador | CRUD |
| AGD-02 | Agendar una cita en un recurso | 3 | Encargado de finca, Vendedor | CRUD |
| AGD-03 | Programar y aprobar una visita | 2 | Encargado de finca | `POST /api/v1/agenda/visitas/{id}/aprobar/`<br>`POST /api/v1/agenda/visitas/{id}/pase/` |
| AGD-04 | Registrar entradas y salidas en portería | 2 | Portería | CRUD |
| AGD-05 | Consultar quién está en la finca | 2 | Portería, Administrador | `GET /api/v1/agenda/en-sitio/` |
| AGD-06 | Consultar la agenda del día | 2 | Encargado de finca, Portería | `GET /api/v1/agenda/dia/?fecha=` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `agenda.recurso` | `Recurso` | `/api/v1/agenda/recursos/` | Lo que se agenda: cabañas, salón, zona de camping, vehículo, equipo, punto de cargue. Cada recurso tiene su calendario sin cruces. |
| `agenda.cita` | `Cita` | `/api/v1/agenda/citas/` | Bloque del calendario de un recurso (reserva, limpieza, mantenimiento, uso familiar, entrega). La base impide cruces, contando el alistamiento. |
| `agenda.visita` | `Visita` | `/api/v1/agenda/visitas/` | Ingreso programado de una persona o un vehículo (proveedor, cliente, turista, técnico, autoridad): se aprueba antes, entrega un pase QR y exige bioseguridad si va al galpón. |
| `agenda.registro_acceso` | `RegistroAcceso` | `/api/v1/agenda/registros-acceso/` | Cada entrada o salida real por la portería (persona o vehículo): con pase, carné QR o NFC, a mano o por lectura de placa. Funciona sin internet y alimenta la jornada. |

## Reglas de la base que protegen esta app

- `agenda.emitir_pase()`
- `agenda.preparar_cita()`
- `agenda.recurso_libre()`
- `agenda.v_agenda_dia`
- `agenda.v_en_sitio`
- `agenda.validar_acceso()`
- `agenda.validar_visita()`
- `exclusión GiST sin cruces`

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
