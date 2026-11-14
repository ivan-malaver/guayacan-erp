"""Diagramas UML de comportamiento (Mermaid): secuencia, estados y actividad.

QUÉ HACE: escribe en <destino>/secuencia, estados y actividad los diagramas SQ01-SQ15, ST01-ST17 y AC01-AC04.
CÓMO: cada diagrama es un bloque de texto Mermaid dentro de este archivo; render() lo guarda como .mmd y
lo convierte a .svg y .png con mmdc. Para cambiar un diagrama, edite su bloque y vuelva a ejecutar.
REQUISITO: Mermaid CLI (npm install -g @mermaid-js/mermaid-cli).
Uso: python3 gen_comportamiento.py <destino>
"""
import os
import subprocess
import sys

DEST = sys.argv[1]
CFG = os.path.join(DEST, 'mermaid.json')
if not os.path.exists(CFG):
    open(CFG, 'w').write('{"theme":"neutral","themeVariables":{"fontFamily":"DejaVu Sans","fontSize":"14px"},'
                         '"sequence":{"useMaxWidth":false},"flowchart":{"useMaxWidth":false},"state":{"useMaxWidth":false}}')

SEC = {}
EST = {}
ACT = {}

# ====================================================================== secuencias
SEC['SQ01_peticion_api_contexto_finca'] = '''sequenceDiagram
  autonumber
  actor U as Usuario (PWA o panel)
  participant N as Nginx
  participant MW as Django · ContextoFincaMiddleware
  participant V as Vista DRF
  participant S as Servicio (caso de uso)
  participant DB as PostgreSQL (rol guayacan_app)
  U->>N: HTTPS con JWT y cabecera X-Predio
  N->>MW: petición
  MW->>MW: valida JWT y que el usuario tenga rol en esa finca
  MW->>DB: BEGIN y set_config(app.predio_id, app.usuario_id, app.agente_id, true)
  MW->>V: request con predio y usuario
  V->>V: serializer valida formato
  V->>S: ejecutar(datos)
  S->>DB: INSERT o UPDATE o SELECT funcion()
  alt la base acepta
    DB-->>S: filas solo de esa finca (RLS)
    S-->>V: resultado
    V-->>U: 200 o 201 con JSON
  else una regla de la base rechaza
    DB-->>S: RAISE EXCEPTION con mensaje en español
    S-->>V: ErrorDeRegla
    V-->>U: 422 con el mensaje de la regla
  end
  MW->>DB: COMMIT o ROLLBACK
'''
SEC['SQ02_inicio_sesion_doble_factor'] = '''sequenceDiagram
  autonumber
  actor U as Usuario
  participant API as Django · auth
  participant DB as PostgreSQL
  participant SEG as seguridad.registrar_intento()
  U->>API: POST /auth/token (correo, contraseña)
  API->>DB: buscar usuario y verificar hash Argon2
  API->>SEG: registrar_intento(correo, ip, exito, motivo)
  alt IP o cuenta bloqueada, o cuenta señuelo
    SEG-->>API: ip_bloqueada, cuenta_bloqueada o senuelo
    API-->>U: 401 genérico (sin decir por qué)
  else fallo número 5 en 15 minutos
    SEG-->>API: cuenta_bloqueada_ahora y alerta alta
    API-->>U: 401 genérico
  else contraseña correcta
    SEG-->>API: aceptado
    API->>DB: requiere_doble_factor(usuario)
    alt administrador, contador o superusuario
      API-->>U: 200 con desafío de segundo factor
      U->>API: POST /auth/doble-factor/verificar (TOTP o llave)
      API->>DB: INSERT sesion_usuario metodo doble_factor, vence en 12 h o menos
    else otros roles
      API->>DB: INSERT sesion_usuario metodo contrasena
    end
    API-->>U: JWT de acceso y de refresco
  end
'''
SEC['SQ03_sincronizacion_sin_conexion'] = '''sequenceDiagram
  autonumber
  actor O as Operario
  participant P as PWA (Angular)
  participant IDB as IndexedDB (Dexie)
  participant SW as Service worker
  participant API as Django · /sincronizacion/lote
  participant DB as PostgreSQL
  O->>P: registra postura sin señal
  P->>IDB: guarda con id_cliente UUIDv7 y capturado_en
  Note over P,IDB: puede capturar cientos de registros sin conexión
  SW->>SW: vuelve la señal (o se abre la app en iPhone)
  SW->>API: POST lote de pendientes
  loop cada registro
    API->>DB: INSERT ... ON CONFLICT (predio_id, id_cliente) DO NOTHING
    alt insertado
      DB-->>API: aceptado
    else ya existía
      DB-->>API: duplicado (cuenta una sola vez)
    else una regla lo rechaza
      DB-->>API: rechazado con el mensaje
    end
  end
  API->>DB: INSERT nucleo.sincronizacion (subidos, rechazados)
  API-->>SW: resultado por registro
  SW->>IDB: borra aceptados y duplicados, marca rechazados
  P-->>O: muestra rechazos para corregir
'''
SEC['SQ04_confirmar_pedido_fefo'] = '''sequenceDiagram
  autonumber
  actor V as Vendedor
  participant API as Django · pedidos
  participant DB as PostgreSQL
  participant OB as nucleo.evento_salida
  participant C as Celery
  participant MG as MongoDB y agentes
  V->>API: POST /pedidos/{id}/confirmar
  API->>DB: SELECT comercial.confirmar_pedido(id)
  DB->>DB: valida borrador, precio vigente y cupo si es a crédito
  loop cada línea del pedido
    DB->>DB: inventario.reservar_fefo(): toma primero el lote que vence antes (FOR UPDATE)
    alt no alcanza el inventario vendible
      DB-->>API: Inventario insuficiente, sin reservas a medias
      API-->>V: 422
    end
  end
  DB->>OB: INSERT pedido.confirmado en la misma transacción
  DB-->>API: pedido confirmado con reservas
  API-->>V: 200
  C->>OB: lee pendientes
  C->>MG: publica en Redis Streams, actualiza perfil de interés
  C->>OB: marca publicado
'''
SEC['SQ05_atencion_whatsapp_agentes'] = '''sequenceDiagram
  autonumber
  actor CL as Cliente
  participant WA as WhatsApp Cloud API
  participant AG as FastAPI · agentes
  participant ORQ as Orquestador
  participant AS as Asesor virtual
  participant MCP as Servidor MCP
  participant API as Django API
  participant MG as MongoDB
  CL->>WA: Hola, ¿tienen huevo AA?
  WA->>AG: webhook firmado
  AG->>MG: guarda mensaje y conversación
  AG->>ORQ: clasifica intención y revisa reglas de conversación
  ORQ->>AS: intención consultar_catalogo
  AS->>MCP: consultar_catalogo()
  MCP->>API: GET catálogo disponible (token del agente)
  API-->>MCP: precio vigente y cantidad vendible
  MCP-->>AS: datos
  AS->>API: verificar envío (ventana de 24 h, consentimiento)
  API-->>AS: permitido
  AS-->>WA: respuesta con precio y disponibilidad
  WA-->>CL: mensaje
  opt el cliente pide comprar
    AS->>MCP: crear_pedido_borrador()
    MCP->>API: POST pedido en borrador
    Note over API: un vendedor lo revisa y confirma (CU VTA-03)
  end
  opt tema no permitido o cliente molesto
    ORQ->>API: crea escalamiento a una persona
  end
'''
SEC['SQ06_cambio_precio_aprobado'] = '''sequenceDiagram
  autonumber
  participant AM as Analista de mercados (IA)
  participant MCP as Servidor MCP
  participant API as Django
  participant DB as PostgreSQL
  actor A as Administrador
  AM->>MCP: consultar_precios_mercado()
  AM->>MCP: proponer_precio(producto, valor, evidencia)
  MCP->>API: POST propuesta de precio
  API->>DB: INSERT propuesta_precio pendiente y solicitud_aprobacion
  DB-->>A: aparece en la bandeja de aprobaciones
  A->>API: POST /propuestas-precio/{id}/aprobar
  API->>DB: SELECT comercial.aplicar_propuesta_precio(id)
  DB->>DB: exigir_persona(), cierra precio vigente y crea el nuevo
  Note over DB: pedidos confirmados conservan su precio congelado
  DB-->>API: aplicada
  API-->>A: 200
'''
SEC['SQ07_tarea_a_nomina'] = '''sequenceDiagram
  autonumber
  participant B as Celery Beat
  participant DB as PostgreSQL
  actor E as Encargado o responsable del área
  actor O as Operario
  actor C as Contador
  B->>DB: personal.generar_tareas_del_dia(fecha)
  DB-->>E: tareas del día sin asignar, con lista de chequeo
  E->>DB: asigna tarea a O
  DB->>DB: validar_tarea(): disponible, habilitado, del área
  O->>DB: en_curso, pasos, foto de evidencia, terminada con cantidad
  E->>DB: aprobada
  DB->>DB: permiso o responsable del área, no la propia
  C->>DB: nomina.preparar_prenomina(periodo)
  DB->>DB: novedad de destajo o jornal desde la tarea aprobada
  C->>DB: nomina.liquidar(periodo)
  DB-->>C: devengado, deducciones, neto y provisiones
'''
SEC['SQ08_cierre_y_pago_nomina'] = '''sequenceDiagram
  autonumber
  actor C as Contador
  actor F as Familia
  actor E as Encargado
  participant DB as PostgreSQL
  C->>DB: causación contable de la nómina (comprobante cuadrado y contabilizado)
  F->>DB: UPDATE periodo estado cerrado, cerrado_por F, aprobado_por C
  DB->>DB: proteger_periodo(): dos personas, ningún agente, comprobante contabilizado
  DB-->>F: periodo cerrado, liquidaciones aprobadas
  C->>DB: INSERT pago_nomina preparado_por C
  F->>DB: aprobado_por F
  alt valor mayor que monto_doble_aprobacion
    E->>DB: segunda_aprobacion_por E (tercera persona)
  end
  C->>DB: pagado_en y referencia de la transferencia
  DB->>DB: marcar_pagada(): liquidación pagada
'''
SEC['SQ09_reserva_cabana'] = '''sequenceDiagram
  autonumber
  actor CL as Cliente
  participant API as Django · turismo
  participant DB as PostgreSQL
  participant PG as Pasarela de pagos
  actor P as Portería
  CL->>API: GET disponibilidad de la cabaña
  API->>DB: agenda.recurso_libre(recurso, desde, hasta)
  CL->>API: POST reserva (fechas, personas)
  API->>DB: INSERT turismo.reserva solicitada
  DB->>DB: validar_reserva(): capacidad y al menos una noche
  CL->>PG: paga el anticipo
  PG->>API: webhook de pago confirmado
  API->>DB: reserva confirmada o pagada
  DB->>DB: sincronizar_agenda(): cita de 15:00 a 12:00 más limpieza
  alt la cabaña ya está ocupada o bloqueada
    DB-->>API: exclusion_violation
    API-->>CL: 409 fechas no disponibles, se reembolsa
  end
  P->>DB: check-in con autorización de datos
  P->>DB: checkout_en
  DB->>DB: crea tarea de limpieza del área de turismo
'''
SEC['SQ10_cadena_frio_bloqueo'] = '''sequenceDiagram
  autonumber
  participant S as Sensor de la nevera
  participant GW as Pasarela IoT local
  participant DB as PostgreSQL
  participant OB as evento_salida
  actor E as Encargado
  participant AG as Agente de IA
  S->>GW: temperatura fuera de rango
  GW->>DB: excursion_temperatura abierta
  loop cada lectura
    DB->>DB: evaluar_excursion(): minutos fuera contra tolerancia
  end
  DB->>DB: supera 30 min: bloqueo_lote de los perecederos de la nevera
  DB->>OB: lote.bloqueado y temperatura.fuera_de_rango
  OB-->>E: aviso push y en el panel
  AG->>DB: intenta liberar el lote
  DB-->>AG: Solo una persona decide sobre un lote bloqueado
  E->>DB: decisión liberado o descartado con observación
  DB->>DB: aplicar_bloqueo(): queda quién y cuándo, la decisión no cambia
'''
SEC['SQ11_iniciativa_a_proyecto'] = '''sequenceDiagram
  autonumber
  participant ES as Estratega (IA)
  actor F as Familia
  participant DB as PostgreSQL
  actor D as Director del proyecto
  ES->>DB: consulta v_matriz_lineas y estados financieros
  ES->>DB: INSERT iniciativa estado idea (desarrollo de mercado HORECA)
  F->>DB: evaluación: inversión, precio, costo variable, fijos, unidades
  F->>DB: estrategia.evaluar_proyecto(id)
  DB-->>F: VPN, TIR, ROI, recuperación, equilibrio, palancas
  F->>DB: iniciativa aprobada (solo con evaluación calculada)
  F->>DB: reinversion desde la línea avícola
  DB->>DB: validar_reinversion(): utilidad positiva y tope del 30 %
  D->>DB: proyecto ligado a la iniciativa (acta)
  F->>DB: aprueba como patrocinador, nace la línea base 1
'''
SEC['SQ12_cronograma_24_7'] = '''sequenceDiagram
  autonumber
  actor E as Encargado
  participant CO as Coordinador (IA)
  participant DB as PostgreSQL
  actor O as Trabajadores
  O->>DB: disponibilidad y ausencias
  E->>DB: cronograma en borrador del área de vigilancia
  E->>DB: asignación de patrón cíclico con desfase por persona
  E->>DB: personal.generar_turnos(cronograma)
  DB->>DB: validar_turno() en cada turno: cruces, descanso, máximo diario
  CO->>DB: consulta huecos y propone ajustes
  E->>DB: personal.huecos_cobertura(cronograma)
  DB-->>E: horas sin cobertura
  E->>DB: agrega turnos que faltan
  E->>DB: cronograma publicado
  DB->>DB: publicar_cronograma(): 42 h + extras, descanso cada 7 días, sin huecos
  DB-->>O: turnos visibles en la app
'''
SEC['SQ13_riego_automatico_local'] = '''sequenceDiagram
  autonumber
  participant HS as Sensor de humedad
  participant TQ as Sensor de nivel del tanque
  participant GW as Pasarela local (reglas)
  participant EV as Electroválvula V-03
  participant EM as Estación meteorológica
  participant API as Django (cuando hay internet)
  HS->>GW: MQTT humedad 27 %
  TQ->>GW: MQTT tanque 55 %
  EM->>GW: llovió en las últimas horas
  GW->>GW: regla: humedad menor a 30 y tanque mayor a 40 y no llovió
  GW->>EV: abrir
  EV-->>GW: abierta
  GW->>GW: cierra al cumplir el tiempo o el volumen
  GW->>API: sube comando_actuador, lecturas y evento_riego al volver la conexión
  Note over GW: funciona sin internet, la regla vive en la pasarela
'''
SEC['SQ14_visita_porteria'] = '''sequenceDiagram
  autonumber
  actor V as Visitante o proveedor
  actor E as Encargado (anfitrión)
  participant DB as PostgreSQL
  actor P as Portería (PWA sin internet)
  V->>E: pide visita (hora, placa, zona)
  E->>DB: visita aprobada
  DB-->>E: si va al galpón exige declarar 72 h sin contacto con aves
  E->>DB: agenda.emitir_pase()
  DB-->>V: código QR (la base guarda solo la huella)
  V->>P: llega con el QR
  P->>DB: registro_acceso entrada (placa, desinfección)
  DB-->>P: rechaza placa distinta, fuera de horario o sin desinfección
  P->>DB: salida
  DB->>DB: visita salió, deja de aparecer en v_en_sitio
'''
SEC['SQ15_captura_prospecto'] = '''sequenceDiagram
  autonumber
  actor PR as Posible cliente
  participant F as Formulario web o QR en feria
  participant API as Django · CRM
  participant DB as PostgreSQL
  actor V as Vendedor
  PR->>F: datos y casilla de autorización con su finalidad
  F->>API: POST /crm/captura/{formulario}
  API->>DB: INSERT consentimiento_datos y prospecto
  DB->>DB: validar_prospecto(): persona con contacto exige autorización
  V->>DB: interacción whatsapp
  DB->>DB: validar_interaccion(): no se contacta sin autorización vigente
  V->>DB: crm.calificar(id)
  DB-->>V: puntaje 0 a 100
  V->>DB: crm.convertir_prospecto(id, segmento)
  DB-->>V: tercero y cliente creados, etapa ganado
'''

# ====================================================================== estados
EST['ST01_pedido'] = '''stateDiagram-v2
  [*] --> borrador: vendedor, cliente o agente
  borrador --> confirmado: confirmar_pedido() reserva FEFO
  borrador --> cancelado
  confirmado --> en_preparacion: empaque
  confirmado --> despachado: despachar_pedido()
  en_preparacion --> despachado: despachar_pedido()
  confirmado --> cancelado: cancelar_pedido() libera reservas
  en_preparacion --> cancelado: cancelar_pedido()
  despachado --> entregado: entrega entregada
  entregado --> [*]
  cancelado --> [*]
  note right of despachado: ya salió de la finca, no se cancela, se devuelve
'''
EST['ST02_lote_inventario'] = '''stateDiagram-v2
  [*] --> disponible: entrada por kardex
  disponible --> agotado: cantidad llega a cero
  disponible --> vencido: marcar_vencidos() pasada la fecha
  disponible --> bloqueado: excursión de frío, retiro o persona
  bloqueado --> disponible: una persona lo libera
  bloqueado --> vencido: una persona lo descarta
  agotado --> [*]
  vencido --> [*]: merma con causa
  note right of disponible: solo se vende si puede_venderse() antes de su fecha límite
'''
EST['ST03_tarea'] = '''stateDiagram-v2
  [*] --> pendiente: plan, manual, agente, orden, acción correctiva, proyecto, agenda
  pendiente --> en_curso: el trabajador inicia
  en_curso --> terminada: cantidad y evidencia
  terminada --> aprobada: encargado o responsable del área
  terminada --> devuelta: con comentario
  devuelta --> en_curso
  pendiente --> cancelada
  en_curso --> cancelada
  aprobada --> [*]: genera novedad de jornal o destajo
  cancelada --> [*]
  note right of aprobada: no se edita, nadie aprueba la propia
'''
EST['ST04_periodo_nomina'] = '''stateDiagram-v2
  [*] --> abierto
  abierto --> prenomina: preparar_prenomina()
  prenomina --> prenomina: liquidar()
  prenomina --> cerrado: dos personas y comprobante contabilizado
  abierto --> anulado
  prenomina --> anulado
  cerrado --> [*]: correcciones por nota de ajuste
  anulado --> [*]
'''
EST['ST05_comprobante'] = '''stateDiagram-v2
  [*] --> borrador: lo generan reglas o el contador
  borrador --> contabilizado: débitos = créditos y periodo abierto
  contabilizado --> anulado: solo con motivo
  borrador --> [*]
  anulado --> [*]
  note right of contabilizado: movimientos inmutables, correcciones con nota contable
'''
EST['ST06_propuesta_precio'] = '''stateDiagram-v2
  [*] --> pendiente: la crea el analista de mercados (IA)
  pendiente --> aprobada: administrador
  pendiente --> rechazada: administrador
  pendiente --> vencida: pasa su fecha
  aprobada --> aplicada: aplicar_propuesta_precio()
  aplicada --> [*]
  rechazada --> [*]
  vencida --> [*]
'''
EST['ST07_reserva_turistica'] = '''stateDiagram-v2
  [*] --> solicitada
  solicitada --> confirmada: ocupa la agenda sin cruces
  solicitada --> pagada: pago anticipado
  confirmada --> pagada
  confirmada --> cancelada: libera la agenda
  pagada --> cancelada: según la política de reembolso
  pagada --> cumplida: checkout crea la limpieza
  confirmada --> cumplida
  cumplida --> [*]
  cancelada --> [*]
'''
EST['ST08_visita'] = '''stateDiagram-v2
  [*] --> solicitada
  solicitada --> aprobada: persona, bioseguridad declarada si va al galpón
  solicitada --> rechazada: con motivo
  aprobada --> en_sitio: entrada en portería dentro del horario
  aprobada --> no_llego
  aprobada --> cancelada
  en_sitio --> salio: salida en portería
  salio --> [*]
  rechazada --> [*]
  no_llego --> [*]
  cancelada --> [*]
'''
EST['ST09_proyecto'] = '''stateDiagram-v2
  [*] --> propuesto: acta en borrador
  propuesto --> aprobado: patrocinador, nace línea base 1
  aprobado --> en_curso
  en_curso --> suspendido
  suspendido --> en_curso
  en_curso --> cerrado: entregables aceptados y lecciones aprendidas
  propuesto --> cancelado
  aprobado --> cancelado
  en_curso --> cancelado
  cerrado --> [*]
  cancelado --> [*]
'''
EST['ST10_iniciativa'] = '''stateDiagram-v2
  [*] --> idea: persona o Estratega (IA)
  idea --> en_evaluacion: se arma la evaluación
  en_evaluacion --> aprobada: VPN, TIR y ROI calculados, decide la familia
  en_evaluacion --> descartada
  aprobada --> piloto
  piloto --> escalada: el retorno real lo justifica
  piloto --> descartada
  escalada --> [*]
  descartada --> [*]
'''
EST['ST11_prospecto'] = '''stateDiagram-v2
  [*] --> nuevo: captura con autorización
  nuevo --> contactado: primera interacción
  contactado --> calificado
  calificado --> propuesta
  propuesta --> negociacion
  negociacion --> ganado: convertir_prospecto() crea el cliente
  contactado --> perdido: con motivo
  calificado --> perdido: con motivo
  propuesta --> perdido: con motivo
  negociacion --> perdido: con motivo
  nuevo --> descartado
  ganado --> [*]
  perdido --> [*]
  descartado --> [*]
'''
EST['ST12_cronograma'] = '''stateDiagram-v2
  [*] --> borrador
  borrador --> borrador: generar_turnos() y ajustes a mano
  borrador --> publicado: jornada, descanso semanal y cobertura cumplen
  publicado --> cerrado: termina el periodo
  cerrado --> [*]
'''
EST['ST13_mision_robot'] = '''stateDiagram-v2
  [*] --> propuesta: función dron_monitoreo o robot_campo encendida
  propuesta --> aprobada: una persona
  aprobada --> en_curso: dron registrado, piloto, póliza, 122 m o robot sin personas
  en_curso --> terminada
  en_curso --> abortada: parada de emergencia
  propuesta --> abortada
  terminada --> [*]
  abortada --> [*]
'''
EST['ST14_alarma'] = '''stateDiagram-v2
  [*] --> desarmado
  desarmado --> armado
  desarmado --> noche
  armado --> desarmado
  noche --> desarmado
  armado --> noche
  noche --> armado
  desarmado --> mantenimiento: solo desde desarmado
  mantenimiento --> desarmado
  note right of armado: solo cambia con iot.cambiar_estado_alarma(), con historial
'''
EST['ST15_alerta_seguridad'] = '''stateDiagram-v2
  [*] --> nueva: detector, señuelo o vigilancia de privilegios
  nueva --> en_analisis: atendida_por queda registrado
  en_analisis --> contenida
  en_analisis --> falso_positivo
  contenida --> cerrada
  falso_positivo --> cerrada
  cerrada --> [*]
  note right of nueva: la API no puede cambiar severidad ni borrarla
'''
EST['ST16_siembra'] = '''stateDiagram-v2
  [*] --> planeada
  planeada --> sembrada
  sembrada --> en_produccion
  sembrada --> recuperacion: mortalidad alta, resiembra
  recuperacion --> en_produccion
  recuperacion --> perdida
  en_produccion --> finalizada
  perdida --> [*]
  finalizada --> [*]
'''
EST['ST17_solicitud_aprobacion'] = '''stateDiagram-v2
  [*] --> pendiente: un agente pide permiso
  pendiente --> aprobada: una persona
  pendiente --> rechazada: una persona
  pendiente --> vencida
  aprobada --> ejecutada
  aprobada --> fallida
  ejecutada --> [*]
  fallida --> [*]
  rechazada --> [*]
  vencida --> [*]
'''

# ====================================================================== actividades
ACT['AC01_tareas_programadas_diarias'] = '''flowchart TD
  A([Celery Beat 00:30]) --> B[nucleo.mantener_particiones]
  B --> C[inventario.marcar_vencidos]
  C --> D[formacion.actualizar_habilitaciones]
  D --> E[activos.generar_ordenes_trabajo]
  E --> F[personal.generar_tareas_del_dia]
  F --> G{pedidos_recurrentes encendida?}
  G -- sí --> H[comercial.generar_pedidos_recurrentes]
  G -- no --> I
  H --> I[cumplimiento.evaluar_expediente por expediente]
  I --> J[seguridad.revisar_copias]
  J --> K{seguro_parametrico encendida?}
  K -- sí --> L[seguros.vigilar_indice por póliza]
  K -- no --> M
  L --> M[iot.depurar_clips]
  M --> N[comercial.actualizar_mora]
  N --> O([Fin: resumen al administrador])
'''
ACT['AC02_cierre_mensual'] = '''flowchart TD
  A([Último día del mes]) --> B[Contador revisa comprobantes en borrador]
  B --> C[activos.depreciar_mes]
  C --> D[finanzas.distribuir_costos por actividades]
  D --> E[Causación de nómina contabilizada]
  E --> F{¿Todo cuadra?}
  F -- no --> B
  F -- sí --> G[finanzas.calcular_indicadores del mes]
  G --> H[estado_financiero congelado: resultados y balance]
  H --> I[Familia revisa tablero y semáforos]
  I --> J[Cerrar periodo contable]
  J --> K([Mes siguiente abierto])
'''
ACT['AC03_mejora_continua_phva'] = '''flowchart LR
  P[Planear: Analista de negocio propone recomendación con evidencia] --> H[Hacer: persona acepta y crea tareas o iniciativa]
  H --> V[Verificar: indicadores del periodo contra meta]
  V --> A{¿Cumplió?}
  A -- sí --> E[Actuar: estandarizar en plan de labores o documento]
  A -- no --> R[Actuar: ajustar o descartar con lección aprendida]
  E --> P
  R --> P
'''
ACT['AC04_flujo_de_una_historia'] = '''flowchart TD
  A([Historia del backlog con su CU]) --> B[Leer especificación, estados y secuencia]
  B --> C[Escribir prueba de la regla en SQL si es nueva]
  C --> D[Modelo Django managed=False y serializer]
  D --> E[Servicio del caso de uso y vista DRF]
  E --> F[Pruebas pytest de la API contra la base de pruebas]
  F --> G[Pantalla Angular y estados de botones]
  G --> H{¿Pasa CI: ruff, pytest, SQL, lint y build?}
  H -- no --> C
  H -- sí --> I[Revisión de código por otra persona]
  I --> J{¿Cumple la definición de terminado?}
  J -- no --> C
  J -- sí --> K([Fusión a main y despliegue a pruebas])
'''


def render(nombre, codigo, carpeta):
    """Guarda el código Mermaid (.mmd) en la carpeta indicada y lo convierte a .svg y .png con mmdc (Mermaid CLI)."""
    d = os.path.join(DEST, carpeta)
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, nombre)
    open(base + '.mmd', 'w', encoding='utf-8').write(codigo)
    subprocess.run(['mmdc', '-q', '-i', base + '.mmd', '-o', base + '.svg', '-c', CFG, '-b', 'white'], check=True, capture_output=True)
    subprocess.run(['mmdc', '-q', '-i', base + '.mmd', '-o', base + '.png', '-c', CFG, '-b', 'white', '-w', '1400', '-s', '1.4'],
                   check=True, capture_output=True)


if __name__ == '__main__':
    for grupo, carpeta in ((SEC, 'secuencia'), (EST, 'estados'), (ACT, 'actividad')):
        for n, c in grupo.items():
            try:
                render(n, c, carpeta)
                print('ok', n)
            except subprocess.CalledProcessError as e:
                print('ERROR', n, e.stderr.decode()[-400:])
