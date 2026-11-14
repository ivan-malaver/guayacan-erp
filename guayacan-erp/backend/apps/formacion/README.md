# App `formacion` (FOR)

Cursos, lecciones, evaluaciones, sesiones presenciales, certificados y habilitaciones que permiten asignar tareas.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| FOR-01 | Diseñar un curso con lecciones y evaluación | 2 | Instructor | CRUD |
| FOR-02 | Tomar un curso virtual | 2 | Estudiante, Operario de campo | CRUD |
| FOR-03 | Dictar una sesión presencial y registrar asistencia | 2 | Instructor | `POST /api/v1/formacion/sesiones-presenciales/{id}/certificar/` |
| FOR-04 | Emitir certificados y habilitaciones | 2 | Tareas programadas | CRUD |
| FOR-05 | Retirar habilitaciones vencidas | 2 | Tareas programadas | CRUD |
| FOR-06 | Detectar necesidades de formación | 2 | Encargado de finca | CRUD |
| FOR-07 | Responder la encuesta de un curso | 2 | Estudiante, Operario de campo | CRUD |
| FOR-08 | Presentar y resolver una queja o apelación | 2 | Estudiante, Operario de campo | CRUD |
| FOR-09 | Preguntar al Instructor virtual | 2 | Operario de campo, Estudiante | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `formacion.competencia` | `Competencia` | `/api/v1/formacion/competencias/` | Habilidad que habilita tareas (registrar vacunas, aplicar insumos, liberar lotes, operar motosierra), con su vigencia. |
| `formacion.curso` | `Curso` | `/api/v1/formacion/cursos/` | Curso virtual, presencial o mixto para operarios o estudiantes; los externos (SENA, FAO, Moodle) se enlazan. |
| `formacion.leccion` | `Leccion` | `/api/v1/formacion/lecciones/` | Lección de un curso (texto, video corto, práctica guiada); se descarga para verla sin señal. |
| `formacion.evaluacion` | `Evaluacion` | `/api/v1/formacion/evaluaciones/` | Examen de un curso. |
| `formacion.pregunta` | `Pregunta` | `/api/v1/formacion/preguntas/` | Pregunta de una evaluación. |
| `formacion.inscripcion` | `Inscripcion` | `/api/v1/formacion/inscripciones/` | Persona (operario o estudiante) inscrita en un curso, con su nota. |
| `formacion.progreso` | `Progreso` | `/api/v1/formacion/progresos/` | Lecciones vistas por cada inscrito. |
| `formacion.sesion_presencial` | `SesionPresencial` | `/api/v1/formacion/sesiones-presencial/` | Sesión dictada por el veterinario, el agrónomo o el encargado; su asistencia cuenta igual que un curso virtual. |
| `formacion.asistencia` | `Asistencia` | `/api/v1/formacion/asistencias/` | Asistencia y nota de cada persona en una sesión presencial. |
| `formacion.certificado` | `Certificado` | `/api/v1/formacion/certificados/` | Certificado interno con fecha, nota y vencimiento; al emitirse crea la habilitación. |
| `formacion.habilitacion` | `Habilitacion` | `/api/v1/formacion/habilitaciones/` | Permiso para hacer una tarea, nacido de un certificado. Al vencer el certificado se retira sola. |
| `formacion.necesidad_formacion` | `NecesidadFormacion` | `/api/v1/formacion/necesidades-formacion/` | Necesidad de formación detectada (por cargo, por una no conformidad, por un cambio o pedida por la persona). |
| `formacion.encuesta` | `Encuesta` | `/api/v1/formacion/encuestas/` | Encuesta de satisfacción y de resultados de un curso o sesión (seguimiento y medición de la formación). |
| `formacion.queja_apelacion` | `QuejaApelacion` | `/api/v1/formacion/quejas-apelacion/` | Queja sobre la formación o apelación de una nota o certificado; se responde en plazo y la resuelve alguien distinto del instructor. |

## Reglas de la base que protegen esta app

- `documental.documento_para_agente()`
- `formacion.actualizar_habilitaciones()`
- `formacion.certificar_inscripcion()`
- `formacion.certificar_sesion()`
- `formacion.emitir_certificado()`
- `formacion.habilitar_desde_certificado()`
- `formacion.v_satisfaccion`
- `formacion.validar_curso()`
- `formacion.validar_inscripcion()`
- `formacion.validar_queja()`

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
