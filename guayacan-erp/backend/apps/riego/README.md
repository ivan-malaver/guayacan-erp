# App `riego` (RIE)

Fuentes de agua, tanques, sistemas de riego, válvulas y eventos de riego (manual hoy, automático en la fase IoT).

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| RIE-01 | Configurar fuentes, tanques, sistemas y válvulas | 1 | Encargado de finca | CRUD |
| RIE-02 | Registrar un riego manual | 1 | Operario de campo | CRUD |
| RIE-03 | Regar automáticamente por reglas | 4 · `riego_automatico` | Pasarela IoT local | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `riego.fuente_agua` | `FuenteAgua` | `/api/v1/riego/fuentes-agua/` | De dónde sale el agua (nacedero, acueducto veredal, lluvia, pozo) y su permiso. |
| `riego.tanque` | `Tanque` | `/api/v1/riego/tanques/` | Tanques de almacenamiento (hoy: dos de 2.000 litros). |
| `riego.sistema_riego` | `SistemaRiego` | `/api/v1/riego/sistemas-riego/` | Red de riego que cubre una o varias zonas (hoy: manguera con aspersores). |
| `riego.valvula` | `Valvula` | `/api/v1/riego/valvulas/` | Cada válvula del sistema (hoy manual en cada aspersor; luego electroválvula). |
| `riego.evento_riego` | `EventoRiego` | `/api/v1/riego/eventos-riego/` | Cada riego hecho: cuánto tiempo, cuánta agua y si fue manual o automático. |

## Reglas de la base que protegen esta app

- `regla determinista en la pasarela`

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
