# ADR 0006 · Versión 5: operación integral de la finca

- Estado: aceptado
- Fecha: 2026-10-27
- Reemplaza: la propuesta v5 (aplicada aquí) · Relacionado: ADR 0005, `docs/arquitectura/patrones-de-diseno.md` (sección 9)

## Contexto

La v4 dejó la base para iniciar el desarrollo (119 tablas, 90 pruebas). La propuesta v5 y dos análisis externos sumaron
personal, nómina, formación, activos, documentos, cumplimiento y seguros. El 27 de octubre de 2026 el instructor pidió
además: módulos de prueba, detector de ataques y monitoreo de seguridad, autenticación segura, captura de posibles
clientes y empresas, un módulo de estrategia que busque nuevos mercados y productos financiados con las utilidades de
cada sección con su retorno calculado, aplicar sus documentos de finanzas, agenda de cabañas, turnos, ingresos y salidas
de vehículos y personas, cronograma flexible 24/7 por áreas de responsabilidad y la metodología de proyectos (PMBOK 8)
con su guía ISO 21001. Las nueve preguntas de decisión quedaron sin responder y se pidió "aplicar todo".

## Decisión

1. **Todo se construye; lo que depende de un trámite, equipo o decisión queda apagado** (`nucleo.funcionalidad`):
   `nomina_electronica`, `diagnostico_imagen`, `api_b2b`, `webhooks_salientes`, `indicadores_credito`, `cursos_externos`,
   `dron_monitoreo`, `robot_campo`, `certificacion_bpa`, `globalgap`, `seguro_parametrico`, `iso_21001`.
   La granja avícola biosegura (Resolución ICA 3651 de 2014) no lleva interruptor: es obligatoria desde 200 aves.
2. **Supuestos para las preguntas sin respuesta**: régimen tributario "por definir"; salario, jornal, destajo y mixto;
   el ERP calcula y exporta al contador; aprueban encargado y familia por permiso, y el responsable de cada área;
   formación para operarios y estudiantes; RSPA como campo del expediente.
3. **La IA propone y una persona decide, ahora en la base**: `nucleo.exigir_persona()` corta la operación si la sesión
   es de un agente al aprobar tareas, cerrar nómina, aprobar pagos, publicar cronogramas, aprobar documentos, visitas,
   iniciativas, proyectos, cambios, diagnósticos o decisiones.
4. **Segregación de funciones**: nadie aprueba su propia tarea ni su propio pago; quien prepara un pago no lo aprueba;
   el cierre de nómina y los pagos grandes llevan dos personas; quien pide un cambio de proyecto no lo aprueba.
5. **Seguridad informática en la base**: el detector de ataques corre como función (`seguridad.registrar_intento`) y
   disparadores, para que funcione igual en la nube y en la finca; alertas e intentos son de solo inserción.
6. **Calendarios sin cruces con restricciones de exclusión** (btree_gist) en lugar de verificaciones en Python, para
   que dos reservas simultáneas no puedan ganar la misma cabaña.
7. **Finanzas sobre el PUC colombiano**: los conceptos de los documentos (costeo variable, ABC, presupuesto maestro,
   indicadores, palancas) se aplican sobre la contabilidad existente. No se adoptan el plan de cuentas argentino del
   glosario, los modelos de balance del plan contable español ni los ajustes contables por inflación.
8. **Proyectos con PMBOK 8 adaptado**: enfoque predictivo, adaptativo o híbrido por proyecto; líneas base inmutables;
   ruta crítica y valor ganado calculados en la base.

## Consecuencias

- 25 esquemas y 246 tablas; 25 apps en el monolito Django. La ruta manual del mapa de APIs v5 agrega seis pasos.
- 305 pruebas automáticas (90 de regresión y 215 nuevas) sobre una base limpia; deben correr antes de cada commit.
- Los límites laborales (42 h semanales desde el 15 de julio de 2026, 12 h extra, hora nocturna desde las 7 p. m.,
  recargo dominical del 90 % y 100 % desde julio de 2027) son parámetros con vigencia que valida el contador.
- Quedan por confirmar: monto de doble aprobación, tasa de oportunidad, tope de reinversión y cuarentena de aves.
