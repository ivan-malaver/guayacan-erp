# Backend · Django + DRF

Monolito modular: una app por esquema de PostgreSQL (25), dueño de todas las tablas. Las reglas críticas viven en la
base (`specs/modelo-datos/generador/reglas_negocio.sql`); aquí no se repiten.

## Estructura

| Carpeta | Qué tiene |
| --- | --- |
| `config/` | Settings (`base`, `dev`, `test`, `prod`), rutas, Celery Beat con las tareas que necesita la base |
| `guayacan/` | Lo transversal: contexto de finca, errores, sincronización, outbox, permisos, autenticación, vistas base |
| `apps/<esquema>/` | `models.py` (generado, `managed=False`), `serializers.py`, `views.py`, `urls.py`, `services.py` (un método por caso de uso), `tests/`, `README.md` |
| `sql/preparar_api.sql` | Crea el usuario `guayacan_api` (miembro de `guayacan_app`) y el esquema `django` |

## Arranque

```
docker compose up -d --build postgres mongodb redis
# cargar esquema y datos (specs/modelo-datos/LEEME.md), luego:
docker compose exec -T postgres psql -U postgres -d guayacan -v ON_ERROR_STOP=1 -v clave_api=<clave> < backend/sql/preparar_api.sql
cd backend
python -m venv .venv && .venv\Scripts\activate        (Linux/macOS: source .venv/bin/activate)
pip install -e .[dev]
python manage.py migrate --database=admin               (solo crea las tablas internas de Django en el esquema django)
python manage.py check
python manage.py runserver
```

Documentación de la API: `http://localhost:8000/api/docs/`. Ingreso: `POST /api/v1/auth/token/` con `correo` y
`contrasena`; después envíe `Authorization: Bearer <acceso>` y, para cambiar de finca, la cabecera `X-Predio`.

## Cómo está armado

- **Contexto de finca** (`guayacan/contexto.py`): abre la transacción de la petición y fija `app.predio_id`,
  `app.usuario_id` y `app.agente_id` con `set_config(..., true)`. Por eso `ATOMIC_REQUESTS` está apagado.
- **Errores** (`guayacan/errores.py`): `P0001` → 422 con el mensaje de la regla, `42501` → 403, `23505`/`23P01` → 409,
  `23514`/`23503`/`23502` → 422, `40001`/`40P01` → 503.
- **Modelos generados**: si cambia `modelo.py`, regenere con `docs/uml/fuentes/gen_apps.py` (ver `docs/desarrollo/`).
  `services.py`, `urls.py` y las pruebas de cada app también salen del generador solo la primera vez: una vez que
  empiece a construir una app, no la regenere completa; regenere solo `models.py`.
- **Acciones por construir**: responden 501 con su caso de uso (`guayacan.vistas.PorConstruir`).
- **CRUD sin borrado**: `VistaModelo` no expone DELETE; los registros se desactivan, anulan o cierran.

## Pruebas

`pytest` usa la base ya cargada (no la crea). En CI se corre después de las baterías de reglas de la base.
Las pruebas de aceptación de cada caso de uso están en `apps/<esquema>/tests/` marcadas como pendientes.
