# App `ia` (IA)

Agentes, herramientas, aprobaciones, base de conocimiento, recomendaciones, evaluaciones y consumo de IA.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| IA-01 | Configurar un agente y sus herramientas | 1 | Administrador | CRUD |
| IA-02 | Resolver la bandeja de aprobaciones | 1 | Administrador | `POST /api/v1/ia/solicitudes-aprobacion/{id}/aprobar/` |
| IA-03 | Alimentar la base de conocimiento | 1 | Administrador | `POST /api/v1/ia/documentos-conocimiento/{id}/indexar/`<br>`POST /api/v1/ia/buscar/` |
| IA-04 | Recibir y seguir recomendaciones de mejora | 1 | Administrador, Familia | CRUD |
| IA-05 | Evaluar las respuestas de los agentes | 1 | Cliente, Administrador | CRUD |
| IA-06 | Controlar el consumo y el costo de la IA | 1 | Administrador | CRUD |
| IA-07 | Pronosticar la demanda | 3 · `pronostico_demanda` | Tareas programadas | CRUD |
| IA-08 | Diagnosticar una foto de campo | 2 · `diagnostico_imagen` | Operario de campo | CRUD |
| IA-09 | Simular un escenario y registrar la decisión | 2 | Familia | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `ia.agente` | `Agente` | `/api/v1/ia/agentes/` | Agente de IA con un rol, sus instrucciones versionadas, su modelo y su nivel de autonomía. |
| `ia.herramienta` | `Herramienta` | `/api/v1/ia/herramientas/` | Función del ERP que un agente puede invocar (por MCP o API), con su nivel de riesgo. |
| `ia.agente_herramienta` | `AgenteHerramienta` | `/api/v1/ia/agentes/{id}/herramientas/` | Qué herramientas puede usar cada agente (mínimo privilegio). |
| `ia.solicitud_aprobacion` | `SolicitudAprobacion` | `/api/v1/ia/solicitudes-aprobacion/` | Bandeja del administrador: toda acción que un agente quiere hacer y requiere permiso humano. |
| `ia.documento_conocimiento` | `DocumentoConocimiento` | `/api/v1/ia/documentos-conocimiento/` | Fuente de la base de conocimiento: fichas de producto, políticas, preguntas frecuentes, manuales técnicos, informes. |
| `ia.fragmento_conocimiento` | `FragmentoConocimiento` | `/api/v1/ia/fragmentos-conocimiento/` | Trozo de un documento con su vector semántico (pgvector) para que los agentes encuentren la información relevante (RAG). |
| `ia.recomendacion` | `Recomendacion` | `/api/v1/ia/recomendaciones/` | Plan de acción o mejora continua propuesto por un agente analista, con su seguimiento (ciclo PHVA). |
| `ia.evaluacion_respuesta` | `EvaluacionRespuesta` | `/api/v1/ia/evaluaciones-respuesta/` | Calificación de una respuesta de un agente por el cliente o el administrador; alimenta la mejora de instrucciones y conocimiento. |
| `ia.consumo_ia` | `ConsumoIa` | `/api/v1/ia/consumos/` | Tokens y costo por agente, modelo y día, para controlar el gasto. |
| `ia.regla_conversacion` | `ReglaConversacion` | `/api/v1/ia/reglas-conversacion/` | Guardia del orquestador: temas permitidos, temas que se rechazan con cortesía y casos que pasan a una persona. |
| `ia.escalamiento` | `Escalamiento` | `/api/v1/ia/escalamientos/` | Conversación pasada a una persona: motivo, quién la atiende y hasta cuándo se puede responder según la ventana del canal. |
| `ia.modelo_pronostico` | `ModeloPronostico` | `/api/v1/ia/modelos-pronostico/` | Modelo de pronóstico de demanda entrenado; gana el de menor error (necesita al menos 12 meses de ventas). |
| `ia.pronostico_demanda` | `PronosticoDemanda` | `/api/v1/ia/pronosticos-demanda/` | Cantidad esperada de venta por producto y periodo, con su rango. |
| `ia.diagnostico_imagen` | `DiagnosticoImagen` | `/api/v1/ia/diagnosticos-imagen/` | Foto de hoja, fruto o animal analizada por el agente Agrónomo. Es una propuesta: no crea compras ni aplicaciones; la confirma una persona. |
| `ia.escenario` | `Escenario` | `/api/v1/ia/escenarios/` | Simulación "qué pasa si" (sube el concentrado 10 %, se pasa de 100 a 500 gallinas, cae la postura). |
| `ia.decision` | `Decision` | `/api/v1/ia/decisiones/` | Registro de decisiones: contexto, opciones, evidencia, quién decidió y, después, el resultado. Memoria de la finca. |

## Reglas de la base que protegen esta app

- `ciclo PHVA semanal`
- `ia.validar_decision()`
- `ia.validar_diagnostico()`
- `límite de costo diario por agente`
- `mínimo 12 meses de ventas`
- `mínimo privilegio`
- `nucleo.exigir_persona()`

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
