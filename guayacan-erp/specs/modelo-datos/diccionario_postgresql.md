# Diccionario de datos · PostgreSQL (v5)

Las tablas no repiten los campos comunes; están descritos una sola vez en "Campos comunes". El CSV trae todos los campos de todas las tablas.

## Campos comunes

| Campo | Dónde está | Significado |
| --- | --- | --- |
| `id` | Todas | Identificador interno consecutivo |
| `predio_id` | Tablas marcadas "por finca" | Finca dueña del registro; lo llena la base según la sesión y la seguridad por filas (RLS) impide ver o tocar otras fincas |
| `id_cliente` | Tablas marcadas "captura sin conexión" | UUIDv7 generado en el celular; si el mismo registro llega dos veces, se ignora |
| `capturado_en` | Tablas marcadas "captura sin conexión" | Momento en que se registró en el celular |
| `dispositivo_captura_id` | Tablas marcadas "captura sin conexión" | Equipo con que se capturó (`nucleo.dispositivo_captura`) |
| `creado_en`, `actualizado_en` | Casi todas | Fecha y hora de creación y de última modificación |

## Esquema `nucleo`

Usuarios, roles, permisos, parámetros con vigencia, auditoría, predio y zonas, eventos de integración.

### `nucleo.usuario` · Fase 1 · catálogo compartido · auditada

Persona que entra al sistema (administrador, operario, contador, cliente con cuenta). Reemplaza el usuario de Django (AUTH_USER_MODEL).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre_completo` | varchar(150) | no |  | Nombre y apellidos como se muestran en pantalla |
| `correo` | citext | no |  | Correo con el que inicia sesión; no distingue mayúsculas |
| `telefono` | varchar(20) | sí |  | Celular en formato internacional, ej. +573001234567 |
| `contrasena_hash` | varchar(255) | no |  | Contraseña cifrada con Argon2; nunca se guarda en claro |
| `es_superusuario` | boolean | no |  | Tiene todos los permisos (solo el dueño del sistema) |
| `activo` | boolean | no |  | Si es falso no puede iniciar sesión (se desactiva en vez de borrar) |
| `ultimo_ingreso` | timestamptz | sí |  | Fecha y hora del último inicio de sesión |
| `tercero_id` | bigint | sí | `terceros.tercero` | Persona en el registro de terceros a la que corresponde, si aplica |

### `nucleo.rol` · Fase 1 · catálogo compartido

Conjunto de permisos que se asigna a usuarios o agentes (administrador, operario de granja, contador, vendedor).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(40) | no |  | Código corto en minúscula, ej. administrador, operario_granja |
| `nombre` | varchar(80) | no |  | Nombre visible del rol |
| `descripcion` | text | sí |  | Qué puede hacer quien tiene este rol |

### `nucleo.permiso` · Fase 1 · catálogo compartido

Acción concreta que se puede autorizar, por módulo (ej. comercial.aprobar_precio).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(80) | no |  | Código módulo.accion, ej. comercial.aprobar_precio |
| `nombre` | varchar(120) | no |  | Descripción corta de la acción |
| `modulo` | varchar(40) | no |  | Módulo al que pertenece (esquema) |

### `nucleo.rol_permiso` · Fase 1 · catálogo compartido · auditada

Qué permisos tiene cada rol (relación muchos a muchos).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `rol_id` | bigint | no | `nucleo.rol` | Rol |
| `permiso_id` | bigint | no | `nucleo.permiso` | Permiso concedido al rol |

### `nucleo.usuario_rol` · Fase 1 · por finca · auditada

Qué roles tiene cada usuario en cada finca (un usuario puede trabajar en varias fincas con roles distintos).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `usuario_id` | bigint | no | `nucleo.usuario` | Usuario |
| `rol_id` | bigint | no | `nucleo.rol` | Rol asignado |

### `nucleo.parametro` · Fase 1 · catálogo compartido · auditada

Valores de negocio que cambian con el tiempo (IVA, salario mínimo, tarifa de domicilio, margen mínimo). Nunca van fijos en el código.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `clave` | varchar(80) | no |  | Nombre del parámetro, ej. salario_minimo, iva_general, margen_minimo_huevo |
| `valor` | text | no |  | Valor como texto; se interpreta según tipo_dato |
| `tipo_dato` | text (lista) | no |  | Cómo interpretar el valor · valores: entero, decimal, porcentaje, dinero, texto, booleano, json |
| `vigente_desde` | date | no |  | Primer día en que aplica |
| `vigente_hasta` | date | sí |  | Último día en que aplica; vacío = vigente hoy |
| `descripcion` | text | sí |  | Para qué se usa y de dónde sale (norma, decreto, decisión) |

### `nucleo.auditoria` · Fase 1 · catálogo compartido

Registro inalterable de cada cambio importante: quién (persona o agente), qué, cuándo y cómo estaba antes. Particionada por mes.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `esquema_tabla` | varchar(80) | no |  | Tabla afectada, ej. comercial.precio_producto |
| `registro_id` | bigint | no |  | Id del registro afectado |
| `accion` | text (lista) | no |  | Tipo de acción · valores: crear, actualizar, eliminar, aprobar, rechazar, iniciar_sesion, exportar |
| `datos_antes` | jsonb | sí |  | Valores antes del cambio |
| `datos_despues` | jsonb | sí |  | Valores después del cambio |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Persona que hizo o aprobó la acción |
| `agente_id` | bigint | sí | `ia.agente` | Agente de IA que la propuso o ejecutó, si aplica |
| `direccion_ip` | inet | sí |  | IP de origen |
| `ocurrido_en` | timestamptz | no |  | Momento exacto del cambio |

### `nucleo.evento_salida` · Fase 1 · por finca

Bandeja de salida (patrón outbox): cada hecho de negocio se escribe aquí en la misma transacción y luego se publica a MongoDB, a los agentes y a otros servicios.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo_evento` | varchar(80) | no |  | Nombre del hecho, ej. pedido.confirmado, precio.aprobado |
| `entidad` | varchar(80) | no |  | Tabla de origen |
| `entidad_id` | bigint | no |  | Id del registro de origen |
| `carga` | jsonb | no |  | Datos del evento |
| `estado` | text (lista) | no |  | Si ya se entregó a los consumidores · valores: pendiente, publicado, fallido |
| `intentos` | smallint | no |  | Veces que se intentó publicar |
| `publicado_en` | timestamptz | sí |  | Cuándo se publicó |

### `nucleo.predio` · Fase 1 · catálogo compartido · auditada

Finca o terreno donde opera el sistema (permite replicarlo en otras fincas).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(120) | no |  | Nombre de la finca, ej. El Guayacán de los Malaver |
| `matricula_inmobiliaria` | varchar(40) | sí |  | Número de matrícula del certificado de tradición |
| `propietario` | varchar(150) | sí |  | Titular del predio según el certificado |
| `tenencia` | text (lista) | no |  | Cómo se usa el predio · valores: propio, comodato, arriendo, otro |
| `area_m2` | numeric(12,2) | sí |  | Área total en metros cuadrados |
| `codigo_dane_municipio` | char(5) | sí |  | Código DANE del municipio (Nilo = 25488) |
| `vereda` | varchar(80) | sí |  | Vereda |
| `geometria` | geometry(MultiPolygon, 9377) | sí |  | Linderos en el sistema de coordenadas oficial CTM12 (EPSG 9377) |
| `es_practica` | boolean | no |  | Finca de práctica para el modo aprendiz: datos de ejemplo aislados de la finca real |
| `regimen_tributario` | text (lista) | no |  | Régimen del empleador (lo confirma el contador); define si la nómina electrónica es obligatoria · valores: por_definir, ordinario, simple, no_responsable |
| `empleador_tercero_id` | bigint | sí | `terceros.tercero` | Persona o empresa que figura como empleador |

### `nucleo.zona` · Fase 1 · por finca

Área dentro del predio con un uso (galpón, aprisco, estanque, lote de cultivo, potrero, bodega, ronda hídrica).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código corto, ej. GAL-01, EST-02, LOT-C3 |
| `nombre` | varchar(120) | no |  | Nombre descriptivo |
| `tipo_zona` | text (lista) | no |  | Uso de la zona · valores: galpon, aprisco, estanque, lote_cultivo, potrero, bodega, vivienda, ronda_hidrica, apiario, lombricultivo, biodigestor, otra |
| `area_m2` | numeric(12,2) | sí |  | Área en metros cuadrados |
| `capacidad` | integer | sí |  | Capacidad máxima (aves, animales, plantas o m³ según el tipo) |
| `geometria` | geometry(Polygon, 9377) | sí |  | Polígono de la zona en CTM12 |
| `modelo_3d_url` | varchar(300) | sí |  | Modelo 3D de la zona en el almacén de archivos (gemelo digital, listo para cuando exista el levantamiento) |
| `activa` | boolean | no |  | Si está en uso |

### `nucleo.dispositivo_captura` · Fase 1 · por finca · auditada

Equipo con el que se capturan datos: celulares con la app, lectores de código de barras, básculas e impresoras de etiquetas.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código, ej. CEL-SAMID, BAS-01, LEC-01 |
| `tipo` | text (lista) | no |  | Tipo de equipo · valores: celular, tableta, lector_codigo, bascula, impresora_etiquetas |
| `conexion` | text (lista) | no |  | Cómo se conecta: teclado_hid = el lector escribe como un teclado; red_local = a través de la pasarela de la finca · valores: camara, teclado_hid, bluetooth_ble, bluetooth_serial, usb, red_local |
| `marca_modelo` | varchar(80) | sí |  | Marca y modelo |
| `numero_serie` | varchar(60) | sí |  | Serie del fabricante |
| `capacidad_max_kg` | numeric(10,3) | sí |  | Báscula: peso máximo |
| `division_g` | numeric(8,2) | sí |  | Báscula: resolución en gramos |
| `uso_comercial` | boolean | no |  | Báscula usada para vender por peso: sujeta a verificación metrológica de la SIC |
| `ultima_verificacion` | date | sí |  | Fecha de la última verificación o calibración |
| `proxima_verificacion` | date | sí |  | Fecha en que vence la verificación |
| `certificado_url` | varchar(300) | sí |  | Certificado de verificación o calibración |
| `usuario_asignado_id` | bigint | sí | `nucleo.usuario` | Persona a cargo (celulares) |
| `activo` | boolean | no |  | En uso |

### `nucleo.sincronizacion` · Fase 1 · por finca

Cada sincronización de la app sin conexión: cuántos registros subió, cuántos se rechazaron y por qué.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `dispositivo_captura_id` | bigint | no | `nucleo.dispositivo_captura` | Celular o tableta que sincroniza |
| `usuario_id` | bigint | no | `nucleo.usuario` | Usuario que tenía la sesión |
| `version_app` | varchar(20) | no |  | Versión de la app |
| `iniciada_en` | timestamptz | no |  | Inicio |
| `terminada_en` | timestamptz | sí |  | Fin |
| `registros_recibidos` | integer | no |  | Registros que llegaron |
| `registros_duplicados` | integer | no |  | Ya existían (mismo id_cliente); se ignoran sin error |
| `registros_rechazados` | integer | no |  | No pasaron una regla (ej. dos personas registraron la postura del mismo lote y día) |
| `detalle_rechazos` | jsonb | sí |  | Qué se rechazó y por qué, para resolverlo en la app |

### `nucleo.funcionalidad` · Fase 1 · por finca · auditada

Interruptor de funciones por finca (feature flag): lo que aún no tiene equipo o decisión queda construido y apagado, y se enciende sin desplegar otra versión.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(40) | no |  | Código, ej. venta_credito, permuta, camara_termica, reconocimiento_facial |
| `descripcion` | text | no |  | Qué habilita |
| `fase` | smallint | no |  | Fase del plan en que se prevé |
| `requiere_equipo` | varchar(150) | sí |  | Equipo que hay que comprar antes de activarla, si aplica |
| `activa` | boolean | no |  | Encendida en esta finca |
| `activada_por` | bigint | sí | `nucleo.usuario` | Quién la encendió |
| `activada_en` | timestamptz | sí |  | Cuándo |

### `nucleo.nota_voz` · Fase 2 · por finca · captura sin conexión

Nota de voz grabada en campo sin conexión; se transcribe al sincronizar y el operario confirma lo interpretado antes de crear el registro.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `usuario_id` | bigint | no | `nucleo.usuario` | Quién grabó |
| `audio_url` | varchar(300) | no |  | Audio en el almacén de archivos |
| `duracion_seg` | smallint | sí |  | Duración en segundos |
| `transcripcion` | text | sí |  | Texto obtenido por el servicio de voz a texto |
| `proveedor_voz_texto` | varchar(40) | sí |  | Servicio usado (intercambiable) |
| `interpretacion` | jsonb | sí |  | Registro propuesto, ej. {"tabla":"registro_postura","lote":"AV-2026-01","huevos":87} |
| `estado` | text (lista) | no |  | Solo una nota confirmada por la persona crea el registro · valores: pendiente, interpretada, confirmada, descartada |
| `registro_tabla` | varchar(60) | sí |  | Tabla del registro creado |
| `registro_id` | bigint | sí |  | Id del registro creado |

### `nucleo.llave_api` · Fase 3 · por finca · auditada

Llave de un cliente B2B (HORECA) para la API: guarda solo su huella, con alcances, límite de peticiones y vencimiento. Se enciende con api_b2b.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Cliente dueño de la llave |
| `nombre` | varchar(80) | no |  | Nombre |
| `prefijo` | varchar(12) | no |  | Prefijo visible para identificarla |
| `hash_llave` | char(64) | no |  | Huella SHA-256 de la llave (la llave nunca se guarda) |
| `alcances` | text[] | no |  | Permisos: catalogo:leer, pedidos:leer, pedidos:crear |
| `limite_por_minuto` | smallint | no |  | Límite de peticiones |
| `activa` | boolean | no |  | Encendida |
| `vence_en` | date | no |  | Vencimiento |
| `ultimo_uso` | timestamptz | sí |  | Último uso |

### `nucleo.webhook_suscripcion` · Fase 3 · por finca · auditada

Sistema externo (comprador, logística) que recibe eventos firmados del outbox: pedido confirmado, lote despachado, factura emitida.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(80) | no |  | Nombre |
| `tercero_id` | bigint | sí | `terceros.tercero` | Dueño |
| `url` | varchar(300) | no |  | URL https de destino |
| `eventos` | text[] | no |  | Tipos de evento |
| `secreto_ref` | varchar(120) | no |  | Nombre del secreto para firmar (HMAC); nunca el secreto |
| `activa` | boolean | no |  | Encendida |
| `fallos_seguidos` | smallint | no |  | Fallos seguidos (al llegar a 10 se apaga) |

### `nucleo.webhook_entrega` · Fase 3 · por finca

Intento de entrega de un evento a un webhook, con reintentos.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `suscripcion_id` | bigint | no | `nucleo.webhook_suscripcion` | Suscripción |
| `evento_salida_id` | bigint | no |  | Evento del outbox |
| `estado` | text (lista) | no |  | Estado · valores: pendiente, entregado, fallido |
| `intentos` | smallint | no |  | Intentos |
| `codigo_respuesta` | smallint | sí |  | Código HTTP |
| `proximo_intento` | timestamptz | sí |  | Próximo intento |

## Esquema `terceros`

Personas y empresas con las que se relaciona la finca: clientes, proveedores, empleados y su consentimiento de datos.

### `terceros.tercero` · Fase 1 · por finca · auditada

Toda persona natural o jurídica con la que se relaciona la finca. Un mismo tercero puede ser cliente, proveedor y empleado a la vez.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo_persona` | text (lista) | no |  | Persona natural o empresa · valores: natural, juridica |
| `tipo_documento` | text (lista) | sí |  | Tipo de documento según la DIAN · valores: CC, CE, NIT, PAS, TI, PPT |
| `numero_documento` | varchar(20) | sí |  | Número de documento sin puntos |
| `digito_verificacion` | char(1) | sí |  | Dígito de verificación del NIT |
| `nombres` | varchar(120) | sí |  | Nombres (persona natural) |
| `apellidos` | varchar(120) | sí |  | Apellidos (persona natural) |
| `razon_social` | varchar(200) | sí |  | Nombre de la empresa (persona jurídica) |
| `correo` | citext | sí |  | Correo de contacto |
| `telefono` | varchar(20) | sí |  | Teléfono |
| `whatsapp` | varchar(20) | sí |  | Número de WhatsApp en formato internacional |
| `direccion` | varchar(200) | sí |  | Dirección o indicación rural |
| `codigo_dane_municipio` | char(5) | sí |  | Municipio según DANE |
| `es_cliente` | boolean | no |  | Marca rápida de rol |
| `es_proveedor` | boolean | no |  | Marca rápida de rol |
| `es_empleado` | boolean | no |  | Marca rápida de rol |

### `terceros.consentimiento_datos` · Fase 1 · por finca · auditada

Autorización de tratamiento de datos personales (Ley 1581 de 2012) por finalidad. Sin consentimiento vigente los agentes no personalizan ni envían publicidad.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Titular de los datos |
| `finalidad` | text (lista) | no |  | Para qué se autoriza el uso · valores: atencion_pedidos, publicidad, personalizacion_ofertas, analitica, imagen_redes, biometria_acceso |
| `version_politica` | varchar(20) | no |  | Versión de la política de tratamiento aceptada |
| `otorgado` | boolean | no |  | Verdadero si autorizó, falso si negó |
| `medio` | text (lista) | no |  | Cómo se obtuvo · valores: whatsapp, web, formulario_fisico, verbal_grabado, correo |
| `evidencia_url` | varchar(300) | sí |  | Ubicación de la prueba en el almacén de archivos |
| `otorgado_en` | timestamptz | no |  | Cuándo se dio la respuesta |
| `revocado_en` | timestamptz | sí |  | Cuándo la retiró; vacío = vigente |

### `terceros.cliente` · Fase 1 · por finca · auditada

Datos comerciales del tercero que compra.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Tercero |
| `segmento` | text (lista) | no |  | Tipo de cliente (restaurante y hotel forman el canal HORECA) · valores: hogar, tienda, restaurante, hotel, asadero, carniceria, mayorista, turista, otro |
| `canal_origen` | text (lista) | sí |  | Por dónde llegó · valores: whatsapp, web, redes, referido, mercado_campesino, finca, otro |
| `frecuencia_compra_dias` | smallint | sí |  | Cada cuántos días suele comprar (calculado) |
| `fecha_primera_compra` | date | sí |  | Primera compra |
| `cupo_credito` | numeric(14,2) | no |  | Monto máximo de cartera abierta (solo aplica si la función venta_credito está activa) |
| `dias_plazo` | smallint | no |  | Días de plazo para pagar una factura a crédito |
| `bloqueado_por_mora` | boolean | no |  | Si tiene facturas vencidas sin pagar no puede comprar a crédito |
| `lista_precios_id` | bigint | sí | `comercial.lista_precios` | Lista de precios que le aplica |
| `perfil_interes_ref` | varchar(24) | sí |  | Id del documento en MongoDB perfiles_interes |

### `terceros.proveedor` · Fase 1 · por finca · auditada

Datos de compra del tercero que vende insumos o servicios.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Tercero |
| `categoria` | text (lista) | no |  | Qué suministra · valores: concentrado, animales, semillas, medicamentos, materiales, servicios, transporte, otro |
| `dias_credito` | smallint | no |  | Días de plazo que concede |
| `calificacion` | numeric(3,2) | sí |  | Calificación de 1 a 5 (precio, puntualidad, calidad) |

### `terceros.empleado` · Fase 1 · por finca · auditada

Persona que trabaja en la finca, con su forma de vinculación.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Tercero |
| `cargo` | varchar(80) | no |  | Cargo, ej. operario de granja |
| `tipo_vinculacion` | text (lista) | no |  | Tipo de contrato · valores: termino_fijo, termino_indefinido, jornal, prestacion_servicios, aprendiz |
| `salario_base` | numeric(14,2) | sí |  | Salario mensual o valor del jornal |
| `forma_pago` | text (lista) | no |  | Cómo se le paga; el salario fijo nunca depende de tareas aprobadas · valores: salario, jornal, destajo, mixto |
| `valor_jornal` | numeric(14,2) | sí |  | Valor del jornal, si se le paga por día |
| `ruta_aprendizaje` | varchar(60) | sí |  | Ruta de formación por cargo, ej. operario_galpon |
| `fecha_ingreso` | date | no |  | Inicio |
| `fecha_retiro` | date | sí |  | Fin; vacío = activo |

## Esquema `produccion`

Producción animal (aves, ovinos, caprinos, peces, abejas, lombrices) y agrícola (siembras, labores, cosechas, suelo).

### `produccion.especie` · Fase 1 · catálogo compartido

Catálogo de especies animales que maneja la finca.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. gallina, ovino, caprino, tilapia, abeja, lombriz |
| `nombre_comun` | varchar(80) | no |  | Nombre común |
| `nombre_cientifico` | varchar(120) | sí |  | Nombre científico |
| `grupo` | text (lista) | no |  | Grupo productivo · valores: ave, ovino, caprino, pez, abeja, lombriz, otro |
| `manejo_individual` | boolean | no |  | Si se registra animal por animal (ovinos, caprinos) o solo por lote (aves, peces) |

### `produccion.lote_animal` · Fase 1 · por finca

Grupo de animales que entra junto y se maneja junto (un lote de 100 gallinas, un ciclo de 1.000 alevinos, un rebaño).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. AV-2026-01 |
| `especie_id` | bigint | no | `produccion.especie` | Especie |
| `zona_id` | bigint | no | `nucleo.zona` | Galpón, aprisco o estanque donde está |
| `raza_linea` | varchar(80) | sí |  | Raza o línea genética |
| `proposito` | text (lista) | no |  | Para qué se tiene · valores: postura, engorde, cria, reproduccion, miel, humus |
| `fecha_ingreso` | date | no |  | Fecha de llegada o nacimiento |
| `edad_ingreso_semanas` | smallint | sí |  | Edad al llegar |
| `cantidad_inicial` | integer | no |  | Animales al ingresar |
| `cantidad_actual` | integer | no |  | Animales vivos hoy (se actualiza con mortalidad, ventas y nacimientos) |
| `costo_ingreso` | numeric(14,2) | sí |  | Costo total de compra del lote |
| `estado` | text (lista) | no |  | Activo o cerrado (vendido o descartado) · valores: activo, cerrado |
| `fecha_cierre` | date | sí |  | Fecha de cierre |

### `produccion.animal` · Fase 1 · por finca

Animal identificado individualmente (ovinos y caprinos), con su genealogía.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_animal_id` | bigint | no | `produccion.lote_animal` | Lote o rebaño al que pertenece |
| `identificador` | varchar(20) | no |  | Número de arete o chapeta |
| `sexo` | text (lista) | no |  | Sexo · valores: hembra, macho |
| `fecha_nacimiento` | date | sí |  | Nacimiento |
| `madre_id` | bigint | sí | `produccion.animal` | Madre, si nació en la finca |
| `padre_id` | bigint | sí | `produccion.animal` | Padre, si se conoce |
| `estado` | text (lista) | no |  | Situación actual · valores: activo, vendido, muerto, descartado |

### `produccion.registro_postura` · Fase 1 · por finca · captura sin conexión

Huevos recogidos por día y por lote; las categorías por peso se registran en clasificacion_postura.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_animal_id` | bigint | no | `produccion.lote_animal` | Lote de gallinas |
| `fecha` | date | no |  | Día de recolección |
| `huevos_recogidos` | integer | no |  | Total de huevos recogidos en el día |
| `huevos_rotos` | integer | no |  | Rotos o sucios (no vendibles); la clasificación de los buenos va en clasificacion_postura |
| `registrado_por` | bigint | no | `nucleo.usuario` | Quien registró |

### `produccion.registro_alimentacion` · Fase 1 · por finca · captura sin conexión

Alimento suministrado a un lote, distinguiendo lo comprado de lo producido en la finca (base para medir el ahorro).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_animal_id` | bigint | no | `produccion.lote_animal` | Lote alimentado |
| `fecha` | date | no |  | Día |
| `producto_id` | bigint | no | `inventario.producto` | Alimento (concentrado, maíz, forraje, lombriz) |
| `cantidad_kg` | numeric(10,2) | no |  | Kilogramos suministrados |
| `origen` | text (lista) | no |  | Comprado o producido en la finca · valores: comprado, propio |

### `produccion.evento_sanitario` · Fase 1 · por finca · captura sin conexión

Vacunas, desparasitaciones, tratamientos, revisiones y muertes.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_animal_id` | bigint | no | `produccion.lote_animal` | Lote afectado |
| `animal_id` | bigint | sí | `produccion.animal` | Animal, si el evento es individual |
| `fecha` | date | no |  | Día |
| `tipo` | text (lista) | no |  | Tipo de evento · valores: vacuna, desparasitacion, tratamiento, revision, mortalidad, descarte |
| `producto_id` | bigint | sí | `inventario.producto` | Medicamento o vacuna usada |
| `dosis` | varchar(40) | sí |  | Dosis aplicada |
| `cantidad_afectada` | integer | no |  | Animales tratados o muertos |
| `causa` | varchar(150) | sí |  | Diagnóstico o causa probable |
| `responsable` | varchar(120) | sí |  | Quien lo aplicó (operario, veterinario) |

### `produccion.registro_pesaje` · Fase 1 · por finca · captura sin conexión

Pesos de animales o muestras de un lote (corderos, cabritos, tilapia).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_animal_id` | bigint | no | `produccion.lote_animal` | Lote |
| `animal_id` | bigint | sí | `produccion.animal` | Animal pesado, si es individual |
| `fecha` | date | no |  | Día |
| `animales_muestreados` | integer | no |  | Cuántos se pesaron |
| `peso_promedio_kg` | numeric(8,3) | no |  | Peso promedio en kg |

### `produccion.evento_reproductivo` · Fase 1 · por finca · captura sin conexión

Montas, partos, abortos y destetes de ovinos y caprinos.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `hembra_id` | bigint | no | `produccion.animal` | Hembra |
| `macho_id` | bigint | sí | `produccion.animal` | Macho, en montas |
| `tipo` | text (lista) | no |  | Tipo de evento · valores: monta, parto, aborto, destete |
| `fecha` | date | no |  | Día |
| `crias_vivas` | smallint | sí |  | Crías vivas (partos) |
| `crias_muertas` | smallint | sí |  | Crías muertas (partos) |

### `produccion.calidad_agua_estanque` · Fase 1 · por finca · captura sin conexión

Mediciones del agua de los estanques de peces.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `zona_id` | bigint | no | `nucleo.zona` | Estanque |
| `medido_en` | timestamptz | no |  | Fecha y hora |
| `oxigeno_mg_l` | numeric(5,2) | sí |  | Oxígeno disuelto en mg/L |
| `temperatura_c` | numeric(4,1) | sí |  | Temperatura en °C |
| `ph` | numeric(4,2) | sí |  | pH |
| `amonio_mg_l` | numeric(5,2) | sí |  | Amonio en mg/L |

### `produccion.cultivo` · Fase 1 · catálogo compartido

Catálogo de cultivos (plátano, cacao, aguacate papelillo, maíz, frijol, calabacín, forrajes).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. platano, cacao, maiz |
| `nombre_comun` | varchar(80) | no |  | Nombre común |
| `nombre_cientifico` | varchar(120) | sí |  | Nombre científico |
| `tipo_ciclo` | text (lista) | no |  | Ciclo corto, perenne o forraje · valores: corto, perenne, forraje |
| `dias_a_primera_cosecha` | integer | sí |  | Días desde la siembra hasta la primera cosecha |

### `produccion.siembra` · Fase 1 · por finca

Una siembra en una zona: cuántas plantas se sembraron y cuántas siguen vivas (ej. 5.000 plátanos previstos, 600 vivos).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `zona_id` | bigint | no | `nucleo.zona` | Lote de cultivo |
| `cultivo_id` | bigint | no | `produccion.cultivo` | Cultivo |
| `variedad` | varchar(80) | sí |  | Variedad, ej. papelillo, hartón |
| `fecha_siembra` | date | no |  | Fecha de siembra |
| `plantas_previstas` | integer | sí |  | Plantas planeadas |
| `plantas_sembradas` | integer | sí |  | Plantas sembradas |
| `plantas_vivas` | integer | sí |  | Plantas vivas en el último conteo |
| `semilla_kg` | numeric(10,2) | sí |  | Semilla usada en kg (granos) |
| `area_m2` | numeric(12,2) | sí |  | Área sembrada |
| `fecha_estimada_cosecha` | date | sí |  | Primera cosecha esperada |
| `estado` | text (lista) | no |  | Situación actual · valores: planeada, sembrada, en_produccion, recuperacion, perdida, finalizada |
| `observaciones` | text | sí |  | Notas (ej. pérdidas por fenómeno de El Niño) |

### `produccion.labor_cultural` · Fase 1 · por finca · captura sin conexión

Trabajo hecho a una siembra: encalado, fertilización, deshierbe, control de plagas, poda, resiembra.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `siembra_id` | bigint | no | `produccion.siembra` | Siembra |
| `fecha` | date | no |  | Día |
| `tipo` | text (lista) | no |  | Tipo de labor · valores: encalado, fertilizacion, deshierbe, control_plagas, poda, resiembra, aporque, conteo |
| `producto_id` | bigint | sí | `inventario.producto` | Insumo usado |
| `cantidad` | numeric(10,2) | sí |  | Cantidad de insumo |
| `jornales` | numeric(5,2) | sí |  | Jornales empleados |
| `metodo` | text (lista) | no |  | Cómo se hizo (robot y dron llegan por la interfaz RobotCampo) · valores: manual, mecanico, robot, dron |
| `tarea_id` | bigint | sí | `personal.tarea` | Tarea de la que salió |
| `mision_robot_id` | bigint | sí | `iot.mision_robot` | Misión de robot o dron que la hizo |
| `observaciones` | text | sí |  | Notas |

### `produccion.cosecha` · Fase 1 · por finca · captura sin conexión

Producto cosechado y a dónde se fue (venta, alimento para los animales, semilla o pérdida).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `siembra_id` | bigint | no | `produccion.siembra` | Siembra |
| `fecha` | date | no |  | Día |
| `producto_id` | bigint | no | `inventario.producto` | Producto resultante |
| `cantidad` | numeric(12,2) | no |  | Cantidad |
| `destino` | text (lista) | no |  | Destino · valores: venta, alimento_animal, semilla, autoconsumo, perdida |
| `lote_inventario_id` | bigint | sí | `inventario.lote_inventario` | Lote de inventario creado al entrar a bodega |

### `produccion.analisis_suelo` · Fase 1 · por finca

Resultados de laboratorio del suelo de una zona y la recomendación de encalado.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `zona_id` | bigint | no | `nucleo.zona` | Zona muestreada |
| `fecha_muestreo` | date | no |  | Fecha de la muestra |
| `laboratorio` | varchar(120) | sí |  | Laboratorio |
| `ph` | numeric(4,2) | sí |  | pH |
| `materia_organica_pct` | numeric(5,2) | sí |  | Materia orgánica % |
| `aluminio_cmol_kg` | numeric(6,2) | sí |  | Aluminio intercambiable cmol/kg |
| `resultados` | jsonb | sí |  | Demás elementos (P, K, Ca, Mg...) |
| `recomendacion` | text | sí |  | Recomendación del agrónomo |
| `archivo_url` | varchar(300) | sí |  | PDF del resultado |

### `produccion.categoria_huevo` · Fase 1 · catálogo compartido · auditada

Categorías comerciales del huevo por rango de peso, con la norma de la que salen (verificar NTC 1240 vigente).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(10) | no |  | Código, ej. jumbo, aaa, aa, a, b, c |
| `peso_min_g` | numeric(5,1) | no |  | Peso mínimo en gramos (incluido) |
| `peso_max_g` | numeric(5,1) | sí |  | Peso máximo en gramos (excluido); vacío = sin tope |
| `norma` | varchar(80) | no |  | Norma o fuente de los rangos |
| `vigente_desde` | date | no |  | Desde cuándo aplica |

### `produccion.clasificacion_postura` · Fase 1 · por finca · captura sin conexión

Huevos de un registro de postura por categoría; el método dice si se clasificó con báscula, a mano o con visión artificial.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `registro_postura_id` | bigint | no | `produccion.registro_postura` | Registro de postura |
| `categoria_huevo_id` | bigint | no | `produccion.categoria_huevo` | Categoría |
| `cantidad` | integer | no |  | Huevos de esa categoría |
| `metodo` | text (lista) | no |  | Cómo se clasificó (vision = piloto de fase 4) · valores: peso_bascula, manual, vision |

### `produccion.registro_bioseguridad` · Fase 1 · por finca · captura sin conexión

Registros de bioseguridad e inocuidad que pide el ICA: limpieza, desinfección, plagas, visitas, cambio de cama y agua.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `zona_id` | bigint | no | `nucleo.zona` | Galpón, bodega o zona |
| `fecha` | date | no |  | Día |
| `tipo` | text (lista) | no |  | Tipo de registro · valores: limpieza, desinfeccion, control_plagas, visita, cambio_cama, calidad_agua, vacio_sanitario |
| `producto_id` | bigint | sí | `inventario.producto` | Desinfectante o insumo usado |
| `responsable` | varchar(120) | no |  | Quién lo hizo o quién visitó |
| `observaciones` | text | sí |  | Notas |

### `produccion.produccion_abono` · Fase 1 · por finca · captura sin conexión

Humus y compost producidos por el lombricultivo o la compostera; al entrar a bodega crean un lote vendible.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `origen` | text (lista) | no |  | De dónde sale · valores: lombricultivo, compostera, biodigestor |
| `zona_id` | bigint | sí | `nucleo.zona` | Zona |
| `fecha` | date | no |  | Día de cosecha del abono |
| `kg` | numeric(10,2) | no |  | Kilogramos |
| `lote_inventario_id` | bigint | sí | `inventario.lote_inventario` | Lote creado en inventario |

## Esquema `riego`

Fuentes de agua, tanques, sistemas de riego, válvulas y eventos de riego (manual hoy, automático en la fase IoT).

### `riego.fuente_agua` · Fase 1 · por finca

De dónde sale el agua (nacedero, acueducto veredal, lluvia, pozo) y su permiso.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(80) | no |  | Nombre |
| `tipo` | text (lista) | no |  | Tipo de fuente · valores: nacedero, acueducto_veredal, lluvia, pozo, quebrada |
| `caudal_l_s` | numeric(8,3) | sí |  | Caudal disponible en litros por segundo |
| `requiere_concesion` | boolean | no |  | Si necesita concesión de la CAR |
| `numero_concesion` | varchar(40) | sí |  | Número de resolución de la CAR; vacío = en trámite |
| `concesion_vence` | date | sí |  | Vencimiento de la concesión |
| `apta_consumo_humano` | boolean | no |  | Si el último análisis la declara potable |

### `riego.tanque` · Fase 1 · por finca

Tanques de almacenamiento (hoy: dos de 2.000 litros).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. TQ-01 |
| `capacidad_litros` | integer | no |  | Capacidad |
| `fuente_agua_id` | bigint | sí | `riego.fuente_agua` | Fuente que lo llena |
| `zona_id` | bigint | sí | `nucleo.zona` | Ubicación |
| `sensor_nivel_id` | bigint | sí | `iot.sensor` | Sensor de nivel (fase IoT) |

### `riego.sistema_riego` · Fase 1 · por finca

Red de riego que cubre una o varias zonas (hoy: manguera con aspersores).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(80) | no |  | Nombre |
| `tipo` | text (lista) | no |  | Tecnología · valores: aspersion, goteo, microaspersion, manual |
| `tanque_id` | bigint | sí | `riego.tanque` | Tanque que lo alimenta |
| `caudal_l_min` | numeric(8,2) | sí |  | Caudal nominal |
| `modo_control` | text (lista) | no |  | Cómo se acciona hoy · valores: manual, programado, automatico |

### `riego.valvula` · Fase 1 · por finca · auditada

Cada válvula del sistema (hoy manual en cada aspersor; luego electroválvula).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `sistema_riego_id` | bigint | no | `riego.sistema_riego` | Sistema al que pertenece |
| `codigo` | varchar(20) | no |  | Código, ej. V-03 |
| `zona_id` | bigint | no | `nucleo.zona` | Zona que riega |
| `tipo` | text (lista) | no |  | Manual o eléctrica · valores: manual, electrovalvula |
| `actuador_id` | bigint | sí | `iot.actuador` | Actuador IoT que la abre (fase IoT) |

### `riego.evento_riego` · Fase 1 · por finca · captura sin conexión

Cada riego hecho: cuánto tiempo, cuánta agua y si fue manual o automático.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `valvula_id` | bigint | no | `riego.valvula` | Válvula abierta |
| `inicio` | timestamptz | no |  | Apertura |
| `fin` | timestamptz | sí |  | Cierre |
| `litros_estimados` | numeric(10,1) | sí |  | Litros aplicados (caudal × tiempo) |
| `modo` | text (lista) | no |  | Quién lo accionó · valores: manual, programado, automatico |
| `registrado_por` | bigint | sí | `nucleo.usuario` | Operario, si fue manual |
| `regla_id` | bigint | sí | `iot.regla_automatizacion` | Regla que lo disparó, si fue automático |

## Esquema `inventario`

Catálogo de productos, bodegas, lotes de inventario y kardex de movimientos.

### `inventario.unidad_medida` · Fase 1 · catálogo compartido

Unidades (kg, cubeta, unidad, bulto, litro) y su conversión a la unidad base.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(10) | no |  | Código, ej. kg, cub30, und, bul40 |
| `nombre` | varchar(40) | no |  | Nombre |
| `unidad_base` | varchar(10) | sí |  | Unidad a la que se convierte, ej. und o kg |
| `factor_base` | numeric(12,4) | no |  | Cuántas unidades base contiene (cubeta = 30 und) |

### `inventario.categoria_producto` · Fase 1 · catálogo compartido

Agrupación jerárquica de productos (huevo, carne en pie, granos, insumos, medicamentos).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(80) | no |  | Nombre |
| `padre_id` | bigint | sí | `inventario.categoria_producto` | Categoría superior |

### `inventario.producto` · Fase 1 · por finca · auditada

Todo lo que se vende, se compra o se produce: cubeta de huevo, kg de tilapia, bulto de concentrado.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `sku` | varchar(30) | no |  | Código interno, ej. HUE-AA-30 |
| `nombre` | varchar(150) | no |  | Nombre comercial |
| `descripcion` | text | sí |  | Descripción para el catálogo y para los agentes |
| `categoria_id` | bigint | no | `inventario.categoria_producto` | Categoría |
| `unidad_id` | bigint | no | `inventario.unidad_medida` | Unidad de venta o de control |
| `tipo` | text (lista) | no |  | Naturaleza · valores: producto_terminado, insumo, servicio, activo_menor |
| `se_vende` | boolean | no |  | Aparece en el catálogo |
| `se_compra` | boolean | no |  | Se compra a proveedores |
| `se_produce` | boolean | no |  | Se produce en la finca |
| `perecedero` | boolean | no |  | Tiene vencimiento |
| `vida_util_ambiente_dias` | smallint | sí |  | Días que dura a temperatura ambiente (base para estimar el vencimiento) |
| `vida_util_refrigerado_dias` | smallint | sí |  | Días que dura refrigerado |
| `dias_margen_venta` | smallint | no |  | Días antes del vencimiento en que se deja de vender (fecha límite de venta) |
| `dias_alerta_venta` | smallint | no |  | Días antes de la fecha límite de venta en que se activa la alerta para venderlo primero |
| `metodo_salida` | text (lista) | no |  | Orden de salida: fefo = primero lo que vence primero; fifo = primero lo que entró primero · valores: fefo, fifo |
| `gtin` | varchar(14) | sí |  | Código de barras comercial GS1 (EAN-13 o GTIN-14), si la finca lo obtiene; vacío = solo códigos internos |
| `pesable` | boolean | no |  | Se vende o controla por peso leído en báscula (tilapia, cordero en pie) |
| `peso_nominal_kg` | numeric(10,3) | sí |  | Peso esperado por unidad, para validar lo que marca la báscula (ej. cubeta) |
| `tolerancia_peso_pct` | numeric(5,2) | sí |  | Diferencia máxima aceptada contra el peso nominal antes de alertar |
| `tarifa_iva` | numeric(5,2) | no |  | IVA en %: huevo y carne en pie están excluidos (0) |
| `stock_minimo` | numeric(12,2) | sí |  | Alerta de reposición |
| `activo` | boolean | no |  | Si se sigue usando |

### `inventario.bodega` · Fase 1 · por finca · auditada

Lugar físico donde se guarda inventario.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código |
| `nombre` | varchar(80) | no |  | Nombre |
| `zona_id` | bigint | sí | `nucleo.zona` | Zona del predio |
| `refrigerada` | boolean | no |  | Nevera o cuarto frío; sus lotes usan la vida útil refrigerada |
| `sensor_temperatura_id` | bigint | sí | `iot.sensor` | Sensor que vigila la temperatura (cadena de frío) |
| `temperatura_min_c` | numeric(4,1) | sí |  | Temperatura mínima aceptada en °C |
| `temperatura_max_c` | numeric(4,1) | sí |  | Temperatura máxima aceptada en °C |
| `minutos_tolerancia` | smallint | no |  | Minutos fuera de rango antes de bloquear los lotes |

### `inventario.lote_inventario` · Fase 1 · por finca · auditada

Existencia concreta de un producto con fecha, origen y vencimiento. Sus cantidades solo las cambia el kardex (movimiento_inventario); la salida sigue el orden FEFO: primero lo que vence primero.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `bodega_id` | bigint | no | `inventario.bodega` | Bodega |
| `codigo_lote` | varchar(30) | no |  | Código de trazabilidad, ej. HUE-20261025-GAL01 |
| `origen` | text (lista) | no |  | De dónde salió · valores: produccion, compra, ajuste |
| `origen_tabla` | varchar(60) | sí |  | Tabla de origen (cosecha, registro_postura, orden_compra_detalle) |
| `origen_id` | bigint | sí |  | Id en la tabla de origen |
| `fecha_produccion` | date | no |  | Fecha de producción, postura, cosecha o recepción |
| `condicion_almacenamiento` | text (lista) | no |  | Cómo se guarda; cambia la vida útil usada en la estimación · valores: ambiente, refrigerado |
| `origen_vencimiento` | text (lista) | no |  | estimado = lo calcula el sistema con la vida útil del producto; manual o laboratorio = lo fija una persona · valores: estimado, manual, laboratorio |
| `fecha_vencimiento` | date | sí |  | Fecha en que el producto deja de ser apto (calculada si origen_vencimiento = estimado) |
| `fecha_limite_venta` | date | sí |  | Último día para venderlo: vencimiento menos los días de margen del producto |
| `peso_neto_kg` | numeric(12,3) | sí |  | Peso total leído en báscula al ingresar, si el producto es pesable |
| `cantidad_inicial` | numeric(12,2) | no |  | Cantidad al crearse (genera automáticamente el movimiento de entrada) |
| `cantidad_disponible` | numeric(12,2) | no |  | Libre para vender; solo la cambia el kardex |
| `cantidad_reservada` | numeric(12,2) | no |  | Comprometida en pedidos confirmados; solo la cambia el kardex |
| `costo_unitario` | numeric(14,2) | no |  | Costo por unidad |
| `estado` | text (lista) | no |  | Situación: agotado y vencido los pone el sistema; bloqueado lo pone un bloqueo_lote abierto (cadena de frío, sanidad, retiro) · valores: disponible, agotado, vencido, bloqueado |

### `inventario.movimiento_inventario` · Fase 1 · por finca · captura sin conexión

Kardex: cada entrada, salida, ajuste, traslado o merma, con el documento que lo causó.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_inventario_id` | bigint | no | `inventario.lote_inventario` | Lote movido |
| `tipo` | text (lista) | no |  | Tipo de movimiento; define qué cantidad del lote cambia (ver reglas del kardex) · valores: entrada, reserva, liberacion, salida_venta, consumo_interno, merma, ajuste_entrada, ajuste_salida, traslado_salida, traslado_entrada |
| `cantidad` | numeric(12,2) | no |  | Cantidad (siempre positiva; el tipo da el sentido) |
| `causa_merma` | text (lista) | sí |  | Por qué se perdió, cuando tipo = merma (alimenta el ajuste de la vida útil estimada) · valores: vencido, roto, plaga, calidad, robo, otro |
| `pesaje_id` | bigint | sí | `inventario.pesaje` | Lectura de báscula que respalda la cantidad, si aplica |
| `lectura_codigo_id` | bigint | sí | `inventario.lectura_codigo` | Escaneo de código que originó el movimiento, si aplica |
| `costo_unitario` | numeric(14,2) | no |  | Costo usado |
| `documento_tipo` | varchar(40) | no |  | Documento origen, ej. pedido, cosecha, orden_compra |
| `documento_id` | bigint | no |  | Id del documento |
| `ocurrido_en` | timestamptz | no |  | Momento |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Quién lo registró |

### `inventario.etiqueta` · Fase 1 · por finca

Código de barras o QR impreso para un lote. Interno (Code 128 o QR) o GS1-128 si la finca obtiene códigos GS1.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_inventario_id` | bigint | no | `inventario.lote_inventario` | Lote identificado |
| `codigo` | varchar(80) | no |  | Texto que contiene el código, ej. GY-HUE-20261025-GAL01 o (01)…(10)…(17)… |
| `simbologia` | text (lista) | no |  | Tipo de código impreso · valores: code128, qr, gs1_128, gs1_datamatrix, ean13 |
| `impresora_id` | bigint | sí | `nucleo.dispositivo_captura` | Impresora usada |
| `impresa_en` | timestamptz | sí |  | Cuándo se imprimió |
| `anulada` | boolean | no |  | Etiqueta dañada o reemplazada; si se escanea, se rechaza |

### `inventario.lectura_codigo` · Fase 1 · por finca · captura sin conexión

Cada escaneo de un código: qué se leyó, con qué equipo, para qué y qué resultado tuvo.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo_leido` | varchar(120) | no |  | Texto leído |
| `simbologia` | varchar(20) | sí |  | Tipo detectado |
| `etiqueta_id` | bigint | sí | `inventario.etiqueta` | Etiqueta encontrada, si existe |
| `accion` | text (lista) | no |  | Para qué se escaneó · valores: consulta, entrada, salida, conteo, traslado, despacho |
| `resultado` | text (lista) | no |  | Resultado de la validación · valores: ok, desconocido, anulado, vencido, duplicado, rechazado |
| `usuario_id` | bigint | no | `nucleo.usuario` | Quién escaneó |

### `inventario.pesaje` · Fase 1 · por finca · captura sin conexión

Lectura de una báscula digital, automática o digitada, con tara y estabilidad.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `peso_bruto_kg` | numeric(12,3) | no |  | Peso total en la báscula |
| `tara_kg` | numeric(12,3) | no |  | Peso del recipiente (canastilla, bulto, nevera) |
| `peso_neto_kg` | numeric(12,3) | no |  | Bruto menos tara |
| `estable` | boolean | no |  | La báscula indicó lectura estable; si es falso, no se acepta para vender |
| `origen` | text (lista) | no |  | Leído del equipo o escrito a mano (el digitado queda marcado en informes) · valores: bascula_automatica, digitado |
| `referencia_tabla` | varchar(60) | sí |  | Para qué se pesó, ej. cosecha, registro_pesaje, pedido_detalle |
| `referencia_id` | bigint | sí |  | Id del registro relacionado |
| `usuario_id` | bigint | no | `nucleo.usuario` | Quién pesó |

### `inventario.conteo_fisico` · Fase 1 · por finca

Inventario físico de una bodega: se escanea lo que hay y se compara con el sistema.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `bodega_id` | bigint | no | `inventario.bodega` | Bodega contada |
| `fecha` | date | no |  | Día del conteo |
| `estado` | text (lista) | no |  | Ajustado = las diferencias ya generaron movimientos de ajuste · valores: en_curso, cerrado, ajustado |
| `responsable_id` | bigint | no | `nucleo.usuario` | Responsable |

### `inventario.conteo_detalle` · Fase 1 · por finca · captura sin conexión

Resultado del conteo por lote.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `conteo_fisico_id` | bigint | no | `inventario.conteo_fisico` | Conteo |
| `lote_inventario_id` | bigint | no | `inventario.lote_inventario` | Lote contado |
| `cantidad_sistema` | numeric(12,2) | no |  | Lo que decía el sistema al contar |
| `cantidad_contada` | numeric(12,2) | no |  | Lo encontrado |
| `movimiento_ajuste_id` | bigint | sí | `inventario.movimiento_inventario` | Ajuste generado por la diferencia |

### `inventario.vehiculo` · Fase 2 · por finca · auditada

Vehículo de entregas (camioneta, motocarro) y su registrador de temperatura.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. CAM-01 |
| `tipo` | text (lista) | no |  | Tipo · valores: camioneta, motocarro, moto, otro |
| `placa` | varchar(10) | sí |  | Placa |
| `capacidad_kg` | numeric(10,2) | sí |  | Carga máxima |
| `refrigerado` | boolean | no |  | Tiene nevera o caja térmica |
| `sensor_temperatura_id` | bigint | sí | `iot.sensor` | Registrador de temperatura (guarda sin señal) |
| `temperatura_max_c` | numeric(4,1) | sí |  | Temperatura máxima aceptada |
| `minutos_tolerancia` | smallint | no |  | Minutos fuera de rango antes de bloquear lo que transporta |
| `activo` | boolean | no |  | En uso |

### `inventario.excursion_temperatura` · Fase 2 · por finca

Periodo en que una nevera o un vehículo estuvo fuera de su rango de temperatura; si supera la tolerancia, bloquea los lotes perecederos.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `sensor_id` | bigint | no | `iot.sensor` | Sensor que la detectó |
| `bodega_id` | bigint | sí | `inventario.bodega` | Bodega afectada |
| `vehiculo_id` | bigint | sí | `inventario.vehiculo` | Vehículo afectado |
| `inicio` | timestamptz | no |  | Inicio |
| `fin` | timestamptz | sí |  | Fin; vacío = sigue fuera de rango |
| `temperatura_extrema_c` | numeric(4,1) | no |  | Peor temperatura registrada |
| `minutos_fuera` | integer | no |  | Minutos fuera de rango |
| `lotes_bloqueados` | integer | no |  | Lotes que bloqueó (lo calcula la regla) |
| `estado` | text (lista) | no |  | Situación · valores: abierta, cerrada |

### `inventario.bloqueo_lote` · Fase 2 · por finca · auditada

Bloqueo de un lote y su decisión: lo pone una regla o una persona; liberarlo o descartarlo siempre lo decide una persona.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_inventario_id` | bigint | no | `inventario.lote_inventario` | Lote bloqueado |
| `motivo` | text (lista) | no |  | Por qué · valores: cadena_frio, sanitario, calidad, retiro |
| `origen_tabla` | varchar(60) | sí |  | Qué lo causó, ej. excursion_temperatura, retiro_lote |
| `origen_id` | bigint | sí |  | Id del origen |
| `decision` | text (lista) | no |  | Liberado vuelve a disponible; descartado registra la merma · valores: pendiente, liberado, descartado |
| `decidido_por` | bigint | sí | `nucleo.usuario` | Persona que decidió |
| `decidido_en` | timestamptz | sí |  | Cuándo |
| `observacion` | text | sí |  | Motivo de la decisión |

## Esquema `comercial`

Precios con vigencia, propuestas de precio, pedidos, facturas, pagos y entregas.

### `comercial.lista_precios` · Fase 1 · por finca · auditada

Lista de precios por canal o tipo de cliente (público, tiendas, restaurantes, mayoristas).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. PUBLICO, TIENDAS |
| `nombre` | varchar(80) | no |  | Nombre |
| `activa` | boolean | no |  | En uso |

### `comercial.precio_producto` · Fase 1 · por finca · auditada

Precio de un producto en una lista, con vigencia. Nunca se edita un precio: se cierra el vigente y se crea uno nuevo, así el historial queda completo.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lista_precios_id` | bigint | no | `comercial.lista_precios` | Lista |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `precio_unitario` | numeric(14,2) | no |  | Precio por unidad de venta |
| `incluye_iva` | boolean | no |  | Si el precio ya incluye IVA |
| `vigente_desde` | timestamptz | no |  | Desde cuándo aplica |
| `vigente_hasta` | timestamptz | sí |  | Hasta cuándo; vacío = vigente |
| `propuesta_precio_id` | bigint | sí | `comercial.propuesta_precio` | Propuesta que lo originó, si vino de un agente |
| `aprobado_por` | bigint | no | `nucleo.usuario` | Administrador que lo autorizó |

### `comercial.propuesta_precio` · Fase 1 · por finca · auditada

Cambio de precio sugerido por el agente analista de mercados. Solo se aplica cuando el administrador lo aprueba.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `lista_precios_id` | bigint | no | `comercial.lista_precios` | Lista afectada |
| `precio_actual` | numeric(14,2) | no |  | Precio vigente al proponer |
| `precio_propuesto` | numeric(14,2) | no |  | Precio sugerido |
| `variacion_pct` | numeric(6,2) | no |  | Variación porcentual |
| `justificacion` | text | no |  | Razones en lenguaje claro |
| `evidencia` | jsonb | no |  | Fuentes consultadas (SIPSA, competidores, costos) con fecha y enlace |
| `agente_id` | bigint | sí | `ia.agente` | Agente que la generó |
| `estado` | text (lista) | no |  | Situación · valores: pendiente, aprobada, rechazada, vencida, aplicada |
| `vence_en` | timestamptz | no |  | Si nadie la revisa antes, queda vencida |
| `revisado_por` | bigint | sí | `nucleo.usuario` | Administrador que decidió |
| `revisado_en` | timestamptz | sí |  | Cuándo decidió |
| `comentario_revision` | text | sí |  | Motivo de la decisión |
| `aplicada_en` | timestamptz | sí |  | Cuándo entró en vigencia |

### `comercial.pedido` · Fase 1 · por finca · captura sin conexión · auditada

Solicitud de compra de un cliente por cualquier canal; puede crearla una persona o un agente.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `numero` | varchar(20) | no |  | Consecutivo, ej. PED-000123 |
| `cliente_id` | bigint | no | `terceros.cliente` | Cliente |
| `canal` | text (lista) | no |  | Canal · valores: whatsapp, web, redes, telefono, finca, mercado_campesino |
| `estado` | text (lista) | no |  | Situación · valores: borrador, confirmado, en_preparacion, despachado, entregado, cancelado |
| `forma_pago` | text (lista) | no |  | Crédito exige la función venta_credito activa, cliente sin mora y cupo disponible · valores: contado, credito |
| `pedido_recurrente_id` | bigint | sí | `comercial.pedido_recurrente` | Pedido recurrente que lo generó, si aplica |
| `fecha_entrega_programada` | date | sí |  | Día de entrega acordado |
| `direccion_entrega` | varchar(200) | sí |  | Dirección de entrega |
| `subtotal` | numeric(14,2) | no |  | Suma de líneas sin impuestos |
| `descuento` | numeric(14,2) | no |  | Descuentos |
| `impuestos` | numeric(14,2) | no |  | IVA |
| `valor_domicilio` | numeric(14,2) | no |  | Cobro de entrega |
| `total` | numeric(14,2) | no |  | Total a pagar |
| `conversacion_ref` | varchar(24) | sí |  | Id de la conversación en MongoDB que originó el pedido |
| `creado_por_agente_id` | bigint | sí | `ia.agente` | Agente que lo tomó, si aplica |
| `vendedor_id` | bigint | sí | `nucleo.usuario` | Persona responsable |

### `comercial.pedido_detalle` · Fase 1 · por finca · auditada

Línea del pedido. El precio queda congelado al confirmar: un cambio de precio posterior no la afecta.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `pedido_id` | bigint | no | `comercial.pedido` | Pedido |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `cantidad` | numeric(12,2) | no |  | Cantidad (los lotes reservados quedan en comercial.reserva_lote) |
| `precio_producto_id` | bigint | no | `comercial.precio_producto` | Precio vigente usado |
| `precio_unitario` | numeric(14,2) | no |  | Precio copiado (congelado) al confirmar |
| `descuento` | numeric(14,2) | no |  | Descuento de la línea |
| `tarifa_iva` | numeric(5,2) | no |  | IVA aplicado |
| `total_linea` | numeric(14,2) | no |  | Total de la línea |

### `comercial.factura` · Fase 1 · por finca · auditada

Factura electrónica (o documento equivalente) generada por regla fija, no por la IA, y validada por la DIAN.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `prefijo` | varchar(6) | no |  | Prefijo autorizado por la DIAN |
| `numero` | integer | no |  | Número dentro del rango autorizado |
| `pedido_id` | bigint | sí | `comercial.pedido` | Pedido facturado |
| `cliente_id` | bigint | no | `terceros.cliente` | Cliente |
| `fecha_emision` | timestamptz | no |  | Fecha y hora de emisión |
| `subtotal` | numeric(14,2) | no |  | Base |
| `iva` | numeric(14,2) | no |  | IVA |
| `total` | numeric(14,2) | no |  | Total |
| `forma_pago` | text (lista) | no |  | Forma de pago · valores: contado, credito |
| `fecha_vencimiento` | date | sí |  | Fecha límite de pago (crédito): emisión más los días de plazo del cliente |
| `saldo` | numeric(14,2) | no |  | Lo que falta por pagar; lo mantienen los pagos confirmados y las permutas |
| `cufe` | varchar(96) | sí |  | Código único de factura electrónica |
| `estado_dian` | text (lista) | no |  | Respuesta de la DIAN · valores: pendiente, aceptada, rechazada, no_aplica |
| `xml_url` | varchar(300) | sí |  | XML en el almacén de archivos |
| `pdf_url` | varchar(300) | sí |  | Representación gráfica |

### `comercial.pago` · Fase 1 · por finca · captura sin conexión · auditada

Dinero recibido por un pedido o factura.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `pedido_id` | bigint | sí | `comercial.pedido` | Pedido |
| `factura_id` | bigint | sí | `comercial.factura` | Factura |
| `fecha` | timestamptz | no |  | Momento del pago |
| `valor` | numeric(14,2) | no |  | Valor |
| `medio` | text (lista) | no |  | Medio de pago; compensacion_permuta = saldado con una permuta · valores: efectivo, nequi, daviplata, transferencia, tarjeta, bre_b, pasarela, compensacion_permuta |
| `proveedor_pasarela` | text (lista) | sí |  | Pasarela de pago local, si medio = pasarela (Stripe no opera en Colombia) · valores: wompi, mercado_pago, epayco, payu |
| `id_transaccion_pasarela` | varchar(80) | sí |  | Id de la transacción en la pasarela (llave de idempotencia del webhook) |
| `referencia` | varchar(60) | sí |  | Número de transacción |
| `estado` | text (lista) | no |  | Situación · valores: pendiente, confirmado, reversado |
| `confirmado_por` | bigint | sí | `nucleo.usuario` | Quién verificó el ingreso (un agente nunca confirma pagos) |

### `comercial.entrega` · Fase 1 · por finca · captura sin conexión

Despacho de un pedido.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `pedido_id` | bigint | no | `comercial.pedido` | Pedido |
| `fecha_salida` | timestamptz | sí |  | Salida de la finca |
| `fecha_entrega` | timestamptz | sí |  | Recepción por el cliente |
| `responsable` | varchar(120) | sí |  | Quien entrega |
| `vehiculo_id` | bigint | sí | `inventario.vehiculo` | Vehículo usado (su registrador de temperatura vigila la cadena de frío en ruta) |
| `estado` | text (lista) | no |  | Situación · valores: programada, en_ruta, entregada, fallida |
| `evidencia_url` | varchar(300) | sí |  | Foto o firma |
| `calificacion_cliente` | smallint | sí |  | De 1 a 5 |

### `comercial.reserva_lote` · Fase 1 · por finca

Qué lotes se reservaron para cada línea de pedido, escogidos en orden FEFO; una línea puede tomar de varios lotes.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `pedido_detalle_id` | bigint | no | `comercial.pedido_detalle` | Línea del pedido |
| `lote_inventario_id` | bigint | no | `inventario.lote_inventario` | Lote reservado |
| `cantidad` | numeric(12,2) | no |  | Cantidad tomada de ese lote |
| `estado` | text (lista) | no |  | Situación · valores: reservada, despachada, liberada |

### `comercial.retiro_lote` · Fase 1 · por finca · auditada

Retiro de un lote del mercado (recall): se bloquea el lote y se avisa a cada cliente que lo recibió.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_inventario_id` | bigint | no | `inventario.lote_inventario` | Lote retirado |
| `motivo` | text | no |  | Problema sanitario o de calidad |
| `estado` | text (lista) | no |  | Situación · valores: abierto, clientes_avisados, cerrado |
| `abierto_por` | bigint | no | `nucleo.usuario` | Quién lo abrió |
| `cerrado_en` | timestamptz | sí |  | Cuándo se cerró |

### `comercial.retiro_aviso` · Fase 1 · por finca

Cliente que recibió un lote retirado: cuánto recibió, cuándo se le avisó y cuánto devolvió.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `retiro_lote_id` | bigint | no | `comercial.retiro_lote` | Retiro |
| `cliente_id` | bigint | no | `terceros.cliente` | Cliente |
| `pedido_id` | bigint | no | `comercial.pedido` | Pedido en que lo recibió |
| `cantidad` | numeric(12,2) | no |  | Cantidad recibida de ese lote |
| `avisado_en` | timestamptz | sí |  | Cuándo se le avisó |
| `medio_aviso` | text (lista) | sí |  | Cómo · valores: whatsapp, llamada, visita, correo |
| `cantidad_devuelta` | numeric(12,2) | no |  | Lo que devolvió |

### `comercial.pedido_recurrente` · Fase 2 · por finca · auditada

Pedido que se repite (tienda, restaurante, hotel); cada día la tarea crea en borrador los que tocan para que un vendedor los confirme.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `cliente_id` | bigint | no | `terceros.cliente` | Cliente |
| `frecuencia` | text (lista) | no |  | Cada cuánto · valores: semanal, quincenal, mensual |
| `proxima_fecha` | date | no |  | Próxima entrega |
| `canal` | text (lista) | no |  | Canal con que se registra el pedido · valores: whatsapp, web, redes, telefono, finca, mercado_campesino |
| `forma_pago` | text (lista) | no |  | Forma de pago de los pedidos generados · valores: contado, credito |
| `activo` | boolean | no |  | En uso |

### `comercial.pedido_recurrente_detalle` · Fase 2 · por finca

Productos y cantidades del pedido recurrente.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `pedido_recurrente_id` | bigint | no | `comercial.pedido_recurrente` | Pedido recurrente |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `cantidad` | numeric(12,2) | no |  | Cantidad |

### `comercial.permuta` · Fase 2 · por finca · auditada

Trueque formal: una venta (factura) y una compra (documento soporte) que se compensan; requiere la función permuta activa. El pago con mano de obra no se admite.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `factura_id` | bigint | no | `comercial.factura` | Venta |
| `documento_soporte_id` | bigint | no | `compras.documento_soporte` | Compra |
| `valor_compensado` | numeric(14,2) | no |  | Valor que se cruza |
| `acuerdo` | text | no |  | Qué se intercambió y cómo se valoró |
| `registrado_por` | bigint | no | `nucleo.usuario` | Quién la registró |

### `comercial.huella_trazabilidad` · Fase 1 · por finca

Cadena de huellas SHA-256 de los hechos de trazabilidad de los lotes: cada huella incluye la anterior, así cualquier alteración se detecta. Lista para anclarse en una red blockchain si un comprador lo exige.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `lote_inventario_id` | bigint | no | `inventario.lote_inventario` | Lote |
| `hecho` | text (lista) | no |  | Hecho registrado · valores: lote_creado, despachado, bloqueado, liberado, descartado, retirado |
| `contenido` | jsonb | no |  | Datos del hecho (lote, fechas, cliente, pedido) |
| `hash_anterior` | char(64) | sí |  | Huella anterior de la cadena de la finca |
| `hash` | char(64) | no |  | SHA-256 de la huella anterior más el contenido |
| `anclaje_red` | varchar(40) | sí |  | Red externa donde se ancló (vacío = no anclada) |
| `anclaje_transaccion` | varchar(120) | sí |  | Id de la transacción de anclaje |
| `anclado_en` | timestamptz | sí |  | Cuándo |

## Esquema `compras`

Órdenes de compra, cotizaciones de proveedores y precios de mercado de referencia.

### `compras.orden_compra` · Fase 1 · por finca · auditada

Compra a un proveedor.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `numero` | varchar(20) | no |  | Consecutivo |
| `proveedor_id` | bigint | no | `terceros.proveedor` | Proveedor |
| `fecha` | date | no |  | Fecha |
| `estado` | text (lista) | no |  | Situación · valores: borrador, aprobada, recibida, parcial, anulada |
| `total` | numeric(14,2) | no |  | Total |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |

### `compras.orden_compra_detalle` · Fase 1 · por finca

Línea de la orden de compra.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `orden_compra_id` | bigint | no | `compras.orden_compra` | Orden |
| `producto_id` | bigint | no | `inventario.producto` | Insumo |
| `cantidad` | numeric(12,2) | no |  | Cantidad pedida |
| `cantidad_recibida` | numeric(12,2) | no |  | Cantidad recibida |
| `precio_unitario` | numeric(14,2) | no |  | Precio pactado |

### `compras.cotizacion_proveedor` · Fase 1 · por finca

Precio ofrecido por un proveedor para un insumo, registrado por una persona o por el agente de mercados.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proveedor_id` | bigint | sí | `terceros.proveedor` | Proveedor, si está registrado |
| `nombre_proveedor` | varchar(150) | sí |  | Nombre si aún no es tercero |
| `producto_id` | bigint | no | `inventario.producto` | Insumo |
| `precio_unitario` | numeric(14,2) | no |  | Precio |
| `fecha` | date | no |  | Fecha de la cotización |
| `vigente_hasta` | date | sí |  | Validez |
| `fuente` | text (lista) | no |  | Cómo se obtuvo · valores: visita, telefono, correo, web, agente |
| `fuente_url` | varchar(300) | sí |  | Enlace, si es web |

### `compras.precio_mercado` · Fase 1 · por finca

Precio de referencia de un producto en un mercado (SIPSA-DANE, Corabastos, Fenavi), usado por el agente analista.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `producto_id` | bigint | no | `inventario.producto` | Producto comparable |
| `mercado` | varchar(80) | no |  | Mercado o fuente, ej. Corabastos, SIPSA Girardot |
| `fecha` | date | no |  | Fecha del dato |
| `precio_minimo` | numeric(14,2) | sí |  | Mínimo |
| `precio_maximo` | numeric(14,2) | sí |  | Máximo |
| `precio_promedio` | numeric(14,2) | no |  | Promedio |
| `unidad` | varchar(20) | no |  | Unidad del dato, ej. kg, cubeta |
| `fuente_url` | varchar(300) | sí |  | Enlace |

### `compras.documento_soporte` · Fase 1 · por finca · auditada

Documento soporte electrónico de la DIAN para compras a quien no factura (campesinos, permutas).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proveedor_id` | bigint | no | `terceros.proveedor` | Vendedor |
| `orden_compra_id` | bigint | sí | `compras.orden_compra` | Orden de compra, si existe |
| `prefijo` | varchar(6) | no |  | Prefijo autorizado |
| `numero` | integer | no |  | Número |
| `fecha` | date | no |  | Fecha |
| `descripcion` | text | no |  | Qué se compró |
| `total` | numeric(14,2) | no |  | Valor |
| `cuds` | varchar(96) | sí |  | Código único del documento soporte |
| `estado_dian` | text (lista) | no |  | Respuesta de la DIAN · valores: pendiente, aceptado, rechazado |

## Esquema `finanzas`

Plan de cuentas (PUC), centros de costo, comprobantes y movimientos contables.

### `finanzas.cuenta_contable` · Fase 1 · catálogo compartido

Plan Único de Cuentas (PUC) adaptado a la finca.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(10) | no |  | Código PUC, ej. 413505 |
| `nombre` | varchar(150) | no |  | Nombre |
| `naturaleza` | text (lista) | no |  | Naturaleza · valores: debito, credito |
| `nivel` | smallint | no |  | 1 clase, 2 grupo, 3 cuenta, 4 subcuenta, 5 auxiliar |
| `padre_id` | bigint | sí | `finanzas.cuenta_contable` | Cuenta superior |
| `acepta_movimiento` | boolean | no |  | Solo las auxiliares reciben movimientos |

### `finanzas.centro_costo` · Fase 1 · por finca

Unidad de negocio para medir rentabilidad (avícola, ovino-caprino, piscícola, ciclo corto, perennes, turismo, administración).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(10) | no |  | Código, ej. AVI |
| `nombre` | varchar(80) | no |  | Nombre |

### `finanzas.comprobante` · Fase 1 · por finca · auditada

Documento contable (ingreso, egreso, nota, causación). Lo generan reglas a partir de ventas, compras y nómina; el agente contador solo sugiere.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo · valores: ingreso, egreso, nota_contable, causacion, nomina, ajuste |
| `numero` | varchar(20) | no |  | Consecutivo por tipo |
| `fecha` | date | no |  | Fecha contable |
| `descripcion` | text | no |  | Concepto |
| `origen_tabla` | varchar(60) | sí |  | Documento de negocio que lo generó |
| `origen_id` | bigint | sí |  | Id del documento |
| `estado` | text (lista) | no |  | Situación; solo se contabiliza si débitos = créditos y el periodo está abierto · valores: borrador, contabilizado, anulado |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quien lo contabilizó |
| `contabilizado_en` | timestamptz | sí |  | Momento en que quedó contabilizado (desde ahí sus movimientos no se pueden cambiar) |
| `motivo_anulacion` | text | sí |  | Por qué se anuló |

### `finanzas.movimiento_contable` · Fase 1 · por finca · auditada

Línea débito o crédito de un comprobante.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `comprobante_id` | bigint | no | `finanzas.comprobante` | Comprobante |
| `cuenta_id` | bigint | no | `finanzas.cuenta_contable` | Cuenta |
| `tercero_id` | bigint | sí | `terceros.tercero` | Tercero |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Centro de costo |
| `debito` | numeric(14,2) | no |  | Débito |
| `credito` | numeric(14,2) | no |  | Crédito |
| `detalle` | varchar(200) | sí |  | Detalle |

### `finanzas.periodo_contable` · Fase 1 · por finca · auditada

Mes contable; un comprobante solo se contabiliza o anula si su mes está abierto.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `anio` | smallint | no |  | Año |
| `mes` | smallint | no |  | Mes (1 a 12) |
| `estado` | text (lista) | no |  | Estado · valores: abierto, cerrado |
| `cerrado_por` | bigint | sí | `nucleo.usuario` | Quién lo cerró |
| `cerrado_en` | timestamptz | sí |  | Cuándo |

### `finanzas.clasificacion_costo` · Fase 2 · por finca

Cómo se comporta cada cuenta de costo o gasto: elemento (MD, MOD, CIF, administración, ventas, financiero) y comportamiento (fijo, variable, semivariable, escalonado). Base del costeo variable y de las palancas.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `cuenta_id` | bigint | no | `finanzas.cuenta_contable` | Cuenta |
| `elemento` | text (lista) | no |  | Elemento del costo · valores: material_directo, mano_obra_directa, cif, gasto_administracion, gasto_ventas, gasto_financiero, otro |
| `comportamiento` | text (lista) | no |  | Comportamiento frente al volumen · valores: fijo, variable, semivariable, escalonado |
| `parte_fija_pct` | numeric(5,2) | sí |  | Porcentaje fijo de un costo semivariable |
| `controlable` | boolean | no |  | Lo controla el responsable del centro |
| `es_costo_producto` | boolean | no |  | Costo del producto (va al inventario) o costo del periodo |

### `finanzas.actividad_costo` · Fase 2 · por finca

Actividad para costeo basado en actividades (ABC) con su inductor: horas de máquina, aves-día, jornales, m² regados.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código, ej. ALIMENTAR_AVES |
| `nombre` | varchar(120) | no |  | Actividad |
| `inductor` | varchar(60) | no |  | Inductor de costo, ej. aves_dia, horas_maquina, jornales |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Centro de servicio que la presta |

### `finanzas.asignacion_costo` · Fase 2 · por finca

Reparto mensual de costos indirectos a los centros según el inductor consumido.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `mes` | date | no |  | Mes |
| `actividad_id` | bigint | no | `finanzas.actividad_costo` | Actividad |
| `centro_costo_id` | bigint | no | `finanzas.centro_costo` | Centro que la consume |
| `cantidad_inductor` | numeric(14,2) | no |  | Cantidad del inductor consumida |
| `valor_asignado` | numeric(14,2) | sí |  | Valor asignado (lo calcula la regla) |

### `finanzas.costo_estandar` · Fase 2 · por finca

Costo estándar por unidad de producto (materiales, mano de obra y CIF) para comparar contra el real.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `vigente_desde` | date | no |  | Desde |
| `material_directo` | numeric(14,2) | no |  | MD por unidad |
| `mano_obra_directa` | numeric(14,2) | no |  | MOD por unidad |
| `cif` | numeric(14,2) | no |  | CIF por unidad |
| `costo_variable_unitario` | numeric(14,2) | no |  | Parte variable del costo unitario |

### `finanzas.presupuesto` · Fase 2 · por finca · auditada

Presupuesto maestro del año (operación y financiero), con versión y aprobación; puede ser base cero. Base para el informe al Fondo Emprender.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(150) | no |  | Nombre |
| `anio` | smallint | no |  | Año |
| `version` | smallint | no |  | Versión |
| `base_cero` | boolean | no |  | Cada rubro se justifica desde cero |
| `fuente` | text (lista) | no |  | Fuente de los recursos · valores: propio, fondo_emprender, credito, mixto |
| `estado` | text (lista) | no |  | Estado · valores: borrador, aprobado, cerrado |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién lo aprobó |

### `finanzas.premisa_presupuesto` · Fase 2 · por finca

Premisas del presupuesto: inflación, salario mínimo, precio del concentrado, crecimiento del mercado, política de cartera.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `presupuesto_id` | bigint | no | `finanzas.presupuesto` | Presupuesto |
| `tipo` | text (lista) | no |  | Tipo de premisa · valores: macroeconomica, microeconomica |
| `variable` | varchar(80) | no |  | Variable, ej. inflacion, precio_concentrado, pct_ventas_contado |
| `valor` | numeric(14,4) | no |  | Valor |
| `fuente` | varchar(200) | sí |  | Fuente (DANE, Banco de la República, cotización) |

### `finanzas.presupuesto_detalle` · Fase 2 · por finca

Rubro del presupuesto por mes, centro de costo y cuenta, en la secuencia del presupuesto maestro (ventas, producción, materias primas, mano de obra, CIF, gastos, inversión, financiación, caja).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `presupuesto_id` | bigint | no | `finanzas.presupuesto` | Presupuesto |
| `componente` | text (lista) | no |  | Componente del presupuesto maestro · valores: ventas, produccion, materia_prima, mano_obra, cif, gastos_operacion, inversion, financiacion, flujo_caja |
| `mes` | smallint | no |  | Mes (1 a 12) |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Centro de costo |
| `cuenta_id` | bigint | sí | `finanzas.cuenta_contable` | Cuenta |
| `producto_id` | bigint | sí | `inventario.producto` | Producto (ventas y producción) |
| `cantidad` | numeric(14,2) | sí |  | Unidades |
| `valor` | numeric(14,2) | no |  | Valor |
| `justificacion` | text | sí |  | Justificación (obligatoria en base cero) |

### `finanzas.estado_financiero` · Fase 2 · por finca

Estado financiero generado y congelado (balance, resultados por costeo variable o absorbente, flujo de efectivo directo o indirecto), real o presupuestado.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Estado · valores: balance_general, resultados_absorbente, resultados_variable, flujo_efectivo_directo, flujo_efectivo_indirecto, cambios_patrimonio |
| `desde` | date | no |  | Desde |
| `hasta` | date | no |  | Hasta |
| `presupuestado` | boolean | no |  | Es proforma (del presupuesto) |
| `datos` | jsonb | no |  | Partidas y totales |
| `generado_por` | bigint | sí | `nucleo.usuario` | Quién lo generó |

### `finanzas.indicador` · Fase 2 · catálogo compartido

Catálogo de indicadores financieros y de gestión con su fórmula, meta y semáforo (liquidez, endeudamiento, rentabilidad, rotación, EBITDA, EVA, Altman, palancas, postura por ave…).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(40) | no |  | Código, ej. razon_corriente, rsp, gpo |
| `nombre` | varchar(150) | no |  | Nombre |
| `grupo` | text (lista) | no |  | Grupo · valores: liquidez, endeudamiento, rentabilidad, actividad, valor, riesgo, palanca, produccion, comercial, personal, proyecto |
| `formula` | text | no |  | Fórmula |
| `interpretacion` | text | sí |  | Cómo leerlo |
| `unidad` | text (lista) | no |  | Unidad · valores: veces, porcentaje, pesos, dias, unidades |
| `sentido` | text (lista) | no |  | Qué es mejor · valores: mayor_mejor, menor_mejor, rango |

### `finanzas.valor_indicador` · Fase 2 · por finca

Valor calculado de un indicador en un periodo, con meta y semáforo para el tablero del administrador.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `indicador_id` | bigint | no | `finanzas.indicador` | Indicador |
| `desde` | date | no |  | Desde |
| `hasta` | date | no |  | Hasta |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Línea, si es por línea |
| `valor` | numeric(18,4) | sí |  | Valor |
| `meta` | numeric(18,4) | sí |  | Meta |
| `semaforo` | text (lista) | no |  | Semáforo (sin_meta: hay valor pero no hay meta fijada) · valores: verde, amarillo, rojo, sin_meta, sin_dato |

### `finanzas.anticipo_proveedor` · Fase 2 · por finca · auditada

Pago adelantado a un proveedor: queda como saldo a favor y se descuenta en las compras siguientes; nunca queda negativo. No se reciben recargas de clientes.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proveedor_id` | bigint | no | `terceros.proveedor` | Proveedor |
| `fecha` | date | no |  | Fecha |
| `valor` | numeric(14,2) | no |  | Valor |
| `saldo` | numeric(14,2) | no |  | Saldo por descontar |
| `comprobante_id` | bigint | sí | `finanzas.comprobante` | Comprobante |
| `estado` | text (lista) | no |  | Estado · valores: abierto, aplicado, devuelto |

### `finanzas.aplicacion_anticipo` · Fase 2 · por finca

Descuento de un anticipo en una orden de compra.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `anticipo_id` | bigint | no | `finanzas.anticipo_proveedor` | Anticipo |
| `orden_compra_id` | bigint | no | `compras.orden_compra` | Compra |
| `valor` | numeric(14,2) | no |  | Valor descontado |

### `finanzas.reporte_indicadores` · Fase 3 · por finca · auditada

Informe de indicadores verificables para Finagro, bancos, gremios o certificadores, con autorización del titular y sin costos ni datos personales.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `destinatario` | text (lista) | no |  | A quién va · valores: finagro, banco, gremio, certificador, fondo_emprender, otro |
| `tercero_id` | bigint | sí | `terceros.tercero` | Entidad |
| `desde` | date | no |  | Desde |
| `hasta` | date | no |  | Hasta |
| `contenido` | jsonb | no |  | Indicadores (producción, ventas, cumplimiento) |
| `hash_sha256` | char(64) | no |  | Huella del contenido (verificable) |
| `autorizado_por` | bigint | no | `nucleo.usuario` | Titular que autorizó compartirlo |
| `enviado_en` | timestamptz | sí |  | Envío |

## Esquema `ia`

Agentes, herramientas, aprobaciones, base de conocimiento, recomendaciones, evaluaciones y consumo de IA.

### `ia.agente` · Fase 1 · por finca · auditada

Agente de IA con un rol, sus instrucciones versionadas, su modelo y su nivel de autonomía.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(40) | no |  | Código, ej. asesor_clientes, analista_mercados |
| `nombre` | varchar(80) | no |  | Nombre visible, ej. Asesor virtual |
| `rol` | text | no |  | Qué hace y qué no hace |
| `nivel_autonomia` | text (lista) | no |  | Hasta dónde puede actuar · valores: solo_lectura, propone, ejecuta_con_regla |
| `proveedor_modelo` | varchar(40) | no |  | Proveedor, ej. anthropic |
| `modelo` | varchar(60) | no |  | Modelo, ej. claude-sonnet-5-5 |
| `modelo_respaldo` | varchar(60) | sí |  | Modelo si el principal falla |
| `version_instrucciones` | varchar(20) | no |  | Versión del prompt de sistema vigente |
| `instrucciones` | text | no |  | Prompt de sistema vigente |
| `limite_costo_diario_usd` | numeric(8,2) | sí |  | Tope de gasto por día |
| `activo` | boolean | no |  | Si atiende |

### `ia.herramienta` · Fase 1 · catálogo compartido · auditada

Función del ERP que un agente puede invocar (por MCP o API), con su nivel de riesgo.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(60) | no |  | Código, ej. consultar_catalogo, proponer_precio |
| `descripcion` | text | no |  | Qué hace (es lo que lee el modelo) |
| `tipo` | text (lista) | no |  | Lectura no cambia nada; propuesta crea una solicitud; escritura cambia datos · valores: lectura, propuesta, escritura |
| `requiere_aprobacion` | boolean | no |  | Si cada uso pasa por un humano |
| `esquema_entrada` | jsonb | no |  | JSON Schema de los parámetros |

### `ia.agente_herramienta` · Fase 1 · por finca · auditada

Qué herramientas puede usar cada agente (mínimo privilegio).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `agente_id` | bigint | no | `ia.agente` | Agente |
| `herramienta_id` | bigint | no | `ia.herramienta` | Herramienta |

### `ia.solicitud_aprobacion` · Fase 1 · por finca · auditada

Bandeja del administrador: toda acción que un agente quiere hacer y requiere permiso humano.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `agente_id` | bigint | no | `ia.agente` | Agente que pide |
| `herramienta_id` | bigint | no | `ia.herramienta` | Acción solicitada |
| `entidad` | varchar(60) | no |  | Tabla afectada, ej. comercial.propuesta_precio |
| `entidad_id` | bigint | sí |  | Registro afectado |
| `resumen` | text | no |  | Qué se pide, en una frase |
| `carga` | jsonb | no |  | Parámetros exactos que se ejecutarán |
| `estado` | text (lista) | no |  | Situación · valores: pendiente, aprobada, rechazada, vencida, ejecutada, fallida |
| `vence_en` | timestamptz | no |  | Límite para decidir |
| `resuelto_por` | bigint | sí | `nucleo.usuario` | Quién decidió |
| `resuelto_en` | timestamptz | sí |  | Cuándo |
| `motivo` | text | sí |  | Motivo de la decisión |

### `ia.documento_conocimiento` · Fase 1 · por finca · auditada

Fuente de la base de conocimiento: fichas de producto, políticas, preguntas frecuentes, manuales técnicos, informes.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `titulo` | varchar(200) | no |  | Título |
| `tipo` | text (lista) | no |  | Tipo · valores: ficha_producto, politica, pregunta_frecuente, manual_tecnico, informe, receta, turismo |
| `contenido` | text | no |  | Texto completo |
| `fuente` | varchar(300) | sí |  | Origen (archivo, URL, autor) |
| `version` | smallint | no |  | Versión |
| `vigente` | boolean | no |  | Si los agentes lo usan |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién validó el contenido |

### `ia.fragmento_conocimiento` · Fase 1 · por finca

Trozo de un documento con su vector semántico (pgvector) para que los agentes encuentren la información relevante (RAG).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `documento_id` | bigint | no | `ia.documento_conocimiento` | Documento |
| `orden` | integer | no |  | Posición dentro del documento |
| `texto` | text | no |  | Texto del fragmento |
| `vector` | vector(1024) | no |  | Representación numérica del significado (embedding) |
| `metadatos` | jsonb | sí |  | Producto, tema, vigencia |

### `ia.recomendacion` · Fase 1 · por finca

Plan de acción o mejora continua propuesto por un agente analista, con su seguimiento (ciclo PHVA).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `agente_id` | bigint | no | `ia.agente` | Agente que la propone |
| `tipo` | text (lista) | no |  | Tipo · valores: mejora_continua, comercial, compra, produccion, contenido_redes, riesgo |
| `titulo` | varchar(200) | no |  | Título |
| `descripcion` | text | no |  | Qué hacer y por qué |
| `evidencia` | jsonb | no |  | Datos que la sustentan |
| `indicador` | varchar(120) | sí |  | Indicador que debería mejorar |
| `prioridad` | text (lista) | no |  | Prioridad · valores: alta, media, baja |
| `estado` | text (lista) | no |  | Situación · valores: nueva, aceptada, descartada, en_ejecucion, cumplida |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Responsable |
| `fecha_limite` | date | sí |  | Plazo |
| `resultado` | text | sí |  | Qué pasó al ejecutarla (aprendizaje) |

### `ia.evaluacion_respuesta` · Fase 1 · por finca

Calificación de una respuesta de un agente por el cliente o el administrador; alimenta la mejora de instrucciones y conocimiento.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `agente_id` | bigint | no | `ia.agente` | Agente evaluado |
| `mensaje_ref` | varchar(24) | no |  | Id del mensaje en MongoDB |
| `origen` | text (lista) | no |  | Quién califica · valores: cliente, administrador, evaluacion_automatica |
| `calificacion` | smallint | no |  | De 1 a 5 |
| `motivo` | text (lista) | sí |  | Motivo · valores: correcta, incorrecta, incompleta, tono, demora, otro |
| `comentario` | text | sí |  | Comentario |

### `ia.consumo_ia` · Fase 1 · por finca

Tokens y costo por agente, modelo y día, para controlar el gasto.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `agente_id` | bigint | no | `ia.agente` | Agente |
| `fecha` | date | no |  | Día |
| `proveedor_modelo` | varchar(40) | no |  | Proveedor |
| `modelo` | varchar(60) | no |  | Modelo |
| `solicitudes` | integer | no |  | Llamadas |
| `tokens_entrada` | bigint | no |  | Tokens enviados |
| `tokens_salida` | bigint | no |  | Tokens generados |
| `costo_usd` | numeric(10,4) | no |  | Costo en dólares |

### `ia.regla_conversacion` · Fase 1 · por finca · auditada

Guardia del orquestador: temas permitidos, temas que se rechazan con cortesía y casos que pasan a una persona.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Clase de regla · valores: tema_permitido, tema_fuera_de_alcance, escalar_a_humano, dato_prohibido |
| `descripcion` | text | no |  | Qué cubre, en lenguaje claro |
| `ejemplos` | jsonb | sí |  | Frases de ejemplo para el clasificador |
| `respuesta_plantilla` | text | sí |  | Texto de respuesta (ej. cortesía al rechazar un tema ajeno a la finca) |
| `prioridad_escalamiento` | text (lista) | sí |  | Si escala, con qué prioridad · valores: alta, media, baja |
| `activa` | boolean | no |  | En uso |

### `ia.escalamiento` · Fase 1 · por finca

Conversación pasada a una persona: motivo, quién la atiende y hasta cuándo se puede responder según la ventana del canal.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `conversacion_ref` | varchar(24) | no |  | Conversación en MongoDB |
| `canal` | varchar(20) | no |  | Canal (whatsapp, instagram, ...) |
| `motivo` | text (lista) | no |  | Por qué escaló · valores: solicitud_cliente, queja, fuera_de_alcance, sin_respuesta_conocimiento, pedido_grande, pago, error_agente |
| `prioridad` | text (lista) | no |  | Prioridad · valores: alta, media, baja |
| `asignado_a` | bigint | sí | `nucleo.usuario` | Persona que atiende |
| `estado` | text (lista) | no |  | Situación; vencido = se cerró la ventana sin respuesta · valores: pendiente, en_atencion, resuelto, vencido |
| `responder_antes_de` | timestamptz | no |  | Límite según la ventana del canal (incluye la extensión de agente humano cuando aplica) |
| `atendido_en` | timestamptz | sí |  | Primera respuesta de la persona |

### `ia.modelo_pronostico` · Fase 2 · por finca

Modelo de pronóstico de demanda entrenado; gana el de menor error (necesita al menos 12 meses de ventas).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `algoritmo` | text (lista) | no |  | Algoritmo · valores: base_estacional, promedio_movil, ets, prophet, otro |
| `version` | varchar(20) | no |  | Versión |
| `entrenado_en` | timestamptz | no |  | Cuándo se entrenó |
| `meses_historia` | smallint | no |  | Meses de ventas usados |
| `error_mape` | numeric(6,2) | sí |  | Error porcentual medio en la validación |
| `activo` | boolean | no |  | Modelo en uso para ese producto |

### `ia.pronostico_demanda` · Fase 2 · por finca

Cantidad esperada de venta por producto y periodo, con su rango.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `modelo_pronostico_id` | bigint | no | `ia.modelo_pronostico` | Modelo |
| `producto_id` | bigint | no | `inventario.producto` | Producto |
| `periodo_inicio` | date | no |  | Inicio |
| `periodo_fin` | date | no |  | Fin |
| `cantidad` | numeric(12,2) | no |  | Cantidad esperada |
| `limite_inferior` | numeric(12,2) | sí |  | Rango bajo |
| `limite_superior` | numeric(12,2) | sí |  | Rango alto |

### `ia.diagnostico_imagen` · Fase 2 · por finca · captura sin conexión · auditada

Foto de hoja, fruto o animal analizada por el agente Agrónomo. Es una propuesta: no crea compras ni aplicaciones; la confirma una persona.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `agente_id` | bigint | no | `ia.agente` | Agente |
| `foto_url` | varchar(300) | no |  | Foto |
| `objetivo` | text (lista) | no |  | Qué se fotografió · valores: hoja, fruto, tallo, animal, huevo, otro |
| `siembra_id` | bigint | sí | `produccion.siembra` | Siembra |
| `lote_animal_id` | bigint | sí | `produccion.lote_animal` | Lote |
| `tomada_por` | bigint | no | `nucleo.usuario` | Quién la tomó |
| `diagnostico_propuesto` | varchar(150) | sí |  | Plaga o enfermedad probable |
| `confianza` | numeric(4,3) | sí |  | Confianza del modelo (0 a 1) |
| `resultado` | jsonb | sí |  | Alternativas y fotos parecidas |
| `estado` | text (lista) | no |  | Revisión humana · valores: pendiente, confirmado, corregido, descartado |
| `diagnostico_final` | varchar(150) | sí |  | Lo que decidió el agrónomo o el veterinario |
| `revisado_por` | bigint | sí | `nucleo.usuario` | Quién revisó |
| `revisado_en` | timestamptz | sí |  | Cuándo |

### `ia.escenario` · Fase 2 · por finca

Simulación "qué pasa si" (sube el concentrado 10 %, se pasa de 100 a 500 gallinas, cae la postura).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(150) | no |  | Nombre |
| `supuestos` | jsonb | no |  | Variables y valores supuestos |
| `resultado` | jsonb | sí |  | Resultado (margen, caja, punto de equilibrio) |
| `creado_por` | bigint | no | `nucleo.usuario` | Quién |
| `agente_id` | bigint | sí | `ia.agente` | Agente que lo preparó |

### `ia.decision` · Fase 2 · por finca · auditada

Registro de decisiones: contexto, opciones, evidencia, quién decidió y, después, el resultado. Memoria de la finca.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `titulo` | varchar(200) | no |  | Decisión |
| `contexto` | text | no |  | Situación |
| `opciones` | jsonb | no |  | Opciones evaluadas |
| `evidencia` | jsonb | sí |  | Cifras y documentos |
| `opcion_elegida` | varchar(200) | sí |  | Lo que se decidió |
| `decidido_por` | bigint | sí | `nucleo.usuario` | Quién decidió (persona) |
| `decidido_en` | timestamptz | sí |  | Cuándo |
| `resultado_esperado` | text | sí |  | Qué se espera |
| `revisar_en` | date | sí |  | Cuándo revisar el resultado |
| `resultado_real` | text | sí |  | Qué pasó |
| `recomendacion_id` | bigint | sí | `ia.recomendacion` | Recomendación que la originó |
| `escenario_id` | bigint | sí | `ia.escenario` | Escenario usado |
| `iniciativa_id` | bigint | sí | `estrategia.iniciativa` | Iniciativa de negocio decidida |

## Esquema `redes`

Cuentas de redes sociales y publicaciones con su flujo de aprobación.

### `redes.cuenta_red` · Fase 1 · por finca · auditada

Cuenta de la finca en un canal de mensajería o red social; las credenciales van en el gestor de secretos, no aquí.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `plataforma` | varchar(20) | no | `redes.politica_canal` | Canal (whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina) |
| `nombre_cuenta` | varchar(100) | no |  | Nombre o número |
| `identificador_externo` | varchar(80) | no |  | Id en la plataforma |
| `secreto_ref` | varchar(120) | no |  | Nombre del secreto con el token de acceso |
| `activa` | boolean | no |  | En uso |

### `redes.publicacion` · Fase 2 · por finca · auditada

Contenido para redes: lo redacta el agente de redes y se publica solo con aprobación.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `cuenta_red_id` | bigint | no | `redes.cuenta_red` | Cuenta |
| `texto` | text | no |  | Texto |
| `medios` | jsonb | sí |  | Imágenes o videos (rutas en MinIO) |
| `estado` | text (lista) | no |  | Situación · valores: borrador, propuesta, aprobada, programada, publicada, rechazada |
| `programada_para` | timestamptz | sí |  | Fecha de publicación |
| `publicada_en` | timestamptz | sí |  | Fecha real |
| `id_externo` | varchar(80) | sí |  | Id en la plataforma |
| `agente_id` | bigint | sí | `ia.agente` | Agente que la redactó |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |
| `recomendacion_id` | bigint | sí | `ia.recomendacion` | Recomendación que la motivó |

### `redes.politica_canal` · Fase 1 · catálogo compartido

Reglas de cada canal según su proveedor (Meta, TikTok): ventana para responder, quién inicia, límites y cobro. Se actualiza cuando cambian las políticas.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `plataforma` | varchar(20) | no |  | Código del canal: whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina |
| `ventana_horas` | smallint | sí |  | Horas para responder después del último mensaje del cliente; vacío = sin límite (web propia) |
| `ventana_agente_humano_horas` | smallint | sí |  | Horas extra solo para respuestas de una persona (etiqueta de agente humano de Meta) |
| `ventana_anuncio_horas` | smallint | sí |  | Ventana ampliada si el cliente llegó por un anuncio que abre chat |
| `max_mensajes_por_ventana` | smallint | sí |  | Tope de mensajes de la empresa por ventana (TikTok: 10) |
| `empresa_puede_iniciar` | boolean | no |  | Si la empresa puede escribir primero (WhatsApp solo con plantilla aprobada) |
| `requiere_plantilla_fuera_ventana` | boolean | no |  | Fuera de la ventana solo se envían plantillas aprobadas |
| `cobra_por_mensaje` | boolean | no |  | El proveedor cobra por mensaje enviado |
| `mensajes_servicio_gratis_mes` | integer | sí |  | Mensajes de servicio sin costo al mes (WhatsApp: 1.000 por número) |
| `solo_bot_del_negocio` | boolean | no |  | El bot debe limitarse a temas de la finca; no puede ser un asistente general |
| `disponible` | boolean | no |  | Si el canal está disponible para cuentas registradas en Colombia |
| `fuente_url` | varchar(300) | sí |  | Documento donde se verificó la regla |
| `verificado_en` | date | no |  | Cuándo se verificó |

### `redes.plantilla_mensaje` · Fase 1 · por finca · auditada

Plantilla aprobada por Meta para escribir fuera de la ventana de 24 horas de WhatsApp (confirmaciones, recordatorios, promociones).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `cuenta_red_id` | bigint | no | `redes.cuenta_red` | Cuenta de WhatsApp |
| `nombre` | varchar(80) | no |  | Nombre técnico, ej. pedido_confirmado |
| `categoria` | text (lista) | no |  | Categoría de Meta; define el precio y si exige consentimiento de publicidad · valores: marketing, utility, authentication |
| `idioma` | varchar(10) | no |  | Idioma |
| `cuerpo` | text | no |  | Texto con variables {{1}}, {{2}} |
| `variables` | jsonb | sí |  | Qué dato va en cada variable |
| `estado_meta` | text (lista) | no |  | Estado de revisión en Meta · valores: borrador, enviada, aprobada, rechazada, pausada |
| `id_externo` | varchar(80) | sí |  | Id en Meta |
| `finalidad_requerida` | text (lista) | no |  | Consentimiento que debe tener el cliente para recibirla · valores: atencion_pedidos, publicidad |

### `redes.mensaje_saliente` · Fase 1 · por finca

Registro de control de cada mensaje que la finca envía por un canal: si estaba dentro de la ventana, qué plantilla usó, qué consentimiento lo permitió y cuánto costó.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `cuenta_red_id` | bigint | no | `redes.cuenta_red` | Canal |
| `tercero_id` | bigint | sí | `terceros.tercero` | Destinatario, si está identificado |
| `conversacion_ref` | varchar(24) | sí |  | Conversación en MongoDB |
| `tipo` | text (lista) | no |  | Servicio = respuesta normal dentro de la ventana · valores: servicio, plantilla, respuesta_privada_comentario |
| `plantilla_id` | bigint | sí | `redes.plantilla_mensaje` | Plantilla usada |
| `autor` | text (lista) | no |  | Quién lo generó · valores: agente, humano, sistema |
| `dentro_ventana` | boolean | no |  | Si se envió dentro de la ventana del canal |
| `consentimiento_id` | bigint | sí | `terceros.consentimiento_datos` | Consentimiento que lo autoriza (obligatorio para publicidad) |
| `costo_estimado_usd` | numeric(10,4) | no |  | Costo según la tarifa del canal |
| `estado_entrega` | text (lista) | no |  | Resultado; bloqueado_por_regla = el sistema lo detuvo (fuera de ventana, sin consentimiento) · valores: enviado, entregado, leido, fallido, bloqueado_por_regla |
| `enviado_en` | timestamptz | no |  | Momento |

### `redes.pieza_audiovisual` · Fase 2 · por finca · auditada

Video, time-lapse o foto preparada para redes: la IA propone guion y texto, FFmpeg arma el archivo y una persona aprueba. Si aparecen personas, todas deben tener consentimiento de imagen.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo · valores: video_promocional, timelapse, reel, foto |
| `clips` | jsonb | sí |  | Clips de origen (ids de iot.clip_video o archivos subidos) |
| `guion` | text | sí |  | Guion propuesto |
| `texto_publicacion` | text | sí |  | Texto para la red |
| `musica_ref` | varchar(120) | sí |  | Pista con licencia de uso |
| `archivo_url` | varchar(300) | sí |  | MP4 o imagen final |
| `personas_identificables` | boolean | no |  | Si aparecen personas reconocibles |
| `estado` | text (lista) | no |  | Situación · valores: borrador, propuesta, aprobada, rechazada, publicada |
| `agente_id` | bigint | sí | `ia.agente` | Agente que la propuso |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |
| `publicacion_id` | bigint | sí | `redes.publicacion` | Publicación en la que se usó |

### `redes.pieza_persona` · Fase 2 · por finca

Persona que aparece en una pieza audiovisual y su consentimiento de imagen.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `pieza_audiovisual_id` | bigint | no | `redes.pieza_audiovisual` | Pieza |
| `tercero_id` | bigint | no | `terceros.tercero` | Persona |

## Esquema `turismo`

Alojamientos, planes turísticos y reservas (fase 3).

### `turismo.alojamiento` · Fase 3 · por finca

Cabaña o espacio de hospedaje.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código |
| `nombre` | varchar(80) | no |  | Nombre |
| `capacidad_personas` | smallint | no |  | Huéspedes máximos |
| `zona_id` | bigint | sí | `nucleo.zona` | Ubicación |
| `tarifa_noche` | numeric(14,2) | no |  | Tarifa base por noche |
| `activo` | boolean | no |  | Disponible |

### `turismo.plan_turistico` · Fase 3 · por finca

Experiencia ofrecida (pasadía, recorrido del cacao, ordeño, taller).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código |
| `nombre` | varchar(120) | no |  | Nombre |
| `descripcion` | text | no |  | Qué incluye |
| `duracion_horas` | numeric(4,1) | sí |  | Duración |
| `cupo_maximo` | smallint | sí |  | Personas por grupo |
| `precio_persona` | numeric(14,2) | no |  | Precio por persona |

### `turismo.reserva` · Fase 3 · por finca

Reserva de alojamiento o plan.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código |
| `cliente_id` | bigint | no | `terceros.cliente` | Cliente |
| `alojamiento_id` | bigint | sí | `turismo.alojamiento` | Alojamiento |
| `plan_turistico_id` | bigint | sí | `turismo.plan_turistico` | Plan |
| `fecha_inicio` | date | no |  | Llegada |
| `fecha_fin` | date | no |  | Salida |
| `personas` | smallint | no |  | Número de personas |
| `estado` | text (lista) | no |  | Situación · valores: solicitada, confirmada, pagada, cumplida, cancelada |
| `total` | numeric(14,2) | no |  | Valor |
| `valor_deposito` | numeric(14,2) | no |  | Anticipo pagado para confirmar |
| `checkin_en` | timestamptz | sí |  | Llegada real |
| `checkout_en` | timestamptz | sí |  | Salida real |
| `pedido_id` | bigint | sí | `comercial.pedido` | Pedido de cobro asociado |

### `turismo.bloqueo_calendario` · Fase 3 · por finca

Fechas en que un alojamiento o un plan no está disponible (mantenimiento, uso familiar).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `alojamiento_id` | bigint | sí | `turismo.alojamiento` | Alojamiento |
| `plan_turistico_id` | bigint | sí | `turismo.plan_turistico` | Plan |
| `desde` | date | no |  | Desde |
| `hasta` | date | no |  | Hasta |
| `motivo` | varchar(150) | no |  | Motivo |

## Esquema `iot`

Red local de la finca: dispositivos, sensores, actuadores, reglas, seguridad perimetral y cámaras (fase 4, con diseño listo desde ya).

### `iot.dispositivo` · Fase 4 · por finca

Equipo físico de la red local de la finca (ESP32, PLC, estación meteorológica) o la pasarela que la coordina. Los nodos hablan con la pasarela por MQTT local; la pasarela sincroniza con la nube cuando hay internet.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código |
| `tipo` | text (lista) | no |  | Tipo; la pasarela es el cerebro local que ejecuta las reglas, graba los clips y guarda datos sin internet · valores: esp32, plc, estacion_clima, pasarela, registrador_temperatura, camara, camara_termica, lector_acceso, central_alarma, otro |
| `pasarela_id` | bigint | sí | `iot.dispositivo` | Pasarela a la que reporta este nodo (vacío si es la pasarela) |
| `zona_id` | bigint | sí | `nucleo.zona` | Ubicación |
| `topico_mqtt` | varchar(120) | no |  | Tópico base en el broker local, ej. guayacan/riego/v03 |
| `direccion_red_local` | inet | sí |  | IP fija en la red local de la finca |
| `version_firmware` | varchar(30) | sí |  | Versión del programa instalado |
| `ultima_conexion` | timestamptz | sí |  | Último latido recibido |
| `ultima_sincronizacion_nube` | timestamptz | sí |  | Solo pasarela: última vez que subió datos a la nube |
| `activo` | boolean | no |  | En uso |

### `iot.sensor` · Fase 4 · por finca

Sensor de un dispositivo (humedad de suelo, nivel de tanque, caudal, temperatura, movimiento, puerta, humo, gas).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `dispositivo_id` | bigint | no | `iot.dispositivo` | Dispositivo |
| `codigo` | varchar(30) | no |  | Código |
| `magnitud` | text (lista) | no |  | Qué mide o detecta · valores: humedad_suelo, nivel_tanque, caudal, temperatura, humedad_aire, lluvia, oxigeno_agua, ph, movimiento, puerta, rotura_vidrio, humo, gas, amoniaco, presencia_termica |
| `unidad` | varchar(10) | no |  | Unidad, ej. %, cm, L/min |
| `valor_minimo_alerta` | numeric(10,3) | sí |  | Alerta por debajo |
| `valor_maximo_alerta` | numeric(10,3) | sí |  | Alerta por encima |

### `iot.actuador` · Fase 4 · por finca · auditada

Elemento que el sistema puede accionar (electroválvula, bomba, relé, sirena, reflector, cerradura, cortina, extractor).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `dispositivo_id` | bigint | no | `iot.dispositivo` | Dispositivo |
| `codigo` | varchar(30) | no |  | Código |
| `tipo` | text (lista) | no |  | Tipo · valores: electrovalvula, bomba, rele, motor, sirena, reflector, cerradura, cortina, extractor |
| `zona_seguridad_id` | bigint | sí | `iot.zona_seguridad` | Zona de seguridad que protege (sirenas, cerraduras, reflectores) |
| `modo_falla` | text (lista) | no |  | Qué hace si se va la energía: una cerradura en un paso de personas debe abrir sin energía · valores: cierra_sin_energia, abre_sin_energia, mantiene |
| `estado_actual` | text (lista) | no |  | Último estado reportado · valores: abierto, cerrado, encendido, apagado, desconocido |

### `iot.lectura` · Fase 4 · por finca

Medición de un sensor, particionada por mes (o hipertabla si se usa TimescaleDB); sin columnas de auditoría por volumen. La pasarela guarda las lecturas mientras no hay internet y las sube después.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `sensor_id` | bigint | no | `iot.sensor` | Sensor |
| `medido_en` | timestamptz | no |  | Momento de la medición (reloj de la pasarela) |
| `recibido_en` | timestamptz | no |  | Momento en que llegó a la nube; la diferencia muestra el tiempo sin conexión |
| `valor` | double precision | no |  | Valor medido |

### `iot.regla_automatizacion` · Fase 4 · por finca · auditada

Regla determinista que acciona un actuador (ej. abrir V-03 si humedad < 30 % y tanque > 40 %). Se ejecuta en la pasarela local, así funciona sin internet. La IA puede sugerir reglas pero no activarlas.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(120) | no |  | Nombre |
| `condicion` | jsonb | no |  | Condición sobre sensores, horario y clima |
| `actuador_id` | bigint | no | `iot.actuador` | Actuador |
| `accion` | text (lista) | no |  | Acción · valores: abrir, cerrar, encender, apagar |
| `duracion_max_min` | smallint | no |  | Tiempo máximo de seguridad; el nodo ESP32 también lo aplica por su cuenta |
| `ejecuta_en` | text (lista) | no |  | Dónde corre la regla; la nube solo para reglas no críticas · valores: pasarela_local, nodo, nube |
| `version` | integer | no |  | Versión; sube con cada cambio |
| `desplegada_version` | integer | sí |  | Versión que confirmó tener la pasarela; distinta de version = cambio pendiente de bajar |
| `activa` | boolean | no |  | Las reglas nacen inactivas hasta que un humano las activa |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién la activó |

### `iot.comando_actuador` · Fase 4 · por finca · captura sin conexión

Orden manual o automática a un actuador (abrir o cerrar una válvula), con su resultado. Funciona desde la red local aunque no haya internet.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `actuador_id` | bigint | no | `iot.actuador` | Actuador |
| `accion` | text (lista) | no |  | Acción · valores: abrir, cerrar, encender, apagar |
| `origen` | text (lista) | no |  | De dónde salió la orden · valores: app_nube, app_red_local, regla, boton_fisico |
| `regla_id` | bigint | sí | `iot.regla_automatizacion` | Regla que la emitió, si aplica |
| `solicitado_por` | bigint | sí | `nucleo.usuario` | Persona que la pidió, si aplica |
| `duracion_max_min` | smallint | no |  | Tiempo máximo antes de cerrar solo |
| `estado` | text (lista) | no |  | Resultado · valores: pendiente, enviado, ejecutado, fallido, expirado |
| `expira_en` | timestamptz | no |  | Si no se ejecuta antes, se descarta (evita que una orden vieja se ejecute al volver la conexión) |
| `ejecutado_en` | timestamptz | sí |  | Confirmación del nodo |

### `iot.zona_seguridad` · Fase 4 · por finca · auditada

Área vigilada (perímetro, galpón, bodega, acceso) con su estado de alarma; las reglas corren en la pasarela local.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `zona_id` | bigint | sí | `nucleo.zona` | Zona del predio |
| `codigo` | varchar(20) | no |  | Código, ej. SEG-BOD-01 |
| `nombre` | varchar(80) | no |  | Nombre |
| `tipo` | text (lista) | no |  | Tipo · valores: perimetro, acceso, galpon, bodega, vivienda, otra |
| `paso_personas` | boolean | no |  | Si por sus puertas salen personas: sus cerraduras deben abrir sin energía |
| `bioseguridad` | boolean | no |  | Exige registro de visita y desinfección para entrar (galpones) |
| `estado_alarma` | text (lista) | no |  | Estado actual; solo cambia con iot.cambiar_estado_alarma · valores: desarmado, armado, noche, mantenimiento |

### `iot.cambio_estado_alarma` · Fase 4 · por finca

Historial de cambios de estado de la alarma (solo inserción).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `zona_seguridad_id` | bigint | no | `iot.zona_seguridad` | Zona |
| `estado_anterior` | varchar(20) | no |  | Estado antes |
| `estado_nuevo` | varchar(20) | no |  | Estado después |
| `origen` | text (lista) | no |  | De dónde salió el cambio · valores: app_nube, app_red_local, teclado, horario, regla |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Persona, si aplica |
| `ocurrido_en` | timestamptz | no |  | Momento |

### `iot.credencial_acceso` · Fase 4 · por finca · auditada

Credencial para abrir una puerta: PIN, tarjeta RFID o rostro. El rostro exige autorización expresa de biometría y su plantilla solo vive cifrada en la pasarela local, nunca en la nube.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Persona autorizada |
| `zona_seguridad_id` | bigint | sí | `iot.zona_seguridad` | Zona a la que da acceso; vacío = todas |
| `metodo` | text (lista) | no |  | Método · valores: pin, rfid, facial |
| `referencia_hash` | varchar(128) | sí |  | Hash del PIN o del número de tarjeta (nunca el valor en claro) |
| `consentimiento_id` | bigint | sí | `terceros.consentimiento_datos` | Autorización de biometría (obligatoria si el método es facial) |
| `vigente_desde` | date | no |  | Desde |
| `vigente_hasta` | date | sí |  | Hasta |
| `activa` | boolean | no |  | En uso |

### `iot.camara` · Fase 4 · por finca · auditada

Cámara de la finca: graba en la pasarela local por movimiento y sube solo clips elegidos.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `dispositivo_id` | bigint | no | `iot.dispositivo` | Dispositivo |
| `zona_id` | bigint | sí | `nucleo.zona` | Ubicación |
| `zona_seguridad_id` | bigint | sí | `iot.zona_seguridad` | Zona de seguridad que vigila |
| `tipo` | text (lista) | no |  | Tipo · valores: ip_rtsp, termica, timelapse |
| `graba_por_movimiento` | boolean | no |  | Graba solo cuando hay movimiento (ahorra energía y almacenamiento) |
| `intervalo_timelapse_min` | smallint | sí |  | Minutos entre fotos de time-lapse |
| `retencion_dias` | smallint | no |  | Días que se guardan los clips de seguridad antes de borrarse |
| `aviso_visible` | boolean | no |  | Hay aviso de zona vigilada (Ley 1581) |
| `stream_secreto_ref` | varchar(120) | sí |  | Nombre del secreto con la URL y la clave del video |
| `activa` | boolean | no |  | En uso |

### `iot.evento_seguridad` · Fase 4 · por finca

Hecho de seguridad detectado (intrusión, puerta, humo, gas, acceso): lo publica la pasarela, aunque no haya internet, y queda para su atención (solo inserción salvo la atención).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `zona_seguridad_id` | bigint | no | `iot.zona_seguridad` | Zona |
| `tipo` | text (lista) | no |  | Qué pasó · valores: intrusion, puerta_abierta, humo, gas, amoniaco, temperatura, sabotaje, falla_energia, acceso_concedido, acceso_denegado |
| `detector` | text (lista) | no |  | Qué lo detectó: las reglas usan el hecho, no el tipo de sensor (así una cámara térmica entra sin cambiar reglas) · valores: pir, magnetico, vidrio, camara, camara_termica, sensor_gas, lector_acceso, manual |
| `sensor_id` | bigint | sí | `iot.sensor` | Sensor |
| `camara_id` | bigint | sí | `iot.camara` | Cámara |
| `credencial_id` | bigint | sí | `iot.credencial_acceso` | Credencial usada (accesos) |
| `severidad` | text (lista) | no |  | Severidad · valores: informativa, media, alta, critica |
| `estado_alarma` | varchar(20) | no |  | Estado de la alarma cuando ocurrió |
| `acciones` | jsonb | sí |  | Lo que hizo la pasarela: sirena, reflectores, extractor, aviso push o SMS |
| `ocurrido_en` | timestamptz | no |  | Momento (reloj de la pasarela) |
| `atendido_por` | bigint | sí | `nucleo.usuario` | Quién lo atendió |
| `atendido_en` | timestamptz | sí |  | Cuándo |
| `nota_atencion` | text | sí |  | Qué se encontró |

### `iot.clip_video` · Fase 4 · por finca

Clip grabado por una cámara: los de seguridad se borran al vencer su retención; los marcados para redes pasan a una pieza audiovisual.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `camara_id` | bigint | no | `iot.camara` | Cámara |
| `inicio` | timestamptz | no |  | Inicio |
| `fin` | timestamptz | no |  | Fin |
| `motivo` | text (lista) | no |  | Por qué se grabó · valores: movimiento, evento_seguridad, timelapse, manual |
| `evento_seguridad_id` | bigint | sí | `iot.evento_seguridad` | Evento asociado |
| `ubicacion` | text (lista) | no |  | Dónde está guardado · valores: pasarela, nube |
| `archivo_url` | varchar(300) | no |  | Ruta del archivo |
| `para_redes` | boolean | no |  | Elegido para contenido de redes (se conserva) |
| `retener_hasta` | date | no |  | Fecha de borrado automático |
| `borrado_en` | timestamptz | sí |  | Cuándo se borró el archivo |

### `iot.mision_robot` · Fase 4 · por finca · auditada

Misión de un dron de monitoreo o de un robot de campo en piloto: una persona la aprueba; el robot opera solo en zonas sin personas y con parada de emergencia probada.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `activo_id` | bigint | no | `activos.activo` | Dron o robot |
| `tipo` | text (lista) | no |  | Tipo · valores: dron_monitoreo, robot_deshierbe, robot_monitoreo |
| `zona_id` | bigint | no | `nucleo.zona` | Zona |
| `estado` | text (lista) | no |  | Estado · valores: propuesta, aprobada, en_curso, terminada, abortada |
| `aprobada_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |
| `piloto_id` | bigint | sí | `terceros.tercero` | Piloto certificado (dron) |
| `poliza_id` | bigint | sí | `seguros.poliza` | Póliza de responsabilidad civil (dron) |
| `altura_max_m` | numeric(5,1) | sí |  | Altura máxima (RAC 100: hasta 122 m) |
| `zona_sin_personas` | boolean | no |  | Se confirmó que no hay personas en la zona |
| `parada_emergencia_probada` | boolean | no |  | Se probó la parada de emergencia |
| `inicio` | timestamptz | sí |  | Inicio |
| `fin` | timestamptz | sí |  | Fin |
| `resultado` | jsonb | sí |  | Fotos, conteos y lecturas devueltas |

### `iot.prioridad_carga` · Fase 4 · por finca · auditada

Prioridad de cada carga eléctrica: con batería baja se cortan primero las no esenciales; alarma, nevera y agua de animales van primero.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `actuador_id` | bigint | no | `iot.actuador` | Carga (relé) |
| `prioridad` | smallint | no |  | 1 = crítica … 5 = prescindible |
| `esencial` | boolean | no |  | Nunca se corta automáticamente |
| `corte_bateria_pct` | smallint | sí |  | Porcentaje de batería bajo el cual se corta |

## Esquema `ambiental`

Mediciones ambientales (energía solar, biogás, compost, agua) y factores de emisión con su fuente.

### `ambiental.factor_emision` · Fase 2 · catálogo compartido

Factor para convertir una medición en CO₂ equivalente, con su fuente; sin fuente no se publica ninguna cifra.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `magnitud` | varchar(40) | no |  | Magnitud, ej. kwh_solar |
| `factor_kgco2e` | numeric(12,6) | no |  | kg de CO₂ equivalente evitados por unidad |
| `fuente` | varchar(300) | no |  | Documento oficial del que sale el factor |
| `vigente_desde` | date | no |  | Desde |

### `ambiental.registro_ambiental` · Fase 2 · por finca · captura sin conexión

Medición ambiental de la finca (energía solar, biogás, compost, humus, agua).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `magnitud` | text (lista) | no |  | Qué se midió · valores: kwh_solar, m3_biogas, kg_compost, kg_humus, litros_agua_reutilizada, litros_agua_consumida |
| `cantidad` | numeric(12,2) | no |  | Cantidad |
| `fecha` | date | no |  | Día |
| `origen` | text (lista) | no |  | Cómo se obtuvo · valores: sensor, manual |
| `sensor_id` | bigint | sí | `iot.sensor` | Sensor, si aplica |

## Esquema `personal`

Tareas, plan de labores, cuadrillas, turnos, ausencias (sin diagnósticos), matriz de responsabilidades, equipos asignados, carné QR o NFC y jornada.

### `personal.cuadrilla` · Fase 2 · por finca

Grupo de trabajadores que recibe tareas juntos (ej. cuadrilla de cosecha).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. CUA-COSECHA |
| `nombre` | varchar(80) | no |  | Nombre |
| `lider_id` | bigint | sí | `terceros.empleado` | Trabajador que coordina la cuadrilla |
| `activa` | boolean | no |  | En uso |

### `personal.cuadrilla_miembro` · Fase 2 · por finca

Trabajadores de cada cuadrilla, con fechas.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `cuadrilla_id` | bigint | no | `personal.cuadrilla` | Cuadrilla |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `desde` | date | no |  | Desde |
| `hasta` | date | sí |  | Hasta; vacío = sigue |

### `personal.turno` · Fase 2 · por finca · auditada

Horario de trabajo programado de una persona en un día.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `fecha` | date | no |  | Día |
| `hora_inicio` | time | no |  | Hora de entrada |
| `hora_fin` | time | no |  | Hora de salida |
| `tipo` | text (lista) | no |  | Tipo de turno (define recargos) · valores: diurno, nocturno, mixto, descanso, festivo |
| `area_id` | bigint | sí | `personal.area_responsabilidad` | Área en la que trabaja ese turno |
| `cronograma_id` | bigint | sí | `personal.cronograma` | Cronograma del que salió |
| `horas` | numeric(4,2) | sí |  | Horas del turno (las calcula la base; si la salida es menor que la entrada, cruza la medianoche) |

### `personal.ausencia` · Fase 2 · por finca · auditada

Vacaciones, permisos, incapacidades y licencias. Guarda solo el tipo y las fechas, nunca el diagnóstico médico.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `tipo` | text (lista) | no |  | Tipo · valores: vacaciones, permiso, incapacidad_general, incapacidad_laboral, licencia_maternidad, licencia_paternidad, luto, calamidad, suspension |
| `desde` | date | no |  | Primer día |
| `hasta` | date | no |  | Último día |
| `remunerada` | boolean | no |  | Si se paga |
| `soporte_documento_id` | bigint | sí | `documental.documento` | Soporte (sin diagnóstico) |
| `aprobada_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |

### `personal.plantilla_tarea` · Fase 2 · por finca

Labor que se repite (recoger huevos dos veces al día, revisar bebederos, deshierbe semanal) y genera las tareas del día.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código, ej. REC-HUEVO-AM |
| `nombre` | varchar(120) | no |  | Nombre |
| `proceso` | varchar(60) | no |  | Proceso al que pertenece (une con la matriz de responsabilidades), ej. postura |
| `recurrencia` | text (lista) | no |  | Cada cuánto se repite · valores: diaria, semanal, mensual, unica |
| `dias_semana` | smallint[] | sí |  | Días (1 lunes … 7 domingo) para las semanales |
| `hora_limite` | time | sí |  | Hora máxima para terminarla |
| `zona_id` | bigint | sí | `nucleo.zona` | Zona |
| `duracion_estimada_min` | smallint | sí |  | Minutos estimados (estándar para productividad) |
| `competencia_id` | bigint | sí | `formacion.competencia` | Habilitación que exige; sin ella no se asigna |
| `forma_pago` | text (lista) | no |  | Si la tarea aprobada paga jornal o destajo (nunca afecta el salario fijo) · valores: ninguna, jornal, destajo |
| `valor_unitario` | numeric(14,2) | sí |  | Valor del jornal o de cada unidad a destajo |
| `unidad_destajo` | varchar(20) | sí |  | Unidad que se paga a destajo, ej. kg, racimo, planta |
| `registro_que_crea` | text (lista) | no |  | Registro que nace de la tarea aprobada · valores: ninguno, postura, alimentacion, labor_cultural, bioseguridad, riego, cosecha |
| `pasos` | jsonb | sí |  | Lista de chequeo |
| `area_id` | bigint | sí | `personal.area_responsabilidad` | Área de responsabilidad |
| `prioridad` | text (lista) | no |  | Prioridad · valores: baja, media, alta, critica |
| `activa` | boolean | no |  | En uso |

### `personal.tarea` · Fase 2 · por finca · captura sin conexión · auditada

Trabajo concreto con responsable, lugar, plazo y evidencia. Solo se asigna a quien está disponible y habilitado; aprobada no se edita.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `plantilla_tarea_id` | bigint | sí | `personal.plantilla_tarea` | Plantilla de la que salió |
| `titulo` | varchar(150) | no |  | Qué hay que hacer |
| `proceso` | varchar(60) | sí |  | Proceso |
| `fecha` | date | no |  | Día |
| `hora_limite` | timestamptz | sí |  | Plazo |
| `prioridad` | text (lista) | no |  | Prioridad · valores: baja, media, alta, critica |
| `zona_id` | bigint | sí | `nucleo.zona` | Zona |
| `area_id` | bigint | sí | `personal.area_responsabilidad` | Área de responsabilidad (su responsable puede aprobarla) |
| `lote_animal_id` | bigint | sí | `produccion.lote_animal` | Lote de animales |
| `siembra_id` | bigint | sí | `produccion.siembra` | Siembra |
| `activo_id` | bigint | sí | `activos.activo` | Equipo que se usa o se mantiene |
| `empleado_id` | bigint | sí | `terceros.empleado` | Responsable |
| `cuadrilla_id` | bigint | sí | `personal.cuadrilla` | Cuadrilla responsable |
| `origen` | text (lista) | no |  | De dónde salió · valores: plan, manual, agente, orden_trabajo, accion_correctiva, mision_robot, proyecto, agenda |
| `agente_id` | bigint | sí | `ia.agente` | Agente que la propuso (no asigna por su cuenta) |
| `estado` | text (lista) | no |  | Estado · valores: pendiente, en_curso, terminada, aprobada, devuelta, cancelada |
| `iniciada_en` | timestamptz | sí |  | Inicio (escaneo del carné) |
| `terminada_en` | timestamptz | sí |  | Fin |
| `cantidad` | numeric(12,2) | sí |  | Cantidad lograda (kg, aves, plantas) para destajo y productividad |
| `unidad` | varchar(20) | sí |  | Unidad de la cantidad |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó o devolvió |
| `aprobado_en` | timestamptz | sí |  | Cuándo |
| `comentario_revision` | text | sí |  | Comentario al aprobar o devolver |

### `personal.paso_tarea` · Fase 2 · por finca · captura sin conexión

Paso de la lista de chequeo de una tarea.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tarea_id` | bigint | no | `personal.tarea` | Tarea |
| `orden` | smallint | no |  | Orden |
| `descripcion` | varchar(200) | no |  | Paso |
| `hecho` | boolean | no |  | Marcado |
| `hecho_en` | timestamptz | sí |  | Cuándo |

### `personal.evidencia_tarea` · Fase 2 · por finca · captura sin conexión

Prueba de una tarea: foto, lectura del carné o del lote, nota de voz o el registro que creó.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tarea_id` | bigint | no | `personal.tarea` | Tarea |
| `tipo` | text (lista) | no |  | Tipo · valores: foto, lectura_qr, lectura_nfc, nota_voz, documento, registro |
| `archivo_url` | varchar(300) | sí |  | Archivo |
| `registro_tabla` | varchar(60) | sí |  | Tabla del registro creado, ej. produccion.registro_postura |
| `registro_id` | bigint | sí |  | Id del registro |

### `personal.matriz_responsabilidad` · Fase 2 · por finca · auditada

Matriz RACI: para cada proceso, qué rol lo hace, lo aprueba, es consultado o informado.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proceso` | varchar(60) | no |  | Proceso, ej. postura, venta, nomina |
| `rol_id` | bigint | no | `nucleo.rol` | Rol |
| `responsabilidad` | text (lista) | no |  | R, A, C o I · valores: responsable, aprueba, consultado, informado |

### `personal.asignacion_equipo` · Fase 2 · por finca

Quién tiene cada herramienta o equipo, desde cuándo y en qué estado lo recibió y lo devolvió.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `activo_id` | bigint | no | `activos.activo` | Equipo |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `entregado_en` | timestamptz | no |  | Entrega |
| `estado_entrega` | text (lista) | no |  | Estado al entregar · valores: bueno, regular, malo |
| `devuelto_en` | timestamptz | sí |  | Devolución |
| `estado_devolucion` | text (lista) | sí |  | Estado al devolver · valores: bueno, regular, malo, perdido |

### `personal.credencial_trabajo` · Fase 2 · por finca · auditada

Carné del trabajador con QR o etiqueta NFC para registrar quién hizo qué, sin biometría.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `tipo` | text (lista) | no |  | Tipo (nunca biométrico) · valores: qr, nfc |
| `codigo_hash` | char(64) | no |  | Huella SHA-256 del código impreso o grabado |
| `emitida_en` | date | no |  | Emisión |
| `revocada_en` | timestamptz | sí |  | Revocación (pérdida o retiro) |

### `personal.jornada` · Fase 2 · por finca · captura sin conexión · auditada

Registro de jornada (entrada, salida, horas y labor) para jornaleros sin tarea asignada ese día.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `fecha` | date | no |  | Día |
| `entrada` | timestamptz | no |  | Entrada |
| `salida` | timestamptz | sí |  | Salida |
| `horas` | numeric(4,2) | sí |  | Horas trabajadas |
| `labor` | varchar(150) | sí |  | Labor hecha |
| `zona_id` | bigint | sí | `nucleo.zona` | Zona |
| `metodo_registro` | text (lista) | no |  | Cómo se registró · valores: qr, nfc, manual |
| `aprobada_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |
| `aprobada_en` | timestamptz | sí |  | Cuándo |

### `personal.area_responsabilidad` · Fase 2 · por finca

Área de responsabilidad (galpón, cultivos, turismo y cabañas, bodega y despachos, mantenimiento, vigilancia): agrupa zonas, personas y tareas, con un responsable.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. AR-GALPON |
| `nombre` | varchar(120) | no |  | Nombre |
| `descripcion` | text | sí |  | Qué cubre |
| `zonas` | bigint[] | sí |  | Zonas que abarca |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Centro de costo |
| `opera_24_7` | boolean | no |  | Necesita cobertura las 24 horas, todos los días (vigilancia, galpón) |
| `activa` | boolean | no |  | En uso |

### `personal.miembro_area` · Fase 2 · por finca · auditada

Personas de cada área, con quién es el responsable (puede aprobar las tareas del área).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `area_id` | bigint | no | `personal.area_responsabilidad` | Área |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `es_responsable` | boolean | no |  | Responsable del área |
| `desde` | date | no |  | Desde |
| `hasta` | date | sí |  | Hasta |

### `personal.patron_turno` · Fase 2 · por finca

Patrón de turnos reutilizable: semanal (se eligen días y horas), cíclico (ej. 2 días, 2 noches, 2 de descanso para 24/7) o flexible (se arma a mano).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. SEM-LV-6-14, CIC-2D2N2L |
| `nombre` | varchar(120) | no |  | Nombre |
| `tipo` | text (lista) | no |  | Semanal: día 1 = lunes … 7 = domingo; cíclico: día 1 … N del ciclo · valores: semanal, ciclico, flexible |
| `ciclo_dias` | smallint | no |  | Días del ciclo |

### `personal.patron_turno_detalle` · Fase 2 · por finca

Día del patrón con su horario (puede cruzar la medianoche) o descanso.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `patron_id` | bigint | no | `personal.patron_turno` | Patrón |
| `dia_ciclo` | smallint | no |  | Día del ciclo (semanal: 1 lunes … 7 domingo) |
| `hora_inicio` | time | sí |  | Entrada (vacío = descanso) |
| `hora_fin` | time | sí |  | Salida; si es menor o igual a la entrada, termina al día siguiente |
| `tipo` | text (lista) | no |  | Tipo · valores: diurno, nocturno, mixto, descanso |

### `personal.cronograma` · Fase 2 · por finca · auditada

Cronograma de trabajo de un área por un periodo: se genera desde patrones, se ajusta a mano y se publica cuando cumple jornada máxima, descanso semanal y cobertura.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(150) | no |  | Nombre, ej. Galpón · noviembre 2026 |
| `area_id` | bigint | no | `personal.area_responsabilidad` | Área |
| `desde` | date | no |  | Primer día |
| `hasta` | date | no |  | Último día |
| `estado` | text (lista) | no |  | Estado · valores: borrador, publicado, cerrado |
| `permitir_huecos` | boolean | no |  | Publicar aunque falte cobertura (queda la advertencia) |
| `publicado_por` | bigint | sí | `nucleo.usuario` | Quién lo publicó |
| `publicado_en` | timestamptz | sí |  | Cuándo |

### `personal.asignacion_patron` · Fase 2 · por finca

Qué patrón sigue cada persona dentro del cronograma (con desfase para rotar entre varias personas).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `cronograma_id` | bigint | no | `personal.cronograma` | Cronograma |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `patron_id` | bigint | no | `personal.patron_turno` | Patrón |
| `desfase_dias` | smallint | no |  | En qué día del ciclo empieza (rotación) |

### `personal.requerimiento_cobertura` · Fase 2 · por finca

Cuántas personas necesita un área por franja horaria y día (ej. galpón: 1 persona las 24 horas; cabañas: 2 de 8 a 18 los fines de semana).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `area_id` | bigint | no | `personal.area_responsabilidad` | Área |
| `dia_semana` | smallint | sí |  | 1 lunes … 7 domingo; vacío = todos los días |
| `hora_inicio` | time | no |  | Desde |
| `hora_fin` | time | no |  | Hasta (24:00 se escribe 23:59:59) |
| `personas_min` | smallint | no |  | Personas mínimas |

### `personal.disponibilidad` · Fase 2 · por finca

Días y horas en que cada persona puede o prefiere trabajar (para armar el cronograma flexible).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `dia_semana` | smallint | no |  | 1 lunes … 7 domingo |
| `hora_inicio` | time | no |  | Desde |
| `hora_fin` | time | no |  | Hasta |
| `preferencia` | text (lista) | no |  | Preferencia · valores: disponible, preferido, no_disponible |

## Esquema `nomina`

Conceptos, periodos, novedades, liquidación, prestaciones, PILA, nómina electrónica (apagada) y pagos con doble aprobación.

### `nomina.concepto_nomina` · Fase 2 · por finca · auditada

Concepto de la nómina (salario, auxilio, horas extra, recargos, jornal, destajo, deducciones, aportes). La tarifa vive en nucleo.parametro, nunca en el código.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código, ej. SALARIO, AUX_TRANSPORTE, JORNAL, DESTAJO, SALUD_EMP |
| `nombre` | varchar(120) | no |  | Nombre |
| `tipo` | text (lista) | no |  | Tipo · valores: devengado, deduccion, aporte_empleador, provision |
| `base` | text (lista) | no |  | Cómo se calcula · valores: salario, jornal, destajo, horas, valor_fijo, porcentaje |
| `parametro_clave` | varchar(80) | sí |  | Clave de nucleo.parametro con la tarifa vigente |
| `constitutivo_salario` | boolean | no |  | Hace parte de la base para prestaciones |
| `cuenta_contable_id` | bigint | sí | `finanzas.cuenta_contable` | Cuenta de causación |
| `codigo_dian` | varchar(40) | sí |  | Elemento del documento soporte de nómina electrónica |
| `activo` | boolean | no |  | En uso |

### `nomina.periodo_nomina` · Fase 2 · por finca · auditada

Periodo de pago. Cerrado no se edita; las correcciones van como nota de ajuste. Cierre con doble aprobación y nunca por un agente.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. 2026-11 |
| `tipo` | text (lista) | no |  | Frecuencia · valores: mensual, quincenal, semanal |
| `desde` | date | no |  | Primer día |
| `hasta` | date | no |  | Último día |
| `estado` | text (lista) | no |  | Estado · valores: abierto, prenomina, cerrado, anulado |
| `preparado_por` | bigint | sí | `nucleo.usuario` | Quién armó la prenómina |
| `cerrado_por` | bigint | sí | `nucleo.usuario` | Primera aprobación del cierre |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Segunda aprobación (persona distinta) |
| `cerrado_en` | timestamptz | sí |  | Cuándo |
| `comprobante_id` | bigint | sí | `finanzas.comprobante` | Comprobante de causación |
| `ajusta_periodo_id` | bigint | sí | `nomina.periodo_nomina` | Si es nota de ajuste, periodo que corrige |

### `nomina.novedad` · Fase 2 · por finca · auditada

Hecho que se paga o descuenta en el periodo: salario fijo, jornales y destajo de tareas aprobadas, horas extra, ausencias, préstamos.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `periodo_id` | bigint | no | `nomina.periodo_nomina` | Periodo |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `concepto_id` | bigint | no | `nomina.concepto_nomina` | Concepto |
| `cantidad` | numeric(12,2) | no |  | Días, horas, jornales o unidades |
| `valor_unitario` | numeric(14,2) | no |  | Valor por unidad |
| `valor` | numeric(14,2) | no |  | Valor total |
| `origen` | text (lista) | no |  | De dónde sale · valores: contrato, tarea, jornada, ausencia, manual |
| `tarea_id` | bigint | sí | `personal.tarea` | Tarea aprobada que la origina |
| `jornada_id` | bigint | sí | `personal.jornada` | Jornada que la origina |
| `ausencia_id` | bigint | sí | `personal.ausencia` | Ausencia que la origina |
| `observacion` | varchar(200) | sí |  | Nota |

### `nomina.liquidacion` · Fase 2 · por finca · auditada

Resultado del periodo para un trabajador: devengado, deducciones y neto.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `periodo_id` | bigint | no | `nomina.periodo_nomina` | Periodo |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `total_devengado` | numeric(14,2) | no |  | Devengado |
| `total_deducciones` | numeric(14,2) | no |  | Deducciones |
| `neto` | numeric(14,2) | no |  | Neto a pagar |
| `estado` | text (lista) | no |  | Estado · valores: borrador, aprobada, pagada |

### `nomina.liquidacion_detalle` · Fase 2 · por finca

Línea de la liquidación por concepto.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `liquidacion_id` | bigint | no | `nomina.liquidacion` | Liquidación |
| `concepto_id` | bigint | no | `nomina.concepto_nomina` | Concepto |
| `cantidad` | numeric(12,2) | no |  | Cantidad |
| `valor` | numeric(14,2) | no |  | Valor |

### `nomina.provision_prestacion` · Fase 2 · por finca

Provisión mensual de cesantías, intereses, prima y vacaciones.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `periodo_id` | bigint | no | `nomina.periodo_nomina` | Periodo |
| `empleado_id` | bigint | no | `terceros.empleado` | Trabajador |
| `tipo` | text (lista) | no |  | Prestación · valores: cesantias, intereses_cesantias, prima, vacaciones |
| `base` | numeric(14,2) | no |  | Base |
| `valor` | numeric(14,2) | no |  | Valor provisionado |

### `nomina.documento_nomina_electronica` · Fase 2 · por finca · auditada

Documento soporte de pago de nómina electrónica (uno por trabajador al mes). Se transmite por el servicio gratuito de la DIAN o un proveedor autorizado; se enciende con nomina_electronica.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `liquidacion_id` | bigint | no | `nomina.liquidacion` | Liquidación |
| `tipo` | text (lista) | no |  | Tipo · valores: individual, ajuste |
| `proveedor` | text (lista) | no |  | Por dónde se transmite · valores: dian_gratuito, proveedor_tecnologico |
| `cune` | varchar(120) | sí |  | Código único devuelto por la DIAN |
| `estado` | text (lista) | no |  | Estado · valores: pendiente, enviado, aceptado, rechazado |
| `enviado_en` | timestamptz | sí |  | Envío |
| `respuesta` | jsonb | sí |  | Respuesta del proveedor |
| `xml_url` | varchar(300) | sí |  | XML firmado por el proveedor (nunca se firma a mano) |

### `nomina.planilla_pila` · Fase 2 · por finca

Archivo de la planilla de seguridad social para el operador de la PILA; el pago lo hace una persona.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `periodo_id` | bigint | no | `nomina.periodo_nomina` | Periodo |
| `tipo_planilla` | varchar(5) | no |  | Tipo de planilla (E = empleados) |
| `archivo_url` | varchar(300) | no |  | Archivo generado |
| `operador` | varchar(60) | sí |  | Operador de información |
| `numero_planilla` | varchar(30) | sí |  | Número asignado por el operador |
| `pagada_por` | bigint | sí | `nucleo.usuario` | Quién la pagó |
| `pagada_en` | timestamptz | sí |  | Cuándo |

### `nomina.pago_nomina` · Fase 2 · por finca · auditada

Pago de una liquidación (transferencia, Bre-B o efectivo). Lo prepara una persona y lo aprueba otra; nadie aprueba su propio pago.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `liquidacion_id` | bigint | no | `nomina.liquidacion` | Liquidación |
| `medio` | text (lista) | no |  | Medio · valores: transferencia, bre_b, efectivo |
| `valor` | numeric(14,2) | no |  | Valor |
| `preparado_por` | bigint | no | `nucleo.usuario` | Quién lo preparó |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Primera aprobación |
| `segunda_aprobacion_por` | bigint | sí | `nucleo.usuario` | Segunda aprobación (pagos sobre el monto del parámetro monto_doble_aprobacion) |
| `pagado_en` | timestamptz | sí |  | Cuándo se pagó |
| `referencia` | varchar(80) | sí |  | Referencia bancaria |

### `nomina.exportacion_nomina` · Fase 2 · por finca

Archivo para el contador cuando lleva la nómina en su propio programa.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `periodo_id` | bigint | no | `nomina.periodo_nomina` | Periodo |
| `formato` | text (lista) | no |  | Formato · valores: csv, excel, siigo, world_office, helisa, otro |
| `archivo_url` | varchar(300) | no |  | Archivo |
| `generado_por` | bigint | no | `nucleo.usuario` | Quién lo generó |

## Esquema `formacion`

Cursos, lecciones, evaluaciones, sesiones presenciales, certificados y habilitaciones que permiten asignar tareas.

### `formacion.competencia` · Fase 2 · por finca

Habilidad que habilita tareas (registrar vacunas, aplicar insumos, liberar lotes, operar motosierra), con su vigencia.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(40) | no |  | Código, ej. aplicar_vacunas |
| `nombre` | varchar(120) | no |  | Nombre |
| `vigencia_meses` | smallint | sí |  | Meses que dura el certificado; vacío = no vence |
| `descripcion` | text | sí |  | Qué permite hacer |

### `formacion.curso` · Fase 2 · por finca

Curso virtual, presencial o mixto para operarios o estudiantes; los externos (SENA, FAO, Moodle) se enlazan.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código |
| `nombre` | varchar(150) | no |  | Nombre |
| `descripcion` | text | sí |  | Contenido |
| `publico` | text (lista) | no |  | A quién va · valores: operarios, estudiantes, ambos |
| `modalidad` | text (lista) | no |  | Modalidad · valores: virtual, presencial, mixto |
| `competencia_id` | bigint | sí | `formacion.competencia` | Habilitación que otorga al aprobar |
| `nota_minima` | numeric(4,2) | no |  | Nota mínima para aprobar (escala 0 a 5) |
| `duracion_horas` | numeric(5,1) | sí |  | Horas |
| `origen` | text (lista) | no |  | De dónde viene · valores: propio, sena, fao, moodle, otro |
| `url_externa` | varchar(300) | sí |  | Enlace, si es externo |
| `ruta_cargo` | varchar(60) | sí |  | Ruta de aprendizaje, ej. operario_galpon, vendedor |
| `activo` | boolean | no |  | Publicado |

### `formacion.leccion` · Fase 2 · por finca

Lección de un curso (texto, video corto, práctica guiada); se descarga para verla sin señal.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `curso_id` | bigint | no | `formacion.curso` | Curso |
| `orden` | smallint | no |  | Orden |
| `titulo` | varchar(150) | no |  | Título |
| `tipo` | text (lista) | no |  | Tipo · valores: texto, video, practica, tutorial_pantalla |
| `contenido_url` | varchar(300) | sí |  | Archivo |
| `pantalla` | varchar(80) | sí |  | Pantalla de la app que explica (tutoriales dentro de la app) |
| `documento_id` | bigint | sí | `documental.documento` | Protocolo o manual de base |
| `descargable` | boolean | no |  | Se puede ver sin conexión |

### `formacion.evaluacion` · Fase 2 · por finca

Examen de un curso.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `curso_id` | bigint | no | `formacion.curso` | Curso |
| `titulo` | varchar(150) | no |  | Título |
| `intentos_max` | smallint | no |  | Intentos |

### `formacion.pregunta` · Fase 2 · por finca

Pregunta de una evaluación.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `evaluacion_id` | bigint | no | `formacion.evaluacion` | Evaluación |
| `orden` | smallint | no |  | Orden |
| `enunciado` | text | no |  | Pregunta |
| `tipo` | text (lista) | no |  | Tipo · valores: unica, multiple, verdadero_falso, practica |
| `opciones` | jsonb | sí |  | Opciones |
| `respuesta_correcta` | jsonb | sí |  | Respuesta |
| `puntos` | numeric(4,1) | no |  | Puntos |

### `formacion.inscripcion` · Fase 2 · por finca

Persona (operario o estudiante) inscrita en un curso, con su nota.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `curso_id` | bigint | no | `formacion.curso` | Curso |
| `tercero_id` | bigint | no | `terceros.tercero` | Persona |
| `inscrito_en` | date | no |  | Inscripción |
| `estado` | text (lista) | no |  | Estado · valores: inscrito, en_curso, aprobado, reprobado, retirado |
| `nota` | numeric(4,2) | sí |  | Nota final |
| `aprobado_en` | date | sí |  | Fecha de aprobación |

### `formacion.progreso` · Fase 2 · por finca · captura sin conexión

Lecciones vistas por cada inscrito.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `inscripcion_id` | bigint | no | `formacion.inscripcion` | Inscripción |
| `leccion_id` | bigint | no | `formacion.leccion` | Lección |
| `completada_en` | timestamptz | no |  | Cuándo |

### `formacion.sesion_presencial` · Fase 2 · por finca

Sesión dictada por el veterinario, el agrónomo o el encargado; su asistencia cuenta igual que un curso virtual.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `curso_id` | bigint | no | `formacion.curso` | Curso |
| `instructor_id` | bigint | no | `terceros.tercero` | Quién la dicta |
| `fecha` | date | no |  | Día |
| `lugar` | varchar(120) | sí |  | Lugar |
| `duracion_horas` | numeric(4,1) | no |  | Horas |

### `formacion.asistencia` · Fase 2 · por finca · captura sin conexión

Asistencia y nota de cada persona en una sesión presencial.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `sesion_id` | bigint | no | `formacion.sesion_presencial` | Sesión |
| `tercero_id` | bigint | no | `terceros.tercero` | Persona |
| `asistio` | boolean | no |  | Asistió |
| `nota` | numeric(4,2) | sí |  | Nota práctica |

### `formacion.certificado` · Fase 2 · por finca · auditada

Certificado interno con fecha, nota y vencimiento; al emitirse crea la habilitación.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Persona |
| `competencia_id` | bigint | no | `formacion.competencia` | Competencia |
| `inscripcion_id` | bigint | sí | `formacion.inscripcion` | Curso virtual aprobado |
| `sesion_id` | bigint | sí | `formacion.sesion_presencial` | Sesión presencial |
| `emitido_en` | date | no |  | Emisión |
| `vence_en` | date | sí |  | Vencimiento |
| `nota` | numeric(4,2) | sí |  | Nota |
| `codigo_verificacion` | varchar(40) | no |  | Código para verificarlo |

### `formacion.habilitacion` · Fase 2 · por finca · auditada

Permiso para hacer una tarea, nacido de un certificado. Al vencer el certificado se retira sola.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tercero_id` | bigint | no | `terceros.tercero` | Persona |
| `competencia_id` | bigint | no | `formacion.competencia` | Competencia |
| `certificado_id` | bigint | no | `formacion.certificado` | Certificado que la sustenta |
| `desde` | date | no |  | Desde |
| `hasta` | date | sí |  | Hasta |
| `activa` | boolean | no |  | Vigente |
| `retirada_en` | timestamptz | sí |  | Cuándo se retiró |

### `formacion.necesidad_formacion` · Fase 2 · por finca

Necesidad de formación detectada (por cargo, por una no conformidad, por un cambio o pedida por la persona).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `origen` | text (lista) | no |  | De dónde sale · valores: cargo, no_conformidad, cambio, solicitud, evaluacion_desempeno, norma |
| `descripcion` | text | no |  | Qué se necesita aprender |
| `tercero_id` | bigint | sí | `terceros.tercero` | Persona, si es individual |
| `competencia_id` | bigint | sí | `formacion.competencia` | Competencia |
| `curso_id` | bigint | sí | `formacion.curso` | Curso que la atiende |
| `estado` | text (lista) | no |  | Estado · valores: abierta, planificada, atendida, descartada |

### `formacion.encuesta` · Fase 2 · por finca · captura sin conexión

Encuesta de satisfacción y de resultados de un curso o sesión (seguimiento y medición de la formación).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `curso_id` | bigint | sí | `formacion.curso` | Curso |
| `sesion_id` | bigint | sí | `formacion.sesion_presencial` | Sesión |
| `tercero_id` | bigint | sí | `terceros.tercero` | Quién responde (vacío = anónima) |
| `satisfaccion` | smallint | no |  | Satisfacción general 1 a 5 |
| `utilidad` | smallint | no |  | Utilidad para el trabajo 1 a 5 |
| `instructor` | smallint | sí |  | Desempeño del instructor 1 a 5 |
| `comentario` | text | sí |  | Comentario |

### `formacion.queja_apelacion` · Fase 2 · por finca · auditada

Queja sobre la formación o apelación de una nota o certificado; se responde en plazo y la resuelve alguien distinto del instructor.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo · valores: queja, apelacion |
| `tercero_id` | bigint | no | `terceros.tercero` | Quién la presenta |
| `curso_id` | bigint | sí | `formacion.curso` | Curso |
| `certificado_id` | bigint | sí | `formacion.certificado` | Certificado apelado |
| `descripcion` | text | no |  | Qué pasó |
| `presentada_en` | date | no |  | Fecha |
| `responder_antes` | date | no |  | Plazo de respuesta |
| `estado` | text (lista) | no |  | Estado · valores: recibida, en_estudio, resuelta, rechazada |
| `respuesta` | text | sí |  | Respuesta |
| `resuelta_por` | bigint | sí | `nucleo.usuario` | Quién resolvió |

## Esquema `activos`

Hoja de vida de equipos, planes y órdenes de mantenimiento, uso, repuestos y depreciación.

### `activos.activo` · Fase 1 · por finca · auditada

Hoja de vida de cada equipo de la finca (camioneta, motocultor, guadañas, bombas, paneles, dron, robot).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. ACT-GUA-01 |
| `nombre` | varchar(120) | no |  | Nombre |
| `tipo` | text (lista) | no |  | Tipo · valores: vehiculo, maquinaria, herramienta, bomba, panel_solar, bateria, equipo_electronico, dron, robot, infraestructura, otro |
| `marca` | varchar(60) | sí |  | Marca |
| `modelo` | varchar(60) | sí |  | Modelo |
| `serie` | varchar(60) | sí |  | Número de serie |
| `fecha_compra` | date | sí |  | Compra |
| `valor_compra` | numeric(14,2) | sí |  | Costo de adquisición |
| `valor_residual` | numeric(14,2) | no |  | Valor de salvamento |
| `vida_util_meses` | smallint | sí |  | Vida útil |
| `metodo_depreciacion` | text (lista) | no |  | Método · valores: linea_recta, ninguno |
| `zona_id` | bigint | sí | `nucleo.zona` | Ubicación |
| `responsable_id` | bigint | sí | `terceros.empleado` | Responsable |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Centro de costo que lo usa |
| `garantia_hasta` | date | sí |  | Garantía |
| `horometro` | numeric(10,1) | no |  | Horas de uso acumuladas |
| `odometro` | numeric(10,1) | no |  | Kilómetros acumulados |
| `vehiculo_id` | bigint | sí | `inventario.vehiculo` | Vehículo de entregas, si es el mismo |
| `dispositivo_id` | bigint | sí | `iot.dispositivo` | Dispositivo IoT, si lo tiene |
| `registro_aerocivil` | varchar(40) | sí |  | Registro del dron ante la Aerocivil (RAC 100) |
| `estado` | text (lista) | no |  | Estado · valores: operativo, en_mantenimiento, danado, dado_de_baja |

### `activos.plan_mantenimiento` · Fase 2 · por finca

Mantenimiento por horas de uso, kilómetros o días (cambio de aceite, afilado, revisión de la bomba).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `activo_id` | bigint | no | `activos.activo` | Equipo |
| `nombre` | varchar(120) | no |  | Qué se hace |
| `tipo` | text (lista) | no |  | Tipo (predictivo cuando hay sensores) · valores: preventivo, predictivo |
| `frecuencia_tipo` | text (lista) | no |  | Base de la frecuencia · valores: horas, km, dias |
| `frecuencia_valor` | numeric(10,1) | no |  | Cada cuánto |
| `ultima_lectura` | numeric(10,1) | no |  | Horómetro u odómetro en la última ejecución |
| `ultima_fecha` | date | sí |  | Fecha de la última ejecución |
| `activo` | boolean | no |  | En uso |

### `activos.orden_trabajo` · Fase 2 · por finca · auditada

Orden de mantenimiento: la crea sola la regla al vencer el plan y se asigna como tarea; descuenta repuestos del inventario.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `activo_id` | bigint | no | `activos.activo` | Equipo |
| `plan_id` | bigint | sí | `activos.plan_mantenimiento` | Plan que la originó |
| `tipo` | text (lista) | no |  | Tipo · valores: preventivo, correctivo, predictivo |
| `descripcion` | text | no |  | Qué hacer |
| `estado` | text (lista) | no |  | Estado · valores: abierta, en_curso, cerrada, cancelada |
| `tarea_id` | bigint | sí | `personal.tarea` | Tarea asignada |
| `lectura_cierre` | numeric(10,1) | sí |  | Horómetro u odómetro al cerrar |
| `costo_mano_obra` | numeric(14,2) | no |  | Mano de obra |
| `costo_repuestos` | numeric(14,2) | no |  | Repuestos |
| `cerrada_en` | timestamptz | sí |  | Cierre |

### `activos.repuesto_orden` · Fase 2 · por finca

Repuesto usado en una orden de trabajo (sale del kardex).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `orden_id` | bigint | no | `activos.orden_trabajo` | Orden |
| `producto_id` | bigint | no | `inventario.producto` | Repuesto |
| `cantidad` | numeric(10,2) | no |  | Cantidad |
| `movimiento_id` | bigint | sí | `inventario.movimiento_inventario` | Salida en el kardex |

### `activos.uso_activo` · Fase 2 · por finca · captura sin conexión

Uso de un equipo: horas, kilómetros y combustible, cargados al centro de costo que lo usó.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `activo_id` | bigint | no | `activos.activo` | Equipo |
| `fecha` | date | no |  | Día |
| `empleado_id` | bigint | sí | `terceros.empleado` | Quién lo usó |
| `horas` | numeric(6,1) | no |  | Horas |
| `km` | numeric(8,1) | no |  | Kilómetros |
| `combustible_litros` | numeric(8,2) | sí |  | Combustible |
| `costo_combustible` | numeric(14,2) | sí |  | Costo del combustible |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Centro de costo |
| `tarea_id` | bigint | sí | `personal.tarea` | Tarea |

### `activos.depreciacion` · Fase 2 · por finca

Depreciación mensual de cada activo (alimenta la contabilidad y el costo por línea).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `activo_id` | bigint | no | `activos.activo` | Equipo |
| `mes` | date | no |  | Primer día del mes |
| `valor` | numeric(14,2) | no |  | Depreciación del mes |
| `acumulada` | numeric(14,2) | no |  | Depreciación acumulada |
| `comprobante_id` | bigint | sí | `finanzas.comprobante` | Comprobante |

## Esquema `documental`

Documentos con versiones, aprobación, vencimiento y vínculos; los agentes solo leen la versión aprobada y vigente.

### `documental.documento` · Fase 1 · por finca · auditada

Papel que la finca no puede perder: permisos, registros ICA, RUT, contratos, protocolos, manuales, evidencias. Con datos personales sigue la Ley 1581.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código, ej. PRT-BIO-01 |
| `titulo` | varchar(200) | no |  | Título |
| `tipo` | text (lista) | no |  | Tipo · valores: permiso, registro, contrato, protocolo, manual, ficha_tecnica, evidencia, acta, resultado_laboratorio, poliza, certificado, plan, otro |
| `entidad_emisora` | varchar(120) | sí |  | Quién lo expide, ej. ICA, CAR, DIAN |
| `numero` | varchar(60) | sí |  | Número oficial |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Responsable |
| `nivel_acceso` | text (lista) | no |  | Quién lo ve · valores: finca, rol, restringido |
| `rol_id` | bigint | sí | `nucleo.rol` | Rol que lo ve, si es por rol |
| `contiene_datos_personales` | boolean | no |  | Tiene datos personales (Ley 1581) |
| `finalidad` | text | sí |  | Para qué se guarda |
| `conservar_hasta` | date | sí |  | Hasta cuándo se conserva |
| `uso_agentes` | boolean | no |  | Lo pueden leer los agentes (solo la versión aprobada y vigente) |

### `documental.version_documento` · Fase 1 · por finca · auditada

Versión de un documento con su archivo, huella, aprobación y vigencia; solo una aprobada vigente a la vez.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `documento_id` | bigint | no | `documental.documento` | Documento |
| `version` | smallint | no |  | Número de versión |
| `archivo_url` | varchar(300) | no |  | Archivo en el almacén de objetos |
| `hash_sha256` | char(64) | no |  | Huella del archivo |
| `estado` | text (lista) | no |  | Estado · valores: borrador, en_revision, aprobada, obsoleta |
| `aprobada_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |
| `aprobada_en` | timestamptz | sí |  | Cuándo |
| `vigente_desde` | date | sí |  | Desde |
| `vence_en` | date | sí |  | Vencimiento (permisos, registros, pólizas) |
| `avisar_dias` | smallint | no |  | Días de aviso antes de vencer |
| `cambios` | text | sí |  | Qué cambió |

### `documental.vinculo_documento` · Fase 1 · por finca

Une un documento con cualquier registro (un lote, una póliza, un activo, una no conformidad).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `documento_id` | bigint | no | `documental.documento` | Documento |
| `registro_tabla` | varchar(60) | no |  | Tabla |
| `registro_id` | bigint | no |  | Id |

## Esquema `cumplimiento`

Normas (granja avícola biosegura, BPA, GLOBALG.A.P.), requisitos, expediente, evidencias, auditorías y acciones correctivas.

### `cumplimiento.norma` · Fase 1 · catálogo compartido

Norma o certificación (granja avícola biosegura ICA 3651/2014, BPA ICA 30021/2017, GLOBALG.A.P. IFA v6). Catálogo compartido.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código, ej. ICA_GAB, ICA_BPA, GLOBALGAP_IFA6 |
| `nombre` | varchar(200) | no |  | Nombre |
| `entidad` | varchar(80) | no |  | Entidad |
| `referencia` | varchar(120) | no |  | Norma, ej. Resolución ICA 3651 de 2014 |
| `obligatoria` | boolean | no |  | Obligatoria por ley |
| `condicion_obligatoria` | text | sí |  | Cuándo aplica, ej. postura o levante desde 200 aves |
| `funcion_codigo` | varchar(40) | sí |  | Función por finca que la enciende; vacío = siempre activa |
| `vigencia_certificado_meses` | smallint | sí |  | Duración del certificado |
| `url_fuente` | varchar(300) | sí |  | Texto oficial |

### `cumplimiento.requisito` · Fase 1 · catálogo compartido

Requisito de una norma con el tipo de evidencia y, si aplica, la regla que la revisa sola.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `norma_id` | bigint | no | `cumplimiento.norma` | Norma |
| `codigo` | varchar(30) | no |  | Código |
| `descripcion` | text | no |  | Qué pide |
| `tipo_evidencia` | text (lista) | no |  | Evidencia esperada · valores: documento, registro, certificado_formacion, analisis, inspeccion |
| `regla_evidencia` | varchar(80) | sí |  | Revisión automática, ej. documento:protocolo, competencia:bioseguridad, registro:produccion.registro_bioseguridad |
| `vigencia_dias` | smallint | sí |  | Días que vale la evidencia |
| `critico` | boolean | no |  | Sin él no se certifica |

### `cumplimiento.expediente` · Fase 1 · por finca · auditada

Expediente de la finca ante una norma (incluye el registro sanitario de predio avícola, RSPA).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `norma_id` | bigint | no | `cumplimiento.norma` | Norma |
| `estado` | text (lista) | no |  | Estado · valores: en_preparacion, solicitado, certificado, suspendido, vencido |
| `rspa_numero` | varchar(40) | sí |  | Registro sanitario de predio avícola (RSPA) del ICA, si aplica |
| `numero_certificado` | varchar(60) | sí |  | Número del certificado |
| `organismo` | varchar(120) | sí |  | Entidad u organismo certificador |
| `solicitado_en` | date | sí |  | Solicitud |
| `certificado_en` | date | sí |  | Certificación |
| `vence_en` | date | sí |  | Vencimiento |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Responsable |

### `cumplimiento.evaluacion_requisito` · Fase 1 · por finca · captura sin conexión · auditada

Estado de cada requisito en el expediente. Con evidencia vencida pasa solo a no cumple.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `expediente_id` | bigint | no | `cumplimiento.expediente` | Expediente |
| `requisito_id` | bigint | no | `cumplimiento.requisito` | Requisito |
| `estado` | text (lista) | no |  | Estado · valores: cumple, no_cumple, en_proceso, no_aplica |
| `origen` | text (lista) | no |  | Cómo se evaluó · valores: automatica, autoevaluacion, auditoria |
| `evaluado_por` | bigint | sí | `nucleo.usuario` | Quién |
| `evaluado_en` | timestamptz | sí |  | Cuándo |
| `vence_en` | date | sí |  | Vencimiento de la evidencia que lo sostiene |
| `observacion` | text | sí |  | Nota |

### `cumplimiento.evidencia_requisito` · Fase 1 · por finca

Prueba de un requisito: un documento o un registro del sistema, con su vencimiento.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `evaluacion_id` | bigint | no | `cumplimiento.evaluacion_requisito` | Evaluación |
| `documento_id` | bigint | sí | `documental.documento` | Documento |
| `registro_tabla` | varchar(60) | sí |  | Tabla del registro |
| `registro_id` | bigint | sí |  | Id |
| `descripcion` | varchar(200) | no |  | Qué prueba |
| `vence_en` | date | sí |  | Vence |

### `cumplimiento.auditoria_externa` · Fase 1 · por finca

Auditoría interna o externa programada, con aviso previo y resultado.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `expediente_id` | bigint | no | `cumplimiento.expediente` | Expediente |
| `tipo` | text (lista) | no |  | Tipo · valores: interna, externa, seguimiento |
| `organismo` | varchar(120) | sí |  | Quién audita |
| `fecha_programada` | date | no |  | Fecha |
| `fecha_realizada` | date | sí |  | Realizada |
| `resultado` | text (lista) | no |  | Resultado · valores: pendiente, aprobada, con_hallazgos, rechazada |
| `informe_documento_id` | bigint | sí | `documental.documento` | Informe |

### `cumplimiento.no_conformidad` · Fase 1 · por finca · auditada

Hallazgo; no se cierra sin acciones verificadas y sin quien verifique.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `expediente_id` | bigint | no | `cumplimiento.expediente` | Expediente |
| `auditoria_id` | bigint | sí | `cumplimiento.auditoria_externa` | Auditoría que la encontró |
| `requisito_id` | bigint | sí | `cumplimiento.requisito` | Requisito |
| `descripcion` | text | no |  | Hallazgo |
| `severidad` | text (lista) | no |  | Severidad · valores: menor, mayor, critica |
| `detectada_en` | date | no |  | Fecha |
| `estado` | text (lista) | no |  | Estado · valores: abierta, en_tratamiento, cerrada |
| `verificacion` | text | sí |  | Cómo se verificó el cierre |
| `cerrada_por` | bigint | sí | `nucleo.usuario` | Quién la cerró |
| `cerrada_en` | timestamptz | sí |  | Cuándo |

### `cumplimiento.accion_correctiva` · Fase 1 · por finca · auditada

Acción para corregir una no conformidad, con responsable, plazo y verificación; se asigna como tarea.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `no_conformidad_id` | bigint | no | `cumplimiento.no_conformidad` | No conformidad |
| `descripcion` | text | no |  | Qué hacer |
| `responsable_id` | bigint | no | `nucleo.usuario` | Responsable |
| `plazo` | date | no |  | Plazo |
| `tarea_id` | bigint | sí | `personal.tarea` | Tarea |
| `estado` | text (lista) | no |  | Estado · valores: pendiente, hecha, verificada, ineficaz |
| `verificada_por` | bigint | sí | `nucleo.usuario` | Quién verificó |
| `verificada_en` | timestamptz | sí |  | Cuándo |

## Esquema `seguros`

Pólizas, bienes asegurados, índices de seguros paramétricos y avisos de siniestro con evidencia.

### `seguros.poliza` · Fase 2 · por finca · auditada

Póliza (cultivo, animales, equipos, responsabilidad civil del dron, paramétrico) con vigencia, prima, suma asegurada e incentivo de Finagro.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `numero` | varchar(40) | no |  | Número |
| `aseguradora_id` | bigint | no | `terceros.tercero` | Aseguradora |
| `corredor_id` | bigint | sí | `terceros.tercero` | Corredor |
| `tipo` | text (lista) | no |  | Tipo · valores: cultivo, animales, equipos, vehiculo, responsabilidad_civil, dron, parametrico, vida, otro |
| `desde` | date | no |  | Inicio |
| `hasta` | date | no |  | Fin |
| `prima` | numeric(14,2) | no |  | Prima total |
| `incentivo_pct` | numeric(5,2) | no |  | Porcentaje de la prima subsidiado (Incentivo al Seguro Agropecuario) |
| `valor_subsidiado` | numeric(14,2) | no |  | Valor subsidiado |
| `suma_asegurada` | numeric(14,2) | no |  | Suma asegurada |
| `deducible` | varchar(120) | sí |  | Deducible |
| `estado` | text (lista) | no |  | Estado · valores: en_tramite, vigente, vencida, cancelada |
| `avisar_dias` | smallint | no |  | Aviso antes de vencer |
| `documento_id` | bigint | sí | `documental.documento` | Póliza firmada |

### `seguros.bien_asegurado` · Fase 2 · por finca

Lo que cubre la póliza: un activo, una siembra, un lote de animales o una zona.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `poliza_id` | bigint | no | `seguros.poliza` | Póliza |
| `activo_id` | bigint | sí | `activos.activo` | Equipo |
| `siembra_id` | bigint | sí | `produccion.siembra` | Siembra |
| `lote_animal_id` | bigint | sí | `produccion.lote_animal` | Lote |
| `zona_id` | bigint | sí | `nucleo.zona` | Zona |
| `descripcion` | varchar(200) | no |  | Descripción |
| `valor_asegurado` | numeric(14,2) | no |  | Valor |

### `seguros.indice_poliza` · Fase 2 · por finca

Regla del índice de un seguro paramétrico; la decide la aseguradora con su fuente, no los sensores de la finca.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `poliza_id` | bigint | no | `seguros.poliza` | Póliza |
| `variable` | text (lista) | no |  | Variable · valores: lluvia_mm, temperatura_c, dias_secos, viento_kmh, otro |
| `fuente_oficial` | varchar(150) | no |  | Fuente que usa la aseguradora, ej. satélite CHIRPS |
| `comparador` | text (lista) | no |  | Se cumple si el valor es mayor o menor que el umbral · valores: mayor, menor |
| `umbral` | numeric(10,2) | no |  | Umbral |
| `ventana_dias` | smallint | no |  | Días acumulados |
| `sensor_id` | bigint | sí | `iot.sensor` | Sensor propio con que se compara |

### `seguros.aviso_siniestro` · Fase 2 · por finca · auditada

Aviso de posible siniestro con la serie de datos como evidencia. No hay reclamación automática: una persona lo revisa y lo envía.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `poliza_id` | bigint | no | `seguros.poliza` | Póliza |
| `indice_id` | bigint | sí | `seguros.indice_poliza` | Índice, si es paramétrico |
| `detectado_en` | timestamptz | no |  | Cuándo |
| `descripcion` | text | no |  | Qué pasó |
| `serie_datos` | jsonb | sí |  | Datos usados como evidencia |
| `estado` | text (lista) | no |  | Estado · valores: borrador, revisado, enviado, pagado, rechazado, descartado |
| `revisado_por` | bigint | sí | `nucleo.usuario` | Quién lo revisó |
| `enviado_en` | timestamptz | sí |  | Envío al corredor |
| `valor_reclamado` | numeric(14,2) | sí |  | Reclamado |
| `valor_pagado` | numeric(14,2) | sí |  | Pagado |

## Esquema `seguridad`

Doble factor, sesiones, intentos de acceso, detector de ataques, señuelos, bloqueos, alertas, incidentes, pruebas y copias de seguridad.

### `seguridad.factor_autenticacion` · Fase 1 · catálogo compartido · auditada

Segundo factor del usuario: app TOTP o llave de acceso (passkey/WebAuthn). Obligatorio para administrador y contador. El secreto vive en el gestor de secretos.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `usuario_id` | bigint | no | `nucleo.usuario` | Usuario |
| `tipo` | text (lista) | no |  | Tipo (sin biometría guardada en el servidor) · valores: totp, webauthn, codigo_respaldo |
| `nombre` | varchar(60) | no |  | Nombre del dispositivo |
| `secreto_ref` | varchar(120) | no |  | Referencia al secreto o a la llave pública |
| `activo` | boolean | no |  | En uso |
| `ultimo_uso` | timestamptz | sí |  | Último uso |

### `seguridad.sesion_usuario` · Fase 1 · catálogo compartido

Sesión iniciada: método, IP, dispositivo y vencimiento; se puede revocar en bloque ante un incidente.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `usuario_id` | bigint | no | `nucleo.usuario` | Usuario |
| `metodo` | text (lista) | no |  | Cómo se autenticó · valores: contrasena, doble_factor, llave_acceso, token_dispositivo |
| `ip` | inet | no |  | IP |
| `agente_usuario` | varchar(300) | sí |  | Navegador o app |
| `dispositivo_captura_id` | bigint | sí |  | Celular de campo registrado |
| `iniciada_en` | timestamptz | no |  | Inicio |
| `vence_en` | timestamptz | no |  | Vencimiento |
| `revocada_en` | timestamptz | sí |  | Revocación |
| `motivo_revocacion` | varchar(120) | sí |  | Motivo |

### `seguridad.intento_acceso` · Fase 1 · catálogo compartido

Cada intento de inicio de sesión, exitoso o no (solo inserción). Alimenta el detector de ataques.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `correo` | citext | no |  | Correo intentado |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Usuario, si existe |
| `ip` | inet | no |  | IP |
| `exito` | boolean | no |  | Entró |
| `motivo_fallo` | text (lista) | sí |  | Motivo del fallo · valores: contrasena, usuario_inexistente, cuenta_bloqueada, ip_bloqueada, segundo_factor, cuenta_inactiva, senuelo |
| `agente_usuario` | varchar(300) | sí |  | Navegador o app |
| `ocurrido_en` | timestamptz | no |  | Momento |

### `seguridad.regla_deteccion` · Fase 1 · catálogo compartido · auditada

Regla del detector de ataques: cuántos hechos en cuánto tiempo, severidad y respuesta automática.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(40) | no |  | Código, ej. fuerza_bruta_cuenta |
| `descripcion` | text | no |  | Qué detecta |
| `umbral` | smallint | no |  | Número de hechos |
| `ventana_min` | smallint | no |  | Minutos |
| `severidad` | text (lista) | no |  | Severidad · valores: baja, media, alta, critica |
| `respuesta` | text (lista) | no |  | Qué hace sola · valores: alertar, bloquear_ip, bloquear_cuenta, revocar_sesiones |
| `bloqueo_min` | smallint | no |  | Minutos de bloqueo |
| `activa` | boolean | no |  | Encendida |

### `seguridad.bloqueo` · Fase 1 · catálogo compartido · auditada

Bloqueo temporal de una cuenta o una IP por una regla o una persona.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Qué se bloquea · valores: cuenta, ip |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Cuenta |
| `ip` | cidr | sí |  | IP o red |
| `regla_id` | bigint | sí | `seguridad.regla_deteccion` | Regla que lo puso |
| `motivo` | varchar(200) | no |  | Motivo |
| `desde` | timestamptz | no |  | Desde |
| `hasta` | timestamptz | sí |  | Hasta; vacío = indefinido |
| `levantado_por` | bigint | sí | `nucleo.usuario` | Quién lo levantó |

### `seguridad.senuelo` · Fase 1 · catálogo compartido · auditada

Señuelo para intrusos (cuenta, llave de API o URL que nadie legítimo usa): tocarlo dispara una alerta crítica y bloquea la IP.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo · valores: cuenta, llave_api, url, registro |
| `valor` | varchar(200) | no |  | Correo, prefijo o ruta del señuelo |
| `descripcion` | varchar(200) | sí |  | Para qué está |
| `activo` | boolean | no |  | Encendido |

### `seguridad.alerta_seguridad` · Fase 1 · catálogo compartido

Hecho sospechoso detectado por las reglas, el WAF, la pasarela o la base (fuerza bruta, escalada de permisos, exportación masiva, señuelo). Solo inserción salvo su atención.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Qué pasó · valores: fuerza_bruta, relleno_credenciales, senuelo, escalada_privilegios, cambio_permisos, exportacion_masiva, acceso_ip_nueva, sesion_sin_doble_factor, inyeccion, abuso_api, dispositivo_desconocido, firmware_no_firmado, copia_fallida, otro |
| `severidad` | text (lista) | no |  | Severidad · valores: baja, media, alta, critica |
| `fuente` | text (lista) | no |  | Quién lo detectó · valores: app, base_datos, waf, api, pasarela, agente_ia, monitoreo |
| `regla_id` | bigint | sí | `seguridad.regla_deteccion` | Regla |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Usuario implicado |
| `ip` | inet | sí |  | IP |
| `detalle` | jsonb | sí |  | Datos del hecho |
| `ocurrido_en` | timestamptz | no |  | Momento |
| `estado` | text (lista) | no |  | Atención · valores: nueva, en_analisis, contenida, falso_positivo, cerrada |
| `atendida_por` | bigint | sí | `nucleo.usuario` | Quién la atendió |
| `incidente_id` | bigint | sí | `seguridad.incidente` | Incidente al que pertenece |

### `seguridad.incidente` · Fase 1 · catálogo compartido · auditada

Incidente de seguridad con su atención; si compromete datos personales se reporta a la SIC (Ley 1581).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `titulo` | varchar(200) | no |  | Título |
| `severidad` | text (lista) | no |  | Severidad · valores: baja, media, alta, critica |
| `estado` | text (lista) | no |  | Estado · valores: abierto, contenido, erradicado, cerrado |
| `responsable_id` | bigint | no | `nucleo.usuario` | Responsable |
| `datos_personales_afectados` | boolean | no |  | Hubo datos personales comprometidos |
| `reportado_sic_en` | date | sí |  | Reporte a la Superintendencia de Industria y Comercio |
| `abierto_en` | timestamptz | no |  | Apertura |
| `cerrado_en` | timestamptz | sí |  | Cierre |
| `lecciones` | text | sí |  | Lecciones aprendidas |

### `seguridad.ejecucion_prueba` · Fase 1 · catálogo compartido

Módulo de pruebas: cada corrida de pruebas (unitarias, de reglas de la base, extremo a extremo, carga, dependencias, SAST, DAST, pentest, restauración de copias) con su resultado.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo de prueba · valores: unitaria, integracion, reglas_bd, extremo_a_extremo, carga, dependencias, sast, dast, pentest, restauracion_copia, simulacro_incidente |
| `suite` | varchar(80) | no |  | Suite, ej. pruebas_reglas_v5 |
| `version_sistema` | varchar(20) | no |  | Versión probada |
| `entorno` | text (lista) | no |  | Dónde corrió (nunca pentest en producción sin aprobación) · valores: desarrollo, pruebas, practica, produccion |
| `total` | integer | no |  | Casos |
| `aprobadas` | integer | no |  | Aprobados |
| `fallidas` | integer | no |  | Fallidos |
| `hallazgos_criticos` | integer | no |  | Hallazgos críticos (seguridad) |
| `herramienta` | varchar(60) | sí |  | Herramienta, ej. pytest, pgTAP, OWASP ZAP, pip-audit |
| `informe_url` | varchar(300) | sí |  | Informe |
| `ejecutada_en` | timestamptz | no |  | Cuándo |
| `ejecutada_por` | bigint | sí | `nucleo.usuario` | Quién |

### `seguridad.copia_seguridad` · Fase 1 · catálogo compartido

Copia cifrada de la base o los archivos (regla 3-2-1) y su prueba mensual de restauración.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `alcance` | text (lista) | no |  | Qué se copió · valores: postgresql, mongodb, archivos, configuracion |
| `destino` | text (lista) | no |  | Dónde · valores: local, nube, disco_externo |
| `inicio` | timestamptz | no |  | Inicio |
| `fin` | timestamptz | sí |  | Fin |
| `tamano_mb` | numeric(12,1) | sí |  | Tamaño |
| `hash_sha256` | char(64) | sí |  | Huella |
| `cifrada` | boolean | no |  | Cifrada |
| `exitosa` | boolean | no |  | Terminó bien |
| `restauracion_probada_en` | timestamptz | sí |  | Última prueba de restauración |

## Esquema `crm`

Posibles clientes (personas y empresas), formularios de captura con autorización de datos, campañas, interacciones y oportunidades.

### `crm.segmento` · Fase 2 · por finca

Segmento de mercado (hogares, tiendas, restaurantes, hoteles, colegios, exportadores) con sus criterios: base de la palanca de mercadeo.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código |
| `nombre` | varchar(120) | no |  | Nombre |
| `criterios` | jsonb | sí |  | Criterios (municipio, tipo de negocio, volumen) |
| `propuesta_valor` | text | sí |  | Qué se le ofrece y por qué paga más |

### `crm.campana` · Fase 2 · por finca

Campaña para captar clientes: canal, segmento, presupuesto, costo real y conversiones (costo por cliente nuevo).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `nombre` | varchar(150) | no |  | Nombre |
| `canal` | text (lista) | no |  | Canal · valores: whatsapp, instagram, facebook, tiktok, feria, mercado_campesino, visita_finca, referidos, web, volanteo, otro |
| `segmento_id` | bigint | sí | `crm.segmento` | Segmento |
| `objetivo` | text | sí |  | Objetivo |
| `desde` | date | no |  | Inicio |
| `hasta` | date | sí |  | Fin |
| `presupuesto` | numeric(14,2) | no |  | Presupuesto |
| `costo_real` | numeric(14,2) | no |  | Costo real |
| `publicacion_id` | bigint | sí | `redes.publicacion` | Publicación de redes asociada |

### `crm.formulario_captura` · Fase 2 · por finca · auditada

Formulario para registrar posibles clientes (web, QR en ferias, WhatsApp) con su texto de autorización de datos y finalidad.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(30) | no |  | Código |
| `nombre` | varchar(120) | no |  | Nombre |
| `canal` | text (lista) | no |  | Dónde se usa · valores: web, qr_feria, whatsapp, tablet_finca, otro |
| `campos` | jsonb | no |  | Campos que pide (mínimos necesarios) |
| `texto_autorizacion` | text | no |  | Texto de autorización de tratamiento de datos (Ley 1581) |
| `finalidad` | text | no |  | Para qué se usarán los datos |
| `campana_id` | bigint | sí | `crm.campana` | Campaña |
| `activo` | boolean | no |  | Publicado |

### `crm.prospecto` · Fase 2 · por finca · captura sin conexión · auditada

Posible cliente, persona o empresa. No se le escribe sin autorización; al comprar se convierte en tercero y cliente.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo · valores: persona, empresa |
| `nombre` | varchar(150) | no |  | Nombre o razón social |
| `nit` | varchar(20) | sí |  | NIT de la empresa (las personas no necesitan documento para ser prospecto) |
| `sector` | text (lista) | no |  | Sector · valores: hogar, tienda, restaurante, hotel, colegio, casino, supermercado, distribuidor, exportador, agencia_turismo, institucion, otro |
| `municipio` | varchar(80) | sí |  | Municipio |
| `telefono` | varchar(20) | sí |  | Celular |
| `correo` | citext | sí |  | Correo |
| `canal_origen` | text (lista) | no |  | Cómo llegó · valores: whatsapp, instagram, facebook, tiktok, feria, mercado_campesino, visita_finca, referido, web, llamada, base_publica, otro |
| `formulario_id` | bigint | sí | `crm.formulario_captura` | Formulario por el que se registró |
| `campana_id` | bigint | sí | `crm.campana` | Campaña |
| `segmento_id` | bigint | sí | `crm.segmento` | Segmento |
| `intereses` | text[] | sí |  | Productos o servicios de interés |
| `volumen_estimado_mes` | numeric(14,2) | sí |  | Compra mensual estimada |
| `etapa` | text (lista) | no |  | Etapa del embudo · valores: nuevo, contactado, calificado, propuesta, negociacion, ganado, perdido, descartado |
| `puntaje` | smallint | no |  | Puntaje de calificación (0 a 100) |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Vendedor responsable |
| `consentimiento_id` | bigint | sí | `terceros.consentimiento_datos` | Autorización de datos; sin ella solo se guarda la empresa (datos públicos), no se contacta |
| `tercero_id` | bigint | sí | `terceros.tercero` | Tercero al convertirse en cliente |
| `motivo_perdida` | varchar(200) | sí |  | Por qué se perdió |
| `proximo_contacto` | date | sí |  | Próximo contacto |

### `crm.contacto_empresa` · Fase 2 · por finca

Persona de contacto dentro de una empresa prospecto (compras, chef, administrador), con su propia autorización.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `prospecto_id` | bigint | no | `crm.prospecto` | Empresa |
| `nombre` | varchar(150) | no |  | Nombre |
| `cargo` | varchar(80) | sí |  | Cargo |
| `telefono` | varchar(20) | sí |  | Celular |
| `correo` | citext | sí |  | Correo |
| `consentimiento_id` | bigint | sí | `terceros.consentimiento_datos` | Autorización |

### `crm.interaccion` · Fase 2 · por finca · captura sin conexión

Contacto con un prospecto o cliente (llamada, WhatsApp, visita, degustación, feria) y su próximo paso.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `prospecto_id` | bigint | sí | `crm.prospecto` | Prospecto |
| `tercero_id` | bigint | sí | `terceros.tercero` | Cliente existente |
| `tipo` | text (lista) | no |  | Tipo · valores: llamada, whatsapp, visita, correo, reunion, degustacion, feria, visita_finca |
| `fecha` | timestamptz | no |  | Cuándo |
| `resumen` | text | no |  | Qué se habló |
| `proximo_paso` | varchar(200) | sí |  | Próximo paso |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Quién |
| `agente_id` | bigint | sí | `ia.agente` | Agente, si la atendió uno |

### `crm.oportunidad` · Fase 2 · por finca

Negocio posible con un prospecto o cliente: productos, valor, probabilidad y fecha de cierre (proyección del embudo).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `prospecto_id` | bigint | sí | `crm.prospecto` | Prospecto |
| `tercero_id` | bigint | sí | `terceros.tercero` | Cliente |
| `titulo` | varchar(150) | no |  | Título |
| `productos` | jsonb | sí |  | Productos y cantidades |
| `valor_estimado` | numeric(14,2) | no |  | Valor estimado |
| `probabilidad_pct` | smallint | no |  | Probabilidad de cierre |
| `cierre_estimado` | date | sí |  | Fecha estimada |
| `estado` | text (lista) | no |  | Estado · valores: abierta, ganada, perdida |
| `pedido_id` | bigint | sí | `comercial.pedido` | Pedido que la cerró |
| `linea_negocio_id` | bigint | sí | `estrategia.linea_negocio` | Línea de negocio |

## Esquema `estrategia`

Líneas de negocio, DOFA, estudios de mercado, iniciativas de crecimiento, evaluación de proyectos (VPN, TIR, ROI, palancas) y reinversión de utilidades.

### `estrategia.linea_negocio` · Fase 2 · por finca

Línea de negocio de la finca (avícola, piscícola, perennes, turismo…) o una nueva en estudio, unida a su centro de costo.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código |
| `nombre` | varchar(120) | no |  | Nombre |
| `centro_costo_id` | bigint | sí | `finanzas.centro_costo` | Centro de costo |
| `estado` | text (lista) | no |  | Estado · valores: actual, en_estudio, piloto, descartada, cerrada |
| `palanca_dominante` | text (lista) | sí |  | Palanca con la que genera recursos · valores: mercadeo, produccion, operacional, financiera |
| `descripcion` | text | sí |  | Descripción |

### `estrategia.factor_dofa` · Fase 2 · por finca

Debilidad, oportunidad, fortaleza o amenaza de la finca o de una línea, con su fuente.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo · valores: debilidad, oportunidad, fortaleza, amenaza |
| `linea_negocio_id` | bigint | sí | `estrategia.linea_negocio` | Línea (vacío = toda la finca) |
| `descripcion` | text | no |  | Descripción |
| `impacto` | smallint | no |  | Impacto 1 a 5 |
| `fuente` | varchar(200) | sí |  | Fuente |
| `vigente` | boolean | no |  | Vigente |

### `estrategia.estudio_mercado` · Fase 2 · por finca

Dato de un mercado posible: tamaño, precio de referencia, competidores y fuente (SIPSA, DANE, gremios, visitas).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `mercado` | varchar(150) | no |  | Mercado, ej. huevo campesino en hoteles de Girardot |
| `segmento_id` | bigint | sí | `crm.segmento` | Segmento |
| `tamano_estimado` | numeric(14,2) | sí |  | Ventas anuales estimadas del mercado |
| `precio_referencia` | numeric(14,2) | sí |  | Precio de referencia |
| `competidores` | text | sí |  | Competidores |
| `barreras` | text | sí |  | Barreras de entrada (registros, certificaciones, frío) |
| `fuente` | varchar(200) | no |  | Fuente |
| `fecha` | date | no |  | Fecha del dato |

### `estrategia.iniciativa` · Fase 2 · por finca · auditada

Idea de crecimiento: nuevo mercado, producto, canal o negocio, clasificada por la matriz de Ansoff y por la palanca que usa. La IA puede proponerla; decide la familia.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `titulo` | varchar(200) | no |  | Título |
| `descripcion` | text | no |  | Descripción |
| `ansoff` | text (lista) | no |  | Cuadrante de la matriz de Ansoff · valores: penetracion_mercado, desarrollo_mercado, desarrollo_producto, diversificacion |
| `tipo` | text (lista) | no |  | Tipo · valores: nuevo_mercado, nuevo_producto, nuevo_canal, nueva_linea, valor_agregado, integracion_vertical, mejora_proceso |
| `palanca` | text (lista) | no |  | Palanca principal · valores: mercadeo, produccion, operacional, financiera |
| `linea_negocio_id` | bigint | sí | `estrategia.linea_negocio` | Línea existente o nueva |
| `segmento_id` | bigint | sí | `crm.segmento` | Segmento al que apunta |
| `hipotesis` | text | sí |  | Qué se cree y cómo se probará |
| `estado` | text (lista) | no |  | Estado · valores: idea, en_evaluacion, aprobada, piloto, escalada, descartada |
| `propuesta_por` | bigint | sí | `nucleo.usuario` | Quién la propuso |
| `agente_id` | bigint | sí | `ia.agente` | Agente que la propuso |
| `aprobada_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó (persona) |
| `aprobada_en` | timestamptz | sí |  | Cuándo |
| `puntaje` | numeric(5,2) | sí |  | Puntaje de priorización |

### `estrategia.evaluacion_proyecto` · Fase 2 · por finca · auditada

Evaluación financiera de una iniciativa: inversión, flujos, VPN, TIR, ROI, recuperación, punto de equilibrio, margen de seguridad y grados de palanca. La calcula la base.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `iniciativa_id` | bigint | no | `estrategia.iniciativa` | Iniciativa |
| `version` | smallint | no |  | Versión |
| `inversion_inicial` | numeric(14,2) | no |  | Inversión inicial |
| `horizonte_meses` | smallint | no |  | Horizonte |
| `tasa_descuento_anual` | numeric(6,4) | no |  | Costo de capital (tasa de oportunidad) anual |
| `precio_unitario` | numeric(14,2) | sí |  | Precio de venta por unidad |
| `costo_variable_unitario` | numeric(14,2) | sí |  | Costo variable por unidad |
| `costos_fijos_mes` | numeric(14,2) | sí |  | Costos fijos operacionales del mes |
| `intereses_mes` | numeric(14,2) | no |  | Intereses del mes si se financia con deuda |
| `unidades_mes` | numeric(12,2) | sí |  | Unidades esperadas por mes |
| `fuente_fondos` | text (lista) | no |  | De dónde sale la plata · valores: utilidades_retenidas, credito, fondo_emprender, aporte_familia, mixto |
| `vpn` | numeric(14,2) | sí |  | Valor presente neto |
| `tir_anual` | numeric(8,4) | sí |  | Tasa interna de retorno anual |
| `roi_pct` | numeric(8,2) | sí |  | Retorno sobre la inversión en el horizonte |
| `recuperacion_meses` | smallint | sí |  | Meses para recuperar la inversión |
| `punto_equilibrio_unidades` | numeric(12,2) | sí |  | Unidades por mes para no perder |
| `margen_seguridad_pct` | numeric(8,2) | sí |  | Cuánto pueden caer las ventas sin pérdida |
| `gpo` | numeric(10,4) | sí |  | Grado de palanca operativa |
| `gpf` | numeric(10,4) | sí |  | Grado de palanca financiera |
| `gpt` | numeric(10,4) | sí |  | Grado de palanca total |
| `riesgos` | text | sí |  | Riesgos (costos fijos, deuda, precio) |
| `calculado_en` | timestamptz | sí |  | Cuándo se calculó |

### `estrategia.flujo_proyecto` · Fase 2 · por finca

Flujo de caja proyectado de una evaluación por mes (mes 0 = inversión).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `evaluacion_id` | bigint | no | `estrategia.evaluacion_proyecto` | Evaluación |
| `mes` | smallint | no |  | Mes (0 = inversión) |
| `ingresos` | numeric(14,2) | no |  | Ingresos |
| `egresos` | numeric(14,2) | no |  | Egresos |
| `inversion` | numeric(14,2) | no |  | Inversión |

### `estrategia.reinversion` · Fase 2 · por finca · auditada

Parte de la utilidad de una línea que se destina a una iniciativa (apalancarse con lo ganado). Nunca de una línea con pérdida ni por encima del tope de reinversión.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `anio` | smallint | no |  | Año de la utilidad |
| `mes` | smallint | no |  | Mes de la utilidad |
| `linea_origen_id` | bigint | no | `estrategia.linea_negocio` | Línea que generó la utilidad |
| `utilidad_linea` | numeric(14,2) | no |  | Utilidad neta de la línea en el mes (de la contabilidad) |
| `valor` | numeric(14,2) | no |  | Valor reinvertido |
| `iniciativa_id` | bigint | no | `estrategia.iniciativa` | Iniciativa destino |
| `estado` | text (lista) | no |  | Estado · valores: propuesta, aprobada, ejecutada, cancelada |
| `aprobada_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |

### `estrategia.seguimiento_iniciativa` · Fase 2 · por finca

Resultado real mes a mes de una iniciativa en piloto o escalada, contra lo proyectado: así se mide el retorno de verdad.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `iniciativa_id` | bigint | no | `estrategia.iniciativa` | Iniciativa |
| `mes` | date | no |  | Mes |
| `ingresos_reales` | numeric(14,2) | no |  | Ingresos |
| `egresos_reales` | numeric(14,2) | no |  | Egresos |
| `unidades_reales` | numeric(12,2) | sí |  | Unidades |
| `nota` | text | sí |  | Aprendizajes |

### `estrategia.objetivo` · Fase 2 · por finca

Objetivo estratégico por perspectiva del cuadro de mando (financiera, clientes, procesos, aprendizaje), con indicador y meta.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `perspectiva` | text (lista) | no |  | Perspectiva · valores: financiera, clientes, procesos, aprendizaje |
| `descripcion` | text | no |  | Objetivo |
| `indicador_id` | bigint | sí | `finanzas.indicador` | Indicador |
| `meta` | numeric(18,4) | sí |  | Meta |
| `fecha_meta` | date | sí |  | Para cuándo |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Responsable |

## Esquema `agenda`

Recursos agendables (cabañas, salón, vehículos, equipos), calendario sin cruces, visitas programadas e ingresos y salidas de personas y vehículos.

### `agenda.recurso` · Fase 3 · por finca

Lo que se agenda: cabañas, salón, zona de camping, vehículo, equipo, punto de cargue. Cada recurso tiene su calendario sin cruces.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código |
| `nombre` | varchar(120) | no |  | Nombre |
| `tipo` | text (lista) | no |  | Tipo · valores: cabana, salon, zona_camping, vehiculo, equipo, punto_cargue, sala, otro |
| `alojamiento_id` | bigint | sí | `turismo.alojamiento` | Cabaña de turismo que representa |
| `activo_id` | bigint | sí | `activos.activo` | Equipo o vehículo que representa |
| `zona_id` | bigint | sí | `nucleo.zona` | Ubicación |
| `capacidad` | smallint | sí |  | Capacidad |
| `minutos_preparacion` | smallint | no |  | Tiempo de alistamiento o limpieza que se bloquea después de cada uso |
| `activo` | boolean | no |  | En uso |

### `agenda.cita` · Fase 3 · por finca · auditada

Bloque del calendario de un recurso (reserva, limpieza, mantenimiento, uso familiar, entrega). La base impide cruces, contando el alistamiento.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `recurso_id` | bigint | no | `agenda.recurso` | Recurso |
| `titulo` | varchar(150) | no |  | Título |
| `tipo` | text (lista) | no |  | Tipo · valores: reserva_turistica, limpieza, mantenimiento, uso_familiar, bloqueo, entrega_proveedor, recogida_cliente, capacitacion, auditoria, reunion, otro |
| `inicio` | timestamptz | no |  | Inicio |
| `fin` | timestamptz | no |  | Fin |
| `fin_con_preparacion` | timestamptz | sí |  | Fin más el alistamiento del recurso (lo calcula la base) |
| `estado` | text (lista) | no |  | Estado · valores: tentativa, confirmada, cumplida, cancelada |
| `reserva_id` | bigint | sí | `turismo.reserva` | Reserva de turismo |
| `bloqueo_id` | bigint | sí | `turismo.bloqueo_calendario` | Bloqueo del calendario |
| `tarea_id` | bigint | sí | `personal.tarea` | Tarea asociada (limpieza, mantenimiento) |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Responsable |
| `notas` | text | sí |  | Notas |

### `agenda.visita` · Fase 2 · por finca · auditada

Ingreso programado de una persona o un vehículo (proveedor, cliente, turista, técnico, autoridad): se aprueba antes, entrega un pase QR y exige bioseguridad si va al galpón.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `tipo` | text (lista) | no |  | Tipo de visitante · valores: proveedor, cliente, turista, contratista, tecnico, autoridad, visitante, transportador |
| `nombre` | varchar(150) | no |  | Nombre de la persona o empresa |
| `tercero_id` | bigint | sí | `terceros.tercero` | Tercero, si está registrado |
| `personas` | smallint | no |  | Número de personas |
| `vehiculo_placa` | varchar(10) | sí |  | Placa del vehículo |
| `vehiculo_tipo` | text (lista) | sí |  | Tipo de vehículo · valores: carro, camioneta, camion, moto, tractor, bicicleta |
| `motivo` | varchar(200) | no |  | Motivo |
| `zona_destino_id` | bigint | sí | `nucleo.zona` | Zona a la que va |
| `ingreso_programado` | timestamptz | no |  | Hora de llegada |
| `salida_programada` | timestamptz | no |  | Hora de salida |
| `anfitrion_id` | bigint | no | `nucleo.usuario` | Quién lo recibe |
| `requiere_bioseguridad` | boolean | no |  | Entra a una zona de bioseguridad (galpón) |
| `contacto_aves_reciente` | boolean | sí |  | Declaró contacto con otras aves en las últimas horas del parámetro cuarentena_aves_horas |
| `pase_hash` | char(64) | sí |  | Huella del código QR del pase |
| `estado` | text (lista) | no |  | Estado · valores: solicitada, aprobada, rechazada, en_sitio, salio, no_llego, cancelada |
| `aprobada_por` | bigint | sí | `nucleo.usuario` | Quién la aprobó |
| `motivo_rechazo` | varchar(200) | sí |  | Motivo del rechazo |
| `cita_id` | bigint | sí | `agenda.cita` | Cita de cargue o descargue, si aplica |

### `agenda.registro_acceso` · Fase 2 · por finca · captura sin conexión

Cada entrada o salida real por la portería (persona o vehículo): con pase, carné QR o NFC, a mano o por lectura de placa. Funciona sin internet y alimenta la jornada.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `sentido` | text (lista) | no |  | Entrada o salida · valores: entrada, salida |
| `tipo` | text (lista) | no |  | Qué pasa · valores: persona, vehiculo |
| `visita_id` | bigint | sí | `agenda.visita` | Visita programada |
| `empleado_id` | bigint | sí | `terceros.empleado` | Trabajador |
| `nombre` | varchar(150) | sí |  | Nombre (si no es visita ni trabajador) |
| `placa` | varchar(10) | sí |  | Placa |
| `punto` | varchar(40) | no |  | Punto de control |
| `metodo` | text (lista) | no |  | Cómo se identificó · valores: pase_qr, carne_qr, carne_nfc, manual, lectura_placa |
| `desinfeccion` | boolean | no |  | Pasó por desinfección (personas y vehículos que van al galpón) |
| `ocurrido_en` | timestamptz | no |  | Momento |
| `registrado_por` | bigint | sí | `nucleo.usuario` | Portero o encargado |
| `observacion` | varchar(200) | sí |  | Novedad o motivo de la corrección (los registros no se editan: se corrige con uno nuevo) |
| `corrige_id` | bigint | sí | `agenda.registro_acceso` | Registro que este corrige (error de digitación) |

## Esquema `proyectos`

Dirección de proyectos (PMBOK 8): acta, interesados, EDT, cronograma con ruta crítica, iteraciones, riesgos, cambios, líneas base y valor ganado.

### `proyectos.proyecto` · Fase 2 · por finca · auditada

Proyecto de la finca (nuevo galpón, sistema solar, cabañas, certificación, piloto de robot) con acta de constitución, enfoque predictivo, adaptativo o híbrido y área de enfoque actual.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `codigo` | varchar(20) | no |  | Código, ej. PRY-GAL-500 |
| `nombre` | varchar(200) | no |  | Nombre |
| `objetivo` | text | no |  | Objetivo (resultado y valor esperado) |
| `justificacion` | text | sí |  | Por qué (caso de negocio) |
| `criterios_exito` | text | sí |  | Cómo se sabrá que salió bien |
| `iniciativa_id` | bigint | sí | `estrategia.iniciativa` | Iniciativa de negocio que lo origina |
| `linea_negocio_id` | bigint | sí | `estrategia.linea_negocio` | Línea |
| `enfoque` | text (lista) | no |  | Enfoque de desarrollo · valores: predictivo, adaptativo, hibrido |
| `area_enfoque` | text (lista) | no |  | Área de enfoque en que está · valores: inicio, planificacion, ejecucion, monitoreo_control, cierre |
| `estado` | text (lista) | no |  | Estado · valores: propuesto, aprobado, en_curso, suspendido, cerrado, cancelado |
| `patrocinador_id` | bigint | sí | `nucleo.usuario` | Patrocinador (quien aprueba y responde por el valor) |
| `director_id` | bigint | sí | `nucleo.usuario` | Director del proyecto |
| `presupuesto` | numeric(14,2) | sí |  | Presupuesto al concluir (BAC) de la línea base vigente |
| `fuente_fondos` | text (lista) | sí |  | Financiación · valores: utilidades_retenidas, credito, fondo_emprender, aporte_familia, convenio, mixto |
| `inicio_plan` | date | sí |  | Inicio planeado |
| `fin_plan` | date | sí |  | Fin planeado |
| `inicio_real` | date | sí |  | Inicio real |
| `fin_real` | date | sí |  | Fin real |
| `acta_documento_id` | bigint | sí | `documental.documento` | Acta de constitución firmada |
| `aprobado_por` | bigint | sí | `nucleo.usuario` | Quién lo aprobó |
| `aprobado_en` | timestamptz | sí |  | Cuándo |

### `proyectos.interesado` · Fase 2 · por finca

Interesado del proyecto con su interés, influencia y estrategia de relación (dominio de interesados).

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `tercero_id` | bigint | sí | `terceros.tercero` | Persona o entidad |
| `usuario_id` | bigint | sí | `nucleo.usuario` | Usuario interno |
| `nombre` | varchar(150) | no |  | Nombre o rol |
| `rol` | varchar(80) | sí |  | Rol en el proyecto |
| `interes` | smallint | no |  | Interés 1 a 5 |
| `influencia` | smallint | no |  | Influencia 1 a 5 |
| `estrategia` | varchar(30) | sí |  | gestionar_de_cerca, mantener_satisfecho, mantener_informado o monitorear (la calcula la base) |
| `expectativas` | text | sí |  | Qué espera |

### `proyectos.elemento_edt` · Fase 2 · por finca · auditada

Estructura de desglose del trabajo (EDT): entregables y paquetes de trabajo con su criterio de aceptación.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `padre_id` | bigint | sí | `proyectos.elemento_edt` | Elemento superior |
| `codigo` | varchar(20) | no |  | Código EDT, ej. 1.2.3 |
| `nombre` | varchar(200) | no |  | Nombre |
| `es_entregable` | boolean | no |  | Es un entregable que se acepta |
| `criterio_aceptacion` | text | sí |  | Cómo se acepta |
| `estado` | text (lista) | no |  | Estado · valores: pendiente, en_curso, terminado, aceptado, rechazado |
| `aceptado_por` | bigint | sí | `nucleo.usuario` | Quién lo aceptó |
| `aceptado_en` | timestamptz | sí |  | Cuándo |

### `proyectos.iteracion` · Fase 2 · por finca

Iteración o sprint para la parte adaptativa del proyecto.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `numero` | smallint | no |  | Número |
| `objetivo` | text | sí |  | Objetivo de la iteración |
| `inicio` | date | no |  | Inicio |
| `fin` | date | no |  | Fin |
| `estado` | text (lista) | no |  | Estado · valores: planeada, en_curso, cerrada |
| `retrospectiva` | text | sí |  | Qué se aprendió |

### `proyectos.actividad` · Fase 2 · por finca

Actividad del cronograma (o historia de la iteración) con duración, fechas, avance, costo y responsable; la ruta crítica la calcula la base.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `elemento_edt_id` | bigint | sí | `proyectos.elemento_edt` | Paquete de trabajo |
| `iteracion_id` | bigint | sí | `proyectos.iteracion` | Iteración |
| `codigo` | varchar(20) | no |  | Código |
| `nombre` | varchar(200) | no |  | Nombre |
| `es_hito` | boolean | no |  | Hito (duración 0) |
| `duracion_dias` | smallint | no |  | Duración en días |
| `inicio_temprano` | smallint | sí |  | Día de inicio temprano (CPM, desde el día 0) |
| `fin_temprano` | smallint | sí |  | Día de fin temprano |
| `inicio_tardio` | smallint | sí |  | Día de inicio tardío |
| `fin_tardio` | smallint | sí |  | Día de fin tardío |
| `holgura` | smallint | sí |  | Holgura total en días |
| `critica` | boolean | no |  | Está en la ruta crítica |
| `inicio_plan` | date | sí |  | Inicio planeado |
| `fin_plan` | date | sí |  | Fin planeado |
| `inicio_real` | date | sí |  | Inicio real |
| `fin_real` | date | sí |  | Fin real |
| `avance_pct` | numeric(5,2) | no |  | Avance físico |
| `costo_plan` | numeric(14,2) | no |  | Costo planeado |
| `costo_real` | numeric(14,2) | no |  | Costo real |
| `responsable_id` | bigint | sí | `terceros.empleado` | Responsable |
| `area_id` | bigint | sí | `personal.area_responsabilidad` | Área de responsabilidad |
| `tarea_id` | bigint | sí | `personal.tarea` | Tarea de campo que la ejecuta |

### `proyectos.dependencia` · Fase 2 · por finca

Relación entre actividades (fin a comienzo, comienzo a comienzo, fin a fin, comienzo a fin) con adelanto o retraso.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `predecesora_id` | bigint | no | `proyectos.actividad` | Actividad predecesora |
| `sucesora_id` | bigint | no | `proyectos.actividad` | Actividad sucesora |
| `tipo` | text (lista) | no |  | Tipo de relación · valores: FC, CC, FF, CF |
| `desfase_dias` | smallint | no |  | Adelanto (negativo) o retraso (positivo) |

### `proyectos.riesgo` · Fase 2 · por finca · auditada

Riesgo del proyecto (amenaza u oportunidad) con probabilidad, impacto, respuesta y responsable.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `descripcion` | text | no |  | Causa, riesgo y efecto |
| `tipo` | text (lista) | no |  | Tipo · valores: amenaza, oportunidad |
| `categoria` | text (lista) | no |  | Categoría · valores: tecnico, clima, sanitario, mercado, financiero, legal, personas, proveedor, seguridad |
| `probabilidad` | smallint | no |  | 1 a 5 |
| `impacto` | smallint | no |  | 1 a 5 |
| `severidad` | smallint generated always as (probabilidad * impacto) stored | sí |  | Probabilidad × impacto (1 a 25) |
| `respuesta` | text (lista) | sí |  | Estrategia de respuesta · valores: evitar, mitigar, transferir, aceptar, escalar, explotar, mejorar, compartir |
| `plan_respuesta` | text | sí |  | Qué se hará |
| `disparador` | varchar(200) | sí |  | Señal de que se está materializando |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Dueño del riesgo |
| `estado` | text (lista) | no |  | Estado · valores: identificado, en_respuesta, materializado, cerrado |

### `proyectos.registro` · Fase 2 · por finca

Registro de incidentes, supuestos, restricciones, decisiones y lecciones aprendidas del proyecto.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `tipo` | text (lista) | no |  | Tipo · valores: incidente, supuesto, restriccion, decision, leccion_aprendida |
| `descripcion` | text | no |  | Descripción |
| `responsable_id` | bigint | sí | `nucleo.usuario` | Responsable |
| `estado` | text (lista) | no |  | Estado · valores: abierto, cerrado |
| `fecha` | date | no |  | Fecha |

### `proyectos.solicitud_cambio` · Fase 2 · por finca · auditada

Solicitud de cambio al alcance, cronograma o costo; la aprueba una persona distinta de quien la pide y, si se aprueba, crea una nueva línea base.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `descripcion` | text | no |  | Qué cambia y por qué |
| `solicitada_por` | bigint | no | `nucleo.usuario` | Quién la pide |
| `impacto_alcance` | text | sí |  | Impacto en el alcance |
| `impacto_dias` | smallint | no |  | Días que agrega o quita |
| `impacto_costo` | numeric(14,2) | no |  | Costo que agrega o quita |
| `estado` | text (lista) | no |  | Estado · valores: propuesta, aprobada, rechazada |
| `decidida_por` | bigint | sí | `nucleo.usuario` | Quién decidió |
| `decidida_en` | timestamptz | sí |  | Cuándo |

### `proyectos.linea_base` · Fase 2 · por finca · auditada

Línea base aprobada de alcance, cronograma y costo; no se edita: cada cambio aprobado crea una versión nueva.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `version` | smallint | no |  | Versión |
| `presupuesto` | numeric(14,2) | no |  | BAC |
| `fin_plan` | date | no |  | Fecha de fin |
| `alcance` | text | no |  | Resumen del alcance |
| `solicitud_cambio_id` | bigint | sí | `proyectos.solicitud_cambio` | Cambio que la originó |
| `aprobada_por` | bigint | no | `nucleo.usuario` | Quién la aprobó |

### `proyectos.medicion_valor_ganado` · Fase 2 · por finca

Medición del desempeño en una fecha de corte por valor ganado: PV, EV, AC, CPI, SPI, EAC, ETC y VAC.

| Campo | Tipo | Vacío | Referencia | Significado |
| --- | --- | --- | --- | --- |
| `proyecto_id` | bigint | no | `proyectos.proyecto` | Proyecto |
| `fecha_corte` | date | no |  | Fecha de corte |
| `pv` | numeric(14,2) | no |  | Valor planificado |
| `ev` | numeric(14,2) | no |  | Valor ganado |
| `ac` | numeric(14,2) | no |  | Costo real |
| `cpi` | numeric(8,4) | sí |  | Índice de desempeño del costo (EV/AC) |
| `spi` | numeric(8,4) | sí |  | Índice de desempeño del cronograma (EV/PV) |
| `eac` | numeric(14,2) | sí |  | Estimación a la conclusión (BAC/CPI) |
| `etc` | numeric(14,2) | sí |  | Estimación hasta concluir (EAC − AC) |
| `vac` | numeric(14,2) | sí |  | Variación a la conclusión (BAC − EAC) |
