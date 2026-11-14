"""Catálogo de casos de uso de GuayacanERP v5: fuente única de los diagramas de casos de uso y de la trazabilidad.

Cada caso: id, nombre, módulo (esquema), actores primarios, actores secundarios, fase, requerimientos,
tablas principales, reglas en la base (funciones o disparadores), acciones de API, áreas de prueba,
include, extend y función por finca (feature flag) que lo enciende.
"""

ACTORES = {
    # personas
    'USR': 'Usuario autenticado', 'ADM': 'Administrador', 'FAM': 'Familia', 'ENC': 'Encargado de finca',
    'OPE': 'Operario de campo', 'VEN': 'Vendedor', 'CON': 'Contador', 'CLI': 'Cliente', 'PRO': 'Posible cliente',
    'VIS': 'Visitante o turista', 'POR': 'Portería', 'INS': 'Instructor', 'EST': 'Estudiante', 'DIR': 'Director de proyecto',
    'PAT': 'Patrocinador', 'AUD': 'Auditor externo', 'TIT': 'Titular de datos', 'OPR': 'Operador turístico o institución',
    'AUT': 'Autoridad o planta de beneficio (CAR, ICA, INVIMA)',
    'ADP': 'Adoptante',  # Apéndice A: turista o comprador en línea dueño de un árbol o animal
    # sistemas externos y procesos automáticos
    'SCH': 'Tareas programadas', 'GW': 'Pasarela IoT local', 'DIAN': 'DIAN', 'CAN': 'Canales de mensajería',
    'PAG': 'Pasarela de pagos', 'B2B': 'Sistema del cliente B2B', 'MER': 'Fuentes de mercado', 'ASE': 'Aseguradora',
    'CI': 'Integración continua', 'NOT': 'Correo y SMS', 'MOO': 'Plataforma de cursos', 'EST_M': 'Estación meteorológica',
    # agentes de IA (proponen, no deciden)
    'AG_ORQ': 'Orquestador (IA)', 'AG_ASE': 'Asesor virtual (IA)', 'AG_GUI': 'Guía virtual (IA)', 'AG_VEP': 'Vendedor personalizado (IA)',
    'AG_RED': 'Gestor de redes (IA)', 'AG_MER': 'Analista de mercados (IA)', 'AG_NEG': 'Analista de negocio (IA)',
    'AG_CON': 'Asistente contable (IA)', 'AG_AGR': 'Agrónomo (IA)', 'AG_COO': 'Coordinador (IA)', 'AG_INS': 'Instructor (IA)',
    'AG_EST': 'Estratega (IA)', 'AG_VIG': 'Vigía de seguridad (IA)', 'AG_PRY': 'Asistente de proyectos (IA)',
}
HUMANOS = {'USR', 'ADM', 'FAM', 'ENC', 'OPE', 'VEN', 'CON', 'CLI', 'PRO', 'VIS', 'POR', 'INS', 'EST', 'DIR', 'PAT', 'AUD', 'TIT', 'OPR', 'ADP'}

MODULOS = {
    'nucleo': 'Núcleo de la plataforma', 'seguridad': 'Seguridad informática', 'terceros': 'Terceros y datos personales',
    'documental': 'Gestión documental', 'produccion': 'Producción animal y agrícola', 'riego': 'Riego', 'iot': 'IoT, seguridad perimetral y robótica',
    'ambiental': 'Ambiental', 'inventario': 'Inventario y cadena de frío', 'compras': 'Compras', 'activos': 'Activos y mantenimiento',
    'comercial': 'Ventas', 'crm': 'Clientes potenciales (CRM)', 'redes': 'Canales y redes sociales', 'turismo': 'Turismo',
    'agenda': 'Agenda y portería', 'personal': 'Personal, tareas y turnos', 'formacion': 'Formación', 'nomina': 'Nómina',
    'finanzas': 'Finanzas y contabilidad', 'estrategia': 'Estrategia de negocio', 'proyectos': 'Proyectos (PMBOK 8)',
    'seguros': 'Seguros', 'cumplimiento': 'Cumplimiento y certificaciones', 'ia': 'Inteligencia artificial',
    'adopcion': 'Adopción de árboles y animales',  # Apéndice A
}
PREFIJO = {'nucleo': 'NUC', 'seguridad': 'SEG', 'terceros': 'TER', 'documental': 'DOC', 'produccion': 'PRO', 'riego': 'RIE', 'iot': 'IOT',
           'ambiental': 'AMB', 'inventario': 'INV', 'compras': 'CMP', 'activos': 'ACT', 'comercial': 'VTA', 'crm': 'CRM', 'redes': 'RED',
           'turismo': 'TUR', 'agenda': 'AGD', 'personal': 'PER', 'formacion': 'FOR', 'nomina': 'NOM', 'finanzas': 'FIN',
           'estrategia': 'EST', 'proyectos': 'PRY', 'seguros': 'SGR', 'cumplimiento': 'CUM', 'ia': 'IA',
           'adopcion': 'ADO'}

# Pestañas del documento: grupos de módulos por área del negocio
GRUPOS = [
    ('1 · Plataforma y seguridad', ['nucleo', 'seguridad', 'terceros', 'documental']),
    ('2 · Producción y campo', ['produccion', 'riego', 'iot', 'ambiental']),
    ('3 · Inventario, compras y activos', ['inventario', 'compras', 'activos']),
    ('4 · Ventas, clientes y turismo', ['comercial', 'crm', 'redes', 'turismo', 'agenda', 'adopcion']),
    ('5 · Personas', ['personal', 'formacion', 'nomina']),
    ('6 · Dinero y decisiones', ['finanzas', 'estrategia', 'proyectos', 'seguros']),
    ('7 · Cumplimiento e inteligencia artificial', ['cumplimiento', 'ia']),
]

# Requerimientos: RF/RNF del documento de requerimientos v1.0 y los agregados en las versiones 2 a 5 (RQ)
REQUERIMIENTOS = {
    'RF-01': 'Registro e inicio de sesión', 'RF-02': 'Gestión basada en roles', 'RF-03': 'Autenticación segura (JWT) y recuperación de contraseña',
    'RF-04': 'Lotes y cultivos georreferenciados', 'RF-05': 'Registro de labores culturales', 'RF-06': 'Trazabilidad con código QR por lote',
    'RF-07': 'Inventario vivo: mortalidad, resiembra y plantas vivas', 'RF-08': 'Bioinsumos: compost, humus y lixiviados',
    'RF-09': 'Catálogo con precios por canal', 'RF-10': 'Pedidos de clientes recurrentes y finales', 'RF-11': 'Control de cartera y bloqueo por mora',
    'RF-12': 'Punto de venta móvil sin conexión', 'RF-13': 'Calendario de disponibilidad turística', 'RF-14': 'Reservas en línea con pago anticipado',
    'RF-15': 'Gestión de grupos', 'RF-16': 'Check-in digital con consentimiento', 'RF-17': 'Tablero financiero por línea',
    'RF-18': 'Reportes de producción y costo por kilogramo', 'RF-19': 'Reportes de sostenibilidad', 'RF-20': 'Notificaciones automáticas',
    'RF-21': 'Pasarela de pagos', 'RF-22': 'Georreferenciación y mapa de la finca',
    'RNF-01': 'Crecimiento modular', 'RNF-02': 'Respuesta de la API menor a 2 segundos', 'RNF-03': 'Operación sin conexión (PWA)',
    'RNF-04': 'Ley 1581 de protección de datos', 'RNF-05': 'Cifrado en tránsito y en reposo', 'RNF-06': 'Copias de seguridad diarias',
    'RNF-07': 'Interfaz responsiva para campo', 'RNF-08': 'Español de Colombia y términos agrarios locales', 'RNF-09': 'Identidad visual de la marca',
    'RNF-10': 'Disponibilidad del 99 %', 'RNF-11': 'Código documentado (PEP 8, ESLint)', 'RNF-12': 'Bajo costo inicial y escalado a Kubernetes',
    'RNF-13': 'Reportes para el Fondo Emprender', 'RNF-14': 'Economía circular: residuos y energía',
    'RQ-23': 'Agentes de IA que proponen y una persona decide', 'RQ-24': 'Atención por WhatsApp, Instagram, Messenger y TikTok',
    'RQ-25': 'Riego e IoT en red local', 'RQ-26': 'Seguridad perimetral y cámaras', 'RQ-27': 'Inventario perecedero, FEFO y cadena de frío',
    'RQ-28': 'Tareas, áreas de responsabilidad y evidencias', 'RQ-29': 'Nómina con salario, jornal y destajo', 'RQ-30': 'Formación, cursos y habilitaciones',
    'RQ-31': 'Activos y mantenimiento', 'RQ-32': 'Gestión documental', 'RQ-33': 'Cumplimiento y certificaciones (ICA, BPA, GLOBALG.A.P., ISO 21001)',
    'RQ-34': 'Seguros', 'RQ-35': 'Seguridad informática: detector de ataques, doble factor y pruebas', 'RQ-36': 'Captura de clientes potenciales (CRM)',
    'RQ-37': 'Estrategia de negocio y reinversión con retorno calculado', 'RQ-38': 'Costos, presupuesto, estados e indicadores financieros',
    'RQ-39': 'Agenda de cabañas, visitas y portería', 'RQ-40': 'Cronograma de trabajo flexible 24/7', 'RQ-41': 'Dirección de proyectos (PMBOK 8)',
    'RQ-42': 'Robótica y drones', 'RQ-43': 'Integraciones externas (API B2B, webhooks)', 'RQ-44': 'Ambiental y CO₂ estimado con fuente',
    # Apéndice A · adopción
    'RQ-45': 'Venta de árboles y animales con sitio asignado, modalidad de siembra y consentimiento para videos',
    'RQ-46': 'Cuota mensual de cuidado, mora y readopción con 3 cuotas vencidas',
    'RQ-47': 'Productos y liquidación por cuenta del adoptante con 5 % de comisión y soporte legal',
    'RQ-48': 'Seguimiento del bien, reposición en garantía y cesión',
}

CU = []


def cu(id, nombre, act, sec, fase, rf, tablas, reglas, acc, pruebas, inc=(), ext=(), flag=None):
    """Registra un caso de uso en la lista CU. El módulo se deduce del prefijo del id (p. ej. ADO-03 → adopcion).

    act y sec son códigos de actores; rf, requerimientos; tablas, reglas, acc y pruebas alimentan la trazabilidad;
    inc y ext son las relaciones «include» y «extend» del diagrama; flag es la función por finca que lo enciende."""
    mod = next(m for m, p in PREFIJO.items() if id.startswith(p + '-'))
    CU.append(dict(id=id, nombre=nombre, modulo=mod, actores=list(act), secundarios=list(sec), fase=fase, rf=list(rf),
                   tablas=list(tablas), reglas=list(reglas), acciones=list(acc), pruebas=list(pruebas), inc=list(inc),
                   ext=list(ext), flag=flag))


# ------------------------------------------------------------------ nucleo
cu('NUC-01', 'Configurar la finca, sus zonas y el mapa', ['ADM'], [], 1, ['RF-04', 'RF-22', 'RNF-01'],
   ['nucleo.predio', 'nucleo.zona'], ['nucleo.predio_actual()'], ['GET /api/v1/nucleo/zonas/?formato=geojson'], ['v4:RLS', 'v4:Llave compuesta'])
cu('NUC-02', 'Gestionar usuarios, roles y permisos', ['ADM'], [], 1, ['RF-01', 'RF-02'],
   ['nucleo.usuario', 'nucleo.rol', 'nucleo.permiso', 'nucleo.usuario_rol', 'nucleo.rol_permiso'],
   ['seguridad.vigilar_privilegios()', 'nucleo.tiene_permiso()'], [], ['v5:Seguridad'], ext=['SEG-04'])
cu('NUC-03', 'Administrar parámetros con vigencia', ['ADM', 'CON'], [], 1, ['RNF-01'],
   ['nucleo.parametro'], ['nucleo.parametro_valor()', 'nucleo.parametro_texto()'], [], ['v5:Nómina'])
cu('NUC-04', 'Encender o apagar una función de la finca', ['ADM'], [], 1, ['RNF-01'],
   ['nucleo.funcionalidad'], ['nucleo.exigir_funcion()'], [], ['v4:Funciones', 'v4:Listo para crecer'])
cu('NUC-05', 'Sincronizar registros capturados sin conexión', ['OPE', 'VEN'], [], 1, ['RNF-03', 'RF-12'],
   ['nucleo.sincronizacion', 'nucleo.dispositivo_captura'], ['ON CONFLICT (predio_id, id_cliente) DO NOTHING'],
   ['POST /api/v1/sincronizacion/lote/'], ['v4:Sin conexión'])
cu('NUC-06', 'Consultar la auditoría de cambios', ['ADM', 'CON', 'AUD'], [], 1, ['RNF-04', 'RNF-13'],
   ['nucleo.auditoria'], ['nucleo.auditar()'], ['GET /api/v1/nucleo/auditoria/?tabla=&registro='], ['v4:Auditoría', 'v4:Particiones'])
cu('NUC-07', 'Registrar una nota de voz en campo y confirmarla', ['OPE'], ['AG_ORQ'], 2, ['RNF-03', 'RNF-07'],
   ['nucleo.nota_voz'], [], ['POST /api/v1/nucleo/notas-voz/{id}/confirmar/'], [], inc=['NUC-05'], flag='notas_voz')
cu('NUC-08', 'Practicar en la finca de aprendizaje', ['EST', 'INS'], [], 1, ['RNF-11'],
   ['nucleo.predio', 'nucleo.funcionalidad'], ['nucleo.predios_del_usuario()'], [], ['v4:Práctica'], flag='modo_aprendiz')
cu('NUC-09', 'Publicar los eventos de integración', ['SCH'], ['NOT'], 1, ['RF-20'],
   ['nucleo.evento_salida'], ['patrón outbox'], [], ['v4:Frío'])
cu('NUC-10', 'Administrar llaves de API B2B y webhooks', ['ADM'], ['B2B'], 3, ['RQ-43'],
   ['nucleo.llave_api', 'nucleo.webhook_suscripcion', 'nucleo.webhook_entrega'],
   ['nucleo.validar_llave_api()', 'nucleo.autenticar_llave_api()', 'nucleo.validar_webhook()'],
   ['GET /api/b2b/v1/catalogo/', 'POST /api/b2b/v1/pedidos/'], ['v5:Integración'], flag='api_b2b')

# ------------------------------------------------------------------ seguridad
cu('SEG-01', 'Iniciar sesión con doble factor', ['USR'], [], 1, ['RF-01', 'RF-03', 'RQ-35'],
   ['seguridad.intento_acceso', 'seguridad.sesion_usuario', 'seguridad.factor_autenticacion'],
   ['seguridad.registrar_intento()', 'seguridad.requiere_doble_factor()', 'seguridad.validar_sesion()'],
   ['POST /api/v1/auth/token/', 'POST /api/v1/auth/doble-factor/verificar/'], ['v5:Seguridad'], inc=['SEG-03'])
cu('SEG-02', 'Inscribir el segundo factor y recuperar la contraseña', ['USR'], ['NOT'], 1, ['RF-03', 'RQ-35'],
   ['seguridad.factor_autenticacion'], [], ['POST /api/v1/auth/doble-factor/inscribir/', 'POST /api/v1/auth/recuperar/'], ['v5:Seguridad'])
cu('SEG-03', 'Detectar y bloquear ataques de acceso', ['SCH'], ['AG_VIG'], 1, ['RQ-35'],
   ['seguridad.regla_deteccion', 'seguridad.bloqueo', 'seguridad.senuelo', 'seguridad.alerta_seguridad'],
   ['seguridad.registrar_intento()', 'seguridad.vigilar_exportaciones()', 'seguridad.ip_bloqueada()', 'seguridad.cuenta_bloqueada()'],
   [], ['v5:Seguridad', 'v5:Integración'])
cu('SEG-04', 'Atender una alerta o un incidente de seguridad', ['ADM'], ['AG_VIG'], 1, ['RQ-35', 'RNF-04'],
   ['seguridad.alerta_seguridad', 'seguridad.incidente'], ['seguridad.proteger_alerta()'],
   ['GET /api/v1/seguridad/tablero/'], ['v5:Seguridad'])
cu('SEG-05', 'Revocar sesiones y levantar bloqueos', ['ADM'], [], 1, ['RQ-35'],
   ['seguridad.sesion_usuario', 'seguridad.bloqueo'], ['seguridad.revocar_sesiones()'],
   ['POST /api/v1/seguridad/sesiones/{id}/revocar/', 'POST /api/v1/seguridad/bloqueos/{id}/levantar/'], ['v5:Seguridad'])
cu('SEG-06', 'Registrar una corrida de pruebas', ['CI'], [], 1, ['RNF-11', 'RQ-35'],
   ['seguridad.ejecucion_prueba'], ['solo inserción'], ['POST /api/v1/seguridad/ejecuciones-prueba/'], ['v5:Seguridad'])
cu('SEG-07', 'Verificar copias de seguridad y restauraciones', ['SCH', 'ADM'], [], 1, ['RNF-06', 'RNF-05'],
   ['seguridad.copia_seguridad'], ['seguridad.revisar_copias()'], [], ['v5:Seguridad'])

# ------------------------------------------------------------------ terceros
cu('TER-01', 'Registrar un tercero (persona o empresa)', ['VEN', 'CON', 'ADM'], [], 1, ['RF-10'],
   ['terceros.tercero'], [], [], ['v4:RLS'])
cu('TER-02', 'Registrar y revocar una autorización de datos', ['CLI', 'VEN'], [], 1, ['RNF-04'],
   ['terceros.consentimiento_datos'], ['crm.consentimiento_vigente()', 'redes.verificar_envio()'], [], ['v4:WhatsApp', 'v5:CRM'])
cu('TER-03', 'Atender una solicitud del titular de datos', ['TIT'], ['ADM'], 1, ['RNF-04'],
   ['terceros.consentimiento_datos', 'terceros.tercero'], [], ['GET /api/v1/terceros/{id}/datos-personales/'], [])
cu('TER-04', 'Gestionar clientes, proveedores y empleados', ['ADM', 'CON', 'VEN'], [], 1, ['RF-10'],
   ['terceros.cliente', 'terceros.proveedor', 'terceros.empleado'], [], [], ['v4:Crédito', 'v5:Nómina'])

# ------------------------------------------------------------------ documental
cu('DOC-01', 'Publicar un documento con versión aprobada', ['ENC', 'ADM'], [], 1, ['RQ-32'],
   ['documental.documento', 'documental.version_documento'], ['documental.validar_version()', 'documental.obsoletar_anteriores()'],
   [], ['v5:Documental'])
cu('DOC-02', 'Vincular documentos y vigilar vencimientos', ['SCH', 'ENC'], [], 1, ['RQ-32', 'RQ-33'],
   ['documental.vinculo_documento', 'documental.documento'], ['documental.v_vigentes'], ['GET /api/v1/documental/vigentes/'], ['v5:Documental'])
cu('DOC-03', 'Consultar documentos vigentes', ['USR'], ['AG_INS', 'AG_AGR'], 1, ['RQ-32', 'RQ-23'],
   ['documental.version_documento'], ['documental.documento_para_agente()'], ['GET /api/v1/documental/vigentes/'], ['v5:Documental'])

# ------------------------------------------------------------------ produccion
cu('PRO-01', 'Registrar el ingreso de un lote de animales', ['ENC', 'OPE'], [], 1, ['RF-07'],
   ['produccion.lote_animal', 'produccion.animal', 'produccion.especie'], ['cumplimiento.v_granja_biosegura'], [], ['v5:Cumplimiento'], inc=['NUC-05'])
cu('PRO-02', 'Registrar la postura diaria y clasificar el huevo', ['OPE'], ['GW'], 1, ['RF-06', 'RF-18'],
   ['produccion.registro_postura', 'produccion.clasificacion_postura', 'produccion.categoria_huevo'],
   ['produccion.validar_clasificacion()'], [], ['v4:Huevo'], inc=['NUC-05'])
cu('PRO-03', 'Registrar alimentación, pesajes y eventos sanitarios', ['OPE'], [], 1, ['RF-07', 'RF-18'],
   ['produccion.registro_alimentacion', 'produccion.registro_pesaje', 'produccion.evento_sanitario'], [], [], [], inc=['NUC-05'])
cu('PRO-04', 'Registrar eventos reproductivos de ovinos y caprinos', ['OPE'], [], 1, ['RF-07'],
   ['produccion.evento_reproductivo', 'produccion.animal'], [], [], [], inc=['NUC-05'])
cu('PRO-05', 'Registrar una siembra y sus labores culturales', ['OPE', 'ENC'], [], 1, ['RF-04', 'RF-05', 'RF-07'],
   ['produccion.siembra', 'produccion.labor_cultural', 'produccion.cultivo'], ['ck labor por robot exige misión'], [], ['v5:Robótica'], inc=['NUC-05'])
cu('PRO-06', 'Registrar una cosecha y su destino', ['OPE'], [], 1, ['RF-06', 'RF-18'],
   ['produccion.cosecha', 'inventario.lote_inventario'], ['inventario.entrada_inicial()', 'comercial.registrar_huella()'], [], ['v4:Kardex', 'v4:Huellas'], inc=['INV-02'])
cu('PRO-07', 'Registrar un análisis de suelo y su recomendación', ['ENC'], ['AG_AGR'], 1, ['RF-04'],
   ['produccion.analisis_suelo'], [], [], ['v5:Cumplimiento'])
cu('PRO-08', 'Registrar bioseguridad e inocuidad', ['OPE'], [], 1, ['RQ-33'],
   ['produccion.registro_bioseguridad'], ['cumplimiento.evaluar_expediente()'], [], ['v5:Cumplimiento'], inc=['NUC-05'])
cu('PRO-09', 'Producir abono en lombricultivo o compostera', ['OPE'], [], 1, ['RF-08', 'RNF-14'],
   ['produccion.produccion_abono', 'inventario.lote_inventario'], ['inventario.entrada_inicial()'], [], ['v4:Kardex'])
cu('PRO-10', 'Medir la calidad del agua de los estanques', ['OPE'], ['GW'], 1, ['RF-18'],
   ['produccion.calidad_agua_estanque'], [], [], [], inc=['NUC-05'])

# ------------------------------------------------------------------ riego
cu('RIE-01', 'Configurar fuentes, tanques, sistemas y válvulas', ['ENC'], [], 1, ['RQ-25'],
   ['riego.fuente_agua', 'riego.tanque', 'riego.sistema_riego', 'riego.valvula'], [], [], [])
cu('RIE-02', 'Registrar un riego manual', ['OPE'], [], 1, ['RQ-25', 'RF-19'],
   ['riego.evento_riego'], [], [], [], inc=['NUC-05'])
cu('RIE-03', 'Regar automáticamente por reglas', ['GW'], ['EST_M', 'ENC'], 4, ['RQ-25'],
   ['iot.regla_automatizacion', 'iot.comando_actuador', 'riego.evento_riego'], ['regla determinista en la pasarela'], [], [],
   ext=['IOT-03'], flag='riego_automatico')

# ------------------------------------------------------------------ iot
cu('IOT-01', 'Registrar dispositivos, sensores y actuadores', ['ADM'], ['GW'], 4, ['RQ-25', 'RQ-26'],
   ['iot.dispositivo', 'iot.sensor', 'iot.actuador'], ['ck modo_falla'], [], ['v4:Seguridad'])
cu('IOT-02', 'Recibir lecturas de sensores', ['GW'], [], 4, ['RQ-25'],
   ['iot.lectura'], ['inventario.evaluar_excursion()'], ['MQTT finca/<dispositivo>/<sensor>'], ['v4:Frío'])
cu('IOT-03', 'Accionar un actuador a mano', ['ENC'], ['GW'], 4, ['RQ-25'],
   ['iot.comando_actuador'], [], ['POST /api/v1/iot/comandos/'], [])
cu('IOT-04', 'Armar y desarmar la alarma por zonas', ['ENC', 'POR'], ['GW'], 4, ['RQ-26'],
   ['iot.zona_seguridad', 'iot.cambio_estado_alarma'], ['iot.cambiar_estado_alarma()'], ['POST /api/v1/iot/zonas-seguridad/{id}/estado/'], ['v4:Alarma'], flag='seguridad_perimetral')
cu('IOT-05', 'Atender un evento de seguridad perimetral', ['ENC', 'POR'], ['GW', 'NOT'], 4, ['RQ-26'],
   ['iot.evento_seguridad', 'iot.clip_video'], ['solo se registra la atención'], [], ['v4:Seguridad'], flag='seguridad_perimetral')
cu('IOT-06', 'Gestionar credenciales de acceso a puertas', ['ADM'], ['GW'], 4, ['RQ-26', 'RNF-04'],
   ['iot.credencial_acceso', 'terceros.consentimiento_datos'], ['biometría exige autorización expresa'], [], ['v4:Biometría'])
cu('IOT-07', 'Conservar o depurar clips de cámaras', ['SCH', 'ADM'], [], 4, ['RQ-26'],
   ['iot.camara', 'iot.clip_video'], ['iot.depurar_clips()'], [], ['v4:Cámaras'], flag='camaras')
cu('IOT-08', 'Planear y ejecutar una misión de dron o robot', ['ENC', 'ADM'], ['GW'], 4, ['RQ-42'],
   ['iot.mision_robot', 'activos.activo', 'seguros.poliza'], ['iot.validar_mision()'], ['POST /api/v1/iot/misiones-robot/{id}/aprobar/'],
   ['v5:Robótica'], inc=['AGD-05'], flag='dron_monitoreo')
cu('IOT-09', 'Cortar cargas con batería baja', ['GW'], [], 4, ['RQ-25', 'RNF-14'],
   ['iot.prioridad_carga'], ['iot.cargas_a_cortar()'], [], ['v5:Energía'])

# ------------------------------------------------------------------ ambiental
cu('AMB-01', 'Registrar mediciones ambientales', ['OPE'], ['GW'], 2, ['RF-19', 'RNF-14', 'RQ-44'],
   ['ambiental.registro_ambiental'], [], [], ['v4:Ambiental'])
cu('AMB-02', 'Mantener factores de emisión con su fuente', ['ADM'], [], 2, ['RQ-44'],
   ['ambiental.factor_emision'], [], [], ['v4:Ambiental'])
cu('AMB-03', 'Consultar indicadores ambientales y CO₂ estimado', ['FAM', 'ADM'], ['AG_RED'], 2, ['RF-19', 'RNF-13', 'RQ-44'],
   ['ambiental.registro_ambiental'], ['ambiental.v_indicadores'], ['GET /api/v1/ambiental/indicadores/?mes='], ['v4:Ambiental'])

# ------------------------------------------------------------------ inventario
cu('INV-01', 'Gestionar productos, unidades y bodegas', ['ADM'], [], 1, ['RF-09'],
   ['inventario.producto', 'inventario.unidad_medida', 'inventario.categoria_producto', 'inventario.bodega'], [], [], ['v4:RLS'])
cu('INV-02', 'Recibir un lote en bodega y etiquetarlo', ['OPE'], [], 1, ['RF-06', 'RQ-27'],
   ['inventario.lote_inventario', 'inventario.etiqueta', 'inventario.movimiento_inventario'],
   ['inventario.estimar_vencimiento()', 'inventario.entrada_inicial()'], [], ['v4:Vencimiento', 'v4:Kardex'], inc=['INV-03'])
cu('INV-03', 'Escanear un código y pesar con báscula', ['OPE', 'VEN'], ['GW'], 1, ['RF-06', 'RNF-03'],
   ['inventario.lectura_codigo', 'inventario.pesaje'], ['peso no estable no vende'], [], [])
cu('INV-04', 'Registrar merma, ajuste o traslado', ['OPE', 'ENC'], [], 1, ['RQ-27'],
   ['inventario.movimiento_inventario'], ['inventario.aplicar_movimiento()', 'inventario.proteger_cantidades()'], [], ['v4:Merma', 'v4:Kardex'])
cu('INV-05', 'Hacer un conteo físico', ['OPE', 'ENC'], [], 1, ['RQ-27'],
   ['inventario.conteo_fisico', 'inventario.conteo_detalle'], [], [], [], inc=['INV-03'])
cu('INV-06', 'Vigilar vencimientos y liquidar', ['SCH', 'VEN'], ['AG_ASE'], 1, ['RQ-27'],
   ['inventario.lote_inventario'], ['inventario.marcar_vencidos()', 'inventario.v_alertas_vencimiento'],
   ['GET /api/v1/inventario/alertas-vencimiento/'], ['v4:Alerta', 'v4:Vencidos', 'v4:Catálogo'])
cu('INV-07', 'Vigilar la cadena de frío y decidir sobre un lote bloqueado', ['ENC'], ['GW', 'SCH'], 2, ['RQ-27'],
   ['inventario.excursion_temperatura', 'inventario.bloqueo_lote', 'inventario.vehiculo'],
   ['inventario.evaluar_excursion()', 'inventario.aplicar_bloqueo()'], ['POST /api/v1/inventario/bloqueos-lote/{id}/decidir/'],
   ['v4:Frío'], flag='cadena_frio_finca')

# ------------------------------------------------------------------ compras
cu('CMP-01', 'Registrar cotizaciones y precios de mercado', ['ADM'], ['AG_MER', 'MER'], 1, ['RQ-23'],
   ['compras.cotizacion_proveedor', 'compras.precio_mercado'], [], [], [])
cu('CMP-02', 'Crear y aprobar una orden de compra', ['ADM'], ['AG_MER'], 1, ['RQ-23'],
   ['compras.orden_compra', 'compras.orden_compra_detalle'], [], ['POST /api/v1/compras/ordenes-compra/{id}/aprobar/'], [])
cu('CMP-03', 'Recibir una compra en bodega', ['OPE'], [], 1, ['RF-06'],
   ['compras.orden_compra', 'inventario.lote_inventario'], ['inventario.entrada_inicial()'], ['POST /api/v1/compras/ordenes-compra/{id}/recibir/'],
   ['v4:Kardex'], inc=['INV-02'], ext=['FIN-11'])
cu('CMP-04', 'Emitir un documento soporte electrónico', ['CON'], ['DIAN'], 1, ['RNF-13'],
   ['compras.documento_soporte'], [], [], ['v4:Permuta'])

# ------------------------------------------------------------------ activos
cu('ACT-01', 'Registrar un activo con su hoja de vida', ['ADM'], [], 2, ['RQ-31'],
   ['activos.activo', 'activos.plan_mantenimiento'], [], [], ['v5:Activos'])
cu('ACT-02', 'Registrar el uso de un activo', ['OPE'], ['GW'], 2, ['RQ-31'],
   ['activos.uso_activo'], ['activos.sumar_uso()'], [], ['v5:Activos'], inc=['NUC-05'])
cu('ACT-03', 'Generar y cerrar órdenes de mantenimiento', ['SCH', 'ENC', 'OPE'], [], 2, ['RQ-31'],
   ['activos.orden_trabajo', 'activos.repuesto_orden', 'personal.tarea'], ['activos.generar_ordenes_trabajo()', 'activos.cerrar_orden()'],
   ['POST /api/v1/activos/ordenes-trabajo/generar/'], ['v5:Activos'], inc=['PER-05'])
cu('ACT-04', 'Depreciar los activos del mes', ['SCH', 'CON'], [], 2, ['RQ-31', 'RQ-38'],
   ['activos.depreciacion'], ['activos.depreciar_mes()'], ['POST /api/v1/activos/depreciar/?mes='], ['v5:Activos'])
cu('ACT-05', 'Asignar un equipo a un trabajador', ['ENC'], [], 2, ['RQ-31', 'RQ-28'],
   ['personal.asignacion_equipo'], [], [], [])

# ------------------------------------------------------------------ comercial
cu('VTA-01', 'Gestionar listas y precios con vigencia', ['ADM'], [], 1, ['RF-09'],
   ['comercial.lista_precios', 'comercial.precio_producto'], ['precio nunca se edita: se cierra y se crea'], [], [])
cu('VTA-02', 'Proponer y aprobar un cambio de precio', ['ADM'], ['AG_MER'], 1, ['RF-09', 'RQ-23'],
   ['comercial.propuesta_precio', 'ia.solicitud_aprobacion'], ['comercial.aplicar_propuesta_precio()'],
   ['POST /api/v1/comercial/propuestas-precio/{id}/aprobar/'], [], inc=['IA-02'])
cu('VTA-03', 'Tomar y confirmar un pedido', ['VEN', 'CLI'], ['AG_ASE'], 1, ['RF-10', 'RQ-27'],
   ['comercial.pedido', 'comercial.pedido_detalle', 'comercial.reserva_lote'],
   ['inventario.reservar_fefo()', 'comercial.confirmar_pedido()', 'inventario.puede_venderse()'],
   ['POST /api/v1/comercial/pedidos/{id}/confirmar/'], ['v4:FEFO', 'v4:Pedido', 'v4:Catálogo'], ext=['VTA-08'])
cu('VTA-04', 'Vender en la finca o en la feria sin conexión', ['VEN'], [], 2, ['RF-12', 'RNF-03'],
   ['comercial.pedido', 'comercial.pago'], [], [], ['v4:Sin conexión'], inc=['NUC-05', 'INV-03'])
cu('VTA-05', 'Despachar y entregar un pedido', ['OPE', 'VEN'], ['GW'], 1, ['RF-10', 'RQ-27'],
   ['comercial.entrega', 'comercial.reserva_lote', 'inventario.movimiento_inventario'], ['comercial.despachar_pedido()'],
   ['POST /api/v1/comercial/pedidos/{id}/despachar/'], ['v4:Despacho', 'v4:Trazabilidad'], inc=['INV-03'])
cu('VTA-06', 'Facturar electrónicamente', ['SCH'], ['DIAN'], 1, ['RNF-13'],
   ['comercial.factura'], ['comercial.preparar_factura()', 'regla fija, no IA'], ['POST /api/v1/comercial/pedidos/{id}/facturar/'], ['v4:Crédito'])
cu('VTA-07', 'Registrar y confirmar un pago', ['VEN', 'CON'], ['PAG'], 1, ['RF-21'],
   ['comercial.pago'], ['comercial.aplicar_pago()', 'un agente no confirma pagos'], ['POST /api/v1/comercial/pagos/{id}/confirmar/', 'POST /api/v1/pagos/webhook/'], ['v4:Pagos'])
cu('VTA-08', 'Vender a crédito y controlar la cartera', ['CON', 'VEN'], ['NOT'], 2, ['RF-11'],
   ['comercial.factura', 'terceros.cliente'], ['comercial.confirmar_pedido()', 'comercial.actualizar_mora()', 'comercial.v_cartera'], ['GET /api/v1/comercial/cartera/'],
   ['v4:Crédito'], flag='venta_credito')
cu('VTA-09', 'Generar pedidos recurrentes', ['SCH', 'VEN'], [], 2, ['RF-10'],
   ['comercial.pedido_recurrente', 'comercial.pedido_recurrente_detalle'], ['comercial.generar_pedidos_recurrentes()'], [],
   ['v4:Recurrentes'], flag='pedidos_recurrentes')
cu('VTA-10', 'Registrar una permuta', ['CON'], ['DIAN'], 2, ['RNF-13'],
   ['comercial.permuta', 'compras.documento_soporte', 'comercial.factura'], ['comercial.aplicar_permuta()'], [], ['v4:Permuta'], flag='permuta')
cu('VTA-11', 'Consultar la trazabilidad de un lote', ['CLI', 'ADM'], [], 1, ['RF-06'],
   ['comercial.huella_trazabilidad'], ['comercial.v_trazabilidad_lote', 'comercial.verificar_cadena_huellas()'], ['GET /api/v1/publico/trazabilidad/{codigo}/'],
   ['v4:Trazabilidad', 'v4:Huellas'])
cu('VTA-12', 'Retirar un lote del mercado', ['ADM'], ['NOT', 'CAN'], 1, ['RF-06', 'RQ-27'],
   ['comercial.retiro_lote', 'comercial.retiro_aviso', 'inventario.bloqueo_lote'], ['comercial.abrir_retiro()'], [], ['v4:Retiro'])

# ------------------------------------------------------------------ crm
cu('CRM-01', 'Capturar un posible cliente con autorización', ['PRO', 'VEN'], [], 2, ['RQ-36', 'RNF-04'],
   ['crm.formulario_captura', 'crm.prospecto', 'terceros.consentimiento_datos'], ['crm.validar_prospecto()'],
   ['POST /api/v1/crm/captura/{formulario}/'], ['v5:CRM'])
cu('CRM-02', 'Gestionar segmentos y campañas', ['VEN', 'ADM'], [], 2, ['RQ-36'],
   ['crm.segmento', 'crm.campana'], ['crm.v_campanas'], [], ['v5:CRM'])
cu('CRM-03', 'Registrar interacciones y avanzar el embudo', ['VEN'], ['CAN'], 2, ['RQ-36'],
   ['crm.interaccion', 'crm.prospecto', 'crm.contacto_empresa'], ['crm.validar_interaccion()'], [], ['v5:CRM'])
cu('CRM-04', 'Calificar los prospectos', ['SCH', 'VEN'], [], 2, ['RQ-36'],
   ['crm.prospecto'], ['crm.calificar()'], ['POST /api/v1/crm/prospectos/{id}/calificar/'], ['v5:CRM'])
cu('CRM-05', 'Convertir un prospecto en cliente', ['VEN'], [], 2, ['RQ-36'],
   ['crm.prospecto', 'terceros.tercero', 'terceros.cliente'], ['crm.convertir_prospecto()'], ['POST /api/v1/crm/prospectos/{id}/convertir/'],
   ['v5:CRM'], inc=['TER-01'])
cu('CRM-06', 'Gestionar oportunidades y proyectar ventas', ['VEN', 'FAM'], [], 2, ['RQ-36', 'RQ-38'],
   ['crm.oportunidad'], ['crm.v_embudo', 'crm.v_proyeccion_ventas'], ['GET /api/v1/crm/embudo/'], ['v5:CRM'])

# ------------------------------------------------------------------ redes
cu('RED-01', 'Atender el mensaje de un cliente por un canal', ['CLI'], ['CAN', 'AG_ORQ', 'AG_ASE', 'AG_VEP'], 1, ['RQ-24', 'RQ-23'],
   ['redes.cuenta_red', 'ia.regla_conversacion'], ['herramientas MCP de solo lectura y borrador'], ['POST /canales/whatsapp/webhook'],
   ['v4:WhatsApp'], inc=['RED-03'], ext=['RED-02', 'VTA-03'])
cu('RED-02', 'Escalar una conversación a una persona', ['VEN'], ['AG_ORQ'], 1, ['RQ-24'],
   ['ia.escalamiento'], ['ventana del canal'], [], ['v4:Instagram'])
cu('RED-03', 'Enviar un mensaje saliente dentro de las reglas del canal', ['VEN'], ['CAN', 'AG_ASE'], 1, ['RF-20', 'RQ-24', 'RNF-04'],
   ['redes.mensaje_saliente', 'redes.plantilla_mensaje', 'redes.politica_canal'], ['redes.verificar_envio()'], [],
   ['v4:WhatsApp', 'v4:Instagram', 'v4:TikTok'])
cu('RED-04', 'Proponer y aprobar una publicación', ['ADM'], ['AG_RED', 'CAN'], 2, ['RQ-24', 'RQ-23'],
   ['redes.publicacion'], ['solo una persona aprueba contenido'], [], [], inc=['IA-02'])
cu('RED-05', 'Producir una pieza audiovisual con autorización de imagen', ['ADM'], ['AG_RED'], 2, ['RQ-24', 'RNF-04'],
   ['redes.pieza_audiovisual', 'redes.pieza_persona'], ['redes.validar_pieza()'], [], ['v4:Audiovisual'], flag='videos_promocionales')
cu('RED-06', 'Mantener plantillas y políticas de canal', ['ADM'], ['CAN'], 1, ['RQ-24'],
   ['redes.plantilla_mensaje', 'redes.politica_canal'], [], [], ['v4:WhatsApp'])

# ------------------------------------------------------------------ turismo
cu('TUR-01', 'Gestionar alojamientos y planes turísticos', ['ADM'], [], 3, ['RF-13'],
   ['turismo.alojamiento', 'turismo.plan_turistico', 'agenda.recurso'], [], [], ['v5:Agenda'])
cu('TUR-02', 'Reservar una cabaña o un plan', ['CLI', 'VEN'], ['AG_GUI'], 3, ['RF-13', 'RF-14', 'RQ-39'],
   ['turismo.reserva', 'agenda.cita'], ['turismo.validar_reserva()', 'turismo.sincronizar_agenda()'],
   ['GET /api/v1/agenda/recursos/{id}/disponible/'], ['v5:Agenda'], inc=['AGD-02'], ext=['TUR-03'])
cu('TUR-03', 'Pagar anticipadamente una reserva', ['CLI'], ['PAG'], 3, ['RF-14', 'RF-21'],
   ['turismo.reserva', 'comercial.pago'], [], ['POST /api/v1/pagos/webhook/'], ['v4:Pagos'])
cu('TUR-04', 'Hacer check-in y check-out de huéspedes', ['POR', 'VEN'], ['VIS'], 3, ['RF-16', 'RNF-04'],
   ['turismo.reserva', 'terceros.consentimiento_datos', 'personal.tarea'], ['turismo.sincronizar_agenda()'], [], ['v5:Agenda'], inc=['AGD-04'])
cu('TUR-05', 'Atender la solicitud de un grupo', ['OPR'], ['VEN'], 3, ['RF-15'],
   ['turismo.reserva', 'turismo.plan_turistico', 'agenda.visita'], [], [], [], inc=['AGD-03'])
cu('TUR-06', 'Bloquear fechas del calendario', ['ADM'], [], 3, ['RF-13'],
   ['turismo.bloqueo_calendario', 'agenda.cita'], ['turismo.sincronizar_bloqueo()'], [], ['v5:Agenda'])

# ------------------------------------------------------------------ agenda
cu('AGD-01', 'Configurar recursos agendables', ['ADM'], [], 3, ['RQ-39'],
   ['agenda.recurso'], [], [], ['v5:Agenda'])
cu('AGD-02', 'Agendar una cita en un recurso', ['ENC', 'VEN'], [], 3, ['RQ-39'],
   ['agenda.cita'], ['agenda.preparar_cita()', 'exclusión GiST sin cruces', 'agenda.recurso_libre()'], [], ['v5:Agenda'])
cu('AGD-03', 'Programar y aprobar una visita', ['ENC'], ['VIS', 'NOT'], 2, ['RQ-39', 'RF-16'],
   ['agenda.visita'], ['agenda.validar_visita()', 'agenda.emitir_pase()'],
   ['POST /api/v1/agenda/visitas/{id}/aprobar/', 'POST /api/v1/agenda/visitas/{id}/pase/'], ['v5:Visitas'])
cu('AGD-04', 'Registrar entradas y salidas en portería', ['POR'], ['VIS'], 2, ['RQ-39', 'RF-16'],
   ['agenda.registro_acceso', 'personal.jornada'], ['agenda.validar_acceso()'], [], ['v5:Portería'], inc=['NUC-05'])
cu('AGD-05', 'Consultar quién está en la finca', ['POR', 'ADM'], ['GW'], 2, ['RQ-39'],
   ['agenda.registro_acceso'], ['agenda.v_en_sitio'], ['GET /api/v1/agenda/en-sitio/'], ['v5:Portería'])
cu('AGD-06', 'Consultar la agenda del día', ['ENC', 'POR'], [], 2, ['RQ-39'],
   ['agenda.cita', 'agenda.visita', 'personal.turno'], ['agenda.v_agenda_dia'], ['GET /api/v1/agenda/dia/?fecha='], ['v5:Agenda'])

# ------------------------------------------------------------------ personal
cu('PER-01', 'Configurar áreas de responsabilidad y matriz RACI', ['ADM'], [], 1, ['RQ-28'],
   ['personal.area_responsabilidad', 'personal.miembro_area', 'personal.matriz_responsabilidad'], [], [], ['v5:Áreas'])
cu('PER-02', 'Definir el plan de labores', ['ENC'], [], 1, ['RQ-28'],
   ['personal.plantilla_tarea'], [], [], ['v5:Personal'])
cu('PER-03', 'Generar las tareas del día', ['SCH'], ['AG_COO'], 1, ['RQ-28'],
   ['personal.tarea', 'personal.paso_tarea'], ['personal.generar_tareas_del_dia()'], ['POST /api/v1/personal/tareas/generar-dia/'], ['v5:Personal'])
cu('PER-04', 'Asignar una tarea', ['ENC'], ['AG_COO'], 1, ['RQ-28', 'RQ-30'],
   ['personal.tarea'], ['personal.validar_tarea()', 'personal.validar_area_tarea()', 'personal.empleado_disponible()', 'formacion.esta_habilitado()'],
   [], ['v5:Personal', 'v5:Áreas', 'v5:Cronograma'])
cu('PER-05', 'Ejecutar una tarea con evidencia', ['OPE'], [], 1, ['RQ-28', 'RNF-03'],
   ['personal.tarea', 'personal.paso_tarea', 'personal.evidencia_tarea'], ['personal.validar_tarea()'], [], ['v5:Personal'], inc=['NUC-05'])
cu('PER-06', 'Aprobar o devolver una tarea', ['ENC'], [], 1, ['RQ-28', 'RQ-29'],
   ['personal.tarea'], ['personal.validar_tarea()', 'personal.es_responsable_area()'], ['POST /api/v1/personal/tareas/{id}/aprobar/'],
   ['v5:Personal', 'v5:Áreas'])
cu('PER-07', 'Armar y publicar el cronograma de turnos', ['ENC'], ['AG_COO'], 2, ['RQ-40'],
   ['personal.cronograma', 'personal.patron_turno', 'personal.asignacion_patron', 'personal.requerimiento_cobertura', 'personal.turno'],
   ['personal.generar_turnos()', 'personal.huecos_cobertura()', 'personal.publicar_cronograma()', 'personal.validar_turno()'],
   ['POST /api/v1/personal/cronogramas/{id}/generar/', 'GET /api/v1/personal/cronogramas/{id}/huecos/', 'POST /api/v1/personal/cronogramas/{id}/publicar/'],
   ['v5:Turnos', 'v5:Cronograma'])
cu('PER-08', 'Registrar disponibilidad y ausencias', ['OPE', 'ENC'], [], 2, ['RQ-40'],
   ['personal.disponibilidad', 'personal.ausencia'], ['personal.empleado_disponible()'], [], ['v5:Personal', 'v5:Turnos'])
cu('PER-09', 'Registrar la jornada con el carné', ['OPE'], ['POR'], 1, ['RQ-28', 'RQ-29'],
   ['personal.jornada', 'personal.credencial_trabajo'], ['personal.calcular_jornada()'], [], ['v5:Personal', 'v5:Portería'], inc=['NUC-05'])
cu('PER-10', 'Organizar cuadrillas', ['ENC'], [], 1, ['RQ-28'],
   ['personal.cuadrilla', 'personal.cuadrilla_miembro'], [], [], [])

# ------------------------------------------------------------------ formacion
cu('FOR-01', 'Diseñar un curso con lecciones y evaluación', ['INS'], ['MOO'], 2, ['RQ-30'],
   ['formacion.curso', 'formacion.leccion', 'formacion.evaluacion', 'formacion.pregunta', 'formacion.competencia'], ['formacion.validar_curso()'],
   [], ['v5:Formación'])
cu('FOR-02', 'Tomar un curso virtual', ['EST', 'OPE'], [], 2, ['RQ-30'],
   ['formacion.inscripcion', 'formacion.progreso'], ['formacion.validar_inscripcion()', 'formacion.certificar_inscripcion()'], [], ['v5:Formación'],
   inc=['FOR-04'])
cu('FOR-03', 'Dictar una sesión presencial y registrar asistencia', ['INS'], ['EST', 'OPE'], 2, ['RQ-30'],
   ['formacion.sesion_presencial', 'formacion.asistencia'], ['formacion.certificar_sesion()'],
   ['POST /api/v1/formacion/sesiones-presenciales/{id}/certificar/'], ['v5:Formación'], inc=['FOR-04'])
cu('FOR-04', 'Emitir certificados y habilitaciones', ['SCH'], [], 2, ['RQ-30'],
   ['formacion.certificado', 'formacion.habilitacion'], ['formacion.emitir_certificado()', 'formacion.habilitar_desde_certificado()'], [], ['v5:Formación'])
cu('FOR-05', 'Retirar habilitaciones vencidas', ['SCH'], [], 2, ['RQ-30'],
   ['formacion.habilitacion'], ['formacion.actualizar_habilitaciones()'], [], ['v5:Formación'])
cu('FOR-06', 'Detectar necesidades de formación', ['ENC'], [], 2, ['RQ-30', 'RQ-33'],
   ['formacion.necesidad_formacion'], [], [], ['v5:Formación'])
cu('FOR-07', 'Responder la encuesta de un curso', ['EST', 'OPE'], [], 2, ['RQ-30', 'RQ-33'],
   ['formacion.encuesta'], ['formacion.v_satisfaccion'], [], ['v5:Formación'])
cu('FOR-08', 'Presentar y resolver una queja o apelación', ['EST', 'OPE'], ['ADM'], 2, ['RQ-30', 'RQ-33'],
   ['formacion.queja_apelacion'], ['formacion.validar_queja()'], [], ['v5:Formación'])
cu('FOR-09', 'Preguntar al Instructor virtual', ['OPE', 'EST'], ['AG_INS'], 2, ['RQ-30', 'RQ-23'],
   ['documental.version_documento', 'ia.fragmento_conocimiento'], ['documental.documento_para_agente()'], [], ['v5:Documental'], inc=['DOC-03'])

# ------------------------------------------------------------------ nomina
cu('NOM-01', 'Configurar conceptos y tarifas de nómina', ['CON'], [], 2, ['RQ-29'],
   ['nomina.concepto_nomina', 'nucleo.parametro'], ['nomina.concepto()'], [], ['v5:Nómina'])
cu('NOM-02', 'Preparar la prenómina', ['CON', 'ENC'], [], 2, ['RQ-29'],
   ['nomina.periodo_nomina', 'nomina.novedad'], ['nomina.preparar_prenomina()', 'nomina.validar_novedad()'],
   ['POST /api/v1/nomina/periodos/{id}/prenomina/'], ['v5:Nómina'])
cu('NOM-03', 'Registrar novedades manuales', ['CON'], [], 2, ['RQ-29'],
   ['nomina.novedad'], ['nomina.validar_novedad()', 'nomina.proteger_detalle_periodo()'], [], ['v5:Nómina'])
cu('NOM-04', 'Liquidar la nómina', ['CON'], [], 2, ['RQ-29'],
   ['nomina.liquidacion', 'nomina.liquidacion_detalle', 'nomina.provision_prestacion'], ['nomina.liquidar()'],
   ['POST /api/v1/nomina/periodos/{id}/liquidar/'], ['v5:Nómina'])
cu('NOM-05', 'Cerrar el periodo de nómina', ['FAM', 'CON'], [], 2, ['RQ-29'],
   ['nomina.periodo_nomina', 'finanzas.comprobante'], ['nomina.proteger_periodo()'], ['POST /api/v1/nomina/periodos/{id}/cerrar/'],
   ['v5:Nómina'], inc=['FIN-02'])
cu('NOM-06', 'Preparar y aprobar los pagos de nómina', ['CON', 'FAM'], [], 2, ['RQ-29'],
   ['nomina.pago_nomina'], ['nomina.validar_pago()', 'nomina.marcar_pagada()'], [], ['v5:Nómina'])
cu('NOM-07', 'Generar la PILA y exportar al contador', ['CON'], [], 2, ['RQ-29'],
   ['nomina.planilla_pila', 'nomina.exportacion_nomina'], [], ['GET /api/v1/nomina/periodos/{id}/pila/', 'GET /api/v1/nomina/periodos/{id}/exportar/?formato='], [])
cu('NOM-08', 'Transmitir la nómina electrónica', ['CON'], ['DIAN'], 2, ['RQ-29'],
   ['nomina.documento_nomina_electronica'], ['nomina.validar_documento_electronico()'], [], ['v5:Nómina'], flag='nomina_electronica')

# ------------------------------------------------------------------ finanzas
cu('FIN-01', 'Configurar el plan de cuentas y los centros de costo', ['CON'], [], 1, ['RF-17'],
   ['finanzas.cuenta_contable', 'finanzas.centro_costo'], [], [], [])
cu('FIN-02', 'Contabilizar un comprobante', ['CON'], ['AG_CON'], 1, ['RF-17', 'RNF-13'],
   ['finanzas.comprobante', 'finanzas.movimiento_contable'], ['finanzas.validar_cuadre()', 'finanzas.proteger_movimiento()'], [], ['v4:Contabilidad'])
cu('FIN-03', 'Anular un comprobante o registrar una nota', ['CON'], [], 1, ['RNF-13'],
   ['finanzas.comprobante'], ['finanzas.proteger_comprobante()'], [], ['v4:Contabilidad'])
cu('FIN-04', 'Cerrar el periodo contable', ['CON'], ['SCH'], 1, ['RNF-13'],
   ['finanzas.periodo_contable'], [], ['POST /api/v1/finanzas/periodos-contable/{id}/cerrar/'], ['v4:Contabilidad'])
cu('FIN-05', 'Clasificar costos y distribuirlos por actividades', ['CON'], [], 2, ['RF-18', 'RQ-38'],
   ['finanzas.clasificacion_costo', 'finanzas.actividad_costo', 'finanzas.asignacion_costo', 'finanzas.costo_estandar'],
   ['finanzas.validar_clasificacion()', 'finanzas.distribuir_costos()'], [], ['v5:Finanzas'])
cu('FIN-06', 'Elaborar y aprobar el presupuesto maestro', ['CON', 'FAM'], [], 2, ['RQ-38', 'RNF-13'],
   ['finanzas.presupuesto', 'finanzas.premisa_presupuesto', 'finanzas.presupuesto_detalle'], ['finanzas.validar_presupuesto_detalle()'], [], ['v5:Finanzas'])
cu('FIN-07', 'Generar los estados financieros', ['CON', 'FAM'], [], 2, ['RF-17', 'RQ-38'],
   ['finanzas.estado_financiero'], ['finanzas.estado_resultados()', 'finanzas.balance_general()', 'finanzas.saldo()'],
   ['GET /api/v1/finanzas/estado-resultados/?desde=&hasta=&centro=', 'GET /api/v1/finanzas/balance/?hasta='], ['v5:Finanzas'])
cu('FIN-08', 'Calcular indicadores y consultar el tablero', ['FAM', 'SCH'], ['AG_NEG'], 2, ['RF-17', 'RF-18', 'RQ-38'],
   ['finanzas.indicador', 'finanzas.valor_indicador', 'estrategia.objetivo'], ['finanzas.calcular_indicadores()'],
   ['POST /api/v1/finanzas/indicadores/calcular/'], ['v5:Finanzas'])
cu('FIN-09', 'Analizar estados: vertical, horizontal, fuentes y usos', ['CON', 'FAM'], ['AG_NEG'], 2, ['RQ-38'],
   ['finanzas.cuenta_contable', 'finanzas.movimiento_contable'], ['finanzas.analisis_vertical_horizontal()', 'finanzas.fuentes_usos()'],
   ['GET /api/v1/finanzas/analisis/?a=&b=', 'GET /api/v1/finanzas/fuentes-usos/?a=&b='], ['v5:Finanzas'])
cu('FIN-10', 'Calcular punto de equilibrio y palancas', ['FAM'], ['AG_EST'], 2, ['RQ-38', 'RQ-37'],
   [], ['finanzas.palancas()'], ['GET /api/v1/finanzas/palancas/?q=&p=&cv=&cf=&i='], ['v5:Finanzas'])
cu('FIN-11', 'Gestionar anticipos a proveedores', ['CON'], [], 2, ['RQ-38'],
   ['finanzas.anticipo_proveedor', 'finanzas.aplicacion_anticipo'], ['finanzas.aplicar_anticipo()', 'finanzas.preparar_anticipo()'], [], ['v5:Finanzas'])
cu('FIN-12', 'Emitir un informe de indicadores para crédito', ['FAM'], ['B2B'], 3, ['RQ-38', 'RNF-13'],
   ['finanzas.reporte_indicadores'], ['finanzas.validar_reporte_indicadores()'], [], ['v5:Finanzas'], flag='indicadores_credito')

# ------------------------------------------------------------------ estrategia
cu('EST-01', 'Mantener las líneas de negocio y la matriz DOFA', ['FAM'], ['AG_EST'], 2, ['RQ-37'],
   ['estrategia.linea_negocio', 'estrategia.factor_dofa'], ['estrategia.v_matriz_lineas'], ['GET /api/v1/estrategia/lineas/'], ['v5:Estrategia'])
cu('EST-02', 'Registrar un estudio de mercado', ['FAM'], ['AG_EST', 'MER'], 2, ['RQ-37'],
   ['estrategia.estudio_mercado'], [], [], [])
cu('EST-03', 'Proponer una iniciativa de crecimiento', ['FAM'], ['AG_EST'], 2, ['RQ-37', 'RQ-23'],
   ['estrategia.iniciativa'], ['estrategia.validar_iniciativa()'], [], ['v5:Estrategia'])
cu('EST-04', 'Evaluar financieramente una iniciativa', ['FAM'], ['AG_EST'], 2, ['RQ-37'],
   ['estrategia.evaluacion_proyecto', 'estrategia.flujo_proyecto'], ['estrategia.evaluar_proyecto()', 'estrategia.vpn()', 'estrategia.tir()'],
   ['POST /api/v1/estrategia/evaluaciones-proyecto/{id}/calcular/'], ['v5:Estrategia'], inc=['FIN-10'])
cu('EST-05', 'Aprobar una iniciativa', ['FAM'], [], 2, ['RQ-37'],
   ['estrategia.iniciativa'], ['estrategia.validar_iniciativa()'], [], ['v5:Estrategia'], inc=['EST-04'], ext=['PRY-01'])
cu('EST-06', 'Reinvertir utilidades de una línea', ['FAM'], [], 2, ['RQ-37'],
   ['estrategia.reinversion'], ['estrategia.validar_reinversion()', 'estrategia.utilidad_linea()'], [], ['v5:Estrategia'])
cu('EST-07', 'Seguir el retorno de las iniciativas', ['FAM'], ['AG_NEG'], 2, ['RQ-37'],
   ['estrategia.seguimiento_iniciativa'], ['estrategia.v_retorno_iniciativas'], ['GET /api/v1/estrategia/retorno/'], ['v5:Estrategia'])
cu('EST-08', 'Definir objetivos y metas del cuadro de mando', ['FAM'], [], 2, ['RQ-37', 'RQ-38'],
   ['estrategia.objetivo'], ['semáforo de finanzas.calcular_indicadores()'], [], ['v5:Finanzas'])

# ------------------------------------------------------------------ proyectos
cu('PRY-01', 'Constituir un proyecto', ['DIR'], ['AG_PRY'], 2, ['RQ-41'],
   ['proyectos.proyecto', 'documental.documento'], [], [], ['v5:Proyectos'])
cu('PRY-02', 'Aprobar un proyecto', ['PAT'], [], 2, ['RQ-41'],
   ['proyectos.proyecto', 'proyectos.linea_base'], ['proyectos.validar_proyecto()', 'proyectos.linea_base_inicial()'],
   ['POST /api/v1/proyectos/proyectos/{id}/aprobar/'], ['v5:Proyectos'])
cu('PRY-03', 'Planificar el alcance y el cronograma', ['DIR'], ['AG_PRY'], 2, ['RQ-41'],
   ['proyectos.elemento_edt', 'proyectos.actividad', 'proyectos.dependencia'], ['proyectos.validar_dependencia()'], [], ['v5:Proyectos'],
   inc=['PRY-04'])
cu('PRY-04', 'Calcular la ruta crítica', ['DIR'], [], 2, ['RQ-41'],
   ['proyectos.actividad'], ['proyectos.calcular_ruta_critica()'], ['POST /api/v1/proyectos/proyectos/{id}/ruta-critica/'], ['v5:Proyectos'])
cu('PRY-05', 'Gestionar interesados y riesgos', ['DIR'], ['AG_PRY'], 2, ['RQ-41'],
   ['proyectos.interesado', 'proyectos.riesgo', 'proyectos.registro'], ['proyectos.clasificar_interesado()'], [], ['v5:Proyectos'])
cu('PRY-06', 'Registrar avance y medir el valor ganado', ['DIR'], ['SCH'], 2, ['RQ-41'],
   ['proyectos.actividad', 'proyectos.medicion_valor_ganado'], ['proyectos.avance_actividad()', 'proyectos.calcular_valor_ganado()'],
   ['POST /api/v1/proyectos/proyectos/{id}/valor-ganado/?corte=', 'GET /api/v1/proyectos/tablero/'], ['v5:Proyectos'])
cu('PRY-07', 'Solicitar y decidir un cambio', ['DIR', 'PAT'], [], 2, ['RQ-41'],
   ['proyectos.solicitud_cambio', 'proyectos.linea_base'], ['proyectos.decidir_cambio()', 'proyectos.nueva_linea_base()'],
   ['POST /api/v1/proyectos/solicitudes-cambio/{id}/decidir/'], ['v5:Proyectos'])
cu('PRY-08', 'Aceptar entregables y cerrar el proyecto', ['PAT', 'DIR'], [], 2, ['RQ-41'],
   ['proyectos.elemento_edt', 'proyectos.registro', 'proyectos.proyecto'], ['proyectos.aceptar_entregable()', 'proyectos.validar_proyecto()'], [],
   ['v5:Proyectos'])
cu('PRY-09', 'Planear y cerrar una iteración', ['DIR'], [], 2, ['RQ-41'],
   ['proyectos.iteracion', 'proyectos.actividad'], [], [], [])

# ------------------------------------------------------------------ seguros
cu('SGR-01', 'Registrar una póliza y sus bienes asegurados', ['ADM'], ['ASE'], 2, ['RQ-34'],
   ['seguros.poliza', 'seguros.bien_asegurado'], ['seguros.preparar_poliza()'], [], ['v5:Seguros'])
cu('SGR-02', 'Avisar pólizas próximas a vencer', ['SCH'], ['NOT'], 2, ['RQ-34'],
   ['seguros.poliza'], ['seguros.v_por_vencer'], [], ['v5:Seguros'])
cu('SGR-03', 'Registrar y enviar un aviso de siniestro', ['ENC', 'ADM'], ['ASE'], 2, ['RQ-34'],
   ['seguros.aviso_siniestro'], ['seguros.validar_aviso()'], [], ['v5:Seguros'])
cu('SGR-04', 'Vigilar el índice de una póliza paramétrica', ['SCH'], ['EST_M'], 2, ['RQ-34', 'RQ-25'],
   ['seguros.indice_poliza', 'seguros.aviso_siniestro'], ['seguros.vigilar_indice()'], [], ['v5:Seguros'], flag='seguro_parametrico')

# ------------------------------------------------------------------ cumplimiento
cu('CUM-01', 'Cargar normas y requisitos', ['ADM'], [], 1, ['RQ-33'],
   ['cumplimiento.norma', 'cumplimiento.requisito'], [], [], ['v5:Cumplimiento'])
cu('CUM-02', 'Abrir un expediente de cumplimiento', ['ADM'], [], 1, ['RQ-33'],
   ['cumplimiento.expediente'], ['cumplimiento.validar_expediente()'], [], ['v5:Cumplimiento'])
cu('CUM-03', 'Evaluar el expediente contra su evidencia', ['SCH'], [], 1, ['RQ-33'],
   ['cumplimiento.evaluacion_requisito'], ['cumplimiento.evaluar_expediente()'], ['POST /api/v1/cumplimiento/expedientes/{id}/evaluar/'], ['v5:Cumplimiento'])
cu('CUM-04', 'Adjuntar evidencias a un requisito', ['ENC'], [], 1, ['RQ-33'],
   ['cumplimiento.evidencia_requisito'], [], [], ['v5:Cumplimiento'])
cu('CUM-05', 'Registrar una auditoría externa y sus no conformidades', ['ADM'], ['AUD'], 2, ['RQ-33'],
   ['cumplimiento.auditoria_externa', 'cumplimiento.no_conformidad'], [], ['GET /api/v1/cumplimiento/expedientes/{id}/paquete-auditor/'], ['v5:Cumplimiento'])
cu('CUM-06', 'Ejecutar y verificar acciones correctivas', ['ENC', 'ADM'], [], 2, ['RQ-33', 'RQ-28'],
   ['cumplimiento.accion_correctiva', 'cumplimiento.no_conformidad', 'personal.tarea'],
   ['cumplimiento.verificar_accion()', 'cumplimiento.cerrar_no_conformidad()'], [], ['v5:Cumplimiento'])
cu('CUM-07', 'Vigilar la obligación de granja avícola biosegura', ['SCH', 'ADM'], [], 1, ['RQ-33'],
   ['produccion.lote_animal'], ['cumplimiento.v_granja_biosegura'], ['GET /api/v1/cumplimiento/granja-biosegura/'], ['v5:Cumplimiento'])

# ------------------------------------------------------------------ ia
cu('IA-01', 'Configurar un agente y sus herramientas', ['ADM'], [], 1, ['RQ-23'],
   ['ia.agente', 'ia.herramienta', 'ia.agente_herramienta'], ['mínimo privilegio'], [], [])
cu('IA-02', 'Resolver la bandeja de aprobaciones', ['ADM'], ['AG_MER', 'AG_RED'], 1, ['RQ-23'],
   ['ia.solicitud_aprobacion'], ['nucleo.exigir_persona()'], ['POST /api/v1/ia/solicitudes-aprobacion/{id}/aprobar/'], ['v5:IA'])
cu('IA-03', 'Alimentar la base de conocimiento', ['ADM'], [], 1, ['RQ-23'],
   ['ia.documento_conocimiento', 'ia.fragmento_conocimiento'], [], ['POST /api/v1/ia/documentos-conocimiento/{id}/indexar/', 'POST /api/v1/ia/buscar/'], [])
cu('IA-04', 'Recibir y seguir recomendaciones de mejora', ['ADM', 'FAM'], ['AG_NEG'], 1, ['RQ-23'],
   ['ia.recomendacion'], ['ciclo PHVA semanal'], [], [])
cu('IA-05', 'Evaluar las respuestas de los agentes', ['CLI', 'ADM'], [], 1, ['RQ-23'],
   ['ia.evaluacion_respuesta'], [], [], [])
cu('IA-06', 'Controlar el consumo y el costo de la IA', ['ADM'], ['SCH'], 1, ['RQ-23', 'RNF-12'],
   ['ia.consumo_ia', 'ia.agente'], ['límite de costo diario por agente'], [], [])
cu('IA-07', 'Pronosticar la demanda', ['SCH'], ['VEN'], 3, ['RQ-23'],
   ['ia.modelo_pronostico', 'ia.pronostico_demanda'], ['mínimo 12 meses de ventas'], [], [], flag='pronostico_demanda')
cu('IA-08', 'Diagnosticar una foto de campo', ['OPE'], ['AG_AGR', 'ENC'], 2, ['RQ-23'],
   ['ia.diagnostico_imagen'], ['ia.validar_diagnostico()'], [], ['v5:IA'], flag='diagnostico_imagen')
cu('IA-09', 'Simular un escenario y registrar la decisión', ['FAM'], ['AG_NEG', 'AG_EST'], 2, ['RQ-23', 'RQ-37'],
   ['ia.escenario', 'ia.decision'], ['ia.validar_decision()'], [], ['v5:IA'])

# ------------------------------------------------------------------ adopcion (Apéndice A)
# Equivalencia con el documento en línea: ADO-01 = CU-240 ... ADO-15 = CU-254
P_A = ['A:Adopción']
cu('ADO-01', 'Configurar catálogo y sitios', ['ADM'], ['ENC'], 3, ['RQ-45'],
   ['adopcion.plan', 'adopcion.sitio', 'adopcion.bien'], ['nucleo.exigir_funcion()'], [], [], flag='adopcion')
cu('ADO-02', 'Comprar un árbol o un animal', ['ADP'], ['PAG', 'AG_VEP'], 3, ['RQ-45'],
   ['adopcion.contrato', 'adopcion.bien', 'terceros.tercero', 'terceros.consentimiento_datos', 'comercial.pago'],
   ['adopcion.validar_contrato()', 'comercial.preparar_factura()'], [], P_A, ext=['RED-01'], flag='adopcion')
cu('ADO-03', 'Sembrar en persona', ['ADP'], ['ENC', 'POR'], 3, ['RQ-45'],
   ['adopcion.seguimiento', 'agenda.visita'], ['adopcion.registrar_siembra()'], ['POST /api/v1/adopcion/bienes/{id}/siembra/'], P_A,
   inc=['AGD-03', 'AGD-04'], flag='adopcion')
cu('ADO-04', 'Sembrar por un trabajador y enviar el video', ['OPE'], ['ENC', 'AG_RED'], 3, ['RQ-45'],
   ['personal.tarea', 'personal.evidencia_tarea', 'adopcion.seguimiento'], ['adopcion.registrar_siembra()', 'redes.verificar_envio()'],
   ['POST /api/v1/adopcion/bienes/{id}/siembra/'], P_A, inc=['PER-04', 'PER-06'], flag='adopcion')
cu('ADO-05', 'Cobrar y pagar la cuota mensual', ['SCH'], ['ADP', 'PAG'], 3, ['RQ-46'],
   ['adopcion.cuota', 'adopcion.movimiento_saldo', 'comercial.pago'], ['adopcion.generar_cuotas()', 'adopcion.compensar_cuotas()'],
   ['POST /api/v1/adopcion/cuotas/{id}/pagar/'], P_A, flag='adopcion')
cu('ADO-06', 'Seguir mi árbol o mi animal', ['ADP'], ['OPE'], 3, ['RQ-48'],
   ['adopcion.seguimiento', 'adopcion.cuota', 'adopcion.movimiento_saldo'], ['adopcion.saldo()'],
   ['GET /api/v1/adopcion/mis-bienes/', 'GET /api/v1/adopcion/mis-bienes/{id}/seguimiento/'], P_A, flag='adopcion')
cu('ADO-07', 'Detectar abandono y poner en readopción', ['SCH'], ['ADP', 'AG_RED'], 3, ['RQ-46'],
   ['adopcion.contrato', 'adopcion.cuota', 'adopcion.bien', 'adopcion.seguimiento'], ['adopcion.marcar_abandono()'], [], P_A,
   ext=['ADO-05'], flag='adopcion')
cu('ADO-08', 'Readoptar', ['ADP'], ['PAG'], 3, ['RQ-46'],
   ['adopcion.contrato', 'adopcion.bien'], ['adopcion.validar_contrato()'], [], P_A, flag='adopcion')
cu('ADO-09', 'Registrar y vender productos del bien', ['OPE'], ['VEN'], 3, ['RQ-47'],
   ['adopcion.seguimiento', 'comercial.pedido'], [], [], ['v5:Ventas'], inc=['PRO-02', 'VTA-03'], flag='adopcion')
cu('ADO-10', 'Liquidar productos con el 5 %', ['ADM'], ['CON'], 3, ['RQ-47'],
   ['adopcion.liquidacion', 'adopcion.movimiento_saldo'], ['adopcion.validar_liquidacion()', 'adopcion.aplicar_liquidacion()'],
   ['POST /api/v1/adopcion/liquidaciones/{id}/aprobar/', 'POST /api/v1/adopcion/adoptantes/{id}/pagar-saldo/'], P_A,
   inc=['FIN-02'], flag='adopcion')
cu('ADO-11', 'Decidir en la madurez: mantener o liquidar', ['ADP'], ['ADM'], 3, ['RQ-47'],
   ['adopcion.bien', 'adopcion.contrato'], ['adopcion.marcar_madurez()', 'adopcion.validar_contrato()'],
   ['POST /api/v1/adopcion/contratos/{id}/decision/'], P_A, flag='adopcion')
cu('ADO-12', 'Talar o sacrificar y liquidar', ['ADM'], ['AUT'], 3, ['RQ-47'],
   ['adopcion.liquidacion', 'documental.documento'], ['adopcion.validar_liquidacion()', 'adopcion.aplicar_liquidacion()'], [], P_A,
   inc=['ADO-10', 'CUM-03'], flag='adopcion')
cu('ADO-13', 'Reponer un bien muerto en garantía', ['ENC'], ['ADP'], 3, ['RQ-48'],
   ['adopcion.bien', 'adopcion.contrato', 'adopcion.seguimiento'], ['adopcion.registrar_muerte()'],
   ['POST /api/v1/adopcion/bienes/{id}/muerte/'], P_A, flag='adopcion')
cu('ADO-14', 'Ceder o regalar la adopción', ['ADP'], [], 3, ['RQ-48'],
   ['adopcion.contrato'], ['adopcion.validar_contrato()'], ['POST /api/v1/adopcion/contratos/{id}/ceder/'], P_A, flag='adopcion')
cu('ADO-15', 'Consultar el tablero de adopción', ['FAM'], ['ADM'], 3, ['RQ-48'],
   ['adopcion.bien', 'adopcion.contrato', 'adopcion.cuota'], ['adopcion.v_tablero'], ['GET /api/v1/adopcion/tablero/'], P_A, flag='adopcion')


def por_modulo(m):
    """Devuelve los casos de uso de un módulo (esquema), en el orden en que se declararon."""
    return [c for c in CU if c['modulo'] == m]


if __name__ == '__main__':
    import collections
    print(len(CU), 'casos de uso')
    print(collections.Counter(c['modulo'] for c in CU))
    ids = {c['id'] for c in CU}
    for c in CU:
        for r in c['inc'] + c['ext']:
            assert r in ids, (c['id'], r)
        for a in c['actores'] + c['secundarios']:
            assert a in ACTORES, (c['id'], a)
        for r in c['rf']:
            assert r in REQUERIMIENTOS, (c['id'], r)
    sin = [r for r in REQUERIMIENTOS if not any(r in c['rf'] for c in CU)]
    print('requerimientos sin caso de uso:', sin)
