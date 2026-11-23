"""Celery y Celery Beat: las tareas programadas que necesita la base (lista completa en specs/modelo-datos/LEEME.md).

Cómo se arrancan (cada uno en su propia terminal, desde la carpeta backend y con el venv activo):
    celery -A config worker -l info     ejecuta las tareas  (en Windows agregue: --pool=solo)
    celery -A config beat -l info       las lanza a su hora
Necesitan Redis encendido (docker compose up -d redis).

Cada tarea de negocio corre una función de PostgreSQL una vez por finca, con el contexto de esa finca
(ver guayacan/tareas.py). Las horas están en America/Bogota (CELERY_TIMEZONE en settings).
"""
import os

from celery import Celery
from celery.schedules import crontab

# Si no se indica otra configuración, se usa la de desarrollo
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('guayacan')
# Lee de settings todas las variables que empiezan por CELERY_ (p. ej. CELERY_BROKER_URL)
app.config_from_object('django.conf:settings', namespace='CELERY')
# Busca las tareas (@shared_task) en guayacan/tareas.py
app.autodiscover_tasks(['guayacan'])

# crontab(hour=2, minute=15) = todos los días a las 2:15 a. m.
DIARIA = crontab(hour=2, minute=15)

# Agenda de Celery Beat: nombre -> qué tarea, cuándo y con qué argumento (la sentencia SQL)
app.conf.beat_schedule = {
    # Inventario: marca como vencidos los lotes que pasaron su fecha (no se pueden vender)
    'marcar-vencidos': {'task': 'guayacan.tareas.por_finca', 'schedule': DIARIA, 'args': ('select inventario.marcar_vencidos()',)},
    # Ventas: recalcula la mora de los clientes y bloquea a quien supera su plazo
    'mora-clientes': {'task': 'guayacan.tareas.por_finca', 'schedule': DIARIA, 'args': ('select comercial.actualizar_mora()',)},
    # Ventas: crea en borrador los pedidos recurrentes del día (tiendas, hoteles)
    'pedidos-recurrentes': {'task': 'guayacan.tareas.por_finca', 'schedule': crontab(hour=4, minute=0),
                            'args': ('select comercial.generar_pedidos_recurrentes()',)},
    # IoT: borra los clips de cámara vencidos
    'depurar-clips': {'task': 'guayacan.tareas.por_finca', 'schedule': DIARIA, 'args': ('select iot.depurar_clips()',)},
    # Personal: crea las tareas del día a partir del plan de labores
    'tareas-del-dia': {'task': 'guayacan.tareas.por_finca', 'schedule': crontab(hour=4, minute=30),
                       'args': ('select personal.generar_tareas_del_dia()',)},
    # Formación: retira las habilitaciones cuyo certificado venció
    'habilitaciones': {'task': 'guayacan.tareas.por_finca', 'schedule': DIARIA, 'args': ('select formacion.actualizar_habilitaciones()',)},
    # Activos: crea órdenes de trabajo cuando vence un plan de mantenimiento
    'ordenes-mantenimiento': {'task': 'guayacan.tareas.por_finca', 'schedule': DIARIA, 'args': ('select activos.generar_ordenes_trabajo()',)},
    # Cumplimiento: revisa cada expediente contra su evidencia (lo vencido pasa a «no cumple»)
    'expedientes': {'task': 'guayacan.tareas.por_finca', 'schedule': DIARIA,
                    'args': ('select cumplimiento.evaluar_expediente(id) from cumplimiento.expediente',)},
    # Seguridad: alerta si no hubo copia de seguridad o prueba de restauración (no depende de una finca)
    'revisar-copias': {'task': 'guayacan.tareas.global_', 'schedule': DIARIA, 'args': ('select seguridad.revisar_copias()',)},
    # Seguros: vigila el índice de las pólizas paramétricas, solo si la función está encendida
    'indices-seguros': {'task': 'guayacan.tareas.por_finca', 'schedule': DIARIA, 'args': (
        "select seguros.vigilar_indice(i.id) from seguros.indice_poliza i "
        "where exists (select 1 from nucleo.funcionalidad f where f.codigo = 'seguro_parametrico' and f.activa)",)},
    # Núcleo: crea por adelantado las particiones mensuales de las tablas grandes (día 25 de cada mes)
    'particiones': {'task': 'guayacan.tareas.global_', 'schedule': crontab(day_of_month=25, hour=1, minute=0),
                    'args': ('select nucleo.mantener_particiones()',)},
    # Activos: depreciación del mes anterior (día 1)
    'depreciacion': {'task': 'guayacan.tareas.por_finca', 'schedule': crontab(day_of_month=1, hour=3, minute=0),
                     'args': ("select activos.depreciar_mes((date_trunc('month', current_date) - interval '1 month')::date)",)},
    # Finanzas: indicadores financieros del mes anterior (día 2)
    'indicadores': {'task': 'guayacan.tareas.por_finca', 'schedule': crontab(day_of_month=2, hour=3, minute=0),
                    'args': ("select finanzas.calcular_indicadores((date_trunc('month', current_date) - interval '1 month')::date, "
                             "(date_trunc('month', current_date) - interval '1 day')::date)",)},
    # Proyectos: valor ganado de los proyectos en curso (cada lunes)
    'valor-ganado': {'task': 'guayacan.tareas.por_finca', 'schedule': crontab(day_of_week=1, hour=5, minute=0),
                     'args': ("select proyectos.calcular_valor_ganado(id) from proyectos.proyecto where estado = 'en_curso'",)},
    # Apéndice A · Adopción (solo en fincas con la función 'adopcion' encendida):
    # diario (ADO-07): un aviso de mora por cada cuota vencida; readopción con 3 y el último aviso entregado hace 15 días
    'adopcion-abandono': {'task': 'guayacan.tareas.por_finca', 'schedule': crontab(hour=2, minute=45), 'args': (
        "select adopcion.marcar_abandono() where exists (select 1 from nucleo.funcionalidad f "
        "where f.codigo = 'adopcion' and f.activa)",)},
    # día 1: genera las cuotas del mes (las compensa con el saldo del adoptante) y marca los bienes maduros
    'adopcion-cuotas': {'task': 'guayacan.tareas.por_finca', 'schedule': crontab(day_of_month=1, hour=3, minute=30), 'args': (
        "select adopcion.generar_cuotas(), adopcion.marcar_madurez() where exists (select 1 from nucleo.funcionalidad f "
        "where f.codigo = 'adopcion' and f.activa)",)},
    # Outbox: entrega los eventos pendientes a Redis cada 10 segundos
    'publicar-eventos': {'task': 'guayacan.tareas.publicar_eventos', 'schedule': 10.0},
}
