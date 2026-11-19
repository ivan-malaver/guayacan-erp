"""Modelo de datos GuayacanERP v5 (PostgreSQL). Fuente única: de aquí salen el SQL, los comentarios y el diccionario.
Notación de tipos:
  'fk:esquema.tabla'      -> bigint REFERENCES esquema.tabla(id)
  'enum:a,b,c'            -> text con CHECK (valor IN (...))
  'dinero'                -> numeric(14,2)  (pesos colombianos)
  cualquier otro          -> tipo PostgreSQL literal
Cada tabla recibe automáticamente: id (identidad), creado_en, actualizado_en (salvo auditoria=False).
"""

ESQUEMAS = {
    'nucleo': 'Usuarios, roles, permisos, parámetros con vigencia, auditoría, predio y zonas, eventos de integración',
    'terceros': 'Personas y empresas con las que se relaciona la finca: clientes, proveedores, empleados y su consentimiento de datos',
    'produccion': 'Producción animal (aves, ovinos, caprinos, peces, abejas, lombrices) y agrícola (siembras, labores, cosechas, suelo)',
    'riego': 'Fuentes de agua, tanques, sistemas de riego, válvulas y eventos de riego (manual hoy, automático en la fase IoT)',
    'inventario': 'Catálogo de productos, bodegas, lotes de inventario y kardex de movimientos',
    'comercial': 'Precios con vigencia, propuestas de precio, pedidos, facturas, pagos y entregas',
    'compras': 'Órdenes de compra, cotizaciones de proveedores y precios de mercado de referencia',
    'finanzas': 'Plan de cuentas (PUC), centros de costo, comprobantes y movimientos contables',
    'ia': 'Agentes, herramientas, aprobaciones, base de conocimiento, recomendaciones, evaluaciones y consumo de IA',
    'redes': 'Cuentas de redes sociales y publicaciones con su flujo de aprobación',
    'turismo': 'Alojamientos, planes turísticos y reservas (fase 3)',
    'iot': 'Red local de la finca: dispositivos, sensores, actuadores, reglas, seguridad perimetral y cámaras (fase 4, con diseño listo desde ya)',
    'ambiental': 'Mediciones ambientales (energía solar, biogás, compost, agua) y factores de emisión con su fuente',
    'personal': 'Tareas, plan de labores, cuadrillas, turnos, ausencias (sin diagnósticos), matriz de responsabilidades, equipos asignados, carné QR o NFC y jornada',
    'nomina': 'Conceptos, periodos, novedades, liquidación, prestaciones, PILA, nómina electrónica (apagada) y pagos con doble aprobación',
    'formacion': 'Cursos, lecciones, evaluaciones, sesiones presenciales, certificados y habilitaciones que permiten asignar tareas',
    'activos': 'Hoja de vida de equipos, planes y órdenes de mantenimiento, uso, repuestos y depreciación',
    'documental': 'Documentos con versiones, aprobación, vencimiento y vínculos; los agentes solo leen la versión aprobada y vigente',
    'cumplimiento': 'Normas (granja avícola biosegura, BPA, GLOBALG.A.P.), requisitos, expediente, evidencias, auditorías y acciones correctivas',
    'seguros': 'Pólizas, bienes asegurados, índices de seguros paramétricos y avisos de siniestro con evidencia',
    'seguridad': 'Doble factor, sesiones, intentos de acceso, detector de ataques, señuelos, bloqueos, alertas, incidentes, pruebas y copias de seguridad',
    'crm': 'Posibles clientes (personas y empresas), formularios de captura con autorización de datos, campañas, interacciones y oportunidades',
    'estrategia': 'Líneas de negocio, DOFA, estudios de mercado, iniciativas de crecimiento, evaluación de proyectos (VPN, TIR, ROI, palancas) y reinversión de utilidades',
    'agenda': 'Recursos agendables (cabañas, salón, vehículos, equipos), calendario sin cruces, visitas programadas e ingresos y salidas de personas y vehículos',
    'proyectos': 'Dirección de proyectos (PMBOK 8): acta, interesados, EDT, cronograma con ruta crítica, iteraciones, riesgos, cambios, líneas base y valor ganado',
}

T = []  # (esquema, tabla, fase, descripcion, columnas, extras)


def tabla(esq, nombre, fase, desc, cols, extras=(), auditoria=True):
    """Declara una tabla: esquema, nombre, fase del plan, descripción, columnas, restricciones extra y si se audita."""
    T.append((esq, nombre, fase, desc, cols, list(extras), auditoria))


USR = 'fk:nucleo.usuario'
# ---------------------------------------------------------------- núcleo
tabla('nucleo', 'usuario', 1, 'Persona que entra al sistema (administrador, operario, contador, cliente con cuenta). Reemplaza el usuario de Django (AUTH_USER_MODEL).', [
    ('nombre_completo', 'varchar(150)', 'not null', 'Nombre y apellidos como se muestran en pantalla'),
    ('correo', 'citext', 'not null unique', 'Correo con el que inicia sesión; no distingue mayúsculas'),
    ('telefono', 'varchar(20)', '', 'Celular en formato internacional, ej. +573001234567'),
    ('contrasena_hash', 'varchar(255)', 'not null', 'Contraseña cifrada con Argon2; nunca se guarda en claro'),
    ('es_superusuario', 'boolean', 'not null default false', 'Tiene todos los permisos (solo el dueño del sistema)'),
    ('activo', 'boolean', 'not null default true', 'Si es falso no puede iniciar sesión (se desactiva en vez de borrar)'),
    ('ultimo_ingreso', 'timestamptz', '', 'Fecha y hora del último inicio de sesión'),
    ('tercero_id', 'fk:terceros.tercero', '', 'Persona en el registro de terceros a la que corresponde, si aplica'),
])
tabla('nucleo', 'rol', 1, 'Conjunto de permisos que se asigna a usuarios o agentes (administrador, operario de granja, contador, vendedor).', [
    ('codigo', 'varchar(40)', 'not null unique', 'Código corto en minúscula, ej. administrador, operario_granja'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre visible del rol'),
    ('descripcion', 'text', '', 'Qué puede hacer quien tiene este rol'),
])
tabla('nucleo', 'permiso', 1, 'Acción concreta que se puede autorizar, por módulo (ej. comercial.aprobar_precio).', [
    ('codigo', 'varchar(80)', 'not null unique', 'Código módulo.accion, ej. comercial.aprobar_precio'),
    ('nombre', 'varchar(120)', 'not null', 'Descripción corta de la acción'),
    ('modulo', 'varchar(40)', 'not null', 'Módulo al que pertenece (esquema)'),
])
tabla('nucleo', 'rol_permiso', 1, 'Qué permisos tiene cada rol (relación muchos a muchos).', [
    ('rol_id', 'fk:nucleo.rol', 'not null', 'Rol'),
    ('permiso_id', 'fk:nucleo.permiso', 'not null', 'Permiso concedido al rol'),
], ['unique (rol_id, permiso_id)'], auditoria=False)
tabla('nucleo', 'usuario_rol', 1, 'Qué roles tiene cada usuario en cada finca (un usuario puede trabajar en varias fincas con roles distintos).', [
    ('usuario_id', USR, 'not null', 'Usuario'),
    ('rol_id', 'fk:nucleo.rol', 'not null', 'Rol asignado'),
], ['unique (usuario_id, rol_id)'], auditoria=False)
tabla('nucleo', 'parametro', 1, 'Valores de negocio que cambian con el tiempo (IVA, salario mínimo, tarifa de domicilio, margen mínimo). Nunca van fijos en el código.', [
    ('clave', 'varchar(80)', 'not null', 'Nombre del parámetro, ej. salario_minimo, iva_general, margen_minimo_huevo'),
    ('valor', 'text', 'not null', 'Valor como texto; se interpreta según tipo_dato'),
    ('tipo_dato', 'enum:entero,decimal,porcentaje,dinero,texto,booleano,json', 'not null', 'Cómo interpretar el valor'),
    ('vigente_desde', 'date', 'not null', 'Primer día en que aplica'),
    ('vigente_hasta', 'date', '', 'Último día en que aplica; vacío = vigente hoy'),
    ('descripcion', 'text', '', 'Para qué se usa y de dónde sale (norma, decreto, decisión)'),
], ['unique (clave, vigente_desde)'])
tabla('nucleo', 'auditoria', 1, 'Registro inalterable de cada cambio importante: quién (persona o agente), qué, cuándo y cómo estaba antes. Particionada por mes.', [
    ('esquema_tabla', 'varchar(80)', 'not null', 'Tabla afectada, ej. comercial.precio_producto'),
    ('registro_id', 'bigint', 'not null', 'Id del registro afectado'),
    ('accion', 'enum:crear,actualizar,eliminar,aprobar,rechazar,iniciar_sesion,exportar', 'not null', 'Tipo de acción'),
    ('datos_antes', 'jsonb', '', 'Valores antes del cambio'),
    ('datos_despues', 'jsonb', '', 'Valores después del cambio'),
    ('usuario_id', USR, '', 'Persona que hizo o aprobó la acción'),
    ('agente_id', 'fk:ia.agente', '', 'Agente de IA que la propuso o ejecutó, si aplica'),
    ('direccion_ip', 'inet', '', 'IP de origen'),
    ('ocurrido_en', 'timestamptz', 'not null default now()', 'Momento exacto del cambio'),
], ['partition by range (ocurrido_en)'], auditoria=False)
tabla('nucleo', 'evento_salida', 1, 'Bandeja de salida (patrón outbox): cada hecho de negocio se escribe aquí en la misma transacción y luego se publica a MongoDB, a los agentes y a otros servicios.', [
    ('tipo_evento', 'varchar(80)', 'not null', 'Nombre del hecho, ej. pedido.confirmado, precio.aprobado'),
    ('entidad', 'varchar(80)', 'not null', 'Tabla de origen'),
    ('entidad_id', 'bigint', 'not null', 'Id del registro de origen'),
    ('carga', 'jsonb', 'not null', 'Datos del evento'),
    ('estado', "enum:pendiente,publicado,fallido", "not null default 'pendiente'", 'Si ya se entregó a los consumidores'),
    ('intentos', 'smallint', 'not null default 0', 'Veces que se intentó publicar'),
    ('publicado_en', 'timestamptz', '', 'Cuándo se publicó'),
], ['index on (estado, creado_en)'])
tabla('nucleo', 'predio', 1, 'Finca o terreno donde opera el sistema (permite replicarlo en otras fincas).', [
    ('nombre', 'varchar(120)', 'not null', 'Nombre de la finca, ej. El Guayacán de los Malaver'),
    ('matricula_inmobiliaria', 'varchar(40)', '', 'Número de matrícula del certificado de tradición'),
    ('propietario', 'varchar(150)', '', 'Titular del predio según el certificado'),
    ('tenencia', "enum:propio,comodato,arriendo,otro", 'not null', 'Cómo se usa el predio'),
    ('area_m2', 'numeric(12,2)', '', 'Área total en metros cuadrados'),
    ('codigo_dane_municipio', 'char(5)', '', 'Código DANE del municipio (Nilo = 25488)'),
    ('vereda', 'varchar(80)', '', 'Vereda'),
    ('geometria', 'geometry(MultiPolygon, 9377)', '', 'Linderos en el sistema de coordenadas oficial CTM12 (EPSG 9377)'),
    ('es_practica', 'boolean', 'not null default false', 'Finca de práctica para el modo aprendiz: datos de ejemplo aislados de la finca real'),
    ('regimen_tributario', "enum:por_definir,ordinario,simple,no_responsable", "not null default 'por_definir'", 'Régimen del empleador (lo confirma el contador); define si la nómina electrónica es obligatoria'),
    ('empleador_tercero_id', 'fk:terceros.tercero', '', 'Persona o empresa que figura como empleador'),
])
tabla('nucleo', 'zona', 1, 'Área dentro del predio con un uso (galpón, aprisco, estanque, lote de cultivo, potrero, bodega, ronda hídrica).', [
    ('predio_id', 'fk:nucleo.predio', 'not null', 'Predio al que pertenece'),
    ('codigo', 'varchar(20)', 'not null', 'Código corto, ej. GAL-01, EST-02, LOT-C3'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre descriptivo'),
    ('tipo_zona', 'enum:galpon,aprisco,estanque,lote_cultivo,potrero,bodega,vivienda,ronda_hidrica,apiario,lombricultivo,biodigestor,otra', 'not null', 'Uso de la zona'),
    ('area_m2', 'numeric(12,2)', '', 'Área en metros cuadrados'),
    ('capacidad', 'integer', '', 'Capacidad máxima (aves, animales, plantas o m³ según el tipo)'),
    ('geometria', 'geometry(Polygon, 9377)', '', 'Polígono de la zona en CTM12'),
    ('modelo_3d_url', 'varchar(300)', '', 'Modelo 3D de la zona en el almacén de archivos (gemelo digital, listo para cuando exista el levantamiento)'),
    ('activa', 'boolean', 'not null default true', 'Si está en uso'),
], ['unique (predio_id, codigo)'])

# ---------------------------------------------------------------- terceros
tabla('terceros', 'tercero', 1, 'Toda persona natural o jurídica con la que se relaciona la finca. Un mismo tercero puede ser cliente, proveedor y empleado a la vez.', [
    ('tipo_persona', 'enum:natural,juridica', 'not null', 'Persona natural o empresa'),
    ('tipo_documento', 'enum:CC,CE,NIT,PAS,TI,PPT', '', 'Tipo de documento según la DIAN'),
    ('numero_documento', 'varchar(20)', '', 'Número de documento sin puntos'),
    ('digito_verificacion', 'char(1)', '', 'Dígito de verificación del NIT'),
    ('nombres', 'varchar(120)', '', 'Nombres (persona natural)'),
    ('apellidos', 'varchar(120)', '', 'Apellidos (persona natural)'),
    ('razon_social', 'varchar(200)', '', 'Nombre de la empresa (persona jurídica)'),
    ('correo', 'citext', '', 'Correo de contacto'),
    ('telefono', 'varchar(20)', '', 'Teléfono'),
    ('whatsapp', 'varchar(20)', '', 'Número de WhatsApp en formato internacional'),
    ('direccion', 'varchar(200)', '', 'Dirección o indicación rural'),
    ('codigo_dane_municipio', 'char(5)', '', 'Municipio según DANE'),
    ('es_cliente', 'boolean', 'not null default false', 'Marca rápida de rol'),
    ('es_proveedor', 'boolean', 'not null default false', 'Marca rápida de rol'),
    ('es_empleado', 'boolean', 'not null default false', 'Marca rápida de rol'),
], ['unique (tipo_documento, numero_documento)'])
tabla('terceros', 'consentimiento_datos', 1, 'Autorización de tratamiento de datos personales (Ley 1581 de 2012) por finalidad. Sin consentimiento vigente los agentes no personalizan ni envían publicidad.', [
    ('tercero_id', 'fk:terceros.tercero', 'not null', 'Titular de los datos'),
    ('finalidad', 'enum:atencion_pedidos,publicidad,personalizacion_ofertas,analitica,imagen_redes,biometria_acceso', 'not null', 'Para qué se autoriza el uso'),
    ('version_politica', 'varchar(20)', 'not null', 'Versión de la política de tratamiento aceptada'),
    ('otorgado', 'boolean', 'not null', 'Verdadero si autorizó, falso si negó'),
    ('medio', 'enum:whatsapp,web,formulario_fisico,verbal_grabado,correo', 'not null', 'Cómo se obtuvo'),
    ('evidencia_url', 'varchar(300)', '', 'Ubicación de la prueba en el almacén de archivos'),
    ('otorgado_en', 'timestamptz', 'not null', 'Cuándo se dio la respuesta'),
    ('revocado_en', 'timestamptz', '', 'Cuándo la retiró; vacío = vigente'),
])
tabla('terceros', 'cliente', 1, 'Datos comerciales del tercero que compra.', [
    ('tercero_id', 'fk:terceros.tercero', 'not null unique', 'Tercero'),
    ('segmento', 'enum:hogar,tienda,restaurante,hotel,asadero,carniceria,mayorista,turista,otro', 'not null', 'Tipo de cliente (restaurante y hotel forman el canal HORECA)'),
    ('canal_origen', 'enum:whatsapp,web,redes,referido,mercado_campesino,finca,otro', '', 'Por dónde llegó'),
    ('frecuencia_compra_dias', 'smallint', '', 'Cada cuántos días suele comprar (calculado)'),
    ('fecha_primera_compra', 'date', '', 'Primera compra'),
    ('cupo_credito', 'dinero', 'not null default 0', 'Monto máximo de cartera abierta (solo aplica si la función venta_credito está activa)'),
    ('dias_plazo', 'smallint', 'not null default 0', 'Días de plazo para pagar una factura a crédito'),
    ('bloqueado_por_mora', 'boolean', 'not null default false', 'Si tiene facturas vencidas sin pagar no puede comprar a crédito'),
    ('lista_precios_id', 'fk:comercial.lista_precios', '', 'Lista de precios que le aplica'),
    ('perfil_interes_ref', 'varchar(24)', '', 'Id del documento en MongoDB perfiles_interes'),
])
tabla('terceros', 'proveedor', 1, 'Datos de compra del tercero que vende insumos o servicios.', [
    ('tercero_id', 'fk:terceros.tercero', 'not null unique', 'Tercero'),
    ('categoria', 'enum:concentrado,animales,semillas,medicamentos,materiales,servicios,transporte,otro', 'not null', 'Qué suministra'),
    ('dias_credito', 'smallint', 'not null default 0', 'Días de plazo que concede'),
    ('calificacion', 'numeric(3,2)', '', 'Calificación de 1 a 5 (precio, puntualidad, calidad)'),
])
tabla('terceros', 'empleado', 1, 'Persona que trabaja en la finca, con su forma de vinculación.', [
    ('tercero_id', 'fk:terceros.tercero', 'not null unique', 'Tercero'),
    ('cargo', 'varchar(80)', 'not null', 'Cargo, ej. operario de granja'),
    ('tipo_vinculacion', 'enum:termino_fijo,termino_indefinido,jornal,prestacion_servicios,aprendiz', 'not null', 'Tipo de contrato'),
    ('salario_base', 'dinero', '', 'Salario mensual o valor del jornal'),
    ('forma_pago', "enum:salario,jornal,destajo,mixto", "not null default 'salario'", 'Cómo se le paga; el salario fijo nunca depende de tareas aprobadas'),
    ('valor_jornal', 'dinero', '', 'Valor del jornal, si se le paga por día'),
    ('ruta_aprendizaje', 'varchar(60)', '', 'Ruta de formación por cargo, ej. operario_galpon'),
    ('fecha_ingreso', 'date', 'not null', 'Inicio'),
    ('fecha_retiro', 'date', '', 'Fin; vacío = activo'),
])

# ---------------------------------------------------------------- producción
tabla('produccion', 'especie', 1, 'Catálogo de especies animales que maneja la finca.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. gallina, ovino, caprino, tilapia, abeja, lombriz'),
    ('nombre_comun', 'varchar(80)', 'not null', 'Nombre común'),
    ('nombre_cientifico', 'varchar(120)', '', 'Nombre científico'),
    ('grupo', 'enum:ave,ovino,caprino,pez,abeja,lombriz,otro', 'not null', 'Grupo productivo'),
    ('manejo_individual', 'boolean', 'not null default false', 'Si se registra animal por animal (ovinos, caprinos) o solo por lote (aves, peces)'),
])
tabla('produccion', 'lote_animal', 1, 'Grupo de animales que entra junto y se maneja junto (un lote de 100 gallinas, un ciclo de 1.000 alevinos, un rebaño).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. AV-2026-01'),
    ('especie_id', 'fk:produccion.especie', 'not null', 'Especie'),
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Galpón, aprisco o estanque donde está'),
    ('raza_linea', 'varchar(80)', '', 'Raza o línea genética'),
    ('proposito', 'enum:postura,engorde,cria,reproduccion,miel,humus', 'not null', 'Para qué se tiene'),
    ('fecha_ingreso', 'date', 'not null', 'Fecha de llegada o nacimiento'),
    ('edad_ingreso_semanas', 'smallint', '', 'Edad al llegar'),
    ('cantidad_inicial', 'integer', 'not null', 'Animales al ingresar'),
    ('cantidad_actual', 'integer', 'not null', 'Animales vivos hoy (se actualiza con mortalidad, ventas y nacimientos)'),
    ('costo_ingreso', 'dinero', '', 'Costo total de compra del lote'),
    ('estado', "enum:activo,cerrado", "not null default 'activo'", 'Activo o cerrado (vendido o descartado)'),
    ('fecha_cierre', 'date', '', 'Fecha de cierre'),
])
tabla('produccion', 'animal', 1, 'Animal identificado individualmente (ovinos y caprinos), con su genealogía.', [
    ('lote_animal_id', 'fk:produccion.lote_animal', 'not null', 'Lote o rebaño al que pertenece'),
    ('identificador', 'varchar(20)', 'not null unique', 'Número de arete o chapeta'),
    ('sexo', 'enum:hembra,macho', 'not null', 'Sexo'),
    ('fecha_nacimiento', 'date', '', 'Nacimiento'),
    ('madre_id', 'fk:produccion.animal', '', 'Madre, si nació en la finca'),
    ('padre_id', 'fk:produccion.animal', '', 'Padre, si se conoce'),
    ('estado', "enum:activo,vendido,muerto,descartado", "not null default 'activo'", 'Situación actual'),
])
tabla('produccion', 'registro_postura', 1, 'Huevos recogidos por día y por lote; las categorías por peso se registran en clasificacion_postura.', [
    ('lote_animal_id', 'fk:produccion.lote_animal', 'not null', 'Lote de gallinas'),
    ('fecha', 'date', 'not null', 'Día de recolección'),
    ('huevos_recogidos', 'integer', 'not null', 'Total de huevos recogidos en el día'),
    ('huevos_rotos', 'integer', 'not null default 0', 'Rotos o sucios (no vendibles); la clasificación de los buenos va en clasificacion_postura'),
    ('registrado_por', USR, 'not null', 'Quien registró'),
], ['unique (lote_animal_id, fecha)', 'check (huevos_rotos between 0 and huevos_recogidos)'])
tabla('produccion', 'registro_alimentacion', 1, 'Alimento suministrado a un lote, distinguiendo lo comprado de lo producido en la finca (base para medir el ahorro).', [
    ('lote_animal_id', 'fk:produccion.lote_animal', 'not null', 'Lote alimentado'),
    ('fecha', 'date', 'not null', 'Día'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Alimento (concentrado, maíz, forraje, lombriz)'),
    ('cantidad_kg', 'numeric(10,2)', 'not null', 'Kilogramos suministrados'),
    ('origen', 'enum:comprado,propio', 'not null', 'Comprado o producido en la finca'),
])
tabla('produccion', 'evento_sanitario', 1, 'Vacunas, desparasitaciones, tratamientos, revisiones y muertes.', [
    ('lote_animal_id', 'fk:produccion.lote_animal', 'not null', 'Lote afectado'),
    ('animal_id', 'fk:produccion.animal', '', 'Animal, si el evento es individual'),
    ('fecha', 'date', 'not null', 'Día'),
    ('tipo', 'enum:vacuna,desparasitacion,tratamiento,revision,mortalidad,descarte', 'not null', 'Tipo de evento'),
    ('producto_id', 'fk:inventario.producto', '', 'Medicamento o vacuna usada'),
    ('dosis', 'varchar(40)', '', 'Dosis aplicada'),
    ('cantidad_afectada', 'integer', 'not null default 1', 'Animales tratados o muertos'),
    ('causa', 'varchar(150)', '', 'Diagnóstico o causa probable'),
    ('responsable', 'varchar(120)', '', 'Quien lo aplicó (operario, veterinario)'),
])
tabla('produccion', 'registro_pesaje', 1, 'Pesos de animales o muestras de un lote (corderos, cabritos, tilapia).', [
    ('lote_animal_id', 'fk:produccion.lote_animal', 'not null', 'Lote'),
    ('animal_id', 'fk:produccion.animal', '', 'Animal pesado, si es individual'),
    ('fecha', 'date', 'not null', 'Día'),
    ('animales_muestreados', 'integer', 'not null default 1', 'Cuántos se pesaron'),
    ('peso_promedio_kg', 'numeric(8,3)', 'not null', 'Peso promedio en kg'),
])
tabla('produccion', 'evento_reproductivo', 1, 'Montas, partos, abortos y destetes de ovinos y caprinos.', [
    ('hembra_id', 'fk:produccion.animal', 'not null', 'Hembra'),
    ('macho_id', 'fk:produccion.animal', '', 'Macho, en montas'),
    ('tipo', 'enum:monta,parto,aborto,destete', 'not null', 'Tipo de evento'),
    ('fecha', 'date', 'not null', 'Día'),
    ('crias_vivas', 'smallint', '', 'Crías vivas (partos)'),
    ('crias_muertas', 'smallint', '', 'Crías muertas (partos)'),
])
tabla('produccion', 'calidad_agua_estanque', 1, 'Mediciones del agua de los estanques de peces.', [
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Estanque'),
    ('medido_en', 'timestamptz', 'not null', 'Fecha y hora'),
    ('oxigeno_mg_l', 'numeric(5,2)', '', 'Oxígeno disuelto en mg/L'),
    ('temperatura_c', 'numeric(4,1)', '', 'Temperatura en °C'),
    ('ph', 'numeric(4,2)', '', 'pH'),
    ('amonio_mg_l', 'numeric(5,2)', '', 'Amonio en mg/L'),
])
tabla('produccion', 'cultivo', 1, 'Catálogo de cultivos (plátano, cacao, aguacate papelillo, maíz, frijol, calabacín, forrajes).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. platano, cacao, maiz'),
    ('nombre_comun', 'varchar(80)', 'not null', 'Nombre común'),
    ('nombre_cientifico', 'varchar(120)', '', 'Nombre científico'),
    ('tipo_ciclo', 'enum:corto,perenne,forraje', 'not null', 'Ciclo corto, perenne o forraje'),
    ('dias_a_primera_cosecha', 'integer', '', 'Días desde la siembra hasta la primera cosecha'),
])
tabla('produccion', 'siembra', 1, 'Una siembra en una zona: cuántas plantas se sembraron y cuántas siguen vivas (ej. 5.000 plátanos previstos, 600 vivos).', [
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Lote de cultivo'),
    ('cultivo_id', 'fk:produccion.cultivo', 'not null', 'Cultivo'),
    ('variedad', 'varchar(80)', '', 'Variedad, ej. papelillo, hartón'),
    ('fecha_siembra', 'date', 'not null', 'Fecha de siembra'),
    ('plantas_previstas', 'integer', '', 'Plantas planeadas'),
    ('plantas_sembradas', 'integer', '', 'Plantas sembradas'),
    ('plantas_vivas', 'integer', '', 'Plantas vivas en el último conteo'),
    ('semilla_kg', 'numeric(10,2)', '', 'Semilla usada en kg (granos)'),
    ('area_m2', 'numeric(12,2)', '', 'Área sembrada'),
    ('fecha_estimada_cosecha', 'date', '', 'Primera cosecha esperada'),
    ('estado', "enum:planeada,sembrada,en_produccion,recuperacion,perdida,finalizada", "not null default 'sembrada'", 'Situación actual'),
    ('observaciones', 'text', '', 'Notas (ej. pérdidas por fenómeno de El Niño)'),
])
tabla('produccion', 'labor_cultural', 1, 'Trabajo hecho a una siembra: encalado, fertilización, deshierbe, control de plagas, poda, resiembra.', [
    ('siembra_id', 'fk:produccion.siembra', 'not null', 'Siembra'),
    ('fecha', 'date', 'not null', 'Día'),
    ('tipo', 'enum:encalado,fertilizacion,deshierbe,control_plagas,poda,resiembra,aporque,conteo', 'not null', 'Tipo de labor'),
    ('producto_id', 'fk:inventario.producto', '', 'Insumo usado'),
    ('cantidad', 'numeric(10,2)', '', 'Cantidad de insumo'),
    ('jornales', 'numeric(5,2)', '', 'Jornales empleados'),
    ('metodo', "enum:manual,mecanico,robot,dron", "not null default 'manual'", 'Cómo se hizo (robot y dron llegan por la interfaz RobotCampo)'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea de la que salió'),
    ('mision_robot_id', 'fk:iot.mision_robot', '', 'Misión de robot o dron que la hizo'),
    ('observaciones', 'text', '', 'Notas'),
], ["check (metodo not in ('robot', 'dron') or mision_robot_id is not null)"])
tabla('produccion', 'cosecha', 1, 'Producto cosechado y a dónde se fue (venta, alimento para los animales, semilla o pérdida).', [
    ('siembra_id', 'fk:produccion.siembra', 'not null', 'Siembra'),
    ('fecha', 'date', 'not null', 'Día'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto resultante'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad'),
    ('destino', 'enum:venta,alimento_animal,semilla,autoconsumo,perdida', 'not null', 'Destino'),
    ('lote_inventario_id', 'fk:inventario.lote_inventario', '', 'Lote de inventario creado al entrar a bodega'),
])
tabla('produccion', 'analisis_suelo', 1, 'Resultados de laboratorio del suelo de una zona y la recomendación de encalado.', [
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Zona muestreada'),
    ('fecha_muestreo', 'date', 'not null', 'Fecha de la muestra'),
    ('laboratorio', 'varchar(120)', '', 'Laboratorio'),
    ('ph', 'numeric(4,2)', '', 'pH'),
    ('materia_organica_pct', 'numeric(5,2)', '', 'Materia orgánica %'),
    ('aluminio_cmol_kg', 'numeric(6,2)', '', 'Aluminio intercambiable cmol/kg'),
    ('resultados', 'jsonb', '', 'Demás elementos (P, K, Ca, Mg...)'),
    ('recomendacion', 'text', '', 'Recomendación del agrónomo'),
    ('archivo_url', 'varchar(300)', '', 'PDF del resultado'),
])

# ---------------------------------------------------------------- riego
tabla('riego', 'fuente_agua', 1, 'De dónde sale el agua (nacedero, acueducto veredal, lluvia, pozo) y su permiso.', [
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('tipo', 'enum:nacedero,acueducto_veredal,lluvia,pozo,quebrada', 'not null', 'Tipo de fuente'),
    ('caudal_l_s', 'numeric(8,3)', '', 'Caudal disponible en litros por segundo'),
    ('requiere_concesion', 'boolean', 'not null default true', 'Si necesita concesión de la CAR'),
    ('numero_concesion', 'varchar(40)', '', 'Número de resolución de la CAR; vacío = en trámite'),
    ('concesion_vence', 'date', '', 'Vencimiento de la concesión'),
    ('apta_consumo_humano', 'boolean', 'not null default false', 'Si el último análisis la declara potable'),
])
tabla('riego', 'tanque', 1, 'Tanques de almacenamiento (hoy: dos de 2.000 litros).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. TQ-01'),
    ('capacidad_litros', 'integer', 'not null', 'Capacidad'),
    ('fuente_agua_id', 'fk:riego.fuente_agua', '', 'Fuente que lo llena'),
    ('zona_id', 'fk:nucleo.zona', '', 'Ubicación'),
    ('sensor_nivel_id', 'fk:iot.sensor', '', 'Sensor de nivel (fase IoT)'),
])
tabla('riego', 'sistema_riego', 1, 'Red de riego que cubre una o varias zonas (hoy: manguera con aspersores).', [
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('tipo', 'enum:aspersion,goteo,microaspersion,manual', 'not null', 'Tecnología'),
    ('tanque_id', 'fk:riego.tanque', '', 'Tanque que lo alimenta'),
    ('caudal_l_min', 'numeric(8,2)', '', 'Caudal nominal'),
    ('modo_control', "enum:manual,programado,automatico", "not null default 'manual'", 'Cómo se acciona hoy'),
])
tabla('riego', 'valvula', 1, 'Cada válvula del sistema (hoy manual en cada aspersor; luego electroválvula).', [
    ('sistema_riego_id', 'fk:riego.sistema_riego', 'not null', 'Sistema al que pertenece'),
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. V-03'),
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Zona que riega'),
    ('tipo', "enum:manual,electrovalvula", "not null default 'manual'", 'Manual o eléctrica'),
    ('actuador_id', 'fk:iot.actuador', '', 'Actuador IoT que la abre (fase IoT)'),
])
tabla('riego', 'evento_riego', 1, 'Cada riego hecho: cuánto tiempo, cuánta agua y si fue manual o automático.', [
    ('valvula_id', 'fk:riego.valvula', 'not null', 'Válvula abierta'),
    ('inicio', 'timestamptz', 'not null', 'Apertura'),
    ('fin', 'timestamptz', '', 'Cierre'),
    ('litros_estimados', 'numeric(10,1)', '', 'Litros aplicados (caudal × tiempo)'),
    ('modo', 'enum:manual,programado,automatico', 'not null', 'Quién lo accionó'),
    ('registrado_por', USR, '', 'Operario, si fue manual'),
    ('regla_id', 'fk:iot.regla_automatizacion', '', 'Regla que lo disparó, si fue automático'),
])

# ---------------------------------------------------------------- inventario
tabla('inventario', 'unidad_medida', 1, 'Unidades (kg, cubeta, unidad, bulto, litro) y su conversión a la unidad base.', [
    ('codigo', 'varchar(10)', 'not null unique', 'Código, ej. kg, cub30, und, bul40'),
    ('nombre', 'varchar(40)', 'not null', 'Nombre'),
    ('unidad_base', 'varchar(10)', '', 'Unidad a la que se convierte, ej. und o kg'),
    ('factor_base', 'numeric(12,4)', 'not null default 1', 'Cuántas unidades base contiene (cubeta = 30 und)'),
])
tabla('inventario', 'categoria_producto', 1, 'Agrupación jerárquica de productos (huevo, carne en pie, granos, insumos, medicamentos).', [
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('padre_id', 'fk:inventario.categoria_producto', '', 'Categoría superior'),
])
tabla('inventario', 'producto', 1, 'Todo lo que se vende, se compra o se produce: cubeta de huevo, kg de tilapia, bulto de concentrado.', [
    ('sku', 'varchar(30)', 'not null unique', 'Código interno, ej. HUE-AA-30'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre comercial'),
    ('descripcion', 'text', '', 'Descripción para el catálogo y para los agentes'),
    ('categoria_id', 'fk:inventario.categoria_producto', 'not null', 'Categoría'),
    ('unidad_id', 'fk:inventario.unidad_medida', 'not null', 'Unidad de venta o de control'),
    ('tipo', 'enum:producto_terminado,insumo,servicio,activo_menor', 'not null', 'Naturaleza'),
    ('se_vende', 'boolean', 'not null default false', 'Aparece en el catálogo'),
    ('se_compra', 'boolean', 'not null default false', 'Se compra a proveedores'),
    ('se_produce', 'boolean', 'not null default false', 'Se produce en la finca'),
    ('perecedero', 'boolean', 'not null default false', 'Tiene vencimiento'),
    ('vida_util_ambiente_dias', 'smallint', '', 'Días que dura a temperatura ambiente (base para estimar el vencimiento)'),
    ('vida_util_refrigerado_dias', 'smallint', '', 'Días que dura refrigerado'),
    ('dias_margen_venta', 'smallint', 'not null default 0', 'Días antes del vencimiento en que se deja de vender (fecha límite de venta)'),
    ('dias_alerta_venta', 'smallint', 'not null default 0', 'Días antes de la fecha límite de venta en que se activa la alerta para venderlo primero'),
    ('metodo_salida', "enum:fefo,fifo", "not null default 'fefo'", 'Orden de salida: fefo = primero lo que vence primero; fifo = primero lo que entró primero'),
    ('gtin', 'varchar(14)', '', 'Código de barras comercial GS1 (EAN-13 o GTIN-14), si la finca lo obtiene; vacío = solo códigos internos'),
    ('pesable', 'boolean', 'not null default false', 'Se vende o controla por peso leído en báscula (tilapia, cordero en pie)'),
    ('peso_nominal_kg', 'numeric(10,3)', '', 'Peso esperado por unidad, para validar lo que marca la báscula (ej. cubeta)'),
    ('tolerancia_peso_pct', 'numeric(5,2)', '', 'Diferencia máxima aceptada contra el peso nominal antes de alertar'),
    ('tarifa_iva', 'numeric(5,2)', 'not null default 0', 'IVA en %: huevo y carne en pie están excluidos (0)'),
    ('stock_minimo', 'numeric(12,2)', '', 'Alerta de reposición'),
    ('activo', 'boolean', 'not null default true', 'Si se sigue usando'),
], ['check (dias_margen_venta >= 0 and dias_alerta_venta >= 0)'])
tabla('inventario', 'bodega', 1, 'Lugar físico donde se guarda inventario.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('zona_id', 'fk:nucleo.zona', '', 'Zona del predio'),
    ('refrigerada', 'boolean', 'not null default false', 'Nevera o cuarto frío; sus lotes usan la vida útil refrigerada'),
    ('sensor_temperatura_id', 'fk:iot.sensor', '', 'Sensor que vigila la temperatura (cadena de frío)'),
    ('temperatura_min_c', 'numeric(4,1)', '', 'Temperatura mínima aceptada en °C'),
    ('temperatura_max_c', 'numeric(4,1)', '', 'Temperatura máxima aceptada en °C'),
    ('minutos_tolerancia', 'smallint', 'not null default 30', 'Minutos fuera de rango antes de bloquear los lotes'),
])
tabla('inventario', 'lote_inventario', 1, 'Existencia concreta de un producto con fecha, origen y vencimiento. Sus cantidades solo las cambia el kardex (movimiento_inventario); la salida sigue el orden FEFO: primero lo que vence primero.', [
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('bodega_id', 'fk:inventario.bodega', 'not null', 'Bodega'),
    ('codigo_lote', 'varchar(30)', 'not null', 'Código de trazabilidad, ej. HUE-20261025-GAL01'),
    ('origen', 'enum:produccion,compra,ajuste', 'not null', 'De dónde salió'),
    ('origen_tabla', 'varchar(60)', '', 'Tabla de origen (cosecha, registro_postura, orden_compra_detalle)'),
    ('origen_id', 'bigint', '', 'Id en la tabla de origen'),
    ('fecha_produccion', 'date', 'not null', 'Fecha de producción, postura, cosecha o recepción'),
    ('condicion_almacenamiento', "enum:ambiente,refrigerado", "not null default 'ambiente'", 'Cómo se guarda; cambia la vida útil usada en la estimación'),
    ('origen_vencimiento', "enum:estimado,manual,laboratorio", "not null default 'estimado'", 'estimado = lo calcula el sistema con la vida útil del producto; manual o laboratorio = lo fija una persona'),
    ('fecha_vencimiento', 'date', '', 'Fecha en que el producto deja de ser apto (calculada si origen_vencimiento = estimado)'),
    ('fecha_limite_venta', 'date', '', 'Último día para venderlo: vencimiento menos los días de margen del producto'),
    ('peso_neto_kg', 'numeric(12,3)', '', 'Peso total leído en báscula al ingresar, si el producto es pesable'),
    ('cantidad_inicial', 'numeric(12,2)', 'not null', 'Cantidad al crearse (genera automáticamente el movimiento de entrada)'),
    ('cantidad_disponible', 'numeric(12,2)', 'not null default 0', 'Libre para vender; solo la cambia el kardex'),
    ('cantidad_reservada', 'numeric(12,2)', 'not null default 0', 'Comprometida en pedidos confirmados; solo la cambia el kardex'),
    ('costo_unitario', 'dinero', 'not null', 'Costo por unidad'),
    ('estado', "enum:disponible,agotado,vencido,bloqueado", "not null default 'disponible'", 'Situación: agotado y vencido los pone el sistema; bloqueado lo pone un bloqueo_lote abierto (cadena de frío, sanidad, retiro)'),
], ['unique (producto_id, codigo_lote)', 'check (cantidad_disponible >= 0 and cantidad_reservada >= 0)', 'index on (producto_id, estado, fecha_vencimiento)'])
tabla('inventario', 'movimiento_inventario', 1, 'Kardex: cada entrada, salida, ajuste, traslado o merma, con el documento que lo causó.', [
    ('lote_inventario_id', 'fk:inventario.lote_inventario', 'not null', 'Lote movido'),
    ('tipo', 'enum:entrada,reserva,liberacion,salida_venta,consumo_interno,merma,ajuste_entrada,ajuste_salida,traslado_salida,traslado_entrada', 'not null', 'Tipo de movimiento; define qué cantidad del lote cambia (ver reglas del kardex)'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad (siempre positiva; el tipo da el sentido)'),
    ('causa_merma', 'enum:vencido,roto,plaga,calidad,robo,otro', '', 'Por qué se perdió, cuando tipo = merma (alimenta el ajuste de la vida útil estimada)'),
    ('pesaje_id', 'fk:inventario.pesaje', '', 'Lectura de báscula que respalda la cantidad, si aplica'),
    ('lectura_codigo_id', 'fk:inventario.lectura_codigo', '', 'Escaneo de código que originó el movimiento, si aplica'),
    ('costo_unitario', 'dinero', 'not null', 'Costo usado'),
    ('documento_tipo', 'varchar(40)', 'not null', 'Documento origen, ej. pedido, cosecha, orden_compra'),
    ('documento_id', 'bigint', 'not null', 'Id del documento'),
    ('ocurrido_en', 'timestamptz', 'not null default now()', 'Momento'),
    ('usuario_id', USR, '', 'Quién lo registró'),
], ['index on (lote_inventario_id, ocurrido_en)'])

# ---------------------------------------------------------------- comercial
tabla('comercial', 'lista_precios', 1, 'Lista de precios por canal o tipo de cliente (público, tiendas, restaurantes, mayoristas).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. PUBLICO, TIENDAS'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
])
tabla('comercial', 'precio_producto', 1, 'Precio de un producto en una lista, con vigencia. Nunca se edita un precio: se cierra el vigente y se crea uno nuevo, así el historial queda completo.', [
    ('lista_precios_id', 'fk:comercial.lista_precios', 'not null', 'Lista'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('precio_unitario', 'dinero', 'not null', 'Precio por unidad de venta'),
    ('incluye_iva', 'boolean', 'not null default true', 'Si el precio ya incluye IVA'),
    ('vigente_desde', 'timestamptz', 'not null', 'Desde cuándo aplica'),
    ('vigente_hasta', 'timestamptz', '', 'Hasta cuándo; vacío = vigente'),
    ('propuesta_precio_id', 'fk:comercial.propuesta_precio', '', 'Propuesta que lo originó, si vino de un agente'),
    ('aprobado_por', USR, 'not null', 'Administrador que lo autorizó'),
], ['index on (producto_id, lista_precios_id, vigente_desde)'])
tabla('comercial', 'propuesta_precio', 1, 'Cambio de precio sugerido por el agente analista de mercados. Solo se aplica cuando el administrador lo aprueba.', [
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('lista_precios_id', 'fk:comercial.lista_precios', 'not null', 'Lista afectada'),
    ('precio_actual', 'dinero', 'not null', 'Precio vigente al proponer'),
    ('precio_propuesto', 'dinero', 'not null', 'Precio sugerido'),
    ('variacion_pct', 'numeric(6,2)', 'not null', 'Variación porcentual'),
    ('justificacion', 'text', 'not null', 'Razones en lenguaje claro'),
    ('evidencia', 'jsonb', 'not null', 'Fuentes consultadas (SIPSA, competidores, costos) con fecha y enlace'),
    ('agente_id', 'fk:ia.agente', '', 'Agente que la generó'),
    ('estado', "enum:pendiente,aprobada,rechazada,vencida,aplicada", "not null default 'pendiente'", 'Situación'),
    ('vence_en', 'timestamptz', 'not null', 'Si nadie la revisa antes, queda vencida'),
    ('revisado_por', USR, '', 'Administrador que decidió'),
    ('revisado_en', 'timestamptz', '', 'Cuándo decidió'),
    ('comentario_revision', 'text', '', 'Motivo de la decisión'),
    ('aplicada_en', 'timestamptz', '', 'Cuándo entró en vigencia'),
])
tabla('comercial', 'pedido', 1, 'Solicitud de compra de un cliente por cualquier canal; puede crearla una persona o un agente.', [
    ('numero', 'varchar(20)', 'not null unique', 'Consecutivo, ej. PED-000123'),
    ('cliente_id', 'fk:terceros.cliente', 'not null', 'Cliente'),
    ('canal', 'enum:whatsapp,web,redes,telefono,finca,mercado_campesino', 'not null', 'Canal'),
    ('estado', "enum:borrador,confirmado,en_preparacion,despachado,entregado,cancelado", "not null default 'borrador'", 'Situación'),
    ('forma_pago', "enum:contado,credito", "not null default 'contado'", 'Crédito exige la función venta_credito activa, cliente sin mora y cupo disponible'),
    ('pedido_recurrente_id', 'fk:comercial.pedido_recurrente', '', 'Pedido recurrente que lo generó, si aplica'),
    ('fecha_entrega_programada', 'date', '', 'Día de entrega acordado'),
    ('direccion_entrega', 'varchar(200)', '', 'Dirección de entrega'),
    ('subtotal', 'dinero', 'not null default 0', 'Suma de líneas sin impuestos'),
    ('descuento', 'dinero', 'not null default 0', 'Descuentos'),
    ('impuestos', 'dinero', 'not null default 0', 'IVA'),
    ('valor_domicilio', 'dinero', 'not null default 0', 'Cobro de entrega'),
    ('total', 'dinero', 'not null default 0', 'Total a pagar'),
    ('conversacion_ref', 'varchar(24)', '', 'Id de la conversación en MongoDB que originó el pedido'),
    ('creado_por_agente_id', 'fk:ia.agente', '', 'Agente que lo tomó, si aplica'),
    ('vendedor_id', USR, '', 'Persona responsable'),
])
tabla('comercial', 'pedido_detalle', 1, 'Línea del pedido. El precio queda congelado al confirmar: un cambio de precio posterior no la afecta.', [
    ('pedido_id', 'fk:comercial.pedido', 'not null', 'Pedido'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad (los lotes reservados quedan en comercial.reserva_lote)'),
    ('precio_producto_id', 'fk:comercial.precio_producto', 'not null', 'Precio vigente usado'),
    ('precio_unitario', 'dinero', 'not null', 'Precio copiado (congelado) al confirmar'),
    ('descuento', 'dinero', 'not null default 0', 'Descuento de la línea'),
    ('tarifa_iva', 'numeric(5,2)', 'not null default 0', 'IVA aplicado'),
    ('total_linea', 'dinero', 'not null', 'Total de la línea'),
])
tabla('comercial', 'factura', 1, 'Factura electrónica (o documento equivalente) generada por regla fija, no por la IA, y validada por la DIAN.', [
    ('prefijo', 'varchar(6)', 'not null', 'Prefijo autorizado por la DIAN'),
    ('numero', 'integer', 'not null', 'Número dentro del rango autorizado'),
    ('pedido_id', 'fk:comercial.pedido', '', 'Pedido facturado'),
    ('cliente_id', 'fk:terceros.cliente', 'not null', 'Cliente'),
    ('fecha_emision', 'timestamptz', 'not null', 'Fecha y hora de emisión'),
    ('subtotal', 'dinero', 'not null', 'Base'),
    ('iva', 'dinero', 'not null', 'IVA'),
    ('total', 'dinero', 'not null', 'Total'),
    ('forma_pago', 'enum:contado,credito', 'not null', 'Forma de pago'),
    ('fecha_vencimiento', 'date', '', 'Fecha límite de pago (crédito): emisión más los días de plazo del cliente'),
    ('saldo', 'dinero', 'not null default 0', 'Lo que falta por pagar; lo mantienen los pagos confirmados y las permutas'),
    ('cufe', 'varchar(96)', '', 'Código único de factura electrónica'),
    ('estado_dian', "enum:pendiente,aceptada,rechazada,no_aplica", "not null default 'pendiente'", 'Respuesta de la DIAN'),
    ('xml_url', 'varchar(300)', '', 'XML en el almacén de archivos'),
    ('pdf_url', 'varchar(300)', '', 'Representación gráfica'),
], ['unique (prefijo, numero)'])
tabla('comercial', 'pago', 1, 'Dinero recibido por un pedido o factura.', [
    ('pedido_id', 'fk:comercial.pedido', '', 'Pedido'),
    ('factura_id', 'fk:comercial.factura', '', 'Factura'),
    ('fecha', 'timestamptz', 'not null', 'Momento del pago'),
    ('valor', 'dinero', 'not null', 'Valor'),
    ('medio', 'enum:efectivo,nequi,daviplata,transferencia,tarjeta,bre_b,pasarela,compensacion_permuta', 'not null', 'Medio de pago; compensacion_permuta = saldado con una permuta'),
    ('proveedor_pasarela', 'enum:wompi,mercado_pago,epayco,payu', '', 'Pasarela de pago local, si medio = pasarela (Stripe no opera en Colombia)'),
    ('id_transaccion_pasarela', 'varchar(80)', '', 'Id de la transacción en la pasarela (llave de idempotencia del webhook)'),
    ('referencia', 'varchar(60)', '', 'Número de transacción'),
    ('estado', "enum:pendiente,confirmado,reversado", "not null default 'pendiente'", 'Situación'),
    ('confirmado_por', USR, '', 'Quién verificó el ingreso (un agente nunca confirma pagos)'),
], ['check (pedido_id is not null or factura_id is not null)'])
tabla('comercial', 'entrega', 1, 'Despacho de un pedido.', [
    ('pedido_id', 'fk:comercial.pedido', 'not null', 'Pedido'),
    ('fecha_salida', 'timestamptz', '', 'Salida de la finca'),
    ('fecha_entrega', 'timestamptz', '', 'Recepción por el cliente'),
    ('responsable', 'varchar(120)', '', 'Quien entrega'),
    ('vehiculo_id', 'fk:inventario.vehiculo', '', 'Vehículo usado (su registrador de temperatura vigila la cadena de frío en ruta)'),
    ('estado', "enum:programada,en_ruta,entregada,fallida", "not null default 'programada'", 'Situación'),
    ('evidencia_url', 'varchar(300)', '', 'Foto o firma'),
    ('calificacion_cliente', 'smallint', '', 'De 1 a 5'),
])

# ---------------------------------------------------------------- compras
tabla('compras', 'orden_compra', 1, 'Compra a un proveedor.', [
    ('numero', 'varchar(20)', 'not null unique', 'Consecutivo'),
    ('proveedor_id', 'fk:terceros.proveedor', 'not null', 'Proveedor'),
    ('fecha', 'date', 'not null', 'Fecha'),
    ('estado', "enum:borrador,aprobada,recibida,parcial,anulada", "not null default 'borrador'", 'Situación'),
    ('total', 'dinero', 'not null default 0', 'Total'),
    ('aprobado_por', USR, '', 'Quién la aprobó'),
])
tabla('compras', 'orden_compra_detalle', 1, 'Línea de la orden de compra.', [
    ('orden_compra_id', 'fk:compras.orden_compra', 'not null', 'Orden'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Insumo'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad pedida'),
    ('cantidad_recibida', 'numeric(12,2)', 'not null default 0', 'Cantidad recibida'),
    ('precio_unitario', 'dinero', 'not null', 'Precio pactado'),
])
tabla('compras', 'cotizacion_proveedor', 1, 'Precio ofrecido por un proveedor para un insumo, registrado por una persona o por el agente de mercados.', [
    ('proveedor_id', 'fk:terceros.proveedor', '', 'Proveedor, si está registrado'),
    ('nombre_proveedor', 'varchar(150)', '', 'Nombre si aún no es tercero'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Insumo'),
    ('precio_unitario', 'dinero', 'not null', 'Precio'),
    ('fecha', 'date', 'not null', 'Fecha de la cotización'),
    ('vigente_hasta', 'date', '', 'Validez'),
    ('fuente', 'enum:visita,telefono,correo,web,agente', 'not null', 'Cómo se obtuvo'),
    ('fuente_url', 'varchar(300)', '', 'Enlace, si es web'),
])
tabla('compras', 'precio_mercado', 1, 'Precio de referencia de un producto en un mercado (SIPSA-DANE, Corabastos, Fenavi), usado por el agente analista.', [
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto comparable'),
    ('mercado', 'varchar(80)', 'not null', 'Mercado o fuente, ej. Corabastos, SIPSA Girardot'),
    ('fecha', 'date', 'not null', 'Fecha del dato'),
    ('precio_minimo', 'dinero', '', 'Mínimo'),
    ('precio_maximo', 'dinero', '', 'Máximo'),
    ('precio_promedio', 'dinero', 'not null', 'Promedio'),
    ('unidad', 'varchar(20)', 'not null', 'Unidad del dato, ej. kg, cubeta'),
    ('fuente_url', 'varchar(300)', '', 'Enlace'),
], ['unique (producto_id, mercado, fecha)'])

# ---------------------------------------------------------------- finanzas
tabla('finanzas', 'cuenta_contable', 1, 'Plan Único de Cuentas (PUC) adaptado a la finca.', [
    ('codigo', 'varchar(10)', 'not null unique', 'Código PUC, ej. 413505'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre'),
    ('naturaleza', 'enum:debito,credito', 'not null', 'Naturaleza'),
    ('nivel', 'smallint', 'not null', '1 clase, 2 grupo, 3 cuenta, 4 subcuenta, 5 auxiliar'),
    ('padre_id', 'fk:finanzas.cuenta_contable', '', 'Cuenta superior'),
    ('acepta_movimiento', 'boolean', 'not null default false', 'Solo las auxiliares reciben movimientos'),
])
tabla('finanzas', 'centro_costo', 1, 'Unidad de negocio para medir rentabilidad (avícola, ovino-caprino, piscícola, ciclo corto, perennes, turismo, administración).', [
    ('codigo', 'varchar(10)', 'not null unique', 'Código, ej. AVI'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
])
tabla('finanzas', 'comprobante', 1, 'Documento contable (ingreso, egreso, nota, causación). Lo generan reglas a partir de ventas, compras y nómina; el agente contador solo sugiere.', [
    ('tipo', 'enum:ingreso,egreso,nota_contable,causacion,nomina,ajuste', 'not null', 'Tipo'),
    ('numero', 'varchar(20)', 'not null', 'Consecutivo por tipo'),
    ('fecha', 'date', 'not null', 'Fecha contable'),
    ('descripcion', 'text', 'not null', 'Concepto'),
    ('origen_tabla', 'varchar(60)', '', 'Documento de negocio que lo generó'),
    ('origen_id', 'bigint', '', 'Id del documento'),
    ('estado', "enum:borrador,contabilizado,anulado", "not null default 'borrador'", 'Situación; solo se contabiliza si débitos = créditos y el periodo está abierto'),
    ('aprobado_por', USR, '', 'Quien lo contabilizó'),
    ('contabilizado_en', 'timestamptz', '', 'Momento en que quedó contabilizado (desde ahí sus movimientos no se pueden cambiar)'),
    ('motivo_anulacion', 'text', '', 'Por qué se anuló'),
], ['unique (tipo, numero)'])
tabla('finanzas', 'movimiento_contable', 1, 'Línea débito o crédito de un comprobante.', [
    ('comprobante_id', 'fk:finanzas.comprobante', 'not null', 'Comprobante'),
    ('cuenta_id', 'fk:finanzas.cuenta_contable', 'not null', 'Cuenta'),
    ('tercero_id', 'fk:terceros.tercero', '', 'Tercero'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Centro de costo'),
    ('debito', 'dinero', 'not null default 0', 'Débito'),
    ('credito', 'dinero', 'not null default 0', 'Crédito'),
    ('detalle', 'varchar(200)', '', 'Detalle'),
], ['check (debito >= 0 and credito >= 0 and (debito = 0 or credito = 0))'])

# ---------------------------------------------------------------- ia
tabla('ia', 'agente', 1, 'Agente de IA con un rol, sus instrucciones versionadas, su modelo y su nivel de autonomía.', [
    ('codigo', 'varchar(40)', 'not null unique', 'Código, ej. asesor_clientes, analista_mercados'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre visible, ej. Asesor virtual'),
    ('rol', 'text', 'not null', 'Qué hace y qué no hace'),
    ('nivel_autonomia', 'enum:solo_lectura,propone,ejecuta_con_regla', 'not null', 'Hasta dónde puede actuar'),
    ('proveedor_modelo', 'varchar(40)', 'not null', 'Proveedor, ej. anthropic'),
    ('modelo', 'varchar(60)', 'not null', 'Modelo, ej. claude-sonnet-5-5'),
    ('modelo_respaldo', 'varchar(60)', '', 'Modelo si el principal falla'),
    ('version_instrucciones', 'varchar(20)', 'not null', 'Versión del prompt de sistema vigente'),
    ('instrucciones', 'text', 'not null', 'Prompt de sistema vigente'),
    ('limite_costo_diario_usd', 'numeric(8,2)', '', 'Tope de gasto por día'),
    ('activo', 'boolean', 'not null default true', 'Si atiende'),
])
tabla('ia', 'herramienta', 1, 'Función del ERP que un agente puede invocar (por MCP o API), con su nivel de riesgo.', [
    ('codigo', 'varchar(60)', 'not null unique', 'Código, ej. consultar_catalogo, proponer_precio'),
    ('descripcion', 'text', 'not null', 'Qué hace (es lo que lee el modelo)'),
    ('tipo', 'enum:lectura,propuesta,escritura', 'not null', 'Lectura no cambia nada; propuesta crea una solicitud; escritura cambia datos'),
    ('requiere_aprobacion', 'boolean', 'not null default false', 'Si cada uso pasa por un humano'),
    ('esquema_entrada', 'jsonb', 'not null', 'JSON Schema de los parámetros'),
])
tabla('ia', 'agente_herramienta', 1, 'Qué herramientas puede usar cada agente (mínimo privilegio).', [
    ('agente_id', 'fk:ia.agente', 'not null', 'Agente'),
    ('herramienta_id', 'fk:ia.herramienta', 'not null', 'Herramienta'),
], ['unique (agente_id, herramienta_id)'], auditoria=False)
tabla('ia', 'solicitud_aprobacion', 1, 'Bandeja del administrador: toda acción que un agente quiere hacer y requiere permiso humano.', [
    ('agente_id', 'fk:ia.agente', 'not null', 'Agente que pide'),
    ('herramienta_id', 'fk:ia.herramienta', 'not null', 'Acción solicitada'),
    ('entidad', 'varchar(60)', 'not null', 'Tabla afectada, ej. comercial.propuesta_precio'),
    ('entidad_id', 'bigint', '', 'Registro afectado'),
    ('resumen', 'text', 'not null', 'Qué se pide, en una frase'),
    ('carga', 'jsonb', 'not null', 'Parámetros exactos que se ejecutarán'),
    ('estado', "enum:pendiente,aprobada,rechazada,vencida,ejecutada,fallida", "not null default 'pendiente'", 'Situación'),
    ('vence_en', 'timestamptz', 'not null', 'Límite para decidir'),
    ('resuelto_por', USR, '', 'Quién decidió'),
    ('resuelto_en', 'timestamptz', '', 'Cuándo'),
    ('motivo', 'text', '', 'Motivo de la decisión'),
], ['index on (estado, vence_en)'])
tabla('ia', 'documento_conocimiento', 1, 'Fuente de la base de conocimiento: fichas de producto, políticas, preguntas frecuentes, manuales técnicos, informes.', [
    ('titulo', 'varchar(200)', 'not null', 'Título'),
    ('tipo', 'enum:ficha_producto,politica,pregunta_frecuente,manual_tecnico,informe,receta,turismo', 'not null', 'Tipo'),
    ('contenido', 'text', 'not null', 'Texto completo'),
    ('fuente', 'varchar(300)', '', 'Origen (archivo, URL, autor)'),
    ('version', 'smallint', 'not null default 1', 'Versión'),
    ('vigente', 'boolean', 'not null default true', 'Si los agentes lo usan'),
    ('aprobado_por', USR, '', 'Quién validó el contenido'),
])
tabla('ia', 'fragmento_conocimiento', 1, 'Trozo de un documento con su vector semántico (pgvector) para que los agentes encuentren la información relevante (RAG).', [
    ('documento_id', 'fk:ia.documento_conocimiento', 'not null', 'Documento'),
    ('orden', 'integer', 'not null', 'Posición dentro del documento'),
    ('texto', 'text', 'not null', 'Texto del fragmento'),
    ('vector', 'vector(1024)', 'not null', 'Representación numérica del significado (embedding)'),
    ('metadatos', 'jsonb', '', 'Producto, tema, vigencia'),
])
tabla('ia', 'recomendacion', 1, 'Plan de acción o mejora continua propuesto por un agente analista, con su seguimiento (ciclo PHVA).', [
    ('agente_id', 'fk:ia.agente', 'not null', 'Agente que la propone'),
    ('tipo', 'enum:mejora_continua,comercial,compra,produccion,contenido_redes,riesgo', 'not null', 'Tipo'),
    ('titulo', 'varchar(200)', 'not null', 'Título'),
    ('descripcion', 'text', 'not null', 'Qué hacer y por qué'),
    ('evidencia', 'jsonb', 'not null', 'Datos que la sustentan'),
    ('indicador', 'varchar(120)', '', 'Indicador que debería mejorar'),
    ('prioridad', 'enum:alta,media,baja', 'not null', 'Prioridad'),
    ('estado', "enum:nueva,aceptada,descartada,en_ejecucion,cumplida", "not null default 'nueva'", 'Situación'),
    ('responsable_id', USR, '', 'Responsable'),
    ('fecha_limite', 'date', '', 'Plazo'),
    ('resultado', 'text', '', 'Qué pasó al ejecutarla (aprendizaje)'),
])
tabla('ia', 'evaluacion_respuesta', 1, 'Calificación de una respuesta de un agente por el cliente o el administrador; alimenta la mejora de instrucciones y conocimiento.', [
    ('agente_id', 'fk:ia.agente', 'not null', 'Agente evaluado'),
    ('mensaje_ref', 'varchar(24)', 'not null', 'Id del mensaje en MongoDB'),
    ('origen', 'enum:cliente,administrador,evaluacion_automatica', 'not null', 'Quién califica'),
    ('calificacion', 'smallint', 'not null', 'De 1 a 5'),
    ('motivo', 'enum:correcta,incorrecta,incompleta,tono,demora,otro', '', 'Motivo'),
    ('comentario', 'text', '', 'Comentario'),
], ['check (calificacion between 1 and 5)'])
tabla('ia', 'consumo_ia', 1, 'Tokens y costo por agente, modelo y día, para controlar el gasto.', [
    ('agente_id', 'fk:ia.agente', 'not null', 'Agente'),
    ('fecha', 'date', 'not null', 'Día'),
    ('proveedor_modelo', 'varchar(40)', 'not null', 'Proveedor'),
    ('modelo', 'varchar(60)', 'not null', 'Modelo'),
    ('solicitudes', 'integer', 'not null default 0', 'Llamadas'),
    ('tokens_entrada', 'bigint', 'not null default 0', 'Tokens enviados'),
    ('tokens_salida', 'bigint', 'not null default 0', 'Tokens generados'),
    ('costo_usd', 'numeric(10,4)', 'not null default 0', 'Costo en dólares'),
], ['unique (agente_id, fecha, modelo)'])

# ---------------------------------------------------------------- redes
tabla('redes', 'cuenta_red', 1, 'Cuenta de la finca en un canal de mensajería o red social; las credenciales van en el gestor de secretos, no aquí.', [
    ('plataforma', 'fk_codigo:redes.politica_canal', 'not null', 'Canal (whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina)'),
    ('nombre_cuenta', 'varchar(100)', 'not null', 'Nombre o número'),
    ('identificador_externo', 'varchar(80)', 'not null', 'Id en la plataforma'),
    ('secreto_ref', 'varchar(120)', 'not null', 'Nombre del secreto con el token de acceso'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
])
tabla('redes', 'publicacion', 2, 'Contenido para redes: lo redacta el agente de redes y se publica solo con aprobación.', [
    ('cuenta_red_id', 'fk:redes.cuenta_red', 'not null', 'Cuenta'),
    ('texto', 'text', 'not null', 'Texto'),
    ('medios', 'jsonb', '', 'Imágenes o videos (rutas en MinIO)'),
    ('estado', "enum:borrador,propuesta,aprobada,programada,publicada,rechazada", "not null default 'borrador'", 'Situación'),
    ('programada_para', 'timestamptz', '', 'Fecha de publicación'),
    ('publicada_en', 'timestamptz', '', 'Fecha real'),
    ('id_externo', 'varchar(80)', '', 'Id en la plataforma'),
    ('agente_id', 'fk:ia.agente', '', 'Agente que la redactó'),
    ('aprobado_por', USR, '', 'Quién la aprobó'),
    ('recomendacion_id', 'fk:ia.recomendacion', '', 'Recomendación que la motivó'),
])

# ---------------------------------------------------------------- turismo (fase 3)
tabla('turismo', 'alojamiento', 3, 'Cabaña o espacio de hospedaje.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('capacidad_personas', 'smallint', 'not null', 'Huéspedes máximos'),
    ('zona_id', 'fk:nucleo.zona', '', 'Ubicación'),
    ('tarifa_noche', 'dinero', 'not null', 'Tarifa base por noche'),
    ('activo', 'boolean', 'not null default true', 'Disponible'),
])
tabla('turismo', 'plan_turistico', 3, 'Experiencia ofrecida (pasadía, recorrido del cacao, ordeño, taller).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('descripcion', 'text', 'not null', 'Qué incluye'),
    ('duracion_horas', 'numeric(4,1)', '', 'Duración'),
    ('cupo_maximo', 'smallint', '', 'Personas por grupo'),
    ('precio_persona', 'dinero', 'not null', 'Precio por persona'),
])
tabla('turismo', 'reserva', 3, 'Reserva de alojamiento o plan.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código'),
    ('cliente_id', 'fk:terceros.cliente', 'not null', 'Cliente'),
    ('alojamiento_id', 'fk:turismo.alojamiento', '', 'Alojamiento'),
    ('plan_turistico_id', 'fk:turismo.plan_turistico', '', 'Plan'),
    ('fecha_inicio', 'date', 'not null', 'Llegada'),
    ('fecha_fin', 'date', 'not null', 'Salida'),
    ('personas', 'smallint', 'not null', 'Número de personas'),
    ('estado', "enum:solicitada,confirmada,pagada,cumplida,cancelada", "not null default 'solicitada'", 'Situación'),
    ('total', 'dinero', 'not null', 'Valor'),
    ('valor_deposito', 'dinero', 'not null default 0', 'Anticipo pagado para confirmar'),
    ('checkin_en', 'timestamptz', '', 'Llegada real'),
    ('checkout_en', 'timestamptz', '', 'Salida real'),
    ('pedido_id', 'fk:comercial.pedido', '', 'Pedido de cobro asociado'),
], ['check (fecha_fin >= fecha_inicio)'])

# ---------------------------------------------------------------- iot (fase 4)
tabla('iot', 'dispositivo', 4, 'Equipo físico de la red local de la finca (ESP32, PLC, estación meteorológica) o la pasarela que la coordina. Los nodos hablan con la pasarela por MQTT local; la pasarela sincroniza con la nube cuando hay internet.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código'),
    ('tipo', 'enum:esp32,plc,estacion_clima,pasarela,registrador_temperatura,camara,camara_termica,lector_acceso,central_alarma,otro', 'not null', 'Tipo; la pasarela es el cerebro local que ejecuta las reglas, graba los clips y guarda datos sin internet'),
    ('pasarela_id', 'fk:iot.dispositivo', '', 'Pasarela a la que reporta este nodo (vacío si es la pasarela)'),
    ('zona_id', 'fk:nucleo.zona', '', 'Ubicación'),
    ('topico_mqtt', 'varchar(120)', 'not null', 'Tópico base en el broker local, ej. guayacan/riego/v03'),
    ('direccion_red_local', 'inet', '', 'IP fija en la red local de la finca'),
    ('version_firmware', 'varchar(30)', '', 'Versión del programa instalado'),
    ('ultima_conexion', 'timestamptz', '', 'Último latido recibido'),
    ('ultima_sincronizacion_nube', 'timestamptz', '', 'Solo pasarela: última vez que subió datos a la nube'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
])
tabla('iot', 'sensor', 4, 'Sensor de un dispositivo (humedad de suelo, nivel de tanque, caudal, temperatura, movimiento, puerta, humo, gas).', [
    ('dispositivo_id', 'fk:iot.dispositivo', 'not null', 'Dispositivo'),
    ('codigo', 'varchar(30)', 'not null unique', 'Código'),
    ('magnitud', 'enum:humedad_suelo,nivel_tanque,caudal,temperatura,humedad_aire,lluvia,oxigeno_agua,ph,movimiento,puerta,rotura_vidrio,humo,gas,amoniaco,presencia_termica', 'not null', 'Qué mide o detecta'),
    ('unidad', 'varchar(10)', 'not null', 'Unidad, ej. %, cm, L/min'),
    ('valor_minimo_alerta', 'numeric(10,3)', '', 'Alerta por debajo'),
    ('valor_maximo_alerta', 'numeric(10,3)', '', 'Alerta por encima'),
])
tabla('iot', 'actuador', 4, 'Elemento que el sistema puede accionar (electroválvula, bomba, relé, sirena, reflector, cerradura, cortina, extractor).', [
    ('dispositivo_id', 'fk:iot.dispositivo', 'not null', 'Dispositivo'),
    ('codigo', 'varchar(30)', 'not null unique', 'Código'),
    ('tipo', 'enum:electrovalvula,bomba,rele,motor,sirena,reflector,cerradura,cortina,extractor', 'not null', 'Tipo'),
    ('zona_seguridad_id', 'fk:iot.zona_seguridad', '', 'Zona de seguridad que protege (sirenas, cerraduras, reflectores)'),
    ('modo_falla', "enum:cierra_sin_energia,abre_sin_energia,mantiene", "not null default 'mantiene'", 'Qué hace si se va la energía: una cerradura en un paso de personas debe abrir sin energía'),
    ('estado_actual', "enum:abierto,cerrado,encendido,apagado,desconocido", "not null default 'desconocido'", 'Último estado reportado'),
])
tabla('iot', 'lectura', 4, 'Medición de un sensor, particionada por mes (o hipertabla si se usa TimescaleDB); sin columnas de auditoría por volumen. La pasarela guarda las lecturas mientras no hay internet y las sube después.', [
    ('sensor_id', 'fk:iot.sensor', 'not null', 'Sensor'),
    ('medido_en', 'timestamptz', 'not null', 'Momento de la medición (reloj de la pasarela)'),
    ('recibido_en', 'timestamptz', 'not null default now()', 'Momento en que llegó a la nube; la diferencia muestra el tiempo sin conexión'),
    ('valor', 'double precision', 'not null', 'Valor medido'),
], ['index on (sensor_id, medido_en)', 'unique (sensor_id, medido_en)', 'partition by range (medido_en)'], auditoria=False)
tabla('iot', 'regla_automatizacion', 4, 'Regla determinista que acciona un actuador (ej. abrir V-03 si humedad < 30 % y tanque > 40 %). Se ejecuta en la pasarela local, así funciona sin internet. La IA puede sugerir reglas pero no activarlas.', [
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('condicion', 'jsonb', 'not null', 'Condición sobre sensores, horario y clima'),
    ('actuador_id', 'fk:iot.actuador', 'not null', 'Actuador'),
    ('accion', 'enum:abrir,cerrar,encender,apagar', 'not null', 'Acción'),
    ('duracion_max_min', 'smallint', 'not null', 'Tiempo máximo de seguridad; el nodo ESP32 también lo aplica por su cuenta'),
    ('ejecuta_en', "enum:pasarela_local,nodo,nube", "not null default 'pasarela_local'", 'Dónde corre la regla; la nube solo para reglas no críticas'),
    ('version', 'integer', 'not null default 1', 'Versión; sube con cada cambio'),
    ('desplegada_version', 'integer', '', 'Versión que confirmó tener la pasarela; distinta de version = cambio pendiente de bajar'),
    ('activa', 'boolean', 'not null default false', 'Las reglas nacen inactivas hasta que un humano las activa'),
    ('aprobado_por', USR, '', 'Quién la activó'),
])
tabla('iot', 'comando_actuador', 4, 'Orden manual o automática a un actuador (abrir o cerrar una válvula), con su resultado. Funciona desde la red local aunque no haya internet.', [
    ('actuador_id', 'fk:iot.actuador', 'not null', 'Actuador'),
    ('accion', 'enum:abrir,cerrar,encender,apagar', 'not null', 'Acción'),
    ('origen', 'enum:app_nube,app_red_local,regla,boton_fisico', 'not null', 'De dónde salió la orden'),
    ('regla_id', 'fk:iot.regla_automatizacion', '', 'Regla que la emitió, si aplica'),
    ('solicitado_por', USR, '', 'Persona que la pidió, si aplica'),
    ('duracion_max_min', 'smallint', 'not null', 'Tiempo máximo antes de cerrar solo'),
    ('estado', "enum:pendiente,enviado,ejecutado,fallido,expirado", "not null default 'pendiente'", 'Resultado'),
    ('expira_en', 'timestamptz', 'not null', 'Si no se ejecuta antes, se descarta (evita que una orden vieja se ejecute al volver la conexión)'),
    ('ejecutado_en', 'timestamptz', '', 'Confirmación del nodo'),
])

# ================================================================ v2 · tablas nuevas
tabla('nucleo', 'dispositivo_captura', 1, 'Equipo con el que se capturan datos: celulares con la app, lectores de código de barras, básculas e impresoras de etiquetas.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código, ej. CEL-SAMID, BAS-01, LEC-01'),
    ('tipo', 'enum:celular,tableta,lector_codigo,bascula,impresora_etiquetas', 'not null', 'Tipo de equipo'),
    ('conexion', 'enum:camara,teclado_hid,bluetooth_ble,bluetooth_serial,usb,red_local', 'not null', 'Cómo se conecta: teclado_hid = el lector escribe como un teclado; red_local = a través de la pasarela de la finca'),
    ('marca_modelo', 'varchar(80)', '', 'Marca y modelo'),
    ('numero_serie', 'varchar(60)', '', 'Serie del fabricante'),
    ('capacidad_max_kg', 'numeric(10,3)', '', 'Báscula: peso máximo'),
    ('division_g', 'numeric(8,2)', '', 'Báscula: resolución en gramos'),
    ('uso_comercial', 'boolean', 'not null default false', 'Báscula usada para vender por peso: sujeta a verificación metrológica de la SIC'),
    ('ultima_verificacion', 'date', '', 'Fecha de la última verificación o calibración'),
    ('proxima_verificacion', 'date', '', 'Fecha en que vence la verificación'),
    ('certificado_url', 'varchar(300)', '', 'Certificado de verificación o calibración'),
    ('usuario_asignado_id', USR, '', 'Persona a cargo (celulares)'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
])
tabla('nucleo', 'sincronizacion', 1, 'Cada sincronización de la app sin conexión: cuántos registros subió, cuántos se rechazaron y por qué.', [
    ('dispositivo_captura_id', 'fk:nucleo.dispositivo_captura', 'not null', 'Celular o tableta que sincroniza'),
    ('usuario_id', USR, 'not null', 'Usuario que tenía la sesión'),
    ('version_app', 'varchar(20)', 'not null', 'Versión de la app'),
    ('iniciada_en', 'timestamptz', 'not null', 'Inicio'),
    ('terminada_en', 'timestamptz', '', 'Fin'),
    ('registros_recibidos', 'integer', 'not null default 0', 'Registros que llegaron'),
    ('registros_duplicados', 'integer', 'not null default 0', 'Ya existían (mismo id_cliente); se ignoran sin error'),
    ('registros_rechazados', 'integer', 'not null default 0', 'No pasaron una regla (ej. dos personas registraron la postura del mismo lote y día)'),
    ('detalle_rechazos', 'jsonb', '', 'Qué se rechazó y por qué, para resolverlo en la app'),
])
tabla('inventario', 'etiqueta', 1, 'Código de barras o QR impreso para un lote. Interno (Code 128 o QR) o GS1-128 si la finca obtiene códigos GS1.', [
    ('lote_inventario_id', 'fk:inventario.lote_inventario', 'not null', 'Lote identificado'),
    ('codigo', 'varchar(80)', 'not null unique', 'Texto que contiene el código, ej. GY-HUE-20261025-GAL01 o (01)…(10)…(17)…'),
    ('simbologia', 'enum:code128,qr,gs1_128,gs1_datamatrix,ean13', 'not null', 'Tipo de código impreso'),
    ('impresora_id', 'fk:nucleo.dispositivo_captura', '', 'Impresora usada'),
    ('impresa_en', 'timestamptz', '', 'Cuándo se imprimió'),
    ('anulada', 'boolean', 'not null default false', 'Etiqueta dañada o reemplazada; si se escanea, se rechaza'),
])
tabla('inventario', 'lectura_codigo', 1, 'Cada escaneo de un código: qué se leyó, con qué equipo, para qué y qué resultado tuvo.', [
    ('codigo_leido', 'varchar(120)', 'not null', 'Texto leído'),
    ('simbologia', 'varchar(20)', '', 'Tipo detectado'),
    ('etiqueta_id', 'fk:inventario.etiqueta', '', 'Etiqueta encontrada, si existe'),
    ('accion', 'enum:consulta,entrada,salida,conteo,traslado,despacho', 'not null', 'Para qué se escaneó'),
    ('resultado', 'enum:ok,desconocido,anulado,vencido,duplicado,rechazado', 'not null', 'Resultado de la validación'),
    ('usuario_id', USR, 'not null', 'Quién escaneó'),
])
tabla('inventario', 'pesaje', 1, 'Lectura de una báscula digital, automática o digitada, con tara y estabilidad.', [
    ('peso_bruto_kg', 'numeric(12,3)', 'not null', 'Peso total en la báscula'),
    ('tara_kg', 'numeric(12,3)', 'not null default 0', 'Peso del recipiente (canastilla, bulto, nevera)'),
    ('peso_neto_kg', 'numeric(12,3)', 'not null', 'Bruto menos tara'),
    ('estable', 'boolean', 'not null', 'La báscula indicó lectura estable; si es falso, no se acepta para vender'),
    ('origen', 'enum:bascula_automatica,digitado', 'not null', 'Leído del equipo o escrito a mano (el digitado queda marcado en informes)'),
    ('referencia_tabla', 'varchar(60)', '', 'Para qué se pesó, ej. cosecha, registro_pesaje, pedido_detalle'),
    ('referencia_id', 'bigint', '', 'Id del registro relacionado'),
    ('usuario_id', USR, 'not null', 'Quién pesó'),
], ['check (abs(peso_neto_kg - (peso_bruto_kg - tara_kg)) < 0.001)'])
tabla('inventario', 'conteo_fisico', 1, 'Inventario físico de una bodega: se escanea lo que hay y se compara con el sistema.', [
    ('bodega_id', 'fk:inventario.bodega', 'not null', 'Bodega contada'),
    ('fecha', 'date', 'not null', 'Día del conteo'),
    ('estado', "enum:en_curso,cerrado,ajustado", "not null default 'en_curso'", 'Ajustado = las diferencias ya generaron movimientos de ajuste'),
    ('responsable_id', USR, 'not null', 'Responsable'),
])
tabla('inventario', 'conteo_detalle', 1, 'Resultado del conteo por lote.', [
    ('conteo_fisico_id', 'fk:inventario.conteo_fisico', 'not null', 'Conteo'),
    ('lote_inventario_id', 'fk:inventario.lote_inventario', 'not null', 'Lote contado'),
    ('cantidad_sistema', 'numeric(12,2)', 'not null', 'Lo que decía el sistema al contar'),
    ('cantidad_contada', 'numeric(12,2)', 'not null', 'Lo encontrado'),
    ('movimiento_ajuste_id', 'fk:inventario.movimiento_inventario', '', 'Ajuste generado por la diferencia'),
], ['unique (conteo_fisico_id, lote_inventario_id)'])
tabla('comercial', 'reserva_lote', 1, 'Qué lotes se reservaron para cada línea de pedido, escogidos en orden FEFO; una línea puede tomar de varios lotes.', [
    ('pedido_detalle_id', 'fk:comercial.pedido_detalle', 'not null', 'Línea del pedido'),
    ('lote_inventario_id', 'fk:inventario.lote_inventario', 'not null', 'Lote reservado'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad tomada de ese lote'),
    ('estado', "enum:reservada,despachada,liberada", "not null default 'reservada'", 'Situación'),
], ['check (cantidad > 0)'])
tabla('finanzas', 'periodo_contable', 1, 'Mes contable; un comprobante solo se contabiliza o anula si su mes está abierto.', [
    ('anio', 'smallint', 'not null', 'Año'),
    ('mes', 'smallint', 'not null', 'Mes (1 a 12)'),
    ('estado', "enum:abierto,cerrado", "not null default 'abierto'", 'Estado'),
    ('cerrado_por', USR, '', 'Quién lo cerró'),
    ('cerrado_en', 'timestamptz', '', 'Cuándo'),
], ['unique (anio, mes)', 'check (mes between 1 and 12)'])
tabla('redes', 'politica_canal', 1, 'Reglas de cada canal según su proveedor (Meta, TikTok): ventana para responder, quién inicia, límites y cobro. Se actualiza cuando cambian las políticas.', [
    ('plataforma', 'varchar(20)', 'not null unique', 'Código del canal: whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina'),
    ('ventana_horas', 'smallint', '', 'Horas para responder después del último mensaje del cliente; vacío = sin límite (web propia)'),
    ('ventana_agente_humano_horas', 'smallint', '', 'Horas extra solo para respuestas de una persona (etiqueta de agente humano de Meta)'),
    ('ventana_anuncio_horas', 'smallint', '', 'Ventana ampliada si el cliente llegó por un anuncio que abre chat'),
    ('max_mensajes_por_ventana', 'smallint', '', 'Tope de mensajes de la empresa por ventana (TikTok: 10)'),
    ('empresa_puede_iniciar', 'boolean', 'not null', 'Si la empresa puede escribir primero (WhatsApp solo con plantilla aprobada)'),
    ('requiere_plantilla_fuera_ventana', 'boolean', 'not null', 'Fuera de la ventana solo se envían plantillas aprobadas'),
    ('cobra_por_mensaje', 'boolean', 'not null', 'El proveedor cobra por mensaje enviado'),
    ('mensajes_servicio_gratis_mes', 'integer', '', 'Mensajes de servicio sin costo al mes (WhatsApp: 1.000 por número)'),
    ('solo_bot_del_negocio', 'boolean', 'not null default true', 'El bot debe limitarse a temas de la finca; no puede ser un asistente general'),
    ('disponible', 'boolean', 'not null default true', 'Si el canal está disponible para cuentas registradas en Colombia'),
    ('fuente_url', 'varchar(300)', '', 'Documento donde se verificó la regla'),
    ('verificado_en', 'date', 'not null', 'Cuándo se verificó'),
])
tabla('redes', 'plantilla_mensaje', 1, 'Plantilla aprobada por Meta para escribir fuera de la ventana de 24 horas de WhatsApp (confirmaciones, recordatorios, promociones).', [
    ('cuenta_red_id', 'fk:redes.cuenta_red', 'not null', 'Cuenta de WhatsApp'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre técnico, ej. pedido_confirmado'),
    ('categoria', 'enum:marketing,utility,authentication', 'not null', 'Categoría de Meta; define el precio y si exige consentimiento de publicidad'),
    ('idioma', 'varchar(10)', "not null default 'es_CO'", 'Idioma'),
    ('cuerpo', 'text', 'not null', 'Texto con variables {{1}}, {{2}}'),
    ('variables', 'jsonb', '', 'Qué dato va en cada variable'),
    ('estado_meta', "enum:borrador,enviada,aprobada,rechazada,pausada", "not null default 'borrador'", 'Estado de revisión en Meta'),
    ('id_externo', 'varchar(80)', '', 'Id en Meta'),
    ('finalidad_requerida', 'enum:atencion_pedidos,publicidad', 'not null', 'Consentimiento que debe tener el cliente para recibirla'),
], ['unique (cuenta_red_id, nombre, idioma)'])
tabla('redes', 'mensaje_saliente', 1, 'Registro de control de cada mensaje que la finca envía por un canal: si estaba dentro de la ventana, qué plantilla usó, qué consentimiento lo permitió y cuánto costó.', [
    ('cuenta_red_id', 'fk:redes.cuenta_red', 'not null', 'Canal'),
    ('tercero_id', 'fk:terceros.tercero', '', 'Destinatario, si está identificado'),
    ('conversacion_ref', 'varchar(24)', '', 'Conversación en MongoDB'),
    ('tipo', 'enum:servicio,plantilla,respuesta_privada_comentario', 'not null', 'Servicio = respuesta normal dentro de la ventana'),
    ('plantilla_id', 'fk:redes.plantilla_mensaje', '', 'Plantilla usada'),
    ('autor', 'enum:agente,humano,sistema', 'not null', 'Quién lo generó'),
    ('dentro_ventana', 'boolean', 'not null', 'Si se envió dentro de la ventana del canal'),
    ('consentimiento_id', 'fk:terceros.consentimiento_datos', '', 'Consentimiento que lo autoriza (obligatorio para publicidad)'),
    ('costo_estimado_usd', 'numeric(10,4)', 'not null default 0', 'Costo según la tarifa del canal'),
    ('estado_entrega', "enum:enviado,entregado,leido,fallido,bloqueado_por_regla", "not null default 'enviado'", 'Resultado; bloqueado_por_regla = el sistema lo detuvo (fuera de ventana, sin consentimiento)'),
    ('enviado_en', 'timestamptz', 'not null default now()', 'Momento'),
], ['index on (cuenta_red_id, enviado_en)'])
tabla('ia', 'regla_conversacion', 1, 'Guardia del orquestador: temas permitidos, temas que se rechazan con cortesía y casos que pasan a una persona.', [
    ('tipo', 'enum:tema_permitido,tema_fuera_de_alcance,escalar_a_humano,dato_prohibido', 'not null', 'Clase de regla'),
    ('descripcion', 'text', 'not null', 'Qué cubre, en lenguaje claro'),
    ('ejemplos', 'jsonb', '', 'Frases de ejemplo para el clasificador'),
    ('respuesta_plantilla', 'text', '', 'Texto de respuesta (ej. cortesía al rechazar un tema ajeno a la finca)'),
    ('prioridad_escalamiento', 'enum:alta,media,baja', '', 'Si escala, con qué prioridad'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
])
tabla('ia', 'escalamiento', 1, 'Conversación pasada a una persona: motivo, quién la atiende y hasta cuándo se puede responder según la ventana del canal.', [
    ('conversacion_ref', 'varchar(24)', 'not null', 'Conversación en MongoDB'),
    ('canal', 'varchar(20)', 'not null', 'Canal (whatsapp, instagram, ...)'),
    ('motivo', 'enum:solicitud_cliente,queja,fuera_de_alcance,sin_respuesta_conocimiento,pedido_grande,pago,error_agente', 'not null', 'Por qué escaló'),
    ('prioridad', 'enum:alta,media,baja', 'not null', 'Prioridad'),
    ('asignado_a', USR, '', 'Persona que atiende'),
    ('estado', "enum:pendiente,en_atencion,resuelto,vencido", "not null default 'pendiente'", 'Situación; vencido = se cerró la ventana sin respuesta'),
    ('responder_antes_de', 'timestamptz', 'not null', 'Límite según la ventana del canal (incluye la extensión de agente humano cuando aplica)'),
    ('atendido_en', 'timestamptz', '', 'Primera respuesta de la persona'),
])

# ================================================================ v4 · tablas nuevas
# ---- núcleo
tabla('nucleo', 'funcionalidad', 1, 'Interruptor de funciones por finca (feature flag): lo que aún no tiene equipo o decisión queda construido y apagado, y se enciende sin desplegar otra versión.', [
    ('codigo', 'varchar(40)', 'not null unique', 'Código, ej. venta_credito, permuta, camara_termica, reconocimiento_facial'),
    ('descripcion', 'text', 'not null', 'Qué habilita'),
    ('fase', 'smallint', 'not null', 'Fase del plan en que se prevé'),
    ('requiere_equipo', 'varchar(150)', '', 'Equipo que hay que comprar antes de activarla, si aplica'),
    ('activa', 'boolean', 'not null default false', 'Encendida en esta finca'),
    ('activada_por', USR, '', 'Quién la encendió'),
    ('activada_en', 'timestamptz', '', 'Cuándo'),
])
tabla('nucleo', 'nota_voz', 2, 'Nota de voz grabada en campo sin conexión; se transcribe al sincronizar y el operario confirma lo interpretado antes de crear el registro.', [
    ('usuario_id', USR, 'not null', 'Quién grabó'),
    ('audio_url', 'varchar(300)', 'not null', 'Audio en el almacén de archivos'),
    ('duracion_seg', 'smallint', '', 'Duración en segundos'),
    ('transcripcion', 'text', '', 'Texto obtenido por el servicio de voz a texto'),
    ('proveedor_voz_texto', 'varchar(40)', '', 'Servicio usado (intercambiable)'),
    ('interpretacion', 'jsonb', '', 'Registro propuesto, ej. {"tabla":"registro_postura","lote":"AV-2026-01","huevos":87}'),
    ('estado', "enum:pendiente,interpretada,confirmada,descartada", "not null default 'pendiente'", 'Solo una nota confirmada por la persona crea el registro'),
    ('registro_tabla', 'varchar(60)', '', 'Tabla del registro creado'),
    ('registro_id', 'bigint', '', 'Id del registro creado'),
])

# ---- producción
tabla('produccion', 'categoria_huevo', 1, 'Categorías comerciales del huevo por rango de peso, con la norma de la que salen (verificar NTC 1240 vigente).', [
    ('codigo', 'varchar(10)', 'not null', 'Código, ej. jumbo, aaa, aa, a, b, c'),
    ('peso_min_g', 'numeric(5,1)', 'not null', 'Peso mínimo en gramos (incluido)'),
    ('peso_max_g', 'numeric(5,1)', '', 'Peso máximo en gramos (excluido); vacío = sin tope'),
    ('norma', 'varchar(80)', 'not null', 'Norma o fuente de los rangos'),
    ('vigente_desde', 'date', 'not null', 'Desde cuándo aplica'),
], ['unique (codigo, vigente_desde)', 'check (peso_max_g is null or peso_max_g > peso_min_g)'])
tabla('produccion', 'clasificacion_postura', 1, 'Huevos de un registro de postura por categoría; el método dice si se clasificó con báscula, a mano o con visión artificial.', [
    ('registro_postura_id', 'fk:produccion.registro_postura', 'not null', 'Registro de postura'),
    ('categoria_huevo_id', 'fk:produccion.categoria_huevo', 'not null', 'Categoría'),
    ('cantidad', 'integer', 'not null', 'Huevos de esa categoría'),
    ('metodo', "enum:peso_bascula,manual,vision", "not null default 'manual'", 'Cómo se clasificó (vision = piloto de fase 4)'),
], ['unique (registro_postura_id, categoria_huevo_id)', 'check (cantidad >= 0)'])
tabla('produccion', 'registro_bioseguridad', 1, 'Registros de bioseguridad e inocuidad que pide el ICA: limpieza, desinfección, plagas, visitas, cambio de cama y agua.', [
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Galpón, bodega o zona'),
    ('fecha', 'date', 'not null', 'Día'),
    ('tipo', 'enum:limpieza,desinfeccion,control_plagas,visita,cambio_cama,calidad_agua,vacio_sanitario', 'not null', 'Tipo de registro'),
    ('producto_id', 'fk:inventario.producto', '', 'Desinfectante o insumo usado'),
    ('responsable', 'varchar(120)', 'not null', 'Quién lo hizo o quién visitó'),
    ('observaciones', 'text', '', 'Notas'),
])
tabla('produccion', 'produccion_abono', 1, 'Humus y compost producidos por el lombricultivo o la compostera; al entrar a bodega crean un lote vendible.', [
    ('origen', 'enum:lombricultivo,compostera,biodigestor', 'not null', 'De dónde sale'),
    ('zona_id', 'fk:nucleo.zona', '', 'Zona'),
    ('fecha', 'date', 'not null', 'Día de cosecha del abono'),
    ('kg', 'numeric(10,2)', 'not null', 'Kilogramos'),
    ('lote_inventario_id', 'fk:inventario.lote_inventario', '', 'Lote creado en inventario'),
])

# ---- inventario
tabla('inventario', 'vehiculo', 2, 'Vehículo de entregas (camioneta, motocarro) y su registrador de temperatura.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. CAM-01'),
    ('tipo', 'enum:camioneta,motocarro,moto,otro', 'not null', 'Tipo'),
    ('placa', 'varchar(10)', '', 'Placa'),
    ('capacidad_kg', 'numeric(10,2)', '', 'Carga máxima'),
    ('refrigerado', 'boolean', 'not null default false', 'Tiene nevera o caja térmica'),
    ('sensor_temperatura_id', 'fk:iot.sensor', '', 'Registrador de temperatura (guarda sin señal)'),
    ('temperatura_max_c', 'numeric(4,1)', '', 'Temperatura máxima aceptada'),
    ('minutos_tolerancia', 'smallint', 'not null default 30', 'Minutos fuera de rango antes de bloquear lo que transporta'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
])
tabla('inventario', 'excursion_temperatura', 2, 'Periodo en que una nevera o un vehículo estuvo fuera de su rango de temperatura; si supera la tolerancia, bloquea los lotes perecederos.', [
    ('sensor_id', 'fk:iot.sensor', 'not null', 'Sensor que la detectó'),
    ('bodega_id', 'fk:inventario.bodega', '', 'Bodega afectada'),
    ('vehiculo_id', 'fk:inventario.vehiculo', '', 'Vehículo afectado'),
    ('inicio', 'timestamptz', 'not null', 'Inicio'),
    ('fin', 'timestamptz', '', 'Fin; vacío = sigue fuera de rango'),
    ('temperatura_extrema_c', 'numeric(4,1)', 'not null', 'Peor temperatura registrada'),
    ('minutos_fuera', 'integer', 'not null default 0', 'Minutos fuera de rango'),
    ('lotes_bloqueados', 'integer', 'not null default 0', 'Lotes que bloqueó (lo calcula la regla)'),
    ('estado', "enum:abierta,cerrada", "not null default 'abierta'", 'Situación'),
], ['check ((bodega_id is null) <> (vehiculo_id is null))'])
tabla('inventario', 'bloqueo_lote', 2, 'Bloqueo de un lote y su decisión: lo pone una regla o una persona; liberarlo o descartarlo siempre lo decide una persona.', [
    ('lote_inventario_id', 'fk:inventario.lote_inventario', 'not null', 'Lote bloqueado'),
    ('motivo', 'enum:cadena_frio,sanitario,calidad,retiro', 'not null', 'Por qué'),
    ('origen_tabla', 'varchar(60)', '', 'Qué lo causó, ej. excursion_temperatura, retiro_lote'),
    ('origen_id', 'bigint', '', 'Id del origen'),
    ('decision', "enum:pendiente,liberado,descartado", "not null default 'pendiente'", 'Liberado vuelve a disponible; descartado registra la merma'),
    ('decidido_por', USR, '', 'Persona que decidió'),
    ('decidido_en', 'timestamptz', '', 'Cuándo'),
    ('observacion', 'text', '', 'Motivo de la decisión'),
])

# ---- comercial
tabla('comercial', 'retiro_lote', 1, 'Retiro de un lote del mercado (recall): se bloquea el lote y se avisa a cada cliente que lo recibió.', [
    ('lote_inventario_id', 'fk:inventario.lote_inventario', 'not null', 'Lote retirado'),
    ('motivo', 'text', 'not null', 'Problema sanitario o de calidad'),
    ('estado', "enum:abierto,clientes_avisados,cerrado", "not null default 'abierto'", 'Situación'),
    ('abierto_por', USR, 'not null', 'Quién lo abrió'),
    ('cerrado_en', 'timestamptz', '', 'Cuándo se cerró'),
])
tabla('comercial', 'retiro_aviso', 1, 'Cliente que recibió un lote retirado: cuánto recibió, cuándo se le avisó y cuánto devolvió.', [
    ('retiro_lote_id', 'fk:comercial.retiro_lote', 'not null', 'Retiro'),
    ('cliente_id', 'fk:terceros.cliente', 'not null', 'Cliente'),
    ('pedido_id', 'fk:comercial.pedido', 'not null', 'Pedido en que lo recibió'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad recibida de ese lote'),
    ('avisado_en', 'timestamptz', '', 'Cuándo se le avisó'),
    ('medio_aviso', 'enum:whatsapp,llamada,visita,correo', '', 'Cómo'),
    ('cantidad_devuelta', 'numeric(12,2)', 'not null default 0', 'Lo que devolvió'),
], ['unique (retiro_lote_id, pedido_id)'])
tabla('comercial', 'pedido_recurrente', 2, 'Pedido que se repite (tienda, restaurante, hotel); cada día la tarea crea en borrador los que tocan para que un vendedor los confirme.', [
    ('cliente_id', 'fk:terceros.cliente', 'not null', 'Cliente'),
    ('frecuencia', 'enum:semanal,quincenal,mensual', 'not null', 'Cada cuánto'),
    ('proxima_fecha', 'date', 'not null', 'Próxima entrega'),
    ('canal', "enum:whatsapp,web,redes,telefono,finca,mercado_campesino", "not null default 'whatsapp'", 'Canal con que se registra el pedido'),
    ('forma_pago', "enum:contado,credito", "not null default 'contado'", 'Forma de pago de los pedidos generados'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
])
tabla('comercial', 'pedido_recurrente_detalle', 2, 'Productos y cantidades del pedido recurrente.', [
    ('pedido_recurrente_id', 'fk:comercial.pedido_recurrente', 'not null', 'Pedido recurrente'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad'),
], ['unique (pedido_recurrente_id, producto_id)', 'check (cantidad > 0)'])
tabla('comercial', 'permuta', 2, 'Trueque formal: una venta (factura) y una compra (documento soporte) que se compensan; requiere la función permuta activa. El pago con mano de obra no se admite.', [
    ('factura_id', 'fk:comercial.factura', 'not null', 'Venta'),
    ('documento_soporte_id', 'fk:compras.documento_soporte', 'not null', 'Compra'),
    ('valor_compensado', 'dinero', 'not null', 'Valor que se cruza'),
    ('acuerdo', 'text', 'not null', 'Qué se intercambió y cómo se valoró'),
    ('registrado_por', USR, 'not null', 'Quién la registró'),
], ['check (valor_compensado > 0)'])
tabla('comercial', 'huella_trazabilidad', 1, 'Cadena de huellas SHA-256 de los hechos de trazabilidad de los lotes: cada huella incluye la anterior, así cualquier alteración se detecta. Lista para anclarse en una red blockchain si un comprador lo exige.', [
    ('lote_inventario_id', 'fk:inventario.lote_inventario', 'not null', 'Lote'),
    ('hecho', 'enum:lote_creado,despachado,bloqueado,liberado,descartado,retirado', 'not null', 'Hecho registrado'),
    ('contenido', 'jsonb', 'not null', 'Datos del hecho (lote, fechas, cliente, pedido)'),
    ('hash_anterior', 'char(64)', '', 'Huella anterior de la cadena de la finca'),
    ('hash', 'char(64)', 'not null', 'SHA-256 de la huella anterior más el contenido'),
    ('anclaje_red', 'varchar(40)', '', 'Red externa donde se ancló (vacío = no anclada)'),
    ('anclaje_transaccion', 'varchar(120)', '', 'Id de la transacción de anclaje'),
    ('anclado_en', 'timestamptz', '', 'Cuándo'),
], ['unique (hash)'], auditoria=False)

# ---- compras
tabla('compras', 'documento_soporte', 1, 'Documento soporte electrónico de la DIAN para compras a quien no factura (campesinos, permutas).', [
    ('proveedor_id', 'fk:terceros.proveedor', 'not null', 'Vendedor'),
    ('orden_compra_id', 'fk:compras.orden_compra', '', 'Orden de compra, si existe'),
    ('prefijo', 'varchar(6)', 'not null', 'Prefijo autorizado'),
    ('numero', 'integer', 'not null', 'Número'),
    ('fecha', 'date', 'not null', 'Fecha'),
    ('descripcion', 'text', 'not null', 'Qué se compró'),
    ('total', 'dinero', 'not null', 'Valor'),
    ('cuds', 'varchar(96)', '', 'Código único del documento soporte'),
    ('estado_dian', "enum:pendiente,aceptado,rechazado", "not null default 'pendiente'", 'Respuesta de la DIAN'),
], ['unique (prefijo, numero)'])

# ---- ia
tabla('ia', 'modelo_pronostico', 2, 'Modelo de pronóstico de demanda entrenado; gana el de menor error (necesita al menos 12 meses de ventas).', [
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('algoritmo', 'enum:base_estacional,promedio_movil,ets,prophet,otro', 'not null', 'Algoritmo'),
    ('version', 'varchar(20)', 'not null', 'Versión'),
    ('entrenado_en', 'timestamptz', 'not null', 'Cuándo se entrenó'),
    ('meses_historia', 'smallint', 'not null', 'Meses de ventas usados'),
    ('error_mape', 'numeric(6,2)', '', 'Error porcentual medio en la validación'),
    ('activo', 'boolean', 'not null default false', 'Modelo en uso para ese producto'),
])
tabla('ia', 'pronostico_demanda', 2, 'Cantidad esperada de venta por producto y periodo, con su rango.', [
    ('modelo_pronostico_id', 'fk:ia.modelo_pronostico', 'not null', 'Modelo'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('periodo_inicio', 'date', 'not null', 'Inicio'),
    ('periodo_fin', 'date', 'not null', 'Fin'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad esperada'),
    ('limite_inferior', 'numeric(12,2)', '', 'Rango bajo'),
    ('limite_superior', 'numeric(12,2)', '', 'Rango alto'),
], ['check (periodo_fin >= periodo_inicio)'])

# ---- redes
tabla('redes', 'pieza_audiovisual', 2, 'Video, time-lapse o foto preparada para redes: la IA propone guion y texto, FFmpeg arma el archivo y una persona aprueba. Si aparecen personas, todas deben tener consentimiento de imagen.', [
    ('tipo', 'enum:video_promocional,timelapse,reel,foto', 'not null', 'Tipo'),
    ('clips', 'jsonb', '', 'Clips de origen (ids de iot.clip_video o archivos subidos)'),
    ('guion', 'text', '', 'Guion propuesto'),
    ('texto_publicacion', 'text', '', 'Texto para la red'),
    ('musica_ref', 'varchar(120)', '', 'Pista con licencia de uso'),
    ('archivo_url', 'varchar(300)', '', 'MP4 o imagen final'),
    ('personas_identificables', 'boolean', 'not null default false', 'Si aparecen personas reconocibles'),
    ('estado', "enum:borrador,propuesta,aprobada,rechazada,publicada", "not null default 'borrador'", 'Situación'),
    ('agente_id', 'fk:ia.agente', '', 'Agente que la propuso'),
    ('aprobado_por', USR, '', 'Quién la aprobó'),
    ('publicacion_id', 'fk:redes.publicacion', '', 'Publicación en la que se usó'),
])
tabla('redes', 'pieza_persona', 2, 'Persona que aparece en una pieza audiovisual y su consentimiento de imagen.', [
    ('pieza_audiovisual_id', 'fk:redes.pieza_audiovisual', 'not null', 'Pieza'),
    ('tercero_id', 'fk:terceros.tercero', 'not null', 'Persona'),
], ['unique (pieza_audiovisual_id, tercero_id)'], auditoria=False)

# ---- turismo
tabla('turismo', 'bloqueo_calendario', 3, 'Fechas en que un alojamiento o un plan no está disponible (mantenimiento, uso familiar).', [
    ('alojamiento_id', 'fk:turismo.alojamiento', '', 'Alojamiento'),
    ('plan_turistico_id', 'fk:turismo.plan_turistico', '', 'Plan'),
    ('desde', 'date', 'not null', 'Desde'),
    ('hasta', 'date', 'not null', 'Hasta'),
    ('motivo', 'varchar(150)', 'not null', 'Motivo'),
], ['check (hasta >= desde)', 'check (alojamiento_id is not null or plan_turistico_id is not null)'])

# ---- iot · seguridad perimetral y cámaras (fase 4; diseño listo desde ya)
tabla('iot', 'zona_seguridad', 4, 'Área vigilada (perímetro, galpón, bodega, acceso) con su estado de alarma; las reglas corren en la pasarela local.', [
    ('zona_id', 'fk:nucleo.zona', '', 'Zona del predio'),
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. SEG-BOD-01'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('tipo', 'enum:perimetro,acceso,galpon,bodega,vivienda,otra', 'not null', 'Tipo'),
    ('paso_personas', 'boolean', 'not null default true', 'Si por sus puertas salen personas: sus cerraduras deben abrir sin energía'),
    ('bioseguridad', 'boolean', 'not null default false', 'Exige registro de visita y desinfección para entrar (galpones)'),
    ('estado_alarma', "enum:desarmado,armado,noche,mantenimiento", "not null default 'desarmado'", 'Estado actual; solo cambia con iot.cambiar_estado_alarma'),
])
tabla('iot', 'cambio_estado_alarma', 4, 'Historial de cambios de estado de la alarma (solo inserción).', [
    ('zona_seguridad_id', 'fk:iot.zona_seguridad', 'not null', 'Zona'),
    ('estado_anterior', 'varchar(20)', 'not null', 'Estado antes'),
    ('estado_nuevo', 'varchar(20)', 'not null', 'Estado después'),
    ('origen', 'enum:app_nube,app_red_local,teclado,horario,regla', 'not null', 'De dónde salió el cambio'),
    ('usuario_id', USR, '', 'Persona, si aplica'),
    ('ocurrido_en', 'timestamptz', 'not null default now()', 'Momento'),
], auditoria=False)
tabla('iot', 'credencial_acceso', 4, 'Credencial para abrir una puerta: PIN, tarjeta RFID o rostro. El rostro exige autorización expresa de biometría y su plantilla solo vive cifrada en la pasarela local, nunca en la nube.', [
    ('tercero_id', 'fk:terceros.tercero', 'not null', 'Persona autorizada'),
    ('zona_seguridad_id', 'fk:iot.zona_seguridad', '', 'Zona a la que da acceso; vacío = todas'),
    ('metodo', 'enum:pin,rfid,facial', 'not null', 'Método'),
    ('referencia_hash', 'varchar(128)', '', 'Hash del PIN o del número de tarjeta (nunca el valor en claro)'),
    ('consentimiento_id', 'fk:terceros.consentimiento_datos', '', 'Autorización de biometría (obligatoria si el método es facial)'),
    ('vigente_desde', 'date', 'not null', 'Desde'),
    ('vigente_hasta', 'date', '', 'Hasta'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
], ["check (metodo <> 'facial' or consentimiento_id is not null)"])
tabla('iot', 'camara', 4, 'Cámara de la finca: graba en la pasarela local por movimiento y sube solo clips elegidos.', [
    ('dispositivo_id', 'fk:iot.dispositivo', 'not null', 'Dispositivo'),
    ('zona_id', 'fk:nucleo.zona', '', 'Ubicación'),
    ('zona_seguridad_id', 'fk:iot.zona_seguridad', '', 'Zona de seguridad que vigila'),
    ('tipo', 'enum:ip_rtsp,termica,timelapse', 'not null', 'Tipo'),
    ('graba_por_movimiento', 'boolean', 'not null default true', 'Graba solo cuando hay movimiento (ahorra energía y almacenamiento)'),
    ('intervalo_timelapse_min', 'smallint', '', 'Minutos entre fotos de time-lapse'),
    ('retencion_dias', 'smallint', 'not null default 30', 'Días que se guardan los clips de seguridad antes de borrarse'),
    ('aviso_visible', 'boolean', 'not null default false', 'Hay aviso de zona vigilada (Ley 1581)'),
    ('stream_secreto_ref', 'varchar(120)', '', 'Nombre del secreto con la URL y la clave del video'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
])
tabla('iot', 'evento_seguridad', 4, 'Hecho de seguridad detectado (intrusión, puerta, humo, gas, acceso): lo publica la pasarela, aunque no haya internet, y queda para su atención (solo inserción salvo la atención).', [
    ('zona_seguridad_id', 'fk:iot.zona_seguridad', 'not null', 'Zona'),
    ('tipo', 'enum:intrusion,puerta_abierta,humo,gas,amoniaco,temperatura,sabotaje,falla_energia,acceso_concedido,acceso_denegado', 'not null', 'Qué pasó'),
    ('detector', 'enum:pir,magnetico,vidrio,camara,camara_termica,sensor_gas,lector_acceso,manual', 'not null', 'Qué lo detectó: las reglas usan el hecho, no el tipo de sensor (así una cámara térmica entra sin cambiar reglas)'),
    ('sensor_id', 'fk:iot.sensor', '', 'Sensor'),
    ('camara_id', 'fk:iot.camara', '', 'Cámara'),
    ('credencial_id', 'fk:iot.credencial_acceso', '', 'Credencial usada (accesos)'),
    ('severidad', 'enum:informativa,media,alta,critica', 'not null', 'Severidad'),
    ('estado_alarma', 'varchar(20)', 'not null', 'Estado de la alarma cuando ocurrió'),
    ('acciones', 'jsonb', '', 'Lo que hizo la pasarela: sirena, reflectores, extractor, aviso push o SMS'),
    ('ocurrido_en', 'timestamptz', 'not null', 'Momento (reloj de la pasarela)'),
    ('atendido_por', USR, '', 'Quién lo atendió'),
    ('atendido_en', 'timestamptz', '', 'Cuándo'),
    ('nota_atencion', 'text', '', 'Qué se encontró'),
], ['index on (zona_seguridad_id, ocurrido_en)'])
tabla('iot', 'clip_video', 4, 'Clip grabado por una cámara: los de seguridad se borran al vencer su retención; los marcados para redes pasan a una pieza audiovisual.', [
    ('camara_id', 'fk:iot.camara', 'not null', 'Cámara'),
    ('inicio', 'timestamptz', 'not null', 'Inicio'),
    ('fin', 'timestamptz', 'not null', 'Fin'),
    ('motivo', 'enum:movimiento,evento_seguridad,timelapse,manual', 'not null', 'Por qué se grabó'),
    ('evento_seguridad_id', 'fk:iot.evento_seguridad', '', 'Evento asociado'),
    ('ubicacion', "enum:pasarela,nube", "not null default 'pasarela'", 'Dónde está guardado'),
    ('archivo_url', 'varchar(300)', 'not null', 'Ruta del archivo'),
    ('para_redes', 'boolean', 'not null default false', 'Elegido para contenido de redes (se conserva)'),
    ('retener_hasta', 'date', 'not null', 'Fecha de borrado automático'),
    ('borrado_en', 'timestamptz', '', 'Cuándo se borró el archivo'),
], ['check (fin > inicio)'])

# ---- ambiental
tabla('ambiental', 'factor_emision', 2, 'Factor para convertir una medición en CO₂ equivalente, con su fuente; sin fuente no se publica ninguna cifra.', [
    ('magnitud', 'varchar(40)', 'not null', 'Magnitud, ej. kwh_solar'),
    ('factor_kgco2e', 'numeric(12,6)', 'not null', 'kg de CO₂ equivalente evitados por unidad'),
    ('fuente', 'varchar(300)', 'not null', 'Documento oficial del que sale el factor'),
    ('vigente_desde', 'date', 'not null', 'Desde'),
], ['unique (magnitud, vigente_desde)'])
tabla('ambiental', 'registro_ambiental', 2, 'Medición ambiental de la finca (energía solar, biogás, compost, humus, agua).', [
    ('magnitud', 'enum:kwh_solar,m3_biogas,kg_compost,kg_humus,litros_agua_reutilizada,litros_agua_consumida', 'not null', 'Qué se midió'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad'),
    ('fecha', 'date', 'not null', 'Día'),
    ('origen', 'enum:sensor,manual', 'not null', 'Cómo se obtuvo'),
    ('sensor_id', 'fk:iot.sensor', '', 'Sensor, si aplica'),
], ['check (cantidad >= 0)'])


# ================================================================ v5 · operación integral de la finca
# Personal, nómina, formación, activos, documental, cumplimiento, seguros, seguridad informática, CRM y estrategia.
# Lo que depende de un trámite o de un equipo queda construido y apagado con su función (nucleo.funcionalidad).
EMP = 'fk:terceros.empleado'
TER = 'fk:terceros.tercero'

# ---- personal
tabla('personal', 'cuadrilla', 2, 'Grupo de trabajadores que recibe tareas juntos (ej. cuadrilla de cosecha).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. CUA-COSECHA'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('lider_id', EMP, '', 'Trabajador que coordina la cuadrilla'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
])
tabla('personal', 'cuadrilla_miembro', 2, 'Trabajadores de cada cuadrilla, con fechas.', [
    ('cuadrilla_id', 'fk:personal.cuadrilla', 'not null', 'Cuadrilla'),
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('desde', 'date', 'not null', 'Desde'),
    ('hasta', 'date', '', 'Hasta; vacío = sigue'),
], ['unique (cuadrilla_id, empleado_id, desde)'])
tabla('personal', 'turno', 2, 'Horario de trabajo programado de una persona en un día.', [
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('fecha', 'date', 'not null', 'Día'),
    ('hora_inicio', 'time', 'not null', 'Hora de entrada'),
    ('hora_fin', 'time', 'not null', 'Hora de salida'),
    ('tipo', "enum:diurno,nocturno,mixto,descanso,festivo", "not null default 'diurno'", 'Tipo de turno (define recargos)'),
    ('area_id', 'fk:personal.area_responsabilidad', '', 'Área en la que trabaja ese turno'),
    ('cronograma_id', 'fk:personal.cronograma', '', 'Cronograma del que salió'),
    ('horas', 'numeric(4,2)', '', 'Horas del turno (las calcula la base; si la salida es menor que la entrada, cruza la medianoche)'),
], ['unique (empleado_id, fecha, hora_inicio)'])
tabla('personal', 'ausencia', 2, 'Vacaciones, permisos, incapacidades y licencias. Guarda solo el tipo y las fechas, nunca el diagnóstico médico.', [
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('tipo', 'enum:vacaciones,permiso,incapacidad_general,incapacidad_laboral,licencia_maternidad,licencia_paternidad,luto,calamidad,suspension', 'not null', 'Tipo'),
    ('desde', 'date', 'not null', 'Primer día'),
    ('hasta', 'date', 'not null', 'Último día'),
    ('remunerada', 'boolean', 'not null default true', 'Si se paga'),
    ('soporte_documento_id', 'fk:documental.documento', '', 'Soporte (sin diagnóstico)'),
    ('aprobada_por', USR, '', 'Quién la aprobó'),
], ['check (hasta >= desde)'])
tabla('personal', 'plantilla_tarea', 2, 'Labor que se repite (recoger huevos dos veces al día, revisar bebederos, deshierbe semanal) y genera las tareas del día.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código, ej. REC-HUEVO-AM'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('proceso', 'varchar(60)', 'not null', 'Proceso al que pertenece (une con la matriz de responsabilidades), ej. postura'),
    ('recurrencia', "enum:diaria,semanal,mensual,unica", 'not null', 'Cada cuánto se repite'),
    ('dias_semana', 'smallint[]', '', 'Días (1 lunes … 7 domingo) para las semanales'),
    ('hora_limite', 'time', '', 'Hora máxima para terminarla'),
    ('zona_id', 'fk:nucleo.zona', '', 'Zona'),
    ('duracion_estimada_min', 'smallint', '', 'Minutos estimados (estándar para productividad)'),
    ('competencia_id', 'fk:formacion.competencia', '', 'Habilitación que exige; sin ella no se asigna'),
    ('forma_pago', "enum:ninguna,jornal,destajo", "not null default 'ninguna'", 'Si la tarea aprobada paga jornal o destajo (nunca afecta el salario fijo)'),
    ('valor_unitario', 'dinero', '', 'Valor del jornal o de cada unidad a destajo'),
    ('unidad_destajo', 'varchar(20)', '', 'Unidad que se paga a destajo, ej. kg, racimo, planta'),
    ('registro_que_crea', "enum:ninguno,postura,alimentacion,labor_cultural,bioseguridad,riego,cosecha", "not null default 'ninguno'", 'Registro que nace de la tarea aprobada'),
    ('pasos', 'jsonb', '', 'Lista de chequeo'),
    ('area_id', 'fk:personal.area_responsabilidad', '', 'Área de responsabilidad'),
    ('prioridad', "enum:baja,media,alta,critica", "not null default 'media'", 'Prioridad'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
])
tabla('personal', 'tarea', 2, 'Trabajo concreto con responsable, lugar, plazo y evidencia. Solo se asigna a quien está disponible y habilitado; aprobada no se edita.', [
    ('plantilla_tarea_id', 'fk:personal.plantilla_tarea', '', 'Plantilla de la que salió'),
    ('titulo', 'varchar(150)', 'not null', 'Qué hay que hacer'),
    ('proceso', 'varchar(60)', '', 'Proceso'),
    ('fecha', 'date', 'not null', 'Día'),
    ('hora_limite', 'timestamptz', '', 'Plazo'),
    ('prioridad', "enum:baja,media,alta,critica", "not null default 'media'", 'Prioridad'),
    ('zona_id', 'fk:nucleo.zona', '', 'Zona'),
    ('area_id', 'fk:personal.area_responsabilidad', '', 'Área de responsabilidad (su responsable puede aprobarla)'),
    ('lote_animal_id', 'fk:produccion.lote_animal', '', 'Lote de animales'),
    ('siembra_id', 'fk:produccion.siembra', '', 'Siembra'),
    ('activo_id', 'fk:activos.activo', '', 'Equipo que se usa o se mantiene'),
    ('empleado_id', EMP, '', 'Responsable'),
    ('cuadrilla_id', 'fk:personal.cuadrilla', '', 'Cuadrilla responsable'),
    ('origen', "enum:plan,manual,agente,orden_trabajo,accion_correctiva,mision_robot,proyecto,agenda", "not null default 'manual'", 'De dónde salió'),
    ('agente_id', 'fk:ia.agente', '', 'Agente que la propuso (no asigna por su cuenta)'),
    ('estado', "enum:pendiente,en_curso,terminada,aprobada,devuelta,cancelada", "not null default 'pendiente'", 'Estado'),
    ('iniciada_en', 'timestamptz', '', 'Inicio (escaneo del carné)'),
    ('terminada_en', 'timestamptz', '', 'Fin'),
    ('cantidad', 'numeric(12,2)', '', 'Cantidad lograda (kg, aves, plantas) para destajo y productividad'),
    ('unidad', 'varchar(20)', '', 'Unidad de la cantidad'),
    ('aprobado_por', USR, '', 'Quién la aprobó o devolvió'),
    ('aprobado_en', 'timestamptz', '', 'Cuándo'),
    ('comentario_revision', 'text', '', 'Comentario al aprobar o devolver'),
], ['check (empleado_id is null or cuadrilla_id is null)', 'index on (fecha, estado)'])
tabla('personal', 'paso_tarea', 2, 'Paso de la lista de chequeo de una tarea.', [
    ('tarea_id', 'fk:personal.tarea', 'not null', 'Tarea'),
    ('orden', 'smallint', 'not null', 'Orden'),
    ('descripcion', 'varchar(200)', 'not null', 'Paso'),
    ('hecho', 'boolean', 'not null default false', 'Marcado'),
    ('hecho_en', 'timestamptz', '', 'Cuándo'),
], ['unique (tarea_id, orden)'])
tabla('personal', 'evidencia_tarea', 2, 'Prueba de una tarea: foto, lectura del carné o del lote, nota de voz o el registro que creó.', [
    ('tarea_id', 'fk:personal.tarea', 'not null', 'Tarea'),
    ('tipo', 'enum:foto,lectura_qr,lectura_nfc,nota_voz,documento,registro', 'not null', 'Tipo'),
    ('archivo_url', 'varchar(300)', '', 'Archivo'),
    ('registro_tabla', 'varchar(60)', '', 'Tabla del registro creado, ej. produccion.registro_postura'),
    ('registro_id', 'bigint', '', 'Id del registro'),
])
tabla('personal', 'matriz_responsabilidad', 2, 'Matriz RACI: para cada proceso, qué rol lo hace, lo aprueba, es consultado o informado.', [
    ('proceso', 'varchar(60)', 'not null', 'Proceso, ej. postura, venta, nomina'),
    ('rol_id', 'fk:nucleo.rol', 'not null', 'Rol'),
    ('responsabilidad', 'enum:responsable,aprueba,consultado,informado', 'not null', 'R, A, C o I'),
], ['unique (proceso, rol_id, responsabilidad)'])
tabla('personal', 'asignacion_equipo', 2, 'Quién tiene cada herramienta o equipo, desde cuándo y en qué estado lo recibió y lo devolvió.', [
    ('activo_id', 'fk:activos.activo', 'not null', 'Equipo'),
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('entregado_en', 'timestamptz', 'not null', 'Entrega'),
    ('estado_entrega', 'enum:bueno,regular,malo', 'not null', 'Estado al entregar'),
    ('devuelto_en', 'timestamptz', '', 'Devolución'),
    ('estado_devolucion', 'enum:bueno,regular,malo,perdido', '', 'Estado al devolver'),
])
tabla('personal', 'credencial_trabajo', 2, 'Carné del trabajador con QR o etiqueta NFC para registrar quién hizo qué, sin biometría.', [
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('tipo', 'enum:qr,nfc', 'not null', 'Tipo (nunca biométrico)'),
    ('codigo_hash', 'char(64)', 'not null unique', 'Huella SHA-256 del código impreso o grabado'),
    ('emitida_en', 'date', 'not null', 'Emisión'),
    ('revocada_en', 'timestamptz', '', 'Revocación (pérdida o retiro)'),
])
tabla('personal', 'jornada', 2, 'Registro de jornada (entrada, salida, horas y labor) para jornaleros sin tarea asignada ese día.', [
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('fecha', 'date', 'not null', 'Día'),
    ('entrada', 'timestamptz', 'not null', 'Entrada'),
    ('salida', 'timestamptz', '', 'Salida'),
    ('horas', 'numeric(4,2)', '', 'Horas trabajadas'),
    ('labor', 'varchar(150)', '', 'Labor hecha'),
    ('zona_id', 'fk:nucleo.zona', '', 'Zona'),
    ('metodo_registro', "enum:qr,nfc,manual", 'not null', 'Cómo se registró'),
    ('aprobada_por', USR, '', 'Quién la aprobó'),
    ('aprobada_en', 'timestamptz', '', 'Cuándo'),
], ['check (salida is null or salida > entrada)'])

# ---- nómina
tabla('nomina', 'concepto_nomina', 2, 'Concepto de la nómina (salario, auxilio, horas extra, recargos, jornal, destajo, deducciones, aportes). La tarifa vive en nucleo.parametro, nunca en el código.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código, ej. SALARIO, AUX_TRANSPORTE, JORNAL, DESTAJO, SALUD_EMP'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('tipo', 'enum:devengado,deduccion,aporte_empleador,provision', 'not null', 'Tipo'),
    ('base', 'enum:salario,jornal,destajo,horas,valor_fijo,porcentaje', 'not null', 'Cómo se calcula'),
    ('parametro_clave', 'varchar(80)', '', 'Clave de nucleo.parametro con la tarifa vigente'),
    ('constitutivo_salario', 'boolean', 'not null default false', 'Hace parte de la base para prestaciones'),
    ('cuenta_contable_id', 'fk:finanzas.cuenta_contable', '', 'Cuenta de causación'),
    ('codigo_dian', 'varchar(40)', '', 'Elemento del documento soporte de nómina electrónica'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
])
tabla('nomina', 'periodo_nomina', 2, 'Periodo de pago. Cerrado no se edita; las correcciones van como nota de ajuste. Cierre con doble aprobación y nunca por un agente.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. 2026-11'),
    ('tipo', "enum:mensual,quincenal,semanal", 'not null', 'Frecuencia'),
    ('desde', 'date', 'not null', 'Primer día'),
    ('hasta', 'date', 'not null', 'Último día'),
    ('estado', "enum:abierto,prenomina,cerrado,anulado", "not null default 'abierto'", 'Estado'),
    ('preparado_por', USR, '', 'Quién armó la prenómina'),
    ('cerrado_por', USR, '', 'Primera aprobación del cierre'),
    ('aprobado_por', USR, '', 'Segunda aprobación (persona distinta)'),
    ('cerrado_en', 'timestamptz', '', 'Cuándo'),
    ('comprobante_id', 'fk:finanzas.comprobante', '', 'Comprobante de causación'),
    ('ajusta_periodo_id', 'fk:nomina.periodo_nomina', '', 'Si es nota de ajuste, periodo que corrige'),
], ['check (hasta >= desde)'])
tabla('nomina', 'novedad', 2, 'Hecho que se paga o descuenta en el periodo: salario fijo, jornales y destajo de tareas aprobadas, horas extra, ausencias, préstamos.', [
    ('periodo_id', 'fk:nomina.periodo_nomina', 'not null', 'Periodo'),
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('concepto_id', 'fk:nomina.concepto_nomina', 'not null', 'Concepto'),
    ('cantidad', 'numeric(12,2)', 'not null default 1', 'Días, horas, jornales o unidades'),
    ('valor_unitario', 'dinero', 'not null default 0', 'Valor por unidad'),
    ('valor', 'dinero', 'not null', 'Valor total'),
    ('origen', "enum:contrato,tarea,jornada,ausencia,manual", 'not null', 'De dónde sale'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea aprobada que la origina'),
    ('jornada_id', 'fk:personal.jornada', '', 'Jornada que la origina'),
    ('ausencia_id', 'fk:personal.ausencia', '', 'Ausencia que la origina'),
    ('observacion', 'varchar(200)', '', 'Nota'),
], ['unique (tarea_id)', 'unique (jornada_id)'])
tabla('nomina', 'liquidacion', 2, 'Resultado del periodo para un trabajador: devengado, deducciones y neto.', [
    ('periodo_id', 'fk:nomina.periodo_nomina', 'not null', 'Periodo'),
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('total_devengado', 'dinero', 'not null default 0', 'Devengado'),
    ('total_deducciones', 'dinero', 'not null default 0', 'Deducciones'),
    ('neto', 'dinero', 'not null default 0', 'Neto a pagar'),
    ('estado', "enum:borrador,aprobada,pagada", "not null default 'borrador'", 'Estado'),
], ['unique (periodo_id, empleado_id)'])
tabla('nomina', 'liquidacion_detalle', 2, 'Línea de la liquidación por concepto.', [
    ('liquidacion_id', 'fk:nomina.liquidacion', 'not null', 'Liquidación'),
    ('concepto_id', 'fk:nomina.concepto_nomina', 'not null', 'Concepto'),
    ('cantidad', 'numeric(12,2)', 'not null', 'Cantidad'),
    ('valor', 'dinero', 'not null', 'Valor'),
])
tabla('nomina', 'provision_prestacion', 2, 'Provisión mensual de cesantías, intereses, prima y vacaciones.', [
    ('periodo_id', 'fk:nomina.periodo_nomina', 'not null', 'Periodo'),
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('tipo', 'enum:cesantias,intereses_cesantias,prima,vacaciones', 'not null', 'Prestación'),
    ('base', 'dinero', 'not null', 'Base'),
    ('valor', 'dinero', 'not null', 'Valor provisionado'),
], ['unique (periodo_id, empleado_id, tipo)'])
tabla('nomina', 'documento_nomina_electronica', 2, 'Documento soporte de pago de nómina electrónica (uno por trabajador al mes). Se transmite por el servicio gratuito de la DIAN o un proveedor autorizado; se enciende con nomina_electronica.', [
    ('liquidacion_id', 'fk:nomina.liquidacion', 'not null', 'Liquidación'),
    ('tipo', "enum:individual,ajuste", "not null default 'individual'", 'Tipo'),
    ('proveedor', 'enum:dian_gratuito,proveedor_tecnologico', 'not null', 'Por dónde se transmite'),
    ('cune', 'varchar(120)', '', 'Código único devuelto por la DIAN'),
    ('estado', "enum:pendiente,enviado,aceptado,rechazado", "not null default 'pendiente'", 'Estado'),
    ('enviado_en', 'timestamptz', '', 'Envío'),
    ('respuesta', 'jsonb', '', 'Respuesta del proveedor'),
    ('xml_url', 'varchar(300)', '', 'XML firmado por el proveedor (nunca se firma a mano)'),
])
tabla('nomina', 'planilla_pila', 2, 'Archivo de la planilla de seguridad social para el operador de la PILA; el pago lo hace una persona.', [
    ('periodo_id', 'fk:nomina.periodo_nomina', 'not null', 'Periodo'),
    ('tipo_planilla', 'varchar(5)', "not null default 'E'", 'Tipo de planilla (E = empleados)'),
    ('archivo_url', 'varchar(300)', 'not null', 'Archivo generado'),
    ('operador', 'varchar(60)', '', 'Operador de información'),
    ('numero_planilla', 'varchar(30)', '', 'Número asignado por el operador'),
    ('pagada_por', USR, '', 'Quién la pagó'),
    ('pagada_en', 'timestamptz', '', 'Cuándo'),
])
tabla('nomina', 'pago_nomina', 2, 'Pago de una liquidación (transferencia, Bre-B o efectivo). Lo prepara una persona y lo aprueba otra; nadie aprueba su propio pago.', [
    ('liquidacion_id', 'fk:nomina.liquidacion', 'not null', 'Liquidación'),
    ('medio', 'enum:transferencia,bre_b,efectivo', 'not null', 'Medio'),
    ('valor', 'dinero', 'not null', 'Valor'),
    ('preparado_por', USR, 'not null', 'Quién lo preparó'),
    ('aprobado_por', USR, '', 'Primera aprobación'),
    ('segunda_aprobacion_por', USR, '', 'Segunda aprobación (pagos sobre el monto del parámetro monto_doble_aprobacion)'),
    ('pagado_en', 'timestamptz', '', 'Cuándo se pagó'),
    ('referencia', 'varchar(80)', '', 'Referencia bancaria'),
], ['check (valor > 0)'])
tabla('nomina', 'exportacion_nomina', 2, 'Archivo para el contador cuando lleva la nómina en su propio programa.', [
    ('periodo_id', 'fk:nomina.periodo_nomina', 'not null', 'Periodo'),
    ('formato', 'enum:csv,excel,siigo,world_office,helisa,otro', 'not null', 'Formato'),
    ('archivo_url', 'varchar(300)', 'not null', 'Archivo'),
    ('generado_por', USR, 'not null', 'Quién lo generó'),
])

# ---- formación
tabla('formacion', 'competencia', 2, 'Habilidad que habilita tareas (registrar vacunas, aplicar insumos, liberar lotes, operar motosierra), con su vigencia.', [
    ('codigo', 'varchar(40)', 'not null unique', 'Código, ej. aplicar_vacunas'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('vigencia_meses', 'smallint', '', 'Meses que dura el certificado; vacío = no vence'),
    ('descripcion', 'text', '', 'Qué permite hacer'),
])
tabla('formacion', 'curso', 2, 'Curso virtual, presencial o mixto para operarios o estudiantes; los externos (SENA, FAO, Moodle) se enlazan.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre'),
    ('descripcion', 'text', '', 'Contenido'),
    ('publico', "enum:operarios,estudiantes,ambos", "not null default 'ambos'", 'A quién va'),
    ('modalidad', 'enum:virtual,presencial,mixto', 'not null', 'Modalidad'),
    ('competencia_id', 'fk:formacion.competencia', '', 'Habilitación que otorga al aprobar'),
    ('nota_minima', 'numeric(4,2)', 'not null default 3.5', 'Nota mínima para aprobar (escala 0 a 5)'),
    ('duracion_horas', 'numeric(5,1)', '', 'Horas'),
    ('origen', "enum:propio,sena,fao,moodle,otro", "not null default 'propio'", 'De dónde viene'),
    ('url_externa', 'varchar(300)', '', 'Enlace, si es externo'),
    ('ruta_cargo', 'varchar(60)', '', 'Ruta de aprendizaje, ej. operario_galpon, vendedor'),
    ('activo', 'boolean', 'not null default true', 'Publicado'),
])
tabla('formacion', 'leccion', 2, 'Lección de un curso (texto, video corto, práctica guiada); se descarga para verla sin señal.', [
    ('curso_id', 'fk:formacion.curso', 'not null', 'Curso'),
    ('orden', 'smallint', 'not null', 'Orden'),
    ('titulo', 'varchar(150)', 'not null', 'Título'),
    ('tipo', 'enum:texto,video,practica,tutorial_pantalla', 'not null', 'Tipo'),
    ('contenido_url', 'varchar(300)', '', 'Archivo'),
    ('pantalla', 'varchar(80)', '', 'Pantalla de la app que explica (tutoriales dentro de la app)'),
    ('documento_id', 'fk:documental.documento', '', 'Protocolo o manual de base'),
    ('descargable', 'boolean', 'not null default true', 'Se puede ver sin conexión'),
], ['unique (curso_id, orden)'])
tabla('formacion', 'evaluacion', 2, 'Examen de un curso.', [
    ('curso_id', 'fk:formacion.curso', 'not null', 'Curso'),
    ('titulo', 'varchar(150)', 'not null', 'Título'),
    ('intentos_max', 'smallint', 'not null default 3', 'Intentos'),
])
tabla('formacion', 'pregunta', 2, 'Pregunta de una evaluación.', [
    ('evaluacion_id', 'fk:formacion.evaluacion', 'not null', 'Evaluación'),
    ('orden', 'smallint', 'not null', 'Orden'),
    ('enunciado', 'text', 'not null', 'Pregunta'),
    ('tipo', 'enum:unica,multiple,verdadero_falso,practica', 'not null', 'Tipo'),
    ('opciones', 'jsonb', '', 'Opciones'),
    ('respuesta_correcta', 'jsonb', '', 'Respuesta'),
    ('puntos', 'numeric(4,1)', 'not null default 1', 'Puntos'),
], ['unique (evaluacion_id, orden)'])
tabla('formacion', 'inscripcion', 2, 'Persona (operario o estudiante) inscrita en un curso, con su nota.', [
    ('curso_id', 'fk:formacion.curso', 'not null', 'Curso'),
    ('tercero_id', TER, 'not null', 'Persona'),
    ('inscrito_en', 'date', 'not null default current_date', 'Inscripción'),
    ('estado', "enum:inscrito,en_curso,aprobado,reprobado,retirado", "not null default 'inscrito'", 'Estado'),
    ('nota', 'numeric(4,2)', '', 'Nota final'),
    ('aprobado_en', 'date', '', 'Fecha de aprobación'),
], ['unique (curso_id, tercero_id)'])
tabla('formacion', 'progreso', 2, 'Lecciones vistas por cada inscrito.', [
    ('inscripcion_id', 'fk:formacion.inscripcion', 'not null', 'Inscripción'),
    ('leccion_id', 'fk:formacion.leccion', 'not null', 'Lección'),
    ('completada_en', 'timestamptz', 'not null', 'Cuándo'),
], ['unique (inscripcion_id, leccion_id)'])
tabla('formacion', 'sesion_presencial', 2, 'Sesión dictada por el veterinario, el agrónomo o el encargado; su asistencia cuenta igual que un curso virtual.', [
    ('curso_id', 'fk:formacion.curso', 'not null', 'Curso'),
    ('instructor_id', TER, 'not null', 'Quién la dicta'),
    ('fecha', 'date', 'not null', 'Día'),
    ('lugar', 'varchar(120)', '', 'Lugar'),
    ('duracion_horas', 'numeric(4,1)', 'not null', 'Horas'),
])
tabla('formacion', 'asistencia', 2, 'Asistencia y nota de cada persona en una sesión presencial.', [
    ('sesion_id', 'fk:formacion.sesion_presencial', 'not null', 'Sesión'),
    ('tercero_id', TER, 'not null', 'Persona'),
    ('asistio', 'boolean', 'not null', 'Asistió'),
    ('nota', 'numeric(4,2)', '', 'Nota práctica'),
], ['unique (sesion_id, tercero_id)'])
tabla('formacion', 'certificado', 2, 'Certificado interno con fecha, nota y vencimiento; al emitirse crea la habilitación.', [
    ('tercero_id', TER, 'not null', 'Persona'),
    ('competencia_id', 'fk:formacion.competencia', 'not null', 'Competencia'),
    ('inscripcion_id', 'fk:formacion.inscripcion', '', 'Curso virtual aprobado'),
    ('sesion_id', 'fk:formacion.sesion_presencial', '', 'Sesión presencial'),
    ('emitido_en', 'date', 'not null', 'Emisión'),
    ('vence_en', 'date', '', 'Vencimiento'),
    ('nota', 'numeric(4,2)', '', 'Nota'),
    ('codigo_verificacion', 'varchar(40)', 'not null unique', 'Código para verificarlo'),
], ['check (inscripcion_id is not null or sesion_id is not null)'])
tabla('formacion', 'habilitacion', 2, 'Permiso para hacer una tarea, nacido de un certificado. Al vencer el certificado se retira sola.', [
    ('tercero_id', TER, 'not null', 'Persona'),
    ('competencia_id', 'fk:formacion.competencia', 'not null', 'Competencia'),
    ('certificado_id', 'fk:formacion.certificado', 'not null', 'Certificado que la sustenta'),
    ('desde', 'date', 'not null', 'Desde'),
    ('hasta', 'date', '', 'Hasta'),
    ('activa', 'boolean', 'not null default true', 'Vigente'),
    ('retirada_en', 'timestamptz', '', 'Cuándo se retiró'),
], ['unique (certificado_id)'])

# ---- activos
tabla('activos', 'activo', 1, 'Hoja de vida de cada equipo de la finca (camioneta, motocultor, guadañas, bombas, paneles, dron, robot).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. ACT-GUA-01'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('tipo', 'enum:vehiculo,maquinaria,herramienta,bomba,panel_solar,bateria,equipo_electronico,dron,robot,infraestructura,otro', 'not null', 'Tipo'),
    ('marca', 'varchar(60)', '', 'Marca'),
    ('modelo', 'varchar(60)', '', 'Modelo'),
    ('serie', 'varchar(60)', '', 'Número de serie'),
    ('fecha_compra', 'date', '', 'Compra'),
    ('valor_compra', 'dinero', '', 'Costo de adquisición'),
    ('valor_residual', 'dinero', 'not null default 0', 'Valor de salvamento'),
    ('vida_util_meses', 'smallint', '', 'Vida útil'),
    ('metodo_depreciacion', "enum:linea_recta,ninguno", "not null default 'linea_recta'", 'Método'),
    ('zona_id', 'fk:nucleo.zona', '', 'Ubicación'),
    ('responsable_id', EMP, '', 'Responsable'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Centro de costo que lo usa'),
    ('garantia_hasta', 'date', '', 'Garantía'),
    ('horometro', 'numeric(10,1)', 'not null default 0', 'Horas de uso acumuladas'),
    ('odometro', 'numeric(10,1)', 'not null default 0', 'Kilómetros acumulados'),
    ('vehiculo_id', 'fk:inventario.vehiculo', '', 'Vehículo de entregas, si es el mismo'),
    ('dispositivo_id', 'fk:iot.dispositivo', '', 'Dispositivo IoT, si lo tiene'),
    ('registro_aerocivil', 'varchar(40)', '', 'Registro del dron ante la Aerocivil (RAC 100)'),
    ('estado', "enum:operativo,en_mantenimiento,danado,dado_de_baja", "not null default 'operativo'", 'Estado'),
])
tabla('activos', 'plan_mantenimiento', 2, 'Mantenimiento por horas de uso, kilómetros o días (cambio de aceite, afilado, revisión de la bomba).', [
    ('activo_id', 'fk:activos.activo', 'not null', 'Equipo'),
    ('nombre', 'varchar(120)', 'not null', 'Qué se hace'),
    ('tipo', "enum:preventivo,predictivo", "not null default 'preventivo'", 'Tipo (predictivo cuando hay sensores)'),
    ('frecuencia_tipo', 'enum:horas,km,dias', 'not null', 'Base de la frecuencia'),
    ('frecuencia_valor', 'numeric(10,1)', 'not null', 'Cada cuánto'),
    ('ultima_lectura', 'numeric(10,1)', 'not null default 0', 'Horómetro u odómetro en la última ejecución'),
    ('ultima_fecha', 'date', '', 'Fecha de la última ejecución'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
], ['check (frecuencia_valor > 0)'])
tabla('activos', 'orden_trabajo', 2, 'Orden de mantenimiento: la crea sola la regla al vencer el plan y se asigna como tarea; descuenta repuestos del inventario.', [
    ('activo_id', 'fk:activos.activo', 'not null', 'Equipo'),
    ('plan_id', 'fk:activos.plan_mantenimiento', '', 'Plan que la originó'),
    ('tipo', 'enum:preventivo,correctivo,predictivo', 'not null', 'Tipo'),
    ('descripcion', 'text', 'not null', 'Qué hacer'),
    ('estado', "enum:abierta,en_curso,cerrada,cancelada", "not null default 'abierta'", 'Estado'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea asignada'),
    ('lectura_cierre', 'numeric(10,1)', '', 'Horómetro u odómetro al cerrar'),
    ('costo_mano_obra', 'dinero', 'not null default 0', 'Mano de obra'),
    ('costo_repuestos', 'dinero', 'not null default 0', 'Repuestos'),
    ('cerrada_en', 'timestamptz', '', 'Cierre'),
])
tabla('activos', 'repuesto_orden', 2, 'Repuesto usado en una orden de trabajo (sale del kardex).', [
    ('orden_id', 'fk:activos.orden_trabajo', 'not null', 'Orden'),
    ('producto_id', 'fk:inventario.producto', 'not null', 'Repuesto'),
    ('cantidad', 'numeric(10,2)', 'not null', 'Cantidad'),
    ('movimiento_id', 'fk:inventario.movimiento_inventario', '', 'Salida en el kardex'),
], ['check (cantidad > 0)'])
tabla('activos', 'uso_activo', 2, 'Uso de un equipo: horas, kilómetros y combustible, cargados al centro de costo que lo usó.', [
    ('activo_id', 'fk:activos.activo', 'not null', 'Equipo'),
    ('fecha', 'date', 'not null', 'Día'),
    ('empleado_id', EMP, '', 'Quién lo usó'),
    ('horas', 'numeric(6,1)', 'not null default 0', 'Horas'),
    ('km', 'numeric(8,1)', 'not null default 0', 'Kilómetros'),
    ('combustible_litros', 'numeric(8,2)', '', 'Combustible'),
    ('costo_combustible', 'dinero', '', 'Costo del combustible'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Centro de costo'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea'),
], ['check (horas >= 0 and km >= 0)'])
tabla('activos', 'depreciacion', 2, 'Depreciación mensual de cada activo (alimenta la contabilidad y el costo por línea).', [
    ('activo_id', 'fk:activos.activo', 'not null', 'Equipo'),
    ('mes', 'date', 'not null', 'Primer día del mes'),
    ('valor', 'dinero', 'not null', 'Depreciación del mes'),
    ('acumulada', 'dinero', 'not null', 'Depreciación acumulada'),
    ('comprobante_id', 'fk:finanzas.comprobante', '', 'Comprobante'),
], ['unique (activo_id, mes)'])

# ---- documental
tabla('documental', 'documento', 1, 'Papel que la finca no puede perder: permisos, registros ICA, RUT, contratos, protocolos, manuales, evidencias. Con datos personales sigue la Ley 1581.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código, ej. PRT-BIO-01'),
    ('titulo', 'varchar(200)', 'not null', 'Título'),
    ('tipo', 'enum:permiso,registro,contrato,protocolo,manual,ficha_tecnica,evidencia,acta,resultado_laboratorio,poliza,certificado,plan,otro', 'not null', 'Tipo'),
    ('entidad_emisora', 'varchar(120)', '', 'Quién lo expide, ej. ICA, CAR, DIAN'),
    ('numero', 'varchar(60)', '', 'Número oficial'),
    ('responsable_id', USR, '', 'Responsable'),
    ('nivel_acceso', "enum:finca,rol,restringido", "not null default 'finca'", 'Quién lo ve'),
    ('rol_id', 'fk:nucleo.rol', '', 'Rol que lo ve, si es por rol'),
    ('contiene_datos_personales', 'boolean', 'not null default false', 'Tiene datos personales (Ley 1581)'),
    ('finalidad', 'text', '', 'Para qué se guarda'),
    ('conservar_hasta', 'date', '', 'Hasta cuándo se conserva'),
    ('uso_agentes', 'boolean', 'not null default false', 'Lo pueden leer los agentes (solo la versión aprobada y vigente)'),
], ['check (not contiene_datos_personales or (finalidad is not null and conservar_hasta is not null))'])
tabla('documental', 'version_documento', 1, 'Versión de un documento con su archivo, huella, aprobación y vigencia; solo una aprobada vigente a la vez.', [
    ('documento_id', 'fk:documental.documento', 'not null', 'Documento'),
    ('version', 'smallint', 'not null', 'Número de versión'),
    ('archivo_url', 'varchar(300)', 'not null', 'Archivo en el almacén de objetos'),
    ('hash_sha256', 'char(64)', 'not null', 'Huella del archivo'),
    ('estado', "enum:borrador,en_revision,aprobada,obsoleta", "not null default 'borrador'", 'Estado'),
    ('aprobada_por', USR, '', 'Quién la aprobó'),
    ('aprobada_en', 'timestamptz', '', 'Cuándo'),
    ('vigente_desde', 'date', '', 'Desde'),
    ('vence_en', 'date', '', 'Vencimiento (permisos, registros, pólizas)'),
    ('avisar_dias', 'smallint', 'not null default 30', 'Días de aviso antes de vencer'),
    ('cambios', 'text', '', 'Qué cambió'),
], ['unique (documento_id, version)'])
tabla('documental', 'vinculo_documento', 1, 'Une un documento con cualquier registro (un lote, una póliza, un activo, una no conformidad).', [
    ('documento_id', 'fk:documental.documento', 'not null', 'Documento'),
    ('registro_tabla', 'varchar(60)', 'not null', 'Tabla'),
    ('registro_id', 'bigint', 'not null', 'Id'),
], ['unique (documento_id, registro_tabla, registro_id)'])

# ---- cumplimiento
tabla('cumplimiento', 'norma', 1, 'Norma o certificación (granja avícola biosegura ICA 3651/2014, BPA ICA 30021/2017, GLOBALG.A.P. IFA v6). Catálogo compartido.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código, ej. ICA_GAB, ICA_BPA, GLOBALGAP_IFA6'),
    ('nombre', 'varchar(200)', 'not null', 'Nombre'),
    ('entidad', 'varchar(80)', 'not null', 'Entidad'),
    ('referencia', 'varchar(120)', 'not null', 'Norma, ej. Resolución ICA 3651 de 2014'),
    ('obligatoria', 'boolean', 'not null', 'Obligatoria por ley'),
    ('condicion_obligatoria', 'text', '', 'Cuándo aplica, ej. postura o levante desde 200 aves'),
    ('funcion_codigo', 'varchar(40)', '', 'Función por finca que la enciende; vacío = siempre activa'),
    ('vigencia_certificado_meses', 'smallint', '', 'Duración del certificado'),
    ('url_fuente', 'varchar(300)', '', 'Texto oficial'),
])
tabla('cumplimiento', 'requisito', 1, 'Requisito de una norma con el tipo de evidencia y, si aplica, la regla que la revisa sola.', [
    ('norma_id', 'fk:cumplimiento.norma', 'not null', 'Norma'),
    ('codigo', 'varchar(30)', 'not null', 'Código'),
    ('descripcion', 'text', 'not null', 'Qué pide'),
    ('tipo_evidencia', 'enum:documento,registro,certificado_formacion,analisis,inspeccion', 'not null', 'Evidencia esperada'),
    ('regla_evidencia', 'varchar(80)', '', 'Revisión automática, ej. documento:protocolo, competencia:bioseguridad, registro:produccion.registro_bioseguridad'),
    ('vigencia_dias', 'smallint', '', 'Días que vale la evidencia'),
    ('critico', 'boolean', 'not null default false', 'Sin él no se certifica'),
], ['unique (norma_id, codigo)'])
tabla('cumplimiento', 'expediente', 1, 'Expediente de la finca ante una norma (incluye el registro sanitario de predio avícola, RSPA).', [
    ('norma_id', 'fk:cumplimiento.norma', 'not null unique', 'Norma'),
    ('estado', "enum:en_preparacion,solicitado,certificado,suspendido,vencido", "not null default 'en_preparacion'", 'Estado'),
    ('rspa_numero', 'varchar(40)', '', 'Registro sanitario de predio avícola (RSPA) del ICA, si aplica'),
    ('numero_certificado', 'varchar(60)', '', 'Número del certificado'),
    ('organismo', 'varchar(120)', '', 'Entidad u organismo certificador'),
    ('solicitado_en', 'date', '', 'Solicitud'),
    ('certificado_en', 'date', '', 'Certificación'),
    ('vence_en', 'date', '', 'Vencimiento'),
    ('responsable_id', USR, '', 'Responsable'),
])
tabla('cumplimiento', 'evaluacion_requisito', 1, 'Estado de cada requisito en el expediente. Con evidencia vencida pasa solo a no cumple.', [
    ('expediente_id', 'fk:cumplimiento.expediente', 'not null', 'Expediente'),
    ('requisito_id', 'fk:cumplimiento.requisito', 'not null', 'Requisito'),
    ('estado', "enum:cumple,no_cumple,en_proceso,no_aplica", "not null default 'en_proceso'", 'Estado'),
    ('origen', "enum:automatica,autoevaluacion,auditoria", "not null default 'autoevaluacion'", 'Cómo se evaluó'),
    ('evaluado_por', USR, '', 'Quién'),
    ('evaluado_en', 'timestamptz', '', 'Cuándo'),
    ('vence_en', 'date', '', 'Vencimiento de la evidencia que lo sostiene'),
    ('observacion', 'text', '', 'Nota'),
], ['unique (expediente_id, requisito_id)'])
tabla('cumplimiento', 'evidencia_requisito', 1, 'Prueba de un requisito: un documento o un registro del sistema, con su vencimiento.', [
    ('evaluacion_id', 'fk:cumplimiento.evaluacion_requisito', 'not null', 'Evaluación'),
    ('documento_id', 'fk:documental.documento', '', 'Documento'),
    ('registro_tabla', 'varchar(60)', '', 'Tabla del registro'),
    ('registro_id', 'bigint', '', 'Id'),
    ('descripcion', 'varchar(200)', 'not null', 'Qué prueba'),
    ('vence_en', 'date', '', 'Vence'),
], ['check (documento_id is not null or registro_id is not null)'])
tabla('cumplimiento', 'auditoria_externa', 1, 'Auditoría interna o externa programada, con aviso previo y resultado.', [
    ('expediente_id', 'fk:cumplimiento.expediente', 'not null', 'Expediente'),
    ('tipo', 'enum:interna,externa,seguimiento', 'not null', 'Tipo'),
    ('organismo', 'varchar(120)', '', 'Quién audita'),
    ('fecha_programada', 'date', 'not null', 'Fecha'),
    ('fecha_realizada', 'date', '', 'Realizada'),
    ('resultado', "enum:pendiente,aprobada,con_hallazgos,rechazada", "not null default 'pendiente'", 'Resultado'),
    ('informe_documento_id', 'fk:documental.documento', '', 'Informe'),
])
tabla('cumplimiento', 'no_conformidad', 1, 'Hallazgo; no se cierra sin acciones verificadas y sin quien verifique.', [
    ('expediente_id', 'fk:cumplimiento.expediente', 'not null', 'Expediente'),
    ('auditoria_id', 'fk:cumplimiento.auditoria_externa', '', 'Auditoría que la encontró'),
    ('requisito_id', 'fk:cumplimiento.requisito', '', 'Requisito'),
    ('descripcion', 'text', 'not null', 'Hallazgo'),
    ('severidad', 'enum:menor,mayor,critica', 'not null', 'Severidad'),
    ('detectada_en', 'date', 'not null', 'Fecha'),
    ('estado', "enum:abierta,en_tratamiento,cerrada", "not null default 'abierta'", 'Estado'),
    ('verificacion', 'text', '', 'Cómo se verificó el cierre'),
    ('cerrada_por', USR, '', 'Quién la cerró'),
    ('cerrada_en', 'timestamptz', '', 'Cuándo'),
])
tabla('cumplimiento', 'accion_correctiva', 1, 'Acción para corregir una no conformidad, con responsable, plazo y verificación; se asigna como tarea.', [
    ('no_conformidad_id', 'fk:cumplimiento.no_conformidad', 'not null', 'No conformidad'),
    ('descripcion', 'text', 'not null', 'Qué hacer'),
    ('responsable_id', USR, 'not null', 'Responsable'),
    ('plazo', 'date', 'not null', 'Plazo'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea'),
    ('estado', "enum:pendiente,hecha,verificada,ineficaz", "not null default 'pendiente'", 'Estado'),
    ('verificada_por', USR, '', 'Quién verificó'),
    ('verificada_en', 'timestamptz', '', 'Cuándo'),
])

# ---- seguros
tabla('seguros', 'poliza', 2, 'Póliza (cultivo, animales, equipos, responsabilidad civil del dron, paramétrico) con vigencia, prima, suma asegurada e incentivo de Finagro.', [
    ('numero', 'varchar(40)', 'not null unique', 'Número'),
    ('aseguradora_id', TER, 'not null', 'Aseguradora'),
    ('corredor_id', TER, '', 'Corredor'),
    ('tipo', 'enum:cultivo,animales,equipos,vehiculo,responsabilidad_civil,dron,parametrico,vida,otro', 'not null', 'Tipo'),
    ('desde', 'date', 'not null', 'Inicio'),
    ('hasta', 'date', 'not null', 'Fin'),
    ('prima', 'dinero', 'not null', 'Prima total'),
    ('incentivo_pct', 'numeric(5,2)', 'not null default 0', 'Porcentaje de la prima subsidiado (Incentivo al Seguro Agropecuario)'),
    ('valor_subsidiado', 'dinero', 'not null default 0', 'Valor subsidiado'),
    ('suma_asegurada', 'dinero', 'not null', 'Suma asegurada'),
    ('deducible', 'varchar(120)', '', 'Deducible'),
    ('estado', "enum:en_tramite,vigente,vencida,cancelada", "not null default 'en_tramite'", 'Estado'),
    ('avisar_dias', 'smallint', 'not null default 30', 'Aviso antes de vencer'),
    ('documento_id', 'fk:documental.documento', '', 'Póliza firmada'),
], ['check (hasta > desde)'])
tabla('seguros', 'bien_asegurado', 2, 'Lo que cubre la póliza: un activo, una siembra, un lote de animales o una zona.', [
    ('poliza_id', 'fk:seguros.poliza', 'not null', 'Póliza'),
    ('activo_id', 'fk:activos.activo', '', 'Equipo'),
    ('siembra_id', 'fk:produccion.siembra', '', 'Siembra'),
    ('lote_animal_id', 'fk:produccion.lote_animal', '', 'Lote'),
    ('zona_id', 'fk:nucleo.zona', '', 'Zona'),
    ('descripcion', 'varchar(200)', 'not null', 'Descripción'),
    ('valor_asegurado', 'dinero', 'not null', 'Valor'),
])
tabla('seguros', 'indice_poliza', 2, 'Regla del índice de un seguro paramétrico; la decide la aseguradora con su fuente, no los sensores de la finca.', [
    ('poliza_id', 'fk:seguros.poliza', 'not null', 'Póliza'),
    ('variable', 'enum:lluvia_mm,temperatura_c,dias_secos,viento_kmh,otro', 'not null', 'Variable'),
    ('fuente_oficial', 'varchar(150)', 'not null', 'Fuente que usa la aseguradora, ej. satélite CHIRPS'),
    ('comparador', 'enum:mayor,menor', 'not null', 'Se cumple si el valor es mayor o menor que el umbral'),
    ('umbral', 'numeric(10,2)', 'not null', 'Umbral'),
    ('ventana_dias', 'smallint', 'not null', 'Días acumulados'),
    ('sensor_id', 'fk:iot.sensor', '', 'Sensor propio con que se compara'),
])
tabla('seguros', 'aviso_siniestro', 2, 'Aviso de posible siniestro con la serie de datos como evidencia. No hay reclamación automática: una persona lo revisa y lo envía.', [
    ('poliza_id', 'fk:seguros.poliza', 'not null', 'Póliza'),
    ('indice_id', 'fk:seguros.indice_poliza', '', 'Índice, si es paramétrico'),
    ('detectado_en', 'timestamptz', 'not null', 'Cuándo'),
    ('descripcion', 'text', 'not null', 'Qué pasó'),
    ('serie_datos', 'jsonb', '', 'Datos usados como evidencia'),
    ('estado', "enum:borrador,revisado,enviado,pagado,rechazado,descartado", "not null default 'borrador'", 'Estado'),
    ('revisado_por', USR, '', 'Quién lo revisó'),
    ('enviado_en', 'timestamptz', '', 'Envío al corredor'),
    ('valor_reclamado', 'dinero', '', 'Reclamado'),
    ('valor_pagado', 'dinero', '', 'Pagado'),
])

# ---- ia, finanzas e iot (ampliados)
tabla('ia', 'diagnostico_imagen', 2, 'Foto de hoja, fruto o animal analizada por el agente Agrónomo. Es una propuesta: no crea compras ni aplicaciones; la confirma una persona.', [
    ('agente_id', 'fk:ia.agente', 'not null', 'Agente'),
    ('foto_url', 'varchar(300)', 'not null', 'Foto'),
    ('objetivo', 'enum:hoja,fruto,tallo,animal,huevo,otro', 'not null', 'Qué se fotografió'),
    ('siembra_id', 'fk:produccion.siembra', '', 'Siembra'),
    ('lote_animal_id', 'fk:produccion.lote_animal', '', 'Lote'),
    ('tomada_por', USR, 'not null', 'Quién la tomó'),
    ('diagnostico_propuesto', 'varchar(150)', '', 'Plaga o enfermedad probable'),
    ('confianza', 'numeric(4,3)', '', 'Confianza del modelo (0 a 1)'),
    ('resultado', 'jsonb', '', 'Alternativas y fotos parecidas'),
    ('estado', "enum:pendiente,confirmado,corregido,descartado", "not null default 'pendiente'", 'Revisión humana'),
    ('diagnostico_final', 'varchar(150)', '', 'Lo que decidió el agrónomo o el veterinario'),
    ('revisado_por', USR, '', 'Quién revisó'),
    ('revisado_en', 'timestamptz', '', 'Cuándo'),
], ['check (confianza is null or confianza between 0 and 1)'])
tabla('ia', 'escenario', 2, 'Simulación "qué pasa si" (sube el concentrado 10 %, se pasa de 100 a 500 gallinas, cae la postura).', [
    ('nombre', 'varchar(150)', 'not null', 'Nombre'),
    ('supuestos', 'jsonb', 'not null', 'Variables y valores supuestos'),
    ('resultado', 'jsonb', '', 'Resultado (margen, caja, punto de equilibrio)'),
    ('creado_por', USR, 'not null', 'Quién'),
    ('agente_id', 'fk:ia.agente', '', 'Agente que lo preparó'),
])
tabla('ia', 'decision', 2, 'Registro de decisiones: contexto, opciones, evidencia, quién decidió y, después, el resultado. Memoria de la finca.', [
    ('titulo', 'varchar(200)', 'not null', 'Decisión'),
    ('contexto', 'text', 'not null', 'Situación'),
    ('opciones', 'jsonb', 'not null', 'Opciones evaluadas'),
    ('evidencia', 'jsonb', '', 'Cifras y documentos'),
    ('opcion_elegida', 'varchar(200)', '', 'Lo que se decidió'),
    ('decidido_por', USR, '', 'Quién decidió (persona)'),
    ('decidido_en', 'timestamptz', '', 'Cuándo'),
    ('resultado_esperado', 'text', '', 'Qué se espera'),
    ('revisar_en', 'date', '', 'Cuándo revisar el resultado'),
    ('resultado_real', 'text', '', 'Qué pasó'),
    ('recomendacion_id', 'fk:ia.recomendacion', '', 'Recomendación que la originó'),
    ('escenario_id', 'fk:ia.escenario', '', 'Escenario usado'),
    ('iniciativa_id', 'fk:estrategia.iniciativa', '', 'Iniciativa de negocio decidida'),
])
tabla('finanzas', 'clasificacion_costo', 2, 'Cómo se comporta cada cuenta de costo o gasto: elemento (MD, MOD, CIF, administración, ventas, financiero) y comportamiento (fijo, variable, semivariable, escalonado). Base del costeo variable y de las palancas.', [
    ('cuenta_id', 'fk:finanzas.cuenta_contable', 'not null unique', 'Cuenta'),
    ('elemento', 'enum:material_directo,mano_obra_directa,cif,gasto_administracion,gasto_ventas,gasto_financiero,otro', 'not null', 'Elemento del costo'),
    ('comportamiento', 'enum:fijo,variable,semivariable,escalonado', 'not null', 'Comportamiento frente al volumen'),
    ('parte_fija_pct', 'numeric(5,2)', '', 'Porcentaje fijo de un costo semivariable'),
    ('controlable', 'boolean', 'not null default true', 'Lo controla el responsable del centro'),
    ('es_costo_producto', 'boolean', 'not null', 'Costo del producto (va al inventario) o costo del periodo'),
], ['check (parte_fija_pct is null or parte_fija_pct between 0 and 100)'])
tabla('finanzas', 'actividad_costo', 2, 'Actividad para costeo basado en actividades (ABC) con su inductor: horas de máquina, aves-día, jornales, m² regados.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código, ej. ALIMENTAR_AVES'),
    ('nombre', 'varchar(120)', 'not null', 'Actividad'),
    ('inductor', 'varchar(60)', 'not null', 'Inductor de costo, ej. aves_dia, horas_maquina, jornales'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Centro de servicio que la presta'),
])
tabla('finanzas', 'asignacion_costo', 2, 'Reparto mensual de costos indirectos a los centros según el inductor consumido.', [
    ('mes', 'date', 'not null', 'Mes'),
    ('actividad_id', 'fk:finanzas.actividad_costo', 'not null', 'Actividad'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', 'not null', 'Centro que la consume'),
    ('cantidad_inductor', 'numeric(14,2)', 'not null', 'Cantidad del inductor consumida'),
    ('valor_asignado', 'dinero', '', 'Valor asignado (lo calcula la regla)'),
], ['unique (mes, actividad_id, centro_costo_id)'])
tabla('finanzas', 'costo_estandar', 2, 'Costo estándar por unidad de producto (materiales, mano de obra y CIF) para comparar contra el real.', [
    ('producto_id', 'fk:inventario.producto', 'not null', 'Producto'),
    ('vigente_desde', 'date', 'not null', 'Desde'),
    ('material_directo', 'dinero', 'not null', 'MD por unidad'),
    ('mano_obra_directa', 'dinero', 'not null', 'MOD por unidad'),
    ('cif', 'dinero', 'not null', 'CIF por unidad'),
    ('costo_variable_unitario', 'dinero', 'not null', 'Parte variable del costo unitario'),
], ['unique (producto_id, vigente_desde)'])
tabla('finanzas', 'presupuesto', 2, 'Presupuesto maestro del año (operación y financiero), con versión y aprobación; puede ser base cero. Base para el informe al Fondo Emprender.', [
    ('nombre', 'varchar(150)', 'not null', 'Nombre'),
    ('anio', 'smallint', 'not null', 'Año'),
    ('version', 'smallint', 'not null default 1', 'Versión'),
    ('base_cero', 'boolean', 'not null default false', 'Cada rubro se justifica desde cero'),
    ('fuente', "enum:propio,fondo_emprender,credito,mixto", "not null default 'propio'", 'Fuente de los recursos'),
    ('estado', "enum:borrador,aprobado,cerrado", "not null default 'borrador'", 'Estado'),
    ('aprobado_por', USR, '', 'Quién lo aprobó'),
], ['unique (anio, nombre, version)'])
tabla('finanzas', 'premisa_presupuesto', 2, 'Premisas del presupuesto: inflación, salario mínimo, precio del concentrado, crecimiento del mercado, política de cartera.', [
    ('presupuesto_id', 'fk:finanzas.presupuesto', 'not null', 'Presupuesto'),
    ('tipo', 'enum:macroeconomica,microeconomica', 'not null', 'Tipo de premisa'),
    ('variable', 'varchar(80)', 'not null', 'Variable, ej. inflacion, precio_concentrado, pct_ventas_contado'),
    ('valor', 'numeric(14,4)', 'not null', 'Valor'),
    ('fuente', 'varchar(200)', '', 'Fuente (DANE, Banco de la República, cotización)'),
], ['unique (presupuesto_id, variable)'])
tabla('finanzas', 'presupuesto_detalle', 2, 'Rubro del presupuesto por mes, centro de costo y cuenta, en la secuencia del presupuesto maestro (ventas, producción, materias primas, mano de obra, CIF, gastos, inversión, financiación, caja).', [
    ('presupuesto_id', 'fk:finanzas.presupuesto', 'not null', 'Presupuesto'),
    ('componente', 'enum:ventas,produccion,materia_prima,mano_obra,cif,gastos_operacion,inversion,financiacion,flujo_caja', 'not null', 'Componente del presupuesto maestro'),
    ('mes', 'smallint', 'not null', 'Mes (1 a 12)'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Centro de costo'),
    ('cuenta_id', 'fk:finanzas.cuenta_contable', '', 'Cuenta'),
    ('producto_id', 'fk:inventario.producto', '', 'Producto (ventas y producción)'),
    ('cantidad', 'numeric(14,2)', '', 'Unidades'),
    ('valor', 'dinero', 'not null', 'Valor'),
    ('justificacion', 'text', '', 'Justificación (obligatoria en base cero)'),
], ['check (mes between 1 and 12)'])
tabla('finanzas', 'estado_financiero', 2, 'Estado financiero generado y congelado (balance, resultados por costeo variable o absorbente, flujo de efectivo directo o indirecto), real o presupuestado.', [
    ('tipo', 'enum:balance_general,resultados_absorbente,resultados_variable,flujo_efectivo_directo,flujo_efectivo_indirecto,cambios_patrimonio', 'not null', 'Estado'),
    ('desde', 'date', 'not null', 'Desde'),
    ('hasta', 'date', 'not null', 'Hasta'),
    ('presupuestado', 'boolean', 'not null default false', 'Es proforma (del presupuesto)'),
    ('datos', 'jsonb', 'not null', 'Partidas y totales'),
    ('generado_por', USR, '', 'Quién lo generó'),
])
tabla('finanzas', 'indicador', 2, 'Catálogo de indicadores financieros y de gestión con su fórmula, meta y semáforo (liquidez, endeudamiento, rentabilidad, rotación, EBITDA, EVA, Altman, palancas, postura por ave…).', [
    ('codigo', 'varchar(40)', 'not null unique', 'Código, ej. razon_corriente, rsp, gpo'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre'),
    ('grupo', 'enum:liquidez,endeudamiento,rentabilidad,actividad,valor,riesgo,palanca,produccion,comercial,personal,proyecto', 'not null', 'Grupo'),
    ('formula', 'text', 'not null', 'Fórmula'),
    ('interpretacion', 'text', '', 'Cómo leerlo'),
    ('unidad', "enum:veces,porcentaje,pesos,dias,unidades", 'not null', 'Unidad'),
    ('sentido', "enum:mayor_mejor,menor_mejor,rango", 'not null', 'Qué es mejor'),
])
tabla('finanzas', 'valor_indicador', 2, 'Valor calculado de un indicador en un periodo, con meta y semáforo para el tablero del administrador.', [
    ('indicador_id', 'fk:finanzas.indicador', 'not null', 'Indicador'),
    ('desde', 'date', 'not null', 'Desde'),
    ('hasta', 'date', 'not null', 'Hasta'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Línea, si es por línea'),
    ('valor', 'numeric(18,4)', '', 'Valor'),
    ('meta', 'numeric(18,4)', '', 'Meta'),
    ('semaforo', 'enum:verde,amarillo,rojo,sin_meta,sin_dato', 'not null', 'Semáforo (sin_meta: hay valor pero no hay meta fijada)'),
], ['index on (indicador_id, hasta)'])
tabla('finanzas', 'anticipo_proveedor', 2, 'Pago adelantado a un proveedor: queda como saldo a favor y se descuenta en las compras siguientes; nunca queda negativo. No se reciben recargas de clientes.', [
    ('proveedor_id', 'fk:terceros.proveedor', 'not null', 'Proveedor'),
    ('fecha', 'date', 'not null', 'Fecha'),
    ('valor', 'dinero', 'not null', 'Valor'),
    ('saldo', 'dinero', 'not null', 'Saldo por descontar'),
    ('comprobante_id', 'fk:finanzas.comprobante', '', 'Comprobante'),
    ('estado', "enum:abierto,aplicado,devuelto", "not null default 'abierto'", 'Estado'),
], ['check (valor > 0 and saldo >= 0 and saldo <= valor)'])
tabla('finanzas', 'aplicacion_anticipo', 2, 'Descuento de un anticipo en una orden de compra.', [
    ('anticipo_id', 'fk:finanzas.anticipo_proveedor', 'not null', 'Anticipo'),
    ('orden_compra_id', 'fk:compras.orden_compra', 'not null', 'Compra'),
    ('valor', 'dinero', 'not null', 'Valor descontado'),
], ['check (valor > 0)'])
tabla('finanzas', 'reporte_indicadores', 3, 'Informe de indicadores verificables para Finagro, bancos, gremios o certificadores, con autorización del titular y sin costos ni datos personales.', [
    ('destinatario', 'enum:finagro,banco,gremio,certificador,fondo_emprender,otro', 'not null', 'A quién va'),
    ('tercero_id', TER, '', 'Entidad'),
    ('desde', 'date', 'not null', 'Desde'),
    ('hasta', 'date', 'not null', 'Hasta'),
    ('contenido', 'jsonb', 'not null', 'Indicadores (producción, ventas, cumplimiento)'),
    ('hash_sha256', 'char(64)', 'not null', 'Huella del contenido (verificable)'),
    ('autorizado_por', USR, 'not null', 'Titular que autorizó compartirlo'),
    ('enviado_en', 'timestamptz', '', 'Envío'),
])
tabla('iot', 'mision_robot', 4, 'Misión de un dron de monitoreo o de un robot de campo en piloto: una persona la aprueba; el robot opera solo en zonas sin personas y con parada de emergencia probada.', [
    ('activo_id', 'fk:activos.activo', 'not null', 'Dron o robot'),
    ('tipo', 'enum:dron_monitoreo,robot_deshierbe,robot_monitoreo', 'not null', 'Tipo'),
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Zona'),
    ('estado', "enum:propuesta,aprobada,en_curso,terminada,abortada", "not null default 'propuesta'", 'Estado'),
    ('aprobada_por', USR, '', 'Quién la aprobó'),
    ('piloto_id', TER, '', 'Piloto certificado (dron)'),
    ('poliza_id', 'fk:seguros.poliza', '', 'Póliza de responsabilidad civil (dron)'),
    ('altura_max_m', 'numeric(5,1)', '', 'Altura máxima (RAC 100: hasta 122 m)'),
    ('zona_sin_personas', 'boolean', 'not null default false', 'Se confirmó que no hay personas en la zona'),
    ('parada_emergencia_probada', 'boolean', 'not null default false', 'Se probó la parada de emergencia'),
    ('inicio', 'timestamptz', '', 'Inicio'),
    ('fin', 'timestamptz', '', 'Fin'),
    ('resultado', 'jsonb', '', 'Fotos, conteos y lecturas devueltas'),
])
tabla('iot', 'prioridad_carga', 4, 'Prioridad de cada carga eléctrica: con batería baja se cortan primero las no esenciales; alarma, nevera y agua de animales van primero.', [
    ('actuador_id', 'fk:iot.actuador', 'not null unique', 'Carga (relé)'),
    ('prioridad', 'smallint', 'not null', '1 = crítica … 5 = prescindible'),
    ('esencial', 'boolean', 'not null', 'Nunca se corta automáticamente'),
    ('corte_bateria_pct', 'smallint', '', 'Porcentaje de batería bajo el cual se corta'),
], ['check (prioridad between 1 and 5)', 'check (not esencial or corte_bateria_pct is null)'])

# ---- integración externa
tabla('nucleo', 'llave_api', 3, 'Llave de un cliente B2B (HORECA) para la API: guarda solo su huella, con alcances, límite de peticiones y vencimiento. Se enciende con api_b2b.', [
    ('tercero_id', TER, 'not null', 'Cliente dueño de la llave'),
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('prefijo', 'varchar(12)', 'not null unique', 'Prefijo visible para identificarla'),
    ('hash_llave', 'char(64)', 'not null', 'Huella SHA-256 de la llave (la llave nunca se guarda)'),
    ('alcances', 'text[]', "not null default '{catalogo:leer}'", 'Permisos: catalogo:leer, pedidos:leer, pedidos:crear'),
    ('limite_por_minuto', 'smallint', 'not null default 60', 'Límite de peticiones'),
    ('activa', 'boolean', 'not null default false', 'Encendida'),
    ('vence_en', 'date', 'not null', 'Vencimiento'),
    ('ultimo_uso', 'timestamptz', '', 'Último uso'),
])
tabla('nucleo', 'webhook_suscripcion', 3, 'Sistema externo (comprador, logística) que recibe eventos firmados del outbox: pedido confirmado, lote despachado, factura emitida.', [
    ('nombre', 'varchar(80)', 'not null', 'Nombre'),
    ('tercero_id', TER, '', 'Dueño'),
    ('url', 'varchar(300)', 'not null', 'URL https de destino'),
    ('eventos', 'text[]', 'not null', 'Tipos de evento'),
    ('secreto_ref', 'varchar(120)', 'not null', 'Nombre del secreto para firmar (HMAC); nunca el secreto'),
    ('activa', 'boolean', 'not null default false', 'Encendida'),
    ('fallos_seguidos', 'smallint', 'not null default 0', 'Fallos seguidos (al llegar a 10 se apaga)'),
], ["check (url like 'https://%')"])
tabla('nucleo', 'webhook_entrega', 3, 'Intento de entrega de un evento a un webhook, con reintentos.', [
    ('suscripcion_id', 'fk:nucleo.webhook_suscripcion', 'not null', 'Suscripción'),
    ('evento_salida_id', 'bigint', 'not null', 'Evento del outbox'),
    ('estado', "enum:pendiente,entregado,fallido", "not null default 'pendiente'", 'Estado'),
    ('intentos', 'smallint', 'not null default 0', 'Intentos'),
    ('codigo_respuesta', 'smallint', '', 'Código HTTP'),
    ('proximo_intento', 'timestamptz', '', 'Próximo intento'),
], ['unique (suscripcion_id, evento_salida_id)'])

# ---- seguridad informática (catálogos de plataforma: el inicio de sesión ocurre antes de elegir finca)
tabla('seguridad', 'factor_autenticacion', 1, 'Segundo factor del usuario: app TOTP o llave de acceso (passkey/WebAuthn). Obligatorio para administrador y contador. El secreto vive en el gestor de secretos.', [
    ('usuario_id', USR, 'not null', 'Usuario'),
    ('tipo', 'enum:totp,webauthn,codigo_respaldo', 'not null', 'Tipo (sin biometría guardada en el servidor)'),
    ('nombre', 'varchar(60)', 'not null', 'Nombre del dispositivo'),
    ('secreto_ref', 'varchar(120)', 'not null', 'Referencia al secreto o a la llave pública'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
    ('ultimo_uso', 'timestamptz', '', 'Último uso'),
])
tabla('seguridad', 'sesion_usuario', 1, 'Sesión iniciada: método, IP, dispositivo y vencimiento; se puede revocar en bloque ante un incidente.', [
    ('usuario_id', USR, 'not null', 'Usuario'),
    ('metodo', 'enum:contrasena,doble_factor,llave_acceso,token_dispositivo', 'not null', 'Cómo se autenticó'),
    ('ip', 'inet', 'not null', 'IP'),
    ('agente_usuario', 'varchar(300)', '', 'Navegador o app'),
    ('dispositivo_captura_id', 'bigint', '', 'Celular de campo registrado'),
    ('iniciada_en', 'timestamptz', 'not null default now()', 'Inicio'),
    ('vence_en', 'timestamptz', 'not null', 'Vencimiento'),
    ('revocada_en', 'timestamptz', '', 'Revocación'),
    ('motivo_revocacion', 'varchar(120)', '', 'Motivo'),
], ['index on (usuario_id, iniciada_en)'])
tabla('seguridad', 'intento_acceso', 1, 'Cada intento de inicio de sesión, exitoso o no (solo inserción). Alimenta el detector de ataques.', [
    ('correo', 'citext', 'not null', 'Correo intentado'),
    ('usuario_id', USR, '', 'Usuario, si existe'),
    ('ip', 'inet', 'not null', 'IP'),
    ('exito', 'boolean', 'not null', 'Entró'),
    ('motivo_fallo', 'enum:contrasena,usuario_inexistente,cuenta_bloqueada,ip_bloqueada,segundo_factor,cuenta_inactiva,senuelo', '', 'Motivo del fallo'),
    ('agente_usuario', 'varchar(300)', '', 'Navegador o app'),
    ('ocurrido_en', 'timestamptz', 'not null default now()', 'Momento'),
], ['index on (ip, ocurrido_en)', 'index on (correo, ocurrido_en)'], auditoria=False)
tabla('seguridad', 'regla_deteccion', 1, 'Regla del detector de ataques: cuántos hechos en cuánto tiempo, severidad y respuesta automática.', [
    ('codigo', 'varchar(40)', 'not null unique', 'Código, ej. fuerza_bruta_cuenta'),
    ('descripcion', 'text', 'not null', 'Qué detecta'),
    ('umbral', 'smallint', 'not null', 'Número de hechos'),
    ('ventana_min', 'smallint', 'not null', 'Minutos'),
    ('severidad', 'enum:baja,media,alta,critica', 'not null', 'Severidad'),
    ('respuesta', 'enum:alertar,bloquear_ip,bloquear_cuenta,revocar_sesiones', 'not null', 'Qué hace sola'),
    ('bloqueo_min', 'smallint', 'not null default 30', 'Minutos de bloqueo'),
    ('activa', 'boolean', 'not null default true', 'Encendida'),
])
tabla('seguridad', 'bloqueo', 1, 'Bloqueo temporal de una cuenta o una IP por una regla o una persona.', [
    ('tipo', 'enum:cuenta,ip', 'not null', 'Qué se bloquea'),
    ('usuario_id', USR, '', 'Cuenta'),
    ('ip', 'cidr', '', 'IP o red'),
    ('regla_id', 'fk:seguridad.regla_deteccion', '', 'Regla que lo puso'),
    ('motivo', 'varchar(200)', 'not null', 'Motivo'),
    ('desde', 'timestamptz', 'not null default now()', 'Desde'),
    ('hasta', 'timestamptz', '', 'Hasta; vacío = indefinido'),
    ('levantado_por', USR, '', 'Quién lo levantó'),
], ["check ((tipo = 'cuenta' and usuario_id is not null) or (tipo = 'ip' and ip is not null))"])
tabla('seguridad', 'senuelo', 1, 'Señuelo para intrusos (cuenta, llave de API o URL que nadie legítimo usa): tocarlo dispara una alerta crítica y bloquea la IP.', [
    ('tipo', 'enum:cuenta,llave_api,url,registro', 'not null', 'Tipo'),
    ('valor', 'varchar(200)', 'not null unique', 'Correo, prefijo o ruta del señuelo'),
    ('descripcion', 'varchar(200)', '', 'Para qué está'),
    ('activo', 'boolean', 'not null default true', 'Encendido'),
])
tabla('seguridad', 'alerta_seguridad', 1, 'Hecho sospechoso detectado por las reglas, el WAF, la pasarela o la base (fuerza bruta, escalada de permisos, exportación masiva, señuelo). Solo inserción salvo su atención.', [
    ('tipo', 'enum:fuerza_bruta,relleno_credenciales,senuelo,escalada_privilegios,cambio_permisos,exportacion_masiva,acceso_ip_nueva,sesion_sin_doble_factor,inyeccion,abuso_api,dispositivo_desconocido,firmware_no_firmado,copia_fallida,otro', 'not null', 'Qué pasó'),
    ('severidad', 'enum:baja,media,alta,critica', 'not null', 'Severidad'),
    ('fuente', 'enum:app,base_datos,waf,api,pasarela,agente_ia,monitoreo', 'not null', 'Quién lo detectó'),
    ('regla_id', 'fk:seguridad.regla_deteccion', '', 'Regla'),
    ('usuario_id', USR, '', 'Usuario implicado'),
    ('ip', 'inet', '', 'IP'),
    ('predio_id', 'fk:nucleo.predio', '', 'Finca afectada, si aplica'),
    ('detalle', 'jsonb', '', 'Datos del hecho'),
    ('ocurrido_en', 'timestamptz', 'not null default now()', 'Momento'),
    ('estado', "enum:nueva,en_analisis,contenida,falso_positivo,cerrada", "not null default 'nueva'", 'Atención'),
    ('atendida_por', USR, '', 'Quién la atendió'),
    ('incidente_id', 'fk:seguridad.incidente', '', 'Incidente al que pertenece'),
], ['index on (ocurrido_en)'])
tabla('seguridad', 'incidente', 1, 'Incidente de seguridad con su atención; si compromete datos personales se reporta a la SIC (Ley 1581).', [
    ('titulo', 'varchar(200)', 'not null', 'Título'),
    ('severidad', 'enum:baja,media,alta,critica', 'not null', 'Severidad'),
    ('estado', "enum:abierto,contenido,erradicado,cerrado", "not null default 'abierto'", 'Estado'),
    ('responsable_id', USR, 'not null', 'Responsable'),
    ('datos_personales_afectados', 'boolean', 'not null default false', 'Hubo datos personales comprometidos'),
    ('reportado_sic_en', 'date', '', 'Reporte a la Superintendencia de Industria y Comercio'),
    ('abierto_en', 'timestamptz', 'not null default now()', 'Apertura'),
    ('cerrado_en', 'timestamptz', '', 'Cierre'),
    ('lecciones', 'text', '', 'Lecciones aprendidas'),
])
tabla('seguridad', 'ejecucion_prueba', 1, 'Módulo de pruebas: cada corrida de pruebas (unitarias, de reglas de la base, extremo a extremo, carga, dependencias, SAST, DAST, pentest, restauración de copias) con su resultado.', [
    ('tipo', 'enum:unitaria,integracion,reglas_bd,extremo_a_extremo,carga,dependencias,sast,dast,pentest,restauracion_copia,simulacro_incidente', 'not null', 'Tipo de prueba'),
    ('suite', 'varchar(80)', 'not null', 'Suite, ej. pruebas_reglas_v5'),
    ('version_sistema', 'varchar(20)', 'not null', 'Versión probada'),
    ('entorno', "enum:desarrollo,pruebas,practica,produccion", 'not null', 'Dónde corrió (nunca pentest en producción sin aprobación)'),
    ('total', 'integer', 'not null', 'Casos'),
    ('aprobadas', 'integer', 'not null', 'Aprobados'),
    ('fallidas', 'integer', 'not null', 'Fallidos'),
    ('hallazgos_criticos', 'integer', 'not null default 0', 'Hallazgos críticos (seguridad)'),
    ('herramienta', 'varchar(60)', '', 'Herramienta, ej. pytest, pgTAP, OWASP ZAP, pip-audit'),
    ('informe_url', 'varchar(300)', '', 'Informe'),
    ('ejecutada_en', 'timestamptz', 'not null default now()', 'Cuándo'),
    ('ejecutada_por', USR, '', 'Quién'),
], ['check (aprobadas + fallidas <= total)'])
tabla('seguridad', 'copia_seguridad', 1, 'Copia cifrada de la base o los archivos (regla 3-2-1) y su prueba mensual de restauración.', [
    ('alcance', 'enum:postgresql,mongodb,archivos,configuracion', 'not null', 'Qué se copió'),
    ('destino', 'enum:local,nube,disco_externo', 'not null', 'Dónde'),
    ('inicio', 'timestamptz', 'not null', 'Inicio'),
    ('fin', 'timestamptz', '', 'Fin'),
    ('tamano_mb', 'numeric(12,1)', '', 'Tamaño'),
    ('hash_sha256', 'char(64)', '', 'Huella'),
    ('cifrada', 'boolean', 'not null', 'Cifrada'),
    ('exitosa', 'boolean', 'not null', 'Terminó bien'),
    ('restauracion_probada_en', 'timestamptz', '', 'Última prueba de restauración'),
], ['check (cifrada)'])

# ---- crm: posibles clientes, personas y empresas
tabla('crm', 'segmento', 2, 'Segmento de mercado (hogares, tiendas, restaurantes, hoteles, colegios, exportadores) con sus criterios: base de la palanca de mercadeo.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('criterios', 'jsonb', '', 'Criterios (municipio, tipo de negocio, volumen)'),
    ('propuesta_valor', 'text', '', 'Qué se le ofrece y por qué paga más'),
])
tabla('crm', 'campana', 2, 'Campaña para captar clientes: canal, segmento, presupuesto, costo real y conversiones (costo por cliente nuevo).', [
    ('nombre', 'varchar(150)', 'not null', 'Nombre'),
    ('canal', 'enum:whatsapp,instagram,facebook,tiktok,feria,mercado_campesino,visita_finca,referidos,web,volanteo,otro', 'not null', 'Canal'),
    ('segmento_id', 'fk:crm.segmento', '', 'Segmento'),
    ('objetivo', 'text', '', 'Objetivo'),
    ('desde', 'date', 'not null', 'Inicio'),
    ('hasta', 'date', '', 'Fin'),
    ('presupuesto', 'dinero', 'not null default 0', 'Presupuesto'),
    ('costo_real', 'dinero', 'not null default 0', 'Costo real'),
    ('publicacion_id', 'fk:redes.publicacion', '', 'Publicación de redes asociada'),
])
tabla('crm', 'formulario_captura', 2, 'Formulario para registrar posibles clientes (web, QR en ferias, WhatsApp) con su texto de autorización de datos y finalidad.', [
    ('codigo', 'varchar(30)', 'not null unique', 'Código'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('canal', 'enum:web,qr_feria,whatsapp,tablet_finca,otro', 'not null', 'Dónde se usa'),
    ('campos', 'jsonb', 'not null', 'Campos que pide (mínimos necesarios)'),
    ('texto_autorizacion', 'text', 'not null', 'Texto de autorización de tratamiento de datos (Ley 1581)'),
    ('finalidad', 'text', 'not null', 'Para qué se usarán los datos'),
    ('campana_id', 'fk:crm.campana', '', 'Campaña'),
    ('activo', 'boolean', 'not null default true', 'Publicado'),
])
tabla('crm', 'prospecto', 2, 'Posible cliente, persona o empresa. No se le escribe sin autorización; al comprar se convierte en tercero y cliente.', [
    ('tipo', 'enum:persona,empresa', 'not null', 'Tipo'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre o razón social'),
    ('nit', 'varchar(20)', '', 'NIT de la empresa (las personas no necesitan documento para ser prospecto)'),
    ('sector', 'enum:hogar,tienda,restaurante,hotel,colegio,casino,supermercado,distribuidor,exportador,agencia_turismo,institucion,otro', 'not null', 'Sector'),
    ('municipio', 'varchar(80)', '', 'Municipio'),
    ('telefono', 'varchar(20)', '', 'Celular'),
    ('correo', 'citext', '', 'Correo'),
    ('canal_origen', 'enum:whatsapp,instagram,facebook,tiktok,feria,mercado_campesino,visita_finca,referido,web,llamada,base_publica,otro', 'not null', 'Cómo llegó'),
    ('formulario_id', 'fk:crm.formulario_captura', '', 'Formulario por el que se registró'),
    ('campana_id', 'fk:crm.campana', '', 'Campaña'),
    ('segmento_id', 'fk:crm.segmento', '', 'Segmento'),
    ('intereses', 'text[]', '', 'Productos o servicios de interés'),
    ('volumen_estimado_mes', 'dinero', '', 'Compra mensual estimada'),
    ('etapa', "enum:nuevo,contactado,calificado,propuesta,negociacion,ganado,perdido,descartado", "not null default 'nuevo'", 'Etapa del embudo'),
    ('puntaje', 'smallint', 'not null default 0', 'Puntaje de calificación (0 a 100)'),
    ('responsable_id', USR, '', 'Vendedor responsable'),
    ('consentimiento_id', 'fk:terceros.consentimiento_datos', '', 'Autorización de datos; sin ella solo se guarda la empresa (datos públicos), no se contacta'),
    ('tercero_id', TER, '', 'Tercero al convertirse en cliente'),
    ('motivo_perdida', 'varchar(200)', '', 'Por qué se perdió'),
    ('proximo_contacto', 'date', '', 'Próximo contacto'),
], ['check (puntaje between 0 and 100)', 'index on (etapa, proximo_contacto)'])
tabla('crm', 'contacto_empresa', 2, 'Persona de contacto dentro de una empresa prospecto (compras, chef, administrador), con su propia autorización.', [
    ('prospecto_id', 'fk:crm.prospecto', 'not null', 'Empresa'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre'),
    ('cargo', 'varchar(80)', '', 'Cargo'),
    ('telefono', 'varchar(20)', '', 'Celular'),
    ('correo', 'citext', '', 'Correo'),
    ('consentimiento_id', 'fk:terceros.consentimiento_datos', '', 'Autorización'),
])
tabla('crm', 'interaccion', 2, 'Contacto con un prospecto o cliente (llamada, WhatsApp, visita, degustación, feria) y su próximo paso.', [
    ('prospecto_id', 'fk:crm.prospecto', '', 'Prospecto'),
    ('tercero_id', TER, '', 'Cliente existente'),
    ('tipo', 'enum:llamada,whatsapp,visita,correo,reunion,degustacion,feria,visita_finca', 'not null', 'Tipo'),
    ('fecha', 'timestamptz', 'not null', 'Cuándo'),
    ('resumen', 'text', 'not null', 'Qué se habló'),
    ('proximo_paso', 'varchar(200)', '', 'Próximo paso'),
    ('usuario_id', USR, '', 'Quién'),
    ('agente_id', 'fk:ia.agente', '', 'Agente, si la atendió uno'),
], ['check (prospecto_id is not null or tercero_id is not null)'])
tabla('crm', 'oportunidad', 2, 'Negocio posible con un prospecto o cliente: productos, valor, probabilidad y fecha de cierre (proyección del embudo).', [
    ('prospecto_id', 'fk:crm.prospecto', '', 'Prospecto'),
    ('tercero_id', TER, '', 'Cliente'),
    ('titulo', 'varchar(150)', 'not null', 'Título'),
    ('productos', 'jsonb', '', 'Productos y cantidades'),
    ('valor_estimado', 'dinero', 'not null', 'Valor estimado'),
    ('probabilidad_pct', 'smallint', 'not null', 'Probabilidad de cierre'),
    ('cierre_estimado', 'date', '', 'Fecha estimada'),
    ('estado', "enum:abierta,ganada,perdida", "not null default 'abierta'", 'Estado'),
    ('pedido_id', 'fk:comercial.pedido', '', 'Pedido que la cerró'),
    ('linea_negocio_id', 'fk:estrategia.linea_negocio', '', 'Línea de negocio'),
], ['check (probabilidad_pct between 0 and 100)', 'check (prospecto_id is not null or tercero_id is not null)'])

# ---- estrategia: diversificación del negocio y reinversión con retorno medido
tabla('estrategia', 'linea_negocio', 2, 'Línea de negocio de la finca (avícola, piscícola, perennes, turismo…) o una nueva en estudio, unida a su centro de costo.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Centro de costo'),
    ('estado', "enum:actual,en_estudio,piloto,descartada,cerrada", "not null default 'actual'", 'Estado'),
    ('palanca_dominante', 'enum:mercadeo,produccion,operacional,financiera', '', 'Palanca con la que genera recursos'),
    ('descripcion', 'text', '', 'Descripción'),
])
tabla('estrategia', 'factor_dofa', 2, 'Debilidad, oportunidad, fortaleza o amenaza de la finca o de una línea, con su fuente.', [
    ('tipo', 'enum:debilidad,oportunidad,fortaleza,amenaza', 'not null', 'Tipo'),
    ('linea_negocio_id', 'fk:estrategia.linea_negocio', '', 'Línea (vacío = toda la finca)'),
    ('descripcion', 'text', 'not null', 'Descripción'),
    ('impacto', 'smallint', 'not null', 'Impacto 1 a 5'),
    ('fuente', 'varchar(200)', '', 'Fuente'),
    ('vigente', 'boolean', 'not null default true', 'Vigente'),
], ['check (impacto between 1 and 5)'])
tabla('estrategia', 'estudio_mercado', 2, 'Dato de un mercado posible: tamaño, precio de referencia, competidores y fuente (SIPSA, DANE, gremios, visitas).', [
    ('mercado', 'varchar(150)', 'not null', 'Mercado, ej. huevo campesino en hoteles de Girardot'),
    ('segmento_id', 'fk:crm.segmento', '', 'Segmento'),
    ('tamano_estimado', 'dinero', '', 'Ventas anuales estimadas del mercado'),
    ('precio_referencia', 'dinero', '', 'Precio de referencia'),
    ('competidores', 'text', '', 'Competidores'),
    ('barreras', 'text', '', 'Barreras de entrada (registros, certificaciones, frío)'),
    ('fuente', 'varchar(200)', 'not null', 'Fuente'),
    ('fecha', 'date', 'not null', 'Fecha del dato'),
])
tabla('estrategia', 'iniciativa', 2, 'Idea de crecimiento: nuevo mercado, producto, canal o negocio, clasificada por la matriz de Ansoff y por la palanca que usa. La IA puede proponerla; decide la familia.', [
    ('titulo', 'varchar(200)', 'not null', 'Título'),
    ('descripcion', 'text', 'not null', 'Descripción'),
    ('ansoff', 'enum:penetracion_mercado,desarrollo_mercado,desarrollo_producto,diversificacion', 'not null', 'Cuadrante de la matriz de Ansoff'),
    ('tipo', 'enum:nuevo_mercado,nuevo_producto,nuevo_canal,nueva_linea,valor_agregado,integracion_vertical,mejora_proceso', 'not null', 'Tipo'),
    ('palanca', 'enum:mercadeo,produccion,operacional,financiera', 'not null', 'Palanca principal'),
    ('linea_negocio_id', 'fk:estrategia.linea_negocio', '', 'Línea existente o nueva'),
    ('segmento_id', 'fk:crm.segmento', '', 'Segmento al que apunta'),
    ('hipotesis', 'text', '', 'Qué se cree y cómo se probará'),
    ('estado', "enum:idea,en_evaluacion,aprobada,piloto,escalada,descartada", "not null default 'idea'", 'Estado'),
    ('propuesta_por', USR, '', 'Quién la propuso'),
    ('agente_id', 'fk:ia.agente', '', 'Agente que la propuso'),
    ('aprobada_por', USR, '', 'Quién la aprobó (persona)'),
    ('aprobada_en', 'timestamptz', '', 'Cuándo'),
    ('puntaje', 'numeric(5,2)', '', 'Puntaje de priorización'),
])
tabla('estrategia', 'evaluacion_proyecto', 2, 'Evaluación financiera de una iniciativa: inversión, flujos, VPN, TIR, ROI, recuperación, punto de equilibrio, margen de seguridad y grados de palanca. La calcula la base.', [
    ('iniciativa_id', 'fk:estrategia.iniciativa', 'not null', 'Iniciativa'),
    ('version', 'smallint', 'not null default 1', 'Versión'),
    ('inversion_inicial', 'dinero', 'not null', 'Inversión inicial'),
    ('horizonte_meses', 'smallint', 'not null', 'Horizonte'),
    ('tasa_descuento_anual', 'numeric(6,4)', 'not null', 'Costo de capital (tasa de oportunidad) anual'),
    ('precio_unitario', 'dinero', '', 'Precio de venta por unidad'),
    ('costo_variable_unitario', 'dinero', '', 'Costo variable por unidad'),
    ('costos_fijos_mes', 'dinero', '', 'Costos fijos operacionales del mes'),
    ('intereses_mes', 'dinero', 'not null default 0', 'Intereses del mes si se financia con deuda'),
    ('unidades_mes', 'numeric(12,2)', '', 'Unidades esperadas por mes'),
    ('fuente_fondos', 'enum:utilidades_retenidas,credito,fondo_emprender,aporte_familia,mixto', 'not null', 'De dónde sale la plata'),
    ('vpn', 'dinero', '', 'Valor presente neto'),
    ('tir_anual', 'numeric(8,4)', '', 'Tasa interna de retorno anual'),
    ('roi_pct', 'numeric(8,2)', '', 'Retorno sobre la inversión en el horizonte'),
    ('recuperacion_meses', 'smallint', '', 'Meses para recuperar la inversión'),
    ('punto_equilibrio_unidades', 'numeric(12,2)', '', 'Unidades por mes para no perder'),
    ('margen_seguridad_pct', 'numeric(8,2)', '', 'Cuánto pueden caer las ventas sin pérdida'),
    ('gpo', 'numeric(10,4)', '', 'Grado de palanca operativa'),
    ('gpf', 'numeric(10,4)', '', 'Grado de palanca financiera'),
    ('gpt', 'numeric(10,4)', '', 'Grado de palanca total'),
    ('riesgos', 'text', '', 'Riesgos (costos fijos, deuda, precio)'),
    ('calculado_en', 'timestamptz', '', 'Cuándo se calculó'),
], ['unique (iniciativa_id, version)', 'check (inversion_inicial >= 0 and horizonte_meses > 0)'])
tabla('estrategia', 'flujo_proyecto', 2, 'Flujo de caja proyectado de una evaluación por mes (mes 0 = inversión).', [
    ('evaluacion_id', 'fk:estrategia.evaluacion_proyecto', 'not null', 'Evaluación'),
    ('mes', 'smallint', 'not null', 'Mes (0 = inversión)'),
    ('ingresos', 'dinero', 'not null default 0', 'Ingresos'),
    ('egresos', 'dinero', 'not null default 0', 'Egresos'),
    ('inversion', 'dinero', 'not null default 0', 'Inversión'),
], ['unique (evaluacion_id, mes)'])
tabla('estrategia', 'reinversion', 2, 'Parte de la utilidad de una línea que se destina a una iniciativa (apalancarse con lo ganado). Nunca de una línea con pérdida ni por encima del tope de reinversión.', [
    ('anio', 'smallint', 'not null', 'Año de la utilidad'),
    ('mes', 'smallint', 'not null', 'Mes de la utilidad'),
    ('linea_origen_id', 'fk:estrategia.linea_negocio', 'not null', 'Línea que generó la utilidad'),
    ('utilidad_linea', 'dinero', 'not null', 'Utilidad neta de la línea en el mes (de la contabilidad)'),
    ('valor', 'dinero', 'not null', 'Valor reinvertido'),
    ('iniciativa_id', 'fk:estrategia.iniciativa', 'not null', 'Iniciativa destino'),
    ('estado', "enum:propuesta,aprobada,ejecutada,cancelada", "not null default 'propuesta'", 'Estado'),
    ('aprobada_por', USR, '', 'Quién la aprobó'),
], ['check (valor > 0)', 'check (mes between 1 and 12)'])
tabla('estrategia', 'seguimiento_iniciativa', 2, 'Resultado real mes a mes de una iniciativa en piloto o escalada, contra lo proyectado: así se mide el retorno de verdad.', [
    ('iniciativa_id', 'fk:estrategia.iniciativa', 'not null', 'Iniciativa'),
    ('mes', 'date', 'not null', 'Mes'),
    ('ingresos_reales', 'dinero', 'not null default 0', 'Ingresos'),
    ('egresos_reales', 'dinero', 'not null default 0', 'Egresos'),
    ('unidades_reales', 'numeric(12,2)', '', 'Unidades'),
    ('nota', 'text', '', 'Aprendizajes'),
], ['unique (iniciativa_id, mes)'])
tabla('estrategia', 'objetivo', 2, 'Objetivo estratégico por perspectiva del cuadro de mando (financiera, clientes, procesos, aprendizaje), con indicador y meta.', [
    ('perspectiva', 'enum:financiera,clientes,procesos,aprendizaje', 'not null', 'Perspectiva'),
    ('descripcion', 'text', 'not null', 'Objetivo'),
    ('indicador_id', 'fk:finanzas.indicador', '', 'Indicador'),
    ('meta', 'numeric(18,4)', '', 'Meta'),
    ('fecha_meta', 'date', '', 'Para cuándo'),
    ('responsable_id', USR, '', 'Responsable'),
])


# ---- personal · áreas de responsabilidad y cronograma flexible 24/7
tabla('personal', 'area_responsabilidad', 2, 'Área de responsabilidad (galpón, cultivos, turismo y cabañas, bodega y despachos, mantenimiento, vigilancia): agrupa zonas, personas y tareas, con un responsable.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. AR-GALPON'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('descripcion', 'text', '', 'Qué cubre'),
    ('zonas', 'bigint[]', '', 'Zonas que abarca'),
    ('centro_costo_id', 'fk:finanzas.centro_costo', '', 'Centro de costo'),
    ('opera_24_7', 'boolean', 'not null default false', 'Necesita cobertura las 24 horas, todos los días (vigilancia, galpón)'),
    ('activa', 'boolean', 'not null default true', 'En uso'),
])
tabla('personal', 'miembro_area', 2, 'Personas de cada área, con quién es el responsable (puede aprobar las tareas del área).', [
    ('area_id', 'fk:personal.area_responsabilidad', 'not null', 'Área'),
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('es_responsable', 'boolean', 'not null default false', 'Responsable del área'),
    ('desde', 'date', 'not null', 'Desde'),
    ('hasta', 'date', '', 'Hasta'),
], ['unique (area_id, empleado_id, desde)'])
tabla('personal', 'patron_turno', 2, 'Patrón de turnos reutilizable: semanal (se eligen días y horas), cíclico (ej. 2 días, 2 noches, 2 de descanso para 24/7) o flexible (se arma a mano).', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. SEM-LV-6-14, CIC-2D2N2L'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('tipo', 'enum:semanal,ciclico,flexible', 'not null', 'Semanal: día 1 = lunes … 7 = domingo; cíclico: día 1 … N del ciclo'),
    ('ciclo_dias', 'smallint', 'not null default 7', 'Días del ciclo'),
], ['check (ciclo_dias between 1 and 56)'])
tabla('personal', 'patron_turno_detalle', 2, 'Día del patrón con su horario (puede cruzar la medianoche) o descanso.', [
    ('patron_id', 'fk:personal.patron_turno', 'not null', 'Patrón'),
    ('dia_ciclo', 'smallint', 'not null', 'Día del ciclo (semanal: 1 lunes … 7 domingo)'),
    ('hora_inicio', 'time', '', 'Entrada (vacío = descanso)'),
    ('hora_fin', 'time', '', 'Salida; si es menor o igual a la entrada, termina al día siguiente'),
    ('tipo', "enum:diurno,nocturno,mixto,descanso", 'not null', 'Tipo'),
], ['unique (patron_id, dia_ciclo, hora_inicio)', "check ((tipo = 'descanso') = (hora_inicio is null))"])
tabla('personal', 'cronograma', 2, 'Cronograma de trabajo de un área por un periodo: se genera desde patrones, se ajusta a mano y se publica cuando cumple jornada máxima, descanso semanal y cobertura.', [
    ('nombre', 'varchar(150)', 'not null', 'Nombre, ej. Galpón · noviembre 2026'),
    ('area_id', 'fk:personal.area_responsabilidad', 'not null', 'Área'),
    ('desde', 'date', 'not null', 'Primer día'),
    ('hasta', 'date', 'not null', 'Último día'),
    ('estado', "enum:borrador,publicado,cerrado", "not null default 'borrador'", 'Estado'),
    ('permitir_huecos', 'boolean', 'not null default false', 'Publicar aunque falte cobertura (queda la advertencia)'),
    ('publicado_por', USR, '', 'Quién lo publicó'),
    ('publicado_en', 'timestamptz', '', 'Cuándo'),
], ['check (hasta >= desde)'])
tabla('personal', 'asignacion_patron', 2, 'Qué patrón sigue cada persona dentro del cronograma (con desfase para rotar entre varias personas).', [
    ('cronograma_id', 'fk:personal.cronograma', 'not null', 'Cronograma'),
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('patron_id', 'fk:personal.patron_turno', 'not null', 'Patrón'),
    ('desfase_dias', 'smallint', 'not null default 0', 'En qué día del ciclo empieza (rotación)'),
], ['unique (cronograma_id, empleado_id)'])
tabla('personal', 'requerimiento_cobertura', 2, 'Cuántas personas necesita un área por franja horaria y día (ej. galpón: 1 persona las 24 horas; cabañas: 2 de 8 a 18 los fines de semana).', [
    ('area_id', 'fk:personal.area_responsabilidad', 'not null', 'Área'),
    ('dia_semana', 'smallint', '', '1 lunes … 7 domingo; vacío = todos los días'),
    ('hora_inicio', 'time', 'not null', 'Desde'),
    ('hora_fin', 'time', 'not null', 'Hasta (24:00 se escribe 23:59:59)'),
    ('personas_min', 'smallint', 'not null', 'Personas mínimas'),
], ['check (personas_min > 0)', 'check (dia_semana is null or dia_semana between 1 and 7)'])
tabla('personal', 'disponibilidad', 2, 'Días y horas en que cada persona puede o prefiere trabajar (para armar el cronograma flexible).', [
    ('empleado_id', EMP, 'not null', 'Trabajador'),
    ('dia_semana', 'smallint', 'not null', '1 lunes … 7 domingo'),
    ('hora_inicio', 'time', 'not null', 'Desde'),
    ('hora_fin', 'time', 'not null', 'Hasta'),
    ('preferencia', "enum:disponible,preferido,no_disponible", 'not null', 'Preferencia'),
], ['check (dia_semana between 1 and 7)'])

# ---- agenda: recursos agendables, cabañas, visitas e ingresos y salidas de personas y vehículos
tabla('agenda', 'recurso', 3, 'Lo que se agenda: cabañas, salón, zona de camping, vehículo, equipo, punto de cargue. Cada recurso tiene su calendario sin cruces.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre'),
    ('tipo', 'enum:cabana,salon,zona_camping,vehiculo,equipo,punto_cargue,sala,otro', 'not null', 'Tipo'),
    ('alojamiento_id', 'fk:turismo.alojamiento', 'unique', 'Cabaña de turismo que representa'),
    ('activo_id', 'fk:activos.activo', '', 'Equipo o vehículo que representa'),
    ('zona_id', 'fk:nucleo.zona', '', 'Ubicación'),
    ('capacidad', 'smallint', '', 'Capacidad'),
    ('minutos_preparacion', 'smallint', 'not null default 0', 'Tiempo de alistamiento o limpieza que se bloquea después de cada uso'),
    ('activo', 'boolean', 'not null default true', 'En uso'),
])
tabla('agenda', 'cita', 3, 'Bloque del calendario de un recurso (reserva, limpieza, mantenimiento, uso familiar, entrega). La base impide cruces, contando el alistamiento.', [
    ('recurso_id', 'fk:agenda.recurso', 'not null', 'Recurso'),
    ('titulo', 'varchar(150)', 'not null', 'Título'),
    ('tipo', 'enum:reserva_turistica,limpieza,mantenimiento,uso_familiar,bloqueo,entrega_proveedor,recogida_cliente,capacitacion,auditoria,reunion,otro', 'not null', 'Tipo'),
    ('inicio', 'timestamptz', 'not null', 'Inicio'),
    ('fin', 'timestamptz', 'not null', 'Fin'),
    ('fin_con_preparacion', 'timestamptz', '', 'Fin más el alistamiento del recurso (lo calcula la base)'),
    ('estado', "enum:tentativa,confirmada,cumplida,cancelada", "not null default 'confirmada'", 'Estado'),
    ('reserva_id', 'fk:turismo.reserva', '', 'Reserva de turismo'),
    ('bloqueo_id', 'fk:turismo.bloqueo_calendario', '', 'Bloqueo del calendario'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea asociada (limpieza, mantenimiento)'),
    ('responsable_id', USR, '', 'Responsable'),
    ('notas', 'text', '', 'Notas'),
], ['check (fin > inicio)',
    "exclude using gist (predio_id with =, recurso_id with =, tstzrange(inicio, fin_con_preparacion) with &&) where (estado in ('tentativa', 'confirmada'))"])
tabla('agenda', 'visita', 2, 'Ingreso programado de una persona o un vehículo (proveedor, cliente, turista, técnico, autoridad): se aprueba antes, entrega un pase QR y exige bioseguridad si va al galpón.', [
    ('tipo', 'enum:proveedor,cliente,turista,contratista,tecnico,autoridad,visitante,transportador', 'not null', 'Tipo de visitante'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre de la persona o empresa'),
    ('tercero_id', TER, '', 'Tercero, si está registrado'),
    ('personas', 'smallint', 'not null default 1', 'Número de personas'),
    ('vehiculo_placa', 'varchar(10)', '', 'Placa del vehículo'),
    ('vehiculo_tipo', 'enum:carro,camioneta,camion,moto,tractor,bicicleta', '', 'Tipo de vehículo'),
    ('motivo', 'varchar(200)', 'not null', 'Motivo'),
    ('zona_destino_id', 'fk:nucleo.zona', '', 'Zona a la que va'),
    ('ingreso_programado', 'timestamptz', 'not null', 'Hora de llegada'),
    ('salida_programada', 'timestamptz', 'not null', 'Hora de salida'),
    ('anfitrion_id', USR, 'not null', 'Quién lo recibe'),
    ('requiere_bioseguridad', 'boolean', 'not null default false', 'Entra a una zona de bioseguridad (galpón)'),
    ('contacto_aves_reciente', 'boolean', '', 'Declaró contacto con otras aves en las últimas horas del parámetro cuarentena_aves_horas'),
    ('pase_hash', 'char(64)', 'unique', 'Huella del código QR del pase'),
    ('estado', "enum:solicitada,aprobada,rechazada,en_sitio,salio,no_llego,cancelada", "not null default 'solicitada'", 'Estado'),
    ('aprobada_por', USR, '', 'Quién la aprobó'),
    ('motivo_rechazo', 'varchar(200)', '', 'Motivo del rechazo'),
    ('cita_id', 'fk:agenda.cita', '', 'Cita de cargue o descargue, si aplica'),
], ['check (salida_programada > ingreso_programado)', 'index on (ingreso_programado)'])
tabla('agenda', 'registro_acceso', 2, 'Cada entrada o salida real por la portería (persona o vehículo): con pase, carné QR o NFC, a mano o por lectura de placa. Funciona sin internet y alimenta la jornada.', [
    ('sentido', 'enum:entrada,salida', 'not null', 'Entrada o salida'),
    ('tipo', 'enum:persona,vehiculo', 'not null', 'Qué pasa'),
    ('visita_id', 'fk:agenda.visita', '', 'Visita programada'),
    ('empleado_id', EMP, '', 'Trabajador'),
    ('nombre', 'varchar(150)', '', 'Nombre (si no es visita ni trabajador)'),
    ('placa', 'varchar(10)', '', 'Placa'),
    ('punto', 'varchar(40)', "not null default 'porteria'", 'Punto de control'),
    ('metodo', 'enum:pase_qr,carne_qr,carne_nfc,manual,lectura_placa', 'not null', 'Cómo se identificó'),
    ('desinfeccion', 'boolean', 'not null default false', 'Pasó por desinfección (personas y vehículos que van al galpón)'),
    ('ocurrido_en', 'timestamptz', 'not null default now()', 'Momento'),
    ('registrado_por', USR, '', 'Portero o encargado'),
    ('observacion', 'varchar(200)', '', 'Novedad o motivo de la corrección (los registros no se editan: se corrige con uno nuevo)'),
    ('corrige_id', 'fk:agenda.registro_acceso', '', 'Registro que este corrige (error de digitación)'),
], ['check (visita_id is not null or empleado_id is not null or nombre is not null or placa is not null)', 'index on (ocurrido_en)'])

# ---- formación · gestión educativa (ISO 21001: necesidades, satisfacción, quejas y apelaciones)
tabla('formacion', 'necesidad_formacion', 2, 'Necesidad de formación detectada (por cargo, por una no conformidad, por un cambio o pedida por la persona).', [
    ('origen', 'enum:cargo,no_conformidad,cambio,solicitud,evaluacion_desempeno,norma', 'not null', 'De dónde sale'),
    ('descripcion', 'text', 'not null', 'Qué se necesita aprender'),
    ('tercero_id', TER, '', 'Persona, si es individual'),
    ('competencia_id', 'fk:formacion.competencia', '', 'Competencia'),
    ('curso_id', 'fk:formacion.curso', '', 'Curso que la atiende'),
    ('estado', "enum:abierta,planificada,atendida,descartada", "not null default 'abierta'", 'Estado'),
])
tabla('formacion', 'encuesta', 2, 'Encuesta de satisfacción y de resultados de un curso o sesión (seguimiento y medición de la formación).', [
    ('curso_id', 'fk:formacion.curso', '', 'Curso'),
    ('sesion_id', 'fk:formacion.sesion_presencial', '', 'Sesión'),
    ('tercero_id', TER, '', 'Quién responde (vacío = anónima)'),
    ('satisfaccion', 'smallint', 'not null', 'Satisfacción general 1 a 5'),
    ('utilidad', 'smallint', 'not null', 'Utilidad para el trabajo 1 a 5'),
    ('instructor', 'smallint', '', 'Desempeño del instructor 1 a 5'),
    ('comentario', 'text', '', 'Comentario'),
], ['check (satisfaccion between 1 and 5 and utilidad between 1 and 5 and (instructor is null or instructor between 1 and 5))'])
tabla('formacion', 'queja_apelacion', 2, 'Queja sobre la formación o apelación de una nota o certificado; se responde en plazo y la resuelve alguien distinto del instructor.', [
    ('tipo', 'enum:queja,apelacion', 'not null', 'Tipo'),
    ('tercero_id', TER, 'not null', 'Quién la presenta'),
    ('curso_id', 'fk:formacion.curso', '', 'Curso'),
    ('certificado_id', 'fk:formacion.certificado', '', 'Certificado apelado'),
    ('descripcion', 'text', 'not null', 'Qué pasó'),
    ('presentada_en', 'date', 'not null default current_date', 'Fecha'),
    ('responder_antes', 'date', 'not null', 'Plazo de respuesta'),
    ('estado', "enum:recibida,en_estudio,resuelta,rechazada", "not null default 'recibida'", 'Estado'),
    ('respuesta', 'text', '', 'Respuesta'),
    ('resuelta_por', USR, '', 'Quién resolvió'),
])

# ---- proyectos: dirección de proyectos (PMBOK 8: principios, 7 dominios de desempeño y 5 áreas de enfoque)
tabla('proyectos', 'proyecto', 2, 'Proyecto de la finca (nuevo galpón, sistema solar, cabañas, certificación, piloto de robot) con acta de constitución, enfoque predictivo, adaptativo o híbrido y área de enfoque actual.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código, ej. PRY-GAL-500'),
    ('nombre', 'varchar(200)', 'not null', 'Nombre'),
    ('objetivo', 'text', 'not null', 'Objetivo (resultado y valor esperado)'),
    ('justificacion', 'text', '', 'Por qué (caso de negocio)'),
    ('criterios_exito', 'text', '', 'Cómo se sabrá que salió bien'),
    ('iniciativa_id', 'fk:estrategia.iniciativa', '', 'Iniciativa de negocio que lo origina'),
    ('linea_negocio_id', 'fk:estrategia.linea_negocio', '', 'Línea'),
    ('enfoque', "enum:predictivo,adaptativo,hibrido", "not null default 'hibrido'", 'Enfoque de desarrollo'),
    ('area_enfoque', "enum:inicio,planificacion,ejecucion,monitoreo_control,cierre", "not null default 'inicio'", 'Área de enfoque en que está'),
    ('estado', "enum:propuesto,aprobado,en_curso,suspendido,cerrado,cancelado", "not null default 'propuesto'", 'Estado'),
    ('patrocinador_id', USR, '', 'Patrocinador (quien aprueba y responde por el valor)'),
    ('director_id', USR, '', 'Director del proyecto'),
    ('presupuesto', 'dinero', '', 'Presupuesto al concluir (BAC) de la línea base vigente'),
    ('fuente_fondos', 'enum:utilidades_retenidas,credito,fondo_emprender,aporte_familia,convenio,mixto', '', 'Financiación'),
    ('inicio_plan', 'date', '', 'Inicio planeado'),
    ('fin_plan', 'date', '', 'Fin planeado'),
    ('inicio_real', 'date', '', 'Inicio real'),
    ('fin_real', 'date', '', 'Fin real'),
    ('acta_documento_id', 'fk:documental.documento', '', 'Acta de constitución firmada'),
    ('aprobado_por', USR, '', 'Quién lo aprobó'),
    ('aprobado_en', 'timestamptz', '', 'Cuándo'),
])
tabla('proyectos', 'interesado', 2, 'Interesado del proyecto con su interés, influencia y estrategia de relación (dominio de interesados).', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('tercero_id', TER, '', 'Persona o entidad'),
    ('usuario_id', USR, '', 'Usuario interno'),
    ('nombre', 'varchar(150)', 'not null', 'Nombre o rol'),
    ('rol', 'varchar(80)', '', 'Rol en el proyecto'),
    ('interes', 'smallint', 'not null', 'Interés 1 a 5'),
    ('influencia', 'smallint', 'not null', 'Influencia 1 a 5'),
    ('estrategia', 'varchar(30)', '', 'gestionar_de_cerca, mantener_satisfecho, mantener_informado o monitorear (la calcula la base)'),
    ('expectativas', 'text', '', 'Qué espera'),
], ['check (interes between 1 and 5 and influencia between 1 and 5)'])
tabla('proyectos', 'elemento_edt', 2, 'Estructura de desglose del trabajo (EDT): entregables y paquetes de trabajo con su criterio de aceptación.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('padre_id', 'fk:proyectos.elemento_edt', '', 'Elemento superior'),
    ('codigo', 'varchar(20)', 'not null', 'Código EDT, ej. 1.2.3'),
    ('nombre', 'varchar(200)', 'not null', 'Nombre'),
    ('es_entregable', 'boolean', 'not null default false', 'Es un entregable que se acepta'),
    ('criterio_aceptacion', 'text', '', 'Cómo se acepta'),
    ('estado', "enum:pendiente,en_curso,terminado,aceptado,rechazado", "not null default 'pendiente'", 'Estado'),
    ('aceptado_por', USR, '', 'Quién lo aceptó'),
    ('aceptado_en', 'timestamptz', '', 'Cuándo'),
], ['unique (proyecto_id, codigo)', "check (not es_entregable or criterio_aceptacion is not null)"])
tabla('proyectos', 'iteracion', 2, 'Iteración o sprint para la parte adaptativa del proyecto.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('numero', 'smallint', 'not null', 'Número'),
    ('objetivo', 'text', '', 'Objetivo de la iteración'),
    ('inicio', 'date', 'not null', 'Inicio'),
    ('fin', 'date', 'not null', 'Fin'),
    ('estado', "enum:planeada,en_curso,cerrada", "not null default 'planeada'", 'Estado'),
    ('retrospectiva', 'text', '', 'Qué se aprendió'),
], ['unique (proyecto_id, numero)', 'check (fin >= inicio)'])
tabla('proyectos', 'actividad', 2, 'Actividad del cronograma (o historia de la iteración) con duración, fechas, avance, costo y responsable; la ruta crítica la calcula la base.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('elemento_edt_id', 'fk:proyectos.elemento_edt', '', 'Paquete de trabajo'),
    ('iteracion_id', 'fk:proyectos.iteracion', '', 'Iteración'),
    ('codigo', 'varchar(20)', 'not null', 'Código'),
    ('nombre', 'varchar(200)', 'not null', 'Nombre'),
    ('es_hito', 'boolean', 'not null default false', 'Hito (duración 0)'),
    ('duracion_dias', 'smallint', 'not null', 'Duración en días'),
    ('inicio_temprano', 'smallint', '', 'Día de inicio temprano (CPM, desde el día 0)'),
    ('fin_temprano', 'smallint', '', 'Día de fin temprano'),
    ('inicio_tardio', 'smallint', '', 'Día de inicio tardío'),
    ('fin_tardio', 'smallint', '', 'Día de fin tardío'),
    ('holgura', 'smallint', '', 'Holgura total en días'),
    ('critica', 'boolean', 'not null default false', 'Está en la ruta crítica'),
    ('inicio_plan', 'date', '', 'Inicio planeado'),
    ('fin_plan', 'date', '', 'Fin planeado'),
    ('inicio_real', 'date', '', 'Inicio real'),
    ('fin_real', 'date', '', 'Fin real'),
    ('avance_pct', 'numeric(5,2)', 'not null default 0', 'Avance físico'),
    ('costo_plan', 'dinero', 'not null default 0', 'Costo planeado'),
    ('costo_real', 'dinero', 'not null default 0', 'Costo real'),
    ('responsable_id', EMP, '', 'Responsable'),
    ('area_id', 'fk:personal.area_responsabilidad', '', 'Área de responsabilidad'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea de campo que la ejecuta'),
], ['unique (proyecto_id, codigo)', 'check (avance_pct between 0 and 100)', 'check (duracion_dias >= 0 and (not es_hito or duracion_dias = 0))'])
tabla('proyectos', 'dependencia', 2, 'Relación entre actividades (fin a comienzo, comienzo a comienzo, fin a fin, comienzo a fin) con adelanto o retraso.', [
    ('predecesora_id', 'fk:proyectos.actividad', 'not null', 'Actividad predecesora'),
    ('sucesora_id', 'fk:proyectos.actividad', 'not null', 'Actividad sucesora'),
    ('tipo', "enum:FC,CC,FF,CF", "not null default 'FC'", 'Tipo de relación'),
    ('desfase_dias', 'smallint', 'not null default 0', 'Adelanto (negativo) o retraso (positivo)'),
], ['unique (predecesora_id, sucesora_id)', 'check (predecesora_id <> sucesora_id)'])
tabla('proyectos', 'riesgo', 2, 'Riesgo del proyecto (amenaza u oportunidad) con probabilidad, impacto, respuesta y responsable.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('descripcion', 'text', 'not null', 'Causa, riesgo y efecto'),
    ('tipo', "enum:amenaza,oportunidad", "not null default 'amenaza'", 'Tipo'),
    ('categoria', 'enum:tecnico,clima,sanitario,mercado,financiero,legal,personas,proveedor,seguridad', 'not null', 'Categoría'),
    ('probabilidad', 'smallint', 'not null', '1 a 5'),
    ('impacto', 'smallint', 'not null', '1 a 5'),
    ('severidad', 'smallint generated always as (probabilidad * impacto) stored', '', 'Probabilidad × impacto (1 a 25)'),
    ('respuesta', 'enum:evitar,mitigar,transferir,aceptar,escalar,explotar,mejorar,compartir', '', 'Estrategia de respuesta'),
    ('plan_respuesta', 'text', '', 'Qué se hará'),
    ('disparador', 'varchar(200)', '', 'Señal de que se está materializando'),
    ('responsable_id', USR, '', 'Dueño del riesgo'),
    ('estado', "enum:identificado,en_respuesta,materializado,cerrado", "not null default 'identificado'", 'Estado'),
], ['check (probabilidad between 1 and 5 and impacto between 1 and 5)'])
tabla('proyectos', 'registro', 2, 'Registro de incidentes, supuestos, restricciones, decisiones y lecciones aprendidas del proyecto.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('tipo', 'enum:incidente,supuesto,restriccion,decision,leccion_aprendida', 'not null', 'Tipo'),
    ('descripcion', 'text', 'not null', 'Descripción'),
    ('responsable_id', USR, '', 'Responsable'),
    ('estado', "enum:abierto,cerrado", "not null default 'abierto'", 'Estado'),
    ('fecha', 'date', 'not null default current_date', 'Fecha'),
])
tabla('proyectos', 'solicitud_cambio', 2, 'Solicitud de cambio al alcance, cronograma o costo; la aprueba una persona distinta de quien la pide y, si se aprueba, crea una nueva línea base.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('descripcion', 'text', 'not null', 'Qué cambia y por qué'),
    ('solicitada_por', USR, 'not null', 'Quién la pide'),
    ('impacto_alcance', 'text', '', 'Impacto en el alcance'),
    ('impacto_dias', 'smallint', 'not null default 0', 'Días que agrega o quita'),
    ('impacto_costo', 'dinero', 'not null default 0', 'Costo que agrega o quita'),
    ('estado', "enum:propuesta,aprobada,rechazada", "not null default 'propuesta'", 'Estado'),
    ('decidida_por', USR, '', 'Quién decidió'),
    ('decidida_en', 'timestamptz', '', 'Cuándo'),
])
tabla('proyectos', 'linea_base', 2, 'Línea base aprobada de alcance, cronograma y costo; no se edita: cada cambio aprobado crea una versión nueva.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('version', 'smallint', 'not null', 'Versión'),
    ('presupuesto', 'dinero', 'not null', 'BAC'),
    ('fin_plan', 'date', 'not null', 'Fecha de fin'),
    ('alcance', 'text', 'not null', 'Resumen del alcance'),
    ('solicitud_cambio_id', 'fk:proyectos.solicitud_cambio', '', 'Cambio que la originó'),
    ('aprobada_por', USR, 'not null', 'Quién la aprobó'),
], ['unique (proyecto_id, version)'])
tabla('proyectos', 'medicion_valor_ganado', 2, 'Medición del desempeño en una fecha de corte por valor ganado: PV, EV, AC, CPI, SPI, EAC, ETC y VAC.', [
    ('proyecto_id', 'fk:proyectos.proyecto', 'not null', 'Proyecto'),
    ('fecha_corte', 'date', 'not null', 'Fecha de corte'),
    ('pv', 'dinero', 'not null', 'Valor planificado'),
    ('ev', 'dinero', 'not null', 'Valor ganado'),
    ('ac', 'dinero', 'not null', 'Costo real'),
    ('cpi', 'numeric(8,4)', '', 'Índice de desempeño del costo (EV/AC)'),
    ('spi', 'numeric(8,4)', '', 'Índice de desempeño del cronograma (EV/PV)'),
    ('eac', 'dinero', '', 'Estimación a la conclusión (BAC/CPI)'),
    ('etc', 'dinero', '', 'Estimación hasta concluir (EAC − AC)'),
    ('vac', 'dinero', '', 'Variación a la conclusión (BAC − EAC)'),
], ['unique (proyecto_id, fecha_corte)'])

# ================================================================ v2 · reglas transversales
# Tablas sin predio_id (catálogos compartidos por todas las fincas)
GLOBALES = {'nucleo.usuario', 'nucleo.rol', 'nucleo.permiso', 'nucleo.rol_permiso', 'nucleo.predio', 'nucleo.parametro',
            'nucleo.auditoria', 'produccion.especie', 'produccion.cultivo', 'inventario.unidad_medida',
            'inventario.categoria_producto', 'finanzas.cuenta_contable', 'ia.herramienta', 'redes.politica_canal',
            'produccion.categoria_huevo', 'ambiental.factor_emision',
            'cumplimiento.norma', 'cumplimiento.requisito', 'finanzas.indicador',
            'seguridad.factor_autenticacion', 'seguridad.sesion_usuario', 'seguridad.intento_acceso', 'seguridad.regla_deteccion',
            'seguridad.bloqueo', 'seguridad.senuelo', 'seguridad.alerta_seguridad', 'seguridad.incidente',
            'seguridad.ejecucion_prueba', 'seguridad.copia_seguridad'}
# Tablas que se capturan en la app sin conexión: reciben id_cliente, capturado_en y dispositivo_captura_id
CAPTURA = {'produccion.registro_postura', 'produccion.registro_alimentacion', 'produccion.evento_sanitario', 'produccion.registro_pesaje',
           'produccion.evento_reproductivo', 'produccion.calidad_agua_estanque', 'produccion.labor_cultural', 'produccion.cosecha',
           'riego.evento_riego', 'inventario.movimiento_inventario', 'inventario.lectura_codigo', 'inventario.pesaje',
           'inventario.conteo_detalle', 'comercial.pedido', 'comercial.pago', 'comercial.entrega', 'iot.comando_actuador',
           'produccion.clasificacion_postura', 'produccion.registro_bioseguridad', 'produccion.produccion_abono', 'nucleo.nota_voz',
           'ambiental.registro_ambiental',
           'personal.tarea', 'personal.paso_tarea', 'personal.evidencia_tarea', 'personal.jornada', 'activos.uso_activo',
           'ia.diagnostico_imagen', 'cumplimiento.evaluacion_requisito', 'crm.prospecto', 'crm.interaccion', 'formacion.progreso',
           'formacion.asistencia', 'agenda.registro_acceso', 'formacion.encuesta'}
# Tablas sensibles con auditoría automática por disparador
AUDITADAS = {'nucleo.usuario', 'nucleo.usuario_rol', 'nucleo.rol_permiso', 'nucleo.parametro', 'nucleo.predio', 'terceros.tercero',
             'terceros.consentimiento_datos', 'terceros.cliente', 'terceros.proveedor', 'terceros.empleado', 'inventario.producto',
             'inventario.lote_inventario', 'comercial.lista_precios', 'comercial.precio_producto', 'comercial.propuesta_precio',
             'comercial.pedido', 'comercial.pedido_detalle', 'comercial.factura', 'comercial.pago', 'compras.orden_compra',
             'finanzas.comprobante', 'finanzas.movimiento_contable', 'finanzas.periodo_contable', 'ia.agente', 'ia.herramienta',
             'ia.agente_herramienta', 'ia.solicitud_aprobacion', 'ia.documento_conocimiento', 'ia.regla_conversacion',
             'redes.cuenta_red', 'redes.plantilla_mensaje', 'redes.publicacion', 'riego.valvula', 'iot.regla_automatizacion',
             'iot.actuador', 'nucleo.dispositivo_captura',
             'nucleo.funcionalidad', 'inventario.bloqueo_lote', 'comercial.retiro_lote', 'comercial.permuta', 'compras.documento_soporte',
             'terceros.cliente', 'redes.pieza_audiovisual', 'iot.zona_seguridad', 'iot.credencial_acceso', 'iot.camara',
             'inventario.bodega', 'inventario.vehiculo', 'comercial.pedido_recurrente', 'produccion.categoria_huevo',
             'personal.tarea', 'personal.ausencia', 'personal.matriz_responsabilidad', 'personal.credencial_trabajo', 'personal.jornada',
             'nomina.concepto_nomina', 'nomina.periodo_nomina', 'nomina.novedad', 'nomina.liquidacion', 'nomina.pago_nomina',
             'nomina.documento_nomina_electronica', 'formacion.certificado', 'formacion.habilitacion', 'activos.activo',
             'activos.orden_trabajo', 'documental.documento', 'documental.version_documento', 'cumplimiento.expediente',
             'cumplimiento.evaluacion_requisito', 'cumplimiento.no_conformidad', 'cumplimiento.accion_correctiva', 'seguros.poliza',
             'seguros.aviso_siniestro', 'ia.diagnostico_imagen', 'ia.decision', 'finanzas.presupuesto', 'finanzas.anticipo_proveedor',
             'finanzas.reporte_indicadores', 'iot.mision_robot', 'iot.prioridad_carga', 'nucleo.llave_api', 'nucleo.webhook_suscripcion',
             'seguridad.factor_autenticacion', 'seguridad.regla_deteccion', 'seguridad.bloqueo', 'seguridad.senuelo', 'seguridad.incidente',
             'crm.prospecto', 'crm.formulario_captura', 'estrategia.iniciativa', 'estrategia.evaluacion_proyecto', 'estrategia.reinversion',
             'personal.cronograma', 'personal.turno', 'personal.miembro_area', 'agenda.cita', 'agenda.visita', 'formacion.queja_apelacion',
             'proyectos.proyecto', 'proyectos.elemento_edt', 'proyectos.riesgo', 'proyectos.solicitud_cambio', 'proyectos.linea_base'}
