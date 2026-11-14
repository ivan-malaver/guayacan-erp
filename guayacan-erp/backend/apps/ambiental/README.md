# App `ambiental` (AMB)

Mediciones ambientales (energía solar, biogás, compost, agua) y factores de emisión con su fuente.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| AMB-01 | Registrar mediciones ambientales | 2 | Operario de campo | CRUD |
| AMB-02 | Mantener factores de emisión con su fuente | 2 | Administrador | CRUD |
| AMB-03 | Consultar indicadores ambientales y CO₂ estimado | 2 | Familia, Administrador | `GET /api/v1/ambiental/indicadores/?mes=` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `ambiental.factor_emision` | `FactorEmision` | `/api/v1/ambiental/factores-emision/` | Factor para convertir una medición en CO₂ equivalente, con su fuente; sin fuente no se publica ninguna cifra. |
| `ambiental.registro_ambiental` | `RegistroAmbiental` | `/api/v1/ambiental/registros-ambiental/` | Medición ambiental de la finca (energía solar, biogás, compost, humus, agua). |

## Reglas de la base que protegen esta app

- `ambiental.v_indicadores`

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
