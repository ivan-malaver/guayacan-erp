# App `turismo` (TUR)

Alojamientos, planes turísticos y reservas (fase 3).

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| TUR-01 | Gestionar alojamientos y planes turísticos | 3 | Administrador | CRUD |
| TUR-02 | Reservar una cabaña o un plan | 3 | Cliente, Vendedor | `GET /api/v1/agenda/recursos/{id}/disponible/` |
| TUR-03 | Pagar anticipadamente una reserva | 3 | Cliente | `POST /api/v1/pagos/webhook/` |
| TUR-04 | Hacer check-in y check-out de huéspedes | 3 | Portería, Vendedor | CRUD |
| TUR-05 | Atender la solicitud de un grupo | 3 | Operador turístico o institución | CRUD |
| TUR-06 | Bloquear fechas del calendario | 3 | Administrador | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `turismo.alojamiento` | `Alojamiento` | `/api/v1/turismo/alojamientos/` | Cabaña o espacio de hospedaje. |
| `turismo.plan_turistico` | `PlanTuristico` | `/api/v1/turismo/planes-turistico/` | Experiencia ofrecida (pasadía, recorrido del cacao, ordeño, taller). |
| `turismo.reserva` | `Reserva` | `/api/v1/turismo/reservas/` | Reserva de alojamiento o plan. |
| `turismo.bloqueo_calendario` | `BloqueoCalendario` | `/api/v1/turismo/bloqueos-calendario/` | Fechas en que un alojamiento o un plan no está disponible (mantenimiento, uso familiar). |

## Reglas de la base que protegen esta app

- `turismo.sincronizar_agenda()`
- `turismo.sincronizar_bloqueo()`
- `turismo.validar_reserva()`

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
