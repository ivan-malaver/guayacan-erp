"""Lo transversal de GuayacanERP: lo que usan todas las apps.

  contexto.py        fija finca, usuario y agente en cada petición (seguridad por filas)
  autenticacion.py   inicio de sesión con JWT y detector de ataques
  errores.py         traduce los errores de PostgreSQL a respuestas HTTP en español
  sincronizacion.py  recibe los registros capturados sin conexión
  eventos.py         publica eventos con el patrón outbox
  permisos.py        permisos por acción y bloqueo de agentes de IA
  vistas.py          vistas base (CRUD sin borrado y acciones por construir)
  tareas.py          tareas programadas de Celery
  db.py              ayudas de base de datos para los modelos
  captura.py         tablas que se pueden capturar sin conexión (generado)
  paginacion.py      paginación de las listas
  urls.py, urls_b2b.py  rutas transversales y de la API B2B
"""
