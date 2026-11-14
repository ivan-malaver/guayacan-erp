# App `estrategia` (EST)

Líneas de negocio, DOFA, estudios de mercado, iniciativas de crecimiento, evaluación de proyectos (VPN, TIR, ROI, palancas) y reinversión de utilidades.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| EST-01 | Mantener las líneas de negocio y la matriz DOFA | 2 | Familia | `GET /api/v1/estrategia/lineas/` |
| EST-02 | Registrar un estudio de mercado | 2 | Familia | CRUD |
| EST-03 | Proponer una iniciativa de crecimiento | 2 | Familia | CRUD |
| EST-04 | Evaluar financieramente una iniciativa | 2 | Familia | `POST /api/v1/estrategia/evaluaciones-proyecto/{id}/calcular/` |
| EST-05 | Aprobar una iniciativa | 2 | Familia | CRUD |
| EST-06 | Reinvertir utilidades de una línea | 2 | Familia | CRUD |
| EST-07 | Seguir el retorno de las iniciativas | 2 | Familia | `GET /api/v1/estrategia/retorno/` |
| EST-08 | Definir objetivos y metas del cuadro de mando | 2 | Familia | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `estrategia.linea_negocio` | `LineaNegocio` | `/api/v1/estrategia/lineas-negocio/` | Línea de negocio de la finca (avícola, piscícola, perennes, turismo…) o una nueva en estudio, unida a su centro de costo. |
| `estrategia.factor_dofa` | `FactorDofa` | `/api/v1/estrategia/factores-dofa/` | Debilidad, oportunidad, fortaleza o amenaza de la finca o de una línea, con su fuente. |
| `estrategia.estudio_mercado` | `EstudioMercado` | `/api/v1/estrategia/estudios-mercado/` | Dato de un mercado posible: tamaño, precio de referencia, competidores y fuente (SIPSA, DANE, gremios, visitas). |
| `estrategia.iniciativa` | `Iniciativa` | `/api/v1/estrategia/iniciativas/` | Idea de crecimiento: nuevo mercado, producto, canal o negocio, clasificada por la matriz de Ansoff y por la palanca que usa. La IA puede proponerla; decide la familia. |
| `estrategia.evaluacion_proyecto` | `EvaluacionProyecto` | `/api/v1/estrategia/evaluaciones-proyecto/` | Evaluación financiera de una iniciativa: inversión, flujos, VPN, TIR, ROI, recuperación, punto de equilibrio, margen de seguridad y grados de palanca. La calcula la base. |
| `estrategia.flujo_proyecto` | `FlujoProyecto` | `/api/v1/estrategia/evaluaciones-proyecto/{id}/flujos/` | Flujo de caja proyectado de una evaluación por mes (mes 0 = inversión). |
| `estrategia.reinversion` | `Reinversion` | `/api/v1/estrategia/reinversiones/` | Parte de la utilidad de una línea que se destina a una iniciativa (apalancarse con lo ganado). Nunca de una línea con pérdida ni por encima del tope de reinversión. |
| `estrategia.seguimiento_iniciativa` | `SeguimientoIniciativa` | `/api/v1/estrategia/seguimientos-iniciativa/` | Resultado real mes a mes de una iniciativa en piloto o escalada, contra lo proyectado: así se mide el retorno de verdad. |
| `estrategia.objetivo` | `Objetivo` | `/api/v1/estrategia/objetivos/` | Objetivo estratégico por perspectiva del cuadro de mando (financiera, clientes, procesos, aprendizaje), con indicador y meta. |

## Reglas de la base que protegen esta app

- `estrategia.evaluar_proyecto()`
- `estrategia.tir()`
- `estrategia.utilidad_linea()`
- `estrategia.v_matriz_lineas`
- `estrategia.v_retorno_iniciativas`
- `estrategia.validar_iniciativa()`
- `estrategia.validar_reinversion()`
- `estrategia.vpn()`
- `semáforo de finanzas.calcular_indicadores()`

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
