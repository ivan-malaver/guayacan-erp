"""Tablas que la app de campo puede capturar sin conexión (tienen la columna id_cliente).

Para qué sirve: guayacan/sincronizacion.py solo acepta registros de estas tablas, así nadie puede usar la
sincronización para escribir en otras. Generado por docs/uml/fuentes/gen_apps.py desde modelo.py y
modelo_apendice_a.py: no lo edite a mano."""

# frozenset: conjunto que no se puede modificar mientras corre el programa
TABLAS_CAPTURA = frozenset({
    'activos.uso_activo',
    'adopcion.seguimiento',
    'agenda.registro_acceso',
    'ambiental.registro_ambiental',
    'comercial.entrega',
    'comercial.pago',
    'comercial.pedido',
    'crm.interaccion',
    'crm.prospecto',
    'cumplimiento.evaluacion_requisito',
    'formacion.asistencia',
    'formacion.encuesta',
    'formacion.progreso',
    'ia.diagnostico_imagen',
    'inventario.conteo_detalle',
    'inventario.lectura_codigo',
    'inventario.movimiento_inventario',
    'inventario.pesaje',
    'iot.comando_actuador',
    'nucleo.nota_voz',
    'personal.evidencia_tarea',
    'personal.paso_tarea',
    'personal.tarea',
    'produccion.calidad_agua_estanque',
    'produccion.clasificacion_postura',
    'produccion.cosecha',
    'produccion.evento_reproductivo',
    'produccion.evento_sanitario',
    'produccion.labor_cultural',
    'produccion.produccion_abono',
    'produccion.registro_alimentacion',
    'produccion.registro_bioseguridad',
    'produccion.registro_pesaje',
    'produccion.registro_postura',
    'riego.evento_riego',
})
