# App `personal` (PER)

Tareas, plan de labores, cuadrillas, turnos, ausencias (sin diagnósticos), matriz de responsabilidades, equipos asignados, carné QR o NFC y jornada.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| PER-01 | Configurar áreas de responsabilidad y matriz RACI | 1 | Administrador | CRUD |
| PER-02 | Definir el plan de labores | 1 | Encargado de finca | CRUD |
| PER-03 | Generar las tareas del día | 1 | Tareas programadas | `POST /api/v1/personal/tareas/generar-dia/` |
| PER-04 | Asignar una tarea | 1 | Encargado de finca | CRUD |
| PER-05 | Ejecutar una tarea con evidencia | 1 | Operario de campo | CRUD |
| PER-06 | Aprobar o devolver una tarea | 1 | Encargado de finca | `POST /api/v1/personal/tareas/{id}/aprobar/` |
| PER-07 | Armar y publicar el cronograma de turnos | 2 | Encargado de finca | `POST /api/v1/personal/cronogramas/{id}/generar/`<br>`GET /api/v1/personal/cronogramas/{id}/huecos/`<br>`POST /api/v1/personal/cronogramas/{id}/publicar/` |
| PER-08 | Registrar disponibilidad y ausencias | 2 | Operario de campo, Encargado de finca | CRUD |
| PER-09 | Registrar la jornada con el carné | 1 | Operario de campo | CRUD |
| PER-10 | Organizar cuadrillas | 1 | Encargado de finca | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `personal.cuadrilla` | `Cuadrilla` | `/api/v1/personal/cuadrillas/` | Grupo de trabajadores que recibe tareas juntos (ej. cuadrilla de cosecha). |
| `personal.cuadrilla_miembro` | `CuadrillaMiembro` | `/api/v1/personal/cuadrillas-miembro/` | Trabajadores de cada cuadrilla, con fechas. |
| `personal.turno` | `Turno` | `/api/v1/personal/turnos/` | Horario de trabajo programado de una persona en un día. |
| `personal.ausencia` | `Ausencia` | `/api/v1/personal/ausencias/` | Vacaciones, permisos, incapacidades y licencias. Guarda solo el tipo y las fechas, nunca el diagnóstico médico. |
| `personal.plantilla_tarea` | `PlantillaTarea` | `/api/v1/personal/plantillas-tarea/` | Labor que se repite (recoger huevos dos veces al día, revisar bebederos, deshierbe semanal) y genera las tareas del día. |
| `personal.tarea` | `Tarea` | `/api/v1/personal/tareas/` | Trabajo concreto con responsable, lugar, plazo y evidencia. Solo se asigna a quien está disponible y habilitado; aprobada no se edita. |
| `personal.paso_tarea` | `PasoTarea` | `/api/v1/personal/tareas/{id}/pasos/` | Paso de la lista de chequeo de una tarea. |
| `personal.evidencia_tarea` | `EvidenciaTarea` | `/api/v1/personal/tareas/{id}/evidencias/` | Prueba de una tarea: foto, lectura del carné o del lote, nota de voz o el registro que creó. |
| `personal.matriz_responsabilidad` | `MatrizResponsabilidad` | `/api/v1/personal/matrices-responsabilidad/` | Matriz RACI: para cada proceso, qué rol lo hace, lo aprueba, es consultado o informado. |
| `personal.asignacion_equipo` | `AsignacionEquipo` | `/api/v1/personal/asignaciones-equipo/` | Quién tiene cada herramienta o equipo, desde cuándo y en qué estado lo recibió y lo devolvió. |
| `personal.credencial_trabajo` | `CredencialTrabajo` | `/api/v1/personal/credenciales-trabajo/` | Carné del trabajador con QR o etiqueta NFC para registrar quién hizo qué, sin biometría. |
| `personal.jornada` | `Jornada` | `/api/v1/personal/jornadas/` | Registro de jornada (entrada, salida, horas y labor) para jornaleros sin tarea asignada ese día. |
| `personal.area_responsabilidad` | `AreaResponsabilidad` | `/api/v1/personal/areas-responsabilidad/` | Área de responsabilidad (galpón, cultivos, turismo y cabañas, bodega y despachos, mantenimiento, vigilancia): agrupa zonas, personas y tareas, con un responsable. |
| `personal.miembro_area` | `MiembroArea` | `/api/v1/personal/miembros-area/` | Personas de cada área, con quién es el responsable (puede aprobar las tareas del área). |
| `personal.patron_turno` | `PatronTurno` | `/api/v1/personal/patrones-turno/` | Patrón de turnos reutilizable: semanal (se eligen días y horas), cíclico (ej. 2 días, 2 noches, 2 de descanso para 24/7) o flexible (se arma a mano). |
| `personal.patron_turno_detalle` | `PatronTurnoDetalle` | `/api/v1/personal/patrones-turno/{id}/dias/` | Día del patrón con su horario (puede cruzar la medianoche) o descanso. |
| `personal.cronograma` | `Cronograma` | `/api/v1/personal/cronogramas/` | Cronograma de trabajo de un área por un periodo: se genera desde patrones, se ajusta a mano y se publica cuando cumple jornada máxima, descanso semanal y cobertura. |
| `personal.asignacion_patron` | `AsignacionPatron` | `/api/v1/personal/asignaciones-patron/` | Qué patrón sigue cada persona dentro del cronograma (con desfase para rotar entre varias personas). |
| `personal.requerimiento_cobertura` | `RequerimientoCobertura` | `/api/v1/personal/requerimientos-cobertura/` | Cuántas personas necesita un área por franja horaria y día (ej. galpón: 1 persona las 24 horas; cabañas: 2 de 8 a 18 los fines de semana). |
| `personal.disponibilidad` | `Disponibilidad` | `/api/v1/personal/disponibilidades/` | Días y horas en que cada persona puede o prefiere trabajar (para armar el cronograma flexible). |

## Reglas de la base que protegen esta app

- `formacion.esta_habilitado()`
- `personal.calcular_jornada()`
- `personal.empleado_disponible()`
- `personal.es_responsable_area()`
- `personal.generar_tareas_del_dia()`
- `personal.generar_turnos()`
- `personal.huecos_cobertura()`
- `personal.publicar_cronograma()`
- `personal.validar_area_tarea()`
- `personal.validar_tarea()`
- `personal.validar_turno()`

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
