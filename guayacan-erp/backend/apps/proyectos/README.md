# App `proyectos` (PRY)

Dirección de proyectos (PMBOK 8): acta, interesados, EDT, cronograma con ruta crítica, iteraciones, riesgos, cambios, líneas base y valor ganado.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| PRY-01 | Constituir un proyecto | 2 | Director de proyecto | CRUD |
| PRY-02 | Aprobar un proyecto | 2 | Patrocinador | `POST /api/v1/proyectos/proyectos/{id}/aprobar/` |
| PRY-03 | Planificar el alcance y el cronograma | 2 | Director de proyecto | CRUD |
| PRY-04 | Calcular la ruta crítica | 2 | Director de proyecto | `POST /api/v1/proyectos/proyectos/{id}/ruta-critica/` |
| PRY-05 | Gestionar interesados y riesgos | 2 | Director de proyecto | CRUD |
| PRY-06 | Registrar avance y medir el valor ganado | 2 | Director de proyecto | `POST /api/v1/proyectos/proyectos/{id}/valor-ganado/?corte=`<br>`GET /api/v1/proyectos/tablero/` |
| PRY-07 | Solicitar y decidir un cambio | 2 | Director de proyecto, Patrocinador | `POST /api/v1/proyectos/solicitudes-cambio/{id}/decidir/` |
| PRY-08 | Aceptar entregables y cerrar el proyecto | 2 | Patrocinador, Director de proyecto | CRUD |
| PRY-09 | Planear y cerrar una iteración | 2 | Director de proyecto | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `proyectos.proyecto` | `Proyecto` | `/api/v1/proyectos/proyectos/` | Proyecto de la finca (nuevo galpón, sistema solar, cabañas, certificación, piloto de robot) con acta de constitución, enfoque predictivo, adaptativo o híbrido y área de enfoque actual. |
| `proyectos.interesado` | `Interesado` | `/api/v1/proyectos/interesados/` | Interesado del proyecto con su interés, influencia y estrategia de relación (dominio de interesados). |
| `proyectos.elemento_edt` | `ElementoEdt` | `/api/v1/proyectos/elementos-edt/` | Estructura de desglose del trabajo (EDT): entregables y paquetes de trabajo con su criterio de aceptación. |
| `proyectos.iteracion` | `Iteracion` | `/api/v1/proyectos/iteraciones/` | Iteración o sprint para la parte adaptativa del proyecto. |
| `proyectos.actividad` | `Actividad` | `/api/v1/proyectos/actividades/` | Actividad del cronograma (o historia de la iteración) con duración, fechas, avance, costo y responsable; la ruta crítica la calcula la base. |
| `proyectos.dependencia` | `Dependencia` | `/api/v1/proyectos/actividades/{id}/dependencias/` | Relación entre actividades (fin a comienzo, comienzo a comienzo, fin a fin, comienzo a fin) con adelanto o retraso. |
| `proyectos.riesgo` | `Riesgo` | `/api/v1/proyectos/riesgos/` | Riesgo del proyecto (amenaza u oportunidad) con probabilidad, impacto, respuesta y responsable. |
| `proyectos.registro` | `Registro` | `/api/v1/proyectos/registros/` | Registro de incidentes, supuestos, restricciones, decisiones y lecciones aprendidas del proyecto. |
| `proyectos.solicitud_cambio` | `SolicitudCambio` | `/api/v1/proyectos/solicitudes-cambio/` | Solicitud de cambio al alcance, cronograma o costo; la aprueba una persona distinta de quien la pide y, si se aprueba, crea una nueva línea base. |
| `proyectos.linea_base` | `LineaBase` | `/api/v1/proyectos/lineas-base/` | Línea base aprobada de alcance, cronograma y costo; no se edita: cada cambio aprobado crea una versión nueva. |
| `proyectos.medicion_valor_ganado` | `MedicionValorGanado` | `/api/v1/proyectos/mediciones-valor-ganado/` | Medición del desempeño en una fecha de corte por valor ganado: PV, EV, AC, CPI, SPI, EAC, ETC y VAC. |

## Reglas de la base que protegen esta app

- `proyectos.aceptar_entregable()`
- `proyectos.avance_actividad()`
- `proyectos.calcular_ruta_critica()`
- `proyectos.calcular_valor_ganado()`
- `proyectos.clasificar_interesado()`
- `proyectos.decidir_cambio()`
- `proyectos.linea_base_inicial()`
- `proyectos.nueva_linea_base()`
- `proyectos.validar_dependencia()`
- `proyectos.validar_proyecto()`

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
