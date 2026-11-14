-- GuayacanERP · Esquema PostgreSQL v5 para PostgreSQL 18 (generado desde modelo.py + reglas_negocio.sql; no editar a mano)
-- Multi-finca con seguridad por filas, captura sin conexión idempotente, auditoría automática,
-- kardex como única fuente de existencias, vencimiento estimado y salida FEFO, cuadre contable,
-- cadena de frío, retiro de lotes, cartera, permuta, seguridad perimetral, cámaras y funciones por finca;
-- v5: personal y cronogramas 24/7, nómina, formación, activos, documental, cumplimiento, seguros, agenda, proyectos,
-- seguridad informática, CRM, estrategia y finanzas (costos, estados, indicadores, palancas).
create extension if not exists citext;
create extension if not exists btree_gist;
create extension if not exists postgis;
create extension if not exists vector;

create schema if not exists nucleo;
comment on schema nucleo is 'Usuarios, roles, permisos, parámetros con vigencia, auditoría, predio y zonas, eventos de integración';
create schema if not exists terceros;
comment on schema terceros is 'Personas y empresas con las que se relaciona la finca: clientes, proveedores, empleados y su consentimiento de datos';
create schema if not exists produccion;
comment on schema produccion is 'Producción animal (aves, ovinos, caprinos, peces, abejas, lombrices) y agrícola (siembras, labores, cosechas, suelo)';
create schema if not exists riego;
comment on schema riego is 'Fuentes de agua, tanques, sistemas de riego, válvulas y eventos de riego (manual hoy, automático en la fase IoT)';
create schema if not exists inventario;
comment on schema inventario is 'Catálogo de productos, bodegas, lotes de inventario y kardex de movimientos';
create schema if not exists comercial;
comment on schema comercial is 'Precios con vigencia, propuestas de precio, pedidos, facturas, pagos y entregas';
create schema if not exists compras;
comment on schema compras is 'Órdenes de compra, cotizaciones de proveedores y precios de mercado de referencia';
create schema if not exists finanzas;
comment on schema finanzas is 'Plan de cuentas (PUC), centros de costo, comprobantes y movimientos contables';
create schema if not exists ia;
comment on schema ia is 'Agentes, herramientas, aprobaciones, base de conocimiento, recomendaciones, evaluaciones y consumo de IA';
create schema if not exists redes;
comment on schema redes is 'Cuentas de redes sociales y publicaciones con su flujo de aprobación';
create schema if not exists turismo;
comment on schema turismo is 'Alojamientos, planes turísticos y reservas (fase 3)';
create schema if not exists iot;
comment on schema iot is 'Red local de la finca: dispositivos, sensores, actuadores, reglas, seguridad perimetral y cámaras (fase 4, con diseño listo desde ya)';
create schema if not exists ambiental;
comment on schema ambiental is 'Mediciones ambientales (energía solar, biogás, compost, agua) y factores de emisión con su fuente';
create schema if not exists personal;
comment on schema personal is 'Tareas, plan de labores, cuadrillas, turnos, ausencias (sin diagnósticos), matriz de responsabilidades, equipos asignados, carné QR o NFC y jornada';
create schema if not exists nomina;
comment on schema nomina is 'Conceptos, periodos, novedades, liquidación, prestaciones, PILA, nómina electrónica (apagada) y pagos con doble aprobación';
create schema if not exists formacion;
comment on schema formacion is 'Cursos, lecciones, evaluaciones, sesiones presenciales, certificados y habilitaciones que permiten asignar tareas';
create schema if not exists activos;
comment on schema activos is 'Hoja de vida de equipos, planes y órdenes de mantenimiento, uso, repuestos y depreciación';
create schema if not exists documental;
comment on schema documental is 'Documentos con versiones, aprobación, vencimiento y vínculos; los agentes solo leen la versión aprobada y vigente';
create schema if not exists cumplimiento;
comment on schema cumplimiento is 'Normas (granja avícola biosegura, BPA, GLOBALG.A.P.), requisitos, expediente, evidencias, auditorías y acciones correctivas';
create schema if not exists seguros;
comment on schema seguros is 'Pólizas, bienes asegurados, índices de seguros paramétricos y avisos de siniestro con evidencia';
create schema if not exists seguridad;
comment on schema seguridad is 'Doble factor, sesiones, intentos de acceso, detector de ataques, señuelos, bloqueos, alertas, incidentes, pruebas y copias de seguridad';
create schema if not exists crm;
comment on schema crm is 'Posibles clientes (personas y empresas), formularios de captura con autorización de datos, campañas, interacciones y oportunidades';
create schema if not exists estrategia;
comment on schema estrategia is 'Líneas de negocio, DOFA, estudios de mercado, iniciativas de crecimiento, evaluación de proyectos (VPN, TIR, ROI, palancas) y reinversión de utilidades';
create schema if not exists agenda;
comment on schema agenda is 'Recursos agendables (cabañas, salón, vehículos, equipos), calendario sin cruces, visitas programadas e ingresos y salidas de personas y vehículos';
create schema if not exists proyectos;
comment on schema proyectos is 'Dirección de proyectos (PMBOK 8): acta, interesados, EDT, cronograma con ruta crítica, iteraciones, riesgos, cambios, líneas base y valor ganado';

-- ============================================================================
-- GuayacanERP · Reglas de negocio en la base de datos (escritas a mano)
-- El generador inserta la primera parte antes de crear las tablas y la segunda después.
-- ============================================================================

-- Sesión: la API fija estos valores al inicio de cada transacción:
--   select set_config('app.predio_id', '<id>', true), set_config('app.usuario_id', '<id>', true),
--          set_config('app.agente_id', '<id o vacío>', true);
create or replace function nucleo.predio_actual() returns bigint language sql stable as
$$ select nullif(current_setting('app.predio_id', true), '')::bigint $$;
create or replace function nucleo.usuario_actual() returns bigint language sql stable as
$$ select nullif(current_setting('app.usuario_id', true), '')::bigint $$;
create or replace function nucleo.agente_actual() returns bigint language sql stable as
$$ select nullif(current_setting('app.agente_id', true), '')::bigint $$;
comment on function nucleo.predio_actual() is 'Finca de la sesión; base de la seguridad por filas';

create or replace function nucleo.marcar_actualizado() returns trigger language plpgsql as
$$ begin new.actualizado_en := now(); return new; end $$;

-- Particiones mensuales (auditoría y lecturas IoT): una tarea mensual crea las siguientes con nucleo.mantener_particiones()
create or replace function nucleo.crear_particion_mensual(p_tabla text, p_mes date) returns text language plpgsql as $$
declare v_ini date := date_trunc('month', p_mes)::date; v_fin date := (date_trunc('month', p_mes) + interval '1 month')::date;
        v_nombre text := p_tabla || '_' || to_char(date_trunc('month', p_mes), 'YYYYMM');
begin
  if to_regclass(v_nombre) is null then
    execute format('create table %s partition of %s for values from (%L) to (%L)', v_nombre, p_tabla, v_ini, v_fin);
    if exists (select 1 from pg_roles where rolname = 'guayacan_app') then
      execute format('revoke all on %s from guayacan_app', v_nombre);
    end if;
  end if;
  return v_nombre;
end $$;
comment on function nucleo.crear_particion_mensual(text, date) is 'Crea la partición de un mes; la aplicación solo accede por la tabla madre, así la seguridad por filas siempre aplica';



create table nucleo.usuario (
    id bigint generated always as identity primary key,
    nombre_completo varchar(150) not null,
    correo citext not null unique,
    telefono varchar(20),
    contrasena_hash varchar(255) not null,
    es_superusuario boolean not null default false,
    activo boolean not null default true,
    ultimo_ingreso timestamptz,
    tercero_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table nucleo.rol (
    id bigint generated always as identity primary key,
    codigo varchar(40) not null unique,
    nombre varchar(80) not null,
    descripcion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table nucleo.permiso (
    id bigint generated always as identity primary key,
    codigo varchar(80) not null unique,
    nombre varchar(120) not null,
    modulo varchar(40) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table nucleo.rol_permiso (
    id bigint generated always as identity primary key,
    rol_id bigint not null,
    permiso_id bigint not null,
    unique (rol_id, permiso_id)
);

create table nucleo.usuario_rol (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    usuario_id bigint not null,
    rol_id bigint not null,
    unique (predio_id, id),
    unique (predio_id, usuario_id, rol_id)
);

create table nucleo.parametro (
    id bigint generated always as identity primary key,
    predio_id bigint,
    clave varchar(80) not null,
    valor text not null,
    tipo_dato text not null constraint ck_parametro_tipo_dato check (tipo_dato in ('entero', 'decimal', 'porcentaje', 'dinero', 'texto', 'booleano', 'json')),
    vigente_desde date not null,
    vigente_hasta date,
    descripcion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique nulls not distinct (predio_id, clave, vigente_desde)
);

create table nucleo.auditoria (
    id bigint generated always as identity,
    predio_id bigint default nucleo.predio_actual(),
    esquema_tabla varchar(80) not null,
    registro_id bigint not null,
    accion text not null constraint ck_auditoria_accion check (accion in ('crear', 'actualizar', 'eliminar', 'aprobar', 'rechazar', 'iniciar_sesion', 'exportar')),
    datos_antes jsonb,
    datos_despues jsonb,
    usuario_id bigint,
    agente_id bigint,
    direccion_ip inet,
    ocurrido_en timestamptz not null default now(),
    primary key (id, ocurrido_en)
) partition by range (ocurrido_en);

create table nucleo.auditoria_por_defecto partition of nucleo.auditoria default;
select nucleo.crear_particion_mensual('nucleo.auditoria', (make_date(2026, 10, 1) + make_interval(months => m))::date) from generate_series(0, 14) m;

create table nucleo.evento_salida (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo_evento varchar(80) not null,
    entidad varchar(80) not null,
    entidad_id bigint not null,
    carga jsonb not null,
    estado text not null default 'pendiente' constraint ck_evento_salida_estado check (estado in ('pendiente', 'publicado', 'fallido')),
    intentos smallint not null default 0,
    publicado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table nucleo.predio (
    id bigint generated always as identity primary key,
    nombre varchar(120) not null,
    matricula_inmobiliaria varchar(40),
    propietario varchar(150),
    tenencia text not null constraint ck_predio_tenencia check (tenencia in ('propio', 'comodato', 'arriendo', 'otro')),
    area_m2 numeric(12,2),
    codigo_dane_municipio char(5),
    vereda varchar(80),
    geometria geometry(MultiPolygon, 9377),
    es_practica boolean not null default false,
    regimen_tributario text not null default 'por_definir' constraint ck_predio_regimen_tributario check (regimen_tributario in ('por_definir', 'ordinario', 'simple', 'no_responsable')),
    empleador_tercero_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table nucleo.zona (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    tipo_zona text not null constraint ck_zona_tipo_zona check (tipo_zona in ('galpon', 'aprisco', 'estanque', 'lote_cultivo', 'potrero', 'bodega', 'vivienda', 'ronda_hidrica', 'apiario', 'lombricultivo', 'biodigestor', 'otra')),
    area_m2 numeric(12,2),
    capacidad integer,
    geometria geometry(Polygon, 9377),
    modelo_3d_url varchar(300),
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table terceros.tercero (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo_persona text not null constraint ck_tercero_tipo_persona check (tipo_persona in ('natural', 'juridica')),
    tipo_documento text constraint ck_tercero_tipo_documento check (tipo_documento in ('CC', 'CE', 'NIT', 'PAS', 'TI', 'PPT')),
    numero_documento varchar(20),
    digito_verificacion char(1),
    nombres varchar(120),
    apellidos varchar(120),
    razon_social varchar(200),
    correo citext,
    telefono varchar(20),
    whatsapp varchar(20),
    direccion varchar(200),
    codigo_dane_municipio char(5),
    es_cliente boolean not null default false,
    es_proveedor boolean not null default false,
    es_empleado boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, tipo_documento, numero_documento)
);

create table terceros.consentimiento_datos (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    finalidad text not null constraint ck_consentimiento_datos_finalidad check (finalidad in ('atencion_pedidos', 'publicidad', 'personalizacion_ofertas', 'analitica', 'imagen_redes', 'biometria_acceso')),
    version_politica varchar(20) not null,
    otorgado boolean not null,
    medio text not null constraint ck_consentimiento_datos_medio check (medio in ('whatsapp', 'web', 'formulario_fisico', 'verbal_grabado', 'correo')),
    evidencia_url varchar(300),
    otorgado_en timestamptz not null,
    revocado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table terceros.cliente (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    segmento text not null constraint ck_cliente_segmento check (segmento in ('hogar', 'tienda', 'restaurante', 'hotel', 'asadero', 'carniceria', 'mayorista', 'turista', 'otro')),
    canal_origen text constraint ck_cliente_canal_origen check (canal_origen in ('whatsapp', 'web', 'redes', 'referido', 'mercado_campesino', 'finca', 'otro')),
    frecuencia_compra_dias smallint,
    fecha_primera_compra date,
    cupo_credito numeric(14,2) not null default 0,
    dias_plazo smallint not null default 0,
    bloqueado_por_mora boolean not null default false,
    lista_precios_id bigint,
    perfil_interes_ref varchar(24),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, tercero_id)
);

create table terceros.proveedor (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    categoria text not null constraint ck_proveedor_categoria check (categoria in ('concentrado', 'animales', 'semillas', 'medicamentos', 'materiales', 'servicios', 'transporte', 'otro')),
    dias_credito smallint not null default 0,
    calificacion numeric(3,2),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, tercero_id)
);

create table terceros.empleado (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    cargo varchar(80) not null,
    tipo_vinculacion text not null constraint ck_empleado_tipo_vinculacion check (tipo_vinculacion in ('termino_fijo', 'termino_indefinido', 'jornal', 'prestacion_servicios', 'aprendiz')),
    salario_base numeric(14,2),
    forma_pago text not null default 'salario' constraint ck_empleado_forma_pago check (forma_pago in ('salario', 'jornal', 'destajo', 'mixto')),
    valor_jornal numeric(14,2),
    ruta_aprendizaje varchar(60),
    fecha_ingreso date not null,
    fecha_retiro date,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, tercero_id)
);

create table produccion.especie (
    id bigint generated always as identity primary key,
    codigo varchar(20) not null unique,
    nombre_comun varchar(80) not null,
    nombre_cientifico varchar(120),
    grupo text not null constraint ck_especie_grupo check (grupo in ('ave', 'ovino', 'caprino', 'pez', 'abeja', 'lombriz', 'otro')),
    manejo_individual boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table produccion.lote_animal (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    especie_id bigint not null,
    zona_id bigint not null,
    raza_linea varchar(80),
    proposito text not null constraint ck_lote_animal_proposito check (proposito in ('postura', 'engorde', 'cria', 'reproduccion', 'miel', 'humus')),
    fecha_ingreso date not null,
    edad_ingreso_semanas smallint,
    cantidad_inicial integer not null,
    cantidad_actual integer not null,
    costo_ingreso numeric(14,2),
    estado text not null default 'activo' constraint ck_lote_animal_estado check (estado in ('activo', 'cerrado')),
    fecha_cierre date,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table produccion.animal (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_animal_id bigint not null,
    identificador varchar(20) not null,
    sexo text not null constraint ck_animal_sexo check (sexo in ('hembra', 'macho')),
    fecha_nacimiento date,
    madre_id bigint,
    padre_id bigint,
    estado text not null default 'activo' constraint ck_animal_estado check (estado in ('activo', 'vendido', 'muerto', 'descartado')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, identificador)
);

create table produccion.registro_postura (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_animal_id bigint not null,
    fecha date not null,
    huevos_recogidos integer not null,
    huevos_rotos integer not null default 0,
    registrado_por bigint not null,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, lote_animal_id, fecha),
    check (huevos_rotos between 0 and huevos_recogidos)
);

create table produccion.registro_alimentacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_animal_id bigint not null,
    fecha date not null,
    producto_id bigint not null,
    cantidad_kg numeric(10,2) not null,
    origen text not null constraint ck_registro_alimentacion_origen check (origen in ('comprado', 'propio')),
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.evento_sanitario (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_animal_id bigint not null,
    animal_id bigint,
    fecha date not null,
    tipo text not null constraint ck_evento_sanitario_tipo check (tipo in ('vacuna', 'desparasitacion', 'tratamiento', 'revision', 'mortalidad', 'descarte')),
    producto_id bigint,
    dosis varchar(40),
    cantidad_afectada integer not null default 1,
    causa varchar(150),
    responsable varchar(120),
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.registro_pesaje (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_animal_id bigint not null,
    animal_id bigint,
    fecha date not null,
    animales_muestreados integer not null default 1,
    peso_promedio_kg numeric(8,3) not null,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.evento_reproductivo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    hembra_id bigint not null,
    macho_id bigint,
    tipo text not null constraint ck_evento_reproductivo_tipo check (tipo in ('monta', 'parto', 'aborto', 'destete')),
    fecha date not null,
    crias_vivas smallint,
    crias_muertas smallint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.calidad_agua_estanque (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_id bigint not null,
    medido_en timestamptz not null,
    oxigeno_mg_l numeric(5,2),
    temperatura_c numeric(4,1),
    ph numeric(4,2),
    amonio_mg_l numeric(5,2),
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.cultivo (
    id bigint generated always as identity primary key,
    codigo varchar(20) not null unique,
    nombre_comun varchar(80) not null,
    nombre_cientifico varchar(120),
    tipo_ciclo text not null constraint ck_cultivo_tipo_ciclo check (tipo_ciclo in ('corto', 'perenne', 'forraje')),
    dias_a_primera_cosecha integer,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table produccion.siembra (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_id bigint not null,
    cultivo_id bigint not null,
    variedad varchar(80),
    fecha_siembra date not null,
    plantas_previstas integer,
    plantas_sembradas integer,
    plantas_vivas integer,
    semilla_kg numeric(10,2),
    area_m2 numeric(12,2),
    fecha_estimada_cosecha date,
    estado text not null default 'sembrada' constraint ck_siembra_estado check (estado in ('planeada', 'sembrada', 'en_produccion', 'recuperacion', 'perdida', 'finalizada')),
    observaciones text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.labor_cultural (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    siembra_id bigint not null,
    fecha date not null,
    tipo text not null constraint ck_labor_cultural_tipo check (tipo in ('encalado', 'fertilizacion', 'deshierbe', 'control_plagas', 'poda', 'resiembra', 'aporque', 'conteo')),
    producto_id bigint,
    cantidad numeric(10,2),
    jornales numeric(5,2),
    metodo text not null default 'manual' constraint ck_labor_cultural_metodo check (metodo in ('manual', 'mecanico', 'robot', 'dron')),
    tarea_id bigint,
    mision_robot_id bigint,
    observaciones text,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (metodo not in ('robot', 'dron') or mision_robot_id is not null)
);

create table produccion.cosecha (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    siembra_id bigint not null,
    fecha date not null,
    producto_id bigint not null,
    cantidad numeric(12,2) not null,
    destino text not null constraint ck_cosecha_destino check (destino in ('venta', 'alimento_animal', 'semilla', 'autoconsumo', 'perdida')),
    lote_inventario_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.analisis_suelo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_id bigint not null,
    fecha_muestreo date not null,
    laboratorio varchar(120),
    ph numeric(4,2),
    materia_organica_pct numeric(5,2),
    aluminio_cmol_kg numeric(6,2),
    resultados jsonb,
    recomendacion text,
    archivo_url varchar(300),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table riego.fuente_agua (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(80) not null,
    tipo text not null constraint ck_fuente_agua_tipo check (tipo in ('nacedero', 'acueducto_veredal', 'lluvia', 'pozo', 'quebrada')),
    caudal_l_s numeric(8,3),
    requiere_concesion boolean not null default true,
    numero_concesion varchar(40),
    concesion_vence date,
    apta_consumo_humano boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table riego.tanque (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    capacidad_litros integer not null,
    fuente_agua_id bigint,
    zona_id bigint,
    sensor_nivel_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table riego.sistema_riego (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(80) not null,
    tipo text not null constraint ck_sistema_riego_tipo check (tipo in ('aspersion', 'goteo', 'microaspersion', 'manual')),
    tanque_id bigint,
    caudal_l_min numeric(8,2),
    modo_control text not null default 'manual' constraint ck_sistema_riego_modo_control check (modo_control in ('manual', 'programado', 'automatico')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table riego.valvula (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    sistema_riego_id bigint not null,
    codigo varchar(20) not null,
    zona_id bigint not null,
    tipo text not null default 'manual' constraint ck_valvula_tipo check (tipo in ('manual', 'electrovalvula')),
    actuador_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table riego.evento_riego (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    valvula_id bigint not null,
    inicio timestamptz not null,
    fin timestamptz,
    litros_estimados numeric(10,1),
    modo text not null constraint ck_evento_riego_modo check (modo in ('manual', 'programado', 'automatico')),
    registrado_por bigint,
    regla_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table inventario.unidad_medida (
    id bigint generated always as identity primary key,
    codigo varchar(10) not null unique,
    nombre varchar(40) not null,
    unidad_base varchar(10),
    factor_base numeric(12,4) not null default 1,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table inventario.categoria_producto (
    id bigint generated always as identity primary key,
    nombre varchar(80) not null,
    padre_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table inventario.producto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    sku varchar(30) not null,
    nombre varchar(150) not null,
    descripcion text,
    categoria_id bigint not null,
    unidad_id bigint not null,
    tipo text not null constraint ck_producto_tipo check (tipo in ('producto_terminado', 'insumo', 'servicio', 'activo_menor')),
    se_vende boolean not null default false,
    se_compra boolean not null default false,
    se_produce boolean not null default false,
    perecedero boolean not null default false,
    vida_util_ambiente_dias smallint,
    vida_util_refrigerado_dias smallint,
    dias_margen_venta smallint not null default 0,
    dias_alerta_venta smallint not null default 0,
    metodo_salida text not null default 'fefo' constraint ck_producto_metodo_salida check (metodo_salida in ('fefo', 'fifo')),
    gtin varchar(14),
    pesable boolean not null default false,
    peso_nominal_kg numeric(10,3),
    tolerancia_peso_pct numeric(5,2),
    tarifa_iva numeric(5,2) not null default 0,
    stock_minimo numeric(12,2),
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, sku),
    check (dias_margen_venta >= 0 and dias_alerta_venta >= 0)
);

create table inventario.bodega (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(80) not null,
    zona_id bigint,
    refrigerada boolean not null default false,
    sensor_temperatura_id bigint,
    temperatura_min_c numeric(4,1),
    temperatura_max_c numeric(4,1),
    minutos_tolerancia smallint not null default 30,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table inventario.lote_inventario (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    producto_id bigint not null,
    bodega_id bigint not null,
    codigo_lote varchar(30) not null,
    origen text not null constraint ck_lote_inventario_origen check (origen in ('produccion', 'compra', 'ajuste')),
    origen_tabla varchar(60),
    origen_id bigint,
    fecha_produccion date not null,
    condicion_almacenamiento text not null default 'ambiente' constraint ck_lote_inventario_condicion_almacenamiento check (condicion_almacenamiento in ('ambiente', 'refrigerado')),
    origen_vencimiento text not null default 'estimado' constraint ck_lote_inventario_origen_vencimiento check (origen_vencimiento in ('estimado', 'manual', 'laboratorio')),
    fecha_vencimiento date,
    fecha_limite_venta date,
    peso_neto_kg numeric(12,3),
    cantidad_inicial numeric(12,2) not null,
    cantidad_disponible numeric(12,2) not null default 0,
    cantidad_reservada numeric(12,2) not null default 0,
    costo_unitario numeric(14,2) not null,
    estado text not null default 'disponible' constraint ck_lote_inventario_estado check (estado in ('disponible', 'agotado', 'vencido', 'bloqueado')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, producto_id, codigo_lote),
    check (cantidad_disponible >= 0 and cantidad_reservada >= 0)
);

create table inventario.movimiento_inventario (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_inventario_id bigint not null,
    tipo text not null constraint ck_movimiento_inventario_tipo check (tipo in ('entrada', 'reserva', 'liberacion', 'salida_venta', 'consumo_interno', 'merma', 'ajuste_entrada', 'ajuste_salida', 'traslado_salida', 'traslado_entrada')),
    cantidad numeric(12,2) not null,
    causa_merma text constraint ck_movimiento_inventario_causa_merma check (causa_merma in ('vencido', 'roto', 'plaga', 'calidad', 'robo', 'otro')),
    pesaje_id bigint,
    lectura_codigo_id bigint,
    costo_unitario numeric(14,2) not null,
    documento_tipo varchar(40) not null,
    documento_id bigint not null,
    ocurrido_en timestamptz not null default now(),
    usuario_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table comercial.lista_precios (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(80) not null,
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table comercial.precio_producto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lista_precios_id bigint not null,
    producto_id bigint not null,
    precio_unitario numeric(14,2) not null,
    incluye_iva boolean not null default true,
    vigente_desde timestamptz not null,
    vigente_hasta timestamptz,
    propuesta_precio_id bigint,
    aprobado_por bigint not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table comercial.propuesta_precio (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    producto_id bigint not null,
    lista_precios_id bigint not null,
    precio_actual numeric(14,2) not null,
    precio_propuesto numeric(14,2) not null,
    variacion_pct numeric(6,2) not null,
    justificacion text not null,
    evidencia jsonb not null,
    agente_id bigint,
    estado text not null default 'pendiente' constraint ck_propuesta_precio_estado check (estado in ('pendiente', 'aprobada', 'rechazada', 'vencida', 'aplicada')),
    vence_en timestamptz not null,
    revisado_por bigint,
    revisado_en timestamptz,
    comentario_revision text,
    aplicada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table comercial.pedido (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    numero varchar(20) not null,
    cliente_id bigint not null,
    canal text not null constraint ck_pedido_canal check (canal in ('whatsapp', 'web', 'redes', 'telefono', 'finca', 'mercado_campesino')),
    estado text not null default 'borrador' constraint ck_pedido_estado check (estado in ('borrador', 'confirmado', 'en_preparacion', 'despachado', 'entregado', 'cancelado')),
    forma_pago text not null default 'contado' constraint ck_pedido_forma_pago check (forma_pago in ('contado', 'credito')),
    pedido_recurrente_id bigint,
    fecha_entrega_programada date,
    direccion_entrega varchar(200),
    subtotal numeric(14,2) not null default 0,
    descuento numeric(14,2) not null default 0,
    impuestos numeric(14,2) not null default 0,
    valor_domicilio numeric(14,2) not null default 0,
    total numeric(14,2) not null default 0,
    conversacion_ref varchar(24),
    creado_por_agente_id bigint,
    vendedor_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, numero)
);

create table comercial.pedido_detalle (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    pedido_id bigint not null,
    producto_id bigint not null,
    cantidad numeric(12,2) not null,
    precio_producto_id bigint not null,
    precio_unitario numeric(14,2) not null,
    descuento numeric(14,2) not null default 0,
    tarifa_iva numeric(5,2) not null default 0,
    total_linea numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table comercial.factura (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    prefijo varchar(6) not null,
    numero integer not null,
    pedido_id bigint,
    cliente_id bigint not null,
    fecha_emision timestamptz not null,
    subtotal numeric(14,2) not null,
    iva numeric(14,2) not null,
    total numeric(14,2) not null,
    forma_pago text not null constraint ck_factura_forma_pago check (forma_pago in ('contado', 'credito')),
    fecha_vencimiento date,
    saldo numeric(14,2) not null default 0,
    cufe varchar(96),
    estado_dian text not null default 'pendiente' constraint ck_factura_estado_dian check (estado_dian in ('pendiente', 'aceptada', 'rechazada', 'no_aplica')),
    xml_url varchar(300),
    pdf_url varchar(300),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, prefijo, numero)
);

create table comercial.pago (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    pedido_id bigint,
    factura_id bigint,
    fecha timestamptz not null,
    valor numeric(14,2) not null,
    medio text not null constraint ck_pago_medio check (medio in ('efectivo', 'nequi', 'daviplata', 'transferencia', 'tarjeta', 'bre_b', 'pasarela', 'compensacion_permuta')),
    proveedor_pasarela text constraint ck_pago_proveedor_pasarela check (proveedor_pasarela in ('wompi', 'mercado_pago', 'epayco', 'payu')),
    id_transaccion_pasarela varchar(80),
    referencia varchar(60),
    estado text not null default 'pendiente' constraint ck_pago_estado check (estado in ('pendiente', 'confirmado', 'reversado')),
    confirmado_por bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (pedido_id is not null or factura_id is not null)
);

create table comercial.entrega (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    pedido_id bigint not null,
    fecha_salida timestamptz,
    fecha_entrega timestamptz,
    responsable varchar(120),
    vehiculo_id bigint,
    estado text not null default 'programada' constraint ck_entrega_estado check (estado in ('programada', 'en_ruta', 'entregada', 'fallida')),
    evidencia_url varchar(300),
    calificacion_cliente smallint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table compras.orden_compra (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    numero varchar(20) not null,
    proveedor_id bigint not null,
    fecha date not null,
    estado text not null default 'borrador' constraint ck_orden_compra_estado check (estado in ('borrador', 'aprobada', 'recibida', 'parcial', 'anulada')),
    total numeric(14,2) not null default 0,
    aprobado_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, numero)
);

create table compras.orden_compra_detalle (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    orden_compra_id bigint not null,
    producto_id bigint not null,
    cantidad numeric(12,2) not null,
    cantidad_recibida numeric(12,2) not null default 0,
    precio_unitario numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table compras.cotizacion_proveedor (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proveedor_id bigint,
    nombre_proveedor varchar(150),
    producto_id bigint not null,
    precio_unitario numeric(14,2) not null,
    fecha date not null,
    vigente_hasta date,
    fuente text not null constraint ck_cotizacion_proveedor_fuente check (fuente in ('visita', 'telefono', 'correo', 'web', 'agente')),
    fuente_url varchar(300),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table compras.precio_mercado (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    producto_id bigint not null,
    mercado varchar(80) not null,
    fecha date not null,
    precio_minimo numeric(14,2),
    precio_maximo numeric(14,2),
    precio_promedio numeric(14,2) not null,
    unidad varchar(20) not null,
    fuente_url varchar(300),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, producto_id, mercado, fecha)
);

create table finanzas.cuenta_contable (
    id bigint generated always as identity primary key,
    codigo varchar(10) not null unique,
    nombre varchar(150) not null,
    naturaleza text not null constraint ck_cuenta_contable_naturaleza check (naturaleza in ('debito', 'credito')),
    nivel smallint not null,
    padre_id bigint,
    acepta_movimiento boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table finanzas.centro_costo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(10) not null,
    nombre varchar(80) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table finanzas.comprobante (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_comprobante_tipo check (tipo in ('ingreso', 'egreso', 'nota_contable', 'causacion', 'nomina', 'ajuste')),
    numero varchar(20) not null,
    fecha date not null,
    descripcion text not null,
    origen_tabla varchar(60),
    origen_id bigint,
    estado text not null default 'borrador' constraint ck_comprobante_estado check (estado in ('borrador', 'contabilizado', 'anulado')),
    aprobado_por bigint,
    contabilizado_en timestamptz,
    motivo_anulacion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, tipo, numero)
);

create table finanzas.movimiento_contable (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    comprobante_id bigint not null,
    cuenta_id bigint not null,
    tercero_id bigint,
    centro_costo_id bigint,
    debito numeric(14,2) not null default 0,
    credito numeric(14,2) not null default 0,
    detalle varchar(200),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (debito >= 0 and credito >= 0 and (debito = 0 or credito = 0))
);

create table ia.agente (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(40) not null,
    nombre varchar(80) not null,
    rol text not null,
    nivel_autonomia text not null constraint ck_agente_nivel_autonomia check (nivel_autonomia in ('solo_lectura', 'propone', 'ejecuta_con_regla')),
    proveedor_modelo varchar(40) not null,
    modelo varchar(60) not null,
    modelo_respaldo varchar(60),
    version_instrucciones varchar(20) not null,
    instrucciones text not null,
    limite_costo_diario_usd numeric(8,2),
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table ia.herramienta (
    id bigint generated always as identity primary key,
    codigo varchar(60) not null unique,
    descripcion text not null,
    tipo text not null constraint ck_herramienta_tipo check (tipo in ('lectura', 'propuesta', 'escritura')),
    requiere_aprobacion boolean not null default false,
    esquema_entrada jsonb not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table ia.agente_herramienta (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    agente_id bigint not null,
    herramienta_id bigint not null,
    unique (predio_id, id),
    unique (predio_id, agente_id, herramienta_id)
);

create table ia.solicitud_aprobacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    agente_id bigint not null,
    herramienta_id bigint not null,
    entidad varchar(60) not null,
    entidad_id bigint,
    resumen text not null,
    carga jsonb not null,
    estado text not null default 'pendiente' constraint ck_solicitud_aprobacion_estado check (estado in ('pendiente', 'aprobada', 'rechazada', 'vencida', 'ejecutada', 'fallida')),
    vence_en timestamptz not null,
    resuelto_por bigint,
    resuelto_en timestamptz,
    motivo text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.documento_conocimiento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    titulo varchar(200) not null,
    tipo text not null constraint ck_documento_conocimiento_tipo check (tipo in ('ficha_producto', 'politica', 'pregunta_frecuente', 'manual_tecnico', 'informe', 'receta', 'turismo')),
    contenido text not null,
    fuente varchar(300),
    version smallint not null default 1,
    vigente boolean not null default true,
    aprobado_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.fragmento_conocimiento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    documento_id bigint not null,
    orden integer not null,
    texto text not null,
    vector vector(1024) not null,
    metadatos jsonb,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.recomendacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    agente_id bigint not null,
    tipo text not null constraint ck_recomendacion_tipo check (tipo in ('mejora_continua', 'comercial', 'compra', 'produccion', 'contenido_redes', 'riesgo')),
    titulo varchar(200) not null,
    descripcion text not null,
    evidencia jsonb not null,
    indicador varchar(120),
    prioridad text not null constraint ck_recomendacion_prioridad check (prioridad in ('alta', 'media', 'baja')),
    estado text not null default 'nueva' constraint ck_recomendacion_estado check (estado in ('nueva', 'aceptada', 'descartada', 'en_ejecucion', 'cumplida')),
    responsable_id bigint,
    fecha_limite date,
    resultado text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.evaluacion_respuesta (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    agente_id bigint not null,
    mensaje_ref varchar(24) not null,
    origen text not null constraint ck_evaluacion_respuesta_origen check (origen in ('cliente', 'administrador', 'evaluacion_automatica')),
    calificacion smallint not null,
    motivo text constraint ck_evaluacion_respuesta_motivo check (motivo in ('correcta', 'incorrecta', 'incompleta', 'tono', 'demora', 'otro')),
    comentario text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (calificacion between 1 and 5)
);

create table ia.consumo_ia (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    agente_id bigint not null,
    fecha date not null,
    proveedor_modelo varchar(40) not null,
    modelo varchar(60) not null,
    solicitudes integer not null default 0,
    tokens_entrada bigint not null default 0,
    tokens_salida bigint not null default 0,
    costo_usd numeric(10,4) not null default 0,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, agente_id, fecha, modelo)
);

create table redes.cuenta_red (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    plataforma varchar(20) not null,
    nombre_cuenta varchar(100) not null,
    identificador_externo varchar(80) not null,
    secreto_ref varchar(120) not null,
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table redes.publicacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    cuenta_red_id bigint not null,
    texto text not null,
    medios jsonb,
    estado text not null default 'borrador' constraint ck_publicacion_estado check (estado in ('borrador', 'propuesta', 'aprobada', 'programada', 'publicada', 'rechazada')),
    programada_para timestamptz,
    publicada_en timestamptz,
    id_externo varchar(80),
    agente_id bigint,
    aprobado_por bigint,
    recomendacion_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table turismo.alojamiento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(80) not null,
    capacidad_personas smallint not null,
    zona_id bigint,
    tarifa_noche numeric(14,2) not null,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table turismo.plan_turistico (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    descripcion text not null,
    duracion_horas numeric(4,1),
    cupo_maximo smallint,
    precio_persona numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table turismo.reserva (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    cliente_id bigint not null,
    alojamiento_id bigint,
    plan_turistico_id bigint,
    fecha_inicio date not null,
    fecha_fin date not null,
    personas smallint not null,
    estado text not null default 'solicitada' constraint ck_reserva_estado check (estado in ('solicitada', 'confirmada', 'pagada', 'cumplida', 'cancelada')),
    total numeric(14,2) not null,
    valor_deposito numeric(14,2) not null default 0,
    checkin_en timestamptz,
    checkout_en timestamptz,
    pedido_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo),
    check (fecha_fin >= fecha_inicio)
);

create table iot.dispositivo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    tipo text not null constraint ck_dispositivo_tipo check (tipo in ('esp32', 'plc', 'estacion_clima', 'pasarela', 'registrador_temperatura', 'camara', 'camara_termica', 'lector_acceso', 'central_alarma', 'otro')),
    pasarela_id bigint,
    zona_id bigint,
    topico_mqtt varchar(120) not null,
    direccion_red_local inet,
    version_firmware varchar(30),
    ultima_conexion timestamptz,
    ultima_sincronizacion_nube timestamptz,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table iot.sensor (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    dispositivo_id bigint not null,
    codigo varchar(30) not null,
    magnitud text not null constraint ck_sensor_magnitud check (magnitud in ('humedad_suelo', 'nivel_tanque', 'caudal', 'temperatura', 'humedad_aire', 'lluvia', 'oxigeno_agua', 'ph', 'movimiento', 'puerta', 'rotura_vidrio', 'humo', 'gas', 'amoniaco', 'presencia_termica')),
    unidad varchar(10) not null,
    valor_minimo_alerta numeric(10,3),
    valor_maximo_alerta numeric(10,3),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table iot.actuador (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    dispositivo_id bigint not null,
    codigo varchar(30) not null,
    tipo text not null constraint ck_actuador_tipo check (tipo in ('electrovalvula', 'bomba', 'rele', 'motor', 'sirena', 'reflector', 'cerradura', 'cortina', 'extractor')),
    zona_seguridad_id bigint,
    modo_falla text not null default 'mantiene' constraint ck_actuador_modo_falla check (modo_falla in ('cierra_sin_energia', 'abre_sin_energia', 'mantiene')),
    estado_actual text not null default 'desconocido' constraint ck_actuador_estado_actual check (estado_actual in ('abierto', 'cerrado', 'encendido', 'apagado', 'desconocido')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table iot.lectura (
    id bigint generated always as identity,
    predio_id bigint not null default nucleo.predio_actual(),
    sensor_id bigint not null,
    medido_en timestamptz not null,
    recibido_en timestamptz not null default now(),
    valor double precision not null,
    primary key (id, medido_en),
    unique (predio_id, sensor_id, medido_en)
) partition by range (medido_en);

create table iot.lectura_por_defecto partition of iot.lectura default;
select nucleo.crear_particion_mensual('iot.lectura', (make_date(2026, 10, 1) + make_interval(months => m))::date) from generate_series(0, 14) m;

create table iot.regla_automatizacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(120) not null,
    condicion jsonb not null,
    actuador_id bigint not null,
    accion text not null constraint ck_regla_automatizacion_accion check (accion in ('abrir', 'cerrar', 'encender', 'apagar')),
    duracion_max_min smallint not null,
    ejecuta_en text not null default 'pasarela_local' constraint ck_regla_automatizacion_ejecuta_en check (ejecuta_en in ('pasarela_local', 'nodo', 'nube')),
    version integer not null default 1,
    desplegada_version integer,
    activa boolean not null default false,
    aprobado_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table iot.comando_actuador (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    actuador_id bigint not null,
    accion text not null constraint ck_comando_actuador_accion check (accion in ('abrir', 'cerrar', 'encender', 'apagar')),
    origen text not null constraint ck_comando_actuador_origen check (origen in ('app_nube', 'app_red_local', 'regla', 'boton_fisico')),
    regla_id bigint,
    solicitado_por bigint,
    duracion_max_min smallint not null,
    estado text not null default 'pendiente' constraint ck_comando_actuador_estado check (estado in ('pendiente', 'enviado', 'ejecutado', 'fallido', 'expirado')),
    expira_en timestamptz not null,
    ejecutado_en timestamptz,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table nucleo.dispositivo_captura (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    tipo text not null constraint ck_dispositivo_captura_tipo check (tipo in ('celular', 'tableta', 'lector_codigo', 'bascula', 'impresora_etiquetas')),
    conexion text not null constraint ck_dispositivo_captura_conexion check (conexion in ('camara', 'teclado_hid', 'bluetooth_ble', 'bluetooth_serial', 'usb', 'red_local')),
    marca_modelo varchar(80),
    numero_serie varchar(60),
    capacidad_max_kg numeric(10,3),
    division_g numeric(8,2),
    uso_comercial boolean not null default false,
    ultima_verificacion date,
    proxima_verificacion date,
    certificado_url varchar(300),
    usuario_asignado_id bigint,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table nucleo.sincronizacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    dispositivo_captura_id bigint not null,
    usuario_id bigint not null,
    version_app varchar(20) not null,
    iniciada_en timestamptz not null,
    terminada_en timestamptz,
    registros_recibidos integer not null default 0,
    registros_duplicados integer not null default 0,
    registros_rechazados integer not null default 0,
    detalle_rechazos jsonb,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table inventario.etiqueta (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_inventario_id bigint not null,
    codigo varchar(80) not null,
    simbologia text not null constraint ck_etiqueta_simbologia check (simbologia in ('code128', 'qr', 'gs1_128', 'gs1_datamatrix', 'ean13')),
    impresora_id bigint,
    impresa_en timestamptz,
    anulada boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table inventario.lectura_codigo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo_leido varchar(120) not null,
    simbologia varchar(20),
    etiqueta_id bigint,
    accion text not null constraint ck_lectura_codigo_accion check (accion in ('consulta', 'entrada', 'salida', 'conteo', 'traslado', 'despacho')),
    resultado text not null constraint ck_lectura_codigo_resultado check (resultado in ('ok', 'desconocido', 'anulado', 'vencido', 'duplicado', 'rechazado')),
    usuario_id bigint not null,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table inventario.pesaje (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    peso_bruto_kg numeric(12,3) not null,
    tara_kg numeric(12,3) not null default 0,
    peso_neto_kg numeric(12,3) not null,
    estable boolean not null,
    origen text not null constraint ck_pesaje_origen check (origen in ('bascula_automatica', 'digitado')),
    referencia_tabla varchar(60),
    referencia_id bigint,
    usuario_id bigint not null,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (abs(peso_neto_kg - (peso_bruto_kg - tara_kg)) < 0.001)
);

create table inventario.conteo_fisico (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    bodega_id bigint not null,
    fecha date not null,
    estado text not null default 'en_curso' constraint ck_conteo_fisico_estado check (estado in ('en_curso', 'cerrado', 'ajustado')),
    responsable_id bigint not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table inventario.conteo_detalle (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    conteo_fisico_id bigint not null,
    lote_inventario_id bigint not null,
    cantidad_sistema numeric(12,2) not null,
    cantidad_contada numeric(12,2) not null,
    movimiento_ajuste_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, conteo_fisico_id, lote_inventario_id)
);

create table comercial.reserva_lote (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    pedido_detalle_id bigint not null,
    lote_inventario_id bigint not null,
    cantidad numeric(12,2) not null,
    estado text not null default 'reservada' constraint ck_reserva_lote_estado check (estado in ('reservada', 'despachada', 'liberada')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (cantidad > 0)
);

create table finanzas.periodo_contable (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    anio smallint not null,
    mes smallint not null,
    estado text not null default 'abierto' constraint ck_periodo_contable_estado check (estado in ('abierto', 'cerrado')),
    cerrado_por bigint,
    cerrado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, anio, mes),
    check (mes between 1 and 12)
);

create table redes.politica_canal (
    id bigint generated always as identity primary key,
    plataforma varchar(20) not null unique,
    ventana_horas smallint,
    ventana_agente_humano_horas smallint,
    ventana_anuncio_horas smallint,
    max_mensajes_por_ventana smallint,
    empresa_puede_iniciar boolean not null,
    requiere_plantilla_fuera_ventana boolean not null,
    cobra_por_mensaje boolean not null,
    mensajes_servicio_gratis_mes integer,
    solo_bot_del_negocio boolean not null default true,
    disponible boolean not null default true,
    fuente_url varchar(300),
    verificado_en date not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table redes.plantilla_mensaje (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    cuenta_red_id bigint not null,
    nombre varchar(80) not null,
    categoria text not null constraint ck_plantilla_mensaje_categoria check (categoria in ('marketing', 'utility', 'authentication')),
    idioma varchar(10) not null default 'es_CO',
    cuerpo text not null,
    variables jsonb,
    estado_meta text not null default 'borrador' constraint ck_plantilla_mensaje_estado_meta check (estado_meta in ('borrador', 'enviada', 'aprobada', 'rechazada', 'pausada')),
    id_externo varchar(80),
    finalidad_requerida text not null constraint ck_plantilla_mensaje_finalidad_requerida check (finalidad_requerida in ('atencion_pedidos', 'publicidad')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, cuenta_red_id, nombre, idioma)
);

create table redes.mensaje_saliente (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    cuenta_red_id bigint not null,
    tercero_id bigint,
    conversacion_ref varchar(24),
    tipo text not null constraint ck_mensaje_saliente_tipo check (tipo in ('servicio', 'plantilla', 'respuesta_privada_comentario')),
    plantilla_id bigint,
    autor text not null constraint ck_mensaje_saliente_autor check (autor in ('agente', 'humano', 'sistema')),
    dentro_ventana boolean not null,
    consentimiento_id bigint,
    costo_estimado_usd numeric(10,4) not null default 0,
    estado_entrega text not null default 'enviado' constraint ck_mensaje_saliente_estado_entrega check (estado_entrega in ('enviado', 'entregado', 'leido', 'fallido', 'bloqueado_por_regla')),
    enviado_en timestamptz not null default now(),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.regla_conversacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_regla_conversacion_tipo check (tipo in ('tema_permitido', 'tema_fuera_de_alcance', 'escalar_a_humano', 'dato_prohibido')),
    descripcion text not null,
    ejemplos jsonb,
    respuesta_plantilla text,
    prioridad_escalamiento text constraint ck_regla_conversacion_prioridad_escalamiento check (prioridad_escalamiento in ('alta', 'media', 'baja')),
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.escalamiento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    conversacion_ref varchar(24) not null,
    canal varchar(20) not null,
    motivo text not null constraint ck_escalamiento_motivo check (motivo in ('solicitud_cliente', 'queja', 'fuera_de_alcance', 'sin_respuesta_conocimiento', 'pedido_grande', 'pago', 'error_agente')),
    prioridad text not null constraint ck_escalamiento_prioridad check (prioridad in ('alta', 'media', 'baja')),
    asignado_a bigint,
    estado text not null default 'pendiente' constraint ck_escalamiento_estado check (estado in ('pendiente', 'en_atencion', 'resuelto', 'vencido')),
    responder_antes_de timestamptz not null,
    atendido_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table nucleo.funcionalidad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(40) not null,
    descripcion text not null,
    fase smallint not null,
    requiere_equipo varchar(150),
    activa boolean not null default false,
    activada_por bigint,
    activada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table nucleo.nota_voz (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    usuario_id bigint not null,
    audio_url varchar(300) not null,
    duracion_seg smallint,
    transcripcion text,
    proveedor_voz_texto varchar(40),
    interpretacion jsonb,
    estado text not null default 'pendiente' constraint ck_nota_voz_estado check (estado in ('pendiente', 'interpretada', 'confirmada', 'descartada')),
    registro_tabla varchar(60),
    registro_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.categoria_huevo (
    id bigint generated always as identity primary key,
    codigo varchar(10) not null,
    peso_min_g numeric(5,1) not null,
    peso_max_g numeric(5,1),
    norma varchar(80) not null,
    vigente_desde date not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (codigo, vigente_desde),
    check (peso_max_g is null or peso_max_g > peso_min_g)
);

create table produccion.clasificacion_postura (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    registro_postura_id bigint not null,
    categoria_huevo_id bigint not null,
    cantidad integer not null,
    metodo text not null default 'manual' constraint ck_clasificacion_postura_metodo check (metodo in ('peso_bascula', 'manual', 'vision')),
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, registro_postura_id, categoria_huevo_id),
    check (cantidad >= 0)
);

create table produccion.registro_bioseguridad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_id bigint not null,
    fecha date not null,
    tipo text not null constraint ck_registro_bioseguridad_tipo check (tipo in ('limpieza', 'desinfeccion', 'control_plagas', 'visita', 'cambio_cama', 'calidad_agua', 'vacio_sanitario')),
    producto_id bigint,
    responsable varchar(120) not null,
    observaciones text,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table produccion.produccion_abono (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    origen text not null constraint ck_produccion_abono_origen check (origen in ('lombricultivo', 'compostera', 'biodigestor')),
    zona_id bigint,
    fecha date not null,
    kg numeric(10,2) not null,
    lote_inventario_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table inventario.vehiculo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    tipo text not null constraint ck_vehiculo_tipo check (tipo in ('camioneta', 'motocarro', 'moto', 'otro')),
    placa varchar(10),
    capacidad_kg numeric(10,2),
    refrigerado boolean not null default false,
    sensor_temperatura_id bigint,
    temperatura_max_c numeric(4,1),
    minutos_tolerancia smallint not null default 30,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table inventario.excursion_temperatura (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    sensor_id bigint not null,
    bodega_id bigint,
    vehiculo_id bigint,
    inicio timestamptz not null,
    fin timestamptz,
    temperatura_extrema_c numeric(4,1) not null,
    minutos_fuera integer not null default 0,
    lotes_bloqueados integer not null default 0,
    estado text not null default 'abierta' constraint ck_excursion_temperatura_estado check (estado in ('abierta', 'cerrada')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check ((bodega_id is null) <> (vehiculo_id is null))
);

create table inventario.bloqueo_lote (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_inventario_id bigint not null,
    motivo text not null constraint ck_bloqueo_lote_motivo check (motivo in ('cadena_frio', 'sanitario', 'calidad', 'retiro')),
    origen_tabla varchar(60),
    origen_id bigint,
    decision text not null default 'pendiente' constraint ck_bloqueo_lote_decision check (decision in ('pendiente', 'liberado', 'descartado')),
    decidido_por bigint,
    decidido_en timestamptz,
    observacion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table comercial.retiro_lote (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_inventario_id bigint not null,
    motivo text not null,
    estado text not null default 'abierto' constraint ck_retiro_lote_estado check (estado in ('abierto', 'clientes_avisados', 'cerrado')),
    abierto_por bigint not null,
    cerrado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table comercial.retiro_aviso (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    retiro_lote_id bigint not null,
    cliente_id bigint not null,
    pedido_id bigint not null,
    cantidad numeric(12,2) not null,
    avisado_en timestamptz,
    medio_aviso text constraint ck_retiro_aviso_medio_aviso check (medio_aviso in ('whatsapp', 'llamada', 'visita', 'correo')),
    cantidad_devuelta numeric(12,2) not null default 0,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, retiro_lote_id, pedido_id)
);

create table comercial.pedido_recurrente (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    cliente_id bigint not null,
    frecuencia text not null constraint ck_pedido_recurrente_frecuencia check (frecuencia in ('semanal', 'quincenal', 'mensual')),
    proxima_fecha date not null,
    canal text not null default 'whatsapp' constraint ck_pedido_recurrente_canal check (canal in ('whatsapp', 'web', 'redes', 'telefono', 'finca', 'mercado_campesino')),
    forma_pago text not null default 'contado' constraint ck_pedido_recurrente_forma_pago check (forma_pago in ('contado', 'credito')),
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table comercial.pedido_recurrente_detalle (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    pedido_recurrente_id bigint not null,
    producto_id bigint not null,
    cantidad numeric(12,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, pedido_recurrente_id, producto_id),
    check (cantidad > 0)
);

create table comercial.permuta (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    factura_id bigint not null,
    documento_soporte_id bigint not null,
    valor_compensado numeric(14,2) not null,
    acuerdo text not null,
    registrado_por bigint not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (valor_compensado > 0)
);

create table comercial.huella_trazabilidad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    lote_inventario_id bigint not null,
    hecho text not null constraint ck_huella_trazabilidad_hecho check (hecho in ('lote_creado', 'despachado', 'bloqueado', 'liberado', 'descartado', 'retirado')),
    contenido jsonb not null,
    hash_anterior char(64),
    hash char(64) not null,
    anclaje_red varchar(40),
    anclaje_transaccion varchar(120),
    anclado_en timestamptz,
    unique (predio_id, id),
    unique (predio_id, hash)
);

create table compras.documento_soporte (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proveedor_id bigint not null,
    orden_compra_id bigint,
    prefijo varchar(6) not null,
    numero integer not null,
    fecha date not null,
    descripcion text not null,
    total numeric(14,2) not null,
    cuds varchar(96),
    estado_dian text not null default 'pendiente' constraint ck_documento_soporte_estado_dian check (estado_dian in ('pendiente', 'aceptado', 'rechazado')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, prefijo, numero)
);

create table ia.modelo_pronostico (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    producto_id bigint not null,
    algoritmo text not null constraint ck_modelo_pronostico_algoritmo check (algoritmo in ('base_estacional', 'promedio_movil', 'ets', 'prophet', 'otro')),
    version varchar(20) not null,
    entrenado_en timestamptz not null,
    meses_historia smallint not null,
    error_mape numeric(6,2),
    activo boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.pronostico_demanda (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    modelo_pronostico_id bigint not null,
    producto_id bigint not null,
    periodo_inicio date not null,
    periodo_fin date not null,
    cantidad numeric(12,2) not null,
    limite_inferior numeric(12,2),
    limite_superior numeric(12,2),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (periodo_fin >= periodo_inicio)
);

create table redes.pieza_audiovisual (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_pieza_audiovisual_tipo check (tipo in ('video_promocional', 'timelapse', 'reel', 'foto')),
    clips jsonb,
    guion text,
    texto_publicacion text,
    musica_ref varchar(120),
    archivo_url varchar(300),
    personas_identificables boolean not null default false,
    estado text not null default 'borrador' constraint ck_pieza_audiovisual_estado check (estado in ('borrador', 'propuesta', 'aprobada', 'rechazada', 'publicada')),
    agente_id bigint,
    aprobado_por bigint,
    publicacion_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table redes.pieza_persona (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    pieza_audiovisual_id bigint not null,
    tercero_id bigint not null,
    unique (predio_id, id),
    unique (predio_id, pieza_audiovisual_id, tercero_id)
);

create table turismo.bloqueo_calendario (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    alojamiento_id bigint,
    plan_turistico_id bigint,
    desde date not null,
    hasta date not null,
    motivo varchar(150) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (hasta >= desde),
    check (alojamiento_id is not null or plan_turistico_id is not null)
);

create table iot.zona_seguridad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_id bigint,
    codigo varchar(20) not null,
    nombre varchar(80) not null,
    tipo text not null constraint ck_zona_seguridad_tipo check (tipo in ('perimetro', 'acceso', 'galpon', 'bodega', 'vivienda', 'otra')),
    paso_personas boolean not null default true,
    bioseguridad boolean not null default false,
    estado_alarma text not null default 'desarmado' constraint ck_zona_seguridad_estado_alarma check (estado_alarma in ('desarmado', 'armado', 'noche', 'mantenimiento')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table iot.cambio_estado_alarma (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_seguridad_id bigint not null,
    estado_anterior varchar(20) not null,
    estado_nuevo varchar(20) not null,
    origen text not null constraint ck_cambio_estado_alarma_origen check (origen in ('app_nube', 'app_red_local', 'teclado', 'horario', 'regla')),
    usuario_id bigint,
    ocurrido_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table iot.credencial_acceso (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    zona_seguridad_id bigint,
    metodo text not null constraint ck_credencial_acceso_metodo check (metodo in ('pin', 'rfid', 'facial')),
    referencia_hash varchar(128),
    consentimiento_id bigint,
    vigente_desde date not null,
    vigente_hasta date,
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (metodo <> 'facial' or consentimiento_id is not null)
);

create table iot.camara (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    dispositivo_id bigint not null,
    zona_id bigint,
    zona_seguridad_id bigint,
    tipo text not null constraint ck_camara_tipo check (tipo in ('ip_rtsp', 'termica', 'timelapse')),
    graba_por_movimiento boolean not null default true,
    intervalo_timelapse_min smallint,
    retencion_dias smallint not null default 30,
    aviso_visible boolean not null default false,
    stream_secreto_ref varchar(120),
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table iot.evento_seguridad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    zona_seguridad_id bigint not null,
    tipo text not null constraint ck_evento_seguridad_tipo check (tipo in ('intrusion', 'puerta_abierta', 'humo', 'gas', 'amoniaco', 'temperatura', 'sabotaje', 'falla_energia', 'acceso_concedido', 'acceso_denegado')),
    detector text not null constraint ck_evento_seguridad_detector check (detector in ('pir', 'magnetico', 'vidrio', 'camara', 'camara_termica', 'sensor_gas', 'lector_acceso', 'manual')),
    sensor_id bigint,
    camara_id bigint,
    credencial_id bigint,
    severidad text not null constraint ck_evento_seguridad_severidad check (severidad in ('informativa', 'media', 'alta', 'critica')),
    estado_alarma varchar(20) not null,
    acciones jsonb,
    ocurrido_en timestamptz not null,
    atendido_por bigint,
    atendido_en timestamptz,
    nota_atencion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table iot.clip_video (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    camara_id bigint not null,
    inicio timestamptz not null,
    fin timestamptz not null,
    motivo text not null constraint ck_clip_video_motivo check (motivo in ('movimiento', 'evento_seguridad', 'timelapse', 'manual')),
    evento_seguridad_id bigint,
    ubicacion text not null default 'pasarela' constraint ck_clip_video_ubicacion check (ubicacion in ('pasarela', 'nube')),
    archivo_url varchar(300) not null,
    para_redes boolean not null default false,
    retener_hasta date not null,
    borrado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (fin > inicio)
);

create table ambiental.factor_emision (
    id bigint generated always as identity primary key,
    magnitud varchar(40) not null,
    factor_kgco2e numeric(12,6) not null,
    fuente varchar(300) not null,
    vigente_desde date not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (magnitud, vigente_desde)
);

create table ambiental.registro_ambiental (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    magnitud text not null constraint ck_registro_ambiental_magnitud check (magnitud in ('kwh_solar', 'm3_biogas', 'kg_compost', 'kg_humus', 'litros_agua_reutilizada', 'litros_agua_consumida')),
    cantidad numeric(12,2) not null,
    fecha date not null,
    origen text not null constraint ck_registro_ambiental_origen check (origen in ('sensor', 'manual')),
    sensor_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (cantidad >= 0)
);

create table personal.cuadrilla (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(80) not null,
    lider_id bigint,
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table personal.cuadrilla_miembro (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    cuadrilla_id bigint not null,
    empleado_id bigint not null,
    desde date not null,
    hasta date,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, cuadrilla_id, empleado_id, desde)
);

create table personal.turno (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    empleado_id bigint not null,
    fecha date not null,
    hora_inicio time not null,
    hora_fin time not null,
    tipo text not null default 'diurno' constraint ck_turno_tipo check (tipo in ('diurno', 'nocturno', 'mixto', 'descanso', 'festivo')),
    area_id bigint,
    cronograma_id bigint,
    horas numeric(4,2),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, empleado_id, fecha, hora_inicio)
);

create table personal.ausencia (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    empleado_id bigint not null,
    tipo text not null constraint ck_ausencia_tipo check (tipo in ('vacaciones', 'permiso', 'incapacidad_general', 'incapacidad_laboral', 'licencia_maternidad', 'licencia_paternidad', 'luto', 'calamidad', 'suspension')),
    desde date not null,
    hasta date not null,
    remunerada boolean not null default true,
    soporte_documento_id bigint,
    aprobada_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (hasta >= desde)
);

create table personal.plantilla_tarea (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    nombre varchar(120) not null,
    proceso varchar(60) not null,
    recurrencia text not null constraint ck_plantilla_tarea_recurrencia check (recurrencia in ('diaria', 'semanal', 'mensual', 'unica')),
    dias_semana smallint[],
    hora_limite time,
    zona_id bigint,
    duracion_estimada_min smallint,
    competencia_id bigint,
    forma_pago text not null default 'ninguna' constraint ck_plantilla_tarea_forma_pago check (forma_pago in ('ninguna', 'jornal', 'destajo')),
    valor_unitario numeric(14,2),
    unidad_destajo varchar(20),
    registro_que_crea text not null default 'ninguno' constraint ck_plantilla_tarea_registro_que_crea check (registro_que_crea in ('ninguno', 'postura', 'alimentacion', 'labor_cultural', 'bioseguridad', 'riego', 'cosecha')),
    pasos jsonb,
    area_id bigint,
    prioridad text not null default 'media' constraint ck_plantilla_tarea_prioridad check (prioridad in ('baja', 'media', 'alta', 'critica')),
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table personal.tarea (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    plantilla_tarea_id bigint,
    titulo varchar(150) not null,
    proceso varchar(60),
    fecha date not null,
    hora_limite timestamptz,
    prioridad text not null default 'media' constraint ck_tarea_prioridad check (prioridad in ('baja', 'media', 'alta', 'critica')),
    zona_id bigint,
    area_id bigint,
    lote_animal_id bigint,
    siembra_id bigint,
    activo_id bigint,
    empleado_id bigint,
    cuadrilla_id bigint,
    origen text not null default 'manual' constraint ck_tarea_origen check (origen in ('plan', 'manual', 'agente', 'orden_trabajo', 'accion_correctiva', 'mision_robot', 'proyecto', 'agenda')),
    agente_id bigint,
    estado text not null default 'pendiente' constraint ck_tarea_estado check (estado in ('pendiente', 'en_curso', 'terminada', 'aprobada', 'devuelta', 'cancelada')),
    iniciada_en timestamptz,
    terminada_en timestamptz,
    cantidad numeric(12,2),
    unidad varchar(20),
    aprobado_por bigint,
    aprobado_en timestamptz,
    comentario_revision text,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (empleado_id is null or cuadrilla_id is null)
);

create table personal.paso_tarea (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tarea_id bigint not null,
    orden smallint not null,
    descripcion varchar(200) not null,
    hecho boolean not null default false,
    hecho_en timestamptz,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, tarea_id, orden)
);

create table personal.evidencia_tarea (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tarea_id bigint not null,
    tipo text not null constraint ck_evidencia_tarea_tipo check (tipo in ('foto', 'lectura_qr', 'lectura_nfc', 'nota_voz', 'documento', 'registro')),
    archivo_url varchar(300),
    registro_tabla varchar(60),
    registro_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table personal.matriz_responsabilidad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proceso varchar(60) not null,
    rol_id bigint not null,
    responsabilidad text not null constraint ck_matriz_responsabilidad_responsabilidad check (responsabilidad in ('responsable', 'aprueba', 'consultado', 'informado')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, proceso, rol_id, responsabilidad)
);

create table personal.asignacion_equipo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    activo_id bigint not null,
    empleado_id bigint not null,
    entregado_en timestamptz not null,
    estado_entrega text not null constraint ck_asignacion_equipo_estado_entrega check (estado_entrega in ('bueno', 'regular', 'malo')),
    devuelto_en timestamptz,
    estado_devolucion text constraint ck_asignacion_equipo_estado_devolucion check (estado_devolucion in ('bueno', 'regular', 'malo', 'perdido')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table personal.credencial_trabajo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    empleado_id bigint not null,
    tipo text not null constraint ck_credencial_trabajo_tipo check (tipo in ('qr', 'nfc')),
    codigo_hash char(64) not null,
    emitida_en date not null,
    revocada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo_hash)
);

create table personal.jornada (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    empleado_id bigint not null,
    fecha date not null,
    entrada timestamptz not null,
    salida timestamptz,
    horas numeric(4,2),
    labor varchar(150),
    zona_id bigint,
    metodo_registro text not null constraint ck_jornada_metodo_registro check (metodo_registro in ('qr', 'nfc', 'manual')),
    aprobada_por bigint,
    aprobada_en timestamptz,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (salida is null or salida > entrada)
);

create table nomina.concepto_nomina (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    nombre varchar(120) not null,
    tipo text not null constraint ck_concepto_nomina_tipo check (tipo in ('devengado', 'deduccion', 'aporte_empleador', 'provision')),
    base text not null constraint ck_concepto_nomina_base check (base in ('salario', 'jornal', 'destajo', 'horas', 'valor_fijo', 'porcentaje')),
    parametro_clave varchar(80),
    constitutivo_salario boolean not null default false,
    cuenta_contable_id bigint,
    codigo_dian varchar(40),
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table nomina.periodo_nomina (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    tipo text not null constraint ck_periodo_nomina_tipo check (tipo in ('mensual', 'quincenal', 'semanal')),
    desde date not null,
    hasta date not null,
    estado text not null default 'abierto' constraint ck_periodo_nomina_estado check (estado in ('abierto', 'prenomina', 'cerrado', 'anulado')),
    preparado_por bigint,
    cerrado_por bigint,
    aprobado_por bigint,
    cerrado_en timestamptz,
    comprobante_id bigint,
    ajusta_periodo_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo),
    check (hasta >= desde)
);

create table nomina.novedad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    periodo_id bigint not null,
    empleado_id bigint not null,
    concepto_id bigint not null,
    cantidad numeric(12,2) not null default 1,
    valor_unitario numeric(14,2) not null default 0,
    valor numeric(14,2) not null,
    origen text not null constraint ck_novedad_origen check (origen in ('contrato', 'tarea', 'jornada', 'ausencia', 'manual')),
    tarea_id bigint,
    jornada_id bigint,
    ausencia_id bigint,
    observacion varchar(200),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, tarea_id),
    unique (predio_id, jornada_id)
);

create table nomina.liquidacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    periodo_id bigint not null,
    empleado_id bigint not null,
    total_devengado numeric(14,2) not null default 0,
    total_deducciones numeric(14,2) not null default 0,
    neto numeric(14,2) not null default 0,
    estado text not null default 'borrador' constraint ck_liquidacion_estado check (estado in ('borrador', 'aprobada', 'pagada')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, periodo_id, empleado_id)
);

create table nomina.liquidacion_detalle (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    liquidacion_id bigint not null,
    concepto_id bigint not null,
    cantidad numeric(12,2) not null,
    valor numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table nomina.provision_prestacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    periodo_id bigint not null,
    empleado_id bigint not null,
    tipo text not null constraint ck_provision_prestacion_tipo check (tipo in ('cesantias', 'intereses_cesantias', 'prima', 'vacaciones')),
    base numeric(14,2) not null,
    valor numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, periodo_id, empleado_id, tipo)
);

create table nomina.documento_nomina_electronica (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    liquidacion_id bigint not null,
    tipo text not null default 'individual' constraint ck_documento_nomina_electronica_tipo check (tipo in ('individual', 'ajuste')),
    proveedor text not null constraint ck_documento_nomina_electronica_proveedor check (proveedor in ('dian_gratuito', 'proveedor_tecnologico')),
    cune varchar(120),
    estado text not null default 'pendiente' constraint ck_documento_nomina_electronica_estado check (estado in ('pendiente', 'enviado', 'aceptado', 'rechazado')),
    enviado_en timestamptz,
    respuesta jsonb,
    xml_url varchar(300),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table nomina.planilla_pila (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    periodo_id bigint not null,
    tipo_planilla varchar(5) not null default 'E',
    archivo_url varchar(300) not null,
    operador varchar(60),
    numero_planilla varchar(30),
    pagada_por bigint,
    pagada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table nomina.pago_nomina (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    liquidacion_id bigint not null,
    medio text not null constraint ck_pago_nomina_medio check (medio in ('transferencia', 'bre_b', 'efectivo')),
    valor numeric(14,2) not null,
    preparado_por bigint not null,
    aprobado_por bigint,
    segunda_aprobacion_por bigint,
    pagado_en timestamptz,
    referencia varchar(80),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (valor > 0)
);

create table nomina.exportacion_nomina (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    periodo_id bigint not null,
    formato text not null constraint ck_exportacion_nomina_formato check (formato in ('csv', 'excel', 'siigo', 'world_office', 'helisa', 'otro')),
    archivo_url varchar(300) not null,
    generado_por bigint not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table formacion.competencia (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(40) not null,
    nombre varchar(120) not null,
    vigencia_meses smallint,
    descripcion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table formacion.curso (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    nombre varchar(150) not null,
    descripcion text,
    publico text not null default 'ambos' constraint ck_curso_publico check (publico in ('operarios', 'estudiantes', 'ambos')),
    modalidad text not null constraint ck_curso_modalidad check (modalidad in ('virtual', 'presencial', 'mixto')),
    competencia_id bigint,
    nota_minima numeric(4,2) not null default 3.5,
    duracion_horas numeric(5,1),
    origen text not null default 'propio' constraint ck_curso_origen check (origen in ('propio', 'sena', 'fao', 'moodle', 'otro')),
    url_externa varchar(300),
    ruta_cargo varchar(60),
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table formacion.leccion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    curso_id bigint not null,
    orden smallint not null,
    titulo varchar(150) not null,
    tipo text not null constraint ck_leccion_tipo check (tipo in ('texto', 'video', 'practica', 'tutorial_pantalla')),
    contenido_url varchar(300),
    pantalla varchar(80),
    documento_id bigint,
    descargable boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, curso_id, orden)
);

create table formacion.evaluacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    curso_id bigint not null,
    titulo varchar(150) not null,
    intentos_max smallint not null default 3,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table formacion.pregunta (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    evaluacion_id bigint not null,
    orden smallint not null,
    enunciado text not null,
    tipo text not null constraint ck_pregunta_tipo check (tipo in ('unica', 'multiple', 'verdadero_falso', 'practica')),
    opciones jsonb,
    respuesta_correcta jsonb,
    puntos numeric(4,1) not null default 1,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, evaluacion_id, orden)
);

create table formacion.inscripcion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    curso_id bigint not null,
    tercero_id bigint not null,
    inscrito_en date not null default current_date,
    estado text not null default 'inscrito' constraint ck_inscripcion_estado check (estado in ('inscrito', 'en_curso', 'aprobado', 'reprobado', 'retirado')),
    nota numeric(4,2),
    aprobado_en date,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, curso_id, tercero_id)
);

create table formacion.progreso (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    inscripcion_id bigint not null,
    leccion_id bigint not null,
    completada_en timestamptz not null,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, inscripcion_id, leccion_id)
);

create table formacion.sesion_presencial (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    curso_id bigint not null,
    instructor_id bigint not null,
    fecha date not null,
    lugar varchar(120),
    duracion_horas numeric(4,1) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table formacion.asistencia (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    sesion_id bigint not null,
    tercero_id bigint not null,
    asistio boolean not null,
    nota numeric(4,2),
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, sesion_id, tercero_id)
);

create table formacion.certificado (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    competencia_id bigint not null,
    inscripcion_id bigint,
    sesion_id bigint,
    emitido_en date not null,
    vence_en date,
    nota numeric(4,2),
    codigo_verificacion varchar(40) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo_verificacion),
    check (inscripcion_id is not null or sesion_id is not null)
);

create table formacion.habilitacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    competencia_id bigint not null,
    certificado_id bigint not null,
    desde date not null,
    hasta date,
    activa boolean not null default true,
    retirada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, certificado_id)
);

create table activos.activo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    tipo text not null constraint ck_activo_tipo check (tipo in ('vehiculo', 'maquinaria', 'herramienta', 'bomba', 'panel_solar', 'bateria', 'equipo_electronico', 'dron', 'robot', 'infraestructura', 'otro')),
    marca varchar(60),
    modelo varchar(60),
    serie varchar(60),
    fecha_compra date,
    valor_compra numeric(14,2),
    valor_residual numeric(14,2) not null default 0,
    vida_util_meses smallint,
    metodo_depreciacion text not null default 'linea_recta' constraint ck_activo_metodo_depreciacion check (metodo_depreciacion in ('linea_recta', 'ninguno')),
    zona_id bigint,
    responsable_id bigint,
    centro_costo_id bigint,
    garantia_hasta date,
    horometro numeric(10,1) not null default 0,
    odometro numeric(10,1) not null default 0,
    vehiculo_id bigint,
    dispositivo_id bigint,
    registro_aerocivil varchar(40),
    estado text not null default 'operativo' constraint ck_activo_estado check (estado in ('operativo', 'en_mantenimiento', 'danado', 'dado_de_baja')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table activos.plan_mantenimiento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    activo_id bigint not null,
    nombre varchar(120) not null,
    tipo text not null default 'preventivo' constraint ck_plan_mantenimiento_tipo check (tipo in ('preventivo', 'predictivo')),
    frecuencia_tipo text not null constraint ck_plan_mantenimiento_frecuencia_tipo check (frecuencia_tipo in ('horas', 'km', 'dias')),
    frecuencia_valor numeric(10,1) not null,
    ultima_lectura numeric(10,1) not null default 0,
    ultima_fecha date,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (frecuencia_valor > 0)
);

create table activos.orden_trabajo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    activo_id bigint not null,
    plan_id bigint,
    tipo text not null constraint ck_orden_trabajo_tipo check (tipo in ('preventivo', 'correctivo', 'predictivo')),
    descripcion text not null,
    estado text not null default 'abierta' constraint ck_orden_trabajo_estado check (estado in ('abierta', 'en_curso', 'cerrada', 'cancelada')),
    tarea_id bigint,
    lectura_cierre numeric(10,1),
    costo_mano_obra numeric(14,2) not null default 0,
    costo_repuestos numeric(14,2) not null default 0,
    cerrada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table activos.repuesto_orden (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    orden_id bigint not null,
    producto_id bigint not null,
    cantidad numeric(10,2) not null,
    movimiento_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (cantidad > 0)
);

create table activos.uso_activo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    activo_id bigint not null,
    fecha date not null,
    empleado_id bigint,
    horas numeric(6,1) not null default 0,
    km numeric(8,1) not null default 0,
    combustible_litros numeric(8,2),
    costo_combustible numeric(14,2),
    centro_costo_id bigint,
    tarea_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (horas >= 0 and km >= 0)
);

create table activos.depreciacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    activo_id bigint not null,
    mes date not null,
    valor numeric(14,2) not null,
    acumulada numeric(14,2) not null,
    comprobante_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, activo_id, mes)
);

create table documental.documento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    titulo varchar(200) not null,
    tipo text not null constraint ck_documento_tipo check (tipo in ('permiso', 'registro', 'contrato', 'protocolo', 'manual', 'ficha_tecnica', 'evidencia', 'acta', 'resultado_laboratorio', 'poliza', 'certificado', 'plan', 'otro')),
    entidad_emisora varchar(120),
    numero varchar(60),
    responsable_id bigint,
    nivel_acceso text not null default 'finca' constraint ck_documento_nivel_acceso check (nivel_acceso in ('finca', 'rol', 'restringido')),
    rol_id bigint,
    contiene_datos_personales boolean not null default false,
    finalidad text,
    conservar_hasta date,
    uso_agentes boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo),
    check (not contiene_datos_personales or (finalidad is not null and conservar_hasta is not null))
);

create table documental.version_documento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    documento_id bigint not null,
    version smallint not null,
    archivo_url varchar(300) not null,
    hash_sha256 char(64) not null,
    estado text not null default 'borrador' constraint ck_version_documento_estado check (estado in ('borrador', 'en_revision', 'aprobada', 'obsoleta')),
    aprobada_por bigint,
    aprobada_en timestamptz,
    vigente_desde date,
    vence_en date,
    avisar_dias smallint not null default 30,
    cambios text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, documento_id, version)
);

create table documental.vinculo_documento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    documento_id bigint not null,
    registro_tabla varchar(60) not null,
    registro_id bigint not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, documento_id, registro_tabla, registro_id)
);

create table cumplimiento.norma (
    id bigint generated always as identity primary key,
    codigo varchar(30) not null unique,
    nombre varchar(200) not null,
    entidad varchar(80) not null,
    referencia varchar(120) not null,
    obligatoria boolean not null,
    condicion_obligatoria text,
    funcion_codigo varchar(40),
    vigencia_certificado_meses smallint,
    url_fuente varchar(300),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table cumplimiento.requisito (
    id bigint generated always as identity primary key,
    norma_id bigint not null,
    codigo varchar(30) not null,
    descripcion text not null,
    tipo_evidencia text not null constraint ck_requisito_tipo_evidencia check (tipo_evidencia in ('documento', 'registro', 'certificado_formacion', 'analisis', 'inspeccion')),
    regla_evidencia varchar(80),
    vigencia_dias smallint,
    critico boolean not null default false,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (norma_id, codigo)
);

create table cumplimiento.expediente (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    norma_id bigint not null,
    estado text not null default 'en_preparacion' constraint ck_expediente_estado check (estado in ('en_preparacion', 'solicitado', 'certificado', 'suspendido', 'vencido')),
    rspa_numero varchar(40),
    numero_certificado varchar(60),
    organismo varchar(120),
    solicitado_en date,
    certificado_en date,
    vence_en date,
    responsable_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, norma_id)
);

create table cumplimiento.evaluacion_requisito (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    expediente_id bigint not null,
    requisito_id bigint not null,
    estado text not null default 'en_proceso' constraint ck_evaluacion_requisito_estado check (estado in ('cumple', 'no_cumple', 'en_proceso', 'no_aplica')),
    origen text not null default 'autoevaluacion' constraint ck_evaluacion_requisito_origen check (origen in ('automatica', 'autoevaluacion', 'auditoria')),
    evaluado_por bigint,
    evaluado_en timestamptz,
    vence_en date,
    observacion text,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, expediente_id, requisito_id)
);

create table cumplimiento.evidencia_requisito (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    evaluacion_id bigint not null,
    documento_id bigint,
    registro_tabla varchar(60),
    registro_id bigint,
    descripcion varchar(200) not null,
    vence_en date,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (documento_id is not null or registro_id is not null)
);

create table cumplimiento.auditoria_externa (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    expediente_id bigint not null,
    tipo text not null constraint ck_auditoria_externa_tipo check (tipo in ('interna', 'externa', 'seguimiento')),
    organismo varchar(120),
    fecha_programada date not null,
    fecha_realizada date,
    resultado text not null default 'pendiente' constraint ck_auditoria_externa_resultado check (resultado in ('pendiente', 'aprobada', 'con_hallazgos', 'rechazada')),
    informe_documento_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table cumplimiento.no_conformidad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    expediente_id bigint not null,
    auditoria_id bigint,
    requisito_id bigint,
    descripcion text not null,
    severidad text not null constraint ck_no_conformidad_severidad check (severidad in ('menor', 'mayor', 'critica')),
    detectada_en date not null,
    estado text not null default 'abierta' constraint ck_no_conformidad_estado check (estado in ('abierta', 'en_tratamiento', 'cerrada')),
    verificacion text,
    cerrada_por bigint,
    cerrada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table cumplimiento.accion_correctiva (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    no_conformidad_id bigint not null,
    descripcion text not null,
    responsable_id bigint not null,
    plazo date not null,
    tarea_id bigint,
    estado text not null default 'pendiente' constraint ck_accion_correctiva_estado check (estado in ('pendiente', 'hecha', 'verificada', 'ineficaz')),
    verificada_por bigint,
    verificada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table seguros.poliza (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    numero varchar(40) not null,
    aseguradora_id bigint not null,
    corredor_id bigint,
    tipo text not null constraint ck_poliza_tipo check (tipo in ('cultivo', 'animales', 'equipos', 'vehiculo', 'responsabilidad_civil', 'dron', 'parametrico', 'vida', 'otro')),
    desde date not null,
    hasta date not null,
    prima numeric(14,2) not null,
    incentivo_pct numeric(5,2) not null default 0,
    valor_subsidiado numeric(14,2) not null default 0,
    suma_asegurada numeric(14,2) not null,
    deducible varchar(120),
    estado text not null default 'en_tramite' constraint ck_poliza_estado check (estado in ('en_tramite', 'vigente', 'vencida', 'cancelada')),
    avisar_dias smallint not null default 30,
    documento_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, numero),
    check (hasta > desde)
);

create table seguros.bien_asegurado (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    poliza_id bigint not null,
    activo_id bigint,
    siembra_id bigint,
    lote_animal_id bigint,
    zona_id bigint,
    descripcion varchar(200) not null,
    valor_asegurado numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table seguros.indice_poliza (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    poliza_id bigint not null,
    variable text not null constraint ck_indice_poliza_variable check (variable in ('lluvia_mm', 'temperatura_c', 'dias_secos', 'viento_kmh', 'otro')),
    fuente_oficial varchar(150) not null,
    comparador text not null constraint ck_indice_poliza_comparador check (comparador in ('mayor', 'menor')),
    umbral numeric(10,2) not null,
    ventana_dias smallint not null,
    sensor_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table seguros.aviso_siniestro (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    poliza_id bigint not null,
    indice_id bigint,
    detectado_en timestamptz not null,
    descripcion text not null,
    serie_datos jsonb,
    estado text not null default 'borrador' constraint ck_aviso_siniestro_estado check (estado in ('borrador', 'revisado', 'enviado', 'pagado', 'rechazado', 'descartado')),
    revisado_por bigint,
    enviado_en timestamptz,
    valor_reclamado numeric(14,2),
    valor_pagado numeric(14,2),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.diagnostico_imagen (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    agente_id bigint not null,
    foto_url varchar(300) not null,
    objetivo text not null constraint ck_diagnostico_imagen_objetivo check (objetivo in ('hoja', 'fruto', 'tallo', 'animal', 'huevo', 'otro')),
    siembra_id bigint,
    lote_animal_id bigint,
    tomada_por bigint not null,
    diagnostico_propuesto varchar(150),
    confianza numeric(4,3),
    resultado jsonb,
    estado text not null default 'pendiente' constraint ck_diagnostico_imagen_estado check (estado in ('pendiente', 'confirmado', 'corregido', 'descartado')),
    diagnostico_final varchar(150),
    revisado_por bigint,
    revisado_en timestamptz,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (confianza is null or confianza between 0 and 1)
);

create table ia.escenario (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(150) not null,
    supuestos jsonb not null,
    resultado jsonb,
    creado_por bigint not null,
    agente_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table ia.decision (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    titulo varchar(200) not null,
    contexto text not null,
    opciones jsonb not null,
    evidencia jsonb,
    opcion_elegida varchar(200),
    decidido_por bigint,
    decidido_en timestamptz,
    resultado_esperado text,
    revisar_en date,
    resultado_real text,
    recomendacion_id bigint,
    escenario_id bigint,
    iniciativa_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table finanzas.clasificacion_costo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    cuenta_id bigint not null,
    elemento text not null constraint ck_clasificacion_costo_elemento check (elemento in ('material_directo', 'mano_obra_directa', 'cif', 'gasto_administracion', 'gasto_ventas', 'gasto_financiero', 'otro')),
    comportamiento text not null constraint ck_clasificacion_costo_comportamiento check (comportamiento in ('fijo', 'variable', 'semivariable', 'escalonado')),
    parte_fija_pct numeric(5,2),
    controlable boolean not null default true,
    es_costo_producto boolean not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, cuenta_id),
    check (parte_fija_pct is null or parte_fija_pct between 0 and 100)
);

create table finanzas.actividad_costo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    nombre varchar(120) not null,
    inductor varchar(60) not null,
    centro_costo_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table finanzas.asignacion_costo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    mes date not null,
    actividad_id bigint not null,
    centro_costo_id bigint not null,
    cantidad_inductor numeric(14,2) not null,
    valor_asignado numeric(14,2),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, mes, actividad_id, centro_costo_id)
);

create table finanzas.costo_estandar (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    producto_id bigint not null,
    vigente_desde date not null,
    material_directo numeric(14,2) not null,
    mano_obra_directa numeric(14,2) not null,
    cif numeric(14,2) not null,
    costo_variable_unitario numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, producto_id, vigente_desde)
);

create table finanzas.presupuesto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(150) not null,
    anio smallint not null,
    version smallint not null default 1,
    base_cero boolean not null default false,
    fuente text not null default 'propio' constraint ck_presupuesto_fuente check (fuente in ('propio', 'fondo_emprender', 'credito', 'mixto')),
    estado text not null default 'borrador' constraint ck_presupuesto_estado check (estado in ('borrador', 'aprobado', 'cerrado')),
    aprobado_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, anio, nombre, version)
);

create table finanzas.premisa_presupuesto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    presupuesto_id bigint not null,
    tipo text not null constraint ck_premisa_presupuesto_tipo check (tipo in ('macroeconomica', 'microeconomica')),
    variable varchar(80) not null,
    valor numeric(14,4) not null,
    fuente varchar(200),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, presupuesto_id, variable)
);

create table finanzas.presupuesto_detalle (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    presupuesto_id bigint not null,
    componente text not null constraint ck_presupuesto_detalle_componente check (componente in ('ventas', 'produccion', 'materia_prima', 'mano_obra', 'cif', 'gastos_operacion', 'inversion', 'financiacion', 'flujo_caja')),
    mes smallint not null,
    centro_costo_id bigint,
    cuenta_id bigint,
    producto_id bigint,
    cantidad numeric(14,2),
    valor numeric(14,2) not null,
    justificacion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (mes between 1 and 12)
);

create table finanzas.estado_financiero (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_estado_financiero_tipo check (tipo in ('balance_general', 'resultados_absorbente', 'resultados_variable', 'flujo_efectivo_directo', 'flujo_efectivo_indirecto', 'cambios_patrimonio')),
    desde date not null,
    hasta date not null,
    presupuestado boolean not null default false,
    datos jsonb not null,
    generado_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table finanzas.indicador (
    id bigint generated always as identity primary key,
    codigo varchar(40) not null unique,
    nombre varchar(150) not null,
    grupo text not null constraint ck_indicador_grupo check (grupo in ('liquidez', 'endeudamiento', 'rentabilidad', 'actividad', 'valor', 'riesgo', 'palanca', 'produccion', 'comercial', 'personal', 'proyecto')),
    formula text not null,
    interpretacion text,
    unidad text not null constraint ck_indicador_unidad check (unidad in ('veces', 'porcentaje', 'pesos', 'dias', 'unidades')),
    sentido text not null constraint ck_indicador_sentido check (sentido in ('mayor_mejor', 'menor_mejor', 'rango')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table finanzas.valor_indicador (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    indicador_id bigint not null,
    desde date not null,
    hasta date not null,
    centro_costo_id bigint,
    valor numeric(18,4),
    meta numeric(18,4),
    semaforo text not null constraint ck_valor_indicador_semaforo check (semaforo in ('verde', 'amarillo', 'rojo', 'sin_meta', 'sin_dato')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table finanzas.anticipo_proveedor (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proveedor_id bigint not null,
    fecha date not null,
    valor numeric(14,2) not null,
    saldo numeric(14,2) not null,
    comprobante_id bigint,
    estado text not null default 'abierto' constraint ck_anticipo_proveedor_estado check (estado in ('abierto', 'aplicado', 'devuelto')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (valor > 0 and saldo >= 0 and saldo <= valor)
);

create table finanzas.aplicacion_anticipo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    anticipo_id bigint not null,
    orden_compra_id bigint not null,
    valor numeric(14,2) not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (valor > 0)
);

create table finanzas.reporte_indicadores (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    destinatario text not null constraint ck_reporte_indicadores_destinatario check (destinatario in ('finagro', 'banco', 'gremio', 'certificador', 'fondo_emprender', 'otro')),
    tercero_id bigint,
    desde date not null,
    hasta date not null,
    contenido jsonb not null,
    hash_sha256 char(64) not null,
    autorizado_por bigint not null,
    enviado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table iot.mision_robot (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    activo_id bigint not null,
    tipo text not null constraint ck_mision_robot_tipo check (tipo in ('dron_monitoreo', 'robot_deshierbe', 'robot_monitoreo')),
    zona_id bigint not null,
    estado text not null default 'propuesta' constraint ck_mision_robot_estado check (estado in ('propuesta', 'aprobada', 'en_curso', 'terminada', 'abortada')),
    aprobada_por bigint,
    piloto_id bigint,
    poliza_id bigint,
    altura_max_m numeric(5,1),
    zona_sin_personas boolean not null default false,
    parada_emergencia_probada boolean not null default false,
    inicio timestamptz,
    fin timestamptz,
    resultado jsonb,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table iot.prioridad_carga (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    actuador_id bigint not null,
    prioridad smallint not null,
    esencial boolean not null,
    corte_bateria_pct smallint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, actuador_id),
    check (prioridad between 1 and 5),
    check (not esencial or corte_bateria_pct is null)
);

create table nucleo.llave_api (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tercero_id bigint not null,
    nombre varchar(80) not null,
    prefijo varchar(12) not null,
    hash_llave char(64) not null,
    alcances text[] not null default '{catalogo:leer}',
    limite_por_minuto smallint not null default 60,
    activa boolean not null default false,
    vence_en date not null,
    ultimo_uso timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, prefijo)
);

create table nucleo.webhook_suscripcion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(80) not null,
    tercero_id bigint,
    url varchar(300) not null,
    eventos text[] not null,
    secreto_ref varchar(120) not null,
    activa boolean not null default false,
    fallos_seguidos smallint not null default 0,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (url like 'https://%')
);

create table nucleo.webhook_entrega (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    suscripcion_id bigint not null,
    evento_salida_id bigint not null,
    estado text not null default 'pendiente' constraint ck_webhook_entrega_estado check (estado in ('pendiente', 'entregado', 'fallido')),
    intentos smallint not null default 0,
    codigo_respuesta smallint,
    proximo_intento timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, suscripcion_id, evento_salida_id)
);

create table seguridad.factor_autenticacion (
    id bigint generated always as identity primary key,
    usuario_id bigint not null,
    tipo text not null constraint ck_factor_autenticacion_tipo check (tipo in ('totp', 'webauthn', 'codigo_respaldo')),
    nombre varchar(60) not null,
    secreto_ref varchar(120) not null,
    activo boolean not null default true,
    ultimo_uso timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table seguridad.sesion_usuario (
    id bigint generated always as identity primary key,
    usuario_id bigint not null,
    metodo text not null constraint ck_sesion_usuario_metodo check (metodo in ('contrasena', 'doble_factor', 'llave_acceso', 'token_dispositivo')),
    ip inet not null,
    agente_usuario varchar(300),
    dispositivo_captura_id bigint,
    iniciada_en timestamptz not null default now(),
    vence_en timestamptz not null,
    revocada_en timestamptz,
    motivo_revocacion varchar(120),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table seguridad.intento_acceso (
    id bigint generated always as identity primary key,
    correo citext not null,
    usuario_id bigint,
    ip inet not null,
    exito boolean not null,
    motivo_fallo text constraint ck_intento_acceso_motivo_fallo check (motivo_fallo in ('contrasena', 'usuario_inexistente', 'cuenta_bloqueada', 'ip_bloqueada', 'segundo_factor', 'cuenta_inactiva', 'senuelo')),
    agente_usuario varchar(300),
    ocurrido_en timestamptz not null default now()
);

create table seguridad.regla_deteccion (
    id bigint generated always as identity primary key,
    codigo varchar(40) not null unique,
    descripcion text not null,
    umbral smallint not null,
    ventana_min smallint not null,
    severidad text not null constraint ck_regla_deteccion_severidad check (severidad in ('baja', 'media', 'alta', 'critica')),
    respuesta text not null constraint ck_regla_deteccion_respuesta check (respuesta in ('alertar', 'bloquear_ip', 'bloquear_cuenta', 'revocar_sesiones')),
    bloqueo_min smallint not null default 30,
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table seguridad.bloqueo (
    id bigint generated always as identity primary key,
    tipo text not null constraint ck_bloqueo_tipo check (tipo in ('cuenta', 'ip')),
    usuario_id bigint,
    ip cidr,
    regla_id bigint,
    motivo varchar(200) not null,
    desde timestamptz not null default now(),
    hasta timestamptz,
    levantado_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    check ((tipo = 'cuenta' and usuario_id is not null) or (tipo = 'ip' and ip is not null))
);

create table seguridad.senuelo (
    id bigint generated always as identity primary key,
    tipo text not null constraint ck_senuelo_tipo check (tipo in ('cuenta', 'llave_api', 'url', 'registro')),
    valor varchar(200) not null unique,
    descripcion varchar(200),
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table seguridad.alerta_seguridad (
    id bigint generated always as identity primary key,
    tipo text not null constraint ck_alerta_seguridad_tipo check (tipo in ('fuerza_bruta', 'relleno_credenciales', 'senuelo', 'escalada_privilegios', 'cambio_permisos', 'exportacion_masiva', 'acceso_ip_nueva', 'sesion_sin_doble_factor', 'inyeccion', 'abuso_api', 'dispositivo_desconocido', 'firmware_no_firmado', 'copia_fallida', 'otro')),
    severidad text not null constraint ck_alerta_seguridad_severidad check (severidad in ('baja', 'media', 'alta', 'critica')),
    fuente text not null constraint ck_alerta_seguridad_fuente check (fuente in ('app', 'base_datos', 'waf', 'api', 'pasarela', 'agente_ia', 'monitoreo')),
    regla_id bigint,
    usuario_id bigint,
    ip inet,
    predio_id bigint,
    detalle jsonb,
    ocurrido_en timestamptz not null default now(),
    estado text not null default 'nueva' constraint ck_alerta_seguridad_estado check (estado in ('nueva', 'en_analisis', 'contenida', 'falso_positivo', 'cerrada')),
    atendida_por bigint,
    incidente_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table seguridad.incidente (
    id bigint generated always as identity primary key,
    titulo varchar(200) not null,
    severidad text not null constraint ck_incidente_severidad check (severidad in ('baja', 'media', 'alta', 'critica')),
    estado text not null default 'abierto' constraint ck_incidente_estado check (estado in ('abierto', 'contenido', 'erradicado', 'cerrado')),
    responsable_id bigint not null,
    datos_personales_afectados boolean not null default false,
    reportado_sic_en date,
    abierto_en timestamptz not null default now(),
    cerrado_en timestamptz,
    lecciones text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now()
);

create table seguridad.ejecucion_prueba (
    id bigint generated always as identity primary key,
    tipo text not null constraint ck_ejecucion_prueba_tipo check (tipo in ('unitaria', 'integracion', 'reglas_bd', 'extremo_a_extremo', 'carga', 'dependencias', 'sast', 'dast', 'pentest', 'restauracion_copia', 'simulacro_incidente')),
    suite varchar(80) not null,
    version_sistema varchar(20) not null,
    entorno text not null constraint ck_ejecucion_prueba_entorno check (entorno in ('desarrollo', 'pruebas', 'practica', 'produccion')),
    total integer not null,
    aprobadas integer not null,
    fallidas integer not null,
    hallazgos_criticos integer not null default 0,
    herramienta varchar(60),
    informe_url varchar(300),
    ejecutada_en timestamptz not null default now(),
    ejecutada_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    check (aprobadas + fallidas <= total)
);

create table seguridad.copia_seguridad (
    id bigint generated always as identity primary key,
    alcance text not null constraint ck_copia_seguridad_alcance check (alcance in ('postgresql', 'mongodb', 'archivos', 'configuracion')),
    destino text not null constraint ck_copia_seguridad_destino check (destino in ('local', 'nube', 'disco_externo')),
    inicio timestamptz not null,
    fin timestamptz,
    tamano_mb numeric(12,1),
    hash_sha256 char(64),
    cifrada boolean not null,
    exitosa boolean not null,
    restauracion_probada_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    check (cifrada)
);

create table crm.segmento (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    nombre varchar(120) not null,
    criterios jsonb,
    propuesta_valor text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table crm.campana (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(150) not null,
    canal text not null constraint ck_campana_canal check (canal in ('whatsapp', 'instagram', 'facebook', 'tiktok', 'feria', 'mercado_campesino', 'visita_finca', 'referidos', 'web', 'volanteo', 'otro')),
    segmento_id bigint,
    objetivo text,
    desde date not null,
    hasta date,
    presupuesto numeric(14,2) not null default 0,
    costo_real numeric(14,2) not null default 0,
    publicacion_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table crm.formulario_captura (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(30) not null,
    nombre varchar(120) not null,
    canal text not null constraint ck_formulario_captura_canal check (canal in ('web', 'qr_feria', 'whatsapp', 'tablet_finca', 'otro')),
    campos jsonb not null,
    texto_autorizacion text not null,
    finalidad text not null,
    campana_id bigint,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table crm.prospecto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_prospecto_tipo check (tipo in ('persona', 'empresa')),
    nombre varchar(150) not null,
    nit varchar(20),
    sector text not null constraint ck_prospecto_sector check (sector in ('hogar', 'tienda', 'restaurante', 'hotel', 'colegio', 'casino', 'supermercado', 'distribuidor', 'exportador', 'agencia_turismo', 'institucion', 'otro')),
    municipio varchar(80),
    telefono varchar(20),
    correo citext,
    canal_origen text not null constraint ck_prospecto_canal_origen check (canal_origen in ('whatsapp', 'instagram', 'facebook', 'tiktok', 'feria', 'mercado_campesino', 'visita_finca', 'referido', 'web', 'llamada', 'base_publica', 'otro')),
    formulario_id bigint,
    campana_id bigint,
    segmento_id bigint,
    intereses text[],
    volumen_estimado_mes numeric(14,2),
    etapa text not null default 'nuevo' constraint ck_prospecto_etapa check (etapa in ('nuevo', 'contactado', 'calificado', 'propuesta', 'negociacion', 'ganado', 'perdido', 'descartado')),
    puntaje smallint not null default 0,
    responsable_id bigint,
    consentimiento_id bigint,
    tercero_id bigint,
    motivo_perdida varchar(200),
    proximo_contacto date,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (puntaje between 0 and 100)
);

create table crm.contacto_empresa (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    prospecto_id bigint not null,
    nombre varchar(150) not null,
    cargo varchar(80),
    telefono varchar(20),
    correo citext,
    consentimiento_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table crm.interaccion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    prospecto_id bigint,
    tercero_id bigint,
    tipo text not null constraint ck_interaccion_tipo check (tipo in ('llamada', 'whatsapp', 'visita', 'correo', 'reunion', 'degustacion', 'feria', 'visita_finca')),
    fecha timestamptz not null,
    resumen text not null,
    proximo_paso varchar(200),
    usuario_id bigint,
    agente_id bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (prospecto_id is not null or tercero_id is not null)
);

create table crm.oportunidad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    prospecto_id bigint,
    tercero_id bigint,
    titulo varchar(150) not null,
    productos jsonb,
    valor_estimado numeric(14,2) not null,
    probabilidad_pct smallint not null,
    cierre_estimado date,
    estado text not null default 'abierta' constraint ck_oportunidad_estado check (estado in ('abierta', 'ganada', 'perdida')),
    pedido_id bigint,
    linea_negocio_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (probabilidad_pct between 0 and 100),
    check (prospecto_id is not null or tercero_id is not null)
);

create table estrategia.linea_negocio (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    centro_costo_id bigint,
    estado text not null default 'actual' constraint ck_linea_negocio_estado check (estado in ('actual', 'en_estudio', 'piloto', 'descartada', 'cerrada')),
    palanca_dominante text constraint ck_linea_negocio_palanca_dominante check (palanca_dominante in ('mercadeo', 'produccion', 'operacional', 'financiera')),
    descripcion text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table estrategia.factor_dofa (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_factor_dofa_tipo check (tipo in ('debilidad', 'oportunidad', 'fortaleza', 'amenaza')),
    linea_negocio_id bigint,
    descripcion text not null,
    impacto smallint not null,
    fuente varchar(200),
    vigente boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (impacto between 1 and 5)
);

create table estrategia.estudio_mercado (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    mercado varchar(150) not null,
    segmento_id bigint,
    tamano_estimado numeric(14,2),
    precio_referencia numeric(14,2),
    competidores text,
    barreras text,
    fuente varchar(200) not null,
    fecha date not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table estrategia.iniciativa (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    titulo varchar(200) not null,
    descripcion text not null,
    ansoff text not null constraint ck_iniciativa_ansoff check (ansoff in ('penetracion_mercado', 'desarrollo_mercado', 'desarrollo_producto', 'diversificacion')),
    tipo text not null constraint ck_iniciativa_tipo check (tipo in ('nuevo_mercado', 'nuevo_producto', 'nuevo_canal', 'nueva_linea', 'valor_agregado', 'integracion_vertical', 'mejora_proceso')),
    palanca text not null constraint ck_iniciativa_palanca check (palanca in ('mercadeo', 'produccion', 'operacional', 'financiera')),
    linea_negocio_id bigint,
    segmento_id bigint,
    hipotesis text,
    estado text not null default 'idea' constraint ck_iniciativa_estado check (estado in ('idea', 'en_evaluacion', 'aprobada', 'piloto', 'escalada', 'descartada')),
    propuesta_por bigint,
    agente_id bigint,
    aprobada_por bigint,
    aprobada_en timestamptz,
    puntaje numeric(5,2),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table estrategia.evaluacion_proyecto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    iniciativa_id bigint not null,
    version smallint not null default 1,
    inversion_inicial numeric(14,2) not null,
    horizonte_meses smallint not null,
    tasa_descuento_anual numeric(6,4) not null,
    precio_unitario numeric(14,2),
    costo_variable_unitario numeric(14,2),
    costos_fijos_mes numeric(14,2),
    intereses_mes numeric(14,2) not null default 0,
    unidades_mes numeric(12,2),
    fuente_fondos text not null constraint ck_evaluacion_proyecto_fuente_fondos check (fuente_fondos in ('utilidades_retenidas', 'credito', 'fondo_emprender', 'aporte_familia', 'mixto')),
    vpn numeric(14,2),
    tir_anual numeric(8,4),
    roi_pct numeric(8,2),
    recuperacion_meses smallint,
    punto_equilibrio_unidades numeric(12,2),
    margen_seguridad_pct numeric(8,2),
    gpo numeric(10,4),
    gpf numeric(10,4),
    gpt numeric(10,4),
    riesgos text,
    calculado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, iniciativa_id, version),
    check (inversion_inicial >= 0 and horizonte_meses > 0)
);

create table estrategia.flujo_proyecto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    evaluacion_id bigint not null,
    mes smallint not null,
    ingresos numeric(14,2) not null default 0,
    egresos numeric(14,2) not null default 0,
    inversion numeric(14,2) not null default 0,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, evaluacion_id, mes)
);

create table estrategia.reinversion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    anio smallint not null,
    mes smallint not null,
    linea_origen_id bigint not null,
    utilidad_linea numeric(14,2) not null,
    valor numeric(14,2) not null,
    iniciativa_id bigint not null,
    estado text not null default 'propuesta' constraint ck_reinversion_estado check (estado in ('propuesta', 'aprobada', 'ejecutada', 'cancelada')),
    aprobada_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (valor > 0),
    check (mes between 1 and 12)
);

create table estrategia.seguimiento_iniciativa (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    iniciativa_id bigint not null,
    mes date not null,
    ingresos_reales numeric(14,2) not null default 0,
    egresos_reales numeric(14,2) not null default 0,
    unidades_reales numeric(12,2),
    nota text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, iniciativa_id, mes)
);

create table estrategia.objetivo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    perspectiva text not null constraint ck_objetivo_perspectiva check (perspectiva in ('financiera', 'clientes', 'procesos', 'aprendizaje')),
    descripcion text not null,
    indicador_id bigint,
    meta numeric(18,4),
    fecha_meta date,
    responsable_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table personal.area_responsabilidad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    descripcion text,
    zonas bigint[],
    centro_costo_id bigint,
    opera_24_7 boolean not null default false,
    activa boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table personal.miembro_area (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    area_id bigint not null,
    empleado_id bigint not null,
    es_responsable boolean not null default false,
    desde date not null,
    hasta date,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, area_id, empleado_id, desde)
);

create table personal.patron_turno (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    tipo text not null constraint ck_patron_turno_tipo check (tipo in ('semanal', 'ciclico', 'flexible')),
    ciclo_dias smallint not null default 7,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo),
    check (ciclo_dias between 1 and 56)
);

create table personal.patron_turno_detalle (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    patron_id bigint not null,
    dia_ciclo smallint not null,
    hora_inicio time,
    hora_fin time,
    tipo text not null constraint ck_patron_turno_detalle_tipo check (tipo in ('diurno', 'nocturno', 'mixto', 'descanso')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, patron_id, dia_ciclo, hora_inicio),
    check ((tipo = 'descanso') = (hora_inicio is null))
);

create table personal.cronograma (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    nombre varchar(150) not null,
    area_id bigint not null,
    desde date not null,
    hasta date not null,
    estado text not null default 'borrador' constraint ck_cronograma_estado check (estado in ('borrador', 'publicado', 'cerrado')),
    permitir_huecos boolean not null default false,
    publicado_por bigint,
    publicado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (hasta >= desde)
);

create table personal.asignacion_patron (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    cronograma_id bigint not null,
    empleado_id bigint not null,
    patron_id bigint not null,
    desfase_dias smallint not null default 0,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, cronograma_id, empleado_id)
);

create table personal.requerimiento_cobertura (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    area_id bigint not null,
    dia_semana smallint,
    hora_inicio time not null,
    hora_fin time not null,
    personas_min smallint not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (personas_min > 0),
    check (dia_semana is null or dia_semana between 1 and 7)
);

create table personal.disponibilidad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    empleado_id bigint not null,
    dia_semana smallint not null,
    hora_inicio time not null,
    hora_fin time not null,
    preferencia text not null constraint ck_disponibilidad_preferencia check (preferencia in ('disponible', 'preferido', 'no_disponible')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (dia_semana between 1 and 7)
);

create table agenda.recurso (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(120) not null,
    tipo text not null constraint ck_recurso_tipo check (tipo in ('cabana', 'salon', 'zona_camping', 'vehiculo', 'equipo', 'punto_cargue', 'sala', 'otro')),
    alojamiento_id bigint,
    activo_id bigint,
    zona_id bigint,
    capacidad smallint,
    minutos_preparacion smallint not null default 0,
    activo boolean not null default true,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo),
    unique (predio_id, alojamiento_id)
);

create table agenda.cita (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    recurso_id bigint not null,
    titulo varchar(150) not null,
    tipo text not null constraint ck_cita_tipo check (tipo in ('reserva_turistica', 'limpieza', 'mantenimiento', 'uso_familiar', 'bloqueo', 'entrega_proveedor', 'recogida_cliente', 'capacitacion', 'auditoria', 'reunion', 'otro')),
    inicio timestamptz not null,
    fin timestamptz not null,
    fin_con_preparacion timestamptz,
    estado text not null default 'confirmada' constraint ck_cita_estado check (estado in ('tentativa', 'confirmada', 'cumplida', 'cancelada')),
    reserva_id bigint,
    bloqueo_id bigint,
    tarea_id bigint,
    responsable_id bigint,
    notas text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (fin > inicio),
    exclude using gist (predio_id with =, recurso_id with =, tstzrange(inicio, fin_con_preparacion) with &&) where (estado in ('tentativa', 'confirmada'))
);

create table agenda.visita (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_visita_tipo check (tipo in ('proveedor', 'cliente', 'turista', 'contratista', 'tecnico', 'autoridad', 'visitante', 'transportador')),
    nombre varchar(150) not null,
    tercero_id bigint,
    personas smallint not null default 1,
    vehiculo_placa varchar(10),
    vehiculo_tipo text constraint ck_visita_vehiculo_tipo check (vehiculo_tipo in ('carro', 'camioneta', 'camion', 'moto', 'tractor', 'bicicleta')),
    motivo varchar(200) not null,
    zona_destino_id bigint,
    ingreso_programado timestamptz not null,
    salida_programada timestamptz not null,
    anfitrion_id bigint not null,
    requiere_bioseguridad boolean not null default false,
    contacto_aves_reciente boolean,
    pase_hash char(64),
    estado text not null default 'solicitada' constraint ck_visita_estado check (estado in ('solicitada', 'aprobada', 'rechazada', 'en_sitio', 'salio', 'no_llego', 'cancelada')),
    aprobada_por bigint,
    motivo_rechazo varchar(200),
    cita_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, pase_hash),
    check (salida_programada > ingreso_programado)
);

create table agenda.registro_acceso (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    sentido text not null constraint ck_registro_acceso_sentido check (sentido in ('entrada', 'salida')),
    tipo text not null constraint ck_registro_acceso_tipo check (tipo in ('persona', 'vehiculo')),
    visita_id bigint,
    empleado_id bigint,
    nombre varchar(150),
    placa varchar(10),
    punto varchar(40) not null default 'porteria',
    metodo text not null constraint ck_registro_acceso_metodo check (metodo in ('pase_qr', 'carne_qr', 'carne_nfc', 'manual', 'lectura_placa')),
    desinfeccion boolean not null default false,
    ocurrido_en timestamptz not null default now(),
    registrado_por bigint,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (visita_id is not null or empleado_id is not null or nombre is not null or placa is not null)
);

create table formacion.necesidad_formacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    origen text not null constraint ck_necesidad_formacion_origen check (origen in ('cargo', 'no_conformidad', 'cambio', 'solicitud', 'evaluacion_desempeno', 'norma')),
    descripcion text not null,
    tercero_id bigint,
    competencia_id bigint,
    curso_id bigint,
    estado text not null default 'abierta' constraint ck_necesidad_formacion_estado check (estado in ('abierta', 'planificada', 'atendida', 'descartada')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table formacion.encuesta (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    curso_id bigint,
    sesion_id bigint,
    tercero_id bigint,
    satisfaccion smallint not null,
    utilidad smallint not null,
    instructor smallint,
    comentario text,
    id_cliente uuid unique,
    capturado_en timestamptz,
    dispositivo_captura_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (satisfaccion between 1 and 5 and utilidad between 1 and 5 and (instructor is null or instructor between 1 and 5))
);

create table formacion.queja_apelacion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    tipo text not null constraint ck_queja_apelacion_tipo check (tipo in ('queja', 'apelacion')),
    tercero_id bigint not null,
    curso_id bigint,
    certificado_id bigint,
    descripcion text not null,
    presentada_en date not null default current_date,
    responder_antes date not null,
    estado text not null default 'recibida' constraint ck_queja_apelacion_estado check (estado in ('recibida', 'en_estudio', 'resuelta', 'rechazada')),
    respuesta text,
    resuelta_por bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table proyectos.proyecto (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    codigo varchar(20) not null,
    nombre varchar(200) not null,
    objetivo text not null,
    justificacion text,
    criterios_exito text,
    iniciativa_id bigint,
    linea_negocio_id bigint,
    enfoque text not null default 'hibrido' constraint ck_proyecto_enfoque check (enfoque in ('predictivo', 'adaptativo', 'hibrido')),
    area_enfoque text not null default 'inicio' constraint ck_proyecto_area_enfoque check (area_enfoque in ('inicio', 'planificacion', 'ejecucion', 'monitoreo_control', 'cierre')),
    estado text not null default 'propuesto' constraint ck_proyecto_estado check (estado in ('propuesto', 'aprobado', 'en_curso', 'suspendido', 'cerrado', 'cancelado')),
    patrocinador_id bigint,
    director_id bigint,
    presupuesto numeric(14,2),
    fuente_fondos text constraint ck_proyecto_fuente_fondos check (fuente_fondos in ('utilidades_retenidas', 'credito', 'fondo_emprender', 'aporte_familia', 'convenio', 'mixto')),
    inicio_plan date,
    fin_plan date,
    inicio_real date,
    fin_real date,
    acta_documento_id bigint,
    aprobado_por bigint,
    aprobado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, codigo)
);

create table proyectos.interesado (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    tercero_id bigint,
    usuario_id bigint,
    nombre varchar(150) not null,
    rol varchar(80),
    interes smallint not null,
    influencia smallint not null,
    estrategia varchar(30),
    expectativas text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (interes between 1 and 5 and influencia between 1 and 5)
);

create table proyectos.elemento_edt (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    padre_id bigint,
    codigo varchar(20) not null,
    nombre varchar(200) not null,
    es_entregable boolean not null default false,
    criterio_aceptacion text,
    estado text not null default 'pendiente' constraint ck_elemento_edt_estado check (estado in ('pendiente', 'en_curso', 'terminado', 'aceptado', 'rechazado')),
    aceptado_por bigint,
    aceptado_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, proyecto_id, codigo),
    check (not es_entregable or criterio_aceptacion is not null)
);

create table proyectos.iteracion (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    numero smallint not null,
    objetivo text,
    inicio date not null,
    fin date not null,
    estado text not null default 'planeada' constraint ck_iteracion_estado check (estado in ('planeada', 'en_curso', 'cerrada')),
    retrospectiva text,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, proyecto_id, numero),
    check (fin >= inicio)
);

create table proyectos.actividad (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    elemento_edt_id bigint,
    iteracion_id bigint,
    codigo varchar(20) not null,
    nombre varchar(200) not null,
    es_hito boolean not null default false,
    duracion_dias smallint not null,
    inicio_temprano smallint,
    fin_temprano smallint,
    inicio_tardio smallint,
    fin_tardio smallint,
    holgura smallint,
    critica boolean not null default false,
    inicio_plan date,
    fin_plan date,
    inicio_real date,
    fin_real date,
    avance_pct numeric(5,2) not null default 0,
    costo_plan numeric(14,2) not null default 0,
    costo_real numeric(14,2) not null default 0,
    responsable_id bigint,
    area_id bigint,
    tarea_id bigint,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, proyecto_id, codigo),
    check (avance_pct between 0 and 100),
    check (duracion_dias >= 0 and (not es_hito or duracion_dias = 0))
);

create table proyectos.dependencia (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    predecesora_id bigint not null,
    sucesora_id bigint not null,
    tipo text not null default 'FC' constraint ck_dependencia_tipo check (tipo in ('FC', 'CC', 'FF', 'CF')),
    desfase_dias smallint not null default 0,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, predecesora_id, sucesora_id),
    check (predecesora_id <> sucesora_id)
);

create table proyectos.riesgo (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    descripcion text not null,
    tipo text not null default 'amenaza' constraint ck_riesgo_tipo check (tipo in ('amenaza', 'oportunidad')),
    categoria text not null constraint ck_riesgo_categoria check (categoria in ('tecnico', 'clima', 'sanitario', 'mercado', 'financiero', 'legal', 'personas', 'proveedor', 'seguridad')),
    probabilidad smallint not null,
    impacto smallint not null,
    severidad smallint generated always as (probabilidad * impacto) stored,
    respuesta text constraint ck_riesgo_respuesta check (respuesta in ('evitar', 'mitigar', 'transferir', 'aceptar', 'escalar', 'explotar', 'mejorar', 'compartir')),
    plan_respuesta text,
    disparador varchar(200),
    responsable_id bigint,
    estado text not null default 'identificado' constraint ck_riesgo_estado check (estado in ('identificado', 'en_respuesta', 'materializado', 'cerrado')),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    check (probabilidad between 1 and 5 and impacto between 1 and 5)
);

create table proyectos.registro (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    tipo text not null constraint ck_registro_tipo check (tipo in ('incidente', 'supuesto', 'restriccion', 'decision', 'leccion_aprendida')),
    descripcion text not null,
    responsable_id bigint,
    estado text not null default 'abierto' constraint ck_registro_estado check (estado in ('abierto', 'cerrado')),
    fecha date not null default current_date,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table proyectos.solicitud_cambio (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    descripcion text not null,
    solicitada_por bigint not null,
    impacto_alcance text,
    impacto_dias smallint not null default 0,
    impacto_costo numeric(14,2) not null default 0,
    estado text not null default 'propuesta' constraint ck_solicitud_cambio_estado check (estado in ('propuesta', 'aprobada', 'rechazada')),
    decidida_por bigint,
    decidida_en timestamptz,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id)
);

create table proyectos.linea_base (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    version smallint not null,
    presupuesto numeric(14,2) not null,
    fin_plan date not null,
    alcance text not null,
    solicitud_cambio_id bigint,
    aprobada_por bigint not null,
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, proyecto_id, version)
);

create table proyectos.medicion_valor_ganado (
    id bigint generated always as identity primary key,
    predio_id bigint not null default nucleo.predio_actual(),
    proyecto_id bigint not null,
    fecha_corte date not null,
    pv numeric(14,2) not null,
    ev numeric(14,2) not null,
    ac numeric(14,2) not null,
    cpi numeric(8,4),
    spi numeric(8,4),
    eac numeric(14,2),
    etc numeric(14,2),
    vac numeric(14,2),
    creado_en timestamptz not null default now(),
    actualizado_en timestamptz not null default now(),
    unique (predio_id, id),
    unique (predio_id, proyecto_id, fecha_corte)
);

-- Llaves foráneas (compuestas con predio_id entre tablas operativas)
alter table nucleo.usuario add constraint fk_usuario_tercero_id foreign key (tercero_id) references terceros.tercero(id);
alter table nucleo.rol_permiso add constraint fk_rol_permiso_rol_id foreign key (rol_id) references nucleo.rol(id);
alter table nucleo.rol_permiso add constraint fk_rol_permiso_permiso_id foreign key (permiso_id) references nucleo.permiso(id);
alter table nucleo.usuario_rol add constraint fk_usuario_rol_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.usuario_rol add constraint fk_usuario_rol_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table nucleo.usuario_rol add constraint fk_usuario_rol_rol_id foreign key (rol_id) references nucleo.rol(id);
alter table nucleo.parametro add constraint fk_parametro_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.auditoria add constraint fk_auditoria_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table nucleo.auditoria add constraint fk_auditoria_agente_id foreign key (agente_id) references ia.agente(id);
alter table nucleo.evento_salida add constraint fk_evento_salida_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.predio add constraint fk_predio_empleador_tercero_id foreign key (empleador_tercero_id) references terceros.tercero(id);
alter table nucleo.zona add constraint fk_zona_predio foreign key (predio_id) references nucleo.predio(id);
alter table terceros.tercero add constraint fk_tercero_predio foreign key (predio_id) references nucleo.predio(id);
alter table terceros.consentimiento_datos add constraint fk_consentimiento_datos_predio foreign key (predio_id) references nucleo.predio(id);
alter table terceros.consentimiento_datos add constraint fk_consentimiento_datos_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table terceros.cliente add constraint fk_cliente_predio foreign key (predio_id) references nucleo.predio(id);
alter table terceros.cliente add constraint fk_cliente_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table terceros.cliente add constraint fk_cliente_lista_precios_id foreign key (predio_id, lista_precios_id) references comercial.lista_precios(predio_id, id);
alter table terceros.proveedor add constraint fk_proveedor_predio foreign key (predio_id) references nucleo.predio(id);
alter table terceros.proveedor add constraint fk_proveedor_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table terceros.empleado add constraint fk_empleado_predio foreign key (predio_id) references nucleo.predio(id);
alter table terceros.empleado add constraint fk_empleado_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table produccion.lote_animal add constraint fk_lote_animal_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.lote_animal add constraint fk_lote_animal_especie_id foreign key (especie_id) references produccion.especie(id);
alter table produccion.lote_animal add constraint fk_lote_animal_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table produccion.animal add constraint fk_animal_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.animal add constraint fk_animal_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table produccion.animal add constraint fk_animal_madre_id foreign key (predio_id, madre_id) references produccion.animal(predio_id, id);
alter table produccion.animal add constraint fk_animal_padre_id foreign key (predio_id, padre_id) references produccion.animal(predio_id, id);
alter table produccion.registro_postura add constraint fk_registro_postura_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.registro_postura add constraint fk_registro_postura_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table produccion.registro_postura add constraint fk_registro_postura_registrado_por foreign key (registrado_por) references nucleo.usuario(id);
alter table produccion.registro_postura add constraint fk_registro_postura_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.registro_alimentacion add constraint fk_registro_alimentacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.registro_alimentacion add constraint fk_registro_alimentacion_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table produccion.registro_alimentacion add constraint fk_registro_alimentacion_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table produccion.registro_alimentacion add constraint fk_registro_alimentacion_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.evento_sanitario add constraint fk_evento_sanitario_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.evento_sanitario add constraint fk_evento_sanitario_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table produccion.evento_sanitario add constraint fk_evento_sanitario_animal_id foreign key (predio_id, animal_id) references produccion.animal(predio_id, id);
alter table produccion.evento_sanitario add constraint fk_evento_sanitario_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table produccion.evento_sanitario add constraint fk_evento_sanitario_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.registro_pesaje add constraint fk_registro_pesaje_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.registro_pesaje add constraint fk_registro_pesaje_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table produccion.registro_pesaje add constraint fk_registro_pesaje_animal_id foreign key (predio_id, animal_id) references produccion.animal(predio_id, id);
alter table produccion.registro_pesaje add constraint fk_registro_pesaje_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.evento_reproductivo add constraint fk_evento_reproductivo_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.evento_reproductivo add constraint fk_evento_reproductivo_hembra_id foreign key (predio_id, hembra_id) references produccion.animal(predio_id, id);
alter table produccion.evento_reproductivo add constraint fk_evento_reproductivo_macho_id foreign key (predio_id, macho_id) references produccion.animal(predio_id, id);
alter table produccion.evento_reproductivo add constraint fk_evento_reproductivo_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.calidad_agua_estanque add constraint fk_calidad_agua_estanque_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.calidad_agua_estanque add constraint fk_calidad_agua_estanque_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table produccion.calidad_agua_estanque add constraint fk_calidad_agua_estanque_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.siembra add constraint fk_siembra_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.siembra add constraint fk_siembra_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table produccion.siembra add constraint fk_siembra_cultivo_id foreign key (cultivo_id) references produccion.cultivo(id);
alter table produccion.labor_cultural add constraint fk_labor_cultural_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.labor_cultural add constraint fk_labor_cultural_siembra_id foreign key (predio_id, siembra_id) references produccion.siembra(predio_id, id);
alter table produccion.labor_cultural add constraint fk_labor_cultural_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table produccion.labor_cultural add constraint fk_labor_cultural_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table produccion.labor_cultural add constraint fk_labor_cultural_mision_robot_id foreign key (predio_id, mision_robot_id) references iot.mision_robot(predio_id, id);
alter table produccion.labor_cultural add constraint fk_labor_cultural_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.cosecha add constraint fk_cosecha_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.cosecha add constraint fk_cosecha_siembra_id foreign key (predio_id, siembra_id) references produccion.siembra(predio_id, id);
alter table produccion.cosecha add constraint fk_cosecha_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table produccion.cosecha add constraint fk_cosecha_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table produccion.cosecha add constraint fk_cosecha_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.analisis_suelo add constraint fk_analisis_suelo_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.analisis_suelo add constraint fk_analisis_suelo_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table riego.fuente_agua add constraint fk_fuente_agua_predio foreign key (predio_id) references nucleo.predio(id);
alter table riego.tanque add constraint fk_tanque_predio foreign key (predio_id) references nucleo.predio(id);
alter table riego.tanque add constraint fk_tanque_fuente_agua_id foreign key (predio_id, fuente_agua_id) references riego.fuente_agua(predio_id, id);
alter table riego.tanque add constraint fk_tanque_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table riego.tanque add constraint fk_tanque_sensor_nivel_id foreign key (predio_id, sensor_nivel_id) references iot.sensor(predio_id, id);
alter table riego.sistema_riego add constraint fk_sistema_riego_predio foreign key (predio_id) references nucleo.predio(id);
alter table riego.sistema_riego add constraint fk_sistema_riego_tanque_id foreign key (predio_id, tanque_id) references riego.tanque(predio_id, id);
alter table riego.valvula add constraint fk_valvula_predio foreign key (predio_id) references nucleo.predio(id);
alter table riego.valvula add constraint fk_valvula_sistema_riego_id foreign key (predio_id, sistema_riego_id) references riego.sistema_riego(predio_id, id);
alter table riego.valvula add constraint fk_valvula_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table riego.valvula add constraint fk_valvula_actuador_id foreign key (predio_id, actuador_id) references iot.actuador(predio_id, id);
alter table riego.evento_riego add constraint fk_evento_riego_predio foreign key (predio_id) references nucleo.predio(id);
alter table riego.evento_riego add constraint fk_evento_riego_valvula_id foreign key (predio_id, valvula_id) references riego.valvula(predio_id, id);
alter table riego.evento_riego add constraint fk_evento_riego_registrado_por foreign key (registrado_por) references nucleo.usuario(id);
alter table riego.evento_riego add constraint fk_evento_riego_regla_id foreign key (predio_id, regla_id) references iot.regla_automatizacion(predio_id, id);
alter table riego.evento_riego add constraint fk_evento_riego_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table inventario.categoria_producto add constraint fk_categoria_producto_padre_id foreign key (padre_id) references inventario.categoria_producto(id);
alter table inventario.producto add constraint fk_producto_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.producto add constraint fk_producto_categoria_id foreign key (categoria_id) references inventario.categoria_producto(id);
alter table inventario.producto add constraint fk_producto_unidad_id foreign key (unidad_id) references inventario.unidad_medida(id);
alter table inventario.bodega add constraint fk_bodega_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.bodega add constraint fk_bodega_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table inventario.bodega add constraint fk_bodega_sensor_temperatura_id foreign key (predio_id, sensor_temperatura_id) references iot.sensor(predio_id, id);
alter table inventario.lote_inventario add constraint fk_lote_inventario_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.lote_inventario add constraint fk_lote_inventario_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table inventario.lote_inventario add constraint fk_lote_inventario_bodega_id foreign key (predio_id, bodega_id) references inventario.bodega(predio_id, id);
alter table inventario.movimiento_inventario add constraint fk_movimiento_inventario_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.movimiento_inventario add constraint fk_movimiento_inventario_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table inventario.movimiento_inventario add constraint fk_movimiento_inventario_pesaje_id foreign key (predio_id, pesaje_id) references inventario.pesaje(predio_id, id);
alter table inventario.movimiento_inventario add constraint fk_movimiento_inventario_lectura_codigo_id foreign key (predio_id, lectura_codigo_id) references inventario.lectura_codigo(predio_id, id);
alter table inventario.movimiento_inventario add constraint fk_movimiento_inventario_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table inventario.movimiento_inventario add constraint fk_movimiento_inventario_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table comercial.lista_precios add constraint fk_lista_precios_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.precio_producto add constraint fk_precio_producto_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.precio_producto add constraint fk_precio_producto_lista_precios_id foreign key (predio_id, lista_precios_id) references comercial.lista_precios(predio_id, id);
alter table comercial.precio_producto add constraint fk_precio_producto_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table comercial.precio_producto add constraint fk_precio_producto_propuesta_precio_id foreign key (predio_id, propuesta_precio_id) references comercial.propuesta_precio(predio_id, id);
alter table comercial.precio_producto add constraint fk_precio_producto_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table comercial.propuesta_precio add constraint fk_propuesta_precio_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.propuesta_precio add constraint fk_propuesta_precio_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table comercial.propuesta_precio add constraint fk_propuesta_precio_lista_precios_id foreign key (predio_id, lista_precios_id) references comercial.lista_precios(predio_id, id);
alter table comercial.propuesta_precio add constraint fk_propuesta_precio_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table comercial.propuesta_precio add constraint fk_propuesta_precio_revisado_por foreign key (revisado_por) references nucleo.usuario(id);
alter table comercial.pedido add constraint fk_pedido_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.pedido add constraint fk_pedido_cliente_id foreign key (predio_id, cliente_id) references terceros.cliente(predio_id, id);
alter table comercial.pedido add constraint fk_pedido_pedido_recurrente_id foreign key (predio_id, pedido_recurrente_id) references comercial.pedido_recurrente(predio_id, id);
alter table comercial.pedido add constraint fk_pedido_creado_por_agente_id foreign key (predio_id, creado_por_agente_id) references ia.agente(predio_id, id);
alter table comercial.pedido add constraint fk_pedido_vendedor_id foreign key (vendedor_id) references nucleo.usuario(id);
alter table comercial.pedido add constraint fk_pedido_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table comercial.pedido_detalle add constraint fk_pedido_detalle_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.pedido_detalle add constraint fk_pedido_detalle_pedido_id foreign key (predio_id, pedido_id) references comercial.pedido(predio_id, id);
alter table comercial.pedido_detalle add constraint fk_pedido_detalle_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table comercial.pedido_detalle add constraint fk_pedido_detalle_precio_producto_id foreign key (predio_id, precio_producto_id) references comercial.precio_producto(predio_id, id);
alter table comercial.factura add constraint fk_factura_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.factura add constraint fk_factura_pedido_id foreign key (predio_id, pedido_id) references comercial.pedido(predio_id, id);
alter table comercial.factura add constraint fk_factura_cliente_id foreign key (predio_id, cliente_id) references terceros.cliente(predio_id, id);
alter table comercial.pago add constraint fk_pago_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.pago add constraint fk_pago_pedido_id foreign key (predio_id, pedido_id) references comercial.pedido(predio_id, id);
alter table comercial.pago add constraint fk_pago_factura_id foreign key (predio_id, factura_id) references comercial.factura(predio_id, id);
alter table comercial.pago add constraint fk_pago_confirmado_por foreign key (confirmado_por) references nucleo.usuario(id);
alter table comercial.pago add constraint fk_pago_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table comercial.entrega add constraint fk_entrega_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.entrega add constraint fk_entrega_pedido_id foreign key (predio_id, pedido_id) references comercial.pedido(predio_id, id);
alter table comercial.entrega add constraint fk_entrega_vehiculo_id foreign key (predio_id, vehiculo_id) references inventario.vehiculo(predio_id, id);
alter table comercial.entrega add constraint fk_entrega_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table compras.orden_compra add constraint fk_orden_compra_predio foreign key (predio_id) references nucleo.predio(id);
alter table compras.orden_compra add constraint fk_orden_compra_proveedor_id foreign key (predio_id, proveedor_id) references terceros.proveedor(predio_id, id);
alter table compras.orden_compra add constraint fk_orden_compra_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table compras.orden_compra_detalle add constraint fk_orden_compra_detalle_predio foreign key (predio_id) references nucleo.predio(id);
alter table compras.orden_compra_detalle add constraint fk_orden_compra_detalle_orden_compra_id foreign key (predio_id, orden_compra_id) references compras.orden_compra(predio_id, id);
alter table compras.orden_compra_detalle add constraint fk_orden_compra_detalle_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table compras.cotizacion_proveedor add constraint fk_cotizacion_proveedor_predio foreign key (predio_id) references nucleo.predio(id);
alter table compras.cotizacion_proveedor add constraint fk_cotizacion_proveedor_proveedor_id foreign key (predio_id, proveedor_id) references terceros.proveedor(predio_id, id);
alter table compras.cotizacion_proveedor add constraint fk_cotizacion_proveedor_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table compras.precio_mercado add constraint fk_precio_mercado_predio foreign key (predio_id) references nucleo.predio(id);
alter table compras.precio_mercado add constraint fk_precio_mercado_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table finanzas.cuenta_contable add constraint fk_cuenta_contable_padre_id foreign key (padre_id) references finanzas.cuenta_contable(id);
alter table finanzas.centro_costo add constraint fk_centro_costo_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.comprobante add constraint fk_comprobante_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.comprobante add constraint fk_comprobante_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table finanzas.movimiento_contable add constraint fk_movimiento_contable_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.movimiento_contable add constraint fk_movimiento_contable_comprobante_id foreign key (predio_id, comprobante_id) references finanzas.comprobante(predio_id, id);
alter table finanzas.movimiento_contable add constraint fk_movimiento_contable_cuenta_id foreign key (cuenta_id) references finanzas.cuenta_contable(id);
alter table finanzas.movimiento_contable add constraint fk_movimiento_contable_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table finanzas.movimiento_contable add constraint fk_movimiento_contable_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table ia.agente add constraint fk_agente_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.agente_herramienta add constraint fk_agente_herramienta_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.agente_herramienta add constraint fk_agente_herramienta_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table ia.agente_herramienta add constraint fk_agente_herramienta_herramienta_id foreign key (herramienta_id) references ia.herramienta(id);
alter table ia.solicitud_aprobacion add constraint fk_solicitud_aprobacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.solicitud_aprobacion add constraint fk_solicitud_aprobacion_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table ia.solicitud_aprobacion add constraint fk_solicitud_aprobacion_herramienta_id foreign key (herramienta_id) references ia.herramienta(id);
alter table ia.solicitud_aprobacion add constraint fk_solicitud_aprobacion_resuelto_por foreign key (resuelto_por) references nucleo.usuario(id);
alter table ia.documento_conocimiento add constraint fk_documento_conocimiento_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.documento_conocimiento add constraint fk_documento_conocimiento_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table ia.fragmento_conocimiento add constraint fk_fragmento_conocimiento_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.fragmento_conocimiento add constraint fk_fragmento_conocimiento_documento_id foreign key (predio_id, documento_id) references ia.documento_conocimiento(predio_id, id);
alter table ia.recomendacion add constraint fk_recomendacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.recomendacion add constraint fk_recomendacion_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table ia.recomendacion add constraint fk_recomendacion_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table ia.evaluacion_respuesta add constraint fk_evaluacion_respuesta_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.evaluacion_respuesta add constraint fk_evaluacion_respuesta_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table ia.consumo_ia add constraint fk_consumo_ia_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.consumo_ia add constraint fk_consumo_ia_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table redes.cuenta_red add constraint fk_cuenta_red_predio foreign key (predio_id) references nucleo.predio(id);
alter table redes.cuenta_red add constraint fk_cuenta_red_plataforma foreign key (plataforma) references redes.politica_canal(plataforma);
alter table redes.publicacion add constraint fk_publicacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table redes.publicacion add constraint fk_publicacion_cuenta_red_id foreign key (predio_id, cuenta_red_id) references redes.cuenta_red(predio_id, id);
alter table redes.publicacion add constraint fk_publicacion_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table redes.publicacion add constraint fk_publicacion_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table redes.publicacion add constraint fk_publicacion_recomendacion_id foreign key (predio_id, recomendacion_id) references ia.recomendacion(predio_id, id);
alter table turismo.alojamiento add constraint fk_alojamiento_predio foreign key (predio_id) references nucleo.predio(id);
alter table turismo.alojamiento add constraint fk_alojamiento_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table turismo.plan_turistico add constraint fk_plan_turistico_predio foreign key (predio_id) references nucleo.predio(id);
alter table turismo.reserva add constraint fk_reserva_predio foreign key (predio_id) references nucleo.predio(id);
alter table turismo.reserva add constraint fk_reserva_cliente_id foreign key (predio_id, cliente_id) references terceros.cliente(predio_id, id);
alter table turismo.reserva add constraint fk_reserva_alojamiento_id foreign key (predio_id, alojamiento_id) references turismo.alojamiento(predio_id, id);
alter table turismo.reserva add constraint fk_reserva_plan_turistico_id foreign key (predio_id, plan_turistico_id) references turismo.plan_turistico(predio_id, id);
alter table turismo.reserva add constraint fk_reserva_pedido_id foreign key (predio_id, pedido_id) references comercial.pedido(predio_id, id);
alter table iot.dispositivo add constraint fk_dispositivo_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.dispositivo add constraint fk_dispositivo_pasarela_id foreign key (predio_id, pasarela_id) references iot.dispositivo(predio_id, id);
alter table iot.dispositivo add constraint fk_dispositivo_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table iot.sensor add constraint fk_sensor_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.sensor add constraint fk_sensor_dispositivo_id foreign key (predio_id, dispositivo_id) references iot.dispositivo(predio_id, id);
alter table iot.actuador add constraint fk_actuador_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.actuador add constraint fk_actuador_dispositivo_id foreign key (predio_id, dispositivo_id) references iot.dispositivo(predio_id, id);
alter table iot.actuador add constraint fk_actuador_zona_seguridad_id foreign key (predio_id, zona_seguridad_id) references iot.zona_seguridad(predio_id, id);
alter table iot.lectura add constraint fk_lectura_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.lectura add constraint fk_lectura_sensor_id foreign key (predio_id, sensor_id) references iot.sensor(predio_id, id);
alter table iot.regla_automatizacion add constraint fk_regla_automatizacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.regla_automatizacion add constraint fk_regla_automatizacion_actuador_id foreign key (predio_id, actuador_id) references iot.actuador(predio_id, id);
alter table iot.regla_automatizacion add constraint fk_regla_automatizacion_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table iot.comando_actuador add constraint fk_comando_actuador_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.comando_actuador add constraint fk_comando_actuador_actuador_id foreign key (predio_id, actuador_id) references iot.actuador(predio_id, id);
alter table iot.comando_actuador add constraint fk_comando_actuador_regla_id foreign key (predio_id, regla_id) references iot.regla_automatizacion(predio_id, id);
alter table iot.comando_actuador add constraint fk_comando_actuador_solicitado_por foreign key (solicitado_por) references nucleo.usuario(id);
alter table iot.comando_actuador add constraint fk_comando_actuador_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table nucleo.dispositivo_captura add constraint fk_dispositivo_captura_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.dispositivo_captura add constraint fk_dispositivo_captura_usuario_asignado_id foreign key (usuario_asignado_id) references nucleo.usuario(id);
alter table nucleo.sincronizacion add constraint fk_sincronizacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.sincronizacion add constraint fk_sincronizacion_dispositivo_captura_id foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table nucleo.sincronizacion add constraint fk_sincronizacion_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table inventario.etiqueta add constraint fk_etiqueta_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.etiqueta add constraint fk_etiqueta_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table inventario.etiqueta add constraint fk_etiqueta_impresora_id foreign key (predio_id, impresora_id) references nucleo.dispositivo_captura(predio_id, id);
alter table inventario.lectura_codigo add constraint fk_lectura_codigo_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.lectura_codigo add constraint fk_lectura_codigo_etiqueta_id foreign key (predio_id, etiqueta_id) references inventario.etiqueta(predio_id, id);
alter table inventario.lectura_codigo add constraint fk_lectura_codigo_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table inventario.lectura_codigo add constraint fk_lectura_codigo_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table inventario.pesaje add constraint fk_pesaje_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.pesaje add constraint fk_pesaje_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table inventario.pesaje add constraint fk_pesaje_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table inventario.conteo_fisico add constraint fk_conteo_fisico_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.conteo_fisico add constraint fk_conteo_fisico_bodega_id foreign key (predio_id, bodega_id) references inventario.bodega(predio_id, id);
alter table inventario.conteo_fisico add constraint fk_conteo_fisico_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table inventario.conteo_detalle add constraint fk_conteo_detalle_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.conteo_detalle add constraint fk_conteo_detalle_conteo_fisico_id foreign key (predio_id, conteo_fisico_id) references inventario.conteo_fisico(predio_id, id);
alter table inventario.conteo_detalle add constraint fk_conteo_detalle_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table inventario.conteo_detalle add constraint fk_conteo_detalle_movimiento_ajuste_id foreign key (predio_id, movimiento_ajuste_id) references inventario.movimiento_inventario(predio_id, id);
alter table inventario.conteo_detalle add constraint fk_conteo_detalle_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table comercial.reserva_lote add constraint fk_reserva_lote_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.reserva_lote add constraint fk_reserva_lote_pedido_detalle_id foreign key (predio_id, pedido_detalle_id) references comercial.pedido_detalle(predio_id, id);
alter table comercial.reserva_lote add constraint fk_reserva_lote_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table finanzas.periodo_contable add constraint fk_periodo_contable_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.periodo_contable add constraint fk_periodo_contable_cerrado_por foreign key (cerrado_por) references nucleo.usuario(id);
alter table redes.plantilla_mensaje add constraint fk_plantilla_mensaje_predio foreign key (predio_id) references nucleo.predio(id);
alter table redes.plantilla_mensaje add constraint fk_plantilla_mensaje_cuenta_red_id foreign key (predio_id, cuenta_red_id) references redes.cuenta_red(predio_id, id);
alter table redes.mensaje_saliente add constraint fk_mensaje_saliente_predio foreign key (predio_id) references nucleo.predio(id);
alter table redes.mensaje_saliente add constraint fk_mensaje_saliente_cuenta_red_id foreign key (predio_id, cuenta_red_id) references redes.cuenta_red(predio_id, id);
alter table redes.mensaje_saliente add constraint fk_mensaje_saliente_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table redes.mensaje_saliente add constraint fk_mensaje_saliente_plantilla_id foreign key (predio_id, plantilla_id) references redes.plantilla_mensaje(predio_id, id);
alter table redes.mensaje_saliente add constraint fk_mensaje_saliente_consentimiento_id foreign key (predio_id, consentimiento_id) references terceros.consentimiento_datos(predio_id, id);
alter table ia.regla_conversacion add constraint fk_regla_conversacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.escalamiento add constraint fk_escalamiento_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.escalamiento add constraint fk_escalamiento_asignado_a foreign key (asignado_a) references nucleo.usuario(id);
alter table nucleo.funcionalidad add constraint fk_funcionalidad_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.funcionalidad add constraint fk_funcionalidad_activada_por foreign key (activada_por) references nucleo.usuario(id);
alter table nucleo.nota_voz add constraint fk_nota_voz_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.nota_voz add constraint fk_nota_voz_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table nucleo.nota_voz add constraint fk_nota_voz_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.clasificacion_postura add constraint fk_clasificacion_postura_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.clasificacion_postura add constraint fk_clasificacion_postura_registro_postura_id foreign key (predio_id, registro_postura_id) references produccion.registro_postura(predio_id, id);
alter table produccion.clasificacion_postura add constraint fk_clasificacion_postura_categoria_huevo_id foreign key (categoria_huevo_id) references produccion.categoria_huevo(id);
alter table produccion.clasificacion_postura add constraint fk_clasificacion_postura_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.registro_bioseguridad add constraint fk_registro_bioseguridad_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.registro_bioseguridad add constraint fk_registro_bioseguridad_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table produccion.registro_bioseguridad add constraint fk_registro_bioseguridad_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table produccion.registro_bioseguridad add constraint fk_registro_bioseguridad_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table produccion.produccion_abono add constraint fk_produccion_abono_predio foreign key (predio_id) references nucleo.predio(id);
alter table produccion.produccion_abono add constraint fk_produccion_abono_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table produccion.produccion_abono add constraint fk_produccion_abono_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table produccion.produccion_abono add constraint fk_produccion_abono_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table inventario.vehiculo add constraint fk_vehiculo_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.vehiculo add constraint fk_vehiculo_sensor_temperatura_id foreign key (predio_id, sensor_temperatura_id) references iot.sensor(predio_id, id);
alter table inventario.excursion_temperatura add constraint fk_excursion_temperatura_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.excursion_temperatura add constraint fk_excursion_temperatura_sensor_id foreign key (predio_id, sensor_id) references iot.sensor(predio_id, id);
alter table inventario.excursion_temperatura add constraint fk_excursion_temperatura_bodega_id foreign key (predio_id, bodega_id) references inventario.bodega(predio_id, id);
alter table inventario.excursion_temperatura add constraint fk_excursion_temperatura_vehiculo_id foreign key (predio_id, vehiculo_id) references inventario.vehiculo(predio_id, id);
alter table inventario.bloqueo_lote add constraint fk_bloqueo_lote_predio foreign key (predio_id) references nucleo.predio(id);
alter table inventario.bloqueo_lote add constraint fk_bloqueo_lote_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table inventario.bloqueo_lote add constraint fk_bloqueo_lote_decidido_por foreign key (decidido_por) references nucleo.usuario(id);
alter table comercial.retiro_lote add constraint fk_retiro_lote_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.retiro_lote add constraint fk_retiro_lote_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table comercial.retiro_lote add constraint fk_retiro_lote_abierto_por foreign key (abierto_por) references nucleo.usuario(id);
alter table comercial.retiro_aviso add constraint fk_retiro_aviso_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.retiro_aviso add constraint fk_retiro_aviso_retiro_lote_id foreign key (predio_id, retiro_lote_id) references comercial.retiro_lote(predio_id, id);
alter table comercial.retiro_aviso add constraint fk_retiro_aviso_cliente_id foreign key (predio_id, cliente_id) references terceros.cliente(predio_id, id);
alter table comercial.retiro_aviso add constraint fk_retiro_aviso_pedido_id foreign key (predio_id, pedido_id) references comercial.pedido(predio_id, id);
alter table comercial.pedido_recurrente add constraint fk_pedido_recurrente_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.pedido_recurrente add constraint fk_pedido_recurrente_cliente_id foreign key (predio_id, cliente_id) references terceros.cliente(predio_id, id);
alter table comercial.pedido_recurrente_detalle add constraint fk_pedido_recurrente_detalle_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.pedido_recurrente_detalle add constraint fk_pedido_recurrente_detalle_pedido_recurrente_id foreign key (predio_id, pedido_recurrente_id) references comercial.pedido_recurrente(predio_id, id);
alter table comercial.pedido_recurrente_detalle add constraint fk_pedido_recurrente_detalle_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table comercial.permuta add constraint fk_permuta_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.permuta add constraint fk_permuta_factura_id foreign key (predio_id, factura_id) references comercial.factura(predio_id, id);
alter table comercial.permuta add constraint fk_permuta_documento_soporte_id foreign key (predio_id, documento_soporte_id) references compras.documento_soporte(predio_id, id);
alter table comercial.permuta add constraint fk_permuta_registrado_por foreign key (registrado_por) references nucleo.usuario(id);
alter table comercial.huella_trazabilidad add constraint fk_huella_trazabilidad_predio foreign key (predio_id) references nucleo.predio(id);
alter table comercial.huella_trazabilidad add constraint fk_huella_trazabilidad_lote_inventario_id foreign key (predio_id, lote_inventario_id) references inventario.lote_inventario(predio_id, id);
alter table compras.documento_soporte add constraint fk_documento_soporte_predio foreign key (predio_id) references nucleo.predio(id);
alter table compras.documento_soporte add constraint fk_documento_soporte_proveedor_id foreign key (predio_id, proveedor_id) references terceros.proveedor(predio_id, id);
alter table compras.documento_soporte add constraint fk_documento_soporte_orden_compra_id foreign key (predio_id, orden_compra_id) references compras.orden_compra(predio_id, id);
alter table ia.modelo_pronostico add constraint fk_modelo_pronostico_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.modelo_pronostico add constraint fk_modelo_pronostico_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table ia.pronostico_demanda add constraint fk_pronostico_demanda_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.pronostico_demanda add constraint fk_pronostico_demanda_modelo_pronostico_id foreign key (predio_id, modelo_pronostico_id) references ia.modelo_pronostico(predio_id, id);
alter table ia.pronostico_demanda add constraint fk_pronostico_demanda_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table redes.pieza_audiovisual add constraint fk_pieza_audiovisual_predio foreign key (predio_id) references nucleo.predio(id);
alter table redes.pieza_audiovisual add constraint fk_pieza_audiovisual_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table redes.pieza_audiovisual add constraint fk_pieza_audiovisual_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table redes.pieza_audiovisual add constraint fk_pieza_audiovisual_publicacion_id foreign key (predio_id, publicacion_id) references redes.publicacion(predio_id, id);
alter table redes.pieza_persona add constraint fk_pieza_persona_predio foreign key (predio_id) references nucleo.predio(id);
alter table redes.pieza_persona add constraint fk_pieza_persona_pieza_audiovisual_id foreign key (predio_id, pieza_audiovisual_id) references redes.pieza_audiovisual(predio_id, id);
alter table redes.pieza_persona add constraint fk_pieza_persona_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table turismo.bloqueo_calendario add constraint fk_bloqueo_calendario_predio foreign key (predio_id) references nucleo.predio(id);
alter table turismo.bloqueo_calendario add constraint fk_bloqueo_calendario_alojamiento_id foreign key (predio_id, alojamiento_id) references turismo.alojamiento(predio_id, id);
alter table turismo.bloqueo_calendario add constraint fk_bloqueo_calendario_plan_turistico_id foreign key (predio_id, plan_turistico_id) references turismo.plan_turistico(predio_id, id);
alter table iot.zona_seguridad add constraint fk_zona_seguridad_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.zona_seguridad add constraint fk_zona_seguridad_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table iot.cambio_estado_alarma add constraint fk_cambio_estado_alarma_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.cambio_estado_alarma add constraint fk_cambio_estado_alarma_zona_seguridad_id foreign key (predio_id, zona_seguridad_id) references iot.zona_seguridad(predio_id, id);
alter table iot.cambio_estado_alarma add constraint fk_cambio_estado_alarma_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table iot.credencial_acceso add constraint fk_credencial_acceso_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.credencial_acceso add constraint fk_credencial_acceso_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table iot.credencial_acceso add constraint fk_credencial_acceso_zona_seguridad_id foreign key (predio_id, zona_seguridad_id) references iot.zona_seguridad(predio_id, id);
alter table iot.credencial_acceso add constraint fk_credencial_acceso_consentimiento_id foreign key (predio_id, consentimiento_id) references terceros.consentimiento_datos(predio_id, id);
alter table iot.camara add constraint fk_camara_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.camara add constraint fk_camara_dispositivo_id foreign key (predio_id, dispositivo_id) references iot.dispositivo(predio_id, id);
alter table iot.camara add constraint fk_camara_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table iot.camara add constraint fk_camara_zona_seguridad_id foreign key (predio_id, zona_seguridad_id) references iot.zona_seguridad(predio_id, id);
alter table iot.evento_seguridad add constraint fk_evento_seguridad_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.evento_seguridad add constraint fk_evento_seguridad_zona_seguridad_id foreign key (predio_id, zona_seguridad_id) references iot.zona_seguridad(predio_id, id);
alter table iot.evento_seguridad add constraint fk_evento_seguridad_sensor_id foreign key (predio_id, sensor_id) references iot.sensor(predio_id, id);
alter table iot.evento_seguridad add constraint fk_evento_seguridad_camara_id foreign key (predio_id, camara_id) references iot.camara(predio_id, id);
alter table iot.evento_seguridad add constraint fk_evento_seguridad_credencial_id foreign key (predio_id, credencial_id) references iot.credencial_acceso(predio_id, id);
alter table iot.evento_seguridad add constraint fk_evento_seguridad_atendido_por foreign key (atendido_por) references nucleo.usuario(id);
alter table iot.clip_video add constraint fk_clip_video_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.clip_video add constraint fk_clip_video_camara_id foreign key (predio_id, camara_id) references iot.camara(predio_id, id);
alter table iot.clip_video add constraint fk_clip_video_evento_seguridad_id foreign key (predio_id, evento_seguridad_id) references iot.evento_seguridad(predio_id, id);
alter table ambiental.registro_ambiental add constraint fk_registro_ambiental_predio foreign key (predio_id) references nucleo.predio(id);
alter table ambiental.registro_ambiental add constraint fk_registro_ambiental_sensor_id foreign key (predio_id, sensor_id) references iot.sensor(predio_id, id);
alter table ambiental.registro_ambiental add constraint fk_registro_ambiental_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table personal.cuadrilla add constraint fk_cuadrilla_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.cuadrilla add constraint fk_cuadrilla_lider_id foreign key (predio_id, lider_id) references terceros.empleado(predio_id, id);
alter table personal.cuadrilla_miembro add constraint fk_cuadrilla_miembro_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.cuadrilla_miembro add constraint fk_cuadrilla_miembro_cuadrilla_id foreign key (predio_id, cuadrilla_id) references personal.cuadrilla(predio_id, id);
alter table personal.cuadrilla_miembro add constraint fk_cuadrilla_miembro_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.turno add constraint fk_turno_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.turno add constraint fk_turno_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.turno add constraint fk_turno_area_id foreign key (predio_id, area_id) references personal.area_responsabilidad(predio_id, id);
alter table personal.turno add constraint fk_turno_cronograma_id foreign key (predio_id, cronograma_id) references personal.cronograma(predio_id, id);
alter table personal.ausencia add constraint fk_ausencia_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.ausencia add constraint fk_ausencia_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.ausencia add constraint fk_ausencia_soporte_documento_id foreign key (predio_id, soporte_documento_id) references documental.documento(predio_id, id);
alter table personal.ausencia add constraint fk_ausencia_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table personal.plantilla_tarea add constraint fk_plantilla_tarea_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.plantilla_tarea add constraint fk_plantilla_tarea_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table personal.plantilla_tarea add constraint fk_plantilla_tarea_competencia_id foreign key (predio_id, competencia_id) references formacion.competencia(predio_id, id);
alter table personal.plantilla_tarea add constraint fk_plantilla_tarea_area_id foreign key (predio_id, area_id) references personal.area_responsabilidad(predio_id, id);
alter table personal.tarea add constraint fk_tarea_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.tarea add constraint fk_tarea_plantilla_tarea_id foreign key (predio_id, plantilla_tarea_id) references personal.plantilla_tarea(predio_id, id);
alter table personal.tarea add constraint fk_tarea_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table personal.tarea add constraint fk_tarea_area_id foreign key (predio_id, area_id) references personal.area_responsabilidad(predio_id, id);
alter table personal.tarea add constraint fk_tarea_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table personal.tarea add constraint fk_tarea_siembra_id foreign key (predio_id, siembra_id) references produccion.siembra(predio_id, id);
alter table personal.tarea add constraint fk_tarea_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table personal.tarea add constraint fk_tarea_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.tarea add constraint fk_tarea_cuadrilla_id foreign key (predio_id, cuadrilla_id) references personal.cuadrilla(predio_id, id);
alter table personal.tarea add constraint fk_tarea_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table personal.tarea add constraint fk_tarea_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table personal.tarea add constraint fk_tarea_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table personal.paso_tarea add constraint fk_paso_tarea_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.paso_tarea add constraint fk_paso_tarea_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table personal.paso_tarea add constraint fk_paso_tarea_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table personal.evidencia_tarea add constraint fk_evidencia_tarea_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.evidencia_tarea add constraint fk_evidencia_tarea_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table personal.evidencia_tarea add constraint fk_evidencia_tarea_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table personal.matriz_responsabilidad add constraint fk_matriz_responsabilidad_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.matriz_responsabilidad add constraint fk_matriz_responsabilidad_rol_id foreign key (rol_id) references nucleo.rol(id);
alter table personal.asignacion_equipo add constraint fk_asignacion_equipo_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.asignacion_equipo add constraint fk_asignacion_equipo_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table personal.asignacion_equipo add constraint fk_asignacion_equipo_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.credencial_trabajo add constraint fk_credencial_trabajo_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.credencial_trabajo add constraint fk_credencial_trabajo_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.jornada add constraint fk_jornada_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.jornada add constraint fk_jornada_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.jornada add constraint fk_jornada_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table personal.jornada add constraint fk_jornada_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table personal.jornada add constraint fk_jornada_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table nomina.concepto_nomina add constraint fk_concepto_nomina_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.concepto_nomina add constraint fk_concepto_nomina_cuenta_contable_id foreign key (cuenta_contable_id) references finanzas.cuenta_contable(id);
alter table nomina.periodo_nomina add constraint fk_periodo_nomina_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.periodo_nomina add constraint fk_periodo_nomina_preparado_por foreign key (preparado_por) references nucleo.usuario(id);
alter table nomina.periodo_nomina add constraint fk_periodo_nomina_cerrado_por foreign key (cerrado_por) references nucleo.usuario(id);
alter table nomina.periodo_nomina add constraint fk_periodo_nomina_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table nomina.periodo_nomina add constraint fk_periodo_nomina_comprobante_id foreign key (predio_id, comprobante_id) references finanzas.comprobante(predio_id, id);
alter table nomina.periodo_nomina add constraint fk_periodo_nomina_ajusta_periodo_id foreign key (predio_id, ajusta_periodo_id) references nomina.periodo_nomina(predio_id, id);
alter table nomina.novedad add constraint fk_novedad_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.novedad add constraint fk_novedad_periodo_id foreign key (predio_id, periodo_id) references nomina.periodo_nomina(predio_id, id);
alter table nomina.novedad add constraint fk_novedad_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table nomina.novedad add constraint fk_novedad_concepto_id foreign key (predio_id, concepto_id) references nomina.concepto_nomina(predio_id, id);
alter table nomina.novedad add constraint fk_novedad_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table nomina.novedad add constraint fk_novedad_jornada_id foreign key (predio_id, jornada_id) references personal.jornada(predio_id, id);
alter table nomina.novedad add constraint fk_novedad_ausencia_id foreign key (predio_id, ausencia_id) references personal.ausencia(predio_id, id);
alter table nomina.liquidacion add constraint fk_liquidacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.liquidacion add constraint fk_liquidacion_periodo_id foreign key (predio_id, periodo_id) references nomina.periodo_nomina(predio_id, id);
alter table nomina.liquidacion add constraint fk_liquidacion_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table nomina.liquidacion_detalle add constraint fk_liquidacion_detalle_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.liquidacion_detalle add constraint fk_liquidacion_detalle_liquidacion_id foreign key (predio_id, liquidacion_id) references nomina.liquidacion(predio_id, id);
alter table nomina.liquidacion_detalle add constraint fk_liquidacion_detalle_concepto_id foreign key (predio_id, concepto_id) references nomina.concepto_nomina(predio_id, id);
alter table nomina.provision_prestacion add constraint fk_provision_prestacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.provision_prestacion add constraint fk_provision_prestacion_periodo_id foreign key (predio_id, periodo_id) references nomina.periodo_nomina(predio_id, id);
alter table nomina.provision_prestacion add constraint fk_provision_prestacion_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table nomina.documento_nomina_electronica add constraint fk_documento_nomina_electronica_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.documento_nomina_electronica add constraint fk_documento_nomina_electronica_liquidacion_id foreign key (predio_id, liquidacion_id) references nomina.liquidacion(predio_id, id);
alter table nomina.planilla_pila add constraint fk_planilla_pila_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.planilla_pila add constraint fk_planilla_pila_periodo_id foreign key (predio_id, periodo_id) references nomina.periodo_nomina(predio_id, id);
alter table nomina.planilla_pila add constraint fk_planilla_pila_pagada_por foreign key (pagada_por) references nucleo.usuario(id);
alter table nomina.pago_nomina add constraint fk_pago_nomina_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.pago_nomina add constraint fk_pago_nomina_liquidacion_id foreign key (predio_id, liquidacion_id) references nomina.liquidacion(predio_id, id);
alter table nomina.pago_nomina add constraint fk_pago_nomina_preparado_por foreign key (preparado_por) references nucleo.usuario(id);
alter table nomina.pago_nomina add constraint fk_pago_nomina_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table nomina.pago_nomina add constraint fk_pago_nomina_segunda_aprobacion_por foreign key (segunda_aprobacion_por) references nucleo.usuario(id);
alter table nomina.exportacion_nomina add constraint fk_exportacion_nomina_predio foreign key (predio_id) references nucleo.predio(id);
alter table nomina.exportacion_nomina add constraint fk_exportacion_nomina_periodo_id foreign key (predio_id, periodo_id) references nomina.periodo_nomina(predio_id, id);
alter table nomina.exportacion_nomina add constraint fk_exportacion_nomina_generado_por foreign key (generado_por) references nucleo.usuario(id);
alter table formacion.competencia add constraint fk_competencia_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.curso add constraint fk_curso_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.curso add constraint fk_curso_competencia_id foreign key (predio_id, competencia_id) references formacion.competencia(predio_id, id);
alter table formacion.leccion add constraint fk_leccion_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.leccion add constraint fk_leccion_curso_id foreign key (predio_id, curso_id) references formacion.curso(predio_id, id);
alter table formacion.leccion add constraint fk_leccion_documento_id foreign key (predio_id, documento_id) references documental.documento(predio_id, id);
alter table formacion.evaluacion add constraint fk_evaluacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.evaluacion add constraint fk_evaluacion_curso_id foreign key (predio_id, curso_id) references formacion.curso(predio_id, id);
alter table formacion.pregunta add constraint fk_pregunta_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.pregunta add constraint fk_pregunta_evaluacion_id foreign key (predio_id, evaluacion_id) references formacion.evaluacion(predio_id, id);
alter table formacion.inscripcion add constraint fk_inscripcion_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.inscripcion add constraint fk_inscripcion_curso_id foreign key (predio_id, curso_id) references formacion.curso(predio_id, id);
alter table formacion.inscripcion add constraint fk_inscripcion_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table formacion.progreso add constraint fk_progreso_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.progreso add constraint fk_progreso_inscripcion_id foreign key (predio_id, inscripcion_id) references formacion.inscripcion(predio_id, id);
alter table formacion.progreso add constraint fk_progreso_leccion_id foreign key (predio_id, leccion_id) references formacion.leccion(predio_id, id);
alter table formacion.progreso add constraint fk_progreso_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table formacion.sesion_presencial add constraint fk_sesion_presencial_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.sesion_presencial add constraint fk_sesion_presencial_curso_id foreign key (predio_id, curso_id) references formacion.curso(predio_id, id);
alter table formacion.sesion_presencial add constraint fk_sesion_presencial_instructor_id foreign key (predio_id, instructor_id) references terceros.tercero(predio_id, id);
alter table formacion.asistencia add constraint fk_asistencia_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.asistencia add constraint fk_asistencia_sesion_id foreign key (predio_id, sesion_id) references formacion.sesion_presencial(predio_id, id);
alter table formacion.asistencia add constraint fk_asistencia_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table formacion.asistencia add constraint fk_asistencia_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table formacion.certificado add constraint fk_certificado_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.certificado add constraint fk_certificado_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table formacion.certificado add constraint fk_certificado_competencia_id foreign key (predio_id, competencia_id) references formacion.competencia(predio_id, id);
alter table formacion.certificado add constraint fk_certificado_inscripcion_id foreign key (predio_id, inscripcion_id) references formacion.inscripcion(predio_id, id);
alter table formacion.certificado add constraint fk_certificado_sesion_id foreign key (predio_id, sesion_id) references formacion.sesion_presencial(predio_id, id);
alter table formacion.habilitacion add constraint fk_habilitacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.habilitacion add constraint fk_habilitacion_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table formacion.habilitacion add constraint fk_habilitacion_competencia_id foreign key (predio_id, competencia_id) references formacion.competencia(predio_id, id);
alter table formacion.habilitacion add constraint fk_habilitacion_certificado_id foreign key (predio_id, certificado_id) references formacion.certificado(predio_id, id);
alter table activos.activo add constraint fk_activo_predio foreign key (predio_id) references nucleo.predio(id);
alter table activos.activo add constraint fk_activo_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table activos.activo add constraint fk_activo_responsable_id foreign key (predio_id, responsable_id) references terceros.empleado(predio_id, id);
alter table activos.activo add constraint fk_activo_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table activos.activo add constraint fk_activo_vehiculo_id foreign key (predio_id, vehiculo_id) references inventario.vehiculo(predio_id, id);
alter table activos.activo add constraint fk_activo_dispositivo_id foreign key (predio_id, dispositivo_id) references iot.dispositivo(predio_id, id);
alter table activos.plan_mantenimiento add constraint fk_plan_mantenimiento_predio foreign key (predio_id) references nucleo.predio(id);
alter table activos.plan_mantenimiento add constraint fk_plan_mantenimiento_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table activos.orden_trabajo add constraint fk_orden_trabajo_predio foreign key (predio_id) references nucleo.predio(id);
alter table activos.orden_trabajo add constraint fk_orden_trabajo_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table activos.orden_trabajo add constraint fk_orden_trabajo_plan_id foreign key (predio_id, plan_id) references activos.plan_mantenimiento(predio_id, id);
alter table activos.orden_trabajo add constraint fk_orden_trabajo_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table activos.repuesto_orden add constraint fk_repuesto_orden_predio foreign key (predio_id) references nucleo.predio(id);
alter table activos.repuesto_orden add constraint fk_repuesto_orden_orden_id foreign key (predio_id, orden_id) references activos.orden_trabajo(predio_id, id);
alter table activos.repuesto_orden add constraint fk_repuesto_orden_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table activos.repuesto_orden add constraint fk_repuesto_orden_movimiento_id foreign key (predio_id, movimiento_id) references inventario.movimiento_inventario(predio_id, id);
alter table activos.uso_activo add constraint fk_uso_activo_predio foreign key (predio_id) references nucleo.predio(id);
alter table activos.uso_activo add constraint fk_uso_activo_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table activos.uso_activo add constraint fk_uso_activo_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table activos.uso_activo add constraint fk_uso_activo_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table activos.uso_activo add constraint fk_uso_activo_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table activos.uso_activo add constraint fk_uso_activo_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table activos.depreciacion add constraint fk_depreciacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table activos.depreciacion add constraint fk_depreciacion_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table activos.depreciacion add constraint fk_depreciacion_comprobante_id foreign key (predio_id, comprobante_id) references finanzas.comprobante(predio_id, id);
alter table documental.documento add constraint fk_documento_predio foreign key (predio_id) references nucleo.predio(id);
alter table documental.documento add constraint fk_documento_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table documental.documento add constraint fk_documento_rol_id foreign key (rol_id) references nucleo.rol(id);
alter table documental.version_documento add constraint fk_version_documento_predio foreign key (predio_id) references nucleo.predio(id);
alter table documental.version_documento add constraint fk_version_documento_documento_id foreign key (predio_id, documento_id) references documental.documento(predio_id, id);
alter table documental.version_documento add constraint fk_version_documento_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table documental.vinculo_documento add constraint fk_vinculo_documento_predio foreign key (predio_id) references nucleo.predio(id);
alter table documental.vinculo_documento add constraint fk_vinculo_documento_documento_id foreign key (predio_id, documento_id) references documental.documento(predio_id, id);
alter table cumplimiento.requisito add constraint fk_requisito_norma_id foreign key (norma_id) references cumplimiento.norma(id);
alter table cumplimiento.expediente add constraint fk_expediente_predio foreign key (predio_id) references nucleo.predio(id);
alter table cumplimiento.expediente add constraint fk_expediente_norma_id foreign key (norma_id) references cumplimiento.norma(id);
alter table cumplimiento.expediente add constraint fk_expediente_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table cumplimiento.evaluacion_requisito add constraint fk_evaluacion_requisito_predio foreign key (predio_id) references nucleo.predio(id);
alter table cumplimiento.evaluacion_requisito add constraint fk_evaluacion_requisito_expediente_id foreign key (predio_id, expediente_id) references cumplimiento.expediente(predio_id, id);
alter table cumplimiento.evaluacion_requisito add constraint fk_evaluacion_requisito_requisito_id foreign key (requisito_id) references cumplimiento.requisito(id);
alter table cumplimiento.evaluacion_requisito add constraint fk_evaluacion_requisito_evaluado_por foreign key (evaluado_por) references nucleo.usuario(id);
alter table cumplimiento.evaluacion_requisito add constraint fk_evaluacion_requisito_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table cumplimiento.evidencia_requisito add constraint fk_evidencia_requisito_predio foreign key (predio_id) references nucleo.predio(id);
alter table cumplimiento.evidencia_requisito add constraint fk_evidencia_requisito_evaluacion_id foreign key (predio_id, evaluacion_id) references cumplimiento.evaluacion_requisito(predio_id, id);
alter table cumplimiento.evidencia_requisito add constraint fk_evidencia_requisito_documento_id foreign key (predio_id, documento_id) references documental.documento(predio_id, id);
alter table cumplimiento.auditoria_externa add constraint fk_auditoria_externa_predio foreign key (predio_id) references nucleo.predio(id);
alter table cumplimiento.auditoria_externa add constraint fk_auditoria_externa_expediente_id foreign key (predio_id, expediente_id) references cumplimiento.expediente(predio_id, id);
alter table cumplimiento.auditoria_externa add constraint fk_auditoria_externa_informe_documento_id foreign key (predio_id, informe_documento_id) references documental.documento(predio_id, id);
alter table cumplimiento.no_conformidad add constraint fk_no_conformidad_predio foreign key (predio_id) references nucleo.predio(id);
alter table cumplimiento.no_conformidad add constraint fk_no_conformidad_expediente_id foreign key (predio_id, expediente_id) references cumplimiento.expediente(predio_id, id);
alter table cumplimiento.no_conformidad add constraint fk_no_conformidad_auditoria_id foreign key (predio_id, auditoria_id) references cumplimiento.auditoria_externa(predio_id, id);
alter table cumplimiento.no_conformidad add constraint fk_no_conformidad_requisito_id foreign key (requisito_id) references cumplimiento.requisito(id);
alter table cumplimiento.no_conformidad add constraint fk_no_conformidad_cerrada_por foreign key (cerrada_por) references nucleo.usuario(id);
alter table cumplimiento.accion_correctiva add constraint fk_accion_correctiva_predio foreign key (predio_id) references nucleo.predio(id);
alter table cumplimiento.accion_correctiva add constraint fk_accion_correctiva_no_conformidad_id foreign key (predio_id, no_conformidad_id) references cumplimiento.no_conformidad(predio_id, id);
alter table cumplimiento.accion_correctiva add constraint fk_accion_correctiva_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table cumplimiento.accion_correctiva add constraint fk_accion_correctiva_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table cumplimiento.accion_correctiva add constraint fk_accion_correctiva_verificada_por foreign key (verificada_por) references nucleo.usuario(id);
alter table seguros.poliza add constraint fk_poliza_predio foreign key (predio_id) references nucleo.predio(id);
alter table seguros.poliza add constraint fk_poliza_aseguradora_id foreign key (predio_id, aseguradora_id) references terceros.tercero(predio_id, id);
alter table seguros.poliza add constraint fk_poliza_corredor_id foreign key (predio_id, corredor_id) references terceros.tercero(predio_id, id);
alter table seguros.poliza add constraint fk_poliza_documento_id foreign key (predio_id, documento_id) references documental.documento(predio_id, id);
alter table seguros.bien_asegurado add constraint fk_bien_asegurado_predio foreign key (predio_id) references nucleo.predio(id);
alter table seguros.bien_asegurado add constraint fk_bien_asegurado_poliza_id foreign key (predio_id, poliza_id) references seguros.poliza(predio_id, id);
alter table seguros.bien_asegurado add constraint fk_bien_asegurado_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table seguros.bien_asegurado add constraint fk_bien_asegurado_siembra_id foreign key (predio_id, siembra_id) references produccion.siembra(predio_id, id);
alter table seguros.bien_asegurado add constraint fk_bien_asegurado_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table seguros.bien_asegurado add constraint fk_bien_asegurado_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table seguros.indice_poliza add constraint fk_indice_poliza_predio foreign key (predio_id) references nucleo.predio(id);
alter table seguros.indice_poliza add constraint fk_indice_poliza_poliza_id foreign key (predio_id, poliza_id) references seguros.poliza(predio_id, id);
alter table seguros.indice_poliza add constraint fk_indice_poliza_sensor_id foreign key (predio_id, sensor_id) references iot.sensor(predio_id, id);
alter table seguros.aviso_siniestro add constraint fk_aviso_siniestro_predio foreign key (predio_id) references nucleo.predio(id);
alter table seguros.aviso_siniestro add constraint fk_aviso_siniestro_poliza_id foreign key (predio_id, poliza_id) references seguros.poliza(predio_id, id);
alter table seguros.aviso_siniestro add constraint fk_aviso_siniestro_indice_id foreign key (predio_id, indice_id) references seguros.indice_poliza(predio_id, id);
alter table seguros.aviso_siniestro add constraint fk_aviso_siniestro_revisado_por foreign key (revisado_por) references nucleo.usuario(id);
alter table ia.diagnostico_imagen add constraint fk_diagnostico_imagen_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.diagnostico_imagen add constraint fk_diagnostico_imagen_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table ia.diagnostico_imagen add constraint fk_diagnostico_imagen_siembra_id foreign key (predio_id, siembra_id) references produccion.siembra(predio_id, id);
alter table ia.diagnostico_imagen add constraint fk_diagnostico_imagen_lote_animal_id foreign key (predio_id, lote_animal_id) references produccion.lote_animal(predio_id, id);
alter table ia.diagnostico_imagen add constraint fk_diagnostico_imagen_tomada_por foreign key (tomada_por) references nucleo.usuario(id);
alter table ia.diagnostico_imagen add constraint fk_diagnostico_imagen_revisado_por foreign key (revisado_por) references nucleo.usuario(id);
alter table ia.diagnostico_imagen add constraint fk_diagnostico_imagen_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table ia.escenario add constraint fk_escenario_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.escenario add constraint fk_escenario_creado_por foreign key (creado_por) references nucleo.usuario(id);
alter table ia.escenario add constraint fk_escenario_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table ia.decision add constraint fk_decision_predio foreign key (predio_id) references nucleo.predio(id);
alter table ia.decision add constraint fk_decision_decidido_por foreign key (decidido_por) references nucleo.usuario(id);
alter table ia.decision add constraint fk_decision_recomendacion_id foreign key (predio_id, recomendacion_id) references ia.recomendacion(predio_id, id);
alter table ia.decision add constraint fk_decision_escenario_id foreign key (predio_id, escenario_id) references ia.escenario(predio_id, id);
alter table ia.decision add constraint fk_decision_iniciativa_id foreign key (predio_id, iniciativa_id) references estrategia.iniciativa(predio_id, id);
alter table finanzas.clasificacion_costo add constraint fk_clasificacion_costo_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.clasificacion_costo add constraint fk_clasificacion_costo_cuenta_id foreign key (cuenta_id) references finanzas.cuenta_contable(id);
alter table finanzas.actividad_costo add constraint fk_actividad_costo_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.actividad_costo add constraint fk_actividad_costo_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table finanzas.asignacion_costo add constraint fk_asignacion_costo_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.asignacion_costo add constraint fk_asignacion_costo_actividad_id foreign key (predio_id, actividad_id) references finanzas.actividad_costo(predio_id, id);
alter table finanzas.asignacion_costo add constraint fk_asignacion_costo_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table finanzas.costo_estandar add constraint fk_costo_estandar_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.costo_estandar add constraint fk_costo_estandar_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table finanzas.presupuesto add constraint fk_presupuesto_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.presupuesto add constraint fk_presupuesto_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table finanzas.premisa_presupuesto add constraint fk_premisa_presupuesto_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.premisa_presupuesto add constraint fk_premisa_presupuesto_presupuesto_id foreign key (predio_id, presupuesto_id) references finanzas.presupuesto(predio_id, id);
alter table finanzas.presupuesto_detalle add constraint fk_presupuesto_detalle_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.presupuesto_detalle add constraint fk_presupuesto_detalle_presupuesto_id foreign key (predio_id, presupuesto_id) references finanzas.presupuesto(predio_id, id);
alter table finanzas.presupuesto_detalle add constraint fk_presupuesto_detalle_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table finanzas.presupuesto_detalle add constraint fk_presupuesto_detalle_cuenta_id foreign key (cuenta_id) references finanzas.cuenta_contable(id);
alter table finanzas.presupuesto_detalle add constraint fk_presupuesto_detalle_producto_id foreign key (predio_id, producto_id) references inventario.producto(predio_id, id);
alter table finanzas.estado_financiero add constraint fk_estado_financiero_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.estado_financiero add constraint fk_estado_financiero_generado_por foreign key (generado_por) references nucleo.usuario(id);
alter table finanzas.valor_indicador add constraint fk_valor_indicador_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.valor_indicador add constraint fk_valor_indicador_indicador_id foreign key (indicador_id) references finanzas.indicador(id);
alter table finanzas.valor_indicador add constraint fk_valor_indicador_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table finanzas.anticipo_proveedor add constraint fk_anticipo_proveedor_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.anticipo_proveedor add constraint fk_anticipo_proveedor_proveedor_id foreign key (predio_id, proveedor_id) references terceros.proveedor(predio_id, id);
alter table finanzas.anticipo_proveedor add constraint fk_anticipo_proveedor_comprobante_id foreign key (predio_id, comprobante_id) references finanzas.comprobante(predio_id, id);
alter table finanzas.aplicacion_anticipo add constraint fk_aplicacion_anticipo_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.aplicacion_anticipo add constraint fk_aplicacion_anticipo_anticipo_id foreign key (predio_id, anticipo_id) references finanzas.anticipo_proveedor(predio_id, id);
alter table finanzas.aplicacion_anticipo add constraint fk_aplicacion_anticipo_orden_compra_id foreign key (predio_id, orden_compra_id) references compras.orden_compra(predio_id, id);
alter table finanzas.reporte_indicadores add constraint fk_reporte_indicadores_predio foreign key (predio_id) references nucleo.predio(id);
alter table finanzas.reporte_indicadores add constraint fk_reporte_indicadores_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table finanzas.reporte_indicadores add constraint fk_reporte_indicadores_autorizado_por foreign key (autorizado_por) references nucleo.usuario(id);
alter table iot.mision_robot add constraint fk_mision_robot_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.mision_robot add constraint fk_mision_robot_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table iot.mision_robot add constraint fk_mision_robot_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table iot.mision_robot add constraint fk_mision_robot_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table iot.mision_robot add constraint fk_mision_robot_piloto_id foreign key (predio_id, piloto_id) references terceros.tercero(predio_id, id);
alter table iot.mision_robot add constraint fk_mision_robot_poliza_id foreign key (predio_id, poliza_id) references seguros.poliza(predio_id, id);
alter table iot.prioridad_carga add constraint fk_prioridad_carga_predio foreign key (predio_id) references nucleo.predio(id);
alter table iot.prioridad_carga add constraint fk_prioridad_carga_actuador_id foreign key (predio_id, actuador_id) references iot.actuador(predio_id, id);
alter table nucleo.llave_api add constraint fk_llave_api_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.llave_api add constraint fk_llave_api_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table nucleo.webhook_suscripcion add constraint fk_webhook_suscripcion_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.webhook_suscripcion add constraint fk_webhook_suscripcion_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table nucleo.webhook_entrega add constraint fk_webhook_entrega_predio foreign key (predio_id) references nucleo.predio(id);
alter table nucleo.webhook_entrega add constraint fk_webhook_entrega_suscripcion_id foreign key (predio_id, suscripcion_id) references nucleo.webhook_suscripcion(predio_id, id);
alter table seguridad.factor_autenticacion add constraint fk_factor_autenticacion_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table seguridad.sesion_usuario add constraint fk_sesion_usuario_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table seguridad.intento_acceso add constraint fk_intento_acceso_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table seguridad.bloqueo add constraint fk_bloqueo_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table seguridad.bloqueo add constraint fk_bloqueo_regla_id foreign key (regla_id) references seguridad.regla_deteccion(id);
alter table seguridad.bloqueo add constraint fk_bloqueo_levantado_por foreign key (levantado_por) references nucleo.usuario(id);
alter table seguridad.alerta_seguridad add constraint fk_alerta_seguridad_regla_id foreign key (regla_id) references seguridad.regla_deteccion(id);
alter table seguridad.alerta_seguridad add constraint fk_alerta_seguridad_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table seguridad.alerta_seguridad add constraint fk_alerta_seguridad_predio_id foreign key (predio_id) references nucleo.predio(id);
alter table seguridad.alerta_seguridad add constraint fk_alerta_seguridad_atendida_por foreign key (atendida_por) references nucleo.usuario(id);
alter table seguridad.alerta_seguridad add constraint fk_alerta_seguridad_incidente_id foreign key (incidente_id) references seguridad.incidente(id);
alter table seguridad.incidente add constraint fk_incidente_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table seguridad.ejecucion_prueba add constraint fk_ejecucion_prueba_ejecutada_por foreign key (ejecutada_por) references nucleo.usuario(id);
alter table crm.segmento add constraint fk_segmento_predio foreign key (predio_id) references nucleo.predio(id);
alter table crm.campana add constraint fk_campana_predio foreign key (predio_id) references nucleo.predio(id);
alter table crm.campana add constraint fk_campana_segmento_id foreign key (predio_id, segmento_id) references crm.segmento(predio_id, id);
alter table crm.campana add constraint fk_campana_publicacion_id foreign key (predio_id, publicacion_id) references redes.publicacion(predio_id, id);
alter table crm.formulario_captura add constraint fk_formulario_captura_predio foreign key (predio_id) references nucleo.predio(id);
alter table crm.formulario_captura add constraint fk_formulario_captura_campana_id foreign key (predio_id, campana_id) references crm.campana(predio_id, id);
alter table crm.prospecto add constraint fk_prospecto_predio foreign key (predio_id) references nucleo.predio(id);
alter table crm.prospecto add constraint fk_prospecto_formulario_id foreign key (predio_id, formulario_id) references crm.formulario_captura(predio_id, id);
alter table crm.prospecto add constraint fk_prospecto_campana_id foreign key (predio_id, campana_id) references crm.campana(predio_id, id);
alter table crm.prospecto add constraint fk_prospecto_segmento_id foreign key (predio_id, segmento_id) references crm.segmento(predio_id, id);
alter table crm.prospecto add constraint fk_prospecto_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table crm.prospecto add constraint fk_prospecto_consentimiento_id foreign key (predio_id, consentimiento_id) references terceros.consentimiento_datos(predio_id, id);
alter table crm.prospecto add constraint fk_prospecto_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table crm.prospecto add constraint fk_prospecto_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table crm.contacto_empresa add constraint fk_contacto_empresa_predio foreign key (predio_id) references nucleo.predio(id);
alter table crm.contacto_empresa add constraint fk_contacto_empresa_prospecto_id foreign key (predio_id, prospecto_id) references crm.prospecto(predio_id, id);
alter table crm.contacto_empresa add constraint fk_contacto_empresa_consentimiento_id foreign key (predio_id, consentimiento_id) references terceros.consentimiento_datos(predio_id, id);
alter table crm.interaccion add constraint fk_interaccion_predio foreign key (predio_id) references nucleo.predio(id);
alter table crm.interaccion add constraint fk_interaccion_prospecto_id foreign key (predio_id, prospecto_id) references crm.prospecto(predio_id, id);
alter table crm.interaccion add constraint fk_interaccion_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table crm.interaccion add constraint fk_interaccion_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table crm.interaccion add constraint fk_interaccion_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table crm.interaccion add constraint fk_interaccion_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table crm.oportunidad add constraint fk_oportunidad_predio foreign key (predio_id) references nucleo.predio(id);
alter table crm.oportunidad add constraint fk_oportunidad_prospecto_id foreign key (predio_id, prospecto_id) references crm.prospecto(predio_id, id);
alter table crm.oportunidad add constraint fk_oportunidad_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table crm.oportunidad add constraint fk_oportunidad_pedido_id foreign key (predio_id, pedido_id) references comercial.pedido(predio_id, id);
alter table crm.oportunidad add constraint fk_oportunidad_linea_negocio_id foreign key (predio_id, linea_negocio_id) references estrategia.linea_negocio(predio_id, id);
alter table estrategia.linea_negocio add constraint fk_linea_negocio_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.linea_negocio add constraint fk_linea_negocio_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table estrategia.factor_dofa add constraint fk_factor_dofa_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.factor_dofa add constraint fk_factor_dofa_linea_negocio_id foreign key (predio_id, linea_negocio_id) references estrategia.linea_negocio(predio_id, id);
alter table estrategia.estudio_mercado add constraint fk_estudio_mercado_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.estudio_mercado add constraint fk_estudio_mercado_segmento_id foreign key (predio_id, segmento_id) references crm.segmento(predio_id, id);
alter table estrategia.iniciativa add constraint fk_iniciativa_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.iniciativa add constraint fk_iniciativa_linea_negocio_id foreign key (predio_id, linea_negocio_id) references estrategia.linea_negocio(predio_id, id);
alter table estrategia.iniciativa add constraint fk_iniciativa_segmento_id foreign key (predio_id, segmento_id) references crm.segmento(predio_id, id);
alter table estrategia.iniciativa add constraint fk_iniciativa_propuesta_por foreign key (propuesta_por) references nucleo.usuario(id);
alter table estrategia.iniciativa add constraint fk_iniciativa_agente_id foreign key (predio_id, agente_id) references ia.agente(predio_id, id);
alter table estrategia.iniciativa add constraint fk_iniciativa_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table estrategia.evaluacion_proyecto add constraint fk_evaluacion_proyecto_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.evaluacion_proyecto add constraint fk_evaluacion_proyecto_iniciativa_id foreign key (predio_id, iniciativa_id) references estrategia.iniciativa(predio_id, id);
alter table estrategia.flujo_proyecto add constraint fk_flujo_proyecto_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.flujo_proyecto add constraint fk_flujo_proyecto_evaluacion_id foreign key (predio_id, evaluacion_id) references estrategia.evaluacion_proyecto(predio_id, id);
alter table estrategia.reinversion add constraint fk_reinversion_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.reinversion add constraint fk_reinversion_linea_origen_id foreign key (predio_id, linea_origen_id) references estrategia.linea_negocio(predio_id, id);
alter table estrategia.reinversion add constraint fk_reinversion_iniciativa_id foreign key (predio_id, iniciativa_id) references estrategia.iniciativa(predio_id, id);
alter table estrategia.reinversion add constraint fk_reinversion_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table estrategia.seguimiento_iniciativa add constraint fk_seguimiento_iniciativa_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.seguimiento_iniciativa add constraint fk_seguimiento_iniciativa_iniciativa_id foreign key (predio_id, iniciativa_id) references estrategia.iniciativa(predio_id, id);
alter table estrategia.objetivo add constraint fk_objetivo_predio foreign key (predio_id) references nucleo.predio(id);
alter table estrategia.objetivo add constraint fk_objetivo_indicador_id foreign key (indicador_id) references finanzas.indicador(id);
alter table estrategia.objetivo add constraint fk_objetivo_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table personal.area_responsabilidad add constraint fk_area_responsabilidad_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.area_responsabilidad add constraint fk_area_responsabilidad_centro_costo_id foreign key (predio_id, centro_costo_id) references finanzas.centro_costo(predio_id, id);
alter table personal.miembro_area add constraint fk_miembro_area_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.miembro_area add constraint fk_miembro_area_area_id foreign key (predio_id, area_id) references personal.area_responsabilidad(predio_id, id);
alter table personal.miembro_area add constraint fk_miembro_area_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.patron_turno add constraint fk_patron_turno_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.patron_turno_detalle add constraint fk_patron_turno_detalle_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.patron_turno_detalle add constraint fk_patron_turno_detalle_patron_id foreign key (predio_id, patron_id) references personal.patron_turno(predio_id, id);
alter table personal.cronograma add constraint fk_cronograma_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.cronograma add constraint fk_cronograma_area_id foreign key (predio_id, area_id) references personal.area_responsabilidad(predio_id, id);
alter table personal.cronograma add constraint fk_cronograma_publicado_por foreign key (publicado_por) references nucleo.usuario(id);
alter table personal.asignacion_patron add constraint fk_asignacion_patron_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.asignacion_patron add constraint fk_asignacion_patron_cronograma_id foreign key (predio_id, cronograma_id) references personal.cronograma(predio_id, id);
alter table personal.asignacion_patron add constraint fk_asignacion_patron_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table personal.asignacion_patron add constraint fk_asignacion_patron_patron_id foreign key (predio_id, patron_id) references personal.patron_turno(predio_id, id);
alter table personal.requerimiento_cobertura add constraint fk_requerimiento_cobertura_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.requerimiento_cobertura add constraint fk_requerimiento_cobertura_area_id foreign key (predio_id, area_id) references personal.area_responsabilidad(predio_id, id);
alter table personal.disponibilidad add constraint fk_disponibilidad_predio foreign key (predio_id) references nucleo.predio(id);
alter table personal.disponibilidad add constraint fk_disponibilidad_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table agenda.recurso add constraint fk_recurso_predio foreign key (predio_id) references nucleo.predio(id);
alter table agenda.recurso add constraint fk_recurso_alojamiento_id foreign key (predio_id, alojamiento_id) references turismo.alojamiento(predio_id, id);
alter table agenda.recurso add constraint fk_recurso_activo_id foreign key (predio_id, activo_id) references activos.activo(predio_id, id);
alter table agenda.recurso add constraint fk_recurso_zona_id foreign key (predio_id, zona_id) references nucleo.zona(predio_id, id);
alter table agenda.cita add constraint fk_cita_predio foreign key (predio_id) references nucleo.predio(id);
alter table agenda.cita add constraint fk_cita_recurso_id foreign key (predio_id, recurso_id) references agenda.recurso(predio_id, id);
alter table agenda.cita add constraint fk_cita_reserva_id foreign key (predio_id, reserva_id) references turismo.reserva(predio_id, id);
alter table agenda.cita add constraint fk_cita_bloqueo_id foreign key (predio_id, bloqueo_id) references turismo.bloqueo_calendario(predio_id, id);
alter table agenda.cita add constraint fk_cita_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table agenda.cita add constraint fk_cita_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table agenda.visita add constraint fk_visita_predio foreign key (predio_id) references nucleo.predio(id);
alter table agenda.visita add constraint fk_visita_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table agenda.visita add constraint fk_visita_zona_destino_id foreign key (predio_id, zona_destino_id) references nucleo.zona(predio_id, id);
alter table agenda.visita add constraint fk_visita_anfitrion_id foreign key (anfitrion_id) references nucleo.usuario(id);
alter table agenda.visita add constraint fk_visita_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table agenda.visita add constraint fk_visita_cita_id foreign key (predio_id, cita_id) references agenda.cita(predio_id, id);
alter table agenda.registro_acceso add constraint fk_registro_acceso_predio foreign key (predio_id) references nucleo.predio(id);
alter table agenda.registro_acceso add constraint fk_registro_acceso_visita_id foreign key (predio_id, visita_id) references agenda.visita(predio_id, id);
alter table agenda.registro_acceso add constraint fk_registro_acceso_empleado_id foreign key (predio_id, empleado_id) references terceros.empleado(predio_id, id);
alter table agenda.registro_acceso add constraint fk_registro_acceso_registrado_por foreign key (registrado_por) references nucleo.usuario(id);
alter table agenda.registro_acceso add constraint fk_registro_acceso_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table formacion.necesidad_formacion add constraint fk_necesidad_formacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.necesidad_formacion add constraint fk_necesidad_formacion_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table formacion.necesidad_formacion add constraint fk_necesidad_formacion_competencia_id foreign key (predio_id, competencia_id) references formacion.competencia(predio_id, id);
alter table formacion.necesidad_formacion add constraint fk_necesidad_formacion_curso_id foreign key (predio_id, curso_id) references formacion.curso(predio_id, id);
alter table formacion.encuesta add constraint fk_encuesta_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.encuesta add constraint fk_encuesta_curso_id foreign key (predio_id, curso_id) references formacion.curso(predio_id, id);
alter table formacion.encuesta add constraint fk_encuesta_sesion_id foreign key (predio_id, sesion_id) references formacion.sesion_presencial(predio_id, id);
alter table formacion.encuesta add constraint fk_encuesta_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table formacion.encuesta add constraint fk_encuesta_dispositivo foreign key (predio_id, dispositivo_captura_id) references nucleo.dispositivo_captura(predio_id, id);
alter table formacion.queja_apelacion add constraint fk_queja_apelacion_predio foreign key (predio_id) references nucleo.predio(id);
alter table formacion.queja_apelacion add constraint fk_queja_apelacion_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table formacion.queja_apelacion add constraint fk_queja_apelacion_curso_id foreign key (predio_id, curso_id) references formacion.curso(predio_id, id);
alter table formacion.queja_apelacion add constraint fk_queja_apelacion_certificado_id foreign key (predio_id, certificado_id) references formacion.certificado(predio_id, id);
alter table formacion.queja_apelacion add constraint fk_queja_apelacion_resuelta_por foreign key (resuelta_por) references nucleo.usuario(id);
alter table proyectos.proyecto add constraint fk_proyecto_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.proyecto add constraint fk_proyecto_iniciativa_id foreign key (predio_id, iniciativa_id) references estrategia.iniciativa(predio_id, id);
alter table proyectos.proyecto add constraint fk_proyecto_linea_negocio_id foreign key (predio_id, linea_negocio_id) references estrategia.linea_negocio(predio_id, id);
alter table proyectos.proyecto add constraint fk_proyecto_patrocinador_id foreign key (patrocinador_id) references nucleo.usuario(id);
alter table proyectos.proyecto add constraint fk_proyecto_director_id foreign key (director_id) references nucleo.usuario(id);
alter table proyectos.proyecto add constraint fk_proyecto_acta_documento_id foreign key (predio_id, acta_documento_id) references documental.documento(predio_id, id);
alter table proyectos.proyecto add constraint fk_proyecto_aprobado_por foreign key (aprobado_por) references nucleo.usuario(id);
alter table proyectos.interesado add constraint fk_interesado_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.interesado add constraint fk_interesado_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.interesado add constraint fk_interesado_tercero_id foreign key (predio_id, tercero_id) references terceros.tercero(predio_id, id);
alter table proyectos.interesado add constraint fk_interesado_usuario_id foreign key (usuario_id) references nucleo.usuario(id);
alter table proyectos.elemento_edt add constraint fk_elemento_edt_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.elemento_edt add constraint fk_elemento_edt_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.elemento_edt add constraint fk_elemento_edt_padre_id foreign key (predio_id, padre_id) references proyectos.elemento_edt(predio_id, id);
alter table proyectos.elemento_edt add constraint fk_elemento_edt_aceptado_por foreign key (aceptado_por) references nucleo.usuario(id);
alter table proyectos.iteracion add constraint fk_iteracion_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.iteracion add constraint fk_iteracion_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.actividad add constraint fk_actividad_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.actividad add constraint fk_actividad_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.actividad add constraint fk_actividad_elemento_edt_id foreign key (predio_id, elemento_edt_id) references proyectos.elemento_edt(predio_id, id);
alter table proyectos.actividad add constraint fk_actividad_iteracion_id foreign key (predio_id, iteracion_id) references proyectos.iteracion(predio_id, id);
alter table proyectos.actividad add constraint fk_actividad_responsable_id foreign key (predio_id, responsable_id) references terceros.empleado(predio_id, id);
alter table proyectos.actividad add constraint fk_actividad_area_id foreign key (predio_id, area_id) references personal.area_responsabilidad(predio_id, id);
alter table proyectos.actividad add constraint fk_actividad_tarea_id foreign key (predio_id, tarea_id) references personal.tarea(predio_id, id);
alter table proyectos.dependencia add constraint fk_dependencia_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.dependencia add constraint fk_dependencia_predecesora_id foreign key (predio_id, predecesora_id) references proyectos.actividad(predio_id, id);
alter table proyectos.dependencia add constraint fk_dependencia_sucesora_id foreign key (predio_id, sucesora_id) references proyectos.actividad(predio_id, id);
alter table proyectos.riesgo add constraint fk_riesgo_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.riesgo add constraint fk_riesgo_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.riesgo add constraint fk_riesgo_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table proyectos.registro add constraint fk_registro_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.registro add constraint fk_registro_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.registro add constraint fk_registro_responsable_id foreign key (responsable_id) references nucleo.usuario(id);
alter table proyectos.solicitud_cambio add constraint fk_solicitud_cambio_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.solicitud_cambio add constraint fk_solicitud_cambio_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.solicitud_cambio add constraint fk_solicitud_cambio_solicitada_por foreign key (solicitada_por) references nucleo.usuario(id);
alter table proyectos.solicitud_cambio add constraint fk_solicitud_cambio_decidida_por foreign key (decidida_por) references nucleo.usuario(id);
alter table proyectos.linea_base add constraint fk_linea_base_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.linea_base add constraint fk_linea_base_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);
alter table proyectos.linea_base add constraint fk_linea_base_solicitud_cambio_id foreign key (predio_id, solicitud_cambio_id) references proyectos.solicitud_cambio(predio_id, id);
alter table proyectos.linea_base add constraint fk_linea_base_aprobada_por foreign key (aprobada_por) references nucleo.usuario(id);
alter table proyectos.medicion_valor_ganado add constraint fk_medicion_valor_ganado_predio foreign key (predio_id) references nucleo.predio(id);
alter table proyectos.medicion_valor_ganado add constraint fk_medicion_valor_ganado_proyecto_id foreign key (predio_id, proyecto_id) references proyectos.proyecto(predio_id, id);

-- Índices
create index ix_usuario_tercero_id on nucleo.usuario (tercero_id);
create index ix_rol_permiso_rol_id on nucleo.rol_permiso (rol_id);
create index ix_rol_permiso_permiso_id on nucleo.rol_permiso (permiso_id);
create index ix_usuario_rol_usuario_id on nucleo.usuario_rol (usuario_id);
create index ix_usuario_rol_rol_id on nucleo.usuario_rol (rol_id);
create index ix_auditoria_usuario_id on nucleo.auditoria (usuario_id);
create index ix_auditoria_agente_id on nucleo.auditoria (agente_id);
create index ix_evento_salida_estado_creado_en on nucleo.evento_salida (predio_id, estado, creado_en);
create index ix_predio_empleador_tercero_id on nucleo.predio (empleador_tercero_id);
create index ix_consentimiento_datos_tercero_id on terceros.consentimiento_datos (tercero_id);
create index ix_cliente_tercero_id on terceros.cliente (tercero_id);
create index ix_cliente_lista_precios_id on terceros.cliente (lista_precios_id);
create index ix_proveedor_tercero_id on terceros.proveedor (tercero_id);
create index ix_empleado_tercero_id on terceros.empleado (tercero_id);
create index ix_lote_animal_especie_id on produccion.lote_animal (especie_id);
create index ix_lote_animal_zona_id on produccion.lote_animal (zona_id);
create index ix_animal_lote_animal_id on produccion.animal (lote_animal_id);
create index ix_animal_madre_id on produccion.animal (madre_id);
create index ix_animal_padre_id on produccion.animal (padre_id);
create index ix_registro_postura_lote_animal_id on produccion.registro_postura (lote_animal_id);
create index ix_registro_postura_registrado_por on produccion.registro_postura (registrado_por);
create index ix_registro_alimentacion_lote_animal_id on produccion.registro_alimentacion (lote_animal_id);
create index ix_registro_alimentacion_producto_id on produccion.registro_alimentacion (producto_id);
create index ix_evento_sanitario_lote_animal_id on produccion.evento_sanitario (lote_animal_id);
create index ix_evento_sanitario_animal_id on produccion.evento_sanitario (animal_id);
create index ix_evento_sanitario_producto_id on produccion.evento_sanitario (producto_id);
create index ix_registro_pesaje_lote_animal_id on produccion.registro_pesaje (lote_animal_id);
create index ix_registro_pesaje_animal_id on produccion.registro_pesaje (animal_id);
create index ix_evento_reproductivo_hembra_id on produccion.evento_reproductivo (hembra_id);
create index ix_evento_reproductivo_macho_id on produccion.evento_reproductivo (macho_id);
create index ix_calidad_agua_estanque_zona_id on produccion.calidad_agua_estanque (zona_id);
create index ix_siembra_zona_id on produccion.siembra (zona_id);
create index ix_siembra_cultivo_id on produccion.siembra (cultivo_id);
create index ix_labor_cultural_siembra_id on produccion.labor_cultural (siembra_id);
create index ix_labor_cultural_producto_id on produccion.labor_cultural (producto_id);
create index ix_labor_cultural_tarea_id on produccion.labor_cultural (tarea_id);
create index ix_labor_cultural_mision_robot_id on produccion.labor_cultural (mision_robot_id);
create index ix_cosecha_siembra_id on produccion.cosecha (siembra_id);
create index ix_cosecha_producto_id on produccion.cosecha (producto_id);
create index ix_cosecha_lote_inventario_id on produccion.cosecha (lote_inventario_id);
create index ix_analisis_suelo_zona_id on produccion.analisis_suelo (zona_id);
create index ix_tanque_fuente_agua_id on riego.tanque (fuente_agua_id);
create index ix_tanque_zona_id on riego.tanque (zona_id);
create index ix_tanque_sensor_nivel_id on riego.tanque (sensor_nivel_id);
create index ix_sistema_riego_tanque_id on riego.sistema_riego (tanque_id);
create index ix_valvula_sistema_riego_id on riego.valvula (sistema_riego_id);
create index ix_valvula_zona_id on riego.valvula (zona_id);
create index ix_valvula_actuador_id on riego.valvula (actuador_id);
create index ix_evento_riego_valvula_id on riego.evento_riego (valvula_id);
create index ix_evento_riego_registrado_por on riego.evento_riego (registrado_por);
create index ix_evento_riego_regla_id on riego.evento_riego (regla_id);
create index ix_categoria_producto_padre_id on inventario.categoria_producto (padre_id);
create index ix_producto_categoria_id on inventario.producto (categoria_id);
create index ix_producto_unidad_id on inventario.producto (unidad_id);
create index ix_bodega_zona_id on inventario.bodega (zona_id);
create index ix_bodega_sensor_temperatura_id on inventario.bodega (sensor_temperatura_id);
create index ix_lote_inventario_producto_id on inventario.lote_inventario (producto_id);
create index ix_lote_inventario_bodega_id on inventario.lote_inventario (bodega_id);
create index ix_lote_inventario_producto_id_estado_fecha_vencimiento on inventario.lote_inventario (predio_id, producto_id, estado, fecha_vencimiento);
create index ix_movimiento_inventario_lote_inventario_id on inventario.movimiento_inventario (lote_inventario_id);
create index ix_movimiento_inventario_pesaje_id on inventario.movimiento_inventario (pesaje_id);
create index ix_movimiento_inventario_lectura_codigo_id on inventario.movimiento_inventario (lectura_codigo_id);
create index ix_movimiento_inventario_usuario_id on inventario.movimiento_inventario (usuario_id);
create index ix_movimiento_inventario_lote_inventario_id_ocurrido_en on inventario.movimiento_inventario (predio_id, lote_inventario_id, ocurrido_en);
create index ix_precio_producto_lista_precios_id on comercial.precio_producto (lista_precios_id);
create index ix_precio_producto_producto_id on comercial.precio_producto (producto_id);
create index ix_precio_producto_propuesta_precio_id on comercial.precio_producto (propuesta_precio_id);
create index ix_precio_producto_aprobado_por on comercial.precio_producto (aprobado_por);
create index ix_precio_producto_producto_id_lista_precios_id_vigente_desde on comercial.precio_producto (predio_id, producto_id, lista_precios_id, vigente_desde);
create index ix_propuesta_precio_producto_id on comercial.propuesta_precio (producto_id);
create index ix_propuesta_precio_lista_precios_id on comercial.propuesta_precio (lista_precios_id);
create index ix_propuesta_precio_agente_id on comercial.propuesta_precio (agente_id);
create index ix_propuesta_precio_revisado_por on comercial.propuesta_precio (revisado_por);
create index ix_pedido_cliente_id on comercial.pedido (cliente_id);
create index ix_pedido_pedido_recurrente_id on comercial.pedido (pedido_recurrente_id);
create index ix_pedido_creado_por_agente_id on comercial.pedido (creado_por_agente_id);
create index ix_pedido_vendedor_id on comercial.pedido (vendedor_id);
create index ix_pedido_detalle_pedido_id on comercial.pedido_detalle (pedido_id);
create index ix_pedido_detalle_producto_id on comercial.pedido_detalle (producto_id);
create index ix_pedido_detalle_precio_producto_id on comercial.pedido_detalle (precio_producto_id);
create index ix_factura_pedido_id on comercial.factura (pedido_id);
create index ix_factura_cliente_id on comercial.factura (cliente_id);
create index ix_pago_pedido_id on comercial.pago (pedido_id);
create index ix_pago_factura_id on comercial.pago (factura_id);
create index ix_pago_confirmado_por on comercial.pago (confirmado_por);
create index ix_entrega_pedido_id on comercial.entrega (pedido_id);
create index ix_entrega_vehiculo_id on comercial.entrega (vehiculo_id);
create index ix_orden_compra_proveedor_id on compras.orden_compra (proveedor_id);
create index ix_orden_compra_aprobado_por on compras.orden_compra (aprobado_por);
create index ix_orden_compra_detalle_orden_compra_id on compras.orden_compra_detalle (orden_compra_id);
create index ix_orden_compra_detalle_producto_id on compras.orden_compra_detalle (producto_id);
create index ix_cotizacion_proveedor_proveedor_id on compras.cotizacion_proveedor (proveedor_id);
create index ix_cotizacion_proveedor_producto_id on compras.cotizacion_proveedor (producto_id);
create index ix_precio_mercado_producto_id on compras.precio_mercado (producto_id);
create index ix_cuenta_contable_padre_id on finanzas.cuenta_contable (padre_id);
create index ix_comprobante_aprobado_por on finanzas.comprobante (aprobado_por);
create index ix_movimiento_contable_comprobante_id on finanzas.movimiento_contable (comprobante_id);
create index ix_movimiento_contable_cuenta_id on finanzas.movimiento_contable (cuenta_id);
create index ix_movimiento_contable_tercero_id on finanzas.movimiento_contable (tercero_id);
create index ix_movimiento_contable_centro_costo_id on finanzas.movimiento_contable (centro_costo_id);
create index ix_agente_herramienta_agente_id on ia.agente_herramienta (agente_id);
create index ix_agente_herramienta_herramienta_id on ia.agente_herramienta (herramienta_id);
create index ix_solicitud_aprobacion_agente_id on ia.solicitud_aprobacion (agente_id);
create index ix_solicitud_aprobacion_herramienta_id on ia.solicitud_aprobacion (herramienta_id);
create index ix_solicitud_aprobacion_resuelto_por on ia.solicitud_aprobacion (resuelto_por);
create index ix_solicitud_aprobacion_estado_vence_en on ia.solicitud_aprobacion (predio_id, estado, vence_en);
create index ix_documento_conocimiento_aprobado_por on ia.documento_conocimiento (aprobado_por);
create index ix_fragmento_conocimiento_documento_id on ia.fragmento_conocimiento (documento_id);
create index ix_recomendacion_agente_id on ia.recomendacion (agente_id);
create index ix_recomendacion_responsable_id on ia.recomendacion (responsable_id);
create index ix_evaluacion_respuesta_agente_id on ia.evaluacion_respuesta (agente_id);
create index ix_consumo_ia_agente_id on ia.consumo_ia (agente_id);
create index ix_publicacion_cuenta_red_id on redes.publicacion (cuenta_red_id);
create index ix_publicacion_agente_id on redes.publicacion (agente_id);
create index ix_publicacion_aprobado_por on redes.publicacion (aprobado_por);
create index ix_publicacion_recomendacion_id on redes.publicacion (recomendacion_id);
create index ix_alojamiento_zona_id on turismo.alojamiento (zona_id);
create index ix_reserva_cliente_id on turismo.reserva (cliente_id);
create index ix_reserva_alojamiento_id on turismo.reserva (alojamiento_id);
create index ix_reserva_plan_turistico_id on turismo.reserva (plan_turistico_id);
create index ix_reserva_pedido_id on turismo.reserva (pedido_id);
create index ix_dispositivo_pasarela_id on iot.dispositivo (pasarela_id);
create index ix_dispositivo_zona_id on iot.dispositivo (zona_id);
create index ix_sensor_dispositivo_id on iot.sensor (dispositivo_id);
create index ix_actuador_dispositivo_id on iot.actuador (dispositivo_id);
create index ix_actuador_zona_seguridad_id on iot.actuador (zona_seguridad_id);
create index ix_lectura_sensor_id on iot.lectura (sensor_id);
create index ix_lectura_sensor_id_medido_en on iot.lectura (predio_id, sensor_id, medido_en);
create index ix_regla_automatizacion_actuador_id on iot.regla_automatizacion (actuador_id);
create index ix_regla_automatizacion_aprobado_por on iot.regla_automatizacion (aprobado_por);
create index ix_comando_actuador_actuador_id on iot.comando_actuador (actuador_id);
create index ix_comando_actuador_regla_id on iot.comando_actuador (regla_id);
create index ix_comando_actuador_solicitado_por on iot.comando_actuador (solicitado_por);
create index ix_dispositivo_captura_usuario_asignado_id on nucleo.dispositivo_captura (usuario_asignado_id);
create index ix_sincronizacion_dispositivo_captura_id on nucleo.sincronizacion (dispositivo_captura_id);
create index ix_sincronizacion_usuario_id on nucleo.sincronizacion (usuario_id);
create index ix_etiqueta_lote_inventario_id on inventario.etiqueta (lote_inventario_id);
create index ix_etiqueta_impresora_id on inventario.etiqueta (impresora_id);
create index ix_lectura_codigo_etiqueta_id on inventario.lectura_codigo (etiqueta_id);
create index ix_lectura_codigo_usuario_id on inventario.lectura_codigo (usuario_id);
create index ix_pesaje_usuario_id on inventario.pesaje (usuario_id);
create index ix_conteo_fisico_bodega_id on inventario.conteo_fisico (bodega_id);
create index ix_conteo_fisico_responsable_id on inventario.conteo_fisico (responsable_id);
create index ix_conteo_detalle_conteo_fisico_id on inventario.conteo_detalle (conteo_fisico_id);
create index ix_conteo_detalle_lote_inventario_id on inventario.conteo_detalle (lote_inventario_id);
create index ix_conteo_detalle_movimiento_ajuste_id on inventario.conteo_detalle (movimiento_ajuste_id);
create index ix_reserva_lote_pedido_detalle_id on comercial.reserva_lote (pedido_detalle_id);
create index ix_reserva_lote_lote_inventario_id on comercial.reserva_lote (lote_inventario_id);
create index ix_periodo_contable_cerrado_por on finanzas.periodo_contable (cerrado_por);
create index ix_plantilla_mensaje_cuenta_red_id on redes.plantilla_mensaje (cuenta_red_id);
create index ix_mensaje_saliente_cuenta_red_id on redes.mensaje_saliente (cuenta_red_id);
create index ix_mensaje_saliente_tercero_id on redes.mensaje_saliente (tercero_id);
create index ix_mensaje_saliente_plantilla_id on redes.mensaje_saliente (plantilla_id);
create index ix_mensaje_saliente_consentimiento_id on redes.mensaje_saliente (consentimiento_id);
create index ix_mensaje_saliente_cuenta_red_id_enviado_en on redes.mensaje_saliente (predio_id, cuenta_red_id, enviado_en);
create index ix_escalamiento_asignado_a on ia.escalamiento (asignado_a);
create index ix_funcionalidad_activada_por on nucleo.funcionalidad (activada_por);
create index ix_nota_voz_usuario_id on nucleo.nota_voz (usuario_id);
create index ix_clasificacion_postura_registro_postura_id on produccion.clasificacion_postura (registro_postura_id);
create index ix_clasificacion_postura_categoria_huevo_id on produccion.clasificacion_postura (categoria_huevo_id);
create index ix_registro_bioseguridad_zona_id on produccion.registro_bioseguridad (zona_id);
create index ix_registro_bioseguridad_producto_id on produccion.registro_bioseguridad (producto_id);
create index ix_produccion_abono_zona_id on produccion.produccion_abono (zona_id);
create index ix_produccion_abono_lote_inventario_id on produccion.produccion_abono (lote_inventario_id);
create index ix_vehiculo_sensor_temperatura_id on inventario.vehiculo (sensor_temperatura_id);
create index ix_excursion_temperatura_sensor_id on inventario.excursion_temperatura (sensor_id);
create index ix_excursion_temperatura_bodega_id on inventario.excursion_temperatura (bodega_id);
create index ix_excursion_temperatura_vehiculo_id on inventario.excursion_temperatura (vehiculo_id);
create index ix_bloqueo_lote_lote_inventario_id on inventario.bloqueo_lote (lote_inventario_id);
create index ix_bloqueo_lote_decidido_por on inventario.bloqueo_lote (decidido_por);
create index ix_retiro_lote_lote_inventario_id on comercial.retiro_lote (lote_inventario_id);
create index ix_retiro_lote_abierto_por on comercial.retiro_lote (abierto_por);
create index ix_retiro_aviso_retiro_lote_id on comercial.retiro_aviso (retiro_lote_id);
create index ix_retiro_aviso_cliente_id on comercial.retiro_aviso (cliente_id);
create index ix_retiro_aviso_pedido_id on comercial.retiro_aviso (pedido_id);
create index ix_pedido_recurrente_cliente_id on comercial.pedido_recurrente (cliente_id);
create index ix_pedido_recurrente_detalle_pedido_recurrente_id on comercial.pedido_recurrente_detalle (pedido_recurrente_id);
create index ix_pedido_recurrente_detalle_producto_id on comercial.pedido_recurrente_detalle (producto_id);
create index ix_permuta_factura_id on comercial.permuta (factura_id);
create index ix_permuta_documento_soporte_id on comercial.permuta (documento_soporte_id);
create index ix_permuta_registrado_por on comercial.permuta (registrado_por);
create index ix_huella_trazabilidad_lote_inventario_id on comercial.huella_trazabilidad (lote_inventario_id);
create index ix_documento_soporte_proveedor_id on compras.documento_soporte (proveedor_id);
create index ix_documento_soporte_orden_compra_id on compras.documento_soporte (orden_compra_id);
create index ix_modelo_pronostico_producto_id on ia.modelo_pronostico (producto_id);
create index ix_pronostico_demanda_modelo_pronostico_id on ia.pronostico_demanda (modelo_pronostico_id);
create index ix_pronostico_demanda_producto_id on ia.pronostico_demanda (producto_id);
create index ix_pieza_audiovisual_agente_id on redes.pieza_audiovisual (agente_id);
create index ix_pieza_audiovisual_aprobado_por on redes.pieza_audiovisual (aprobado_por);
create index ix_pieza_audiovisual_publicacion_id on redes.pieza_audiovisual (publicacion_id);
create index ix_pieza_persona_pieza_audiovisual_id on redes.pieza_persona (pieza_audiovisual_id);
create index ix_pieza_persona_tercero_id on redes.pieza_persona (tercero_id);
create index ix_bloqueo_calendario_alojamiento_id on turismo.bloqueo_calendario (alojamiento_id);
create index ix_bloqueo_calendario_plan_turistico_id on turismo.bloqueo_calendario (plan_turistico_id);
create index ix_zona_seguridad_zona_id on iot.zona_seguridad (zona_id);
create index ix_cambio_estado_alarma_zona_seguridad_id on iot.cambio_estado_alarma (zona_seguridad_id);
create index ix_cambio_estado_alarma_usuario_id on iot.cambio_estado_alarma (usuario_id);
create index ix_credencial_acceso_tercero_id on iot.credencial_acceso (tercero_id);
create index ix_credencial_acceso_zona_seguridad_id on iot.credencial_acceso (zona_seguridad_id);
create index ix_credencial_acceso_consentimiento_id on iot.credencial_acceso (consentimiento_id);
create index ix_camara_dispositivo_id on iot.camara (dispositivo_id);
create index ix_camara_zona_id on iot.camara (zona_id);
create index ix_camara_zona_seguridad_id on iot.camara (zona_seguridad_id);
create index ix_evento_seguridad_zona_seguridad_id on iot.evento_seguridad (zona_seguridad_id);
create index ix_evento_seguridad_sensor_id on iot.evento_seguridad (sensor_id);
create index ix_evento_seguridad_camara_id on iot.evento_seguridad (camara_id);
create index ix_evento_seguridad_credencial_id on iot.evento_seguridad (credencial_id);
create index ix_evento_seguridad_atendido_por on iot.evento_seguridad (atendido_por);
create index ix_evento_seguridad_zona_seguridad_id_ocurrido_en on iot.evento_seguridad (predio_id, zona_seguridad_id, ocurrido_en);
create index ix_clip_video_camara_id on iot.clip_video (camara_id);
create index ix_clip_video_evento_seguridad_id on iot.clip_video (evento_seguridad_id);
create index ix_registro_ambiental_sensor_id on ambiental.registro_ambiental (sensor_id);
create index ix_cuadrilla_lider_id on personal.cuadrilla (lider_id);
create index ix_cuadrilla_miembro_cuadrilla_id on personal.cuadrilla_miembro (cuadrilla_id);
create index ix_cuadrilla_miembro_empleado_id on personal.cuadrilla_miembro (empleado_id);
create index ix_turno_empleado_id on personal.turno (empleado_id);
create index ix_turno_area_id on personal.turno (area_id);
create index ix_turno_cronograma_id on personal.turno (cronograma_id);
create index ix_ausencia_empleado_id on personal.ausencia (empleado_id);
create index ix_ausencia_soporte_documento_id on personal.ausencia (soporte_documento_id);
create index ix_ausencia_aprobada_por on personal.ausencia (aprobada_por);
create index ix_plantilla_tarea_zona_id on personal.plantilla_tarea (zona_id);
create index ix_plantilla_tarea_competencia_id on personal.plantilla_tarea (competencia_id);
create index ix_plantilla_tarea_area_id on personal.plantilla_tarea (area_id);
create index ix_tarea_plantilla_tarea_id on personal.tarea (plantilla_tarea_id);
create index ix_tarea_zona_id on personal.tarea (zona_id);
create index ix_tarea_area_id on personal.tarea (area_id);
create index ix_tarea_lote_animal_id on personal.tarea (lote_animal_id);
create index ix_tarea_siembra_id on personal.tarea (siembra_id);
create index ix_tarea_activo_id on personal.tarea (activo_id);
create index ix_tarea_empleado_id on personal.tarea (empleado_id);
create index ix_tarea_cuadrilla_id on personal.tarea (cuadrilla_id);
create index ix_tarea_agente_id on personal.tarea (agente_id);
create index ix_tarea_aprobado_por on personal.tarea (aprobado_por);
create index ix_tarea_fecha_estado on personal.tarea (predio_id, fecha, estado);
create index ix_paso_tarea_tarea_id on personal.paso_tarea (tarea_id);
create index ix_evidencia_tarea_tarea_id on personal.evidencia_tarea (tarea_id);
create index ix_matriz_responsabilidad_rol_id on personal.matriz_responsabilidad (rol_id);
create index ix_asignacion_equipo_activo_id on personal.asignacion_equipo (activo_id);
create index ix_asignacion_equipo_empleado_id on personal.asignacion_equipo (empleado_id);
create index ix_credencial_trabajo_empleado_id on personal.credencial_trabajo (empleado_id);
create index ix_jornada_empleado_id on personal.jornada (empleado_id);
create index ix_jornada_zona_id on personal.jornada (zona_id);
create index ix_jornada_aprobada_por on personal.jornada (aprobada_por);
create index ix_concepto_nomina_cuenta_contable_id on nomina.concepto_nomina (cuenta_contable_id);
create index ix_periodo_nomina_preparado_por on nomina.periodo_nomina (preparado_por);
create index ix_periodo_nomina_cerrado_por on nomina.periodo_nomina (cerrado_por);
create index ix_periodo_nomina_aprobado_por on nomina.periodo_nomina (aprobado_por);
create index ix_periodo_nomina_comprobante_id on nomina.periodo_nomina (comprobante_id);
create index ix_periodo_nomina_ajusta_periodo_id on nomina.periodo_nomina (ajusta_periodo_id);
create index ix_novedad_periodo_id on nomina.novedad (periodo_id);
create index ix_novedad_empleado_id on nomina.novedad (empleado_id);
create index ix_novedad_concepto_id on nomina.novedad (concepto_id);
create index ix_novedad_tarea_id on nomina.novedad (tarea_id);
create index ix_novedad_jornada_id on nomina.novedad (jornada_id);
create index ix_novedad_ausencia_id on nomina.novedad (ausencia_id);
create index ix_liquidacion_periodo_id on nomina.liquidacion (periodo_id);
create index ix_liquidacion_empleado_id on nomina.liquidacion (empleado_id);
create index ix_liquidacion_detalle_liquidacion_id on nomina.liquidacion_detalle (liquidacion_id);
create index ix_liquidacion_detalle_concepto_id on nomina.liquidacion_detalle (concepto_id);
create index ix_provision_prestacion_periodo_id on nomina.provision_prestacion (periodo_id);
create index ix_provision_prestacion_empleado_id on nomina.provision_prestacion (empleado_id);
create index ix_documento_nomina_electronica_liquidacion_id on nomina.documento_nomina_electronica (liquidacion_id);
create index ix_planilla_pila_periodo_id on nomina.planilla_pila (periodo_id);
create index ix_planilla_pila_pagada_por on nomina.planilla_pila (pagada_por);
create index ix_pago_nomina_liquidacion_id on nomina.pago_nomina (liquidacion_id);
create index ix_pago_nomina_preparado_por on nomina.pago_nomina (preparado_por);
create index ix_pago_nomina_aprobado_por on nomina.pago_nomina (aprobado_por);
create index ix_pago_nomina_segunda_aprobacion_por on nomina.pago_nomina (segunda_aprobacion_por);
create index ix_exportacion_nomina_periodo_id on nomina.exportacion_nomina (periodo_id);
create index ix_exportacion_nomina_generado_por on nomina.exportacion_nomina (generado_por);
create index ix_curso_competencia_id on formacion.curso (competencia_id);
create index ix_leccion_curso_id on formacion.leccion (curso_id);
create index ix_leccion_documento_id on formacion.leccion (documento_id);
create index ix_evaluacion_curso_id on formacion.evaluacion (curso_id);
create index ix_pregunta_evaluacion_id on formacion.pregunta (evaluacion_id);
create index ix_inscripcion_curso_id on formacion.inscripcion (curso_id);
create index ix_inscripcion_tercero_id on formacion.inscripcion (tercero_id);
create index ix_progreso_inscripcion_id on formacion.progreso (inscripcion_id);
create index ix_progreso_leccion_id on formacion.progreso (leccion_id);
create index ix_sesion_presencial_curso_id on formacion.sesion_presencial (curso_id);
create index ix_sesion_presencial_instructor_id on formacion.sesion_presencial (instructor_id);
create index ix_asistencia_sesion_id on formacion.asistencia (sesion_id);
create index ix_asistencia_tercero_id on formacion.asistencia (tercero_id);
create index ix_certificado_tercero_id on formacion.certificado (tercero_id);
create index ix_certificado_competencia_id on formacion.certificado (competencia_id);
create index ix_certificado_inscripcion_id on formacion.certificado (inscripcion_id);
create index ix_certificado_sesion_id on formacion.certificado (sesion_id);
create index ix_habilitacion_tercero_id on formacion.habilitacion (tercero_id);
create index ix_habilitacion_competencia_id on formacion.habilitacion (competencia_id);
create index ix_habilitacion_certificado_id on formacion.habilitacion (certificado_id);
create index ix_activo_zona_id on activos.activo (zona_id);
create index ix_activo_responsable_id on activos.activo (responsable_id);
create index ix_activo_centro_costo_id on activos.activo (centro_costo_id);
create index ix_activo_vehiculo_id on activos.activo (vehiculo_id);
create index ix_activo_dispositivo_id on activos.activo (dispositivo_id);
create index ix_plan_mantenimiento_activo_id on activos.plan_mantenimiento (activo_id);
create index ix_orden_trabajo_activo_id on activos.orden_trabajo (activo_id);
create index ix_orden_trabajo_plan_id on activos.orden_trabajo (plan_id);
create index ix_orden_trabajo_tarea_id on activos.orden_trabajo (tarea_id);
create index ix_repuesto_orden_orden_id on activos.repuesto_orden (orden_id);
create index ix_repuesto_orden_producto_id on activos.repuesto_orden (producto_id);
create index ix_repuesto_orden_movimiento_id on activos.repuesto_orden (movimiento_id);
create index ix_uso_activo_activo_id on activos.uso_activo (activo_id);
create index ix_uso_activo_empleado_id on activos.uso_activo (empleado_id);
create index ix_uso_activo_centro_costo_id on activos.uso_activo (centro_costo_id);
create index ix_uso_activo_tarea_id on activos.uso_activo (tarea_id);
create index ix_depreciacion_activo_id on activos.depreciacion (activo_id);
create index ix_depreciacion_comprobante_id on activos.depreciacion (comprobante_id);
create index ix_documento_responsable_id on documental.documento (responsable_id);
create index ix_documento_rol_id on documental.documento (rol_id);
create index ix_version_documento_documento_id on documental.version_documento (documento_id);
create index ix_version_documento_aprobada_por on documental.version_documento (aprobada_por);
create index ix_vinculo_documento_documento_id on documental.vinculo_documento (documento_id);
create index ix_requisito_norma_id on cumplimiento.requisito (norma_id);
create index ix_expediente_norma_id on cumplimiento.expediente (norma_id);
create index ix_expediente_responsable_id on cumplimiento.expediente (responsable_id);
create index ix_evaluacion_requisito_expediente_id on cumplimiento.evaluacion_requisito (expediente_id);
create index ix_evaluacion_requisito_requisito_id on cumplimiento.evaluacion_requisito (requisito_id);
create index ix_evaluacion_requisito_evaluado_por on cumplimiento.evaluacion_requisito (evaluado_por);
create index ix_evidencia_requisito_evaluacion_id on cumplimiento.evidencia_requisito (evaluacion_id);
create index ix_evidencia_requisito_documento_id on cumplimiento.evidencia_requisito (documento_id);
create index ix_auditoria_externa_expediente_id on cumplimiento.auditoria_externa (expediente_id);
create index ix_auditoria_externa_informe_documento_id on cumplimiento.auditoria_externa (informe_documento_id);
create index ix_no_conformidad_expediente_id on cumplimiento.no_conformidad (expediente_id);
create index ix_no_conformidad_auditoria_id on cumplimiento.no_conformidad (auditoria_id);
create index ix_no_conformidad_requisito_id on cumplimiento.no_conformidad (requisito_id);
create index ix_no_conformidad_cerrada_por on cumplimiento.no_conformidad (cerrada_por);
create index ix_accion_correctiva_no_conformidad_id on cumplimiento.accion_correctiva (no_conformidad_id);
create index ix_accion_correctiva_responsable_id on cumplimiento.accion_correctiva (responsable_id);
create index ix_accion_correctiva_tarea_id on cumplimiento.accion_correctiva (tarea_id);
create index ix_accion_correctiva_verificada_por on cumplimiento.accion_correctiva (verificada_por);
create index ix_poliza_aseguradora_id on seguros.poliza (aseguradora_id);
create index ix_poliza_corredor_id on seguros.poliza (corredor_id);
create index ix_poliza_documento_id on seguros.poliza (documento_id);
create index ix_bien_asegurado_poliza_id on seguros.bien_asegurado (poliza_id);
create index ix_bien_asegurado_activo_id on seguros.bien_asegurado (activo_id);
create index ix_bien_asegurado_siembra_id on seguros.bien_asegurado (siembra_id);
create index ix_bien_asegurado_lote_animal_id on seguros.bien_asegurado (lote_animal_id);
create index ix_bien_asegurado_zona_id on seguros.bien_asegurado (zona_id);
create index ix_indice_poliza_poliza_id on seguros.indice_poliza (poliza_id);
create index ix_indice_poliza_sensor_id on seguros.indice_poliza (sensor_id);
create index ix_aviso_siniestro_poliza_id on seguros.aviso_siniestro (poliza_id);
create index ix_aviso_siniestro_indice_id on seguros.aviso_siniestro (indice_id);
create index ix_aviso_siniestro_revisado_por on seguros.aviso_siniestro (revisado_por);
create index ix_diagnostico_imagen_agente_id on ia.diagnostico_imagen (agente_id);
create index ix_diagnostico_imagen_siembra_id on ia.diagnostico_imagen (siembra_id);
create index ix_diagnostico_imagen_lote_animal_id on ia.diagnostico_imagen (lote_animal_id);
create index ix_diagnostico_imagen_tomada_por on ia.diagnostico_imagen (tomada_por);
create index ix_diagnostico_imagen_revisado_por on ia.diagnostico_imagen (revisado_por);
create index ix_escenario_creado_por on ia.escenario (creado_por);
create index ix_escenario_agente_id on ia.escenario (agente_id);
create index ix_decision_decidido_por on ia.decision (decidido_por);
create index ix_decision_recomendacion_id on ia.decision (recomendacion_id);
create index ix_decision_escenario_id on ia.decision (escenario_id);
create index ix_decision_iniciativa_id on ia.decision (iniciativa_id);
create index ix_clasificacion_costo_cuenta_id on finanzas.clasificacion_costo (cuenta_id);
create index ix_actividad_costo_centro_costo_id on finanzas.actividad_costo (centro_costo_id);
create index ix_asignacion_costo_actividad_id on finanzas.asignacion_costo (actividad_id);
create index ix_asignacion_costo_centro_costo_id on finanzas.asignacion_costo (centro_costo_id);
create index ix_costo_estandar_producto_id on finanzas.costo_estandar (producto_id);
create index ix_presupuesto_aprobado_por on finanzas.presupuesto (aprobado_por);
create index ix_premisa_presupuesto_presupuesto_id on finanzas.premisa_presupuesto (presupuesto_id);
create index ix_presupuesto_detalle_presupuesto_id on finanzas.presupuesto_detalle (presupuesto_id);
create index ix_presupuesto_detalle_centro_costo_id on finanzas.presupuesto_detalle (centro_costo_id);
create index ix_presupuesto_detalle_cuenta_id on finanzas.presupuesto_detalle (cuenta_id);
create index ix_presupuesto_detalle_producto_id on finanzas.presupuesto_detalle (producto_id);
create index ix_estado_financiero_generado_por on finanzas.estado_financiero (generado_por);
create index ix_valor_indicador_indicador_id on finanzas.valor_indicador (indicador_id);
create index ix_valor_indicador_centro_costo_id on finanzas.valor_indicador (centro_costo_id);
create index ix_valor_indicador_indicador_id_hasta on finanzas.valor_indicador (predio_id, indicador_id, hasta);
create index ix_anticipo_proveedor_proveedor_id on finanzas.anticipo_proveedor (proveedor_id);
create index ix_anticipo_proveedor_comprobante_id on finanzas.anticipo_proveedor (comprobante_id);
create index ix_aplicacion_anticipo_anticipo_id on finanzas.aplicacion_anticipo (anticipo_id);
create index ix_aplicacion_anticipo_orden_compra_id on finanzas.aplicacion_anticipo (orden_compra_id);
create index ix_reporte_indicadores_tercero_id on finanzas.reporte_indicadores (tercero_id);
create index ix_reporte_indicadores_autorizado_por on finanzas.reporte_indicadores (autorizado_por);
create index ix_mision_robot_activo_id on iot.mision_robot (activo_id);
create index ix_mision_robot_zona_id on iot.mision_robot (zona_id);
create index ix_mision_robot_aprobada_por on iot.mision_robot (aprobada_por);
create index ix_mision_robot_piloto_id on iot.mision_robot (piloto_id);
create index ix_mision_robot_poliza_id on iot.mision_robot (poliza_id);
create index ix_prioridad_carga_actuador_id on iot.prioridad_carga (actuador_id);
create index ix_llave_api_tercero_id on nucleo.llave_api (tercero_id);
create index ix_webhook_suscripcion_tercero_id on nucleo.webhook_suscripcion (tercero_id);
create index ix_webhook_entrega_suscripcion_id on nucleo.webhook_entrega (suscripcion_id);
create index ix_factor_autenticacion_usuario_id on seguridad.factor_autenticacion (usuario_id);
create index ix_sesion_usuario_usuario_id on seguridad.sesion_usuario (usuario_id);
create index ix_sesion_usuario_usuario_id_iniciada_en on seguridad.sesion_usuario (usuario_id, iniciada_en);
create index ix_intento_acceso_usuario_id on seguridad.intento_acceso (usuario_id);
create index ix_intento_acceso_ip_ocurrido_en on seguridad.intento_acceso (ip, ocurrido_en);
create index ix_intento_acceso_correo_ocurrido_en on seguridad.intento_acceso (correo, ocurrido_en);
create index ix_bloqueo_usuario_id on seguridad.bloqueo (usuario_id);
create index ix_bloqueo_regla_id on seguridad.bloqueo (regla_id);
create index ix_bloqueo_levantado_por on seguridad.bloqueo (levantado_por);
create index ix_alerta_seguridad_regla_id on seguridad.alerta_seguridad (regla_id);
create index ix_alerta_seguridad_usuario_id on seguridad.alerta_seguridad (usuario_id);
create index ix_alerta_seguridad_predio_id on seguridad.alerta_seguridad (predio_id);
create index ix_alerta_seguridad_atendida_por on seguridad.alerta_seguridad (atendida_por);
create index ix_alerta_seguridad_incidente_id on seguridad.alerta_seguridad (incidente_id);
create index ix_alerta_seguridad_ocurrido_en on seguridad.alerta_seguridad (ocurrido_en);
create index ix_incidente_responsable_id on seguridad.incidente (responsable_id);
create index ix_ejecucion_prueba_ejecutada_por on seguridad.ejecucion_prueba (ejecutada_por);
create index ix_campana_segmento_id on crm.campana (segmento_id);
create index ix_campana_publicacion_id on crm.campana (publicacion_id);
create index ix_formulario_captura_campana_id on crm.formulario_captura (campana_id);
create index ix_prospecto_formulario_id on crm.prospecto (formulario_id);
create index ix_prospecto_campana_id on crm.prospecto (campana_id);
create index ix_prospecto_segmento_id on crm.prospecto (segmento_id);
create index ix_prospecto_responsable_id on crm.prospecto (responsable_id);
create index ix_prospecto_consentimiento_id on crm.prospecto (consentimiento_id);
create index ix_prospecto_tercero_id on crm.prospecto (tercero_id);
create index ix_prospecto_etapa_proximo_contacto on crm.prospecto (predio_id, etapa, proximo_contacto);
create index ix_contacto_empresa_prospecto_id on crm.contacto_empresa (prospecto_id);
create index ix_contacto_empresa_consentimiento_id on crm.contacto_empresa (consentimiento_id);
create index ix_interaccion_prospecto_id on crm.interaccion (prospecto_id);
create index ix_interaccion_tercero_id on crm.interaccion (tercero_id);
create index ix_interaccion_usuario_id on crm.interaccion (usuario_id);
create index ix_interaccion_agente_id on crm.interaccion (agente_id);
create index ix_oportunidad_prospecto_id on crm.oportunidad (prospecto_id);
create index ix_oportunidad_tercero_id on crm.oportunidad (tercero_id);
create index ix_oportunidad_pedido_id on crm.oportunidad (pedido_id);
create index ix_oportunidad_linea_negocio_id on crm.oportunidad (linea_negocio_id);
create index ix_linea_negocio_centro_costo_id on estrategia.linea_negocio (centro_costo_id);
create index ix_factor_dofa_linea_negocio_id on estrategia.factor_dofa (linea_negocio_id);
create index ix_estudio_mercado_segmento_id on estrategia.estudio_mercado (segmento_id);
create index ix_iniciativa_linea_negocio_id on estrategia.iniciativa (linea_negocio_id);
create index ix_iniciativa_segmento_id on estrategia.iniciativa (segmento_id);
create index ix_iniciativa_propuesta_por on estrategia.iniciativa (propuesta_por);
create index ix_iniciativa_agente_id on estrategia.iniciativa (agente_id);
create index ix_iniciativa_aprobada_por on estrategia.iniciativa (aprobada_por);
create index ix_evaluacion_proyecto_iniciativa_id on estrategia.evaluacion_proyecto (iniciativa_id);
create index ix_flujo_proyecto_evaluacion_id on estrategia.flujo_proyecto (evaluacion_id);
create index ix_reinversion_linea_origen_id on estrategia.reinversion (linea_origen_id);
create index ix_reinversion_iniciativa_id on estrategia.reinversion (iniciativa_id);
create index ix_reinversion_aprobada_por on estrategia.reinversion (aprobada_por);
create index ix_seguimiento_iniciativa_iniciativa_id on estrategia.seguimiento_iniciativa (iniciativa_id);
create index ix_objetivo_indicador_id on estrategia.objetivo (indicador_id);
create index ix_objetivo_responsable_id on estrategia.objetivo (responsable_id);
create index ix_area_responsabilidad_centro_costo_id on personal.area_responsabilidad (centro_costo_id);
create index ix_miembro_area_area_id on personal.miembro_area (area_id);
create index ix_miembro_area_empleado_id on personal.miembro_area (empleado_id);
create index ix_patron_turno_detalle_patron_id on personal.patron_turno_detalle (patron_id);
create index ix_cronograma_area_id on personal.cronograma (area_id);
create index ix_cronograma_publicado_por on personal.cronograma (publicado_por);
create index ix_asignacion_patron_cronograma_id on personal.asignacion_patron (cronograma_id);
create index ix_asignacion_patron_empleado_id on personal.asignacion_patron (empleado_id);
create index ix_asignacion_patron_patron_id on personal.asignacion_patron (patron_id);
create index ix_requerimiento_cobertura_area_id on personal.requerimiento_cobertura (area_id);
create index ix_disponibilidad_empleado_id on personal.disponibilidad (empleado_id);
create index ix_recurso_alojamiento_id on agenda.recurso (alojamiento_id);
create index ix_recurso_activo_id on agenda.recurso (activo_id);
create index ix_recurso_zona_id on agenda.recurso (zona_id);
create index ix_cita_recurso_id on agenda.cita (recurso_id);
create index ix_cita_reserva_id on agenda.cita (reserva_id);
create index ix_cita_bloqueo_id on agenda.cita (bloqueo_id);
create index ix_cita_tarea_id on agenda.cita (tarea_id);
create index ix_cita_responsable_id on agenda.cita (responsable_id);
create index ix_visita_tercero_id on agenda.visita (tercero_id);
create index ix_visita_zona_destino_id on agenda.visita (zona_destino_id);
create index ix_visita_anfitrion_id on agenda.visita (anfitrion_id);
create index ix_visita_aprobada_por on agenda.visita (aprobada_por);
create index ix_visita_cita_id on agenda.visita (cita_id);
create index ix_visita_ingreso_programado on agenda.visita (predio_id, ingreso_programado);
create index ix_registro_acceso_visita_id on agenda.registro_acceso (visita_id);
create index ix_registro_acceso_empleado_id on agenda.registro_acceso (empleado_id);
create index ix_registro_acceso_registrado_por on agenda.registro_acceso (registrado_por);
create index ix_registro_acceso_ocurrido_en on agenda.registro_acceso (predio_id, ocurrido_en);
create index ix_necesidad_formacion_tercero_id on formacion.necesidad_formacion (tercero_id);
create index ix_necesidad_formacion_competencia_id on formacion.necesidad_formacion (competencia_id);
create index ix_necesidad_formacion_curso_id on formacion.necesidad_formacion (curso_id);
create index ix_encuesta_curso_id on formacion.encuesta (curso_id);
create index ix_encuesta_sesion_id on formacion.encuesta (sesion_id);
create index ix_encuesta_tercero_id on formacion.encuesta (tercero_id);
create index ix_queja_apelacion_tercero_id on formacion.queja_apelacion (tercero_id);
create index ix_queja_apelacion_curso_id on formacion.queja_apelacion (curso_id);
create index ix_queja_apelacion_certificado_id on formacion.queja_apelacion (certificado_id);
create index ix_queja_apelacion_resuelta_por on formacion.queja_apelacion (resuelta_por);
create index ix_proyecto_iniciativa_id on proyectos.proyecto (iniciativa_id);
create index ix_proyecto_linea_negocio_id on proyectos.proyecto (linea_negocio_id);
create index ix_proyecto_patrocinador_id on proyectos.proyecto (patrocinador_id);
create index ix_proyecto_director_id on proyectos.proyecto (director_id);
create index ix_proyecto_acta_documento_id on proyectos.proyecto (acta_documento_id);
create index ix_proyecto_aprobado_por on proyectos.proyecto (aprobado_por);
create index ix_interesado_proyecto_id on proyectos.interesado (proyecto_id);
create index ix_interesado_tercero_id on proyectos.interesado (tercero_id);
create index ix_interesado_usuario_id on proyectos.interesado (usuario_id);
create index ix_elemento_edt_proyecto_id on proyectos.elemento_edt (proyecto_id);
create index ix_elemento_edt_padre_id on proyectos.elemento_edt (padre_id);
create index ix_elemento_edt_aceptado_por on proyectos.elemento_edt (aceptado_por);
create index ix_iteracion_proyecto_id on proyectos.iteracion (proyecto_id);
create index ix_actividad_proyecto_id on proyectos.actividad (proyecto_id);
create index ix_actividad_elemento_edt_id on proyectos.actividad (elemento_edt_id);
create index ix_actividad_iteracion_id on proyectos.actividad (iteracion_id);
create index ix_actividad_responsable_id on proyectos.actividad (responsable_id);
create index ix_actividad_area_id on proyectos.actividad (area_id);
create index ix_actividad_tarea_id on proyectos.actividad (tarea_id);
create index ix_dependencia_predecesora_id on proyectos.dependencia (predecesora_id);
create index ix_dependencia_sucesora_id on proyectos.dependencia (sucesora_id);
create index ix_riesgo_proyecto_id on proyectos.riesgo (proyecto_id);
create index ix_riesgo_responsable_id on proyectos.riesgo (responsable_id);
create index ix_registro_proyecto_id on proyectos.registro (proyecto_id);
create index ix_registro_responsable_id on proyectos.registro (responsable_id);
create index ix_solicitud_cambio_proyecto_id on proyectos.solicitud_cambio (proyecto_id);
create index ix_solicitud_cambio_solicitada_por on proyectos.solicitud_cambio (solicitada_por);
create index ix_solicitud_cambio_decidida_por on proyectos.solicitud_cambio (decidida_por);
create index ix_linea_base_proyecto_id on proyectos.linea_base (proyecto_id);
create index ix_linea_base_solicitud_cambio_id on proyectos.linea_base (solicitud_cambio_id);
create index ix_linea_base_aprobada_por on proyectos.linea_base (aprobada_por);
create index ix_medicion_valor_ganado_proyecto_id on proyectos.medicion_valor_ganado (proyecto_id);

-- Mantener actualizado_en
create trigger tg_usuario_actualizado before update on nucleo.usuario for each row execute function nucleo.marcar_actualizado();
create trigger tg_rol_actualizado before update on nucleo.rol for each row execute function nucleo.marcar_actualizado();
create trigger tg_permiso_actualizado before update on nucleo.permiso for each row execute function nucleo.marcar_actualizado();
create trigger tg_parametro_actualizado before update on nucleo.parametro for each row execute function nucleo.marcar_actualizado();
create trigger tg_evento_salida_actualizado before update on nucleo.evento_salida for each row execute function nucleo.marcar_actualizado();
create trigger tg_predio_actualizado before update on nucleo.predio for each row execute function nucleo.marcar_actualizado();
create trigger tg_zona_actualizado before update on nucleo.zona for each row execute function nucleo.marcar_actualizado();
create trigger tg_tercero_actualizado before update on terceros.tercero for each row execute function nucleo.marcar_actualizado();
create trigger tg_consentimiento_datos_actualizado before update on terceros.consentimiento_datos for each row execute function nucleo.marcar_actualizado();
create trigger tg_cliente_actualizado before update on terceros.cliente for each row execute function nucleo.marcar_actualizado();
create trigger tg_proveedor_actualizado before update on terceros.proveedor for each row execute function nucleo.marcar_actualizado();
create trigger tg_empleado_actualizado before update on terceros.empleado for each row execute function nucleo.marcar_actualizado();
create trigger tg_especie_actualizado before update on produccion.especie for each row execute function nucleo.marcar_actualizado();
create trigger tg_lote_animal_actualizado before update on produccion.lote_animal for each row execute function nucleo.marcar_actualizado();
create trigger tg_animal_actualizado before update on produccion.animal for each row execute function nucleo.marcar_actualizado();
create trigger tg_registro_postura_actualizado before update on produccion.registro_postura for each row execute function nucleo.marcar_actualizado();
create trigger tg_registro_alimentacion_actualizado before update on produccion.registro_alimentacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_evento_sanitario_actualizado before update on produccion.evento_sanitario for each row execute function nucleo.marcar_actualizado();
create trigger tg_registro_pesaje_actualizado before update on produccion.registro_pesaje for each row execute function nucleo.marcar_actualizado();
create trigger tg_evento_reproductivo_actualizado before update on produccion.evento_reproductivo for each row execute function nucleo.marcar_actualizado();
create trigger tg_calidad_agua_estanque_actualizado before update on produccion.calidad_agua_estanque for each row execute function nucleo.marcar_actualizado();
create trigger tg_cultivo_actualizado before update on produccion.cultivo for each row execute function nucleo.marcar_actualizado();
create trigger tg_siembra_actualizado before update on produccion.siembra for each row execute function nucleo.marcar_actualizado();
create trigger tg_labor_cultural_actualizado before update on produccion.labor_cultural for each row execute function nucleo.marcar_actualizado();
create trigger tg_cosecha_actualizado before update on produccion.cosecha for each row execute function nucleo.marcar_actualizado();
create trigger tg_analisis_suelo_actualizado before update on produccion.analisis_suelo for each row execute function nucleo.marcar_actualizado();
create trigger tg_fuente_agua_actualizado before update on riego.fuente_agua for each row execute function nucleo.marcar_actualizado();
create trigger tg_tanque_actualizado before update on riego.tanque for each row execute function nucleo.marcar_actualizado();
create trigger tg_sistema_riego_actualizado before update on riego.sistema_riego for each row execute function nucleo.marcar_actualizado();
create trigger tg_valvula_actualizado before update on riego.valvula for each row execute function nucleo.marcar_actualizado();
create trigger tg_evento_riego_actualizado before update on riego.evento_riego for each row execute function nucleo.marcar_actualizado();
create trigger tg_unidad_medida_actualizado before update on inventario.unidad_medida for each row execute function nucleo.marcar_actualizado();
create trigger tg_categoria_producto_actualizado before update on inventario.categoria_producto for each row execute function nucleo.marcar_actualizado();
create trigger tg_producto_actualizado before update on inventario.producto for each row execute function nucleo.marcar_actualizado();
create trigger tg_bodega_actualizado before update on inventario.bodega for each row execute function nucleo.marcar_actualizado();
create trigger tg_lote_inventario_actualizado before update on inventario.lote_inventario for each row execute function nucleo.marcar_actualizado();
create trigger tg_movimiento_inventario_actualizado before update on inventario.movimiento_inventario for each row execute function nucleo.marcar_actualizado();
create trigger tg_lista_precios_actualizado before update on comercial.lista_precios for each row execute function nucleo.marcar_actualizado();
create trigger tg_precio_producto_actualizado before update on comercial.precio_producto for each row execute function nucleo.marcar_actualizado();
create trigger tg_propuesta_precio_actualizado before update on comercial.propuesta_precio for each row execute function nucleo.marcar_actualizado();
create trigger tg_pedido_actualizado before update on comercial.pedido for each row execute function nucleo.marcar_actualizado();
create trigger tg_pedido_detalle_actualizado before update on comercial.pedido_detalle for each row execute function nucleo.marcar_actualizado();
create trigger tg_factura_actualizado before update on comercial.factura for each row execute function nucleo.marcar_actualizado();
create trigger tg_pago_actualizado before update on comercial.pago for each row execute function nucleo.marcar_actualizado();
create trigger tg_entrega_actualizado before update on comercial.entrega for each row execute function nucleo.marcar_actualizado();
create trigger tg_orden_compra_actualizado before update on compras.orden_compra for each row execute function nucleo.marcar_actualizado();
create trigger tg_orden_compra_detalle_actualizado before update on compras.orden_compra_detalle for each row execute function nucleo.marcar_actualizado();
create trigger tg_cotizacion_proveedor_actualizado before update on compras.cotizacion_proveedor for each row execute function nucleo.marcar_actualizado();
create trigger tg_precio_mercado_actualizado before update on compras.precio_mercado for each row execute function nucleo.marcar_actualizado();
create trigger tg_cuenta_contable_actualizado before update on finanzas.cuenta_contable for each row execute function nucleo.marcar_actualizado();
create trigger tg_centro_costo_actualizado before update on finanzas.centro_costo for each row execute function nucleo.marcar_actualizado();
create trigger tg_comprobante_actualizado before update on finanzas.comprobante for each row execute function nucleo.marcar_actualizado();
create trigger tg_movimiento_contable_actualizado before update on finanzas.movimiento_contable for each row execute function nucleo.marcar_actualizado();
create trigger tg_agente_actualizado before update on ia.agente for each row execute function nucleo.marcar_actualizado();
create trigger tg_herramienta_actualizado before update on ia.herramienta for each row execute function nucleo.marcar_actualizado();
create trigger tg_solicitud_aprobacion_actualizado before update on ia.solicitud_aprobacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_documento_conocimiento_actualizado before update on ia.documento_conocimiento for each row execute function nucleo.marcar_actualizado();
create trigger tg_fragmento_conocimiento_actualizado before update on ia.fragmento_conocimiento for each row execute function nucleo.marcar_actualizado();
create trigger tg_recomendacion_actualizado before update on ia.recomendacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_evaluacion_respuesta_actualizado before update on ia.evaluacion_respuesta for each row execute function nucleo.marcar_actualizado();
create trigger tg_consumo_ia_actualizado before update on ia.consumo_ia for each row execute function nucleo.marcar_actualizado();
create trigger tg_cuenta_red_actualizado before update on redes.cuenta_red for each row execute function nucleo.marcar_actualizado();
create trigger tg_publicacion_actualizado before update on redes.publicacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_alojamiento_actualizado before update on turismo.alojamiento for each row execute function nucleo.marcar_actualizado();
create trigger tg_plan_turistico_actualizado before update on turismo.plan_turistico for each row execute function nucleo.marcar_actualizado();
create trigger tg_reserva_actualizado before update on turismo.reserva for each row execute function nucleo.marcar_actualizado();
create trigger tg_dispositivo_actualizado before update on iot.dispositivo for each row execute function nucleo.marcar_actualizado();
create trigger tg_sensor_actualizado before update on iot.sensor for each row execute function nucleo.marcar_actualizado();
create trigger tg_actuador_actualizado before update on iot.actuador for each row execute function nucleo.marcar_actualizado();
create trigger tg_regla_automatizacion_actualizado before update on iot.regla_automatizacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_comando_actuador_actualizado before update on iot.comando_actuador for each row execute function nucleo.marcar_actualizado();
create trigger tg_dispositivo_captura_actualizado before update on nucleo.dispositivo_captura for each row execute function nucleo.marcar_actualizado();
create trigger tg_sincronizacion_actualizado before update on nucleo.sincronizacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_etiqueta_actualizado before update on inventario.etiqueta for each row execute function nucleo.marcar_actualizado();
create trigger tg_lectura_codigo_actualizado before update on inventario.lectura_codigo for each row execute function nucleo.marcar_actualizado();
create trigger tg_pesaje_actualizado before update on inventario.pesaje for each row execute function nucleo.marcar_actualizado();
create trigger tg_conteo_fisico_actualizado before update on inventario.conteo_fisico for each row execute function nucleo.marcar_actualizado();
create trigger tg_conteo_detalle_actualizado before update on inventario.conteo_detalle for each row execute function nucleo.marcar_actualizado();
create trigger tg_reserva_lote_actualizado before update on comercial.reserva_lote for each row execute function nucleo.marcar_actualizado();
create trigger tg_periodo_contable_actualizado before update on finanzas.periodo_contable for each row execute function nucleo.marcar_actualizado();
create trigger tg_politica_canal_actualizado before update on redes.politica_canal for each row execute function nucleo.marcar_actualizado();
create trigger tg_plantilla_mensaje_actualizado before update on redes.plantilla_mensaje for each row execute function nucleo.marcar_actualizado();
create trigger tg_mensaje_saliente_actualizado before update on redes.mensaje_saliente for each row execute function nucleo.marcar_actualizado();
create trigger tg_regla_conversacion_actualizado before update on ia.regla_conversacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_escalamiento_actualizado before update on ia.escalamiento for each row execute function nucleo.marcar_actualizado();
create trigger tg_funcionalidad_actualizado before update on nucleo.funcionalidad for each row execute function nucleo.marcar_actualizado();
create trigger tg_nota_voz_actualizado before update on nucleo.nota_voz for each row execute function nucleo.marcar_actualizado();
create trigger tg_categoria_huevo_actualizado before update on produccion.categoria_huevo for each row execute function nucleo.marcar_actualizado();
create trigger tg_clasificacion_postura_actualizado before update on produccion.clasificacion_postura for each row execute function nucleo.marcar_actualizado();
create trigger tg_registro_bioseguridad_actualizado before update on produccion.registro_bioseguridad for each row execute function nucleo.marcar_actualizado();
create trigger tg_produccion_abono_actualizado before update on produccion.produccion_abono for each row execute function nucleo.marcar_actualizado();
create trigger tg_vehiculo_actualizado before update on inventario.vehiculo for each row execute function nucleo.marcar_actualizado();
create trigger tg_excursion_temperatura_actualizado before update on inventario.excursion_temperatura for each row execute function nucleo.marcar_actualizado();
create trigger tg_bloqueo_lote_actualizado before update on inventario.bloqueo_lote for each row execute function nucleo.marcar_actualizado();
create trigger tg_retiro_lote_actualizado before update on comercial.retiro_lote for each row execute function nucleo.marcar_actualizado();
create trigger tg_retiro_aviso_actualizado before update on comercial.retiro_aviso for each row execute function nucleo.marcar_actualizado();
create trigger tg_pedido_recurrente_actualizado before update on comercial.pedido_recurrente for each row execute function nucleo.marcar_actualizado();
create trigger tg_pedido_recurrente_detalle_actualizado before update on comercial.pedido_recurrente_detalle for each row execute function nucleo.marcar_actualizado();
create trigger tg_permuta_actualizado before update on comercial.permuta for each row execute function nucleo.marcar_actualizado();
create trigger tg_documento_soporte_actualizado before update on compras.documento_soporte for each row execute function nucleo.marcar_actualizado();
create trigger tg_modelo_pronostico_actualizado before update on ia.modelo_pronostico for each row execute function nucleo.marcar_actualizado();
create trigger tg_pronostico_demanda_actualizado before update on ia.pronostico_demanda for each row execute function nucleo.marcar_actualizado();
create trigger tg_pieza_audiovisual_actualizado before update on redes.pieza_audiovisual for each row execute function nucleo.marcar_actualizado();
create trigger tg_bloqueo_calendario_actualizado before update on turismo.bloqueo_calendario for each row execute function nucleo.marcar_actualizado();
create trigger tg_zona_seguridad_actualizado before update on iot.zona_seguridad for each row execute function nucleo.marcar_actualizado();
create trigger tg_credencial_acceso_actualizado before update on iot.credencial_acceso for each row execute function nucleo.marcar_actualizado();
create trigger tg_camara_actualizado before update on iot.camara for each row execute function nucleo.marcar_actualizado();
create trigger tg_evento_seguridad_actualizado before update on iot.evento_seguridad for each row execute function nucleo.marcar_actualizado();
create trigger tg_clip_video_actualizado before update on iot.clip_video for each row execute function nucleo.marcar_actualizado();
create trigger tg_factor_emision_actualizado before update on ambiental.factor_emision for each row execute function nucleo.marcar_actualizado();
create trigger tg_registro_ambiental_actualizado before update on ambiental.registro_ambiental for each row execute function nucleo.marcar_actualizado();
create trigger tg_cuadrilla_actualizado before update on personal.cuadrilla for each row execute function nucleo.marcar_actualizado();
create trigger tg_cuadrilla_miembro_actualizado before update on personal.cuadrilla_miembro for each row execute function nucleo.marcar_actualizado();
create trigger tg_turno_actualizado before update on personal.turno for each row execute function nucleo.marcar_actualizado();
create trigger tg_ausencia_actualizado before update on personal.ausencia for each row execute function nucleo.marcar_actualizado();
create trigger tg_plantilla_tarea_actualizado before update on personal.plantilla_tarea for each row execute function nucleo.marcar_actualizado();
create trigger tg_tarea_actualizado before update on personal.tarea for each row execute function nucleo.marcar_actualizado();
create trigger tg_paso_tarea_actualizado before update on personal.paso_tarea for each row execute function nucleo.marcar_actualizado();
create trigger tg_evidencia_tarea_actualizado before update on personal.evidencia_tarea for each row execute function nucleo.marcar_actualizado();
create trigger tg_matriz_responsabilidad_actualizado before update on personal.matriz_responsabilidad for each row execute function nucleo.marcar_actualizado();
create trigger tg_asignacion_equipo_actualizado before update on personal.asignacion_equipo for each row execute function nucleo.marcar_actualizado();
create trigger tg_credencial_trabajo_actualizado before update on personal.credencial_trabajo for each row execute function nucleo.marcar_actualizado();
create trigger tg_jornada_actualizado before update on personal.jornada for each row execute function nucleo.marcar_actualizado();
create trigger tg_concepto_nomina_actualizado before update on nomina.concepto_nomina for each row execute function nucleo.marcar_actualizado();
create trigger tg_periodo_nomina_actualizado before update on nomina.periodo_nomina for each row execute function nucleo.marcar_actualizado();
create trigger tg_novedad_actualizado before update on nomina.novedad for each row execute function nucleo.marcar_actualizado();
create trigger tg_liquidacion_actualizado before update on nomina.liquidacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_liquidacion_detalle_actualizado before update on nomina.liquidacion_detalle for each row execute function nucleo.marcar_actualizado();
create trigger tg_provision_prestacion_actualizado before update on nomina.provision_prestacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_documento_nomina_electronica_actualizado before update on nomina.documento_nomina_electronica for each row execute function nucleo.marcar_actualizado();
create trigger tg_planilla_pila_actualizado before update on nomina.planilla_pila for each row execute function nucleo.marcar_actualizado();
create trigger tg_pago_nomina_actualizado before update on nomina.pago_nomina for each row execute function nucleo.marcar_actualizado();
create trigger tg_exportacion_nomina_actualizado before update on nomina.exportacion_nomina for each row execute function nucleo.marcar_actualizado();
create trigger tg_competencia_actualizado before update on formacion.competencia for each row execute function nucleo.marcar_actualizado();
create trigger tg_curso_actualizado before update on formacion.curso for each row execute function nucleo.marcar_actualizado();
create trigger tg_leccion_actualizado before update on formacion.leccion for each row execute function nucleo.marcar_actualizado();
create trigger tg_evaluacion_actualizado before update on formacion.evaluacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_pregunta_actualizado before update on formacion.pregunta for each row execute function nucleo.marcar_actualizado();
create trigger tg_inscripcion_actualizado before update on formacion.inscripcion for each row execute function nucleo.marcar_actualizado();
create trigger tg_progreso_actualizado before update on formacion.progreso for each row execute function nucleo.marcar_actualizado();
create trigger tg_sesion_presencial_actualizado before update on formacion.sesion_presencial for each row execute function nucleo.marcar_actualizado();
create trigger tg_asistencia_actualizado before update on formacion.asistencia for each row execute function nucleo.marcar_actualizado();
create trigger tg_certificado_actualizado before update on formacion.certificado for each row execute function nucleo.marcar_actualizado();
create trigger tg_habilitacion_actualizado before update on formacion.habilitacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_activo_actualizado before update on activos.activo for each row execute function nucleo.marcar_actualizado();
create trigger tg_plan_mantenimiento_actualizado before update on activos.plan_mantenimiento for each row execute function nucleo.marcar_actualizado();
create trigger tg_orden_trabajo_actualizado before update on activos.orden_trabajo for each row execute function nucleo.marcar_actualizado();
create trigger tg_repuesto_orden_actualizado before update on activos.repuesto_orden for each row execute function nucleo.marcar_actualizado();
create trigger tg_uso_activo_actualizado before update on activos.uso_activo for each row execute function nucleo.marcar_actualizado();
create trigger tg_depreciacion_actualizado before update on activos.depreciacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_documento_actualizado before update on documental.documento for each row execute function nucleo.marcar_actualizado();
create trigger tg_version_documento_actualizado before update on documental.version_documento for each row execute function nucleo.marcar_actualizado();
create trigger tg_vinculo_documento_actualizado before update on documental.vinculo_documento for each row execute function nucleo.marcar_actualizado();
create trigger tg_norma_actualizado before update on cumplimiento.norma for each row execute function nucleo.marcar_actualizado();
create trigger tg_requisito_actualizado before update on cumplimiento.requisito for each row execute function nucleo.marcar_actualizado();
create trigger tg_expediente_actualizado before update on cumplimiento.expediente for each row execute function nucleo.marcar_actualizado();
create trigger tg_evaluacion_requisito_actualizado before update on cumplimiento.evaluacion_requisito for each row execute function nucleo.marcar_actualizado();
create trigger tg_evidencia_requisito_actualizado before update on cumplimiento.evidencia_requisito for each row execute function nucleo.marcar_actualizado();
create trigger tg_auditoria_externa_actualizado before update on cumplimiento.auditoria_externa for each row execute function nucleo.marcar_actualizado();
create trigger tg_no_conformidad_actualizado before update on cumplimiento.no_conformidad for each row execute function nucleo.marcar_actualizado();
create trigger tg_accion_correctiva_actualizado before update on cumplimiento.accion_correctiva for each row execute function nucleo.marcar_actualizado();
create trigger tg_poliza_actualizado before update on seguros.poliza for each row execute function nucleo.marcar_actualizado();
create trigger tg_bien_asegurado_actualizado before update on seguros.bien_asegurado for each row execute function nucleo.marcar_actualizado();
create trigger tg_indice_poliza_actualizado before update on seguros.indice_poliza for each row execute function nucleo.marcar_actualizado();
create trigger tg_aviso_siniestro_actualizado before update on seguros.aviso_siniestro for each row execute function nucleo.marcar_actualizado();
create trigger tg_diagnostico_imagen_actualizado before update on ia.diagnostico_imagen for each row execute function nucleo.marcar_actualizado();
create trigger tg_escenario_actualizado before update on ia.escenario for each row execute function nucleo.marcar_actualizado();
create trigger tg_decision_actualizado before update on ia.decision for each row execute function nucleo.marcar_actualizado();
create trigger tg_clasificacion_costo_actualizado before update on finanzas.clasificacion_costo for each row execute function nucleo.marcar_actualizado();
create trigger tg_actividad_costo_actualizado before update on finanzas.actividad_costo for each row execute function nucleo.marcar_actualizado();
create trigger tg_asignacion_costo_actualizado before update on finanzas.asignacion_costo for each row execute function nucleo.marcar_actualizado();
create trigger tg_costo_estandar_actualizado before update on finanzas.costo_estandar for each row execute function nucleo.marcar_actualizado();
create trigger tg_presupuesto_actualizado before update on finanzas.presupuesto for each row execute function nucleo.marcar_actualizado();
create trigger tg_premisa_presupuesto_actualizado before update on finanzas.premisa_presupuesto for each row execute function nucleo.marcar_actualizado();
create trigger tg_presupuesto_detalle_actualizado before update on finanzas.presupuesto_detalle for each row execute function nucleo.marcar_actualizado();
create trigger tg_estado_financiero_actualizado before update on finanzas.estado_financiero for each row execute function nucleo.marcar_actualizado();
create trigger tg_indicador_actualizado before update on finanzas.indicador for each row execute function nucleo.marcar_actualizado();
create trigger tg_valor_indicador_actualizado before update on finanzas.valor_indicador for each row execute function nucleo.marcar_actualizado();
create trigger tg_anticipo_proveedor_actualizado before update on finanzas.anticipo_proveedor for each row execute function nucleo.marcar_actualizado();
create trigger tg_aplicacion_anticipo_actualizado before update on finanzas.aplicacion_anticipo for each row execute function nucleo.marcar_actualizado();
create trigger tg_reporte_indicadores_actualizado before update on finanzas.reporte_indicadores for each row execute function nucleo.marcar_actualizado();
create trigger tg_mision_robot_actualizado before update on iot.mision_robot for each row execute function nucleo.marcar_actualizado();
create trigger tg_prioridad_carga_actualizado before update on iot.prioridad_carga for each row execute function nucleo.marcar_actualizado();
create trigger tg_llave_api_actualizado before update on nucleo.llave_api for each row execute function nucleo.marcar_actualizado();
create trigger tg_webhook_suscripcion_actualizado before update on nucleo.webhook_suscripcion for each row execute function nucleo.marcar_actualizado();
create trigger tg_webhook_entrega_actualizado before update on nucleo.webhook_entrega for each row execute function nucleo.marcar_actualizado();
create trigger tg_factor_autenticacion_actualizado before update on seguridad.factor_autenticacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_sesion_usuario_actualizado before update on seguridad.sesion_usuario for each row execute function nucleo.marcar_actualizado();
create trigger tg_regla_deteccion_actualizado before update on seguridad.regla_deteccion for each row execute function nucleo.marcar_actualizado();
create trigger tg_bloqueo_actualizado before update on seguridad.bloqueo for each row execute function nucleo.marcar_actualizado();
create trigger tg_senuelo_actualizado before update on seguridad.senuelo for each row execute function nucleo.marcar_actualizado();
create trigger tg_alerta_seguridad_actualizado before update on seguridad.alerta_seguridad for each row execute function nucleo.marcar_actualizado();
create trigger tg_incidente_actualizado before update on seguridad.incidente for each row execute function nucleo.marcar_actualizado();
create trigger tg_ejecucion_prueba_actualizado before update on seguridad.ejecucion_prueba for each row execute function nucleo.marcar_actualizado();
create trigger tg_copia_seguridad_actualizado before update on seguridad.copia_seguridad for each row execute function nucleo.marcar_actualizado();
create trigger tg_segmento_actualizado before update on crm.segmento for each row execute function nucleo.marcar_actualizado();
create trigger tg_campana_actualizado before update on crm.campana for each row execute function nucleo.marcar_actualizado();
create trigger tg_formulario_captura_actualizado before update on crm.formulario_captura for each row execute function nucleo.marcar_actualizado();
create trigger tg_prospecto_actualizado before update on crm.prospecto for each row execute function nucleo.marcar_actualizado();
create trigger tg_contacto_empresa_actualizado before update on crm.contacto_empresa for each row execute function nucleo.marcar_actualizado();
create trigger tg_interaccion_actualizado before update on crm.interaccion for each row execute function nucleo.marcar_actualizado();
create trigger tg_oportunidad_actualizado before update on crm.oportunidad for each row execute function nucleo.marcar_actualizado();
create trigger tg_linea_negocio_actualizado before update on estrategia.linea_negocio for each row execute function nucleo.marcar_actualizado();
create trigger tg_factor_dofa_actualizado before update on estrategia.factor_dofa for each row execute function nucleo.marcar_actualizado();
create trigger tg_estudio_mercado_actualizado before update on estrategia.estudio_mercado for each row execute function nucleo.marcar_actualizado();
create trigger tg_iniciativa_actualizado before update on estrategia.iniciativa for each row execute function nucleo.marcar_actualizado();
create trigger tg_evaluacion_proyecto_actualizado before update on estrategia.evaluacion_proyecto for each row execute function nucleo.marcar_actualizado();
create trigger tg_flujo_proyecto_actualizado before update on estrategia.flujo_proyecto for each row execute function nucleo.marcar_actualizado();
create trigger tg_reinversion_actualizado before update on estrategia.reinversion for each row execute function nucleo.marcar_actualizado();
create trigger tg_seguimiento_iniciativa_actualizado before update on estrategia.seguimiento_iniciativa for each row execute function nucleo.marcar_actualizado();
create trigger tg_objetivo_actualizado before update on estrategia.objetivo for each row execute function nucleo.marcar_actualizado();
create trigger tg_area_responsabilidad_actualizado before update on personal.area_responsabilidad for each row execute function nucleo.marcar_actualizado();
create trigger tg_miembro_area_actualizado before update on personal.miembro_area for each row execute function nucleo.marcar_actualizado();
create trigger tg_patron_turno_actualizado before update on personal.patron_turno for each row execute function nucleo.marcar_actualizado();
create trigger tg_patron_turno_detalle_actualizado before update on personal.patron_turno_detalle for each row execute function nucleo.marcar_actualizado();
create trigger tg_cronograma_actualizado before update on personal.cronograma for each row execute function nucleo.marcar_actualizado();
create trigger tg_asignacion_patron_actualizado before update on personal.asignacion_patron for each row execute function nucleo.marcar_actualizado();
create trigger tg_requerimiento_cobertura_actualizado before update on personal.requerimiento_cobertura for each row execute function nucleo.marcar_actualizado();
create trigger tg_disponibilidad_actualizado before update on personal.disponibilidad for each row execute function nucleo.marcar_actualizado();
create trigger tg_recurso_actualizado before update on agenda.recurso for each row execute function nucleo.marcar_actualizado();
create trigger tg_cita_actualizado before update on agenda.cita for each row execute function nucleo.marcar_actualizado();
create trigger tg_visita_actualizado before update on agenda.visita for each row execute function nucleo.marcar_actualizado();
create trigger tg_registro_acceso_actualizado before update on agenda.registro_acceso for each row execute function nucleo.marcar_actualizado();
create trigger tg_necesidad_formacion_actualizado before update on formacion.necesidad_formacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_encuesta_actualizado before update on formacion.encuesta for each row execute function nucleo.marcar_actualizado();
create trigger tg_queja_apelacion_actualizado before update on formacion.queja_apelacion for each row execute function nucleo.marcar_actualizado();
create trigger tg_proyecto_actualizado before update on proyectos.proyecto for each row execute function nucleo.marcar_actualizado();
create trigger tg_interesado_actualizado before update on proyectos.interesado for each row execute function nucleo.marcar_actualizado();
create trigger tg_elemento_edt_actualizado before update on proyectos.elemento_edt for each row execute function nucleo.marcar_actualizado();
create trigger tg_iteracion_actualizado before update on proyectos.iteracion for each row execute function nucleo.marcar_actualizado();
create trigger tg_actividad_actualizado before update on proyectos.actividad for each row execute function nucleo.marcar_actualizado();
create trigger tg_dependencia_actualizado before update on proyectos.dependencia for each row execute function nucleo.marcar_actualizado();
create trigger tg_riesgo_actualizado before update on proyectos.riesgo for each row execute function nucleo.marcar_actualizado();
create trigger tg_registro_actualizado before update on proyectos.registro for each row execute function nucleo.marcar_actualizado();
create trigger tg_solicitud_cambio_actualizado before update on proyectos.solicitud_cambio for each row execute function nucleo.marcar_actualizado();
create trigger tg_linea_base_actualizado before update on proyectos.linea_base for each row execute function nucleo.marcar_actualizado();
create trigger tg_medicion_valor_ganado_actualizado before update on proyectos.medicion_valor_ganado for each row execute function nucleo.marcar_actualizado();

-- Seguridad por filas (RLS): cada finca solo ve lo suyo
alter table nucleo.usuario_rol enable row level security;
alter table nucleo.usuario_rol force row level security;
create policy aislamiento_predio on nucleo.usuario_rol using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.parametro enable row level security;
alter table nucleo.parametro force row level security;
create policy leer_parametro on nucleo.parametro for select using (predio_id is null or predio_id = nucleo.predio_actual());
create policy escribir_parametro on nucleo.parametro for all using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.auditoria enable row level security;
alter table nucleo.auditoria force row level security;
create policy leer_auditoria on nucleo.auditoria for select using (predio_id = nucleo.predio_actual());
create policy registrar_auditoria on nucleo.auditoria for insert with check (true);

alter table nucleo.evento_salida enable row level security;
alter table nucleo.evento_salida force row level security;
create policy aislamiento_predio on nucleo.evento_salida using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.predio enable row level security;
alter table nucleo.predio force row level security;
create policy ver_predio_actual on nucleo.predio using (id = nucleo.predio_actual());

alter table nucleo.zona enable row level security;
alter table nucleo.zona force row level security;
create policy aislamiento_predio on nucleo.zona using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table terceros.tercero enable row level security;
alter table terceros.tercero force row level security;
create policy aislamiento_predio on terceros.tercero using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table terceros.consentimiento_datos enable row level security;
alter table terceros.consentimiento_datos force row level security;
create policy aislamiento_predio on terceros.consentimiento_datos using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table terceros.cliente enable row level security;
alter table terceros.cliente force row level security;
create policy aislamiento_predio on terceros.cliente using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table terceros.proveedor enable row level security;
alter table terceros.proveedor force row level security;
create policy aislamiento_predio on terceros.proveedor using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table terceros.empleado enable row level security;
alter table terceros.empleado force row level security;
create policy aislamiento_predio on terceros.empleado using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.lote_animal enable row level security;
alter table produccion.lote_animal force row level security;
create policy aislamiento_predio on produccion.lote_animal using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.animal enable row level security;
alter table produccion.animal force row level security;
create policy aislamiento_predio on produccion.animal using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.registro_postura enable row level security;
alter table produccion.registro_postura force row level security;
create policy aislamiento_predio on produccion.registro_postura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.registro_alimentacion enable row level security;
alter table produccion.registro_alimentacion force row level security;
create policy aislamiento_predio on produccion.registro_alimentacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.evento_sanitario enable row level security;
alter table produccion.evento_sanitario force row level security;
create policy aislamiento_predio on produccion.evento_sanitario using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.registro_pesaje enable row level security;
alter table produccion.registro_pesaje force row level security;
create policy aislamiento_predio on produccion.registro_pesaje using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.evento_reproductivo enable row level security;
alter table produccion.evento_reproductivo force row level security;
create policy aislamiento_predio on produccion.evento_reproductivo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.calidad_agua_estanque enable row level security;
alter table produccion.calidad_agua_estanque force row level security;
create policy aislamiento_predio on produccion.calidad_agua_estanque using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.siembra enable row level security;
alter table produccion.siembra force row level security;
create policy aislamiento_predio on produccion.siembra using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.labor_cultural enable row level security;
alter table produccion.labor_cultural force row level security;
create policy aislamiento_predio on produccion.labor_cultural using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.cosecha enable row level security;
alter table produccion.cosecha force row level security;
create policy aislamiento_predio on produccion.cosecha using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.analisis_suelo enable row level security;
alter table produccion.analisis_suelo force row level security;
create policy aislamiento_predio on produccion.analisis_suelo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table riego.fuente_agua enable row level security;
alter table riego.fuente_agua force row level security;
create policy aislamiento_predio on riego.fuente_agua using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table riego.tanque enable row level security;
alter table riego.tanque force row level security;
create policy aislamiento_predio on riego.tanque using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table riego.sistema_riego enable row level security;
alter table riego.sistema_riego force row level security;
create policy aislamiento_predio on riego.sistema_riego using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table riego.valvula enable row level security;
alter table riego.valvula force row level security;
create policy aislamiento_predio on riego.valvula using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table riego.evento_riego enable row level security;
alter table riego.evento_riego force row level security;
create policy aislamiento_predio on riego.evento_riego using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.producto enable row level security;
alter table inventario.producto force row level security;
create policy aislamiento_predio on inventario.producto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.bodega enable row level security;
alter table inventario.bodega force row level security;
create policy aislamiento_predio on inventario.bodega using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.lote_inventario enable row level security;
alter table inventario.lote_inventario force row level security;
create policy aislamiento_predio on inventario.lote_inventario using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.movimiento_inventario enable row level security;
alter table inventario.movimiento_inventario force row level security;
create policy aislamiento_predio on inventario.movimiento_inventario using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.lista_precios enable row level security;
alter table comercial.lista_precios force row level security;
create policy aislamiento_predio on comercial.lista_precios using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.precio_producto enable row level security;
alter table comercial.precio_producto force row level security;
create policy aislamiento_predio on comercial.precio_producto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.propuesta_precio enable row level security;
alter table comercial.propuesta_precio force row level security;
create policy aislamiento_predio on comercial.propuesta_precio using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.pedido enable row level security;
alter table comercial.pedido force row level security;
create policy aislamiento_predio on comercial.pedido using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.pedido_detalle enable row level security;
alter table comercial.pedido_detalle force row level security;
create policy aislamiento_predio on comercial.pedido_detalle using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.factura enable row level security;
alter table comercial.factura force row level security;
create policy aislamiento_predio on comercial.factura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.pago enable row level security;
alter table comercial.pago force row level security;
create policy aislamiento_predio on comercial.pago using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.entrega enable row level security;
alter table comercial.entrega force row level security;
create policy aislamiento_predio on comercial.entrega using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table compras.orden_compra enable row level security;
alter table compras.orden_compra force row level security;
create policy aislamiento_predio on compras.orden_compra using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table compras.orden_compra_detalle enable row level security;
alter table compras.orden_compra_detalle force row level security;
create policy aislamiento_predio on compras.orden_compra_detalle using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table compras.cotizacion_proveedor enable row level security;
alter table compras.cotizacion_proveedor force row level security;
create policy aislamiento_predio on compras.cotizacion_proveedor using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table compras.precio_mercado enable row level security;
alter table compras.precio_mercado force row level security;
create policy aislamiento_predio on compras.precio_mercado using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.centro_costo enable row level security;
alter table finanzas.centro_costo force row level security;
create policy aislamiento_predio on finanzas.centro_costo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.comprobante enable row level security;
alter table finanzas.comprobante force row level security;
create policy aislamiento_predio on finanzas.comprobante using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.movimiento_contable enable row level security;
alter table finanzas.movimiento_contable force row level security;
create policy aislamiento_predio on finanzas.movimiento_contable using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.agente enable row level security;
alter table ia.agente force row level security;
create policy aislamiento_predio on ia.agente using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.agente_herramienta enable row level security;
alter table ia.agente_herramienta force row level security;
create policy aislamiento_predio on ia.agente_herramienta using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.solicitud_aprobacion enable row level security;
alter table ia.solicitud_aprobacion force row level security;
create policy aislamiento_predio on ia.solicitud_aprobacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.documento_conocimiento enable row level security;
alter table ia.documento_conocimiento force row level security;
create policy aislamiento_predio on ia.documento_conocimiento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.fragmento_conocimiento enable row level security;
alter table ia.fragmento_conocimiento force row level security;
create policy aislamiento_predio on ia.fragmento_conocimiento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.recomendacion enable row level security;
alter table ia.recomendacion force row level security;
create policy aislamiento_predio on ia.recomendacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.evaluacion_respuesta enable row level security;
alter table ia.evaluacion_respuesta force row level security;
create policy aislamiento_predio on ia.evaluacion_respuesta using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.consumo_ia enable row level security;
alter table ia.consumo_ia force row level security;
create policy aislamiento_predio on ia.consumo_ia using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table redes.cuenta_red enable row level security;
alter table redes.cuenta_red force row level security;
create policy aislamiento_predio on redes.cuenta_red using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table redes.publicacion enable row level security;
alter table redes.publicacion force row level security;
create policy aislamiento_predio on redes.publicacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table turismo.alojamiento enable row level security;
alter table turismo.alojamiento force row level security;
create policy aislamiento_predio on turismo.alojamiento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table turismo.plan_turistico enable row level security;
alter table turismo.plan_turistico force row level security;
create policy aislamiento_predio on turismo.plan_turistico using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table turismo.reserva enable row level security;
alter table turismo.reserva force row level security;
create policy aislamiento_predio on turismo.reserva using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.dispositivo enable row level security;
alter table iot.dispositivo force row level security;
create policy aislamiento_predio on iot.dispositivo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.sensor enable row level security;
alter table iot.sensor force row level security;
create policy aislamiento_predio on iot.sensor using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.actuador enable row level security;
alter table iot.actuador force row level security;
create policy aislamiento_predio on iot.actuador using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.lectura enable row level security;
alter table iot.lectura force row level security;
create policy aislamiento_predio on iot.lectura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.regla_automatizacion enable row level security;
alter table iot.regla_automatizacion force row level security;
create policy aislamiento_predio on iot.regla_automatizacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.comando_actuador enable row level security;
alter table iot.comando_actuador force row level security;
create policy aislamiento_predio on iot.comando_actuador using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.dispositivo_captura enable row level security;
alter table nucleo.dispositivo_captura force row level security;
create policy aislamiento_predio on nucleo.dispositivo_captura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.sincronizacion enable row level security;
alter table nucleo.sincronizacion force row level security;
create policy aislamiento_predio on nucleo.sincronizacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.etiqueta enable row level security;
alter table inventario.etiqueta force row level security;
create policy aislamiento_predio on inventario.etiqueta using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.lectura_codigo enable row level security;
alter table inventario.lectura_codigo force row level security;
create policy aislamiento_predio on inventario.lectura_codigo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.pesaje enable row level security;
alter table inventario.pesaje force row level security;
create policy aislamiento_predio on inventario.pesaje using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.conteo_fisico enable row level security;
alter table inventario.conteo_fisico force row level security;
create policy aislamiento_predio on inventario.conteo_fisico using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.conteo_detalle enable row level security;
alter table inventario.conteo_detalle force row level security;
create policy aislamiento_predio on inventario.conteo_detalle using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.reserva_lote enable row level security;
alter table comercial.reserva_lote force row level security;
create policy aislamiento_predio on comercial.reserva_lote using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.periodo_contable enable row level security;
alter table finanzas.periodo_contable force row level security;
create policy aislamiento_predio on finanzas.periodo_contable using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table redes.plantilla_mensaje enable row level security;
alter table redes.plantilla_mensaje force row level security;
create policy aislamiento_predio on redes.plantilla_mensaje using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table redes.mensaje_saliente enable row level security;
alter table redes.mensaje_saliente force row level security;
create policy aislamiento_predio on redes.mensaje_saliente using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.regla_conversacion enable row level security;
alter table ia.regla_conversacion force row level security;
create policy aislamiento_predio on ia.regla_conversacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.escalamiento enable row level security;
alter table ia.escalamiento force row level security;
create policy aislamiento_predio on ia.escalamiento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.funcionalidad enable row level security;
alter table nucleo.funcionalidad force row level security;
create policy aislamiento_predio on nucleo.funcionalidad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.nota_voz enable row level security;
alter table nucleo.nota_voz force row level security;
create policy aislamiento_predio on nucleo.nota_voz using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.clasificacion_postura enable row level security;
alter table produccion.clasificacion_postura force row level security;
create policy aislamiento_predio on produccion.clasificacion_postura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.registro_bioseguridad enable row level security;
alter table produccion.registro_bioseguridad force row level security;
create policy aislamiento_predio on produccion.registro_bioseguridad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table produccion.produccion_abono enable row level security;
alter table produccion.produccion_abono force row level security;
create policy aislamiento_predio on produccion.produccion_abono using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.vehiculo enable row level security;
alter table inventario.vehiculo force row level security;
create policy aislamiento_predio on inventario.vehiculo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.excursion_temperatura enable row level security;
alter table inventario.excursion_temperatura force row level security;
create policy aislamiento_predio on inventario.excursion_temperatura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table inventario.bloqueo_lote enable row level security;
alter table inventario.bloqueo_lote force row level security;
create policy aislamiento_predio on inventario.bloqueo_lote using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.retiro_lote enable row level security;
alter table comercial.retiro_lote force row level security;
create policy aislamiento_predio on comercial.retiro_lote using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.retiro_aviso enable row level security;
alter table comercial.retiro_aviso force row level security;
create policy aislamiento_predio on comercial.retiro_aviso using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.pedido_recurrente enable row level security;
alter table comercial.pedido_recurrente force row level security;
create policy aislamiento_predio on comercial.pedido_recurrente using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.pedido_recurrente_detalle enable row level security;
alter table comercial.pedido_recurrente_detalle force row level security;
create policy aislamiento_predio on comercial.pedido_recurrente_detalle using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.permuta enable row level security;
alter table comercial.permuta force row level security;
create policy aislamiento_predio on comercial.permuta using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table comercial.huella_trazabilidad enable row level security;
alter table comercial.huella_trazabilidad force row level security;
create policy aislamiento_predio on comercial.huella_trazabilidad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table compras.documento_soporte enable row level security;
alter table compras.documento_soporte force row level security;
create policy aislamiento_predio on compras.documento_soporte using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.modelo_pronostico enable row level security;
alter table ia.modelo_pronostico force row level security;
create policy aislamiento_predio on ia.modelo_pronostico using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.pronostico_demanda enable row level security;
alter table ia.pronostico_demanda force row level security;
create policy aislamiento_predio on ia.pronostico_demanda using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table redes.pieza_audiovisual enable row level security;
alter table redes.pieza_audiovisual force row level security;
create policy aislamiento_predio on redes.pieza_audiovisual using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table redes.pieza_persona enable row level security;
alter table redes.pieza_persona force row level security;
create policy aislamiento_predio on redes.pieza_persona using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table turismo.bloqueo_calendario enable row level security;
alter table turismo.bloqueo_calendario force row level security;
create policy aislamiento_predio on turismo.bloqueo_calendario using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.zona_seguridad enable row level security;
alter table iot.zona_seguridad force row level security;
create policy aislamiento_predio on iot.zona_seguridad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.cambio_estado_alarma enable row level security;
alter table iot.cambio_estado_alarma force row level security;
create policy aislamiento_predio on iot.cambio_estado_alarma using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.credencial_acceso enable row level security;
alter table iot.credencial_acceso force row level security;
create policy aislamiento_predio on iot.credencial_acceso using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.camara enable row level security;
alter table iot.camara force row level security;
create policy aislamiento_predio on iot.camara using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.evento_seguridad enable row level security;
alter table iot.evento_seguridad force row level security;
create policy aislamiento_predio on iot.evento_seguridad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.clip_video enable row level security;
alter table iot.clip_video force row level security;
create policy aislamiento_predio on iot.clip_video using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ambiental.registro_ambiental enable row level security;
alter table ambiental.registro_ambiental force row level security;
create policy aislamiento_predio on ambiental.registro_ambiental using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.cuadrilla enable row level security;
alter table personal.cuadrilla force row level security;
create policy aislamiento_predio on personal.cuadrilla using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.cuadrilla_miembro enable row level security;
alter table personal.cuadrilla_miembro force row level security;
create policy aislamiento_predio on personal.cuadrilla_miembro using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.turno enable row level security;
alter table personal.turno force row level security;
create policy aislamiento_predio on personal.turno using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.ausencia enable row level security;
alter table personal.ausencia force row level security;
create policy aislamiento_predio on personal.ausencia using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.plantilla_tarea enable row level security;
alter table personal.plantilla_tarea force row level security;
create policy aislamiento_predio on personal.plantilla_tarea using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.tarea enable row level security;
alter table personal.tarea force row level security;
create policy aislamiento_predio on personal.tarea using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.paso_tarea enable row level security;
alter table personal.paso_tarea force row level security;
create policy aislamiento_predio on personal.paso_tarea using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.evidencia_tarea enable row level security;
alter table personal.evidencia_tarea force row level security;
create policy aislamiento_predio on personal.evidencia_tarea using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.matriz_responsabilidad enable row level security;
alter table personal.matriz_responsabilidad force row level security;
create policy aislamiento_predio on personal.matriz_responsabilidad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.asignacion_equipo enable row level security;
alter table personal.asignacion_equipo force row level security;
create policy aislamiento_predio on personal.asignacion_equipo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.credencial_trabajo enable row level security;
alter table personal.credencial_trabajo force row level security;
create policy aislamiento_predio on personal.credencial_trabajo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.jornada enable row level security;
alter table personal.jornada force row level security;
create policy aislamiento_predio on personal.jornada using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.concepto_nomina enable row level security;
alter table nomina.concepto_nomina force row level security;
create policy aislamiento_predio on nomina.concepto_nomina using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.periodo_nomina enable row level security;
alter table nomina.periodo_nomina force row level security;
create policy aislamiento_predio on nomina.periodo_nomina using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.novedad enable row level security;
alter table nomina.novedad force row level security;
create policy aislamiento_predio on nomina.novedad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.liquidacion enable row level security;
alter table nomina.liquidacion force row level security;
create policy aislamiento_predio on nomina.liquidacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.liquidacion_detalle enable row level security;
alter table nomina.liquidacion_detalle force row level security;
create policy aislamiento_predio on nomina.liquidacion_detalle using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.provision_prestacion enable row level security;
alter table nomina.provision_prestacion force row level security;
create policy aislamiento_predio on nomina.provision_prestacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.documento_nomina_electronica enable row level security;
alter table nomina.documento_nomina_electronica force row level security;
create policy aislamiento_predio on nomina.documento_nomina_electronica using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.planilla_pila enable row level security;
alter table nomina.planilla_pila force row level security;
create policy aislamiento_predio on nomina.planilla_pila using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.pago_nomina enable row level security;
alter table nomina.pago_nomina force row level security;
create policy aislamiento_predio on nomina.pago_nomina using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nomina.exportacion_nomina enable row level security;
alter table nomina.exportacion_nomina force row level security;
create policy aislamiento_predio on nomina.exportacion_nomina using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.competencia enable row level security;
alter table formacion.competencia force row level security;
create policy aislamiento_predio on formacion.competencia using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.curso enable row level security;
alter table formacion.curso force row level security;
create policy aislamiento_predio on formacion.curso using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.leccion enable row level security;
alter table formacion.leccion force row level security;
create policy aislamiento_predio on formacion.leccion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.evaluacion enable row level security;
alter table formacion.evaluacion force row level security;
create policy aislamiento_predio on formacion.evaluacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.pregunta enable row level security;
alter table formacion.pregunta force row level security;
create policy aislamiento_predio on formacion.pregunta using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.inscripcion enable row level security;
alter table formacion.inscripcion force row level security;
create policy aislamiento_predio on formacion.inscripcion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.progreso enable row level security;
alter table formacion.progreso force row level security;
create policy aislamiento_predio on formacion.progreso using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.sesion_presencial enable row level security;
alter table formacion.sesion_presencial force row level security;
create policy aislamiento_predio on formacion.sesion_presencial using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.asistencia enable row level security;
alter table formacion.asistencia force row level security;
create policy aislamiento_predio on formacion.asistencia using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.certificado enable row level security;
alter table formacion.certificado force row level security;
create policy aislamiento_predio on formacion.certificado using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.habilitacion enable row level security;
alter table formacion.habilitacion force row level security;
create policy aislamiento_predio on formacion.habilitacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table activos.activo enable row level security;
alter table activos.activo force row level security;
create policy aislamiento_predio on activos.activo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table activos.plan_mantenimiento enable row level security;
alter table activos.plan_mantenimiento force row level security;
create policy aislamiento_predio on activos.plan_mantenimiento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table activos.orden_trabajo enable row level security;
alter table activos.orden_trabajo force row level security;
create policy aislamiento_predio on activos.orden_trabajo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table activos.repuesto_orden enable row level security;
alter table activos.repuesto_orden force row level security;
create policy aislamiento_predio on activos.repuesto_orden using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table activos.uso_activo enable row level security;
alter table activos.uso_activo force row level security;
create policy aislamiento_predio on activos.uso_activo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table activos.depreciacion enable row level security;
alter table activos.depreciacion force row level security;
create policy aislamiento_predio on activos.depreciacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table documental.documento enable row level security;
alter table documental.documento force row level security;
create policy aislamiento_predio on documental.documento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table documental.version_documento enable row level security;
alter table documental.version_documento force row level security;
create policy aislamiento_predio on documental.version_documento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table documental.vinculo_documento enable row level security;
alter table documental.vinculo_documento force row level security;
create policy aislamiento_predio on documental.vinculo_documento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table cumplimiento.expediente enable row level security;
alter table cumplimiento.expediente force row level security;
create policy aislamiento_predio on cumplimiento.expediente using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table cumplimiento.evaluacion_requisito enable row level security;
alter table cumplimiento.evaluacion_requisito force row level security;
create policy aislamiento_predio on cumplimiento.evaluacion_requisito using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table cumplimiento.evidencia_requisito enable row level security;
alter table cumplimiento.evidencia_requisito force row level security;
create policy aislamiento_predio on cumplimiento.evidencia_requisito using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table cumplimiento.auditoria_externa enable row level security;
alter table cumplimiento.auditoria_externa force row level security;
create policy aislamiento_predio on cumplimiento.auditoria_externa using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table cumplimiento.no_conformidad enable row level security;
alter table cumplimiento.no_conformidad force row level security;
create policy aislamiento_predio on cumplimiento.no_conformidad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table cumplimiento.accion_correctiva enable row level security;
alter table cumplimiento.accion_correctiva force row level security;
create policy aislamiento_predio on cumplimiento.accion_correctiva using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table seguros.poliza enable row level security;
alter table seguros.poliza force row level security;
create policy aislamiento_predio on seguros.poliza using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table seguros.bien_asegurado enable row level security;
alter table seguros.bien_asegurado force row level security;
create policy aislamiento_predio on seguros.bien_asegurado using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table seguros.indice_poliza enable row level security;
alter table seguros.indice_poliza force row level security;
create policy aislamiento_predio on seguros.indice_poliza using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table seguros.aviso_siniestro enable row level security;
alter table seguros.aviso_siniestro force row level security;
create policy aislamiento_predio on seguros.aviso_siniestro using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.diagnostico_imagen enable row level security;
alter table ia.diagnostico_imagen force row level security;
create policy aislamiento_predio on ia.diagnostico_imagen using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.escenario enable row level security;
alter table ia.escenario force row level security;
create policy aislamiento_predio on ia.escenario using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table ia.decision enable row level security;
alter table ia.decision force row level security;
create policy aislamiento_predio on ia.decision using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.clasificacion_costo enable row level security;
alter table finanzas.clasificacion_costo force row level security;
create policy aislamiento_predio on finanzas.clasificacion_costo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.actividad_costo enable row level security;
alter table finanzas.actividad_costo force row level security;
create policy aislamiento_predio on finanzas.actividad_costo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.asignacion_costo enable row level security;
alter table finanzas.asignacion_costo force row level security;
create policy aislamiento_predio on finanzas.asignacion_costo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.costo_estandar enable row level security;
alter table finanzas.costo_estandar force row level security;
create policy aislamiento_predio on finanzas.costo_estandar using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.presupuesto enable row level security;
alter table finanzas.presupuesto force row level security;
create policy aislamiento_predio on finanzas.presupuesto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.premisa_presupuesto enable row level security;
alter table finanzas.premisa_presupuesto force row level security;
create policy aislamiento_predio on finanzas.premisa_presupuesto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.presupuesto_detalle enable row level security;
alter table finanzas.presupuesto_detalle force row level security;
create policy aislamiento_predio on finanzas.presupuesto_detalle using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.estado_financiero enable row level security;
alter table finanzas.estado_financiero force row level security;
create policy aislamiento_predio on finanzas.estado_financiero using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.valor_indicador enable row level security;
alter table finanzas.valor_indicador force row level security;
create policy aislamiento_predio on finanzas.valor_indicador using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.anticipo_proveedor enable row level security;
alter table finanzas.anticipo_proveedor force row level security;
create policy aislamiento_predio on finanzas.anticipo_proveedor using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.aplicacion_anticipo enable row level security;
alter table finanzas.aplicacion_anticipo force row level security;
create policy aislamiento_predio on finanzas.aplicacion_anticipo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table finanzas.reporte_indicadores enable row level security;
alter table finanzas.reporte_indicadores force row level security;
create policy aislamiento_predio on finanzas.reporte_indicadores using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.mision_robot enable row level security;
alter table iot.mision_robot force row level security;
create policy aislamiento_predio on iot.mision_robot using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table iot.prioridad_carga enable row level security;
alter table iot.prioridad_carga force row level security;
create policy aislamiento_predio on iot.prioridad_carga using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.llave_api enable row level security;
alter table nucleo.llave_api force row level security;
create policy aislamiento_predio on nucleo.llave_api using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.webhook_suscripcion enable row level security;
alter table nucleo.webhook_suscripcion force row level security;
create policy aislamiento_predio on nucleo.webhook_suscripcion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table nucleo.webhook_entrega enable row level security;
alter table nucleo.webhook_entrega force row level security;
create policy aislamiento_predio on nucleo.webhook_entrega using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table crm.segmento enable row level security;
alter table crm.segmento force row level security;
create policy aislamiento_predio on crm.segmento using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table crm.campana enable row level security;
alter table crm.campana force row level security;
create policy aislamiento_predio on crm.campana using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table crm.formulario_captura enable row level security;
alter table crm.formulario_captura force row level security;
create policy aislamiento_predio on crm.formulario_captura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table crm.prospecto enable row level security;
alter table crm.prospecto force row level security;
create policy aislamiento_predio on crm.prospecto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table crm.contacto_empresa enable row level security;
alter table crm.contacto_empresa force row level security;
create policy aislamiento_predio on crm.contacto_empresa using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table crm.interaccion enable row level security;
alter table crm.interaccion force row level security;
create policy aislamiento_predio on crm.interaccion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table crm.oportunidad enable row level security;
alter table crm.oportunidad force row level security;
create policy aislamiento_predio on crm.oportunidad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.linea_negocio enable row level security;
alter table estrategia.linea_negocio force row level security;
create policy aislamiento_predio on estrategia.linea_negocio using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.factor_dofa enable row level security;
alter table estrategia.factor_dofa force row level security;
create policy aislamiento_predio on estrategia.factor_dofa using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.estudio_mercado enable row level security;
alter table estrategia.estudio_mercado force row level security;
create policy aislamiento_predio on estrategia.estudio_mercado using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.iniciativa enable row level security;
alter table estrategia.iniciativa force row level security;
create policy aislamiento_predio on estrategia.iniciativa using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.evaluacion_proyecto enable row level security;
alter table estrategia.evaluacion_proyecto force row level security;
create policy aislamiento_predio on estrategia.evaluacion_proyecto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.flujo_proyecto enable row level security;
alter table estrategia.flujo_proyecto force row level security;
create policy aislamiento_predio on estrategia.flujo_proyecto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.reinversion enable row level security;
alter table estrategia.reinversion force row level security;
create policy aislamiento_predio on estrategia.reinversion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.seguimiento_iniciativa enable row level security;
alter table estrategia.seguimiento_iniciativa force row level security;
create policy aislamiento_predio on estrategia.seguimiento_iniciativa using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table estrategia.objetivo enable row level security;
alter table estrategia.objetivo force row level security;
create policy aislamiento_predio on estrategia.objetivo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.area_responsabilidad enable row level security;
alter table personal.area_responsabilidad force row level security;
create policy aislamiento_predio on personal.area_responsabilidad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.miembro_area enable row level security;
alter table personal.miembro_area force row level security;
create policy aislamiento_predio on personal.miembro_area using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.patron_turno enable row level security;
alter table personal.patron_turno force row level security;
create policy aislamiento_predio on personal.patron_turno using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.patron_turno_detalle enable row level security;
alter table personal.patron_turno_detalle force row level security;
create policy aislamiento_predio on personal.patron_turno_detalle using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.cronograma enable row level security;
alter table personal.cronograma force row level security;
create policy aislamiento_predio on personal.cronograma using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.asignacion_patron enable row level security;
alter table personal.asignacion_patron force row level security;
create policy aislamiento_predio on personal.asignacion_patron using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.requerimiento_cobertura enable row level security;
alter table personal.requerimiento_cobertura force row level security;
create policy aislamiento_predio on personal.requerimiento_cobertura using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table personal.disponibilidad enable row level security;
alter table personal.disponibilidad force row level security;
create policy aislamiento_predio on personal.disponibilidad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table agenda.recurso enable row level security;
alter table agenda.recurso force row level security;
create policy aislamiento_predio on agenda.recurso using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table agenda.cita enable row level security;
alter table agenda.cita force row level security;
create policy aislamiento_predio on agenda.cita using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table agenda.visita enable row level security;
alter table agenda.visita force row level security;
create policy aislamiento_predio on agenda.visita using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table agenda.registro_acceso enable row level security;
alter table agenda.registro_acceso force row level security;
create policy aislamiento_predio on agenda.registro_acceso using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.necesidad_formacion enable row level security;
alter table formacion.necesidad_formacion force row level security;
create policy aislamiento_predio on formacion.necesidad_formacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.encuesta enable row level security;
alter table formacion.encuesta force row level security;
create policy aislamiento_predio on formacion.encuesta using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table formacion.queja_apelacion enable row level security;
alter table formacion.queja_apelacion force row level security;
create policy aislamiento_predio on formacion.queja_apelacion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.proyecto enable row level security;
alter table proyectos.proyecto force row level security;
create policy aislamiento_predio on proyectos.proyecto using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.interesado enable row level security;
alter table proyectos.interesado force row level security;
create policy aislamiento_predio on proyectos.interesado using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.elemento_edt enable row level security;
alter table proyectos.elemento_edt force row level security;
create policy aislamiento_predio on proyectos.elemento_edt using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.iteracion enable row level security;
alter table proyectos.iteracion force row level security;
create policy aislamiento_predio on proyectos.iteracion using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.actividad enable row level security;
alter table proyectos.actividad force row level security;
create policy aislamiento_predio on proyectos.actividad using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.dependencia enable row level security;
alter table proyectos.dependencia force row level security;
create policy aislamiento_predio on proyectos.dependencia using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.riesgo enable row level security;
alter table proyectos.riesgo force row level security;
create policy aislamiento_predio on proyectos.riesgo using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.registro enable row level security;
alter table proyectos.registro force row level security;
create policy aislamiento_predio on proyectos.registro using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.solicitud_cambio enable row level security;
alter table proyectos.solicitud_cambio force row level security;
create policy aislamiento_predio on proyectos.solicitud_cambio using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.linea_base enable row level security;
alter table proyectos.linea_base force row level security;
create policy aislamiento_predio on proyectos.linea_base using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());

alter table proyectos.medicion_valor_ganado enable row level security;
alter table proyectos.medicion_valor_ganado force row level security;
create policy aislamiento_predio on proyectos.medicion_valor_ganado using (predio_id = nucleo.predio_actual()) with check (predio_id = nucleo.predio_actual());



-- ============================================================================
-- 1. Auditoría automática (tablas sensibles). Guarda solo los campos que cambiaron.
-- ============================================================================
create or replace function nucleo.auditar() returns trigger language plpgsql security definer set search_path = pg_catalog, nucleo as $$
declare
  v_antes jsonb := case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) end;
  v_despues jsonb := case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) end;
  v_fila jsonb := case when tg_op = 'DELETE' then to_jsonb(old) else to_jsonb(new) end;
  v_clave text;
begin
  if tg_op = 'UPDATE' then
    for v_clave in select key from jsonb_each(v_despues) loop
      if v_antes -> v_clave is not distinct from v_despues -> v_clave then
        v_antes := v_antes - v_clave; v_despues := v_despues - v_clave;
      end if;
    end loop;
    v_antes := v_antes - 'actualizado_en'; v_despues := v_despues - 'actualizado_en';
    if v_despues = '{}'::jsonb then return null; end if;
  end if;
  insert into nucleo.auditoria (predio_id, esquema_tabla, registro_id, accion, datos_antes, datos_despues, usuario_id, agente_id)
  values (coalesce((v_fila ->> 'predio_id')::bigint, nucleo.predio_actual()),
          tg_table_schema || '.' || tg_table_name, (v_fila ->> 'id')::bigint,
          case tg_op when 'INSERT' then 'crear' when 'UPDATE' then 'actualizar' else 'eliminar' end,
          v_antes, v_despues, nucleo.usuario_actual(), nucleo.agente_actual());
  return null;
end $$;
comment on function nucleo.auditar() is 'Disparador genérico de auditoría: quién (usuario o agente de la sesión), qué tabla, qué registro y qué campos cambiaron';

create or replace function nucleo.impedir_cambio() returns trigger language plpgsql as
$$ begin raise exception 'La tabla % es de solo inserción', tg_table_name; end $$;
create trigger tg_auditoria_inmutable before update or delete on nucleo.auditoria for each row execute function nucleo.impedir_cambio();

-- Fincas a las que puede entrar un usuario (para elegir finca al iniciar sesión; salta la RLS a propósito)
create or replace function nucleo.predios_del_usuario(p_usuario bigint)
returns table (predio_id bigint, nombre varchar, rol varchar) language sql stable security definer set search_path = pg_catalog, nucleo as $$
  select p.id, p.nombre, r.codigo from nucleo.usuario_rol ur join nucleo.predio p on p.id = ur.predio_id join nucleo.rol r on r.id = ur.rol_id
  where ur.usuario_id = p_usuario order by p.nombre $$;

-- ============================================================================
-- 2. Inventario perecedero: vencimiento estimado, kardex como única fuente, FEFO
-- ============================================================================
-- 2.1 Estimar vencimiento y fecha límite de venta
create or replace function inventario.estimar_vencimiento() returns trigger language plpgsql as $$
declare v_prod record; v_dias smallint;
begin
  select perecedero, vida_util_ambiente_dias, vida_util_refrigerado_dias, dias_margen_venta into v_prod
  from inventario.producto where id = new.producto_id;
  if new.origen_vencimiento = 'estimado' then
    v_dias := case new.condicion_almacenamiento when 'refrigerado' then coalesce(v_prod.vida_util_refrigerado_dias, v_prod.vida_util_ambiente_dias)
                                                 else v_prod.vida_util_ambiente_dias end;
    new.fecha_vencimiento := case when v_prod.perecedero and v_dias is not null then new.fecha_produccion + v_dias end;
  elsif new.fecha_vencimiento is null then
    raise exception 'Lote %: con vencimiento % debe indicar la fecha de vencimiento', new.codigo_lote, new.origen_vencimiento;
  end if;
  new.fecha_limite_venta := new.fecha_vencimiento - coalesce(v_prod.dias_margen_venta, 0);
  return new;
end $$;
create trigger tg_lote_vencimiento before insert or update of fecha_produccion, condicion_almacenamiento, origen_vencimiento, fecha_vencimiento
  on inventario.lote_inventario for each row execute function inventario.estimar_vencimiento();

-- 2.2 Las cantidades del lote solo las cambia el kardex
create or replace function inventario.proteger_cantidades() returns trigger language plpgsql as $$
begin
  if coalesce(current_setting('guayacan.desde_kardex', true), '') <> 'si' then
    if tg_op = 'INSERT' then
      new.cantidad_disponible := 0; new.cantidad_reservada := 0;
    elsif new.cantidad_disponible is distinct from old.cantidad_disponible or new.cantidad_reservada is distinct from old.cantidad_reservada then
      raise exception 'Las cantidades del lote % solo cambian con un movimiento de inventario', old.codigo_lote;
    end if;
  end if;
  return new;
end $$;
create trigger tg_lote_proteger before insert or update on inventario.lote_inventario for each row execute function inventario.proteger_cantidades();

create or replace function inventario.entrada_inicial() returns trigger language plpgsql as $$
begin
  insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
  values (new.predio_id, new.id, 'entrada', new.cantidad_inicial, new.costo_unitario, coalesce(new.origen_tabla, 'lote_inventario'), coalesce(new.origen_id, new.id), nucleo.usuario_actual());
  return null;
end $$;
create trigger tg_lote_entrada after insert on inventario.lote_inventario for each row execute function inventario.entrada_inicial();

-- 2.3 Aplicar cada movimiento al lote (con bloqueo de fila: dos reservas simultáneas no pueden tomar el mismo producto)
create or replace function inventario.aplicar_movimiento() returns trigger language plpgsql as $$
declare v_lote record; v_disp numeric; v_res numeric;
begin
  if new.cantidad <= 0 then raise exception 'La cantidad del movimiento debe ser positiva'; end if;
  if new.tipo = 'merma' and new.causa_merma is null then raise exception 'Toda merma debe indicar su causa'; end if;
  select * into v_lote from inventario.lote_inventario where id = new.lote_inventario_id for update;
  v_disp := v_lote.cantidad_disponible; v_res := v_lote.cantidad_reservada;
  case new.tipo
    when 'entrada', 'ajuste_entrada', 'traslado_entrada' then v_disp := v_disp + new.cantidad;
    when 'reserva' then v_disp := v_disp - new.cantidad; v_res := v_res + new.cantidad;
    when 'liberacion' then v_res := v_res - new.cantidad; v_disp := v_disp + new.cantidad;
    when 'salida_venta' then v_res := v_res - new.cantidad;
    else v_disp := v_disp - new.cantidad;  -- consumo_interno, merma, ajuste_salida, traslado_salida
  end case;
  if v_disp < 0 or v_res < 0 then
    raise exception 'Inventario insuficiente en el lote %: disponible %, reservado %, se pidió % (%)',
      v_lote.codigo_lote, v_lote.cantidad_disponible, v_lote.cantidad_reservada, new.cantidad, new.tipo;
  end if;
  if new.tipo in ('reserva', 'salida_venta') and v_lote.estado in ('vencido', 'bloqueado') then
    raise exception 'El lote % está % y no se puede vender', v_lote.codigo_lote, v_lote.estado;
  end if;
  perform set_config('guayacan.desde_kardex', 'si', true);
  update inventario.lote_inventario set cantidad_disponible = v_disp, cantidad_reservada = v_res,
    estado = case when v_disp + v_res = 0 and estado = 'disponible' then 'agotado'
                  when v_disp + v_res > 0 and estado = 'agotado' then 'disponible' else estado end
  where id = new.lote_inventario_id;
  perform set_config('guayacan.desde_kardex', 'no', true);
  return null;
end $$;
create trigger tg_movimiento_aplicar after insert on inventario.movimiento_inventario for each row execute function inventario.aplicar_movimiento();
create trigger tg_movimiento_inmutable before update or delete on inventario.movimiento_inventario for each row execute function nucleo.impedir_cambio();
comment on function inventario.aplicar_movimiento() is 'Kardex: único camino para cambiar existencias; las correcciones se hacen con ajuste_entrada o ajuste_salida, nunca editando';

-- 2.3b Especificación única: ¿se puede vender este lote? (la usan la reserva FEFO, el catálogo y el escaneo)
create or replace function inventario.puede_venderse(l inventario.lote_inventario) returns boolean language sql stable as $$
  select l.estado = 'disponible' and l.cantidad_disponible > 0
     and (l.fecha_limite_venta is null or l.fecha_limite_venta >= current_date)
     and not exists (select 1 from inventario.bloqueo_lote b where b.lote_inventario_id = l.id and b.decision = 'pendiente') $$;
comment on function inventario.puede_venderse(inventario.lote_inventario) is 'Patrón Specification: disponible, con existencias, antes de su fecha límite de venta y sin bloqueo abierto';

-- 2.4 Reservar en orden FEFO (primero lo que vence primero); no toma lotes pasados de su fecha límite de venta
create or replace function inventario.reservar_fefo(p_detalle bigint) returns numeric language plpgsql as $$
declare d record; r record; v_pend numeric; v_tomar numeric;
begin
  select pd.*, p.metodo_salida, p.nombre as producto into d
  from comercial.pedido_detalle pd join inventario.producto p on p.id = pd.producto_id where pd.id = p_detalle;
  v_pend := d.cantidad;
  for r in select l.id, l.cantidad_disponible, l.costo_unitario from inventario.lote_inventario l
           where l.producto_id = d.producto_id and inventario.puede_venderse(l)
           order by case when d.metodo_salida = 'fefo' then l.fecha_vencimiento end nulls last, l.fecha_produccion, l.id
           for update skip locked loop
    v_tomar := least(v_pend, r.cantidad_disponible);
    insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
    values (d.predio_id, r.id, 'reserva', v_tomar, r.costo_unitario, 'pedido_detalle', p_detalle, nucleo.usuario_actual());
    insert into comercial.reserva_lote (predio_id, pedido_detalle_id, lote_inventario_id, cantidad) values (d.predio_id, p_detalle, r.id, v_tomar);
    v_pend := v_pend - v_tomar;
    exit when v_pend = 0;
  end loop;
  if v_pend > 0 then
    raise exception 'Inventario insuficiente de %: faltan % para la línea %', d.producto, v_pend, p_detalle;
  end if;
  return d.cantidad;
end $$;

-- 2.5 Confirmar, despachar y cancelar pedidos
create or replace function comercial.confirmar_pedido(p_pedido bigint) returns void language plpgsql as $$
declare d record; v_ped record; v_cli record; v_total numeric; v_cartera numeric;
begin
  select * into v_ped from comercial.pedido where id = p_pedido for update;
  if v_ped.estado <> 'borrador' then raise exception 'El pedido % está % y no se puede confirmar', v_ped.numero, v_ped.estado; end if;
  if v_ped.forma_pago = 'credito' then
    perform nucleo.exigir_funcion('venta_credito');
    select * into v_cli from terceros.cliente where id = v_ped.cliente_id;
    if v_cli.bloqueado_por_mora then raise exception 'El cliente tiene facturas vencidas: no puede comprar a crédito'; end if;
  end if;
  for d in select pd.id, pp.vigente_hasta from comercial.pedido_detalle pd join comercial.precio_producto pp on pp.id = pd.precio_producto_id
           where pd.pedido_id = p_pedido loop
    if d.vigente_hasta is not null then
      raise exception 'El precio de la línea % cambió después de crear el pedido; actualícelo antes de confirmar', d.id;
    end if;
    perform inventario.reservar_fefo(d.id);
  end loop;
  update comercial.pedido p set estado = 'confirmado',
    subtotal = t.sub, descuento = t.des, impuestos = t.iva, total = t.sub - t.des + t.iva + p.valor_domicilio
  from (select coalesce(sum(cantidad * precio_unitario), 0) sub, coalesce(sum(descuento), 0) des,
               coalesce(sum(round((cantidad * precio_unitario - descuento) * tarifa_iva / 100, 2)), 0) iva
        from comercial.pedido_detalle where pedido_id = p_pedido) t
  where p.id = p_pedido
  returning p.total into v_total;
  if v_ped.forma_pago = 'credito' then
    select coalesce(sum(saldo), 0) into v_cartera from comercial.factura where cliente_id = v_ped.cliente_id and saldo > 0;
    if v_cartera + v_total > v_cli.cupo_credito then
      raise exception 'Cupo de crédito insuficiente: cartera %, pedido %, cupo %', v_cartera, v_total, v_cli.cupo_credito;
    end if;
  end if;
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (v_ped.predio_id, 'pedido.confirmado', 'comercial.pedido', p_pedido, jsonb_build_object('numero', v_ped.numero, 'cliente_id', v_ped.cliente_id));
end $$;

create or replace function comercial.despachar_pedido(p_pedido bigint) returns void language plpgsql as $$
declare r record;
begin
  for r in select rl.* , l.costo_unitario from comercial.reserva_lote rl join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id
           join inventario.lote_inventario l on l.id = rl.lote_inventario_id
           where pd.pedido_id = p_pedido and rl.estado = 'reservada' loop
    insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
    values (r.predio_id, r.lote_inventario_id, 'salida_venta', r.cantidad, r.costo_unitario, 'pedido', p_pedido, nucleo.usuario_actual());
    update comercial.reserva_lote set estado = 'despachada' where id = r.id;
  end loop;
  update comercial.pedido set estado = 'despachado' where id = p_pedido and estado in ('confirmado', 'en_preparacion');
  if not found then raise exception 'El pedido % no está confirmado', p_pedido; end if;
end $$;

create or replace function comercial.cancelar_pedido(p_pedido bigint) returns void language plpgsql as $$
declare r record;
begin
  for r in select rl.*, l.costo_unitario from comercial.reserva_lote rl join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id
           join inventario.lote_inventario l on l.id = rl.lote_inventario_id
           where pd.pedido_id = p_pedido and rl.estado = 'reservada' loop
    insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, costo_unitario, documento_tipo, documento_id, usuario_id)
    values (r.predio_id, r.lote_inventario_id, 'liberacion', r.cantidad, r.costo_unitario, 'pedido', p_pedido, nucleo.usuario_actual());
    update comercial.reserva_lote set estado = 'liberada' where id = r.id;
  end loop;
  update comercial.pedido set estado = 'cancelado' where id = p_pedido and estado not in ('despachado', 'entregado');
  if not found then raise exception 'El pedido % ya salió de la finca; use una devolución', p_pedido; end if;
end $$;

-- 2.6 Tarea diaria (Celery Beat): marcar vencidos. La merma la registra una persona tras revisar el producto.
create or replace function inventario.marcar_vencidos() returns integer language plpgsql as $$
declare n integer;
begin
  update inventario.lote_inventario set estado = 'vencido'
  where estado = 'disponible' and fecha_vencimiento < current_date and cantidad_disponible + cantidad_reservada > 0;
  get diagnostics n = row_count;
  return n;
end $$;

-- 2.7 Alertas de vencimiento (semáforo) con precio de liquidación según la política aprobada por el administrador
create view inventario.v_alertas_vencimiento with (security_invoker = true) as
select l.predio_id, l.id as lote_inventario_id, l.codigo_lote, p.id as producto_id, p.sku, p.nombre as producto,
       l.cantidad_disponible, l.fecha_produccion, l.fecha_vencimiento, l.fecha_limite_venta,
       l.fecha_limite_venta - current_date as dias_para_limite,
       case when l.fecha_limite_venta < current_date then 'rojo'
            when l.fecha_limite_venta - current_date <= p.dias_alerta_venta then 'amarillo' else 'verde' end as semaforo,
       case when l.fecha_limite_venta < current_date then 'no vender: revisar y registrar merma, autoconsumo o alimento animal'
            when l.fecha_limite_venta - current_date <= p.dias_alerta_venta then 'vender primero: ofrecer a clientes frecuentes con precio de liquidación'
            else 'normal' end as accion_sugerida,
       pp.precio_unitario as precio_vigente,
       case when l.fecha_limite_venta >= current_date and l.fecha_limite_venta - current_date <= p.dias_alerta_venta
            then round(pp.precio_unitario * (1 - coalesce((select par.valor::numeric from nucleo.parametro par
                   where par.clave = 'descuento_por_vencer_pct' and (par.predio_id = l.predio_id or par.predio_id is null)
                     and par.vigente_desde <= current_date and (par.vigente_hasta is null or par.vigente_hasta >= current_date)
                   order by par.predio_id nulls last, par.vigente_desde desc limit 1), 0) / 100), 0) end as precio_liquidacion
from inventario.lote_inventario l
join inventario.producto p on p.id = l.producto_id and p.perecedero
left join comercial.lista_precios lp on lp.predio_id = l.predio_id and lp.codigo = 'PUBLICO'
left join comercial.precio_producto pp on pp.producto_id = p.id and pp.lista_precios_id = lp.id and pp.vigente_hasta is null
where l.estado = 'disponible' and l.cantidad_disponible > 0;
comment on view inventario.v_alertas_vencimiento is 'Lotes perecederos con días para su fecha límite de venta, semáforo, acción sugerida y precio de liquidación; la consultan el panel y el vendedor virtual';

-- Catálogo para los agentes: solo lo que se puede vender hoy (sin costos)
create view comercial.v_catalogo_disponible with (security_invoker = true) as
select p.predio_id, p.id as producto_id, p.sku, p.nombre, p.descripcion, u.codigo as unidad, lp.codigo as lista, pp.precio_unitario,
       coalesce(sum(l.cantidad_disponible) filter (where inventario.puede_venderse(l)), 0) as cantidad_disponible,
       min(l.fecha_limite_venta) filter (where inventario.puede_venderse(l)) as proxima_fecha_limite
from inventario.producto p
join inventario.unidad_medida u on u.id = p.unidad_id
join comercial.precio_producto pp on pp.producto_id = p.id and pp.vigente_hasta is null
join comercial.lista_precios lp on lp.id = pp.lista_precios_id
left join inventario.lote_inventario l on l.producto_id = p.id
where p.se_vende and p.activo
group by p.predio_id, p.id, p.sku, p.nombre, p.descripcion, u.codigo, lp.codigo, pp.precio_unitario;

-- ============================================================================
-- 3. Precios
-- ============================================================================
create unique index ux_precio_vigente on comercial.precio_producto (predio_id, producto_id, lista_precios_id) where vigente_hasta is null;

create or replace function comercial.aplicar_propuesta_precio(p_propuesta bigint) returns bigint language plpgsql as $$
declare v record; v_nuevo bigint;
begin
  select * into v from comercial.propuesta_precio where id = p_propuesta and estado = 'aprobada' for update;
  if not found then raise exception 'La propuesta % no existe o no está aprobada', p_propuesta; end if;
  update comercial.precio_producto set vigente_hasta = now()
   where producto_id = v.producto_id and lista_precios_id = v.lista_precios_id and vigente_hasta is null;
  insert into comercial.precio_producto (predio_id, lista_precios_id, producto_id, precio_unitario, vigente_desde, propuesta_precio_id, aprobado_por)
  values (v.predio_id, v.lista_precios_id, v.producto_id, v.precio_propuesto, now(), v.id, coalesce(v.revisado_por, nucleo.usuario_actual()))
  returning id into v_nuevo;
  update comercial.propuesta_precio set estado = 'aplicada', aplicada_en = now() where id = v.id;
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (v.predio_id, 'precio.aplicado', 'comercial.precio_producto', v_nuevo, jsonb_build_object('producto_id', v.producto_id, 'precio', v.precio_propuesto));
  return v_nuevo;
end $$;
comment on function comercial.aplicar_propuesta_precio(bigint) is 'Aplica una propuesta aprobada: cierra el precio vigente y crea el nuevo. Lo confirmado, reservado o facturado conserva su precio congelado en pedido_detalle';

-- ============================================================================
-- 4. Contabilidad: cuadre, periodos e inmutabilidad
-- ============================================================================
create or replace function finanzas.periodo_abierto(p_predio bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from finanzas.periodo_contable where predio_id = p_predio and anio = extract(year from p_fecha)
                 and mes = extract(month from p_fecha) and estado = 'abierto') $$;

create or replace function finanzas.proteger_comprobante() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then
    if old.estado <> 'borrador' then raise exception 'El comprobante % no se puede borrar; anúlelo', old.numero; end if;
    return old;
  end if;
  if tg_op = 'UPDATE' and old.estado = 'anulado' then raise exception 'El comprobante % está anulado', old.numero; end if;
  if tg_op = 'UPDATE' and old.estado = 'contabilizado' then
    if new.estado <> 'anulado' or new.motivo_anulacion is null then
      raise exception 'El comprobante % está contabilizado: solo se puede anular indicando el motivo', old.numero;
    end if;
    if (to_jsonb(new) - array['estado', 'motivo_anulacion', 'actualizado_en']) <> (to_jsonb(old) - array['estado', 'motivo_anulacion', 'actualizado_en']) then
      raise exception 'Solo se pueden cambiar el estado y el motivo de anulación de un comprobante contabilizado';
    end if;
  end if;
  if new.estado in ('contabilizado', 'anulado') and not finanzas.periodo_abierto(new.predio_id, new.fecha) then
    raise exception 'El periodo %-% está cerrado o no existe', extract(year from new.fecha), extract(month from new.fecha);
  end if;
  if new.estado = 'contabilizado' and (tg_op = 'INSERT' or old.estado = 'borrador') then
    new.contabilizado_en := now(); new.aprobado_por := coalesce(new.aprobado_por, nucleo.usuario_actual());
  end if;
  return new;
end $$;
create trigger tg_comprobante_proteger before insert or update or delete on finanzas.comprobante for each row execute function finanzas.proteger_comprobante();

-- Débitos = créditos: se revisa al confirmar la transacción (diferido), así se pueden insertar todas las líneas primero
create or replace function finanzas.validar_cuadre() returns trigger language plpgsql as $$
declare v_deb numeric; v_cred numeric; v_n integer;
begin
  if new.estado <> 'contabilizado' then return null; end if;
  select coalesce(sum(debito), 0), coalesce(sum(credito), 0), count(*) into v_deb, v_cred, v_n
  from finanzas.movimiento_contable where comprobante_id = new.id;
  if v_n < 2 or v_deb <> v_cred or v_deb = 0 then
    raise exception 'Comprobante % descuadrado: débitos %, créditos %, líneas %', new.numero, v_deb, v_cred, v_n;
  end if;
  return null;
end $$;
create constraint trigger tg_comprobante_cuadre after insert or update on finanzas.comprobante
  deferrable initially deferred for each row execute function finanzas.validar_cuadre();

create or replace function finanzas.proteger_movimiento() returns trigger language plpgsql as $$
declare v_estado text;
begin
  select estado into v_estado from finanzas.comprobante where id = coalesce(new.comprobante_id, old.comprobante_id);
  if v_estado <> 'borrador' then
    raise exception 'El comprobante está %: sus movimientos no se pueden cambiar (use una nota contable)', v_estado;
  end if;
  return coalesce(new, old);
end $$;
create trigger tg_movimiento_contable_proteger before insert or update or delete on finanzas.movimiento_contable
  for each row execute function finanzas.proteger_movimiento();

-- ============================================================================
-- 5. Canales: ¿se puede enviar este mensaje? (regla fija que consulta el conector antes de cada envío)
-- ============================================================================
create or replace function redes.verificar_envio(p_cuenta_red bigint, p_tercero bigint, p_ultimo_mensaje_cliente timestamptz,
  p_desde_anuncio boolean, p_autor text, p_plantilla bigint default null) returns text language plpgsql stable as $$
declare pc record; v_horas integer; v_dentro boolean; v_pl record; v_enviados integer;
begin
  select pol.* into pc from redes.cuenta_red cr join redes.politica_canal pol on pol.plataforma = cr.plataforma where cr.id = p_cuenta_red;
  if not found or not pc.disponible then return 'bloqueado: canal no disponible'; end if;
  v_horas := pc.ventana_horas;
  if p_desde_anuncio and pc.ventana_anuncio_horas is not null then v_horas := greatest(v_horas, pc.ventana_anuncio_horas); end if;
  if p_autor = 'humano' and pc.ventana_agente_humano_horas is not null then v_horas := greatest(v_horas, pc.ventana_agente_humano_horas); end if;
  v_dentro := v_horas is null or (p_ultimo_mensaje_cliente is not null and now() <= p_ultimo_mensaje_cliente + make_interval(hours => v_horas));
  if p_plantilla is not null then
    select * into v_pl from redes.plantilla_mensaje where id = p_plantilla and cuenta_red_id = p_cuenta_red;
    if not found or v_pl.estado_meta <> 'aprobada' then return 'bloqueado: plantilla no aprobada por el canal'; end if;
    if not exists (select 1 from terceros.consentimiento_datos c where c.tercero_id = p_tercero and c.finalidad = v_pl.finalidad_requerida
                   and c.otorgado and c.revocado_en is null) then
      return 'bloqueado: el cliente no ha autorizado ' || v_pl.finalidad_requerida;
    end if;
    return 'permitido: plantilla';
  end if;
  if not v_dentro then
    return case when pc.requiere_plantilla_fuera_ventana then 'bloqueado: fuera de la ventana; solo con plantilla aprobada'
                else 'bloqueado: fuera de la ventana; el canal no permite escribir hasta que el cliente vuelva a escribir' end;
  end if;
  if pc.max_mensajes_por_ventana is not null then
    select count(*) into v_enviados from redes.mensaje_saliente
    where cuenta_red_id = p_cuenta_red and tercero_id = p_tercero and enviado_en >= p_ultimo_mensaje_cliente and estado_entrega <> 'bloqueado_por_regla';
    if v_enviados >= pc.max_mensajes_por_ventana then return 'bloqueado: se alcanzó el tope de mensajes de la ventana'; end if;
  end if;
  return 'permitido: servicio';
end $$;
comment on function redes.verificar_envio(bigint, bigint, timestamptz, boolean, text, bigint) is 'Aplica las reglas del canal (ventana, extensión para agente humano, plantillas, consentimiento, tope de mensajes) antes de enviar';

-- ============================================================================
-- 7. Funciones por finca (feature flags): lo que espera equipo o decisión queda construido y apagado
-- ============================================================================
create or replace function nucleo.funcion_activa(p_codigo text) returns boolean language sql stable as $$
  select coalesce((select activa from nucleo.funcionalidad where codigo = p_codigo and predio_id = nucleo.predio_actual()), false) $$;
create or replace function nucleo.exigir_funcion(p_codigo text) returns void language plpgsql stable as $$
begin
  if not nucleo.funcion_activa(p_codigo) then raise exception 'La función % no está activa en esta finca', p_codigo; end if;
end $$;
create or replace function nucleo.registrar_activacion() returns trigger language plpgsql as $$
begin
  if new.activa and (tg_op = 'INSERT' or not old.activa) then
    new.activada_en := now(); new.activada_por := coalesce(new.activada_por, nucleo.usuario_actual());
  end if;
  return new;
end $$;
create trigger tg_funcionalidad_activacion before insert or update on nucleo.funcionalidad for each row execute function nucleo.registrar_activacion();

create or replace function nucleo.mantener_particiones(p_meses integer default 3) returns integer language plpgsql as $$
declare m integer;
begin
  for m in 0 .. p_meses loop
    perform nucleo.crear_particion_mensual('nucleo.auditoria', (current_date + make_interval(months => m))::date);
    perform nucleo.crear_particion_mensual('iot.lectura', (current_date + make_interval(months => m))::date);
  end loop;
  return p_meses + 1;
end $$;

-- ============================================================================
-- 8. Trazabilidad: cadena de huellas, bloqueos, cadena de frío y retiro de lotes
-- ============================================================================
create or replace function comercial.registrar_huella(p_predio bigint, p_lote bigint, p_hecho text, p_contenido jsonb) returns char(64)
language plpgsql as $$
declare v_ant char(64); v_hash char(64);
begin
  perform pg_advisory_xact_lock(hashtext('huella_trazabilidad'), p_predio::integer);
  select hash into v_ant from comercial.huella_trazabilidad where predio_id = p_predio order by id desc limit 1;
  v_hash := encode(sha256(convert_to(coalesce(v_ant, '') || p_contenido::text, 'UTF8')), 'hex');
  insert into comercial.huella_trazabilidad (predio_id, lote_inventario_id, hecho, contenido, hash_anterior, hash)
  values (p_predio, p_lote, p_hecho, p_contenido, v_ant, v_hash);
  return v_hash;
end $$;
comment on function comercial.registrar_huella(bigint, bigint, text, jsonb) is 'Agrega un eslabón a la cadena SHA-256 de la finca; lista para anclarse en una red externa con el adaptador RegistroExterno';

create or replace function comercial.verificar_cadena_huellas()
returns table (huella_id bigint, hecho text, valida boolean) language sql stable as $$
  select id, hecho,
         hash = encode(sha256(convert_to(coalesce(lag(hash) over w, '') || contenido::text, 'UTF8')), 'hex')
         and hash_anterior is not distinct from lag(hash) over w
  from comercial.huella_trazabilidad window w as (partition by predio_id order by id) order by id $$;

create or replace function comercial.proteger_huella() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' or (to_jsonb(new) - array['anclaje_red', 'anclaje_transaccion', 'anclado_en'])
                         <> (to_jsonb(old) - array['anclaje_red', 'anclaje_transaccion', 'anclado_en']) then
    raise exception 'La cadena de huellas es de solo inserción; solo se registra su anclaje';
  end if;
  return new;
end $$;
create trigger tg_huella_proteger before update or delete on comercial.huella_trazabilidad for each row execute function comercial.proteger_huella();

create or replace function inventario.huella_lote_creado() returns trigger language plpgsql as $$
begin
  perform comercial.registrar_huella(new.predio_id, new.id, 'lote_creado', jsonb_build_object('codigo_lote', new.codigo_lote,
    'producto_id', new.producto_id, 'origen', new.origen, 'fecha_produccion', new.fecha_produccion, 'fecha_vencimiento', new.fecha_vencimiento,
    'cantidad', new.cantidad_inicial));
  return null;
end $$;
create trigger tg_lote_huella after insert on inventario.lote_inventario for each row execute function inventario.huella_lote_creado();

create or replace function comercial.huella_despacho() returns trigger language plpgsql as $$
begin
  if new.estado = 'despachada' and old.estado <> 'despachada' then
    perform comercial.registrar_huella(new.predio_id, new.lote_inventario_id, 'despachado', jsonb_build_object('pedido_detalle_id', new.pedido_detalle_id,
      'cantidad', new.cantidad, 'cliente_id', (select p.cliente_id from comercial.pedido_detalle pd join comercial.pedido p on p.id = pd.pedido_id
                                              where pd.id = new.pedido_detalle_id)));
  end if;
  return null;
end $$;
create trigger tg_reserva_huella after update on comercial.reserva_lote for each row execute function comercial.huella_despacho();

-- 8.1 Bloqueo de lotes: lo pone una regla o una persona; solo una persona lo libera o lo descarta
create or replace function inventario.aplicar_bloqueo() returns trigger language plpgsql as $$
declare v_lote record;
begin
  select * into v_lote from inventario.lote_inventario where id = new.lote_inventario_id for update;
  if tg_op = 'INSERT' then
    if new.decision <> 'pendiente' then raise exception 'Un bloqueo nace pendiente'; end if;
    update inventario.lote_inventario set estado = 'bloqueado' where id = new.lote_inventario_id and estado in ('disponible', 'agotado');
    insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
    values (new.predio_id, 'lote.bloqueado', 'inventario.lote_inventario', new.lote_inventario_id, jsonb_build_object('motivo', new.motivo, 'codigo_lote', v_lote.codigo_lote));
    perform comercial.registrar_huella(new.predio_id, new.lote_inventario_id, 'bloqueado', jsonb_build_object('motivo', new.motivo, 'origen', new.origen_tabla));
    return new;
  end if;
  if old.decision <> 'pendiente' then raise exception 'El bloqueo % ya fue decidido', old.id; end if;
  if new.decision = 'pendiente' then return new; end if;
  if nucleo.agente_actual() is not null then raise exception 'Solo una persona decide sobre un lote bloqueado'; end if;
  new.decidido_por := coalesce(new.decidido_por, nucleo.usuario_actual());
  if new.decidido_por is null then raise exception 'La decisión sobre el lote % debe tener responsable', v_lote.codigo_lote; end if;
  new.decidido_en := now();
  if new.decision = 'liberado' then
    if not exists (select 1 from inventario.bloqueo_lote where lote_inventario_id = new.lote_inventario_id and decision = 'pendiente' and id <> new.id) then
      update inventario.lote_inventario set estado = case when fecha_vencimiento < current_date then 'vencido'
                                                         when cantidad_disponible + cantidad_reservada = 0 then 'agotado' else 'disponible' end
      where id = new.lote_inventario_id and estado = 'bloqueado';
    end if;
  else
    if v_lote.cantidad_disponible > 0 then
      insert into inventario.movimiento_inventario (predio_id, lote_inventario_id, tipo, cantidad, causa_merma, costo_unitario, documento_tipo, documento_id, usuario_id)
      values (new.predio_id, new.lote_inventario_id, 'merma', v_lote.cantidad_disponible, 'calidad', v_lote.costo_unitario, 'bloqueo_lote', new.id, new.decidido_por);
    end if;
  end if;
  perform comercial.registrar_huella(new.predio_id, new.lote_inventario_id, new.decision, jsonb_build_object('bloqueo_id', new.id, 'decidido_por', new.decidido_por));
  return new;
end $$;
create trigger tg_bloqueo_aplicar before insert or update on inventario.bloqueo_lote for each row execute function inventario.aplicar_bloqueo();

-- 8.2 Cadena de frío: una excursión que supera la tolerancia bloquea los lotes perecederos de la nevera o del vehículo en ruta
create or replace function inventario.evaluar_excursion() returns trigger language plpgsql as $$
declare v_tol integer; r record; n integer := 0;
begin
  if new.bodega_id is not null then select minutos_tolerancia into v_tol from inventario.bodega where id = new.bodega_id;
  else select minutos_tolerancia into v_tol from inventario.vehiculo where id = new.vehiculo_id; end if;
  if new.minutos_fuera <= v_tol or new.lotes_bloqueados > 0 then return new; end if;
  for r in select l.id from inventario.lote_inventario l join inventario.producto p on p.id = l.producto_id
           where p.perecedero and l.estado in ('disponible', 'agotado') and l.cantidad_disponible + l.cantidad_reservada > 0
             and (l.bodega_id = new.bodega_id
                  or l.id in (select rl.lote_inventario_id from comercial.entrega e
                              join comercial.pedido_detalle pd on pd.pedido_id = e.pedido_id
                              join comercial.reserva_lote rl on rl.pedido_detalle_id = pd.id
                              where e.vehiculo_id = new.vehiculo_id and e.estado = 'en_ruta')) loop
    insert into inventario.bloqueo_lote (predio_id, lote_inventario_id, motivo, origen_tabla, origen_id)
    values (new.predio_id, r.id, 'cadena_frio', 'excursion_temperatura', new.id);
    n := n + 1;
  end loop;
  new.lotes_bloqueados := n;
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (new.predio_id, 'temperatura.fuera_de_rango', 'inventario.excursion_temperatura', new.id,
          jsonb_build_object('minutos_fuera', new.minutos_fuera, 'temperatura', new.temperatura_extrema_c, 'lotes_bloqueados', n));
  return new;
end $$;
create trigger tg_excursion_evaluar before insert or update on inventario.excursion_temperatura for each row execute function inventario.evaluar_excursion();

-- 8.3 Trazabilidad y retiro (recall)
create view comercial.v_trazabilidad_lote with (security_invoker = true) as
select l.predio_id, l.id as lote_inventario_id, l.codigo_lote, p.nombre as producto, l.origen, l.origen_tabla, l.origen_id,
       l.fecha_produccion, l.fecha_vencimiento, l.estado as estado_lote, ped.id as pedido_id, ped.numero as pedido, ped.estado as estado_pedido,
       c.id as cliente_id, coalesce(t.razon_social, concat_ws(' ', t.nombres, t.apellidos)) as cliente, t.whatsapp, rl.cantidad, rl.estado as estado_reserva
from inventario.lote_inventario l
join inventario.producto p on p.id = l.producto_id
left join comercial.reserva_lote rl on rl.lote_inventario_id = l.id and rl.estado <> 'liberada'
left join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id
left join comercial.pedido ped on ped.id = pd.pedido_id
left join terceros.cliente c on c.id = ped.cliente_id
left join terceros.tercero t on t.id = c.tercero_id;
comment on view comercial.v_trazabilidad_lote is 'De dónde salió un lote y a qué clientes y pedidos llegó';

create or replace function comercial.abrir_retiro(p_lote bigint, p_motivo text) returns bigint language plpgsql as $$
declare v_id bigint; v_predio bigint;
begin
  select predio_id into v_predio from inventario.lote_inventario where id = p_lote;
  if not found then raise exception 'El lote % no existe', p_lote; end if;
  insert into comercial.retiro_lote (predio_id, lote_inventario_id, motivo, abierto_por) values (v_predio, p_lote, p_motivo, nucleo.usuario_actual())
  returning id into v_id;
  insert into inventario.bloqueo_lote (predio_id, lote_inventario_id, motivo, origen_tabla, origen_id) values (v_predio, p_lote, 'retiro', 'retiro_lote', v_id);
  insert into comercial.retiro_aviso (predio_id, retiro_lote_id, cliente_id, pedido_id, cantidad)
  select v_predio, v_id, ped.cliente_id, ped.id, sum(rl.cantidad) from comercial.reserva_lote rl
  join comercial.pedido_detalle pd on pd.id = rl.pedido_detalle_id join comercial.pedido ped on ped.id = pd.pedido_id
  where rl.lote_inventario_id = p_lote and rl.estado = 'despachada' group by ped.cliente_id, ped.id;
  perform comercial.registrar_huella(v_predio, p_lote, 'retirado', jsonb_build_object('retiro_id', v_id, 'motivo', p_motivo));
  insert into nucleo.evento_salida (predio_id, tipo_evento, entidad, entidad_id, carga)
  values (v_predio, 'lote.retirado', 'comercial.retiro_lote', v_id, jsonb_build_object('lote_id', p_lote));
  return v_id;
end $$;
comment on function comercial.abrir_retiro(bigint, text) is 'Retiro de un lote: lo bloquea y crea un aviso por cada cliente que lo recibió';

-- ============================================================================
-- 9. Producción: clasificación del huevo por peso
-- ============================================================================
create or replace function produccion.clasificar_por_peso(p_peso_g numeric, p_fecha date default current_date) returns varchar language sql stable as $$
  select c.codigo from produccion.categoria_huevo c
  where c.vigente_desde = (select max(vigente_desde) from produccion.categoria_huevo where vigente_desde <= p_fecha)
    and p_peso_g >= c.peso_min_g and (c.peso_max_g is null or p_peso_g < c.peso_max_g)
  order by c.peso_min_g desc limit 1 $$;

create or replace function produccion.validar_clasificacion() returns trigger language plpgsql as $$
declare v_buenos integer; v_suma integer;
begin
  if new.metodo = 'vision' then perform nucleo.exigir_funcion('vision_artificial'); end if;
  select huevos_recogidos - huevos_rotos into v_buenos from produccion.registro_postura where id = new.registro_postura_id;
  select coalesce(sum(cantidad), 0) into v_suma from produccion.clasificacion_postura where registro_postura_id = new.registro_postura_id;
  if v_suma > v_buenos then raise exception 'La clasificación suma % huevos y solo hay % buenos', v_suma, v_buenos; end if;
  return null;
end $$;
create trigger tg_clasificacion_validar after insert or update on produccion.clasificacion_postura for each row execute function produccion.validar_clasificacion();

-- ============================================================================
-- 10. Cartera, pagos, permuta y pedidos recurrentes (cartera y permuta se encienden con su función)
-- ============================================================================
create or replace function comercial.preparar_factura() returns trigger language plpgsql as $$
declare v_plazo smallint;
begin
  select dias_plazo into v_plazo from terceros.cliente where id = new.cliente_id;
  new.saldo := new.total;
  new.fecha_vencimiento := coalesce(new.fecha_vencimiento, new.fecha_emision::date + case when new.forma_pago = 'credito' then coalesce(v_plazo, 0) else 0 end);
  return new;
end $$;
create trigger tg_factura_preparar before insert on comercial.factura for each row execute function comercial.preparar_factura();

create or replace function comercial.aplicar_pago() returns trigger language plpgsql as $$
declare v_delta numeric := 0;
begin
  if new.estado = 'confirmado' and nucleo.agente_actual() is not null then raise exception 'Un agente no puede confirmar pagos'; end if;
  if new.medio = 'pasarela' and new.proveedor_pasarela is null then raise exception 'Indique la pasarela de pago'; end if;
  if new.factura_id is null then return new; end if;
  if new.estado = 'confirmado' and (tg_op = 'INSERT' or old.estado <> 'confirmado') then v_delta := -new.valor;
  elsif tg_op = 'UPDATE' and old.estado = 'confirmado' and new.estado <> 'confirmado' then v_delta := old.valor; end if;
  if v_delta <> 0 then
    update comercial.factura set saldo = saldo + v_delta where id = new.factura_id;
    if (select saldo from comercial.factura where id = new.factura_id) < 0 then raise exception 'El pago supera el saldo de la factura'; end if;
  end if;
  return new;
end $$;
create trigger tg_pago_aplicar before insert or update on comercial.pago for each row execute function comercial.aplicar_pago();

create view comercial.v_cartera with (security_invoker = true) as
select f.predio_id, f.cliente_id, coalesce(t.razon_social, concat_ws(' ', t.nombres, t.apellidos)) as cliente, f.id as factura_id,
       f.prefijo || '-' || f.numero as factura, f.fecha_emision::date as fecha_emision, f.fecha_vencimiento, f.total, f.saldo,
       greatest(current_date - f.fecha_vencimiento, 0) as dias_mora,
       case when current_date <= f.fecha_vencimiento then 'al_dia' when current_date - f.fecha_vencimiento <= 30 then '1_30'
            when current_date - f.fecha_vencimiento <= 60 then '31_60' when current_date - f.fecha_vencimiento <= 90 then '61_90' else 'mas_90' end as edad
from comercial.factura f join terceros.cliente c on c.id = f.cliente_id join terceros.tercero t on t.id = c.tercero_id
where f.saldo > 0 and f.estado_dian <> 'rechazada';
comment on view comercial.v_cartera is 'Saldo por factura y edad de la deuda; base de la mora y del cupo';

create or replace function comercial.actualizar_mora() returns integer language plpgsql as $$
declare n integer;
begin
  update terceros.cliente c set bloqueado_por_mora = exists (select 1 from comercial.factura f where f.cliente_id = c.id and f.saldo > 0
                                                             and f.fecha_vencimiento < current_date)
  where bloqueado_por_mora is distinct from exists (select 1 from comercial.factura f where f.cliente_id = c.id and f.saldo > 0
                                                    and f.fecha_vencimiento < current_date);
  get diagnostics n = row_count;
  return n;
end $$;

create or replace function comercial.aplicar_permuta() returns trigger language plpgsql as $$
declare v_fac record; v_ds record; v_usado numeric;
begin
  perform nucleo.exigir_funcion('permuta');
  select * into v_fac from comercial.factura where id = new.factura_id for update;
  select * into v_ds from compras.documento_soporte where id = new.documento_soporte_id for update;
  select coalesce(sum(valor_compensado), 0) into v_usado from comercial.permuta where documento_soporte_id = new.documento_soporte_id;
  if new.valor_compensado > v_fac.saldo or v_usado + new.valor_compensado > v_ds.total then
    raise exception 'La permuta (%) supera el saldo de la factura (%) o lo disponible del documento soporte (%)', new.valor_compensado, v_fac.saldo, v_ds.total - v_usado;
  end if;
  new.registrado_por := coalesce(new.registrado_por, nucleo.usuario_actual());
  insert into comercial.pago (predio_id, factura_id, fecha, valor, medio, referencia, estado, confirmado_por)
  values (new.predio_id, new.factura_id, now(), new.valor_compensado, 'compensacion_permuta', 'DS ' || v_ds.prefijo || '-' || v_ds.numero, 'confirmado', new.registrado_por);
  return new;
end $$;
create trigger tg_permuta_aplicar before insert on comercial.permuta for each row execute function comercial.aplicar_permuta();
create trigger tg_permuta_inmutable before update or delete on comercial.permuta for each row execute function nucleo.impedir_cambio();

create or replace function comercial.generar_pedidos_recurrentes(p_fecha date default current_date) returns integer language plpgsql as $$
declare r record; d record; v_ped bigint; v_lista bigint; v_precio record; n integer := 0;
begin
  if not nucleo.funcion_activa('pedidos_recurrentes') then return 0; end if;
  for r in select pr.*, c.lista_precios_id from comercial.pedido_recurrente pr join terceros.cliente c on c.id = pr.cliente_id
           where pr.activo and pr.proxima_fecha <= p_fecha for update of pr loop
    v_lista := coalesce(r.lista_precios_id, (select id from comercial.lista_precios where codigo = 'PUBLICO'));
    insert into comercial.pedido (predio_id, numero, cliente_id, canal, forma_pago, pedido_recurrente_id, fecha_entrega_programada)
    values (r.predio_id, 'REC-' || r.id || '-' || to_char(r.proxima_fecha, 'YYYYMMDD'), r.cliente_id, r.canal, r.forma_pago, r.id, r.proxima_fecha)
    returning id into v_ped;
    for d in select rd.*, p.tarifa_iva from comercial.pedido_recurrente_detalle rd join inventario.producto p on p.id = rd.producto_id
             where rd.pedido_recurrente_id = r.id loop
      select * into v_precio from comercial.precio_producto where producto_id = d.producto_id and lista_precios_id = v_lista and vigente_hasta is null;
      if not found then raise exception 'El producto % no tiene precio vigente para el pedido recurrente %', d.producto_id, r.id; end if;
      insert into comercial.pedido_detalle (predio_id, pedido_id, producto_id, cantidad, precio_producto_id, precio_unitario, tarifa_iva, total_linea)
      values (r.predio_id, v_ped, d.producto_id, d.cantidad, v_precio.id, v_precio.precio_unitario, d.tarifa_iva, d.cantidad * v_precio.precio_unitario);
    end loop;
    update comercial.pedido_recurrente set proxima_fecha = (proxima_fecha + case frecuencia when 'semanal' then interval '7 days'
                                                            when 'quincenal' then interval '15 days' else interval '1 month' end)::date
    where id = r.id;
    n := n + 1;
  end loop;
  return n;
end $$;
comment on function comercial.generar_pedidos_recurrentes(date) is 'Tarea diaria: crea en borrador los pedidos recurrentes que tocan; un vendedor los confirma';

-- ============================================================================
-- 11. Audiovisual: consentimiento de imagen, aprobación humana y retención de clips
-- ============================================================================
create or replace function redes.validar_pieza() returns trigger language plpgsql as $$
declare v_faltan text;
begin
  if new.estado in ('aprobada', 'publicada') and (tg_op = 'INSERT' or old.estado not in ('aprobada', 'publicada')) then
    if nucleo.agente_actual() is not null then raise exception 'Solo una persona aprueba contenido para redes'; end if;
    new.aprobado_por := coalesce(new.aprobado_por, nucleo.usuario_actual());
    if new.aprobado_por is null then raise exception 'La aprobación debe tener responsable'; end if;
    if new.personas_identificables then
      if not exists (select 1 from redes.pieza_persona where pieza_audiovisual_id = new.id) then
        raise exception 'La pieza muestra personas: registre quiénes aparecen';
      end if;
      select string_agg(coalesce(t.razon_social, concat_ws(' ', t.nombres, t.apellidos)), ', ') into v_faltan
      from redes.pieza_persona pp join terceros.tercero t on t.id = pp.tercero_id
      where pp.pieza_audiovisual_id = new.id and not exists (select 1 from terceros.consentimiento_datos c where c.tercero_id = pp.tercero_id
            and c.finalidad = 'imagen_redes' and c.otorgado and c.revocado_en is null);
      if v_faltan is not null then raise exception 'Falta autorización de imagen de: %', v_faltan; end if;
    end if;
  end if;
  return new;
end $$;
create trigger tg_pieza_validar before insert or update on redes.pieza_audiovisual for each row execute function redes.validar_pieza();

create or replace function iot.preparar_clip() returns trigger language plpgsql as $$
begin
  if new.retener_hasta is null then
    new.retener_hasta := new.inicio::date + (select retencion_dias from iot.camara where id = new.camara_id);
  end if;
  return new;
end $$;
create trigger tg_clip_preparar before insert on iot.clip_video for each row execute function iot.preparar_clip();

create or replace function iot.depurar_clips() returns integer language plpgsql as $$
declare n integer;
begin
  update iot.clip_video set borrado_en = now() where borrado_en is null and not para_redes and retener_hasta < current_date;
  get diagnostics n = row_count;
  return n;
end $$;
comment on function iot.depurar_clips() is 'Tarea diaria: marca para borrar los clips vencidos; el servicio IoT borra el archivo';

create or replace function iot.validar_camara() returns trigger language plpgsql as $$
begin
  if new.tipo = 'termica' then perform nucleo.exigir_funcion('camara_termica'); end if;
  return new;
end $$;
create trigger tg_camara_validar before insert or update of tipo on iot.camara for each row execute function iot.validar_camara();

-- ============================================================================
-- 12. Seguridad perimetral: estados de la alarma, cerraduras seguras y credenciales
-- ============================================================================
create or replace function iot.cambiar_estado_alarma(p_zona bigint, p_nuevo text, p_origen text) returns void language plpgsql as $$
declare v_zona record;
begin
  select * into v_zona from iot.zona_seguridad where id = p_zona for update;
  if not found then raise exception 'La zona de seguridad % no existe', p_zona; end if;
  if (v_zona.estado_alarma, p_nuevo) not in (('desarmado', 'armado'), ('desarmado', 'noche'), ('desarmado', 'mantenimiento'),
       ('armado', 'desarmado'), ('armado', 'noche'), ('noche', 'desarmado'), ('noche', 'armado'), ('mantenimiento', 'desarmado')) then
    raise exception 'Cambio de alarma no permitido: % a %', v_zona.estado_alarma, p_nuevo;
  end if;
  perform set_config('guayacan.desde_alarma', 'si', true);
  update iot.zona_seguridad set estado_alarma = p_nuevo where id = p_zona;
  perform set_config('guayacan.desde_alarma', 'no', true);
  insert into iot.cambio_estado_alarma (predio_id, zona_seguridad_id, estado_anterior, estado_nuevo, origen, usuario_id)
  values (v_zona.predio_id, p_zona, v_zona.estado_alarma, p_nuevo, p_origen, nucleo.usuario_actual());
end $$;
comment on function iot.cambiar_estado_alarma(bigint, text, text) is 'Patrón State: solo transiciones válidas (mantenimiento solo desde desarmado), con historial';

create or replace function iot.proteger_estado_alarma() returns trigger language plpgsql as $$
begin
  if new.estado_alarma is distinct from old.estado_alarma and coalesce(current_setting('guayacan.desde_alarma', true), '') <> 'si' then
    raise exception 'El estado de la alarma solo cambia con iot.cambiar_estado_alarma';
  end if;
  return new;
end $$;
create trigger tg_zona_seguridad_estado before update on iot.zona_seguridad for each row execute function iot.proteger_estado_alarma();
create trigger tg_cambio_alarma_inmutable before update or delete on iot.cambio_estado_alarma for each row execute function nucleo.impedir_cambio();

create or replace function iot.validar_actuador() returns trigger language plpgsql as $$
begin
  if new.tipo = 'cerradura' then
    if new.zona_seguridad_id is null then raise exception 'Una cerradura debe pertenecer a una zona de seguridad'; end if;
    if new.modo_falla <> 'abre_sin_energia' and (select paso_personas from iot.zona_seguridad where id = new.zona_seguridad_id) then
      raise exception 'La cerradura % está en un paso de personas: debe abrir sin energía', new.codigo;
    end if;
  end if;
  return new;
end $$;
create trigger tg_actuador_validar before insert or update on iot.actuador for each row execute function iot.validar_actuador();

create or replace function iot.proteger_evento_seguridad() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' or (to_jsonb(new) - array['atendido_por', 'atendido_en', 'nota_atencion', 'actualizado_en'])
                         <> (to_jsonb(old) - array['atendido_por', 'atendido_en', 'nota_atencion', 'actualizado_en']) then
    raise exception 'Un evento de seguridad no se modifica; solo se registra su atención';
  end if;
  return new;
end $$;
create trigger tg_evento_seguridad_proteger before update or delete on iot.evento_seguridad for each row execute function iot.proteger_evento_seguridad();

create or replace function iot.validar_credencial() returns trigger language plpgsql as $$
begin
  if new.metodo = 'facial' and new.activa then
    perform nucleo.exigir_funcion('reconocimiento_facial');
    if not exists (select 1 from terceros.consentimiento_datos c where c.id = new.consentimiento_id and c.tercero_id = new.tercero_id
                   and c.finalidad = 'biometria_acceso' and c.otorgado and c.revocado_en is null) then
      raise exception 'El acceso facial exige autorización expresa y vigente de biometría de la misma persona; use PIN o tarjeta';
    end if;
  end if;
  return new;
end $$;
create trigger tg_credencial_validar before insert or update on iot.credencial_acceso for each row execute function iot.validar_credencial();

create or replace function terceros.revocar_biometria() returns trigger language plpgsql as $$
begin
  if new.finalidad = 'biometria_acceso' and new.revocado_en is not null and old.revocado_en is null then
    update iot.credencial_acceso set activa = false where consentimiento_id = new.id and metodo = 'facial';
  end if;
  return null;
end $$;
create trigger tg_consentimiento_biometria after update on terceros.consentimiento_datos for each row execute function terceros.revocar_biometria();

-- ============================================================================
-- 13. Indicadores ambientales (CO₂ siempre "estimado" y con su fuente)
-- ============================================================================
create view ambiental.v_indicadores with (security_invoker = true) as
select r.predio_id, date_trunc('month', r.fecha)::date as mes, r.magnitud, sum(r.cantidad) as cantidad,
       f.factor_kgco2e, round(sum(r.cantidad) * f.factor_kgco2e, 2) as kgco2e_estimado, f.fuente
from ambiental.registro_ambiental r
left join lateral (select fe.factor_kgco2e, fe.fuente from ambiental.factor_emision fe
                   where fe.magnitud = r.magnitud and fe.vigente_desde <= r.fecha order by fe.vigente_desde desc limit 1) f on true
group by r.predio_id, date_trunc('month', r.fecha), r.magnitud, f.factor_kgco2e, f.fuente;
comment on view ambiental.v_indicadores is 'Totales del mes y CO₂ equivalente estimado con el factor y la fuente a la vista';

-- ============================================================================
-- 14. Apoyos comunes v5: parámetros vigentes, permisos y "solo personas"
-- ============================================================================
create or replace function nucleo.parametro_valor(p_clave text, p_fecha date default current_date) returns numeric language sql stable as $$
  select par.valor::numeric from nucleo.parametro par
  where par.clave = p_clave and (par.predio_id = nucleo.predio_actual() or par.predio_id is null)
    and par.vigente_desde <= p_fecha and (par.vigente_hasta is null or par.vigente_hasta >= p_fecha)
  order by par.predio_id nulls last, par.vigente_desde desc limit 1 $$;
comment on function nucleo.parametro_valor(text, date) is 'Valor numérico vigente de un parámetro: primero el de la finca, si no el nacional';

create or replace function nucleo.tiene_permiso(p_usuario bigint, p_permiso text) returns boolean language sql stable as $$
  select coalesce((select es_superusuario from nucleo.usuario where id = p_usuario), false)
      or exists (select 1 from nucleo.usuario_rol ur join nucleo.rol_permiso rp on rp.rol_id = ur.rol_id
                 join nucleo.permiso pe on pe.id = rp.permiso_id where ur.usuario_id = p_usuario and pe.codigo = p_permiso) $$;

create or replace function nucleo.exigir_persona(p_accion text) returns void language plpgsql stable as $$
begin
  if nucleo.agente_actual() is not null then raise exception 'Un agente de IA no puede %: lo hace una persona', p_accion; end if;
  if nucleo.usuario_actual() is null then raise exception 'Para % se necesita un usuario identificado', p_accion; end if;
end $$;
comment on function nucleo.exigir_persona(text) is 'La IA propone y una persona decide: corta la acción si la sesión es de un agente';

create or replace function nucleo.tercero_de_usuario(p_usuario bigint) returns bigint language sql stable as $$
  select tercero_id from nucleo.usuario where id = p_usuario $$;

-- ============================================================================
-- 15. Personal: disponibilidad, habilitación, aprobación y plan de labores
-- ============================================================================
create or replace function personal.empleado_disponible(p_empleado bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from terceros.empleado e where e.id = p_empleado and e.fecha_ingreso <= p_fecha
                 and (e.fecha_retiro is null or e.fecha_retiro >= p_fecha))
     and not exists (select 1 from personal.ausencia a where a.empleado_id = p_empleado and p_fecha between a.desde and a.hasta) $$;

create or replace function formacion.esta_habilitado(p_tercero bigint, p_competencia bigint, p_fecha date default current_date)
returns boolean language sql stable as $$
  select exists (select 1 from formacion.habilitacion h where h.tercero_id = p_tercero and h.competencia_id = p_competencia
                 and h.activa and h.desde <= p_fecha and (h.hasta is null or h.hasta >= p_fecha)) $$;

create or replace function personal.validar_tarea() returns trigger language plpgsql as $$
declare v_comp bigint; v_ter bigint; v_emp record;
begin
  if tg_op = 'UPDATE' and old.estado in ('aprobada', 'cancelada') then
    raise exception 'La tarea % está %: no se edita', old.id, old.estado;
  end if;
  if nucleo.agente_actual() is not null and (new.empleado_id is not null or new.cuadrilla_id is not null)
     and (tg_op = 'INSERT' or new.empleado_id is distinct from old.empleado_id or new.cuadrilla_id is distinct from old.cuadrilla_id) then
    raise exception 'Un agente propone tareas pero no las asigna: la asignación la hace el encargado';
  end if;
  select competencia_id into v_comp from personal.plantilla_tarea where id = new.plantilla_tarea_id;
  if new.empleado_id is not null and (tg_op = 'INSERT' or new.empleado_id is distinct from old.empleado_id or new.fecha <> old.fecha) then
    if not personal.empleado_disponible(new.empleado_id, new.fecha) then
      raise exception 'El trabajador % no está disponible el % (retirado o con ausencia)', new.empleado_id, new.fecha;
    end if;
    select tercero_id into v_ter from terceros.empleado where id = new.empleado_id;
    if v_comp is not null and not formacion.esta_habilitado(v_ter, v_comp, new.fecha) then
      raise exception 'El trabajador % no está habilitado para esta tarea (falta el curso o el certificado venció)', new.empleado_id;
    end if;
  end if;
  if new.cuadrilla_id is not null and (tg_op = 'INSERT' or new.cuadrilla_id is distinct from old.cuadrilla_id or new.fecha <> old.fecha) then
    for v_emp in select e.id, e.tercero_id from personal.cuadrilla_miembro m join terceros.empleado e on e.id = m.empleado_id
                 where m.cuadrilla_id = new.cuadrilla_id and m.desde <= new.fecha and (m.hasta is null or m.hasta >= new.fecha) loop
      if v_comp is not null and not formacion.esta_habilitado(v_emp.tercero_id, v_comp, new.fecha) then
        raise exception 'El trabajador % de la cuadrilla no está habilitado para esta tarea', v_emp.id;
      end if;
    end loop;
  end if;
  if new.estado = 'en_curso' and (tg_op = 'INSERT' or old.estado <> 'en_curso') then new.iniciada_en := coalesce(new.iniciada_en, now()); end if;
  if new.estado = 'terminada' and (tg_op = 'INSERT' or old.estado <> 'terminada') then new.terminada_en := coalesce(new.terminada_en, now()); end if;
  if new.estado in ('aprobada', 'devuelta') and (tg_op = 'INSERT' or old.estado <> new.estado) then
    perform nucleo.exigir_persona('aprobar o devolver tareas');
    if tg_op = 'INSERT' or old.estado <> 'terminada' then raise exception 'Solo se aprueba o devuelve una tarea terminada'; end if;
    new.aprobado_por := coalesce(new.aprobado_por, nucleo.usuario_actual());
    if not nucleo.tiene_permiso(new.aprobado_por, 'personal.aprobar_tarea')
       and not (new.area_id is not null and personal.es_responsable_area(new.aprobado_por, new.area_id, new.fecha)) then
      raise exception 'El usuario % no tiene el permiso personal.aprobar_tarea ni es responsable del área', new.aprobado_por;
    end if;
    if new.empleado_id is not null and nucleo.tercero_de_usuario(new.aprobado_por) = (select tercero_id from terceros.empleado where id = new.empleado_id) then
      raise exception 'Nadie aprueba su propia tarea';
    end if;
    if new.estado = 'devuelta' and new.comentario_revision is null then raise exception 'Para devolver una tarea hay que decir por qué'; end if;
    new.aprobado_en := now();
  end if;
  return new;
end $$;
create trigger tg_tarea_validar before insert or update on personal.tarea for each row execute function personal.validar_tarea();
create trigger tg_tarea_no_borrar before delete on personal.tarea for each row execute function nucleo.impedir_cambio();

create or replace function personal.generar_tareas_del_dia(p_fecha date default current_date) returns integer language plpgsql as $$
declare v_n integer := 0; r record; v_tarea bigint;
begin
  for r in select * from personal.plantilla_tarea p where p.activa and (
             p.recurrencia = 'diaria'
          or (p.recurrencia = 'semanal' and extract(isodow from p_fecha)::smallint = any(p.dias_semana))
          or (p.recurrencia = 'mensual' and extract(day from p_fecha) = 1))
          and not exists (select 1 from personal.tarea t where t.plantilla_tarea_id = p.id and t.fecha = p_fecha) loop
    insert into personal.tarea (plantilla_tarea_id, titulo, proceso, fecha, hora_limite, prioridad, zona_id, origen)
    values (r.id, r.nombre, r.proceso, p_fecha, case when r.hora_limite is not null then (p_fecha + r.hora_limite)::timestamptz end,
            r.prioridad, r.zona_id, 'plan') returning id into v_tarea;
    insert into personal.paso_tarea (tarea_id, orden, descripcion)
    select v_tarea, x.ord::smallint, x.paso #>> '{}' from jsonb_array_elements(coalesce(r.pasos, '[]')) with ordinality x(paso, ord);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function personal.generar_tareas_del_dia(date) is 'Tarea diaria (Celery Beat): crea las tareas del día desde el plan de labores, sin asignar; el encargado asigna';

create or replace function personal.calcular_jornada() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and old.aprobada_en is not null then raise exception 'La jornada % ya fue aprobada: no se edita', old.id; end if;
  if new.salida is not null and new.horas is null then new.horas := round(extract(epoch from new.salida - new.entrada) / 3600.0, 2); end if;
  if new.aprobada_por is not null and new.aprobada_en is null then
    perform nucleo.exigir_persona('aprobar jornadas'); new.aprobada_en := now();
  end if;
  return new;
end $$;
create trigger tg_jornada_calcular before insert or update on personal.jornada for each row execute function personal.calcular_jornada();

create or replace view personal.v_productividad as
select t.empleado_id, t.plantilla_tarea_id, date_trunc('month', t.fecha)::date as mes, count(*) as tareas_aprobadas,
       sum(t.cantidad) as cantidad, round(sum(t.cantidad) / nullif(sum(extract(epoch from t.terminada_en - t.iniciada_en)) / 3600, 0), 2) as cantidad_por_hora,
       round(avg(extract(epoch from t.terminada_en - t.iniciada_en) / 60) / nullif(max(p.duracion_estimada_min), 0) * 100, 1) as pct_tiempo_vs_estandar
from personal.tarea t left join personal.plantilla_tarea p on p.id = t.plantilla_tarea_id
where t.estado = 'aprobada' group by 1, 2, 3;

-- ============================================================================
-- 16. Nómina: prenómina, liquidación, periodo inmutable y pagos con doble aprobación
-- ============================================================================
create or replace function nomina.proteger_periodo() returns trigger language plpgsql as $$
declare v_estado_comp text;
begin
  if tg_op = 'DELETE' then
    if old.estado <> 'abierto' then raise exception 'El periodo % no se puede borrar', old.codigo; end if;
    return old;
  end if;
  if old.estado in ('cerrado', 'anulado') then
    raise exception 'El periodo % está %: no se edita; las correcciones van como nota de ajuste', old.codigo, old.estado;
  end if;
  if new.estado = 'cerrado' then
    perform nucleo.exigir_persona('cerrar la nómina');
    new.cerrado_por := coalesce(new.cerrado_por, nucleo.usuario_actual());
    if new.aprobado_por is null or new.aprobado_por = new.cerrado_por then
      raise exception 'El cierre de nómina necesita dos personas distintas (cierra % y aprueba %)', new.cerrado_por, new.aprobado_por;
    end if;
    if not exists (select 1 from nomina.liquidacion where periodo_id = new.id) then raise exception 'El periodo % no tiene liquidaciones', new.codigo; end if;
    select estado into v_estado_comp from finanzas.comprobante where id = new.comprobante_id;
    if v_estado_comp is distinct from 'contabilizado' then
      raise exception 'El cierre necesita su comprobante de causación contabilizado (cuadrado)';
    end if;
    update nomina.liquidacion set estado = 'aprobada' where periodo_id = new.id and estado = 'borrador';
    new.cerrado_en := now();
  end if;
  return new;
end $$;
create trigger tg_periodo_nomina_proteger before update or delete on nomina.periodo_nomina for each row execute function nomina.proteger_periodo();

create or replace function nomina.proteger_detalle_periodo() returns trigger language plpgsql as $$
declare v_periodo bigint; v_estado text; v_reg record;
begin
  v_reg := coalesce(new, old);
  if tg_table_name = 'liquidacion_detalle' then
    select l.periodo_id into v_periodo from nomina.liquidacion l where l.id = v_reg.liquidacion_id;
  else
    v_periodo := v_reg.periodo_id;
  end if;
  select estado into v_estado from nomina.periodo_nomina where id = v_periodo;
  if v_estado in ('cerrado', 'anulado') then
    if tg_table_name = 'liquidacion' and tg_op = 'UPDATE'
       and (to_jsonb(new) - array['estado', 'actualizado_en']) = (to_jsonb(old) - array['estado', 'actualizado_en']) then
      return new;  -- solo el paso a "pagada"
    end if;
    raise exception 'El periodo de nómina está %: no se cambian sus datos', v_estado;
  end if;
  return coalesce(new, old);
end $$;
create trigger tg_novedad_periodo before insert or update or delete on nomina.novedad for each row execute function nomina.proteger_detalle_periodo();
create trigger tg_liquidacion_periodo before insert or update or delete on nomina.liquidacion for each row execute function nomina.proteger_detalle_periodo();
create trigger tg_liquidacion_detalle_periodo before insert or update or delete on nomina.liquidacion_detalle for each row execute function nomina.proteger_detalle_periodo();
create trigger tg_provision_periodo before insert or update or delete on nomina.provision_prestacion for each row execute function nomina.proteger_detalle_periodo();

create or replace function nomina.validar_novedad() returns trigger language plpgsql as $$
declare v_base text; v_pago text; v_estado text;
begin
  select base into v_base from nomina.concepto_nomina where id = new.concepto_id;
  if v_base = 'salario' and new.origen in ('tarea', 'jornada') then
    raise exception 'El salario de un contrato no depende de que se aprueben tareas: las tareas solo pagan jornales y destajo';
  end if;
  if new.origen = 'tarea' then
    select t.estado, p.forma_pago into v_estado, v_pago from personal.tarea t left join personal.plantilla_tarea p on p.id = t.plantilla_tarea_id where t.id = new.tarea_id;
    if v_estado is distinct from 'aprobada' then raise exception 'Solo una tarea aprobada genera pago'; end if;
    if coalesce(v_pago, 'ninguna') = 'ninguna' then raise exception 'La tarea % no paga jornal ni destajo', new.tarea_id; end if;
  end if;
  if new.origen = 'jornada' and not exists (select 1 from personal.jornada where id = new.jornada_id and aprobada_en is not null) then
    raise exception 'Solo una jornada aprobada genera pago';
  end if;
  new.valor := coalesce(new.valor, round(new.cantidad * new.valor_unitario, 0));
  return new;
end $$;
create trigger tg_novedad_validar before insert or update on nomina.novedad for each row execute function nomina.validar_novedad();

create or replace function nomina.concepto(p_codigo text) returns bigint language sql stable as $$
  select id from nomina.concepto_nomina where codigo = p_codigo and activo $$;

create or replace function nomina.preparar_prenomina(p_periodo bigint) returns integer language plpgsql as $$
declare v_p nomina.periodo_nomina; v_n integer := 0; v_k integer; v_smmlv numeric; v_aux numeric;
begin
  select * into v_p from nomina.periodo_nomina where id = p_periodo for update;
  if v_p.estado not in ('abierto', 'prenomina') then raise exception 'El periodo % está %', v_p.codigo, v_p.estado; end if;
  v_smmlv := nucleo.parametro_valor('salario_minimo', v_p.hasta);
  v_aux := nucleo.parametro_valor('auxilio_transporte', v_p.hasta);
  -- a) Salario fijo de los contratos (no depende de tareas); días calendario comerciales (máximo 30)
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, valor, origen)
  select p_periodo, e.id, nomina.concepto('SALARIO'), d.dias, round(e.salario_base / 30, 2), round(e.salario_base / 30 * d.dias, 0), 'contrato'
  from terceros.empleado e
  cross join lateral (select least(30, (least(v_p.hasta, coalesce(e.fecha_retiro, v_p.hasta)) - greatest(v_p.desde, e.fecha_ingreso) + 1))::numeric as dias) d
  where e.forma_pago in ('salario', 'mixto') and e.salario_base > 0 and d.dias > 0
    and not exists (select 1 from nomina.novedad n where n.periodo_id = p_periodo and n.empleado_id = e.id and n.origen = 'contrato');
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  -- Auxilio de transporte a quien gana hasta dos salarios mínimos
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, valor, origen, observacion)
  select p_periodo, n.empleado_id, nomina.concepto('AUX_TRANSPORTE'), n.cantidad, round(v_aux / 30, 2), round(v_aux / 30 * n.cantidad, 0), 'contrato', 'Auxilio de transporte'
  from nomina.novedad n join terceros.empleado e on e.id = n.empleado_id
  where n.periodo_id = p_periodo and n.concepto_id = nomina.concepto('SALARIO') and e.salario_base <= 2 * v_smmlv
    and not exists (select 1 from nomina.novedad x where x.periodo_id = p_periodo and x.empleado_id = n.empleado_id and x.concepto_id = nomina.concepto('AUX_TRANSPORTE'));
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  -- b) Jornales y destajo de tareas aprobadas del periodo
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, origen, tarea_id)
  select p_periodo, t.empleado_id, nomina.concepto(case p.forma_pago when 'jornal' then 'JORNAL' else 'DESTAJO' end),
         case p.forma_pago when 'jornal' then 1 else coalesce(t.cantidad, 0) end, p.valor_unitario, 'tarea', t.id
  from personal.tarea t join personal.plantilla_tarea p on p.id = t.plantilla_tarea_id
  where t.estado = 'aprobada' and t.empleado_id is not null and t.fecha between v_p.desde and v_p.hasta and p.forma_pago in ('jornal', 'destajo')
  on conflict do nothing;
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  -- c) Jornadas aprobadas de jornaleros sin tarea
  insert into nomina.novedad (periodo_id, empleado_id, concepto_id, cantidad, valor_unitario, origen, jornada_id)
  select p_periodo, j.empleado_id, nomina.concepto('JORNAL'), 1, e.valor_jornal, 'jornada', j.id
  from personal.jornada j join terceros.empleado e on e.id = j.empleado_id
  where j.aprobada_en is not null and j.fecha between v_p.desde and v_p.hasta and e.forma_pago in ('jornal', 'mixto') and e.valor_jornal > 0
  on conflict do nothing;
  get diagnostics v_k = row_count; v_n := v_n + v_k;
  update nomina.periodo_nomina set estado = 'prenomina', preparado_por = coalesce(preparado_por, nucleo.usuario_actual()) where id = p_periodo;
  return v_n;
end $$;
comment on function nomina.preparar_prenomina(bigint) is 'Reúne el periodo: salario de los contratos, auxilio de transporte, jornales y destajo de tareas aprobadas y jornadas aprobadas. El encargado la revisa antes de cerrar';

create or replace function nomina.liquidar(p_periodo bigint) returns integer language plpgsql as $$
declare v_p nomina.periodo_nomina; r record; v_liq bigint; v_base numeric; v_ded numeric; v_n integer := 0; v_aux numeric;
begin
  select * into v_p from nomina.periodo_nomina where id = p_periodo;
  if v_p.estado <> 'prenomina' then raise exception 'Primero prepare la prenómina del periodo %', v_p.codigo; end if;
  delete from nomina.liquidacion_detalle where liquidacion_id in (select id from nomina.liquidacion where periodo_id = p_periodo);
  delete from nomina.provision_prestacion where periodo_id = p_periodo;
  delete from nomina.liquidacion where periodo_id = p_periodo;
  for r in select distinct n.empleado_id, e.forma_pago from nomina.novedad n join terceros.empleado e on e.id = n.empleado_id where n.periodo_id = p_periodo loop
    insert into nomina.liquidacion (periodo_id, empleado_id) values (p_periodo, r.empleado_id) returning id into v_liq;
    insert into nomina.liquidacion_detalle (liquidacion_id, concepto_id, cantidad, valor)
    select v_liq, n.concepto_id, sum(n.cantidad), sum(n.valor) from nomina.novedad n where n.periodo_id = p_periodo and n.empleado_id = r.empleado_id group by n.concepto_id;
    select coalesce(sum(d.valor), 0) into v_base from nomina.liquidacion_detalle d join nomina.concepto_nomina c on c.id = d.concepto_id
    where d.liquidacion_id = v_liq and c.tipo = 'devengado' and c.constitutivo_salario;
    select coalesce(sum(d.valor), 0) into v_aux from nomina.liquidacion_detalle d where d.liquidacion_id = v_liq and d.concepto_id = nomina.concepto('AUX_TRANSPORTE');
    -- Aportes del trabajador a salud y pensión (tarifas en nucleo.parametro)
    insert into nomina.liquidacion_detalle (liquidacion_id, concepto_id, cantidad, valor)
    select v_liq, nomina.concepto(c.cod), 1, round(v_base * nucleo.parametro_valor(c.par, v_p.hasta) / 100, 0)
    from (values ('SALUD_EMP', 'aporte_salud_empleado_pct'), ('PENSION_EMP', 'aporte_pension_empleado_pct')) c(cod, par)
    where v_base > 0 and nomina.concepto(c.cod) is not null;
    select coalesce(sum(case c.tipo when 'devengado' then d.valor end), 0), coalesce(sum(case c.tipo when 'deduccion' then d.valor end), 0)
      into v_base, v_ded
    from nomina.liquidacion_detalle d join nomina.concepto_nomina c on c.id = d.concepto_id where d.liquidacion_id = v_liq;
    update nomina.liquidacion set total_devengado = v_base, total_deducciones = v_ded, neto = v_base - v_ded where id = v_liq;
    -- Provisión de prestaciones para contratos (cesantías y prima incluyen el auxilio de transporte; vacaciones no)
    if r.forma_pago in ('salario', 'mixto') then
      insert into nomina.provision_prestacion (periodo_id, empleado_id, tipo, base, valor)
      select p_periodo, r.empleado_id, x.tipo, x.base, round(x.base * nucleo.parametro_valor(x.par, v_p.hasta) / 100, 0)
      from (select 'cesantias' tipo, v_base base, 'provision_cesantias_pct' par union all
            select 'intereses_cesantias', v_base, 'provision_intereses_cesantias_pct' union all
            select 'prima', v_base, 'provision_prima_pct' union all
            select 'vacaciones', v_base - v_aux, 'provision_vacaciones_pct') x
      where nucleo.parametro_valor(x.par, v_p.hasta) is not null;
    end if;
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function nomina.liquidar(bigint) is 'Liquida la prenómina: devengado, aportes del trabajador, neto y provisión de prestaciones, con tarifas de nucleo.parametro (se configuran con el contador)';

create or replace function nomina.validar_pago() returns trigger language plpgsql as $$
declare v_emp_ter bigint; v_neto numeric; v_pagado numeric; v_umbral numeric;
begin
  if tg_op = 'UPDATE' and old.pagado_en is not null then raise exception 'El pago % ya se hizo: no se edita', old.id; end if;
  select e.tercero_id, l.neto into v_emp_ter, v_neto from nomina.liquidacion l join terceros.empleado e on e.id = l.empleado_id where l.id = new.liquidacion_id;
  select coalesce(sum(valor), 0) into v_pagado from nomina.pago_nomina where liquidacion_id = new.liquidacion_id and id is distinct from new.id;
  if v_pagado + new.valor > v_neto then raise exception 'El pago supera el neto de la liquidación (% de %)', v_pagado + new.valor, v_neto; end if;
  if nucleo.tercero_de_usuario(new.preparado_por) = v_emp_ter then raise exception 'Nadie prepara su propio pago'; end if;
  if (tg_op = 'INSERT' and new.aprobado_por is not null) or (tg_op = 'UPDATE' and new.aprobado_por is distinct from old.aprobado_por)
     or (tg_op = 'INSERT' and new.segunda_aprobacion_por is not null) or (tg_op = 'UPDATE' and new.segunda_aprobacion_por is distinct from old.segunda_aprobacion_por) then
    perform nucleo.exigir_persona('aprobar pagos');
  end if;
  if new.aprobado_por is not null then
    if new.aprobado_por = new.preparado_por then raise exception 'Quien prepara el pago no lo aprueba'; end if;
    if nucleo.tercero_de_usuario(new.aprobado_por) = v_emp_ter then raise exception 'Nadie aprueba su propio pago'; end if;
  end if;
  if new.segunda_aprobacion_por is not null and (new.segunda_aprobacion_por in (new.preparado_por, new.aprobado_por)
     or nucleo.tercero_de_usuario(new.segunda_aprobacion_por) = v_emp_ter) then
    raise exception 'La segunda aprobación la da una tercera persona distinta';
  end if;
  if new.pagado_en is not null then
    perform nucleo.exigir_persona('registrar pagos');
    if new.aprobado_por is null then raise exception 'El pago no está aprobado'; end if;
    v_umbral := nucleo.parametro_valor('monto_doble_aprobacion');
    if v_umbral is not null and new.valor > v_umbral and new.segunda_aprobacion_por is null then
      raise exception 'Pagos mayores a % necesitan segunda aprobación', v_umbral;
    end if;
  end if;
  return new;
end $$;
create trigger tg_pago_nomina_validar before insert or update on nomina.pago_nomina for each row execute function nomina.validar_pago();
create trigger tg_pago_nomina_no_borrar before delete on nomina.pago_nomina for each row execute function nucleo.impedir_cambio();

create or replace function nomina.marcar_pagada() returns trigger language plpgsql as $$
begin
  if new.pagado_en is not null and (select coalesce(sum(valor), 0) from nomina.pago_nomina where liquidacion_id = new.liquidacion_id and pagado_en is not null)
       >= (select neto from nomina.liquidacion where id = new.liquidacion_id) then
    update nomina.liquidacion set estado = 'pagada' where id = new.liquidacion_id;
  end if;
  return null;
end $$;
create trigger tg_pago_nomina_pagada after insert or update on nomina.pago_nomina for each row execute function nomina.marcar_pagada();

create or replace function nomina.validar_documento_electronico() returns trigger language plpgsql as $$
begin
  perform nucleo.exigir_funcion('nomina_electronica');
  if (select regimen_tributario from nucleo.predio where id = nucleo.predio_actual()) = 'por_definir' then
    raise exception 'Defina el régimen tributario del empleador antes de transmitir nómina electrónica';
  end if;
  return new;
end $$;
create trigger tg_documento_nomina_validar before insert on nomina.documento_nomina_electronica for each row execute function nomina.validar_documento_electronico();

-- ============================================================================
-- 17. Formación: aprobar un curso emite certificado y habilita; al vencer se retira
-- ============================================================================
create or replace function formacion.validar_curso() returns trigger language plpgsql as $$
begin
  if new.origen = 'moodle' then perform nucleo.exigir_funcion('cursos_externos'); end if;
  return new;
end $$;
create trigger tg_curso_validar before insert or update on formacion.curso for each row execute function formacion.validar_curso();

create or replace function formacion.emitir_certificado(p_tercero bigint, p_competencia bigint, p_nota numeric, p_inscripcion bigint, p_sesion bigint)
returns bigint language plpgsql as $$
declare v_meses smallint; v_id bigint;
begin
  select vigencia_meses into v_meses from formacion.competencia where id = p_competencia;
  insert into formacion.certificado (tercero_id, competencia_id, inscripcion_id, sesion_id, emitido_en, vence_en, nota, codigo_verificacion)
  values (p_tercero, p_competencia, p_inscripcion, p_sesion, current_date,
          case when v_meses is not null then (current_date + make_interval(months => v_meses))::date end, p_nota,
          upper(substr(md5(random()::text || clock_timestamp()::text), 1, 12)))
  returning id into v_id;
  return v_id;
end $$;

create or replace function formacion.validar_inscripcion() returns trigger language plpgsql as $$
declare v_min numeric;
begin
  if new.estado = 'aprobado' and (tg_op = 'INSERT' or old.estado <> 'aprobado') then
    select nota_minima into v_min from formacion.curso where id = new.curso_id;
    if new.nota is null or new.nota < v_min then raise exception 'Nota % menor que la mínima % para aprobar', new.nota, v_min; end if;
    new.aprobado_en := coalesce(new.aprobado_en, current_date);
  end if;
  return new;
end $$;
create trigger tg_inscripcion_validar before insert or update on formacion.inscripcion for each row execute function formacion.validar_inscripcion();

create or replace function formacion.certificar_inscripcion() returns trigger language plpgsql as $$
declare v_comp bigint;
begin
  if new.estado = 'aprobado' and (tg_op = 'INSERT' or old.estado <> 'aprobado') then
    select competencia_id into v_comp from formacion.curso where id = new.curso_id;
    if v_comp is not null then perform formacion.emitir_certificado(new.tercero_id, v_comp, new.nota, new.id, null); end if;
  end if;
  return null;
end $$;
create trigger tg_inscripcion_certificar after insert or update on formacion.inscripcion for each row execute function formacion.certificar_inscripcion();

create or replace function formacion.certificar_sesion(p_sesion bigint) returns integer language plpgsql as $$
declare v_comp bigint; v_min numeric; r record; v_n integer := 0;
begin
  select c.competencia_id, c.nota_minima into v_comp, v_min from formacion.sesion_presencial s join formacion.curso c on c.id = s.curso_id where s.id = p_sesion;
  if v_comp is null then return 0; end if;
  for r in select a.* from formacion.asistencia a where a.sesion_id = p_sesion and a.asistio and (a.nota is null or a.nota >= v_min)
             and not exists (select 1 from formacion.certificado c where c.sesion_id = p_sesion and c.tercero_id = a.tercero_id) loop
    perform formacion.emitir_certificado(r.tercero_id, v_comp, r.nota, null, p_sesion);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function formacion.certificar_sesion(bigint) is 'La asistencia a una sesión presencial cuenta igual que un curso virtual: emite los certificados';

create or replace function formacion.habilitar_desde_certificado() returns trigger language plpgsql as $$
begin
  insert into formacion.habilitacion (tercero_id, competencia_id, certificado_id, desde, hasta)
  values (new.tercero_id, new.competencia_id, new.id, new.emitido_en, new.vence_en);
  return null;
end $$;
create trigger tg_certificado_habilitar after insert on formacion.certificado for each row execute function formacion.habilitar_desde_certificado();

create or replace function formacion.actualizar_habilitaciones(p_fecha date default current_date) returns integer language plpgsql as $$
declare v_n integer;
begin
  update formacion.habilitacion set activa = false, retirada_en = now() where activa and hasta is not null and hasta < p_fecha;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
comment on function formacion.actualizar_habilitaciones(date) is 'Tarea diaria: un certificado vencido retira la habilitación (la regla de asignación ya la ignora desde el día siguiente al vencimiento)';

-- ============================================================================
-- 18. Activos: uso, órdenes de trabajo automáticas y depreciación
-- ============================================================================
create or replace function activos.sumar_uso() returns trigger language plpgsql as $$
begin
  update activos.activo set horometro = horometro + new.horas, odometro = odometro + new.km where id = new.activo_id;
  return null;
end $$;
create trigger tg_uso_activo_sumar after insert on activos.uso_activo for each row execute function activos.sumar_uso();

create or replace function activos.generar_ordenes_trabajo(p_fecha date default current_date) returns integer language plpgsql as $$
declare r record; v_tarea bigint; v_n integer := 0;
begin
  for r in select pm.*, a.nombre as activo_nombre, a.horometro, a.odometro from activos.plan_mantenimiento pm join activos.activo a on a.id = pm.activo_id
           where pm.activo and a.estado <> 'dado_de_baja'
             and ((pm.frecuencia_tipo = 'horas' and a.horometro - pm.ultima_lectura >= pm.frecuencia_valor)
               or (pm.frecuencia_tipo = 'km' and a.odometro - pm.ultima_lectura >= pm.frecuencia_valor)
               or (pm.frecuencia_tipo = 'dias' and coalesce(pm.ultima_fecha, a.fecha_compra, p_fecha) + pm.frecuencia_valor::integer <= p_fecha))
             and not exists (select 1 from activos.orden_trabajo o where o.plan_id = pm.id and o.estado in ('abierta', 'en_curso')) loop
    insert into personal.tarea (titulo, proceso, fecha, activo_id, origen, prioridad)
    values (r.nombre || ' · ' || r.activo_nombre, 'mantenimiento', p_fecha, r.activo_id, 'orden_trabajo', 'alta') returning id into v_tarea;
    insert into activos.orden_trabajo (activo_id, plan_id, tipo, descripcion, tarea_id)
    values (r.activo_id, r.id, r.tipo, r.nombre, v_tarea);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function activos.generar_ordenes_trabajo(date) is 'Tarea diaria: crea la orden de trabajo y su tarea cuando el plan vence por horas, kilómetros o días';

create or replace function activos.cerrar_orden() returns trigger language plpgsql as $$
declare v_lect numeric; v_tipo text;
begin
  if old.estado in ('cerrada', 'cancelada') then raise exception 'La orden % ya está %', old.id, old.estado; end if;
  if new.estado = 'cerrada' then
    new.cerrada_en := now();
    select case pm.frecuencia_tipo when 'km' then a.odometro else a.horometro end, pm.frecuencia_tipo into v_lect, v_tipo
    from activos.plan_mantenimiento pm join activos.activo a on a.id = pm.activo_id where pm.id = new.plan_id;
    update activos.plan_mantenimiento set ultima_lectura = coalesce(new.lectura_cierre, v_lect, 0), ultima_fecha = current_date where id = new.plan_id;
  end if;
  return new;
end $$;
create trigger tg_orden_trabajo_cerrar before update on activos.orden_trabajo for each row execute function activos.cerrar_orden();

create or replace function activos.depreciar_mes(p_mes date) returns integer language plpgsql as $$
declare v_mes date := date_trunc('month', p_mes)::date; v_n integer;
begin
  insert into activos.depreciacion (activo_id, mes, valor, acumulada)
  select a.id, v_mes, x.cuota, coalesce(prev.acum, 0) + x.cuota
  from activos.activo a
  left join lateral (select sum(d.valor) acum from activos.depreciacion d where d.activo_id = a.id and d.mes < v_mes) prev on true
  cross join lateral (select least(round((a.valor_compra - a.valor_residual) / a.vida_util_meses, 0),
                                   a.valor_compra - a.valor_residual - coalesce(prev.acum, 0)) as cuota) x
  where a.metodo_depreciacion = 'linea_recta' and a.valor_compra > 0 and a.vida_util_meses > 0 and a.estado <> 'dado_de_baja'
    and a.fecha_compra < v_mes + interval '1 month' and x.cuota > 0
  on conflict do nothing;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
comment on function activos.depreciar_mes(date) is 'Depreciación en línea recta del mes; se detiene al llegar al valor residual';

-- ============================================================================
-- 19. Documental: una sola versión aprobada vigente y lectura de los agentes
-- ============================================================================
create or replace function documental.validar_version() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and old.estado in ('aprobada', 'obsoleta') and (new.archivo_url <> old.archivo_url or new.hash_sha256 <> old.hash_sha256) then
    raise exception 'Una versión aprobada no cambia su archivo: cree una versión nueva';
  end if;
  if tg_op = 'UPDATE' and old.estado = 'obsoleta' and new.estado <> 'obsoleta' then raise exception 'Una versión obsoleta no vuelve a estar vigente'; end if;
  if new.estado = 'aprobada' and (tg_op = 'INSERT' or old.estado <> 'aprobada') then
    perform nucleo.exigir_persona('aprobar documentos');
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
    new.aprobada_en := now(); new.vigente_desde := coalesce(new.vigente_desde, current_date);
  end if;
  return new;
end $$;
create trigger tg_version_documento_validar before insert or update on documental.version_documento for each row execute function documental.validar_version();

create or replace function documental.obsoletar_anteriores() returns trigger language plpgsql as $$
begin
  if new.estado = 'aprobada' then
    update documental.version_documento set estado = 'obsoleta' where documento_id = new.documento_id and id <> new.id and estado = 'aprobada';
  end if;
  return null;
end $$;
create trigger tg_version_documento_obsoletar after insert or update of estado on documental.version_documento
  for each row execute function documental.obsoletar_anteriores();

create or replace view documental.v_vigentes as
select d.id as documento_id, d.codigo, d.titulo, d.tipo, d.uso_agentes, v.id as version_id, v.version, v.archivo_url, v.vigente_desde, v.vence_en,
       case when v.vence_en is null then 'vigente' when v.vence_en < current_date then 'vencido'
            when v.vence_en - v.avisar_dias <= current_date then 'por_vencer' else 'vigente' end as situacion
from documental.documento d join documental.version_documento v on v.documento_id = d.id and v.estado = 'aprobada';

create or replace function documental.documento_para_agente(p_documento bigint) returns varchar language plpgsql stable as $$
declare v record;
begin
  select * into v from documental.v_vigentes where documento_id = p_documento;
  if v is null or not v.uso_agentes or v.situacion = 'vencido' then
    raise exception 'El documento % no está aprobado, vigente y autorizado para agentes', p_documento;
  end if;
  return v.archivo_url;
end $$;
comment on function documental.documento_para_agente(bigint) is 'Los agentes (Instructor, Agrónomo) solo leen la versión aprobada y vigente de documentos autorizados';

-- ============================================================================
-- 20. Cumplimiento: evidencia automática, vencimientos y cierre de no conformidades
-- ============================================================================
create or replace function cumplimiento.validar_expediente() returns trigger language plpgsql as $$
declare v_funcion text;
begin
  select funcion_codigo into v_funcion from cumplimiento.norma where id = new.norma_id;
  if v_funcion is not null then perform nucleo.exigir_funcion(v_funcion); end if;
  return new;
end $$;
create trigger tg_expediente_validar before insert on cumplimiento.expediente for each row execute function cumplimiento.validar_expediente();

create or replace function cumplimiento.evaluar_expediente(p_expediente bigint) returns integer language plpgsql as $$
declare r record; v_ok boolean; v_vence date; v_tipo text; v_val text; v_no integer;
begin
  insert into cumplimiento.evaluacion_requisito (expediente_id, requisito_id)
  select p_expediente, q.id from cumplimiento.requisito q join cumplimiento.expediente e on e.norma_id = q.norma_id
  where e.id = p_expediente on conflict do nothing;
  for r in select ev.id, q.regla_evidencia, q.vigencia_dias from cumplimiento.evaluacion_requisito ev
           join cumplimiento.requisito q on q.id = ev.requisito_id where ev.expediente_id = p_expediente loop
    v_ok := null; v_vence := null;
    if r.regla_evidencia is not null then
      v_tipo := split_part(r.regla_evidencia, ':', 1); v_val := split_part(r.regla_evidencia, ':', 2);
      if v_tipo = 'competencia' then
        select count(*) > 0, min(h.hasta) into v_ok, v_vence from formacion.habilitacion h join formacion.competencia c on c.id = h.competencia_id
        where c.codigo = v_val and h.activa and (h.hasta is null or h.hasta >= current_date);
      elsif v_tipo = 'documento' then
        select count(*) > 0, min(vence_en) into v_ok, v_vence from documental.v_vigentes where tipo = v_val and situacion <> 'vencido';
      elsif v_tipo = 'registro' and to_regclass(v_val) is not null then
        execute format('select count(*) > 0 from %s where creado_en >= now() - make_interval(days => %s)', v_val, coalesce(r.vigencia_dias, 365)) into v_ok;
      end if;
    end if;
    -- Evidencias cargadas a mano: si todas vencieron, el requisito deja de cumplirse
    if v_ok is null and exists (select 1 from cumplimiento.evidencia_requisito where evaluacion_id = r.id) then
      select bool_or(vence_en is null or vence_en >= current_date), min(vence_en) filter (where vence_en >= current_date) into v_ok, v_vence
      from cumplimiento.evidencia_requisito where evaluacion_id = r.id;
    end if;
    if v_ok is not null then
      update cumplimiento.evaluacion_requisito set estado = case when v_ok then 'cumple' else 'no_cumple' end, origen = 'automatica',
             evaluado_en = now(), vence_en = v_vence where id = r.id and estado <> 'no_aplica';
    end if;
  end loop;
  select count(*) into v_no from cumplimiento.evaluacion_requisito where expediente_id = p_expediente and estado <> 'cumple' and estado <> 'no_aplica';
  return v_no;
end $$;
comment on function cumplimiento.evaluar_expediente(bigint) is 'Tarea diaria: revisa cada requisito contra su evidencia (habilitaciones, documentos vigentes, registros recientes); lo vencido pasa a no cumple. Devuelve cuántos faltan';

create or replace function cumplimiento.cerrar_no_conformidad() returns trigger language plpgsql as $$
begin
  if old.estado = 'cerrada' then raise exception 'La no conformidad % ya está cerrada', old.id; end if;
  if new.estado = 'cerrada' then
    perform nucleo.exigir_persona('cerrar no conformidades');
    if new.verificacion is null then raise exception 'Para cerrar una no conformidad hay que registrar la verificación'; end if;
    if not exists (select 1 from cumplimiento.accion_correctiva where no_conformidad_id = new.id and estado = 'verificada')
       or exists (select 1 from cumplimiento.accion_correctiva where no_conformidad_id = new.id and estado in ('pendiente', 'hecha')) then
      raise exception 'Una no conformidad no se cierra sin todas sus acciones correctivas verificadas';
    end if;
    new.cerrada_por := coalesce(new.cerrada_por, nucleo.usuario_actual()); new.cerrada_en := now();
  end if;
  return new;
end $$;
create trigger tg_no_conformidad_cerrar before update on cumplimiento.no_conformidad for each row execute function cumplimiento.cerrar_no_conformidad();

create or replace function cumplimiento.verificar_accion() returns trigger language plpgsql as $$
begin
  if new.estado = 'verificada' and old.estado <> 'verificada' then
    perform nucleo.exigir_persona('verificar acciones correctivas');
    new.verificada_por := coalesce(new.verificada_por, nucleo.usuario_actual()); new.verificada_en := now();
    if old.estado <> 'hecha' then raise exception 'Solo se verifica una acción hecha'; end if;
  end if;
  return new;
end $$;
create trigger tg_accion_correctiva_verificar before update on cumplimiento.accion_correctiva for each row execute function cumplimiento.verificar_accion();

create or replace view cumplimiento.v_granja_biosegura as
select (select coalesce(sum(l.cantidad_actual), 0) from produccion.lote_animal l join produccion.especie e on e.id = l.especie_id
        where e.grupo = 'ave' and l.estado = 'activo' and l.proposito in ('postura', 'cria')) as aves_postura_levante,
       200 as umbral_obligatorio,
       (select x.estado from cumplimiento.expediente x join cumplimiento.norma n on n.id = x.norma_id where n.codigo = 'ICA_GAB') as estado_expediente,
       (select x.rspa_numero from cumplimiento.expediente x join cumplimiento.norma n on n.id = x.norma_id where n.codigo = 'ICA_GAB') as rspa,
       case when (select coalesce(sum(l.cantidad_actual), 0) from produccion.lote_animal l join produccion.especie e on e.id = l.especie_id
                  where e.grupo = 'ave' and l.estado = 'activo' and l.proposito in ('postura', 'cria')) >= 200
             and coalesce((select x.estado from cumplimiento.expediente x join cumplimiento.norma n on n.id = x.norma_id where n.codigo = 'ICA_GAB'), '') <> 'certificado'
            then 'alerta: 200 aves o más sin certificado de granja avícola biosegura' else 'en regla' end as situacion;
comment on view cumplimiento.v_granja_biosegura is 'Resolución ICA 3651 de 2014: postura o levante desde 200 aves exige certificado de granja avícola biosegura';

-- ============================================================================
-- 21. Seguros: subsidio, avisos de siniestro revisados por una persona e índice paramétrico
-- ============================================================================
create or replace function seguros.preparar_poliza() returns trigger language plpgsql as $$
begin
  if new.valor_subsidiado = 0 and new.incentivo_pct > 0 then new.valor_subsidiado := round(new.prima * new.incentivo_pct / 100, 0); end if;
  if new.tipo = 'parametrico' then perform nucleo.exigir_funcion('seguro_parametrico'); end if;
  return new;
end $$;
create trigger tg_poliza_preparar before insert or update on seguros.poliza for each row execute function seguros.preparar_poliza();

create or replace view seguros.v_por_vencer as
select p.id, p.numero, p.tipo, p.hasta, p.hasta - current_date as dias_para_vencer
from seguros.poliza p where p.estado = 'vigente' and p.hasta - p.avisar_dias <= current_date;

create or replace function seguros.validar_aviso() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' and (new.indice_id is not null or (select tipo from seguros.poliza where id = new.poliza_id) = 'parametrico') then
    perform nucleo.exigir_funcion('seguro_parametrico');
    if new.serie_datos is null then raise exception 'Un aviso paramétrico guarda la serie de datos usada como evidencia'; end if;
  end if;
  if tg_op = 'UPDATE' and new.estado <> old.estado then
    if new.estado = 'revisado' then
      perform nucleo.exigir_persona('revisar avisos de siniestro');
      new.revisado_por := coalesce(new.revisado_por, nucleo.usuario_actual());
    elsif new.estado = 'enviado' then
      perform nucleo.exigir_persona('enviar avisos de siniestro');
      if old.estado <> 'revisado' then raise exception 'No hay reclamación automática: el aviso se revisa antes de enviarlo'; end if;
      new.enviado_en := now();
    end if;
  end if;
  return new;
end $$;
create trigger tg_aviso_siniestro_validar before insert or update on seguros.aviso_siniestro for each row execute function seguros.validar_aviso();

create or replace function seguros.vigilar_indice(p_indice bigint, p_hasta date default current_date) returns bigint language plpgsql as $$
declare i seguros.indice_poliza; v_valor numeric; v_serie jsonb; v_id bigint;
begin
  perform nucleo.exigir_funcion('seguro_parametrico');
  select * into i from seguros.indice_poliza where id = p_indice;
  if i.sensor_id is null then return null; end if;
  select case when i.variable in ('lluvia_mm', 'dias_secos') then sum(v) else avg(v) end,
         jsonb_agg(jsonb_build_object('dia', d, 'valor', round(v::numeric, 2)) order by d)
    into v_valor, v_serie
  from (select date_trunc('day', medido_en)::date d,
               case when i.variable = 'lluvia_mm' then sum(valor) when i.variable = 'dias_secos' then case when sum(valor) < 1 then 1 else 0 end else avg(valor) end v
        from iot.lectura where sensor_id = i.sensor_id and medido_en >= p_hasta - i.ventana_dias and medido_en < p_hasta + 1 group by 1) x;
  if v_valor is null or not ((i.comparador = 'mayor' and v_valor > i.umbral) or (i.comparador = 'menor' and v_valor < i.umbral)) then return null; end if;
  insert into seguros.aviso_siniestro (poliza_id, indice_id, detectado_en, descripcion, serie_datos)
  values (i.poliza_id, i.id, now(), format('La estación propia marca %s = %s en %s días (umbral %s %s). Verificar con la fuente oficial: %s',
          i.variable, round(v_valor, 1), i.ventana_dias, i.comparador, i.umbral, i.fuente_oficial), v_serie)
  returning id into v_id;
  return v_id;
end $$;
comment on function seguros.vigilar_indice(bigint, date) is 'Compara la estación de la finca con el índice de la póliza; si parece cumplirse, deja un aviso en borrador para que una persona lo revise. El pago lo define el índice oficial de la aseguradora';

-- ============================================================================
-- 22. IA y finanzas ampliadas: diagnóstico revisado, anticipos, costos, estados financieros e indicadores
-- ============================================================================
create or replace function ia.validar_diagnostico() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then perform nucleo.exigir_funcion('diagnostico_imagen'); return new; end if;
  if old.estado <> 'pendiente' then raise exception 'El diagnóstico % ya fue revisado', old.id; end if;
  if new.estado <> 'pendiente' then
    perform nucleo.exigir_persona('confirmar diagnósticos');
    new.revisado_por := coalesce(new.revisado_por, nucleo.usuario_actual()); new.revisado_en := now();
    if new.estado = 'confirmado' then new.diagnostico_final := coalesce(new.diagnostico_final, new.diagnostico_propuesto); end if;
    if new.estado = 'corregido' and new.diagnostico_final is null then raise exception 'Al corregir indique el diagnóstico final'; end if;
  end if;
  return new;
end $$;
create trigger tg_diagnostico_validar before insert or update on ia.diagnostico_imagen for each row execute function ia.validar_diagnostico();

create or replace function ia.validar_decision() returns trigger language plpgsql as $$
begin
  if new.opcion_elegida is not null and (tg_op = 'INSERT' or old.opcion_elegida is null) then
    perform nucleo.exigir_persona('tomar decisiones');
    new.decidido_por := coalesce(new.decidido_por, nucleo.usuario_actual()); new.decidido_en := now();
  end if;
  if tg_op = 'UPDATE' and old.opcion_elegida is not null and new.opcion_elegida is distinct from old.opcion_elegida then
    raise exception 'Una decisión tomada no se cambia: registre una decisión nueva';
  end if;
  return new;
end $$;
create trigger tg_decision_validar before insert or update on ia.decision for each row execute function ia.validar_decision();

create or replace function finanzas.preparar_anticipo() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then new.saldo := new.valor; end if;
  if new.saldo = 0 and new.estado = 'abierto' then new.estado := 'aplicado'; end if;
  return new;
end $$;
create trigger tg_anticipo_preparar before insert or update on finanzas.anticipo_proveedor for each row execute function finanzas.preparar_anticipo();

create or replace function finanzas.aplicar_anticipo() returns trigger language plpgsql as $$
declare a finanzas.anticipo_proveedor;
begin
  select * into a from finanzas.anticipo_proveedor where id = new.anticipo_id for update;
  if a.estado <> 'abierto' then raise exception 'El anticipo % está %', a.id, a.estado; end if;
  if (select proveedor_id from compras.orden_compra where id = new.orden_compra_id) <> a.proveedor_id then
    raise exception 'El anticipo es de otro proveedor';
  end if;
  if new.valor > a.saldo then raise exception 'El anticipo solo tiene saldo de % (se intentó descontar %)', a.saldo, new.valor; end if;
  update finanzas.anticipo_proveedor set saldo = saldo - new.valor where id = a.id;
  return new;
end $$;
create trigger tg_aplicacion_anticipo before insert on finanzas.aplicacion_anticipo for each row execute function finanzas.aplicar_anticipo();
create trigger tg_aplicacion_anticipo_inmutable before update or delete on finanzas.aplicacion_anticipo for each row execute function nucleo.impedir_cambio();

create or replace function finanzas.validar_clasificacion() returns trigger language plpgsql as $$
begin
  if new.comportamiento = 'semivariable' and new.parte_fija_pct is null then raise exception 'Un costo semivariable necesita su parte fija (%%)'; end if;
  if new.comportamiento in ('fijo', 'variable') then new.parte_fija_pct := case new.comportamiento when 'fijo' then 100 else 0 end; end if;
  return new;
end $$;
create trigger tg_clasificacion_costo_validar before insert or update on finanzas.clasificacion_costo for each row execute function finanzas.validar_clasificacion();

create or replace function finanzas.validar_presupuesto_detalle() returns trigger language plpgsql as $$
declare p finanzas.presupuesto;
begin
  select * into p from finanzas.presupuesto where id = coalesce(new.presupuesto_id, old.presupuesto_id);
  if p.estado <> 'borrador' then raise exception 'El presupuesto % está %: no se cambian sus rubros (cree una versión nueva)', p.nombre, p.estado; end if;
  if tg_op <> 'DELETE' and p.base_cero and new.justificacion is null then raise exception 'En presupuesto base cero cada rubro se justifica'; end if;
  return coalesce(new, old);
end $$;
create trigger tg_presupuesto_detalle_validar before insert or update or delete on finanzas.presupuesto_detalle for each row execute function finanzas.validar_presupuesto_detalle();

-- Saldos por cuenta (PUC colombiano: 1 activo, 2 pasivo, 3 patrimonio, 4 ingresos, 5 gastos, 6 costo de ventas, 7 costo de producción)
create or replace function finanzas.saldo(p_prefijo text, p_desde date, p_hasta date, p_centro bigint default null) returns numeric language sql stable as $$
  select coalesce(sum(case when left(c.codigo, 1) in ('1', '5', '6', '7') then m.debito - m.credito else m.credito - m.debito end), 0)
  from finanzas.movimiento_contable m join finanzas.comprobante k on k.id = m.comprobante_id join finanzas.cuenta_contable c on c.id = m.cuenta_id
  where k.estado = 'contabilizado' and c.codigo like p_prefijo || '%' and k.fecha between coalesce(p_desde, '1900-01-01') and p_hasta
    and (p_centro is null or m.centro_costo_id = p_centro) $$;
comment on function finanzas.saldo(text, date, date, bigint) is 'Saldo de las cuentas que empiezan por el prefijo según la naturaleza de su clase (así la depreciación acumulada resta del activo); sin fecha inicial = acumulado (balance)';

create or replace function finanzas.costo_por_comportamiento(p_desde date, p_hasta date, p_variable boolean, p_centro bigint default null)
returns numeric language sql stable as $$
  select coalesce(sum((m.debito - m.credito) * case when p_variable then 1 - coalesce(cc.parte_fija_pct, 100) / 100 else coalesce(cc.parte_fija_pct, 100) / 100 end), 0)
  from finanzas.movimiento_contable m join finanzas.comprobante k on k.id = m.comprobante_id join finanzas.cuenta_contable c on c.id = m.cuenta_id
  left join finanzas.clasificacion_costo cc on cc.cuenta_id = c.id
  where k.estado = 'contabilizado' and k.fecha between p_desde and p_hasta and left(c.codigo, 1) in ('5', '6')
    and c.codigo not like '53%' and c.codigo not like '54%' and (p_centro is null or m.centro_costo_id = p_centro) $$;
comment on function finanzas.costo_por_comportamiento(date, date, boolean, bigint) is 'Costos y gastos operacionales variables o fijos según su clasificación; lo no clasificado se trata como fijo (prudente)';

create or replace function finanzas.estado_resultados(p_desde date, p_hasta date, p_centro bigint default null) returns jsonb language plpgsql stable as $$
declare v_ing numeric; v_var numeric; v_fij numeric; v_mc numeric; v_uo numeric; v_noi numeric; v_noe numeric; v_int numeric; v_tx numeric; v_un numeric; v_dep numeric;
begin
  v_ing := finanzas.saldo('41', p_desde, p_hasta, p_centro);
  v_var := finanzas.costo_por_comportamiento(p_desde, p_hasta, true, p_centro);
  v_fij := finanzas.costo_por_comportamiento(p_desde, p_hasta, false, p_centro);
  v_mc := v_ing - v_var; v_uo := v_mc - v_fij;
  v_noi := finanzas.saldo('42', p_desde, p_hasta, p_centro);
  v_noe := finanzas.saldo('53', p_desde, p_hasta, p_centro);
  v_int := finanzas.saldo('5305', p_desde, p_hasta, p_centro);
  v_tx := finanzas.saldo('54', p_desde, p_hasta, p_centro);
  v_dep := finanzas.saldo('5160', p_desde, p_hasta, p_centro) + finanzas.saldo('5260', p_desde, p_hasta, p_centro);
  v_un := v_uo + v_noi - v_noe - v_tx;
  return jsonb_build_object('ingresos_operacionales', v_ing, 'costos_gastos_variables', v_var, 'margen_contribucion', v_mc,
    'costos_gastos_fijos', v_fij, 'utilidad_operacional', v_uo, 'ingresos_no_operacionales', v_noi, 'gastos_no_operacionales', v_noe,
    'intereses', v_int, 'utilidad_antes_impuestos', v_uo + v_noi - v_noe, 'impuestos', v_tx, 'utilidad_neta', v_un,
    'depreciacion', v_dep, 'ebitda', v_uo + v_dep,
    'costo_ventas', finanzas.saldo('6', p_desde, p_hasta, p_centro), 'utilidad_bruta', v_ing - finanzas.saldo('6', p_desde, p_hasta, p_centro));
end $$;
comment on function finanzas.estado_resultados(date, date, bigint) is 'Estado de resultados por costeo variable (margen de contribución, utilidad operacional, neta y EBITDA), total o por centro de costo';

create or replace function finanzas.balance_general(p_hasta date) returns jsonb language plpgsql stable as $$
declare v jsonb; v_ac numeric; v_anc numeric; v_pc numeric; v_pt numeric; v_pat numeric; v_res numeric;
begin
  -- La clase 7 (costos de producción) se trata como producción en proceso hasta trasladarse al inventario
  v_ac := finanzas.saldo('11', null, p_hasta) + finanzas.saldo('12', null, p_hasta) + finanzas.saldo('13', null, p_hasta) + finanzas.saldo('14', null, p_hasta)
        + finanzas.saldo('7', null, p_hasta);
  v_anc := finanzas.saldo('15', null, p_hasta) + finanzas.saldo('16', null, p_hasta) + finanzas.saldo('17', null, p_hasta) + finanzas.saldo('18', null, p_hasta) + finanzas.saldo('19', null, p_hasta);
  v_pt := finanzas.saldo('2', null, p_hasta);
  v_pc := v_pt - finanzas.saldo('27', null, p_hasta) - finanzas.saldo('29', null, p_hasta);
  v_res := finanzas.saldo('4', null, p_hasta) - finanzas.saldo('5', null, p_hasta) - finanzas.saldo('6', null, p_hasta);
  v_pat := finanzas.saldo('3', null, p_hasta) + v_res;
  return jsonb_build_object('disponible', finanzas.saldo('11', null, p_hasta), 'deudores', finanzas.saldo('13', null, p_hasta),
    'inventarios', finanzas.saldo('14', null, p_hasta), 'activo_corriente', v_ac, 'activo_no_corriente', v_anc, 'activo_total', v_ac + v_anc,
    'obligaciones_financieras', finanzas.saldo('21', null, p_hasta), 'pasivo_corriente', v_pc, 'pasivo_total', v_pt,
    'patrimonio', v_pat, 'resultado_ejercicio', v_res, 'utilidades_retenidas', finanzas.saldo('37', null, p_hasta),
    'cuadra', (v_ac + v_anc) = (v_pt + v_pat));
end $$;
comment on function finanzas.balance_general(date) is 'Balance general a una fecha: activo = pasivo + patrimonio (el resultado del ejercicio entra al patrimonio)';

create or replace function finanzas.palancas(p_unidades numeric, p_precio numeric, p_cv_unitario numeric, p_costos_fijos numeric, p_intereses numeric default 0)
returns table (margen_contribucion numeric, utilidad_operacional numeric, punto_equilibrio_unidades numeric, margen_seguridad_pct numeric,
               gpo numeric, gpf numeric, gpt numeric) language sql immutable as $$
  select mc, uo, case when p_precio > p_cv_unitario then round(p_costos_fijos / (p_precio - p_cv_unitario), 2) end,
         case when p_unidades > 0 and p_precio > p_cv_unitario then round((p_unidades - p_costos_fijos / (p_precio - p_cv_unitario)) / p_unidades * 100, 2) end,
         case when uo <> 0 then round(mc / uo, 4) end,
         case when uo - p_intereses <> 0 then round(uo / (uo - p_intereses), 4) end,
         case when uo - p_intereses <> 0 then round(mc / (uo - p_intereses), 4) end
  from (select p_unidades * (p_precio - p_cv_unitario) mc, p_unidades * (p_precio - p_cv_unitario) - p_costos_fijos uo) x $$;
comment on function finanzas.palancas(numeric, numeric, numeric, numeric, numeric) is 'Modelo costo-volumen-utilidad y teoría de las palancas: PE = CF/(P-CV), margen de seguridad, GPO = MC/UO, GPF = UO/(UO-I), GPT = GPO×GPF';

create or replace function finanzas.distribuir_costos(p_mes date) returns integer language plpgsql as $$
declare v_mes date := date_trunc('month', p_mes)::date; v_n integer;
begin
  update finanzas.asignacion_costo ac set valor_asignado = round(x.costo * ac.cantidad_inductor / nullif(x.total_inductor, 0), 0)
  from (select a.id actividad_id, sum(ac2.cantidad_inductor) total_inductor,
               finanzas.saldo('5', v_mes, (v_mes + interval '1 month - 1 day')::date, a.centro_costo_id)
             + finanzas.saldo('7', v_mes, (v_mes + interval '1 month - 1 day')::date, a.centro_costo_id) costo
        from finanzas.actividad_costo a join finanzas.asignacion_costo ac2 on ac2.actividad_id = a.id and ac2.mes = v_mes group by a.id, a.centro_costo_id) x
  where ac.actividad_id = x.actividad_id and ac.mes = v_mes;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
comment on function finanzas.distribuir_costos(date) is 'Costeo basado en actividades: reparte el costo del centro de servicio de cada actividad según el inductor consumido por cada línea';

create or replace function finanzas.calcular_indicadores(p_desde date, p_hasta date) returns integer language plpgsql as $$
declare er jsonb := finanzas.estado_resultados(p_desde, p_hasta); bg jsonb := finanzas.balance_general(p_hasta);
        v_dias numeric := p_hasta - p_desde + 1; v jsonb; r record; v_meta numeric; v_n integer := 0; v_sem text;
        ing numeric; uo numeric; un numeric; mc numeric; intr numeric; tot_act numeric; pat numeric; pt numeric; ac numeric; pc numeric;
        kc numeric := nucleo.parametro_valor('costo_capital_anual_pct', p_hasta); tx numeric := nucleo.parametro_valor('tarifa_renta_pct', p_hasta);
begin
  ing := (er->>'ingresos_operacionales')::numeric; uo := (er->>'utilidad_operacional')::numeric; un := (er->>'utilidad_neta')::numeric;
  mc := (er->>'margen_contribucion')::numeric; intr := (er->>'intereses')::numeric;
  tot_act := (bg->>'activo_total')::numeric; pat := (bg->>'patrimonio')::numeric; pt := (bg->>'pasivo_total')::numeric;
  ac := (bg->>'activo_corriente')::numeric; pc := (bg->>'pasivo_corriente')::numeric;
  v := jsonb_build_object(
    'capital_trabajo', ac - pc,
    'razon_corriente', ac / nullif(pc, 0),
    'prueba_acida', (ac - (bg->>'inventarios')::numeric) / nullif(pc, 0),
    'endeudamiento', pt / nullif(tot_act, 0) * 100,
    'apalancamiento', tot_act / nullif(pat, 0),
    'cobertura_intereses', uo / nullif(intr, 0),
    'margen_bruto', (er->>'utilidad_bruta')::numeric / nullif(ing, 0) * 100,
    'margen_operacional', uo / nullif(ing, 0) * 100,
    'margen_neto', un / nullif(ing, 0) * 100,
    'ebitda', (er->>'ebitda')::numeric,
    'rsa', un / nullif(tot_act, 0) * 100,
    'rsp', un / nullif(pat, 0) * 100,
    'rotacion_activos', ing / nullif(tot_act, 0),
    'dias_cartera', (bg->>'deudores')::numeric / nullif(ing, 0) * v_dias,
    'dias_inventario', (bg->>'inventarios')::numeric / nullif((er->>'costo_ventas')::numeric, 0) * v_dias,
    'gpo', mc / nullif(uo, 0),
    'gpf', uo / nullif(uo - intr, 0),
    'gpt', mc / nullif(uo - intr, 0),
    'punto_equilibrio_pesos', (er->>'costos_gastos_fijos')::numeric / nullif(mc / nullif(ing, 0), 0),
    'margen_seguridad', (ing - (er->>'costos_gastos_fijos')::numeric / nullif(mc / nullif(ing, 0), 0)) / nullif(ing, 0) * 100,
    'eva', case when kc is not null then uo * (1 - coalesce(tx, 0) / 100) - (pat + (bg->>'obligaciones_financieras')::numeric) * kc / 100 * v_dias / 365 end,
    'altman_z2', 6.56 * (ac - pc) / nullif(tot_act, 0) + 3.26 * (bg->>'utilidades_retenidas')::numeric / nullif(tot_act, 0)
               + 6.72 * uo / nullif(tot_act, 0) + 1.05 * pat / nullif(pt, 0));
  for r in select i.id, i.codigo, i.sentido from finanzas.indicador i where v ? i.codigo loop
    select o.meta into v_meta from estrategia.objetivo o where o.indicador_id = r.id order by o.fecha_meta desc nulls last limit 1;
    v_sem := case when v->>r.codigo is null then 'sin_dato' when v_meta is null then 'sin_meta'
                  when r.sentido = 'mayor_mejor' then case when (v->>r.codigo)::numeric >= v_meta then 'verde' when (v->>r.codigo)::numeric >= v_meta * 0.9 then 'amarillo' else 'rojo' end
                  when r.sentido = 'menor_mejor' then case when (v->>r.codigo)::numeric <= v_meta then 'verde' when (v->>r.codigo)::numeric <= v_meta * 1.1 then 'amarillo' else 'rojo' end
                  else 'sin_meta' end;
    insert into finanzas.valor_indicador (indicador_id, desde, hasta, valor, meta, semaforo)
    values (r.id, p_desde, p_hasta, round((v->>r.codigo)::numeric, 4), v_meta, v_sem);
    v_n := v_n + 1;
  end loop;
  return v_n;
end $$;
comment on function finanzas.calcular_indicadores(date, date) is 'Calcula los indicadores financieros del periodo desde la contabilidad (liquidez, endeudamiento, rentabilidad, actividad, palancas, EVA, Z de Altman para empresas no manufactureras) con semáforo contra la meta';

create or replace function finanzas.validar_reporte_indicadores() returns trigger language plpgsql as $$
begin
  perform nucleo.exigir_funcion('indicadores_credito');
  perform nucleo.exigir_persona('autorizar el envío de indicadores');
  if new.contenido ?| array['costo', 'costos', 'costo_unitario', 'salario', 'telefono', 'correo', 'documento', 'numero_documento', 'clientes'] then
    raise exception 'El informe de indicadores no lleva costos ni datos personales';
  end if;
  new.hash_sha256 := encode(sha256(convert_to(new.contenido::text, 'UTF8')), 'hex');
  return new;
end $$;
create trigger tg_reporte_indicadores_validar before insert on finanzas.reporte_indicadores for each row execute function finanzas.validar_reporte_indicadores();
create trigger tg_reporte_indicadores_inmutable before update or delete on finanzas.reporte_indicadores for each row execute function nucleo.impedir_cambio();

-- ============================================================================
-- 23. Robótica, energía e integraciones externas (todas encendidas por función)
-- ============================================================================
create or replace function iot.validar_mision() returns trigger language plpgsql as $$
declare v_tipo_activo text; v_reg text;
begin
  select tipo, registro_aerocivil into v_tipo_activo, v_reg from activos.activo where id = new.activo_id;
  if tg_op = 'INSERT' then
    if new.tipo = 'dron_monitoreo' then
      perform nucleo.exigir_funcion('dron_monitoreo');
      if v_tipo_activo <> 'dron' then raise exception 'La misión de dron necesita un activo tipo dron'; end if;
    else
      perform nucleo.exigir_funcion('robot_campo');
      if v_tipo_activo <> 'robot' then raise exception 'La misión de robot necesita un activo tipo robot'; end if;
    end if;
    return new;
  end if;
  if old.estado in ('terminada', 'abortada') then raise exception 'La misión % ya terminó', old.id; end if;
  if new.estado = 'aprobada' and old.estado = 'propuesta' then
    perform nucleo.exigir_persona('aprobar misiones de robots o drones');
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
  end if;
  if new.estado = 'en_curso' and old.estado <> 'en_curso' then
    if old.estado <> 'aprobada' then raise exception 'Una misión solo arranca aprobada por una persona'; end if;
    if new.tipo = 'dron_monitoreo' then
      if v_reg is null then raise exception 'El dron no tiene registro ante la Aerocivil (RAC 100)'; end if;
      if new.piloto_id is null then raise exception 'El vuelo necesita piloto'; end if;
      if coalesce(new.altura_max_m, 999) > 122 then raise exception 'RAC 100: la altura máxima es 122 m'; end if;
      if not exists (select 1 from seguros.poliza p where p.id = new.poliza_id and p.estado = 'vigente' and current_date between p.desde and p.hasta
                     and p.tipo in ('responsabilidad_civil', 'dron')) then
        raise exception 'El vuelo necesita póliza de responsabilidad civil vigente';
      end if;
    else
      if not new.zona_sin_personas or not new.parada_emergencia_probada then
        raise exception 'El robot solo opera en una zona sin personas y con la parada de emergencia probada';
      end if;
    end if;
    new.inicio := coalesce(new.inicio, now());
  end if;
  if new.estado in ('terminada', 'abortada') then new.fin := coalesce(new.fin, now()); end if;
  return new;
end $$;
create trigger tg_mision_robot_validar before insert or update on iot.mision_robot for each row execute function iot.validar_mision();

create or replace function iot.cargas_a_cortar(p_bateria_pct numeric) returns table (actuador_id bigint, prioridad smallint) language sql stable as $$
  select actuador_id, prioridad from iot.prioridad_carga where not esencial and corte_bateria_pct is not null and p_bateria_pct <= corte_bateria_pct
  order by prioridad desc $$;
comment on function iot.cargas_a_cortar(numeric) is 'Con batería baja, cargas no esenciales a cortar de la menos a la más importante; alarma, nevera y agua de animales nunca se cortan';

create or replace function nucleo.validar_llave_api() returns trigger language plpgsql as $$
begin
  if new.activa then
    perform nucleo.exigir_funcion('api_b2b');
    if new.vence_en <= current_date then raise exception 'La llave está vencida'; end if;
    if not exists (select 1 from terceros.cliente where tercero_id = new.tercero_id) then raise exception 'Solo un cliente tiene llave de la API B2B'; end if;
    if not new.alcances <@ array['catalogo:leer', 'pedidos:leer', 'pedidos:crear'] then raise exception 'Alcance no permitido en la API B2B'; end if;
  end if;
  return new;
end $$;
create trigger tg_llave_api_validar before insert or update on nucleo.llave_api for each row execute function nucleo.validar_llave_api();

create or replace function nucleo.autenticar_llave_api(p_prefijo text, p_hash text, p_ip inet) returns bigint language plpgsql as $$
declare v nucleo.llave_api;
begin
  if exists (select 1 from seguridad.senuelo where tipo = 'llave_api' and valor = p_prefijo and activo) then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, ip, predio_id, detalle)
    values ('senuelo', 'critica', 'api', p_ip, nucleo.predio_actual(), jsonb_build_object('llave', p_prefijo));
    insert into seguridad.bloqueo (tipo, ip, motivo, hasta) values ('ip', p_ip::cidr, 'Usó una llave señuelo', now() + interval '24 hours');
    return null;
  end if;
  select * into v from nucleo.llave_api where prefijo = p_prefijo and hash_llave = p_hash and activa and vence_en > current_date;
  if v.id is null then return null; end if;
  update nucleo.llave_api set ultimo_uso = now() where id = v.id;
  return v.tercero_id;
end $$;

create or replace function nucleo.validar_webhook() returns trigger language plpgsql as $$
begin
  if new.activa then perform nucleo.exigir_funcion('webhooks_salientes'); end if;
  if new.fallos_seguidos >= 10 then new.activa := false; end if;
  return new;
end $$;
create trigger tg_webhook_validar before insert or update on nucleo.webhook_suscripcion for each row execute function nucleo.validar_webhook();

-- ============================================================================
-- 24. Seguridad informática: detector de ataques, señuelos, doble factor y alertas
-- ============================================================================
create or replace function seguridad.regla(p_codigo text) returns seguridad.regla_deteccion language sql stable as $$
  select * from seguridad.regla_deteccion where codigo = p_codigo and activa $$;

create or replace function seguridad.ip_bloqueada(p_ip inet) returns boolean language sql stable as $$
  select exists (select 1 from seguridad.bloqueo where tipo = 'ip' and p_ip <<= ip and levantado_por is null and (hasta is null or hasta > now())) $$;
create or replace function seguridad.cuenta_bloqueada(p_usuario bigint) returns boolean language sql stable as $$
  select exists (select 1 from seguridad.bloqueo where tipo = 'cuenta' and usuario_id = p_usuario and levantado_por is null and (hasta is null or hasta > now())) $$;

create or replace function seguridad.registrar_intento(p_correo text, p_ip inet, p_exito boolean, p_motivo text default null, p_agente_usuario text default null)
returns text language plpgsql as $$
declare v_usr bigint; r seguridad.regla_deteccion; v_n integer;
begin
  if seguridad.ip_bloqueada(p_ip) then
    insert into seguridad.intento_acceso (correo, ip, exito, motivo_fallo, agente_usuario) values (p_correo, p_ip, false, 'ip_bloqueada', p_agente_usuario);
    return 'ip_bloqueada';
  end if;
  if exists (select 1 from seguridad.senuelo where tipo = 'cuenta' and lower(valor) = lower(p_correo) and activo) then
    insert into seguridad.intento_acceso (correo, ip, exito, motivo_fallo, agente_usuario) values (p_correo, p_ip, false, 'senuelo', p_agente_usuario);
    r := seguridad.regla('senuelo');
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, ip, detalle)
    values ('senuelo', 'critica', 'app', r.id, p_ip, jsonb_build_object('correo', p_correo));
    insert into seguridad.bloqueo (tipo, ip, regla_id, motivo, hasta)
    values ('ip', p_ip::cidr, r.id, 'Intentó entrar con una cuenta señuelo', now() + make_interval(mins => coalesce(r.bloqueo_min, 1440)));
    return 'senuelo';
  end if;
  select id into v_usr from nucleo.usuario where correo = p_correo;
  if v_usr is not null and seguridad.cuenta_bloqueada(v_usr) then
    insert into seguridad.intento_acceso (correo, usuario_id, ip, exito, motivo_fallo, agente_usuario) values (p_correo, v_usr, p_ip, false, 'cuenta_bloqueada', p_agente_usuario);
    return 'cuenta_bloqueada';
  end if;
  insert into seguridad.intento_acceso (correo, usuario_id, ip, exito, motivo_fallo, agente_usuario)
  values (p_correo, v_usr, p_ip, p_exito, case when not p_exito then coalesce(p_motivo, case when v_usr is null then 'usuario_inexistente' else 'contrasena' end) end, p_agente_usuario);
  if p_exito then return 'permitido'; end if;
  -- Fuerza bruta contra una cuenta
  r := seguridad.regla('fuerza_bruta_cuenta');
  if r.id is not null and v_usr is not null then
    select count(*) into v_n from seguridad.intento_acceso where correo = p_correo and not exito and ocurrido_en > now() - make_interval(mins => r.ventana_min);
    if v_n >= r.umbral then
      insert into seguridad.bloqueo (tipo, usuario_id, regla_id, motivo, hasta) values ('cuenta', v_usr, r.id, format('%s intentos fallidos en %s minutos', v_n, r.ventana_min), now() + make_interval(mins => r.bloqueo_min));
      insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, usuario_id, ip, detalle)
      values ('fuerza_bruta', r.severidad, 'app', r.id, v_usr, p_ip, jsonb_build_object('intentos', v_n));
      return 'cuenta_bloqueada_ahora';
    end if;
  end if;
  -- Relleno de credenciales: muchas cuentas distintas desde la misma IP
  r := seguridad.regla('relleno_credenciales');
  if r.id is not null then
    select count(distinct correo) into v_n from seguridad.intento_acceso where ip = p_ip and not exito and ocurrido_en > now() - make_interval(mins => r.ventana_min);
    if v_n >= r.umbral then
      insert into seguridad.bloqueo (tipo, ip, regla_id, motivo, hasta) values ('ip', p_ip::cidr, r.id, format('%s cuentas distintas fallidas en %s minutos', v_n, r.ventana_min), now() + make_interval(mins => r.bloqueo_min));
      insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, ip, detalle)
      values ('relleno_credenciales', r.severidad, 'app', r.id, p_ip, jsonb_build_object('cuentas', v_n));
      return 'ip_bloqueada_ahora';
    end if;
  end if;
  return 'rechazado';
end $$;
comment on function seguridad.registrar_intento(text, inet, boolean, text, text) is 'Detector de ataques: registra el intento, bloquea IPs y cuentas por fuerza bruta, relleno de credenciales o señuelos, y crea la alerta. La API lo llama en cada inicio de sesión';

create or replace function seguridad.requiere_doble_factor(p_usuario bigint) returns boolean language sql stable security definer set search_path = pg_catalog, nucleo as $$
  select exists (select 1 from nucleo.usuario_rol ur join nucleo.rol r on r.id = ur.rol_id where ur.usuario_id = p_usuario and r.codigo in ('administrador', 'contador'))
      or coalesce((select es_superusuario from nucleo.usuario where id = p_usuario), false) $$;
comment on function seguridad.requiere_doble_factor(bigint) is 'Administrador, contador y superusuario entran siempre con doble factor (mira los roles de todas las fincas)';

create or replace function seguridad.validar_sesion() returns trigger language plpgsql as $$
begin
  if seguridad.cuenta_bloqueada(new.usuario_id) then raise exception 'La cuenta % está bloqueada', new.usuario_id; end if;
  if seguridad.ip_bloqueada(new.ip) then raise exception 'La IP % está bloqueada', new.ip; end if;
  if seguridad.requiere_doble_factor(new.usuario_id) and new.metodo not in ('doble_factor', 'llave_acceso') then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, usuario_id, ip) values ('sesion_sin_doble_factor', 'alta', 'base_datos', new.usuario_id, new.ip);
    raise exception 'Este usuario debe entrar con doble factor';
  end if;
  if new.vence_en > new.iniciada_en + interval '12 hours' then raise exception 'Una sesión dura como máximo 12 horas'; end if;
  return new;
end $$;
create trigger tg_sesion_validar before insert on seguridad.sesion_usuario for each row execute function seguridad.validar_sesion();

create or replace function seguridad.revocar_sesiones(p_usuario bigint, p_motivo text) returns integer language plpgsql as $$
declare v_n integer;
begin
  update seguridad.sesion_usuario set revocada_en = now(), motivo_revocacion = p_motivo where usuario_id = p_usuario and revocada_en is null and vence_en > now();
  get diagnostics v_n = row_count;
  return v_n;
end $$;

create or replace function seguridad.vigilar_privilegios() returns trigger language plpgsql as $$
declare v_rol text;
begin
  if tg_table_name = 'usuario_rol' then
    select codigo into v_rol from nucleo.rol where id = new.rol_id;
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, usuario_id, predio_id, detalle)
    values ('escalada_privilegios', case when v_rol in ('administrador', 'contador') then 'alta' else 'baja' end, 'base_datos', new.usuario_id, new.predio_id,
            jsonb_build_object('rol', v_rol, 'otorgado_por', nucleo.usuario_actual(), 'agente', nucleo.agente_actual()));
  elsif tg_table_name = 'rol_permiso' then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, detalle)
    values ('cambio_permisos', 'media', 'base_datos', jsonb_build_object('operacion', tg_op, 'rol_id', coalesce(new.rol_id, old.rol_id),
            'permiso_id', coalesce(new.permiso_id, old.permiso_id), 'por', nucleo.usuario_actual()));
  elsif tg_table_name = 'usuario' and new.es_superusuario and not old.es_superusuario then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, usuario_id, detalle)
    values ('escalada_privilegios', 'critica', 'base_datos', new.id, jsonb_build_object('superusuario', true, 'por', nucleo.usuario_actual()));
  end if;
  return null;
end $$;
create trigger tg_usuario_rol_vigilar after insert on nucleo.usuario_rol for each row execute function seguridad.vigilar_privilegios();
create trigger tg_rol_permiso_vigilar after insert or delete on nucleo.rol_permiso for each row execute function seguridad.vigilar_privilegios();
create trigger tg_usuario_vigilar after update of es_superusuario on nucleo.usuario for each row execute function seguridad.vigilar_privilegios();

create or replace function seguridad.vigilar_exportaciones() returns trigger language plpgsql as $$
declare r seguridad.regla_deteccion; v_n integer;
begin
  if new.accion <> 'exportar' or new.usuario_id is null then return null; end if;
  r := seguridad.regla('exportacion_masiva');
  if r.id is null then return null; end if;
  select count(*) into v_n from nucleo.auditoria where accion = 'exportar' and usuario_id = new.usuario_id and ocurrido_en > now() - make_interval(mins => r.ventana_min);
  if v_n >= r.umbral and not exists (select 1 from seguridad.alerta_seguridad a where a.tipo = 'exportacion_masiva' and a.usuario_id = new.usuario_id
                                       and a.ocurrido_en > now() - make_interval(mins => r.ventana_min)) then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, regla_id, usuario_id, predio_id, detalle)
    values ('exportacion_masiva', r.severidad, 'base_datos', r.id, new.usuario_id, new.predio_id, jsonb_build_object('exportaciones', v_n, 'minutos', r.ventana_min));
    if r.respuesta = 'revocar_sesiones' then perform seguridad.revocar_sesiones(new.usuario_id, 'Exportación masiva'); end if;
  end if;
  return null;
end $$;
create trigger tg_auditoria_exportaciones after insert on nucleo.auditoria for each row execute function seguridad.vigilar_exportaciones();

create or replace function seguridad.proteger_alerta() returns trigger language plpgsql as $$
begin
  if tg_op = 'DELETE' then raise exception 'Las alertas de seguridad no se borran'; end if;
  if (to_jsonb(new) - array['estado', 'atendida_por', 'incidente_id', 'actualizado_en']) <> (to_jsonb(old) - array['estado', 'atendida_por', 'incidente_id', 'actualizado_en']) then
    raise exception 'De una alerta solo se registra su atención';
  end if;
  if new.estado <> old.estado then new.atendida_por := coalesce(new.atendida_por, nucleo.usuario_actual()); end if;
  return new;
end $$;
create trigger tg_alerta_proteger before update or delete on seguridad.alerta_seguridad for each row execute function seguridad.proteger_alerta();
create trigger tg_intento_inmutable before update or delete on seguridad.intento_acceso for each row execute function nucleo.impedir_cambio();
create trigger tg_ejecucion_prueba_inmutable before update or delete on seguridad.ejecucion_prueba for each row execute function nucleo.impedir_cambio();

create or replace function seguridad.revisar_copias() returns integer language plpgsql as $$
declare v_n integer := 0;
begin
  if not exists (select 1 from seguridad.copia_seguridad where alcance = 'postgresql' and exitosa and inicio > now() - interval '26 hours') then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, detalle) values ('copia_fallida', 'alta', 'monitoreo', '{"motivo": "sin copia exitosa de PostgreSQL en 26 horas"}');
    v_n := v_n + 1;
  end if;
  if not exists (select 1 from seguridad.copia_seguridad where restauracion_probada_en > now() - interval '35 days') then
    insert into seguridad.alerta_seguridad (tipo, severidad, fuente, detalle) values ('copia_fallida', 'media', 'monitoreo', '{"motivo": "sin prueba de restauración en 35 días"}');
    v_n := v_n + 1;
  end if;
  return v_n;
end $$;
comment on function seguridad.revisar_copias() is 'Tarea diaria: alerta si no hubo copia cifrada exitosa en 26 horas o si no se probó una restauración en el último mes';

create or replace view seguridad.v_tablero as
select (select count(*) from seguridad.alerta_seguridad where ocurrido_en > now() - interval '24 hours') as alertas_24h,
       (select count(*) from seguridad.alerta_seguridad where estado = 'nueva' and severidad in ('alta', 'critica')) as alertas_graves_sin_atender,
       (select count(*) from seguridad.bloqueo where levantado_por is null and (hasta is null or hasta > now())) as bloqueos_activos,
       (select count(*) from seguridad.intento_acceso where not exito and ocurrido_en > now() - interval '24 hours') as accesos_fallidos_24h,
       (select count(*) from seguridad.incidente where estado <> 'cerrado') as incidentes_abiertos,
       (select max(ejecutada_en) from seguridad.ejecucion_prueba where fallidas = 0) as ultima_prueba_limpia,
       (select max(restauracion_probada_en) from seguridad.copia_seguridad) as ultima_restauracion_probada;

-- ============================================================================
-- 25. CRM: captura con autorización, calificación, conversión y embudo
-- ============================================================================
create or replace function crm.consentimiento_vigente(p_consentimiento bigint) returns boolean language sql stable as $$
  select exists (select 1 from terceros.consentimiento_datos where id = p_consentimiento and otorgado and revocado_en is null) $$;

create or replace function crm.validar_prospecto() returns trigger language plpgsql as $$
begin
  if new.tipo = 'persona' and (new.telefono is not null or new.correo is not null) and not crm.consentimiento_vigente(new.consentimiento_id) then
    raise exception 'Los datos de contacto de una persona solo se guardan con su autorización (Ley 1581)';
  end if;
  if new.etapa = 'ganado' and not exists (select 1 from terceros.cliente where tercero_id = new.tercero_id) then
    raise exception 'Para ganar el prospecto conviértalo en cliente (crm.convertir_prospecto)';
  end if;
  if new.etapa = 'perdido' and new.motivo_perdida is null then raise exception 'Registre por qué se perdió el prospecto'; end if;
  return new;
end $$;
create trigger tg_prospecto_validar before insert or update on crm.prospecto for each row execute function crm.validar_prospecto();

create or replace function crm.validar_interaccion() returns trigger language plpgsql as $$
declare p crm.prospecto;
begin
  if new.prospecto_id is not null and new.tipo in ('llamada', 'whatsapp', 'correo') then
    select * into p from crm.prospecto where id = new.prospecto_id;
    if p.tipo = 'persona' and not crm.consentimiento_vigente(p.consentimiento_id) then
      raise exception 'No se contacta a una persona sin su autorización vigente';
    end if;
    if p.tipo = 'empresa' and p.telefono is null and p.correo is null
       and not exists (select 1 from crm.contacto_empresa c where c.prospecto_id = p.id and crm.consentimiento_vigente(c.consentimiento_id)) then
      raise exception 'La empresa no tiene un canal de contacto autorizado';
    end if;
  end if;
  if new.prospecto_id is not null then
    update crm.prospecto set etapa = 'contactado' where id = new.prospecto_id and etapa = 'nuevo';
  end if;
  return new;
end $$;
create trigger tg_interaccion_validar before insert on crm.interaccion for each row execute function crm.validar_interaccion();

create or replace function crm.calificar(p_prospecto bigint) returns smallint language plpgsql as $$
declare p crm.prospecto; v integer := 0; v_ref numeric := coalesce(nucleo.parametro_valor('volumen_referencia_prospecto'), 1000000);
begin
  select * into p from crm.prospecto where id = p_prospecto;
  if crm.consentimiento_vigente(p.consentimiento_id) or p.tipo = 'empresa' then v := v + 20; end if;
  if p.sector in ('restaurante', 'hotel', 'supermercado', 'distribuidor', 'casino', 'colegio', 'exportador') then v := v + 20; end if;
  v := v + least(30, round(coalesce(p.volumen_estimado_mes, 0) / v_ref * 30))::integer;
  if exists (select 1 from crm.interaccion i where i.prospecto_id = p.id and i.fecha > now() - interval '30 days') then v := v + 15; end if;
  if p.etapa in ('calificado', 'propuesta', 'negociacion') then v := v + 15; end if;
  update crm.prospecto set puntaje = least(v, 100) where id = p_prospecto;
  return least(v, 100);
end $$;
comment on function crm.calificar(bigint) is 'Puntaje simple y explicable: autorización, sector, volumen estimado, contacto reciente y etapa';

create or replace function crm.convertir_prospecto(p_prospecto bigint, p_segmento text) returns bigint language plpgsql as $$
declare p crm.prospecto; v_ter bigint;
begin
  select * into p from crm.prospecto where id = p_prospecto for update;
  v_ter := p.tercero_id;
  -- Una persona con autorización ya tiene tercero desde la captura (la autorización se guarda a nombre del titular)
  if v_ter is null then
    insert into terceros.tercero (tipo_persona, tipo_documento, numero_documento, nombres, razon_social, correo, telefono, es_cliente)
    values (case p.tipo when 'empresa' then 'juridica' else 'natural' end, case when p.nit is not null then 'NIT' end, p.nit,
            case when p.tipo = 'persona' then p.nombre end, case when p.tipo = 'empresa' then p.nombre end, p.correo, p.telefono, true)
    returning id into v_ter;
  else
    update terceros.tercero set es_cliente = true where id = v_ter;
  end if;
  insert into terceros.cliente (tercero_id, segmento) values (v_ter, p_segmento) on conflict do nothing;
  update crm.prospecto set tercero_id = v_ter, etapa = 'ganado' where id = p_prospecto;
  return v_ter;
end $$;
comment on function crm.convertir_prospecto(bigint, text) is 'Convierte el prospecto en tercero y cliente (si ya tenía tercero por su autorización, lo reutiliza)';

create or replace view crm.v_embudo as
select etapa, count(*) as prospectos, sum(volumen_estimado_mes) as volumen_estimado_mes, round(avg(puntaje), 1) as puntaje_promedio
from crm.prospecto group by etapa;

create or replace view crm.v_campanas as
select c.id, c.nombre, c.canal, c.costo_real, count(p.id) as prospectos, count(p.id) filter (where p.etapa = 'ganado') as clientes_ganados,
       round(c.costo_real / nullif(count(p.id), 0), 0) as costo_por_prospecto,
       round(c.costo_real / nullif(count(p.id) filter (where p.etapa = 'ganado'), 0), 0) as costo_por_cliente
from crm.campana c left join crm.prospecto p on p.campana_id = c.id group by c.id;

create or replace view crm.v_proyeccion_ventas as
select date_trunc('month', cierre_estimado)::date as mes, count(*) as oportunidades, sum(valor_estimado) as valor_total,
       round(sum(valor_estimado * probabilidad_pct / 100.0), 0) as valor_ponderado
from crm.oportunidad where estado = 'abierta' group by 1;

-- ============================================================================
-- 26. Estrategia: evaluación de proyectos (VPN, TIR, ROI, palancas) y reinversión de utilidades
-- ============================================================================
create or replace function estrategia.vpn(p_tasa_periodo numeric, p_flujos numeric[]) returns numeric language sql immutable as $$
  select round(sum(f / power(1 + p_tasa_periodo, t - 1)), 2) from unnest(p_flujos) with ordinality x(f, t) $$;
comment on function estrategia.vpn(numeric, numeric[]) is 'Valor presente neto; el primer flujo es el periodo 0 (inversión)';

create or replace function estrategia.tir(p_flujos numeric[]) returns numeric language plpgsql immutable as $$
declare lo numeric := -0.99; hi numeric := 10; mid numeric; f_lo numeric; f_mid numeric; i integer;
begin
  f_lo := estrategia.vpn(lo, p_flujos);
  if sign(f_lo) = sign(estrategia.vpn(hi, p_flujos)) then return null; end if;
  for i in 1 .. 200 loop
    mid := (lo + hi) / 2; f_mid := (select sum(f / power(1 + mid, t - 1)) from unnest(p_flujos) with ordinality x(f, t));
    if abs(f_mid) < 0.01 then exit; end if;
    if sign(f_mid) = sign(f_lo) then lo := mid; f_lo := f_mid; else hi := mid; end if;
  end loop;
  return round(mid, 6);
end $$;
comment on function estrategia.tir(numeric[]) is 'Tasa interna de retorno por periodo (bisección); vacía si los flujos no cambian de signo';

create or replace function estrategia.evaluar_proyecto(p_evaluacion bigint) returns numeric language plpgsql as $$
declare e estrategia.evaluacion_proyecto; v_flujos numeric[]; v_tm numeric; v_tir numeric; v_acum numeric := 0; v_rec smallint; v_net numeric; pl record; i integer;
begin
  select * into e from estrategia.evaluacion_proyecto where id = p_evaluacion;
  if not exists (select 1 from estrategia.flujo_proyecto where evaluacion_id = e.id) then
    if e.precio_unitario is null or e.unidades_mes is null then raise exception 'Cargue los flujos o los datos de precio, costo y volumen'; end if;
    insert into estrategia.flujo_proyecto (evaluacion_id, mes, inversion) values (e.id, 0, e.inversion_inicial);
    insert into estrategia.flujo_proyecto (evaluacion_id, mes, ingresos, egresos)
    select e.id, m, e.precio_unitario * e.unidades_mes, coalesce(e.costo_variable_unitario, 0) * e.unidades_mes + coalesce(e.costos_fijos_mes, 0) + e.intereses_mes
    from generate_series(1, e.horizonte_meses) m;
  end if;
  select array_agg(ingresos - egresos - inversion order by mes) into v_flujos from estrategia.flujo_proyecto where evaluacion_id = e.id;
  v_tm := power(1 + e.tasa_descuento_anual, 1.0 / 12) - 1;
  v_tir := estrategia.tir(v_flujos);
  for i in 1 .. array_length(v_flujos, 1) loop
    v_acum := v_acum + v_flujos[i];
    if v_rec is null and i > 1 and v_acum >= 0 then v_rec := i - 1; end if;
  end loop;
  v_net := v_acum;
  select * into pl from finanzas.palancas(e.unidades_mes, e.precio_unitario, coalesce(e.costo_variable_unitario, 0), coalesce(e.costos_fijos_mes, 0), e.intereses_mes);
  update estrategia.evaluacion_proyecto set
    vpn = estrategia.vpn(v_tm, v_flujos),
    tir_anual = case when v_tir is not null then round(power(1 + v_tir, 12) - 1, 4) end,
    roi_pct = case when e.inversion_inicial > 0 then round(v_net / e.inversion_inicial * 100, 2) end,
    recuperacion_meses = v_rec, punto_equilibrio_unidades = pl.punto_equilibrio_unidades, margen_seguridad_pct = pl.margen_seguridad_pct,
    gpo = pl.gpo, gpf = pl.gpf, gpt = pl.gpt, calculado_en = now()
  where id = e.id;
  return estrategia.vpn(v_tm, v_flujos);
end $$;
comment on function estrategia.evaluar_proyecto(bigint) is 'Calcula VPN (a la tasa de oportunidad), TIR anual, ROI neto, meses de recuperación, punto de equilibrio, margen de seguridad y grados de palanca de una iniciativa';

create or replace function estrategia.validar_iniciativa() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' and nucleo.agente_actual() is not null then
    new.agente_id := coalesce(new.agente_id, nucleo.agente_actual());
    if new.estado <> 'idea' then raise exception 'Un agente solo propone ideas'; end if;
  end if;
  if new.estado in ('aprobada', 'piloto', 'escalada') and (tg_op = 'INSERT' or old.estado not in ('aprobada', 'piloto', 'escalada')) then
    perform nucleo.exigir_persona('aprobar iniciativas de negocio');
    if not exists (select 1 from estrategia.evaluacion_proyecto where iniciativa_id = new.id and calculado_en is not null) then
      raise exception 'Una iniciativa se aprueba con su evaluación financiera calculada (VPN, TIR, ROI)';
    end if;
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual()); new.aprobada_en := now();
  end if;
  return new;
end $$;
create trigger tg_iniciativa_validar before insert or update on estrategia.iniciativa for each row execute function estrategia.validar_iniciativa();

create or replace function estrategia.utilidad_linea(p_linea bigint, p_anio integer, p_mes integer) returns numeric language plpgsql stable as $$
declare v_cc bigint; v_desde date := make_date(p_anio, p_mes, 1);
begin
  select centro_costo_id into v_cc from estrategia.linea_negocio where id = p_linea;
  if v_cc is null then raise exception 'La línea % no tiene centro de costo', p_linea; end if;
  return (finanzas.estado_resultados(v_desde, (v_desde + interval '1 month - 1 day')::date, v_cc)->>'utilidad_neta')::numeric;
end $$;
comment on function estrategia.utilidad_linea(bigint, integer, integer) is 'Utilidad neta de una línea en un mes, tomada de la contabilidad por centro de costo';

create or replace function estrategia.validar_reinversion() returns trigger language plpgsql as $$
declare v_tope numeric := coalesce(nucleo.parametro_valor('tope_reinversion_pct'), 30); v_usado numeric; v_estado text;
begin
  if tg_op = 'UPDATE' and old.estado in ('ejecutada', 'cancelada') then raise exception 'La reinversión % ya está %', old.id, old.estado; end if;
  new.utilidad_linea := estrategia.utilidad_linea(new.linea_origen_id, new.anio, new.mes);
  if new.utilidad_linea <= 0 then raise exception 'No se reinvierte desde una línea con pérdida o sin utilidad en %-%', new.anio, new.mes; end if;
  select coalesce(sum(valor), 0) into v_usado from estrategia.reinversion
  where linea_origen_id = new.linea_origen_id and anio = new.anio and mes = new.mes and estado <> 'cancelada' and id is distinct from new.id;
  if new.estado <> 'cancelada' and v_usado + new.valor > round(new.utilidad_linea * v_tope / 100, 0) then
    raise exception 'La reinversión supera el tope: % %% de la utilidad (% de %)', v_tope, v_usado + new.valor, new.utilidad_linea;
  end if;
  if new.estado in ('aprobada', 'ejecutada') and (tg_op = 'INSERT' or old.estado = 'propuesta') then
    perform nucleo.exigir_persona('aprobar reinversiones');
    select estado into v_estado from estrategia.iniciativa where id = new.iniciativa_id;
    if v_estado not in ('aprobada', 'piloto', 'escalada') then raise exception 'Solo se reinvierte en una iniciativa aprobada'; end if;
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
  end if;
  return new;
end $$;
create trigger tg_reinversion_validar before insert or update on estrategia.reinversion for each row execute function estrategia.validar_reinversion();

create or replace view estrategia.v_retorno_iniciativas as
select i.id, i.titulo, i.ansoff, i.palanca, i.estado, ev.inversion_inicial, ev.vpn, ev.tir_anual, ev.roi_pct as roi_proyectado_pct,
       (select coalesce(sum(valor), 0) from estrategia.reinversion r where r.iniciativa_id = i.id and r.estado in ('aprobada', 'ejecutada')) as reinvertido,
       s.ingresos, s.egresos, s.meses,
       case when ev.inversion_inicial > 0 and s.meses > 0 then round((s.ingresos - s.egresos - ev.inversion_inicial) / ev.inversion_inicial * 100, 2) end as roi_real_pct
from estrategia.iniciativa i
left join lateral (select * from estrategia.evaluacion_proyecto e where e.iniciativa_id = i.id order by e.version desc limit 1) ev on true
left join lateral (select coalesce(sum(ingresos_reales), 0) ingresos, coalesce(sum(egresos_reales), 0) egresos, count(*) meses
                   from estrategia.seguimiento_iniciativa where iniciativa_id = i.id) s on true;
comment on view estrategia.v_retorno_iniciativas is 'Retorno proyectado contra real de cada iniciativa y cuánto se le ha reinvertido';

create or replace view estrategia.v_matriz_lineas as
select l.id, l.codigo, l.nombre, l.estado, l.palanca_dominante,
       (finanzas.estado_resultados(date_trunc('year', current_date)::date, current_date, l.centro_costo_id)->>'ingresos_operacionales')::numeric as ingresos_anio,
       (finanzas.estado_resultados(date_trunc('year', current_date)::date, current_date, l.centro_costo_id)->>'margen_contribucion')::numeric as margen_contribucion_anio,
       (finanzas.estado_resultados(date_trunc('year', current_date)::date, current_date, l.centro_costo_id)->>'utilidad_neta')::numeric as utilidad_anio
from estrategia.linea_negocio l where l.centro_costo_id is not null;
comment on view estrategia.v_matriz_lineas is 'Cada sección de la finca con su ingreso, margen de contribución y utilidad del año: muestra qué líneas generan recursos para reinvertir y cuáles están subsidiadas';

-- ============================================================================
-- 27. Áreas de responsabilidad y cronograma de trabajo flexible 24/7
-- ============================================================================
create or replace function nucleo.parametro_texto(p_clave text, p_fecha date default current_date) returns text language sql stable as $$
  select par.valor from nucleo.parametro par
  where par.clave = p_clave and (par.predio_id = nucleo.predio_actual() or par.predio_id is null)
    and par.vigente_desde <= p_fecha and (par.vigente_hasta is null or par.vigente_hasta >= p_fecha)
  order by par.predio_id nulls last, par.vigente_desde desc limit 1 $$;

create or replace function personal.es_miembro_area(p_empleado bigint, p_area bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from personal.miembro_area m where m.empleado_id = p_empleado and m.area_id = p_area
                 and m.desde <= p_fecha and (m.hasta is null or m.hasta >= p_fecha)) $$;
create or replace function personal.es_responsable_area(p_usuario bigint, p_area bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from personal.miembro_area m join terceros.empleado e on e.id = m.empleado_id
                 where m.area_id = p_area and m.es_responsable and e.tercero_id = nucleo.tercero_de_usuario(p_usuario)
                   and m.desde <= p_fecha and (m.hasta is null or m.hasta >= p_fecha)) $$;

create or replace function personal.turno_rango(p_fecha date, p_inicio time, p_fin time) returns tsrange language sql immutable as $$
  select tsrange(p_fecha + p_inicio, case when p_fin <= p_inicio then p_fecha + 1 + p_fin else p_fecha + p_fin end) $$;
comment on function personal.turno_rango(date, time, time) is 'Rango real del turno: si la salida es menor o igual a la entrada, termina al día siguiente (turnos de noche)';

create or replace function personal.validar_turno() returns trigger language plpgsql as $$
declare v_desc numeric := coalesce(nucleo.parametro_valor('descanso_minimo_entre_turnos_horas'), 10);
        v_max numeric := coalesce(nucleo.parametro_valor('jornada_maxima_diaria_horas'), 11); v_r tsrange; v_otro record;
begin
  if new.tipo = 'descanso' then new.horas := 0; return new; end if;
  v_r := personal.turno_rango(new.fecha, new.hora_inicio, new.hora_fin);
  new.horas := round(extract(epoch from upper(v_r) - lower(v_r)) / 3600.0, 2);
  if new.horas > v_max then raise exception 'El turno de % horas supera la jornada máxima diaria de % horas', new.horas, v_max; end if;
  if exists (select 1 from personal.ausencia a where a.empleado_id = new.empleado_id and new.fecha between a.desde and a.hasta) then
    raise exception 'El trabajador % tiene una ausencia el %', new.empleado_id, new.fecha;
  end if;
  for v_otro in select t.* from personal.turno t where t.empleado_id = new.empleado_id and t.id is distinct from new.id and t.tipo <> 'descanso'
                  and t.fecha between new.fecha - 2 and new.fecha + 2 loop
    if personal.turno_rango(v_otro.fecha, v_otro.hora_inicio, v_otro.hora_fin) && v_r then
      raise exception 'El turno se cruza con otro del mismo trabajador el %', v_otro.fecha;
    end if;
    if extract(epoch from greatest(lower(v_r) - upper(personal.turno_rango(v_otro.fecha, v_otro.hora_inicio, v_otro.hora_fin)),
                                   lower(personal.turno_rango(v_otro.fecha, v_otro.hora_inicio, v_otro.hora_fin)) - upper(v_r))) / 3600.0 < v_desc then
      raise exception 'Entre dos turnos debe haber al menos % horas de descanso', v_desc;
    end if;
  end loop;
  return new;
end $$;
create trigger tg_turno_validar before insert or update on personal.turno for each row execute function personal.validar_turno();

-- Disponible = vinculado, sin ausencia y sin turno de descanso ese día
create or replace function personal.empleado_disponible(p_empleado bigint, p_fecha date) returns boolean language sql stable as $$
  select exists (select 1 from terceros.empleado e where e.id = p_empleado and e.fecha_ingreso <= p_fecha
                 and (e.fecha_retiro is null or e.fecha_retiro >= p_fecha))
     and not exists (select 1 from personal.ausencia a where a.empleado_id = p_empleado and p_fecha between a.desde and a.hasta)
     and not exists (select 1 from personal.turno t where t.empleado_id = p_empleado and t.fecha = p_fecha and t.tipo = 'descanso') $$;

create or replace function personal.validar_area_tarea() returns trigger language plpgsql as $$
begin
  if new.area_id is null and new.plantilla_tarea_id is not null then
    select area_id into new.area_id from personal.plantilla_tarea where id = new.plantilla_tarea_id;
  end if;
  if new.area_id is not null and new.empleado_id is not null
     and (tg_op = 'INSERT' or new.empleado_id is distinct from old.empleado_id or new.area_id is distinct from old.area_id)
     and not personal.es_miembro_area(new.empleado_id, new.area_id, new.fecha) then
    raise exception 'El trabajador % no pertenece al área de responsabilidad de la tarea', new.empleado_id;
  end if;
  return new;
end $$;
create trigger tg_tarea_area before insert or update on personal.tarea for each row execute function personal.validar_area_tarea();

create or replace function personal.generar_turnos(p_cronograma bigint) returns integer language plpgsql as $$
declare c personal.cronograma; a record; d date; v_dia smallint; det record; v_n integer := 0; v_k integer;
begin
  select * into c from personal.cronograma where id = p_cronograma;
  if c.estado <> 'borrador' then raise exception 'El cronograma % está %: los turnos se generan en borrador', c.nombre, c.estado; end if;
  for a in select ap.*, p.tipo as tipo_patron, p.ciclo_dias from personal.asignacion_patron ap join personal.patron_turno p on p.id = ap.patron_id
           where ap.cronograma_id = p_cronograma and p.tipo <> 'flexible' loop
    d := c.desde;
    while d <= c.hasta loop
      v_dia := case when a.tipo_patron = 'semanal' then extract(isodow from d)::smallint
                    else (((d - c.desde) + a.desfase_dias) % a.ciclo_dias + 1)::smallint end;
      for det in select * from personal.patron_turno_detalle where patron_id = a.patron_id and dia_ciclo = v_dia loop
        if det.tipo <> 'descanso' and exists (select 1 from personal.ausencia x where x.empleado_id = a.empleado_id and d between x.desde and x.hasta) then
          continue;
        end if;
        insert into personal.turno (empleado_id, fecha, hora_inicio, hora_fin, tipo, area_id, cronograma_id)
        values (a.empleado_id, d, coalesce(det.hora_inicio, '00:00'), coalesce(det.hora_fin, '00:00'), det.tipo, c.area_id, c.id)
        on conflict do nothing;
        get diagnostics v_k = row_count; v_n := v_n + v_k;
      end loop;
      d := d + 1;
    end loop;
  end loop;
  return v_n;
end $$;
comment on function personal.generar_turnos(bigint) is 'Arma los turnos del cronograma desde los patrones (semanal: días y horas elegidos; cíclico: rotación 24/7 con desfase por persona). Después se ajustan a mano';

create or replace function personal.huecos_cobertura(p_cronograma bigint)
returns table (fecha date, hora time, requeridas integer, programadas integer) language sql stable as $$
  with c as (select * from personal.cronograma where id = p_cronograma),
  franjas as (
    select d::date as fecha, (h || ':00')::time as hora, max(r.personas_min) as requeridas
    from c, generate_series(c.desde, c.hasta, interval '1 day') d, generate_series(0, 23) h, personal.requerimiento_cobertura r
    where r.area_id = c.area_id and (r.dia_semana is null or r.dia_semana = extract(isodow from d))
      and (h || ':00')::time >= r.hora_inicio and (h || ':00')::time < r.hora_fin
    group by 1, 2)
  select f.fecha, f.hora, f.requeridas,
         (select count(distinct t.empleado_id) from personal.turno t, c where t.area_id = c.area_id and t.tipo <> 'descanso'
            and t.fecha between f.fecha - 1 and f.fecha and personal.turno_rango(t.fecha, t.hora_inicio, t.hora_fin) @> (f.fecha + f.hora))::integer
  from franjas f
  where f.requeridas > (select count(distinct t.empleado_id) from personal.turno t, c where t.area_id = c.area_id and t.tipo <> 'descanso'
            and t.fecha between f.fecha - 1 and f.fecha and personal.turno_rango(t.fecha, t.hora_inicio, t.hora_fin) @> (f.fecha + f.hora))
  order by 1, 2 $$;
comment on function personal.huecos_cobertura(bigint) is 'Horas del cronograma en que hay menos personas que las requeridas por el área (sirve para la operación 24/7)';

create or replace view personal.v_carga_semanal as
select t.empleado_id, date_trunc('week', t.fecha)::date as semana, sum(t.horas) as horas,
       count(*) filter (where t.tipo <> 'descanso') as dias_trabajados,
       sum(t.horas) filter (where extract(isodow from t.fecha) = 7) as horas_domingo,
       count(*) filter (where t.tipo = 'nocturno') as turnos_nocturnos
from personal.turno t group by 1, 2;
comment on view personal.v_carga_semanal is 'Horas por semana (lunes a domingo), días trabajados, horas en domingo y turnos de noche: base de recargos y del control de jornada';

create or replace function personal.publicar_cronograma() returns trigger language plpgsql as $$
declare v_max numeric; v_extra numeric; r record; v_hueco record;
begin
  if old.estado = 'cerrado' then raise exception 'El cronograma % está cerrado', old.nombre; end if;
  if new.estado = 'publicado' and old.estado = 'borrador' then
    perform nucleo.exigir_persona('publicar cronogramas');
    v_max := coalesce(nucleo.parametro_valor('jornada_maxima_semanal_horas', new.desde), 42);
    v_extra := coalesce(nucleo.parametro_valor('horas_extra_max_semana', new.desde), 12);
    for r in select t.empleado_id, date_trunc('week', t.fecha)::date semana, sum(t.horas) horas
             from personal.turno t where t.cronograma_id = new.id group by 1, 2 having sum(t.horas) > v_max + v_extra loop
      raise exception 'El trabajador % tendría % horas la semana del % (máximo % + % extra)', r.empleado_id, r.horas, r.semana, v_max, v_extra;
    end loop;
    for r in select t.empleado_id, d::date dia from personal.turno t, generate_series(new.desde, new.hasta - 6, interval '1 day') d
             where t.cronograma_id = new.id and t.tipo <> 'descanso' and t.fecha between d::date and d::date + 6
             group by 1, 2 having count(distinct t.fecha) = 7 loop
      raise exception 'El trabajador % no tendría día de descanso en los 7 días desde el %', r.empleado_id, r.dia;
    end loop;
    select * into v_hueco from personal.huecos_cobertura(new.id) limit 1;
    if v_hueco.fecha is not null and not new.permitir_huecos then
      raise exception 'Falta cobertura: el % a las % hay % de % personas requeridas', v_hueco.fecha, v_hueco.hora, v_hueco.programadas, v_hueco.requeridas;
    end if;
    new.publicado_por := nucleo.usuario_actual(); new.publicado_en := now();
  end if;
  return new;
end $$;
create trigger tg_cronograma_publicar before update on personal.cronograma for each row execute function personal.publicar_cronograma();

-- ============================================================================
-- 28. Agenda: calendario sin cruces, cabañas, visitas e ingresos y salidas
-- ============================================================================
create or replace function agenda.preparar_cita() returns trigger language plpgsql as $$
declare v_prep smallint; v_activo boolean;
begin
  select minutos_preparacion, activo into v_prep, v_activo from agenda.recurso where id = new.recurso_id;
  if not v_activo and new.estado in ('tentativa', 'confirmada') then raise exception 'El recurso no está activo'; end if;
  new.fin_con_preparacion := new.fin + make_interval(mins => coalesce(v_prep, 0));
  return new;
end $$;
create trigger tg_cita_preparar before insert or update on agenda.cita for each row execute function agenda.preparar_cita();

create or replace function agenda.recurso_libre(p_recurso bigint, p_inicio timestamptz, p_fin timestamptz) returns boolean language sql stable as $$
  select not exists (select 1 from agenda.cita c where c.recurso_id = p_recurso and c.estado in ('tentativa', 'confirmada')
                     and tstzrange(c.inicio, c.fin_con_preparacion) && tstzrange(p_inicio, p_fin)) $$;

create or replace function turismo.validar_reserva() returns trigger language plpgsql as $$
declare v_cap smallint;
begin
  if new.alojamiento_id is not null then
    select capacidad_personas into v_cap from turismo.alojamiento where id = new.alojamiento_id;
    if new.personas > v_cap then raise exception 'La cabaña admite % personas y la reserva es para %', v_cap, new.personas; end if;
  end if;
  if new.fecha_fin = new.fecha_inicio and new.alojamiento_id is not null then raise exception 'Una reserva de cabaña es de al menos una noche'; end if;
  return new;
end $$;
create trigger tg_reserva_validar before insert or update on turismo.reserva for each row execute function turismo.validar_reserva();

create or replace function turismo.sincronizar_agenda() returns trigger language plpgsql as $$
declare v_rec bigint; v_in time := coalesce(nucleo.parametro_texto('hora_checkin'), '15:00')::time; v_out time := coalesce(nucleo.parametro_texto('hora_checkout'), '12:00')::time;
        v_area bigint;
begin
  if new.alojamiento_id is null then return null; end if;
  select id into v_rec from agenda.recurso where alojamiento_id = new.alojamiento_id;
  if v_rec is null then return null; end if;
  if new.estado in ('confirmada', 'pagada') then
    begin
      if exists (select 1 from agenda.cita where reserva_id = new.id) then
        update agenda.cita set inicio = new.fecha_inicio + v_in, fin = new.fecha_fin + v_out, estado = 'confirmada' where reserva_id = new.id;
      else
        insert into agenda.cita (recurso_id, titulo, tipo, inicio, fin, reserva_id)
        values (v_rec, 'Reserva ' || new.codigo, 'reserva_turistica', new.fecha_inicio + v_in, new.fecha_fin + v_out, new.id);
      end if;
    exception when exclusion_violation then
      raise exception 'La cabaña ya está ocupada o bloqueada entre el % y el % (incluye el tiempo de limpieza)', new.fecha_inicio, new.fecha_fin;
    end;
  elsif new.estado = 'cancelada' then
    update agenda.cita set estado = 'cancelada' where reserva_id = new.id;
  elsif new.estado = 'cumplida' then
    update agenda.cita set estado = 'cumplida' where reserva_id = new.id;
  end if;
  if new.checkout_en is not null and (tg_op = 'INSERT' or old.checkout_en is null) then
    select id into v_area from personal.area_responsabilidad where codigo = 'AR-TURISMO';
    insert into personal.tarea (titulo, proceso, fecha, area_id, origen, prioridad)
    select 'Limpieza y alistamiento · ' || a.nombre, 'turismo', new.checkout_en::date, v_area, 'agenda', 'alta' from turismo.alojamiento a where a.id = new.alojamiento_id;
  end if;
  return null;
end $$;
create trigger tg_reserva_agenda after insert or update on turismo.reserva for each row execute function turismo.sincronizar_agenda();

create or replace function turismo.sincronizar_bloqueo() returns trigger language plpgsql as $$
declare v_rec bigint;
begin
  if tg_op = 'DELETE' then
    update agenda.cita set estado = 'cancelada' where bloqueo_id = old.id; return old;
  end if;
  select id into v_rec from agenda.recurso where alojamiento_id = new.alojamiento_id;
  if v_rec is null then return new; end if;
  begin
    insert into agenda.cita (recurso_id, titulo, tipo, inicio, fin, bloqueo_id)
    values (v_rec, new.motivo, 'bloqueo', new.desde::timestamptz, (new.hasta + 1)::timestamptz, new.id);
  exception when exclusion_violation then
    raise exception 'El bloqueo choca con una reserva o cita de la cabaña';
  end;
  return new;
end $$;
create trigger tg_bloqueo_agenda after insert on turismo.bloqueo_calendario for each row execute function turismo.sincronizar_bloqueo();
create trigger tg_bloqueo_agenda_borrar before delete on turismo.bloqueo_calendario for each row execute function turismo.sincronizar_bloqueo();

create or replace function agenda.validar_visita() returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and old.estado in ('salio', 'rechazada', 'cancelada', 'no_llego') and new.estado <> old.estado then
    raise exception 'La visita % ya está %', old.id, old.estado;
  end if;
  if new.estado = 'aprobada' and (tg_op = 'INSERT' or old.estado = 'solicitada') then
    perform nucleo.exigir_persona('aprobar visitas');
    if new.requiere_bioseguridad and new.contacto_aves_reciente is distinct from false then
      raise exception 'Bioseguridad: quien entra al galpón declara no haber tenido contacto con otras aves en las últimas % horas',
        coalesce(nucleo.parametro_valor('cuarentena_aves_horas'), 72);
    end if;
    new.aprobada_por := coalesce(new.aprobada_por, nucleo.usuario_actual());
  end if;
  if new.estado = 'rechazada' and new.motivo_rechazo is null then raise exception 'Registre el motivo del rechazo'; end if;
  return new;
end $$;
create trigger tg_visita_validar before insert or update on agenda.visita for each row execute function agenda.validar_visita();

create or replace function agenda.emitir_pase(p_visita bigint) returns text language plpgsql as $$
declare v_codigo text := upper(substr(encode(sha256(convert_to(random()::text || clock_timestamp()::text || p_visita::text, 'UTF8')), 'hex'), 1, 12));
begin
  if (select estado from agenda.visita where id = p_visita) <> 'aprobada' then raise exception 'Solo una visita aprobada recibe pase'; end if;
  update agenda.visita set pase_hash = encode(sha256(convert_to(v_codigo, 'UTF8')), 'hex') where id = p_visita;
  return v_codigo;
end $$;
comment on function agenda.emitir_pase(bigint) is 'Genera el código del pase (se envía al visitante como QR); la base guarda solo su huella';

create or replace function agenda.validar_acceso() returns trigger language plpgsql as $$
declare v agenda.visita; v_tol integer := coalesce(nucleo.parametro_valor('tolerancia_visita_min'), 60)::integer; v_clave text; v_jor bigint;
begin
  new.registrado_por := coalesce(new.registrado_por, nucleo.usuario_actual());
  if new.visita_id is not null then
    select * into v from agenda.visita where id = new.visita_id for update;
    if new.sentido = 'entrada' then
      if v.estado <> 'aprobada' then raise exception 'La visita no está aprobada (estado %)', v.estado; end if;
      if new.ocurrido_en < v.ingreso_programado - make_interval(mins => v_tol) or new.ocurrido_en > v.salida_programada then
        raise exception 'La visita llega fuera del horario programado';
      end if;
      if v.requiere_bioseguridad and not new.desinfeccion then raise exception 'Bioseguridad: la entrada al galpón exige desinfección de personas y vehículos'; end if;
      if new.tipo = 'vehiculo' and v.vehiculo_placa is not null and upper(coalesce(new.placa, '')) <> upper(v.vehiculo_placa) then
        raise exception 'La placa % no corresponde a la visita programada (%)', new.placa, v.vehiculo_placa;
      end if;
      update agenda.visita set estado = 'en_sitio' where id = v.id;
    else
      if v.estado <> 'en_sitio' then raise exception 'La visita no ha entrado'; end if;
      update agenda.visita set estado = 'salio' where id = v.id;
    end if;
  elsif new.empleado_id is not null then
    select id into v_jor from personal.jornada where empleado_id = new.empleado_id and fecha >= new.ocurrido_en::date - 1 and salida is null order by entrada desc limit 1;
    if new.sentido = 'entrada' then
      if v_jor is null then
        insert into personal.jornada (empleado_id, fecha, entrada, metodo_registro)
        values (new.empleado_id, new.ocurrido_en::date, new.ocurrido_en, case new.metodo when 'carne_qr' then 'qr' when 'carne_nfc' then 'nfc' else 'manual' end);
      end if;
    else
      if v_jor is null then raise exception 'No hay entrada abierta del trabajador %', new.empleado_id; end if;
      update personal.jornada set salida = new.ocurrido_en where id = v_jor;
    end if;
  elsif new.sentido = 'salida' then
    v_clave := upper(coalesce(new.placa, new.nombre));
    if not exists (select 1 from agenda.registro_acceso r where r.sentido = 'entrada' and upper(coalesce(r.placa, r.nombre)) = v_clave
                   and r.ocurrido_en::date = new.ocurrido_en::date and r.ocurrido_en < new.ocurrido_en) then
      raise exception 'No hay una entrada registrada hoy para %', v_clave;
    end if;
  end if;
  return new;
end $$;
create trigger tg_registro_acceso_validar before insert on agenda.registro_acceso for each row execute function agenda.validar_acceso();
create trigger tg_registro_acceso_inmutable before update or delete on agenda.registro_acceso for each row execute function nucleo.impedir_cambio();

create or replace view agenda.v_en_sitio as
with ultimos as (
  select distinct on (coalesce('V' || r.visita_id, 'E' || r.empleado_id, 'N' || upper(coalesce(r.placa, r.nombre))))
         r.*, coalesce('V' || r.visita_id, 'E' || r.empleado_id, 'N' || upper(coalesce(r.placa, r.nombre))) as clave
  from agenda.registro_acceso r where r.ocurrido_en > now() - interval '24 hours'
  order by coalesce('V' || r.visita_id, 'E' || r.empleado_id, 'N' || upper(coalesce(r.placa, r.nombre))), r.ocurrido_en desc)
select u.clave, u.tipo, u.visita_id, u.empleado_id, coalesce(v.nombre, u.nombre) as nombre, coalesce(u.placa, v.vehiculo_placa) as placa,
       v.zona_destino_id, u.ocurrido_en as entro_en
from ultimos u left join agenda.visita v on v.id = u.visita_id where u.sentido = 'entrada';
comment on view agenda.v_en_sitio is 'Quién y qué vehículo está dentro de la finca ahora (emergencias, robots en zonas sin personas, cierre de portería)';

create or replace view agenda.v_agenda_dia as
select 'cita' as clase, c.id, r.nombre as recurso, c.titulo, c.tipo, c.inicio, c.fin, c.estado from agenda.cita c join agenda.recurso r on r.id = c.recurso_id
union all
select 'visita', v.id, coalesce(z.nombre, 'Portería'), v.nombre || ' · ' || v.motivo, v.tipo, v.ingreso_programado, v.salida_programada, v.estado
from agenda.visita v left join nucleo.zona z on z.id = v.zona_destino_id
union all
select 'turno', t.id, coalesce(a.nombre, 'Sin área'), 'Turno trabajador ' || t.empleado_id, t.tipo, (t.fecha + t.hora_inicio)::timestamptz,
       upper(personal.turno_rango(t.fecha, t.hora_inicio, t.hora_fin))::timestamptz, 'programado'
from personal.turno t left join personal.area_responsabilidad a on a.id = t.area_id where t.tipo <> 'descanso';
comment on view agenda.v_agenda_dia is 'Agenda unificada: citas de recursos (cabañas, equipos), visitas programadas y turnos de trabajo';

-- ============================================================================
-- 29. Formación como organización educativa (ISO 21001): quejas, apelaciones y satisfacción
-- ============================================================================
create or replace function formacion.validar_queja() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' then
    new.responder_antes := coalesce(new.responder_antes, new.presentada_en + coalesce(nucleo.parametro_valor('dias_respuesta_queja'), 15)::integer);
  end if;
  if new.estado in ('resuelta', 'rechazada') and (tg_op = 'INSERT' or old.estado not in ('resuelta', 'rechazada')) then
    perform nucleo.exigir_persona('resolver quejas y apelaciones');
    new.resuelta_por := coalesce(new.resuelta_por, nucleo.usuario_actual());
    if new.respuesta is null then raise exception 'Registre la respuesta'; end if;
    if exists (select 1 from formacion.sesion_presencial s where s.curso_id = new.curso_id and s.instructor_id = nucleo.tercero_de_usuario(new.resuelta_por)) then
      raise exception 'La queja o apelación la resuelve alguien distinto del instructor del curso';
    end if;
  end if;
  return new;
end $$;
create trigger tg_queja_validar before insert or update on formacion.queja_apelacion for each row execute function formacion.validar_queja();

create or replace view formacion.v_satisfaccion as
select c.id as curso_id, c.codigo, c.nombre, count(e.id) as respuestas, round(avg(e.satisfaccion), 2) as satisfaccion, round(avg(e.utilidad), 2) as utilidad,
       round(avg(e.instructor), 2) as instructor,
       (select count(*) from formacion.inscripcion i where i.curso_id = c.id and i.estado = 'aprobado') as aprobados,
       (select count(*) from formacion.inscripcion i where i.curso_id = c.id) as inscritos
from formacion.curso c left join formacion.encuesta e on e.curso_id = c.id group by c.id;
comment on view formacion.v_satisfaccion is 'Seguimiento de la formación: satisfacción, utilidad, instructor y tasa de aprobación por curso';

-- ============================================================================
-- 30. Proyectos (PMBOK 8): aprobación, línea base, ruta crítica, cambios, valor ganado y cierre
-- ============================================================================
create or replace function proyectos.clasificar_interesado() returns trigger language plpgsql as $$
begin
  new.estrategia := case when new.influencia >= 3 and new.interes >= 3 then 'gestionar_de_cerca' when new.influencia >= 3 then 'mantener_satisfecho'
                         when new.interes >= 3 then 'mantener_informado' else 'monitorear' end;
  return new;
end $$;
create trigger tg_interesado_clasificar before insert or update on proyectos.interesado for each row execute function proyectos.clasificar_interesado();

create or replace function proyectos.validar_proyecto() returns trigger language plpgsql as $$
declare v_ini text;
begin
  if tg_op = 'UPDATE' and old.estado in ('cerrado', 'cancelado') then raise exception 'El proyecto % está %', old.codigo, old.estado; end if;
  if tg_op = 'UPDATE' and new.estado <> old.estado then
    if new.estado = 'aprobado' then
      perform nucleo.exigir_persona('aprobar proyectos');
      if new.patrocinador_id is null or new.director_id is null or new.presupuesto is null or new.fin_plan is null or new.inicio_plan is null then
        raise exception 'El acta de constitución necesita patrocinador, director, presupuesto y fechas';
      end if;
      if nucleo.usuario_actual() <> new.patrocinador_id then raise exception 'El proyecto lo aprueba su patrocinador'; end if;
      if new.iniciativa_id is not null then
        select estado into v_ini from estrategia.iniciativa where id = new.iniciativa_id;
        if v_ini not in ('aprobada', 'piloto', 'escalada') then raise exception 'La iniciativa de negocio del proyecto no está aprobada'; end if;
      end if;
      new.aprobado_por := nucleo.usuario_actual(); new.aprobado_en := now(); new.area_enfoque := 'planificacion';
    elsif new.estado = 'en_curso' then
      if old.estado not in ('aprobado', 'suspendido') then raise exception 'Un proyecto empieza después de aprobado'; end if;
      new.inicio_real := coalesce(new.inicio_real, current_date); new.area_enfoque := 'ejecucion';
    elsif new.estado = 'cerrado' then
      perform nucleo.exigir_persona('cerrar proyectos');
      if exists (select 1 from proyectos.elemento_edt where proyecto_id = new.id and es_entregable and estado <> 'aceptado') then
        raise exception 'No se cierra: hay entregables sin aceptar';
      end if;
      if not exists (select 1 from proyectos.registro where proyecto_id = new.id and tipo = 'leccion_aprendida') then
        raise exception 'No se cierra sin registrar lecciones aprendidas';
      end if;
      new.fin_real := coalesce(new.fin_real, current_date); new.area_enfoque := 'cierre';
    end if;
  end if;
  return new;
end $$;
create trigger tg_proyecto_validar before update on proyectos.proyecto for each row execute function proyectos.validar_proyecto();

create or replace function proyectos.linea_base_inicial() returns trigger language plpgsql as $$
begin
  if new.estado = 'aprobado' and old.estado = 'propuesto' then
    insert into proyectos.linea_base (proyecto_id, version, presupuesto, fin_plan, alcance, aprobada_por)
    values (new.id, 1, new.presupuesto, new.fin_plan, new.objetivo, new.aprobado_por);
  end if;
  return null;
end $$;
create trigger tg_proyecto_linea_base after update on proyectos.proyecto for each row execute function proyectos.linea_base_inicial();
create trigger tg_linea_base_inmutable before update or delete on proyectos.linea_base for each row execute function nucleo.impedir_cambio();

create or replace function proyectos.aceptar_entregable() returns trigger language plpgsql as $$
begin
  if new.estado = 'aceptado' and old.estado <> 'aceptado' then
    perform nucleo.exigir_persona('aceptar entregables');
    if old.estado <> 'terminado' then raise exception 'Solo se acepta un entregable terminado'; end if;
    new.aceptado_por := coalesce(new.aceptado_por, nucleo.usuario_actual()); new.aceptado_en := now();
  end if;
  return new;
end $$;
create trigger tg_elemento_edt_aceptar before update on proyectos.elemento_edt for each row execute function proyectos.aceptar_entregable();

create or replace function proyectos.validar_dependencia() returns trigger language plpgsql as $$
begin
  if (select proyecto_id from proyectos.actividad where id = new.predecesora_id) <> (select proyecto_id from proyectos.actividad where id = new.sucesora_id) then
    raise exception 'Las dos actividades deben ser del mismo proyecto';
  end if;
  if exists (with recursive camino(id) as (select new.sucesora_id union select d.sucesora_id from proyectos.dependencia d join camino c on d.predecesora_id = c.id)
             select 1 from camino where id = new.predecesora_id) then
    raise exception 'La dependencia crea un ciclo en el cronograma';
  end if;
  return new;
end $$;
create trigger tg_dependencia_validar before insert or update on proyectos.dependencia for each row execute function proyectos.validar_dependencia();

create or replace function proyectos.avance_actividad() returns trigger language plpgsql as $$
begin
  if new.avance_pct > 0 then new.inicio_real := coalesce(new.inicio_real, current_date); end if;
  if new.avance_pct = 100 then new.fin_real := coalesce(new.fin_real, current_date); end if;
  return new;
end $$;
create trigger tg_actividad_avance before insert or update of avance_pct on proyectos.actividad for each row execute function proyectos.avance_actividad();

create or replace function proyectos.calcular_ruta_critica(p_proyecto bigint) returns integer language plpgsql as $$
declare v_n integer; v_fin integer; v_ini date; i integer;
begin
  select count(*) into v_n from proyectos.actividad where proyecto_id = p_proyecto;
  update proyectos.actividad set inicio_temprano = 0, fin_temprano = duracion_dias where proyecto_id = p_proyecto;
  for i in 1 .. v_n loop  -- pasada hacia adelante (relajación hasta estabilizar)
    update proyectos.actividad a set inicio_temprano = x.es, fin_temprano = x.es + a.duracion_dias
    from (select s.id, greatest(0, max(case d.tipo when 'FC' then p.fin_temprano + d.desfase_dias when 'CC' then p.inicio_temprano + d.desfase_dias
                                                   when 'FF' then p.fin_temprano + d.desfase_dias - s.duracion_dias else p.inicio_temprano + d.desfase_dias - s.duracion_dias end)) es
          from proyectos.actividad s join proyectos.dependencia d on d.sucesora_id = s.id join proyectos.actividad p on p.id = d.predecesora_id
          where s.proyecto_id = p_proyecto group by s.id) x
    where a.id = x.id and a.inicio_temprano <> x.es;
    exit when not found;
  end loop;
  select max(fin_temprano) into v_fin from proyectos.actividad where proyecto_id = p_proyecto;
  update proyectos.actividad set fin_tardio = v_fin, inicio_tardio = v_fin - duracion_dias where proyecto_id = p_proyecto;
  for i in 1 .. v_n loop  -- pasada hacia atrás
    update proyectos.actividad a set fin_tardio = x.lf, inicio_tardio = x.lf - a.duracion_dias
    from (select p.id, least(v_fin, min(case d.tipo when 'FC' then s.inicio_tardio - d.desfase_dias when 'CC' then s.inicio_tardio - d.desfase_dias + p.duracion_dias
                                                   when 'FF' then s.fin_tardio - d.desfase_dias else s.fin_tardio - d.desfase_dias + p.duracion_dias end)) lf
          from proyectos.actividad p join proyectos.dependencia d on d.predecesora_id = p.id join proyectos.actividad s on s.id = d.sucesora_id
          where p.proyecto_id = p_proyecto group by p.id) x
    where a.id = x.id and a.fin_tardio <> x.lf;
    exit when not found;
  end loop;
  select inicio_plan into v_ini from proyectos.proyecto where id = p_proyecto;
  update proyectos.actividad set holgura = inicio_tardio - inicio_temprano, critica = (inicio_tardio - inicio_temprano = 0),
         inicio_plan = case when v_ini is not null then v_ini + inicio_temprano end, fin_plan = case when v_ini is not null then v_ini + fin_temprano end
  where proyecto_id = p_proyecto;
  return v_fin;
end $$;
comment on function proyectos.calcular_ruta_critica(bigint) is 'Método de la ruta crítica (CPM) con relaciones FC, CC, FF y CF: inicio y fin tempranos y tardíos, holgura y actividades críticas; devuelve la duración en días';

create or replace function proyectos.decidir_cambio() returns trigger language plpgsql as $$
begin
  if old.estado <> 'propuesta' and new.estado <> old.estado then raise exception 'La solicitud de cambio ya fue decidida'; end if;
  if new.estado in ('aprobada', 'rechazada') and old.estado = 'propuesta' then
    perform nucleo.exigir_persona('decidir cambios');
    new.decidida_por := coalesce(new.decidida_por, nucleo.usuario_actual()); new.decidida_en := now();
    if new.decidida_por = new.solicitada_por then raise exception 'Quien pide el cambio no lo aprueba'; end if;
  end if;
  return new;
end $$;
create trigger tg_solicitud_cambio_decidir before update on proyectos.solicitud_cambio for each row execute function proyectos.decidir_cambio();

create or replace function proyectos.nueva_linea_base() returns trigger language plpgsql as $$
declare lb proyectos.linea_base;
begin
  if new.estado = 'aprobada' and old.estado = 'propuesta' then
    select * into lb from proyectos.linea_base where proyecto_id = new.proyecto_id order by version desc limit 1;
    if lb.id is null then raise exception 'El proyecto no tiene línea base: apruébelo primero'; end if;
    insert into proyectos.linea_base (proyecto_id, version, presupuesto, fin_plan, alcance, solicitud_cambio_id, aprobada_por)
    values (new.proyecto_id, lb.version + 1, lb.presupuesto + new.impacto_costo, lb.fin_plan + new.impacto_dias,
            lb.alcance || coalesce(E'\n' || new.impacto_alcance, ''), new.id, new.decidida_por);
    update proyectos.proyecto set presupuesto = lb.presupuesto + new.impacto_costo, fin_plan = lb.fin_plan + new.impacto_dias where id = new.proyecto_id;
  end if;
  return null;
end $$;
create trigger tg_solicitud_cambio_linea_base after update on proyectos.solicitud_cambio for each row execute function proyectos.nueva_linea_base();

create or replace function proyectos.calcular_valor_ganado(p_proyecto bigint, p_fecha date default current_date) returns numeric language plpgsql as $$
declare v_bac numeric; v_pv numeric; v_ev numeric; v_ac numeric; v_cpi numeric; v_spi numeric; v_eac numeric;
begin
  select presupuesto into v_bac from proyectos.proyecto where id = p_proyecto;
  select coalesce(sum(costo_plan * case when inicio_plan is null or p_fecha < inicio_plan then 0 when p_fecha >= fin_plan then 1
                                        else (p_fecha - inicio_plan)::numeric / nullif(fin_plan - inicio_plan, 0) end), 0),
         coalesce(sum(costo_plan * avance_pct / 100), 0), coalesce(sum(costo_real), 0)
    into v_pv, v_ev, v_ac from proyectos.actividad where proyecto_id = p_proyecto;
  v_cpi := round(v_ev / nullif(v_ac, 0), 4); v_spi := round(v_ev / nullif(v_pv, 0), 4); v_eac := round(v_bac / nullif(v_cpi, 0), 0);
  insert into proyectos.medicion_valor_ganado (proyecto_id, fecha_corte, pv, ev, ac, cpi, spi, eac, etc, vac)
  values (p_proyecto, p_fecha, round(v_pv, 0), round(v_ev, 0), v_ac, v_cpi, v_spi, v_eac, v_eac - v_ac, v_bac - v_eac)
  on conflict (predio_id, proyecto_id, fecha_corte) do update set pv = excluded.pv, ev = excluded.ev, ac = excluded.ac, cpi = excluded.cpi,
     spi = excluded.spi, eac = excluded.eac, etc = excluded.etc, vac = excluded.vac;
  return v_cpi;
end $$;
comment on function proyectos.calcular_valor_ganado(bigint, date) is 'Valor ganado a una fecha de corte: PV (plan lineal por actividad), EV (avance × costo plan), AC, CPI, SPI, EAC = BAC/CPI, ETC y VAC';

create or replace view proyectos.v_tablero as
select p.id, p.codigo, p.nombre, p.estado, p.area_enfoque, p.enfoque, p.presupuesto, p.fin_plan,
       round(sum(a.costo_plan * a.avance_pct) / nullif(sum(a.costo_plan), 0), 1) as avance_ponderado_pct,
       (select m.cpi from proyectos.medicion_valor_ganado m where m.proyecto_id = p.id order by m.fecha_corte desc limit 1) as cpi,
       (select m.spi from proyectos.medicion_valor_ganado m where m.proyecto_id = p.id order by m.fecha_corte desc limit 1) as spi,
       (select count(*) from proyectos.riesgo r where r.proyecto_id = p.id and r.severidad >= 15 and r.estado <> 'cerrado') as riesgos_altos,
       (select count(*) from proyectos.solicitud_cambio c where c.proyecto_id = p.id and c.estado = 'propuesta') as cambios_pendientes,
       count(a.id) filter (where a.critica and a.avance_pct < 100 and a.fin_plan < current_date) as criticas_atrasadas
from proyectos.proyecto p left join proyectos.actividad a on a.proyecto_id = p.id group by p.id;
comment on view proyectos.v_tablero is 'Tablero de proyectos: avance, CPI, SPI, riesgos altos, cambios por decidir y actividades críticas atrasadas';

-- ============================================================================
-- 31. Análisis financiero: vertical, horizontal y fuentes y usos
-- ============================================================================
create or replace function finanzas.analisis_vertical_horizontal(p_desde_a date, p_hasta_a date, p_desde_b date, p_hasta_b date)
returns table (cuenta varchar, nombre varchar, clase text, valor_a numeric, valor_b numeric, variacion numeric, variacion_pct numeric,
               vertical_a_pct numeric, vertical_b_pct numeric) language sql stable as $$
  with base as (
    select c.codigo, c.nombre, left(c.codigo, 1) clase,
           case when left(c.codigo, 1) in ('1', '2', '3') then finanzas.saldo(c.codigo, null, p_hasta_a) else finanzas.saldo(c.codigo, p_desde_a, p_hasta_a) end a,
           case when left(c.codigo, 1) in ('1', '2', '3') then finanzas.saldo(c.codigo, null, p_hasta_b) else finanzas.saldo(c.codigo, p_desde_b, p_hasta_b) end b
    from finanzas.cuenta_contable c where c.acepta_movimiento),
  tot as (select (finanzas.balance_general(p_hasta_a)->>'activo_total')::numeric ata, (finanzas.balance_general(p_hasta_b)->>'activo_total')::numeric atb,
                 finanzas.saldo('41', p_desde_a, p_hasta_a) va, finanzas.saldo('41', p_desde_b, p_hasta_b) vb)
  select b.codigo, b.nombre, b.clase, b.a, b.b, b.b - b.a, round((b.b - b.a) / nullif(abs(b.a), 0) * 100, 2),
         round(b.a / nullif(case when b.clase in ('1', '2', '3') then t.ata else t.va end, 0) * 100, 2),
         round(b.b / nullif(case when b.clase in ('1', '2', '3') then t.atb else t.vb end, 0) * 100, 2)
  from base b, tot t where b.a <> 0 or b.b <> 0 order by b.codigo $$;
comment on function finanzas.analisis_vertical_horizontal(date, date, date, date) is 'Análisis vertical (peso de cada cuenta sobre el activo total o las ventas) y horizontal (variación absoluta y relativa entre dos periodos)';

create or replace function finanzas.fuentes_usos(p_fecha_a date, p_fecha_b date)
returns table (cuenta varchar, nombre varchar, variacion numeric, clasificacion text) language sql stable as $$
  select c.codigo, c.nombre, x.var,
         case when left(c.codigo, 1) = '1' then case when x.var > 0 then 'uso' else 'fuente' end
              else case when x.var > 0 then 'fuente' else 'uso' end end
  from finanzas.cuenta_contable c
  cross join lateral (select finanzas.saldo(c.codigo, null, p_fecha_b) - finanzas.saldo(c.codigo, null, p_fecha_a) var) x
  where c.acepta_movimiento and left(c.codigo, 1) in ('1', '2', '3') and x.var <> 0 order by 4, 1 $$;
comment on function finanzas.fuentes_usos(date, date) is 'Estado de fuentes y usos: aumento de activo o disminución de pasivo y patrimonio = uso; lo contrario = fuente';

-- ============================================================================
-- 6. Índice semántico y rol de la aplicación
-- ============================================================================
create index ix_fragmento_vector on ia.fragmento_conocimiento using hnsw (vector vector_cosine_ops);

do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'guayacan_app') then
    create role guayacan_app nologin nosuperuser nobypassrls;
  end if;
end $$;
grant usage on schema nucleo, terceros, produccion, riego, inventario, comercial, compras, finanzas, ia, redes, turismo, iot, ambiental, personal, nomina, formacion, activos, documental, cumplimiento, seguros, seguridad, crm, estrategia, agenda, proyectos to guayacan_app;
grant select, insert, update, delete on all tables in schema nucleo, terceros, produccion, riego, inventario, comercial, compras, finanzas, ia, redes, turismo, iot, ambiental, personal, nomina, formacion, activos, documental, cumplimiento, seguros, seguridad, crm, estrategia, agenda, proyectos to guayacan_app;
revoke update, delete on nucleo.auditoria, comercial.huella_trazabilidad, iot.cambio_estado_alarma from guayacan_app;
grant update (anclaje_red, anclaje_transaccion, anclado_en) on comercial.huella_trazabilidad to guayacan_app;
grant execute on all functions in schema nucleo, terceros, produccion, inventario, comercial, finanzas, ia, redes, iot, ambiental,
  personal, nomina, formacion, activos, documental, cumplimiento, seguros, seguridad, crm, estrategia, agenda, proyectos to guayacan_app;
-- Seguridad: los registros de acceso, alertas y pruebas son de solo inserción para la API (la atención de alertas va por columnas)
revoke update, delete on seguridad.intento_acceso, seguridad.ejecucion_prueba, finanzas.reporte_indicadores, finanzas.aplicacion_anticipo from guayacan_app;
revoke update, delete on seguridad.alerta_seguridad from guayacan_app;
grant update (estado, atendida_por, incidente_id, actualizado_en) on seguridad.alerta_seguridad to guayacan_app;
revoke delete on seguridad.copia_seguridad, seguridad.sesion_usuario, seguridad.bloqueo, nomina.pago_nomina, personal.tarea from guayacan_app;
-- Las particiones solo se consultan por la tabla madre (así aplica la seguridad por filas)
do $$ declare r record; begin
  for r in select c.oid::regclass as t from pg_class c where c.relispartition and c.relkind in ('r', 'p') loop
    execute format('revoke all on %s from guayacan_app', r.t);
  end loop;
end $$;
comment on role guayacan_app is 'Rol de la API: sin superusuario ni BYPASSRLS, así la seguridad por filas siempre aplica';


-- Auditoría automática en tablas sensibles
create trigger tg_usuario_auditoria after insert or update or delete on nucleo.usuario for each row execute function nucleo.auditar();
create trigger tg_rol_permiso_auditoria after insert or update or delete on nucleo.rol_permiso for each row execute function nucleo.auditar();
create trigger tg_usuario_rol_auditoria after insert or update or delete on nucleo.usuario_rol for each row execute function nucleo.auditar();
create trigger tg_parametro_auditoria after insert or update or delete on nucleo.parametro for each row execute function nucleo.auditar();
create trigger tg_predio_auditoria after insert or update or delete on nucleo.predio for each row execute function nucleo.auditar();
create trigger tg_tercero_auditoria after insert or update or delete on terceros.tercero for each row execute function nucleo.auditar();
create trigger tg_consentimiento_datos_auditoria after insert or update or delete on terceros.consentimiento_datos for each row execute function nucleo.auditar();
create trigger tg_cliente_auditoria after insert or update or delete on terceros.cliente for each row execute function nucleo.auditar();
create trigger tg_proveedor_auditoria after insert or update or delete on terceros.proveedor for each row execute function nucleo.auditar();
create trigger tg_empleado_auditoria after insert or update or delete on terceros.empleado for each row execute function nucleo.auditar();
create trigger tg_valvula_auditoria after insert or update or delete on riego.valvula for each row execute function nucleo.auditar();
create trigger tg_producto_auditoria after insert or update or delete on inventario.producto for each row execute function nucleo.auditar();
create trigger tg_bodega_auditoria after insert or update or delete on inventario.bodega for each row execute function nucleo.auditar();
create trigger tg_lote_inventario_auditoria after insert or update or delete on inventario.lote_inventario for each row execute function nucleo.auditar();
create trigger tg_lista_precios_auditoria after insert or update or delete on comercial.lista_precios for each row execute function nucleo.auditar();
create trigger tg_precio_producto_auditoria after insert or update or delete on comercial.precio_producto for each row execute function nucleo.auditar();
create trigger tg_propuesta_precio_auditoria after insert or update or delete on comercial.propuesta_precio for each row execute function nucleo.auditar();
create trigger tg_pedido_auditoria after insert or update or delete on comercial.pedido for each row execute function nucleo.auditar();
create trigger tg_pedido_detalle_auditoria after insert or update or delete on comercial.pedido_detalle for each row execute function nucleo.auditar();
create trigger tg_factura_auditoria after insert or update or delete on comercial.factura for each row execute function nucleo.auditar();
create trigger tg_pago_auditoria after insert or update or delete on comercial.pago for each row execute function nucleo.auditar();
create trigger tg_orden_compra_auditoria after insert or update or delete on compras.orden_compra for each row execute function nucleo.auditar();
create trigger tg_comprobante_auditoria after insert or update or delete on finanzas.comprobante for each row execute function nucleo.auditar();
create trigger tg_movimiento_contable_auditoria after insert or update or delete on finanzas.movimiento_contable for each row execute function nucleo.auditar();
create trigger tg_agente_auditoria after insert or update or delete on ia.agente for each row execute function nucleo.auditar();
create trigger tg_herramienta_auditoria after insert or update or delete on ia.herramienta for each row execute function nucleo.auditar();
create trigger tg_agente_herramienta_auditoria after insert or update or delete on ia.agente_herramienta for each row execute function nucleo.auditar();
create trigger tg_solicitud_aprobacion_auditoria after insert or update or delete on ia.solicitud_aprobacion for each row execute function nucleo.auditar();
create trigger tg_documento_conocimiento_auditoria after insert or update or delete on ia.documento_conocimiento for each row execute function nucleo.auditar();
create trigger tg_cuenta_red_auditoria after insert or update or delete on redes.cuenta_red for each row execute function nucleo.auditar();
create trigger tg_publicacion_auditoria after insert or update or delete on redes.publicacion for each row execute function nucleo.auditar();
create trigger tg_actuador_auditoria after insert or update or delete on iot.actuador for each row execute function nucleo.auditar();
create trigger tg_regla_automatizacion_auditoria after insert or update or delete on iot.regla_automatizacion for each row execute function nucleo.auditar();
create trigger tg_dispositivo_captura_auditoria after insert or update or delete on nucleo.dispositivo_captura for each row execute function nucleo.auditar();
create trigger tg_periodo_contable_auditoria after insert or update or delete on finanzas.periodo_contable for each row execute function nucleo.auditar();
create trigger tg_plantilla_mensaje_auditoria after insert or update or delete on redes.plantilla_mensaje for each row execute function nucleo.auditar();
create trigger tg_regla_conversacion_auditoria after insert or update or delete on ia.regla_conversacion for each row execute function nucleo.auditar();
create trigger tg_funcionalidad_auditoria after insert or update or delete on nucleo.funcionalidad for each row execute function nucleo.auditar();
create trigger tg_categoria_huevo_auditoria after insert or update or delete on produccion.categoria_huevo for each row execute function nucleo.auditar();
create trigger tg_vehiculo_auditoria after insert or update or delete on inventario.vehiculo for each row execute function nucleo.auditar();
create trigger tg_bloqueo_lote_auditoria after insert or update or delete on inventario.bloqueo_lote for each row execute function nucleo.auditar();
create trigger tg_retiro_lote_auditoria after insert or update or delete on comercial.retiro_lote for each row execute function nucleo.auditar();
create trigger tg_pedido_recurrente_auditoria after insert or update or delete on comercial.pedido_recurrente for each row execute function nucleo.auditar();
create trigger tg_permuta_auditoria after insert or update or delete on comercial.permuta for each row execute function nucleo.auditar();
create trigger tg_documento_soporte_auditoria after insert or update or delete on compras.documento_soporte for each row execute function nucleo.auditar();
create trigger tg_pieza_audiovisual_auditoria after insert or update or delete on redes.pieza_audiovisual for each row execute function nucleo.auditar();
create trigger tg_zona_seguridad_auditoria after insert or update or delete on iot.zona_seguridad for each row execute function nucleo.auditar();
create trigger tg_credencial_acceso_auditoria after insert or update or delete on iot.credencial_acceso for each row execute function nucleo.auditar();
create trigger tg_camara_auditoria after insert or update or delete on iot.camara for each row execute function nucleo.auditar();
create trigger tg_turno_auditoria after insert or update or delete on personal.turno for each row execute function nucleo.auditar();
create trigger tg_ausencia_auditoria after insert or update or delete on personal.ausencia for each row execute function nucleo.auditar();
create trigger tg_tarea_auditoria after insert or update or delete on personal.tarea for each row execute function nucleo.auditar();
create trigger tg_matriz_responsabilidad_auditoria after insert or update or delete on personal.matriz_responsabilidad for each row execute function nucleo.auditar();
create trigger tg_credencial_trabajo_auditoria after insert or update or delete on personal.credencial_trabajo for each row execute function nucleo.auditar();
create trigger tg_jornada_auditoria after insert or update or delete on personal.jornada for each row execute function nucleo.auditar();
create trigger tg_concepto_nomina_auditoria after insert or update or delete on nomina.concepto_nomina for each row execute function nucleo.auditar();
create trigger tg_periodo_nomina_auditoria after insert or update or delete on nomina.periodo_nomina for each row execute function nucleo.auditar();
create trigger tg_novedad_auditoria after insert or update or delete on nomina.novedad for each row execute function nucleo.auditar();
create trigger tg_liquidacion_auditoria after insert or update or delete on nomina.liquidacion for each row execute function nucleo.auditar();
create trigger tg_documento_nomina_electronica_auditoria after insert or update or delete on nomina.documento_nomina_electronica for each row execute function nucleo.auditar();
create trigger tg_pago_nomina_auditoria after insert or update or delete on nomina.pago_nomina for each row execute function nucleo.auditar();
create trigger tg_certificado_auditoria after insert or update or delete on formacion.certificado for each row execute function nucleo.auditar();
create trigger tg_habilitacion_auditoria after insert or update or delete on formacion.habilitacion for each row execute function nucleo.auditar();
create trigger tg_activo_auditoria after insert or update or delete on activos.activo for each row execute function nucleo.auditar();
create trigger tg_orden_trabajo_auditoria after insert or update or delete on activos.orden_trabajo for each row execute function nucleo.auditar();
create trigger tg_documento_auditoria after insert or update or delete on documental.documento for each row execute function nucleo.auditar();
create trigger tg_version_documento_auditoria after insert or update or delete on documental.version_documento for each row execute function nucleo.auditar();
create trigger tg_expediente_auditoria after insert or update or delete on cumplimiento.expediente for each row execute function nucleo.auditar();
create trigger tg_evaluacion_requisito_auditoria after insert or update or delete on cumplimiento.evaluacion_requisito for each row execute function nucleo.auditar();
create trigger tg_no_conformidad_auditoria after insert or update or delete on cumplimiento.no_conformidad for each row execute function nucleo.auditar();
create trigger tg_accion_correctiva_auditoria after insert or update or delete on cumplimiento.accion_correctiva for each row execute function nucleo.auditar();
create trigger tg_poliza_auditoria after insert or update or delete on seguros.poliza for each row execute function nucleo.auditar();
create trigger tg_aviso_siniestro_auditoria after insert or update or delete on seguros.aviso_siniestro for each row execute function nucleo.auditar();
create trigger tg_diagnostico_imagen_auditoria after insert or update or delete on ia.diagnostico_imagen for each row execute function nucleo.auditar();
create trigger tg_decision_auditoria after insert or update or delete on ia.decision for each row execute function nucleo.auditar();
create trigger tg_presupuesto_auditoria after insert or update or delete on finanzas.presupuesto for each row execute function nucleo.auditar();
create trigger tg_anticipo_proveedor_auditoria after insert or update or delete on finanzas.anticipo_proveedor for each row execute function nucleo.auditar();
create trigger tg_reporte_indicadores_auditoria after insert or update or delete on finanzas.reporte_indicadores for each row execute function nucleo.auditar();
create trigger tg_mision_robot_auditoria after insert or update or delete on iot.mision_robot for each row execute function nucleo.auditar();
create trigger tg_prioridad_carga_auditoria after insert or update or delete on iot.prioridad_carga for each row execute function nucleo.auditar();
create trigger tg_llave_api_auditoria after insert or update or delete on nucleo.llave_api for each row execute function nucleo.auditar();
create trigger tg_webhook_suscripcion_auditoria after insert or update or delete on nucleo.webhook_suscripcion for each row execute function nucleo.auditar();
create trigger tg_factor_autenticacion_auditoria after insert or update or delete on seguridad.factor_autenticacion for each row execute function nucleo.auditar();
create trigger tg_regla_deteccion_auditoria after insert or update or delete on seguridad.regla_deteccion for each row execute function nucleo.auditar();
create trigger tg_bloqueo_auditoria after insert or update or delete on seguridad.bloqueo for each row execute function nucleo.auditar();
create trigger tg_senuelo_auditoria after insert or update or delete on seguridad.senuelo for each row execute function nucleo.auditar();
create trigger tg_incidente_auditoria after insert or update or delete on seguridad.incidente for each row execute function nucleo.auditar();
create trigger tg_formulario_captura_auditoria after insert or update or delete on crm.formulario_captura for each row execute function nucleo.auditar();
create trigger tg_prospecto_auditoria after insert or update or delete on crm.prospecto for each row execute function nucleo.auditar();
create trigger tg_iniciativa_auditoria after insert or update or delete on estrategia.iniciativa for each row execute function nucleo.auditar();
create trigger tg_evaluacion_proyecto_auditoria after insert or update or delete on estrategia.evaluacion_proyecto for each row execute function nucleo.auditar();
create trigger tg_reinversion_auditoria after insert or update or delete on estrategia.reinversion for each row execute function nucleo.auditar();
create trigger tg_miembro_area_auditoria after insert or update or delete on personal.miembro_area for each row execute function nucleo.auditar();
create trigger tg_cronograma_auditoria after insert or update or delete on personal.cronograma for each row execute function nucleo.auditar();
create trigger tg_cita_auditoria after insert or update or delete on agenda.cita for each row execute function nucleo.auditar();
create trigger tg_visita_auditoria after insert or update or delete on agenda.visita for each row execute function nucleo.auditar();
create trigger tg_queja_apelacion_auditoria after insert or update or delete on formacion.queja_apelacion for each row execute function nucleo.auditar();
create trigger tg_proyecto_auditoria after insert or update or delete on proyectos.proyecto for each row execute function nucleo.auditar();
create trigger tg_elemento_edt_auditoria after insert or update or delete on proyectos.elemento_edt for each row execute function nucleo.auditar();
create trigger tg_riesgo_auditoria after insert or update or delete on proyectos.riesgo for each row execute function nucleo.auditar();
create trigger tg_solicitud_cambio_auditoria after insert or update or delete on proyectos.solicitud_cambio for each row execute function nucleo.auditar();
create trigger tg_linea_base_auditoria after insert or update or delete on proyectos.linea_base for each row execute function nucleo.auditar();

-- Comentarios (diccionario dentro de la base)
comment on table nucleo.usuario is 'Persona que entra al sistema (administrador, operario, contador, cliente con cuenta). Reemplaza el usuario de Django (AUTH_USER_MODEL).';
comment on column nucleo.usuario.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.usuario.nombre_completo is 'Nombre y apellidos como se muestran en pantalla';
comment on column nucleo.usuario.correo is 'Correo con el que inicia sesión; no distingue mayúsculas';
comment on column nucleo.usuario.telefono is 'Celular en formato internacional, ej. +573001234567';
comment on column nucleo.usuario.contrasena_hash is 'Contraseña cifrada con Argon2; nunca se guarda en claro';
comment on column nucleo.usuario.es_superusuario is 'Tiene todos los permisos (solo el dueño del sistema)';
comment on column nucleo.usuario.activo is 'Si es falso no puede iniciar sesión (se desactiva en vez de borrar)';
comment on column nucleo.usuario.ultimo_ingreso is 'Fecha y hora del último inicio de sesión';
comment on column nucleo.usuario.tercero_id is 'Persona en el registro de terceros a la que corresponde, si aplica';
comment on column nucleo.usuario.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.usuario.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.rol is 'Conjunto de permisos que se asigna a usuarios o agentes (administrador, operario de granja, contador, vendedor).';
comment on column nucleo.rol.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.rol.codigo is 'Código corto en minúscula, ej. administrador, operario_granja';
comment on column nucleo.rol.nombre is 'Nombre visible del rol';
comment on column nucleo.rol.descripcion is 'Qué puede hacer quien tiene este rol';
comment on column nucleo.rol.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.rol.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.permiso is 'Acción concreta que se puede autorizar, por módulo (ej. comercial.aprobar_precio).';
comment on column nucleo.permiso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.permiso.codigo is 'Código módulo.accion, ej. comercial.aprobar_precio';
comment on column nucleo.permiso.nombre is 'Descripción corta de la acción';
comment on column nucleo.permiso.modulo is 'Módulo al que pertenece (esquema)';
comment on column nucleo.permiso.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.permiso.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.rol_permiso is 'Qué permisos tiene cada rol (relación muchos a muchos).';
comment on column nucleo.rol_permiso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.rol_permiso.rol_id is 'Rol';
comment on column nucleo.rol_permiso.permiso_id is 'Permiso concedido al rol';
comment on table nucleo.usuario_rol is 'Qué roles tiene cada usuario en cada finca (un usuario puede trabajar en varias fincas con roles distintos).';
comment on column nucleo.usuario_rol.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.usuario_rol.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.usuario_rol.usuario_id is 'Usuario';
comment on column nucleo.usuario_rol.rol_id is 'Rol asignado';
comment on table nucleo.parametro is 'Valores de negocio que cambian con el tiempo (IVA, salario mínimo, tarifa de domicilio, margen mínimo). Nunca van fijos en el código.';
comment on column nucleo.parametro.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.parametro.predio_id is 'Finca a la que aplica; vacío = parámetro nacional para todas las fincas (ej. salario mínimo)';
comment on column nucleo.parametro.clave is 'Nombre del parámetro, ej. salario_minimo, iva_general, margen_minimo_huevo';
comment on column nucleo.parametro.valor is 'Valor como texto; se interpreta según tipo_dato';
comment on column nucleo.parametro.tipo_dato is 'Cómo interpretar el valor (valores: entero, decimal, porcentaje, dinero, texto, booleano, json)';
comment on column nucleo.parametro.vigente_desde is 'Primer día en que aplica';
comment on column nucleo.parametro.vigente_hasta is 'Último día en que aplica; vacío = vigente hoy';
comment on column nucleo.parametro.descripcion is 'Para qué se usa y de dónde sale (norma, decreto, decisión)';
comment on column nucleo.parametro.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.parametro.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.auditoria is 'Registro inalterable de cada cambio importante: quién (persona o agente), qué, cuándo y cómo estaba antes. Particionada por mes.';
comment on column nucleo.auditoria.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.auditoria.predio_id is 'Finca en la que ocurrió el cambio (vacío para catálogos compartidos)';
comment on column nucleo.auditoria.esquema_tabla is 'Tabla afectada, ej. comercial.precio_producto';
comment on column nucleo.auditoria.registro_id is 'Id del registro afectado';
comment on column nucleo.auditoria.accion is 'Tipo de acción (valores: crear, actualizar, eliminar, aprobar, rechazar, iniciar_sesion, exportar)';
comment on column nucleo.auditoria.datos_antes is 'Valores antes del cambio';
comment on column nucleo.auditoria.datos_despues is 'Valores después del cambio';
comment on column nucleo.auditoria.usuario_id is 'Persona que hizo o aprobó la acción';
comment on column nucleo.auditoria.agente_id is 'Agente de IA que la propuso o ejecutó, si aplica';
comment on column nucleo.auditoria.direccion_ip is 'IP de origen';
comment on column nucleo.auditoria.ocurrido_en is 'Momento exacto del cambio';
comment on table nucleo.evento_salida is 'Bandeja de salida (patrón outbox): cada hecho de negocio se escribe aquí en la misma transacción y luego se publica a MongoDB, a los agentes y a otros servicios.';
comment on column nucleo.evento_salida.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.evento_salida.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.evento_salida.tipo_evento is 'Nombre del hecho, ej. pedido.confirmado, precio.aprobado';
comment on column nucleo.evento_salida.entidad is 'Tabla de origen';
comment on column nucleo.evento_salida.entidad_id is 'Id del registro de origen';
comment on column nucleo.evento_salida.carga is 'Datos del evento';
comment on column nucleo.evento_salida.estado is 'Si ya se entregó a los consumidores (valores: pendiente, publicado, fallido)';
comment on column nucleo.evento_salida.intentos is 'Veces que se intentó publicar';
comment on column nucleo.evento_salida.publicado_en is 'Cuándo se publicó';
comment on column nucleo.evento_salida.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.evento_salida.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.predio is 'Finca o terreno donde opera el sistema (permite replicarlo en otras fincas).';
comment on column nucleo.predio.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.predio.nombre is 'Nombre de la finca, ej. El Guayacán de los Malaver';
comment on column nucleo.predio.matricula_inmobiliaria is 'Número de matrícula del certificado de tradición';
comment on column nucleo.predio.propietario is 'Titular del predio según el certificado';
comment on column nucleo.predio.tenencia is 'Cómo se usa el predio (valores: propio, comodato, arriendo, otro)';
comment on column nucleo.predio.area_m2 is 'Área total en metros cuadrados';
comment on column nucleo.predio.codigo_dane_municipio is 'Código DANE del municipio (Nilo = 25488)';
comment on column nucleo.predio.vereda is 'Vereda';
comment on column nucleo.predio.geometria is 'Linderos en el sistema de coordenadas oficial CTM12 (EPSG 9377)';
comment on column nucleo.predio.es_practica is 'Finca de práctica para el modo aprendiz: datos de ejemplo aislados de la finca real';
comment on column nucleo.predio.regimen_tributario is 'Régimen del empleador (lo confirma el contador); define si la nómina electrónica es obligatoria (valores: por_definir, ordinario, simple, no_responsable)';
comment on column nucleo.predio.empleador_tercero_id is 'Persona o empresa que figura como empleador';
comment on column nucleo.predio.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.predio.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.zona is 'Área dentro del predio con un uso (galpón, aprisco, estanque, lote de cultivo, potrero, bodega, ronda hídrica).';
comment on column nucleo.zona.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.zona.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.zona.codigo is 'Código corto, ej. GAL-01, EST-02, LOT-C3';
comment on column nucleo.zona.nombre is 'Nombre descriptivo';
comment on column nucleo.zona.tipo_zona is 'Uso de la zona (valores: galpon, aprisco, estanque, lote_cultivo, potrero, bodega, vivienda, ronda_hidrica, apiario, lombricultivo, biodigestor, otra)';
comment on column nucleo.zona.area_m2 is 'Área en metros cuadrados';
comment on column nucleo.zona.capacidad is 'Capacidad máxima (aves, animales, plantas o m³ según el tipo)';
comment on column nucleo.zona.geometria is 'Polígono de la zona en CTM12';
comment on column nucleo.zona.modelo_3d_url is 'Modelo 3D de la zona en el almacén de archivos (gemelo digital, listo para cuando exista el levantamiento)';
comment on column nucleo.zona.activa is 'Si está en uso';
comment on column nucleo.zona.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.zona.actualizado_en is 'Fecha y hora de la última modificación';
comment on table terceros.tercero is 'Toda persona natural o jurídica con la que se relaciona la finca. Un mismo tercero puede ser cliente, proveedor y empleado a la vez.';
comment on column terceros.tercero.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column terceros.tercero.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column terceros.tercero.tipo_persona is 'Persona natural o empresa (valores: natural, juridica)';
comment on column terceros.tercero.tipo_documento is 'Tipo de documento según la DIAN (valores: CC, CE, NIT, PAS, TI, PPT)';
comment on column terceros.tercero.numero_documento is 'Número de documento sin puntos';
comment on column terceros.tercero.digito_verificacion is 'Dígito de verificación del NIT';
comment on column terceros.tercero.nombres is 'Nombres (persona natural)';
comment on column terceros.tercero.apellidos is 'Apellidos (persona natural)';
comment on column terceros.tercero.razon_social is 'Nombre de la empresa (persona jurídica)';
comment on column terceros.tercero.correo is 'Correo de contacto';
comment on column terceros.tercero.telefono is 'Teléfono';
comment on column terceros.tercero.whatsapp is 'Número de WhatsApp en formato internacional';
comment on column terceros.tercero.direccion is 'Dirección o indicación rural';
comment on column terceros.tercero.codigo_dane_municipio is 'Municipio según DANE';
comment on column terceros.tercero.es_cliente is 'Marca rápida de rol';
comment on column terceros.tercero.es_proveedor is 'Marca rápida de rol';
comment on column terceros.tercero.es_empleado is 'Marca rápida de rol';
comment on column terceros.tercero.creado_en is 'Fecha y hora de creación del registro';
comment on column terceros.tercero.actualizado_en is 'Fecha y hora de la última modificación';
comment on table terceros.consentimiento_datos is 'Autorización de tratamiento de datos personales (Ley 1581 de 2012) por finalidad. Sin consentimiento vigente los agentes no personalizan ni envían publicidad.';
comment on column terceros.consentimiento_datos.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column terceros.consentimiento_datos.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column terceros.consentimiento_datos.tercero_id is 'Titular de los datos';
comment on column terceros.consentimiento_datos.finalidad is 'Para qué se autoriza el uso (valores: atencion_pedidos, publicidad, personalizacion_ofertas, analitica, imagen_redes, biometria_acceso)';
comment on column terceros.consentimiento_datos.version_politica is 'Versión de la política de tratamiento aceptada';
comment on column terceros.consentimiento_datos.otorgado is 'Verdadero si autorizó, falso si negó';
comment on column terceros.consentimiento_datos.medio is 'Cómo se obtuvo (valores: whatsapp, web, formulario_fisico, verbal_grabado, correo)';
comment on column terceros.consentimiento_datos.evidencia_url is 'Ubicación de la prueba en el almacén de archivos';
comment on column terceros.consentimiento_datos.otorgado_en is 'Cuándo se dio la respuesta';
comment on column terceros.consentimiento_datos.revocado_en is 'Cuándo la retiró; vacío = vigente';
comment on column terceros.consentimiento_datos.creado_en is 'Fecha y hora de creación del registro';
comment on column terceros.consentimiento_datos.actualizado_en is 'Fecha y hora de la última modificación';
comment on table terceros.cliente is 'Datos comerciales del tercero que compra.';
comment on column terceros.cliente.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column terceros.cliente.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column terceros.cliente.tercero_id is 'Tercero';
comment on column terceros.cliente.segmento is 'Tipo de cliente (restaurante y hotel forman el canal HORECA) (valores: hogar, tienda, restaurante, hotel, asadero, carniceria, mayorista, turista, otro)';
comment on column terceros.cliente.canal_origen is 'Por dónde llegó (valores: whatsapp, web, redes, referido, mercado_campesino, finca, otro)';
comment on column terceros.cliente.frecuencia_compra_dias is 'Cada cuántos días suele comprar (calculado)';
comment on column terceros.cliente.fecha_primera_compra is 'Primera compra';
comment on column terceros.cliente.cupo_credito is 'Monto máximo de cartera abierta (solo aplica si la función venta_credito está activa)';
comment on column terceros.cliente.dias_plazo is 'Días de plazo para pagar una factura a crédito';
comment on column terceros.cliente.bloqueado_por_mora is 'Si tiene facturas vencidas sin pagar no puede comprar a crédito';
comment on column terceros.cliente.lista_precios_id is 'Lista de precios que le aplica';
comment on column terceros.cliente.perfil_interes_ref is 'Id del documento en MongoDB perfiles_interes';
comment on column terceros.cliente.creado_en is 'Fecha y hora de creación del registro';
comment on column terceros.cliente.actualizado_en is 'Fecha y hora de la última modificación';
comment on table terceros.proveedor is 'Datos de compra del tercero que vende insumos o servicios.';
comment on column terceros.proveedor.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column terceros.proveedor.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column terceros.proveedor.tercero_id is 'Tercero';
comment on column terceros.proveedor.categoria is 'Qué suministra (valores: concentrado, animales, semillas, medicamentos, materiales, servicios, transporte, otro)';
comment on column terceros.proveedor.dias_credito is 'Días de plazo que concede';
comment on column terceros.proveedor.calificacion is 'Calificación de 1 a 5 (precio, puntualidad, calidad)';
comment on column terceros.proveedor.creado_en is 'Fecha y hora de creación del registro';
comment on column terceros.proveedor.actualizado_en is 'Fecha y hora de la última modificación';
comment on table terceros.empleado is 'Persona que trabaja en la finca, con su forma de vinculación.';
comment on column terceros.empleado.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column terceros.empleado.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column terceros.empleado.tercero_id is 'Tercero';
comment on column terceros.empleado.cargo is 'Cargo, ej. operario de granja';
comment on column terceros.empleado.tipo_vinculacion is 'Tipo de contrato (valores: termino_fijo, termino_indefinido, jornal, prestacion_servicios, aprendiz)';
comment on column terceros.empleado.salario_base is 'Salario mensual o valor del jornal';
comment on column terceros.empleado.forma_pago is 'Cómo se le paga; el salario fijo nunca depende de tareas aprobadas (valores: salario, jornal, destajo, mixto)';
comment on column terceros.empleado.valor_jornal is 'Valor del jornal, si se le paga por día';
comment on column terceros.empleado.ruta_aprendizaje is 'Ruta de formación por cargo, ej. operario_galpon';
comment on column terceros.empleado.fecha_ingreso is 'Inicio';
comment on column terceros.empleado.fecha_retiro is 'Fin; vacío = activo';
comment on column terceros.empleado.creado_en is 'Fecha y hora de creación del registro';
comment on column terceros.empleado.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.especie is 'Catálogo de especies animales que maneja la finca.';
comment on column produccion.especie.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.especie.codigo is 'Código, ej. gallina, ovino, caprino, tilapia, abeja, lombriz';
comment on column produccion.especie.nombre_comun is 'Nombre común';
comment on column produccion.especie.nombre_cientifico is 'Nombre científico';
comment on column produccion.especie.grupo is 'Grupo productivo (valores: ave, ovino, caprino, pez, abeja, lombriz, otro)';
comment on column produccion.especie.manejo_individual is 'Si se registra animal por animal (ovinos, caprinos) o solo por lote (aves, peces)';
comment on column produccion.especie.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.especie.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.lote_animal is 'Grupo de animales que entra junto y se maneja junto (un lote de 100 gallinas, un ciclo de 1.000 alevinos, un rebaño).';
comment on column produccion.lote_animal.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.lote_animal.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.lote_animal.codigo is 'Código, ej. AV-2026-01';
comment on column produccion.lote_animal.especie_id is 'Especie';
comment on column produccion.lote_animal.zona_id is 'Galpón, aprisco o estanque donde está';
comment on column produccion.lote_animal.raza_linea is 'Raza o línea genética';
comment on column produccion.lote_animal.proposito is 'Para qué se tiene (valores: postura, engorde, cria, reproduccion, miel, humus)';
comment on column produccion.lote_animal.fecha_ingreso is 'Fecha de llegada o nacimiento';
comment on column produccion.lote_animal.edad_ingreso_semanas is 'Edad al llegar';
comment on column produccion.lote_animal.cantidad_inicial is 'Animales al ingresar';
comment on column produccion.lote_animal.cantidad_actual is 'Animales vivos hoy (se actualiza con mortalidad, ventas y nacimientos)';
comment on column produccion.lote_animal.costo_ingreso is 'Costo total de compra del lote';
comment on column produccion.lote_animal.estado is 'Activo o cerrado (vendido o descartado) (valores: activo, cerrado)';
comment on column produccion.lote_animal.fecha_cierre is 'Fecha de cierre';
comment on column produccion.lote_animal.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.lote_animal.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.animal is 'Animal identificado individualmente (ovinos y caprinos), con su genealogía.';
comment on column produccion.animal.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.animal.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.animal.lote_animal_id is 'Lote o rebaño al que pertenece';
comment on column produccion.animal.identificador is 'Número de arete o chapeta';
comment on column produccion.animal.sexo is 'Sexo (valores: hembra, macho)';
comment on column produccion.animal.fecha_nacimiento is 'Nacimiento';
comment on column produccion.animal.madre_id is 'Madre, si nació en la finca';
comment on column produccion.animal.padre_id is 'Padre, si se conoce';
comment on column produccion.animal.estado is 'Situación actual (valores: activo, vendido, muerto, descartado)';
comment on column produccion.animal.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.animal.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.registro_postura is 'Huevos recogidos por día y por lote; las categorías por peso se registran en clasificacion_postura.';
comment on column produccion.registro_postura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.registro_postura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.registro_postura.lote_animal_id is 'Lote de gallinas';
comment on column produccion.registro_postura.fecha is 'Día de recolección';
comment on column produccion.registro_postura.huevos_recogidos is 'Total de huevos recogidos en el día';
comment on column produccion.registro_postura.huevos_rotos is 'Rotos o sucios (no vendibles); la clasificación de los buenos va en clasificacion_postura';
comment on column produccion.registro_postura.registrado_por is 'Quien registró';
comment on column produccion.registro_postura.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.registro_postura.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.registro_postura.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.registro_postura.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.registro_postura.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.registro_alimentacion is 'Alimento suministrado a un lote, distinguiendo lo comprado de lo producido en la finca (base para medir el ahorro).';
comment on column produccion.registro_alimentacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.registro_alimentacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.registro_alimentacion.lote_animal_id is 'Lote alimentado';
comment on column produccion.registro_alimentacion.fecha is 'Día';
comment on column produccion.registro_alimentacion.producto_id is 'Alimento (concentrado, maíz, forraje, lombriz)';
comment on column produccion.registro_alimentacion.cantidad_kg is 'Kilogramos suministrados';
comment on column produccion.registro_alimentacion.origen is 'Comprado o producido en la finca (valores: comprado, propio)';
comment on column produccion.registro_alimentacion.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.registro_alimentacion.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.registro_alimentacion.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.registro_alimentacion.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.registro_alimentacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.evento_sanitario is 'Vacunas, desparasitaciones, tratamientos, revisiones y muertes.';
comment on column produccion.evento_sanitario.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.evento_sanitario.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.evento_sanitario.lote_animal_id is 'Lote afectado';
comment on column produccion.evento_sanitario.animal_id is 'Animal, si el evento es individual';
comment on column produccion.evento_sanitario.fecha is 'Día';
comment on column produccion.evento_sanitario.tipo is 'Tipo de evento (valores: vacuna, desparasitacion, tratamiento, revision, mortalidad, descarte)';
comment on column produccion.evento_sanitario.producto_id is 'Medicamento o vacuna usada';
comment on column produccion.evento_sanitario.dosis is 'Dosis aplicada';
comment on column produccion.evento_sanitario.cantidad_afectada is 'Animales tratados o muertos';
comment on column produccion.evento_sanitario.causa is 'Diagnóstico o causa probable';
comment on column produccion.evento_sanitario.responsable is 'Quien lo aplicó (operario, veterinario)';
comment on column produccion.evento_sanitario.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.evento_sanitario.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.evento_sanitario.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.evento_sanitario.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.evento_sanitario.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.registro_pesaje is 'Pesos de animales o muestras de un lote (corderos, cabritos, tilapia).';
comment on column produccion.registro_pesaje.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.registro_pesaje.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.registro_pesaje.lote_animal_id is 'Lote';
comment on column produccion.registro_pesaje.animal_id is 'Animal pesado, si es individual';
comment on column produccion.registro_pesaje.fecha is 'Día';
comment on column produccion.registro_pesaje.animales_muestreados is 'Cuántos se pesaron';
comment on column produccion.registro_pesaje.peso_promedio_kg is 'Peso promedio en kg';
comment on column produccion.registro_pesaje.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.registro_pesaje.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.registro_pesaje.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.registro_pesaje.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.registro_pesaje.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.evento_reproductivo is 'Montas, partos, abortos y destetes de ovinos y caprinos.';
comment on column produccion.evento_reproductivo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.evento_reproductivo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.evento_reproductivo.hembra_id is 'Hembra';
comment on column produccion.evento_reproductivo.macho_id is 'Macho, en montas';
comment on column produccion.evento_reproductivo.tipo is 'Tipo de evento (valores: monta, parto, aborto, destete)';
comment on column produccion.evento_reproductivo.fecha is 'Día';
comment on column produccion.evento_reproductivo.crias_vivas is 'Crías vivas (partos)';
comment on column produccion.evento_reproductivo.crias_muertas is 'Crías muertas (partos)';
comment on column produccion.evento_reproductivo.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.evento_reproductivo.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.evento_reproductivo.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.evento_reproductivo.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.evento_reproductivo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.calidad_agua_estanque is 'Mediciones del agua de los estanques de peces.';
comment on column produccion.calidad_agua_estanque.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.calidad_agua_estanque.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.calidad_agua_estanque.zona_id is 'Estanque';
comment on column produccion.calidad_agua_estanque.medido_en is 'Fecha y hora';
comment on column produccion.calidad_agua_estanque.oxigeno_mg_l is 'Oxígeno disuelto en mg/L';
comment on column produccion.calidad_agua_estanque.temperatura_c is 'Temperatura en °C';
comment on column produccion.calidad_agua_estanque.ph is 'pH';
comment on column produccion.calidad_agua_estanque.amonio_mg_l is 'Amonio en mg/L';
comment on column produccion.calidad_agua_estanque.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.calidad_agua_estanque.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.calidad_agua_estanque.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.calidad_agua_estanque.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.calidad_agua_estanque.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.cultivo is 'Catálogo de cultivos (plátano, cacao, aguacate papelillo, maíz, frijol, calabacín, forrajes).';
comment on column produccion.cultivo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.cultivo.codigo is 'Código, ej. platano, cacao, maiz';
comment on column produccion.cultivo.nombre_comun is 'Nombre común';
comment on column produccion.cultivo.nombre_cientifico is 'Nombre científico';
comment on column produccion.cultivo.tipo_ciclo is 'Ciclo corto, perenne o forraje (valores: corto, perenne, forraje)';
comment on column produccion.cultivo.dias_a_primera_cosecha is 'Días desde la siembra hasta la primera cosecha';
comment on column produccion.cultivo.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.cultivo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.siembra is 'Una siembra en una zona: cuántas plantas se sembraron y cuántas siguen vivas (ej. 5.000 plátanos previstos, 600 vivos).';
comment on column produccion.siembra.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.siembra.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.siembra.zona_id is 'Lote de cultivo';
comment on column produccion.siembra.cultivo_id is 'Cultivo';
comment on column produccion.siembra.variedad is 'Variedad, ej. papelillo, hartón';
comment on column produccion.siembra.fecha_siembra is 'Fecha de siembra';
comment on column produccion.siembra.plantas_previstas is 'Plantas planeadas';
comment on column produccion.siembra.plantas_sembradas is 'Plantas sembradas';
comment on column produccion.siembra.plantas_vivas is 'Plantas vivas en el último conteo';
comment on column produccion.siembra.semilla_kg is 'Semilla usada en kg (granos)';
comment on column produccion.siembra.area_m2 is 'Área sembrada';
comment on column produccion.siembra.fecha_estimada_cosecha is 'Primera cosecha esperada';
comment on column produccion.siembra.estado is 'Situación actual (valores: planeada, sembrada, en_produccion, recuperacion, perdida, finalizada)';
comment on column produccion.siembra.observaciones is 'Notas (ej. pérdidas por fenómeno de El Niño)';
comment on column produccion.siembra.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.siembra.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.labor_cultural is 'Trabajo hecho a una siembra: encalado, fertilización, deshierbe, control de plagas, poda, resiembra.';
comment on column produccion.labor_cultural.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.labor_cultural.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.labor_cultural.siembra_id is 'Siembra';
comment on column produccion.labor_cultural.fecha is 'Día';
comment on column produccion.labor_cultural.tipo is 'Tipo de labor (valores: encalado, fertilizacion, deshierbe, control_plagas, poda, resiembra, aporque, conteo)';
comment on column produccion.labor_cultural.producto_id is 'Insumo usado';
comment on column produccion.labor_cultural.cantidad is 'Cantidad de insumo';
comment on column produccion.labor_cultural.jornales is 'Jornales empleados';
comment on column produccion.labor_cultural.metodo is 'Cómo se hizo (robot y dron llegan por la interfaz RobotCampo) (valores: manual, mecanico, robot, dron)';
comment on column produccion.labor_cultural.tarea_id is 'Tarea de la que salió';
comment on column produccion.labor_cultural.mision_robot_id is 'Misión de robot o dron que la hizo';
comment on column produccion.labor_cultural.observaciones is 'Notas';
comment on column produccion.labor_cultural.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.labor_cultural.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.labor_cultural.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.labor_cultural.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.labor_cultural.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.cosecha is 'Producto cosechado y a dónde se fue (venta, alimento para los animales, semilla o pérdida).';
comment on column produccion.cosecha.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.cosecha.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.cosecha.siembra_id is 'Siembra';
comment on column produccion.cosecha.fecha is 'Día';
comment on column produccion.cosecha.producto_id is 'Producto resultante';
comment on column produccion.cosecha.cantidad is 'Cantidad';
comment on column produccion.cosecha.destino is 'Destino (valores: venta, alimento_animal, semilla, autoconsumo, perdida)';
comment on column produccion.cosecha.lote_inventario_id is 'Lote de inventario creado al entrar a bodega';
comment on column produccion.cosecha.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.cosecha.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.cosecha.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.cosecha.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.cosecha.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.analisis_suelo is 'Resultados de laboratorio del suelo de una zona y la recomendación de encalado.';
comment on column produccion.analisis_suelo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.analisis_suelo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.analisis_suelo.zona_id is 'Zona muestreada';
comment on column produccion.analisis_suelo.fecha_muestreo is 'Fecha de la muestra';
comment on column produccion.analisis_suelo.laboratorio is 'Laboratorio';
comment on column produccion.analisis_suelo.ph is 'pH';
comment on column produccion.analisis_suelo.materia_organica_pct is 'Materia orgánica %';
comment on column produccion.analisis_suelo.aluminio_cmol_kg is 'Aluminio intercambiable cmol/kg';
comment on column produccion.analisis_suelo.resultados is 'Demás elementos (P, K, Ca, Mg...)';
comment on column produccion.analisis_suelo.recomendacion is 'Recomendación del agrónomo';
comment on column produccion.analisis_suelo.archivo_url is 'PDF del resultado';
comment on column produccion.analisis_suelo.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.analisis_suelo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table riego.fuente_agua is 'De dónde sale el agua (nacedero, acueducto veredal, lluvia, pozo) y su permiso.';
comment on column riego.fuente_agua.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column riego.fuente_agua.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column riego.fuente_agua.nombre is 'Nombre';
comment on column riego.fuente_agua.tipo is 'Tipo de fuente (valores: nacedero, acueducto_veredal, lluvia, pozo, quebrada)';
comment on column riego.fuente_agua.caudal_l_s is 'Caudal disponible en litros por segundo';
comment on column riego.fuente_agua.requiere_concesion is 'Si necesita concesión de la CAR';
comment on column riego.fuente_agua.numero_concesion is 'Número de resolución de la CAR; vacío = en trámite';
comment on column riego.fuente_agua.concesion_vence is 'Vencimiento de la concesión';
comment on column riego.fuente_agua.apta_consumo_humano is 'Si el último análisis la declara potable';
comment on column riego.fuente_agua.creado_en is 'Fecha y hora de creación del registro';
comment on column riego.fuente_agua.actualizado_en is 'Fecha y hora de la última modificación';
comment on table riego.tanque is 'Tanques de almacenamiento (hoy: dos de 2.000 litros).';
comment on column riego.tanque.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column riego.tanque.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column riego.tanque.codigo is 'Código, ej. TQ-01';
comment on column riego.tanque.capacidad_litros is 'Capacidad';
comment on column riego.tanque.fuente_agua_id is 'Fuente que lo llena';
comment on column riego.tanque.zona_id is 'Ubicación';
comment on column riego.tanque.sensor_nivel_id is 'Sensor de nivel (fase IoT)';
comment on column riego.tanque.creado_en is 'Fecha y hora de creación del registro';
comment on column riego.tanque.actualizado_en is 'Fecha y hora de la última modificación';
comment on table riego.sistema_riego is 'Red de riego que cubre una o varias zonas (hoy: manguera con aspersores).';
comment on column riego.sistema_riego.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column riego.sistema_riego.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column riego.sistema_riego.nombre is 'Nombre';
comment on column riego.sistema_riego.tipo is 'Tecnología (valores: aspersion, goteo, microaspersion, manual)';
comment on column riego.sistema_riego.tanque_id is 'Tanque que lo alimenta';
comment on column riego.sistema_riego.caudal_l_min is 'Caudal nominal';
comment on column riego.sistema_riego.modo_control is 'Cómo se acciona hoy (valores: manual, programado, automatico)';
comment on column riego.sistema_riego.creado_en is 'Fecha y hora de creación del registro';
comment on column riego.sistema_riego.actualizado_en is 'Fecha y hora de la última modificación';
comment on table riego.valvula is 'Cada válvula del sistema (hoy manual en cada aspersor; luego electroválvula).';
comment on column riego.valvula.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column riego.valvula.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column riego.valvula.sistema_riego_id is 'Sistema al que pertenece';
comment on column riego.valvula.codigo is 'Código, ej. V-03';
comment on column riego.valvula.zona_id is 'Zona que riega';
comment on column riego.valvula.tipo is 'Manual o eléctrica (valores: manual, electrovalvula)';
comment on column riego.valvula.actuador_id is 'Actuador IoT que la abre (fase IoT)';
comment on column riego.valvula.creado_en is 'Fecha y hora de creación del registro';
comment on column riego.valvula.actualizado_en is 'Fecha y hora de la última modificación';
comment on table riego.evento_riego is 'Cada riego hecho: cuánto tiempo, cuánta agua y si fue manual o automático.';
comment on column riego.evento_riego.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column riego.evento_riego.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column riego.evento_riego.valvula_id is 'Válvula abierta';
comment on column riego.evento_riego.inicio is 'Apertura';
comment on column riego.evento_riego.fin is 'Cierre';
comment on column riego.evento_riego.litros_estimados is 'Litros aplicados (caudal × tiempo)';
comment on column riego.evento_riego.modo is 'Quién lo accionó (valores: manual, programado, automatico)';
comment on column riego.evento_riego.registrado_por is 'Operario, si fue manual';
comment on column riego.evento_riego.regla_id is 'Regla que lo disparó, si fue automático';
comment on column riego.evento_riego.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column riego.evento_riego.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column riego.evento_riego.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column riego.evento_riego.creado_en is 'Fecha y hora de creación del registro';
comment on column riego.evento_riego.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.unidad_medida is 'Unidades (kg, cubeta, unidad, bulto, litro) y su conversión a la unidad base.';
comment on column inventario.unidad_medida.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.unidad_medida.codigo is 'Código, ej. kg, cub30, und, bul40';
comment on column inventario.unidad_medida.nombre is 'Nombre';
comment on column inventario.unidad_medida.unidad_base is 'Unidad a la que se convierte, ej. und o kg';
comment on column inventario.unidad_medida.factor_base is 'Cuántas unidades base contiene (cubeta = 30 und)';
comment on column inventario.unidad_medida.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.unidad_medida.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.categoria_producto is 'Agrupación jerárquica de productos (huevo, carne en pie, granos, insumos, medicamentos).';
comment on column inventario.categoria_producto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.categoria_producto.nombre is 'Nombre';
comment on column inventario.categoria_producto.padre_id is 'Categoría superior';
comment on column inventario.categoria_producto.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.categoria_producto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.producto is 'Todo lo que se vende, se compra o se produce: cubeta de huevo, kg de tilapia, bulto de concentrado.';
comment on column inventario.producto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.producto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.producto.sku is 'Código interno, ej. HUE-AA-30';
comment on column inventario.producto.nombre is 'Nombre comercial';
comment on column inventario.producto.descripcion is 'Descripción para el catálogo y para los agentes';
comment on column inventario.producto.categoria_id is 'Categoría';
comment on column inventario.producto.unidad_id is 'Unidad de venta o de control';
comment on column inventario.producto.tipo is 'Naturaleza (valores: producto_terminado, insumo, servicio, activo_menor)';
comment on column inventario.producto.se_vende is 'Aparece en el catálogo';
comment on column inventario.producto.se_compra is 'Se compra a proveedores';
comment on column inventario.producto.se_produce is 'Se produce en la finca';
comment on column inventario.producto.perecedero is 'Tiene vencimiento';
comment on column inventario.producto.vida_util_ambiente_dias is 'Días que dura a temperatura ambiente (base para estimar el vencimiento)';
comment on column inventario.producto.vida_util_refrigerado_dias is 'Días que dura refrigerado';
comment on column inventario.producto.dias_margen_venta is 'Días antes del vencimiento en que se deja de vender (fecha límite de venta)';
comment on column inventario.producto.dias_alerta_venta is 'Días antes de la fecha límite de venta en que se activa la alerta para venderlo primero';
comment on column inventario.producto.metodo_salida is 'Orden de salida: fefo = primero lo que vence primero; fifo = primero lo que entró primero (valores: fefo, fifo)';
comment on column inventario.producto.gtin is 'Código de barras comercial GS1 (EAN-13 o GTIN-14), si la finca lo obtiene; vacío = solo códigos internos';
comment on column inventario.producto.pesable is 'Se vende o controla por peso leído en báscula (tilapia, cordero en pie)';
comment on column inventario.producto.peso_nominal_kg is 'Peso esperado por unidad, para validar lo que marca la báscula (ej. cubeta)';
comment on column inventario.producto.tolerancia_peso_pct is 'Diferencia máxima aceptada contra el peso nominal antes de alertar';
comment on column inventario.producto.tarifa_iva is 'IVA en %: huevo y carne en pie están excluidos (0)';
comment on column inventario.producto.stock_minimo is 'Alerta de reposición';
comment on column inventario.producto.activo is 'Si se sigue usando';
comment on column inventario.producto.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.producto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.bodega is 'Lugar físico donde se guarda inventario.';
comment on column inventario.bodega.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.bodega.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.bodega.codigo is 'Código';
comment on column inventario.bodega.nombre is 'Nombre';
comment on column inventario.bodega.zona_id is 'Zona del predio';
comment on column inventario.bodega.refrigerada is 'Nevera o cuarto frío; sus lotes usan la vida útil refrigerada';
comment on column inventario.bodega.sensor_temperatura_id is 'Sensor que vigila la temperatura (cadena de frío)';
comment on column inventario.bodega.temperatura_min_c is 'Temperatura mínima aceptada en °C';
comment on column inventario.bodega.temperatura_max_c is 'Temperatura máxima aceptada en °C';
comment on column inventario.bodega.minutos_tolerancia is 'Minutos fuera de rango antes de bloquear los lotes';
comment on column inventario.bodega.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.bodega.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.lote_inventario is 'Existencia concreta de un producto con fecha, origen y vencimiento. Sus cantidades solo las cambia el kardex (movimiento_inventario); la salida sigue el orden FEFO: primero lo que vence primero.';
comment on column inventario.lote_inventario.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.lote_inventario.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.lote_inventario.producto_id is 'Producto';
comment on column inventario.lote_inventario.bodega_id is 'Bodega';
comment on column inventario.lote_inventario.codigo_lote is 'Código de trazabilidad, ej. HUE-20261025-GAL01';
comment on column inventario.lote_inventario.origen is 'De dónde salió (valores: produccion, compra, ajuste)';
comment on column inventario.lote_inventario.origen_tabla is 'Tabla de origen (cosecha, registro_postura, orden_compra_detalle)';
comment on column inventario.lote_inventario.origen_id is 'Id en la tabla de origen';
comment on column inventario.lote_inventario.fecha_produccion is 'Fecha de producción, postura, cosecha o recepción';
comment on column inventario.lote_inventario.condicion_almacenamiento is 'Cómo se guarda; cambia la vida útil usada en la estimación (valores: ambiente, refrigerado)';
comment on column inventario.lote_inventario.origen_vencimiento is 'estimado = lo calcula el sistema con la vida útil del producto; manual o laboratorio = lo fija una persona (valores: estimado, manual, laboratorio)';
comment on column inventario.lote_inventario.fecha_vencimiento is 'Fecha en que el producto deja de ser apto (calculada si origen_vencimiento = estimado)';
comment on column inventario.lote_inventario.fecha_limite_venta is 'Último día para venderlo: vencimiento menos los días de margen del producto';
comment on column inventario.lote_inventario.peso_neto_kg is 'Peso total leído en báscula al ingresar, si el producto es pesable';
comment on column inventario.lote_inventario.cantidad_inicial is 'Cantidad al crearse (genera automáticamente el movimiento de entrada)';
comment on column inventario.lote_inventario.cantidad_disponible is 'Libre para vender; solo la cambia el kardex';
comment on column inventario.lote_inventario.cantidad_reservada is 'Comprometida en pedidos confirmados; solo la cambia el kardex';
comment on column inventario.lote_inventario.costo_unitario is 'Costo por unidad';
comment on column inventario.lote_inventario.estado is 'Situación: agotado y vencido los pone el sistema; bloqueado lo pone un bloqueo_lote abierto (cadena de frío, sanidad, retiro) (valores: disponible, agotado, vencido, bloqueado)';
comment on column inventario.lote_inventario.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.lote_inventario.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.movimiento_inventario is 'Kardex: cada entrada, salida, ajuste, traslado o merma, con el documento que lo causó.';
comment on column inventario.movimiento_inventario.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.movimiento_inventario.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.movimiento_inventario.lote_inventario_id is 'Lote movido';
comment on column inventario.movimiento_inventario.tipo is 'Tipo de movimiento; define qué cantidad del lote cambia (ver reglas del kardex) (valores: entrada, reserva, liberacion, salida_venta, consumo_interno, merma, ajuste_entrada, ajuste_salida, traslado_salida, traslado_entrada)';
comment on column inventario.movimiento_inventario.cantidad is 'Cantidad (siempre positiva; el tipo da el sentido)';
comment on column inventario.movimiento_inventario.causa_merma is 'Por qué se perdió, cuando tipo = merma (alimenta el ajuste de la vida útil estimada) (valores: vencido, roto, plaga, calidad, robo, otro)';
comment on column inventario.movimiento_inventario.pesaje_id is 'Lectura de báscula que respalda la cantidad, si aplica';
comment on column inventario.movimiento_inventario.lectura_codigo_id is 'Escaneo de código que originó el movimiento, si aplica';
comment on column inventario.movimiento_inventario.costo_unitario is 'Costo usado';
comment on column inventario.movimiento_inventario.documento_tipo is 'Documento origen, ej. pedido, cosecha, orden_compra';
comment on column inventario.movimiento_inventario.documento_id is 'Id del documento';
comment on column inventario.movimiento_inventario.ocurrido_en is 'Momento';
comment on column inventario.movimiento_inventario.usuario_id is 'Quién lo registró';
comment on column inventario.movimiento_inventario.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column inventario.movimiento_inventario.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column inventario.movimiento_inventario.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column inventario.movimiento_inventario.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.movimiento_inventario.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.lista_precios is 'Lista de precios por canal o tipo de cliente (público, tiendas, restaurantes, mayoristas).';
comment on column comercial.lista_precios.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.lista_precios.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.lista_precios.codigo is 'Código, ej. PUBLICO, TIENDAS';
comment on column comercial.lista_precios.nombre is 'Nombre';
comment on column comercial.lista_precios.activa is 'En uso';
comment on column comercial.lista_precios.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.lista_precios.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.precio_producto is 'Precio de un producto en una lista, con vigencia. Nunca se edita un precio: se cierra el vigente y se crea uno nuevo, así el historial queda completo.';
comment on column comercial.precio_producto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.precio_producto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.precio_producto.lista_precios_id is 'Lista';
comment on column comercial.precio_producto.producto_id is 'Producto';
comment on column comercial.precio_producto.precio_unitario is 'Precio por unidad de venta';
comment on column comercial.precio_producto.incluye_iva is 'Si el precio ya incluye IVA';
comment on column comercial.precio_producto.vigente_desde is 'Desde cuándo aplica';
comment on column comercial.precio_producto.vigente_hasta is 'Hasta cuándo; vacío = vigente';
comment on column comercial.precio_producto.propuesta_precio_id is 'Propuesta que lo originó, si vino de un agente';
comment on column comercial.precio_producto.aprobado_por is 'Administrador que lo autorizó';
comment on column comercial.precio_producto.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.precio_producto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.propuesta_precio is 'Cambio de precio sugerido por el agente analista de mercados. Solo se aplica cuando el administrador lo aprueba.';
comment on column comercial.propuesta_precio.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.propuesta_precio.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.propuesta_precio.producto_id is 'Producto';
comment on column comercial.propuesta_precio.lista_precios_id is 'Lista afectada';
comment on column comercial.propuesta_precio.precio_actual is 'Precio vigente al proponer';
comment on column comercial.propuesta_precio.precio_propuesto is 'Precio sugerido';
comment on column comercial.propuesta_precio.variacion_pct is 'Variación porcentual';
comment on column comercial.propuesta_precio.justificacion is 'Razones en lenguaje claro';
comment on column comercial.propuesta_precio.evidencia is 'Fuentes consultadas (SIPSA, competidores, costos) con fecha y enlace';
comment on column comercial.propuesta_precio.agente_id is 'Agente que la generó';
comment on column comercial.propuesta_precio.estado is 'Situación (valores: pendiente, aprobada, rechazada, vencida, aplicada)';
comment on column comercial.propuesta_precio.vence_en is 'Si nadie la revisa antes, queda vencida';
comment on column comercial.propuesta_precio.revisado_por is 'Administrador que decidió';
comment on column comercial.propuesta_precio.revisado_en is 'Cuándo decidió';
comment on column comercial.propuesta_precio.comentario_revision is 'Motivo de la decisión';
comment on column comercial.propuesta_precio.aplicada_en is 'Cuándo entró en vigencia';
comment on column comercial.propuesta_precio.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.propuesta_precio.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.pedido is 'Solicitud de compra de un cliente por cualquier canal; puede crearla una persona o un agente.';
comment on column comercial.pedido.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.pedido.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.pedido.numero is 'Consecutivo, ej. PED-000123';
comment on column comercial.pedido.cliente_id is 'Cliente';
comment on column comercial.pedido.canal is 'Canal (valores: whatsapp, web, redes, telefono, finca, mercado_campesino)';
comment on column comercial.pedido.estado is 'Situación (valores: borrador, confirmado, en_preparacion, despachado, entregado, cancelado)';
comment on column comercial.pedido.forma_pago is 'Crédito exige la función venta_credito activa, cliente sin mora y cupo disponible (valores: contado, credito)';
comment on column comercial.pedido.pedido_recurrente_id is 'Pedido recurrente que lo generó, si aplica';
comment on column comercial.pedido.fecha_entrega_programada is 'Día de entrega acordado';
comment on column comercial.pedido.direccion_entrega is 'Dirección de entrega';
comment on column comercial.pedido.subtotal is 'Suma de líneas sin impuestos';
comment on column comercial.pedido.descuento is 'Descuentos';
comment on column comercial.pedido.impuestos is 'IVA';
comment on column comercial.pedido.valor_domicilio is 'Cobro de entrega';
comment on column comercial.pedido.total is 'Total a pagar';
comment on column comercial.pedido.conversacion_ref is 'Id de la conversación en MongoDB que originó el pedido';
comment on column comercial.pedido.creado_por_agente_id is 'Agente que lo tomó, si aplica';
comment on column comercial.pedido.vendedor_id is 'Persona responsable';
comment on column comercial.pedido.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column comercial.pedido.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column comercial.pedido.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column comercial.pedido.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.pedido.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.pedido_detalle is 'Línea del pedido. El precio queda congelado al confirmar: un cambio de precio posterior no la afecta.';
comment on column comercial.pedido_detalle.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.pedido_detalle.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.pedido_detalle.pedido_id is 'Pedido';
comment on column comercial.pedido_detalle.producto_id is 'Producto';
comment on column comercial.pedido_detalle.cantidad is 'Cantidad (los lotes reservados quedan en comercial.reserva_lote)';
comment on column comercial.pedido_detalle.precio_producto_id is 'Precio vigente usado';
comment on column comercial.pedido_detalle.precio_unitario is 'Precio copiado (congelado) al confirmar';
comment on column comercial.pedido_detalle.descuento is 'Descuento de la línea';
comment on column comercial.pedido_detalle.tarifa_iva is 'IVA aplicado';
comment on column comercial.pedido_detalle.total_linea is 'Total de la línea';
comment on column comercial.pedido_detalle.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.pedido_detalle.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.factura is 'Factura electrónica (o documento equivalente) generada por regla fija, no por la IA, y validada por la DIAN.';
comment on column comercial.factura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.factura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.factura.prefijo is 'Prefijo autorizado por la DIAN';
comment on column comercial.factura.numero is 'Número dentro del rango autorizado';
comment on column comercial.factura.pedido_id is 'Pedido facturado';
comment on column comercial.factura.cliente_id is 'Cliente';
comment on column comercial.factura.fecha_emision is 'Fecha y hora de emisión';
comment on column comercial.factura.subtotal is 'Base';
comment on column comercial.factura.iva is 'IVA';
comment on column comercial.factura.total is 'Total';
comment on column comercial.factura.forma_pago is 'Forma de pago (valores: contado, credito)';
comment on column comercial.factura.fecha_vencimiento is 'Fecha límite de pago (crédito): emisión más los días de plazo del cliente';
comment on column comercial.factura.saldo is 'Lo que falta por pagar; lo mantienen los pagos confirmados y las permutas';
comment on column comercial.factura.cufe is 'Código único de factura electrónica';
comment on column comercial.factura.estado_dian is 'Respuesta de la DIAN (valores: pendiente, aceptada, rechazada, no_aplica)';
comment on column comercial.factura.xml_url is 'XML en el almacén de archivos';
comment on column comercial.factura.pdf_url is 'Representación gráfica';
comment on column comercial.factura.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.factura.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.pago is 'Dinero recibido por un pedido o factura.';
comment on column comercial.pago.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.pago.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.pago.pedido_id is 'Pedido';
comment on column comercial.pago.factura_id is 'Factura';
comment on column comercial.pago.fecha is 'Momento del pago';
comment on column comercial.pago.valor is 'Valor';
comment on column comercial.pago.medio is 'Medio de pago; compensacion_permuta = saldado con una permuta (valores: efectivo, nequi, daviplata, transferencia, tarjeta, bre_b, pasarela, compensacion_permuta)';
comment on column comercial.pago.proveedor_pasarela is 'Pasarela de pago local, si medio = pasarela (Stripe no opera en Colombia) (valores: wompi, mercado_pago, epayco, payu)';
comment on column comercial.pago.id_transaccion_pasarela is 'Id de la transacción en la pasarela (llave de idempotencia del webhook)';
comment on column comercial.pago.referencia is 'Número de transacción';
comment on column comercial.pago.estado is 'Situación (valores: pendiente, confirmado, reversado)';
comment on column comercial.pago.confirmado_por is 'Quién verificó el ingreso (un agente nunca confirma pagos)';
comment on column comercial.pago.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column comercial.pago.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column comercial.pago.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column comercial.pago.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.pago.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.entrega is 'Despacho de un pedido.';
comment on column comercial.entrega.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.entrega.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.entrega.pedido_id is 'Pedido';
comment on column comercial.entrega.fecha_salida is 'Salida de la finca';
comment on column comercial.entrega.fecha_entrega is 'Recepción por el cliente';
comment on column comercial.entrega.responsable is 'Quien entrega';
comment on column comercial.entrega.vehiculo_id is 'Vehículo usado (su registrador de temperatura vigila la cadena de frío en ruta)';
comment on column comercial.entrega.estado is 'Situación (valores: programada, en_ruta, entregada, fallida)';
comment on column comercial.entrega.evidencia_url is 'Foto o firma';
comment on column comercial.entrega.calificacion_cliente is 'De 1 a 5';
comment on column comercial.entrega.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column comercial.entrega.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column comercial.entrega.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column comercial.entrega.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.entrega.actualizado_en is 'Fecha y hora de la última modificación';
comment on table compras.orden_compra is 'Compra a un proveedor.';
comment on column compras.orden_compra.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column compras.orden_compra.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column compras.orden_compra.numero is 'Consecutivo';
comment on column compras.orden_compra.proveedor_id is 'Proveedor';
comment on column compras.orden_compra.fecha is 'Fecha';
comment on column compras.orden_compra.estado is 'Situación (valores: borrador, aprobada, recibida, parcial, anulada)';
comment on column compras.orden_compra.total is 'Total';
comment on column compras.orden_compra.aprobado_por is 'Quién la aprobó';
comment on column compras.orden_compra.creado_en is 'Fecha y hora de creación del registro';
comment on column compras.orden_compra.actualizado_en is 'Fecha y hora de la última modificación';
comment on table compras.orden_compra_detalle is 'Línea de la orden de compra.';
comment on column compras.orden_compra_detalle.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column compras.orden_compra_detalle.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column compras.orden_compra_detalle.orden_compra_id is 'Orden';
comment on column compras.orden_compra_detalle.producto_id is 'Insumo';
comment on column compras.orden_compra_detalle.cantidad is 'Cantidad pedida';
comment on column compras.orden_compra_detalle.cantidad_recibida is 'Cantidad recibida';
comment on column compras.orden_compra_detalle.precio_unitario is 'Precio pactado';
comment on column compras.orden_compra_detalle.creado_en is 'Fecha y hora de creación del registro';
comment on column compras.orden_compra_detalle.actualizado_en is 'Fecha y hora de la última modificación';
comment on table compras.cotizacion_proveedor is 'Precio ofrecido por un proveedor para un insumo, registrado por una persona o por el agente de mercados.';
comment on column compras.cotizacion_proveedor.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column compras.cotizacion_proveedor.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column compras.cotizacion_proveedor.proveedor_id is 'Proveedor, si está registrado';
comment on column compras.cotizacion_proveedor.nombre_proveedor is 'Nombre si aún no es tercero';
comment on column compras.cotizacion_proveedor.producto_id is 'Insumo';
comment on column compras.cotizacion_proveedor.precio_unitario is 'Precio';
comment on column compras.cotizacion_proveedor.fecha is 'Fecha de la cotización';
comment on column compras.cotizacion_proveedor.vigente_hasta is 'Validez';
comment on column compras.cotizacion_proveedor.fuente is 'Cómo se obtuvo (valores: visita, telefono, correo, web, agente)';
comment on column compras.cotizacion_proveedor.fuente_url is 'Enlace, si es web';
comment on column compras.cotizacion_proveedor.creado_en is 'Fecha y hora de creación del registro';
comment on column compras.cotizacion_proveedor.actualizado_en is 'Fecha y hora de la última modificación';
comment on table compras.precio_mercado is 'Precio de referencia de un producto en un mercado (SIPSA-DANE, Corabastos, Fenavi), usado por el agente analista.';
comment on column compras.precio_mercado.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column compras.precio_mercado.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column compras.precio_mercado.producto_id is 'Producto comparable';
comment on column compras.precio_mercado.mercado is 'Mercado o fuente, ej. Corabastos, SIPSA Girardot';
comment on column compras.precio_mercado.fecha is 'Fecha del dato';
comment on column compras.precio_mercado.precio_minimo is 'Mínimo';
comment on column compras.precio_mercado.precio_maximo is 'Máximo';
comment on column compras.precio_mercado.precio_promedio is 'Promedio';
comment on column compras.precio_mercado.unidad is 'Unidad del dato, ej. kg, cubeta';
comment on column compras.precio_mercado.fuente_url is 'Enlace';
comment on column compras.precio_mercado.creado_en is 'Fecha y hora de creación del registro';
comment on column compras.precio_mercado.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.cuenta_contable is 'Plan Único de Cuentas (PUC) adaptado a la finca.';
comment on column finanzas.cuenta_contable.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.cuenta_contable.codigo is 'Código PUC, ej. 413505';
comment on column finanzas.cuenta_contable.nombre is 'Nombre';
comment on column finanzas.cuenta_contable.naturaleza is 'Naturaleza (valores: debito, credito)';
comment on column finanzas.cuenta_contable.nivel is '1 clase, 2 grupo, 3 cuenta, 4 subcuenta, 5 auxiliar';
comment on column finanzas.cuenta_contable.padre_id is 'Cuenta superior';
comment on column finanzas.cuenta_contable.acepta_movimiento is 'Solo las auxiliares reciben movimientos';
comment on column finanzas.cuenta_contable.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.cuenta_contable.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.centro_costo is 'Unidad de negocio para medir rentabilidad (avícola, ovino-caprino, piscícola, ciclo corto, perennes, turismo, administración).';
comment on column finanzas.centro_costo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.centro_costo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.centro_costo.codigo is 'Código, ej. AVI';
comment on column finanzas.centro_costo.nombre is 'Nombre';
comment on column finanzas.centro_costo.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.centro_costo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.comprobante is 'Documento contable (ingreso, egreso, nota, causación). Lo generan reglas a partir de ventas, compras y nómina; el agente contador solo sugiere.';
comment on column finanzas.comprobante.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.comprobante.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.comprobante.tipo is 'Tipo (valores: ingreso, egreso, nota_contable, causacion, nomina, ajuste)';
comment on column finanzas.comprobante.numero is 'Consecutivo por tipo';
comment on column finanzas.comprobante.fecha is 'Fecha contable';
comment on column finanzas.comprobante.descripcion is 'Concepto';
comment on column finanzas.comprobante.origen_tabla is 'Documento de negocio que lo generó';
comment on column finanzas.comprobante.origen_id is 'Id del documento';
comment on column finanzas.comprobante.estado is 'Situación; solo se contabiliza si débitos = créditos y el periodo está abierto (valores: borrador, contabilizado, anulado)';
comment on column finanzas.comprobante.aprobado_por is 'Quien lo contabilizó';
comment on column finanzas.comprobante.contabilizado_en is 'Momento en que quedó contabilizado (desde ahí sus movimientos no se pueden cambiar)';
comment on column finanzas.comprobante.motivo_anulacion is 'Por qué se anuló';
comment on column finanzas.comprobante.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.comprobante.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.movimiento_contable is 'Línea débito o crédito de un comprobante.';
comment on column finanzas.movimiento_contable.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.movimiento_contable.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.movimiento_contable.comprobante_id is 'Comprobante';
comment on column finanzas.movimiento_contable.cuenta_id is 'Cuenta';
comment on column finanzas.movimiento_contable.tercero_id is 'Tercero';
comment on column finanzas.movimiento_contable.centro_costo_id is 'Centro de costo';
comment on column finanzas.movimiento_contable.debito is 'Débito';
comment on column finanzas.movimiento_contable.credito is 'Crédito';
comment on column finanzas.movimiento_contable.detalle is 'Detalle';
comment on column finanzas.movimiento_contable.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.movimiento_contable.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.agente is 'Agente de IA con un rol, sus instrucciones versionadas, su modelo y su nivel de autonomía.';
comment on column ia.agente.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.agente.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.agente.codigo is 'Código, ej. asesor_clientes, analista_mercados';
comment on column ia.agente.nombre is 'Nombre visible, ej. Asesor virtual';
comment on column ia.agente.rol is 'Qué hace y qué no hace';
comment on column ia.agente.nivel_autonomia is 'Hasta dónde puede actuar (valores: solo_lectura, propone, ejecuta_con_regla)';
comment on column ia.agente.proveedor_modelo is 'Proveedor, ej. anthropic';
comment on column ia.agente.modelo is 'Modelo, ej. claude-sonnet-5-5';
comment on column ia.agente.modelo_respaldo is 'Modelo si el principal falla';
comment on column ia.agente.version_instrucciones is 'Versión del prompt de sistema vigente';
comment on column ia.agente.instrucciones is 'Prompt de sistema vigente';
comment on column ia.agente.limite_costo_diario_usd is 'Tope de gasto por día';
comment on column ia.agente.activo is 'Si atiende';
comment on column ia.agente.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.agente.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.herramienta is 'Función del ERP que un agente puede invocar (por MCP o API), con su nivel de riesgo.';
comment on column ia.herramienta.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.herramienta.codigo is 'Código, ej. consultar_catalogo, proponer_precio';
comment on column ia.herramienta.descripcion is 'Qué hace (es lo que lee el modelo)';
comment on column ia.herramienta.tipo is 'Lectura no cambia nada; propuesta crea una solicitud; escritura cambia datos (valores: lectura, propuesta, escritura)';
comment on column ia.herramienta.requiere_aprobacion is 'Si cada uso pasa por un humano';
comment on column ia.herramienta.esquema_entrada is 'JSON Schema de los parámetros';
comment on column ia.herramienta.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.herramienta.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.agente_herramienta is 'Qué herramientas puede usar cada agente (mínimo privilegio).';
comment on column ia.agente_herramienta.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.agente_herramienta.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.agente_herramienta.agente_id is 'Agente';
comment on column ia.agente_herramienta.herramienta_id is 'Herramienta';
comment on table ia.solicitud_aprobacion is 'Bandeja del administrador: toda acción que un agente quiere hacer y requiere permiso humano.';
comment on column ia.solicitud_aprobacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.solicitud_aprobacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.solicitud_aprobacion.agente_id is 'Agente que pide';
comment on column ia.solicitud_aprobacion.herramienta_id is 'Acción solicitada';
comment on column ia.solicitud_aprobacion.entidad is 'Tabla afectada, ej. comercial.propuesta_precio';
comment on column ia.solicitud_aprobacion.entidad_id is 'Registro afectado';
comment on column ia.solicitud_aprobacion.resumen is 'Qué se pide, en una frase';
comment on column ia.solicitud_aprobacion.carga is 'Parámetros exactos que se ejecutarán';
comment on column ia.solicitud_aprobacion.estado is 'Situación (valores: pendiente, aprobada, rechazada, vencida, ejecutada, fallida)';
comment on column ia.solicitud_aprobacion.vence_en is 'Límite para decidir';
comment on column ia.solicitud_aprobacion.resuelto_por is 'Quién decidió';
comment on column ia.solicitud_aprobacion.resuelto_en is 'Cuándo';
comment on column ia.solicitud_aprobacion.motivo is 'Motivo de la decisión';
comment on column ia.solicitud_aprobacion.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.solicitud_aprobacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.documento_conocimiento is 'Fuente de la base de conocimiento: fichas de producto, políticas, preguntas frecuentes, manuales técnicos, informes.';
comment on column ia.documento_conocimiento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.documento_conocimiento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.documento_conocimiento.titulo is 'Título';
comment on column ia.documento_conocimiento.tipo is 'Tipo (valores: ficha_producto, politica, pregunta_frecuente, manual_tecnico, informe, receta, turismo)';
comment on column ia.documento_conocimiento.contenido is 'Texto completo';
comment on column ia.documento_conocimiento.fuente is 'Origen (archivo, URL, autor)';
comment on column ia.documento_conocimiento.version is 'Versión';
comment on column ia.documento_conocimiento.vigente is 'Si los agentes lo usan';
comment on column ia.documento_conocimiento.aprobado_por is 'Quién validó el contenido';
comment on column ia.documento_conocimiento.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.documento_conocimiento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.fragmento_conocimiento is 'Trozo de un documento con su vector semántico (pgvector) para que los agentes encuentren la información relevante (RAG).';
comment on column ia.fragmento_conocimiento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.fragmento_conocimiento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.fragmento_conocimiento.documento_id is 'Documento';
comment on column ia.fragmento_conocimiento.orden is 'Posición dentro del documento';
comment on column ia.fragmento_conocimiento.texto is 'Texto del fragmento';
comment on column ia.fragmento_conocimiento.vector is 'Representación numérica del significado (embedding)';
comment on column ia.fragmento_conocimiento.metadatos is 'Producto, tema, vigencia';
comment on column ia.fragmento_conocimiento.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.fragmento_conocimiento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.recomendacion is 'Plan de acción o mejora continua propuesto por un agente analista, con su seguimiento (ciclo PHVA).';
comment on column ia.recomendacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.recomendacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.recomendacion.agente_id is 'Agente que la propone';
comment on column ia.recomendacion.tipo is 'Tipo (valores: mejora_continua, comercial, compra, produccion, contenido_redes, riesgo)';
comment on column ia.recomendacion.titulo is 'Título';
comment on column ia.recomendacion.descripcion is 'Qué hacer y por qué';
comment on column ia.recomendacion.evidencia is 'Datos que la sustentan';
comment on column ia.recomendacion.indicador is 'Indicador que debería mejorar';
comment on column ia.recomendacion.prioridad is 'Prioridad (valores: alta, media, baja)';
comment on column ia.recomendacion.estado is 'Situación (valores: nueva, aceptada, descartada, en_ejecucion, cumplida)';
comment on column ia.recomendacion.responsable_id is 'Responsable';
comment on column ia.recomendacion.fecha_limite is 'Plazo';
comment on column ia.recomendacion.resultado is 'Qué pasó al ejecutarla (aprendizaje)';
comment on column ia.recomendacion.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.recomendacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.evaluacion_respuesta is 'Calificación de una respuesta de un agente por el cliente o el administrador; alimenta la mejora de instrucciones y conocimiento.';
comment on column ia.evaluacion_respuesta.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.evaluacion_respuesta.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.evaluacion_respuesta.agente_id is 'Agente evaluado';
comment on column ia.evaluacion_respuesta.mensaje_ref is 'Id del mensaje en MongoDB';
comment on column ia.evaluacion_respuesta.origen is 'Quién califica (valores: cliente, administrador, evaluacion_automatica)';
comment on column ia.evaluacion_respuesta.calificacion is 'De 1 a 5';
comment on column ia.evaluacion_respuesta.motivo is 'Motivo (valores: correcta, incorrecta, incompleta, tono, demora, otro)';
comment on column ia.evaluacion_respuesta.comentario is 'Comentario';
comment on column ia.evaluacion_respuesta.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.evaluacion_respuesta.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.consumo_ia is 'Tokens y costo por agente, modelo y día, para controlar el gasto.';
comment on column ia.consumo_ia.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.consumo_ia.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.consumo_ia.agente_id is 'Agente';
comment on column ia.consumo_ia.fecha is 'Día';
comment on column ia.consumo_ia.proveedor_modelo is 'Proveedor';
comment on column ia.consumo_ia.modelo is 'Modelo';
comment on column ia.consumo_ia.solicitudes is 'Llamadas';
comment on column ia.consumo_ia.tokens_entrada is 'Tokens enviados';
comment on column ia.consumo_ia.tokens_salida is 'Tokens generados';
comment on column ia.consumo_ia.costo_usd is 'Costo en dólares';
comment on column ia.consumo_ia.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.consumo_ia.actualizado_en is 'Fecha y hora de la última modificación';
comment on table redes.cuenta_red is 'Cuenta de la finca en un canal de mensajería o red social; las credenciales van en el gestor de secretos, no aquí.';
comment on column redes.cuenta_red.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column redes.cuenta_red.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column redes.cuenta_red.plataforma is 'Canal (whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina)';
comment on column redes.cuenta_red.nombre_cuenta is 'Nombre o número';
comment on column redes.cuenta_red.identificador_externo is 'Id en la plataforma';
comment on column redes.cuenta_red.secreto_ref is 'Nombre del secreto con el token de acceso';
comment on column redes.cuenta_red.activa is 'En uso';
comment on column redes.cuenta_red.creado_en is 'Fecha y hora de creación del registro';
comment on column redes.cuenta_red.actualizado_en is 'Fecha y hora de la última modificación';
comment on table redes.publicacion is 'Contenido para redes: lo redacta el agente de redes y se publica solo con aprobación.';
comment on column redes.publicacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column redes.publicacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column redes.publicacion.cuenta_red_id is 'Cuenta';
comment on column redes.publicacion.texto is 'Texto';
comment on column redes.publicacion.medios is 'Imágenes o videos (rutas en MinIO)';
comment on column redes.publicacion.estado is 'Situación (valores: borrador, propuesta, aprobada, programada, publicada, rechazada)';
comment on column redes.publicacion.programada_para is 'Fecha de publicación';
comment on column redes.publicacion.publicada_en is 'Fecha real';
comment on column redes.publicacion.id_externo is 'Id en la plataforma';
comment on column redes.publicacion.agente_id is 'Agente que la redactó';
comment on column redes.publicacion.aprobado_por is 'Quién la aprobó';
comment on column redes.publicacion.recomendacion_id is 'Recomendación que la motivó';
comment on column redes.publicacion.creado_en is 'Fecha y hora de creación del registro';
comment on column redes.publicacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table turismo.alojamiento is 'Cabaña o espacio de hospedaje.';
comment on column turismo.alojamiento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column turismo.alojamiento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column turismo.alojamiento.codigo is 'Código';
comment on column turismo.alojamiento.nombre is 'Nombre';
comment on column turismo.alojamiento.capacidad_personas is 'Huéspedes máximos';
comment on column turismo.alojamiento.zona_id is 'Ubicación';
comment on column turismo.alojamiento.tarifa_noche is 'Tarifa base por noche';
comment on column turismo.alojamiento.activo is 'Disponible';
comment on column turismo.alojamiento.creado_en is 'Fecha y hora de creación del registro';
comment on column turismo.alojamiento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table turismo.plan_turistico is 'Experiencia ofrecida (pasadía, recorrido del cacao, ordeño, taller).';
comment on column turismo.plan_turistico.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column turismo.plan_turistico.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column turismo.plan_turistico.codigo is 'Código';
comment on column turismo.plan_turistico.nombre is 'Nombre';
comment on column turismo.plan_turistico.descripcion is 'Qué incluye';
comment on column turismo.plan_turistico.duracion_horas is 'Duración';
comment on column turismo.plan_turistico.cupo_maximo is 'Personas por grupo';
comment on column turismo.plan_turistico.precio_persona is 'Precio por persona';
comment on column turismo.plan_turistico.creado_en is 'Fecha y hora de creación del registro';
comment on column turismo.plan_turistico.actualizado_en is 'Fecha y hora de la última modificación';
comment on table turismo.reserva is 'Reserva de alojamiento o plan.';
comment on column turismo.reserva.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column turismo.reserva.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column turismo.reserva.codigo is 'Código';
comment on column turismo.reserva.cliente_id is 'Cliente';
comment on column turismo.reserva.alojamiento_id is 'Alojamiento';
comment on column turismo.reserva.plan_turistico_id is 'Plan';
comment on column turismo.reserva.fecha_inicio is 'Llegada';
comment on column turismo.reserva.fecha_fin is 'Salida';
comment on column turismo.reserva.personas is 'Número de personas';
comment on column turismo.reserva.estado is 'Situación (valores: solicitada, confirmada, pagada, cumplida, cancelada)';
comment on column turismo.reserva.total is 'Valor';
comment on column turismo.reserva.valor_deposito is 'Anticipo pagado para confirmar';
comment on column turismo.reserva.checkin_en is 'Llegada real';
comment on column turismo.reserva.checkout_en is 'Salida real';
comment on column turismo.reserva.pedido_id is 'Pedido de cobro asociado';
comment on column turismo.reserva.creado_en is 'Fecha y hora de creación del registro';
comment on column turismo.reserva.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.dispositivo is 'Equipo físico de la red local de la finca (ESP32, PLC, estación meteorológica) o la pasarela que la coordina. Los nodos hablan con la pasarela por MQTT local; la pasarela sincroniza con la nube cuando hay internet.';
comment on column iot.dispositivo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.dispositivo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.dispositivo.codigo is 'Código';
comment on column iot.dispositivo.tipo is 'Tipo; la pasarela es el cerebro local que ejecuta las reglas, graba los clips y guarda datos sin internet (valores: esp32, plc, estacion_clima, pasarela, registrador_temperatura, camara, camara_termica, lector_acceso, central_alarma, otro)';
comment on column iot.dispositivo.pasarela_id is 'Pasarela a la que reporta este nodo (vacío si es la pasarela)';
comment on column iot.dispositivo.zona_id is 'Ubicación';
comment on column iot.dispositivo.topico_mqtt is 'Tópico base en el broker local, ej. guayacan/riego/v03';
comment on column iot.dispositivo.direccion_red_local is 'IP fija en la red local de la finca';
comment on column iot.dispositivo.version_firmware is 'Versión del programa instalado';
comment on column iot.dispositivo.ultima_conexion is 'Último latido recibido';
comment on column iot.dispositivo.ultima_sincronizacion_nube is 'Solo pasarela: última vez que subió datos a la nube';
comment on column iot.dispositivo.activo is 'En uso';
comment on column iot.dispositivo.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.dispositivo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.sensor is 'Sensor de un dispositivo (humedad de suelo, nivel de tanque, caudal, temperatura, movimiento, puerta, humo, gas).';
comment on column iot.sensor.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.sensor.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.sensor.dispositivo_id is 'Dispositivo';
comment on column iot.sensor.codigo is 'Código';
comment on column iot.sensor.magnitud is 'Qué mide o detecta (valores: humedad_suelo, nivel_tanque, caudal, temperatura, humedad_aire, lluvia, oxigeno_agua, ph, movimiento, puerta, rotura_vidrio, humo, gas, amoniaco, presencia_termica)';
comment on column iot.sensor.unidad is 'Unidad, ej. %, cm, L/min';
comment on column iot.sensor.valor_minimo_alerta is 'Alerta por debajo';
comment on column iot.sensor.valor_maximo_alerta is 'Alerta por encima';
comment on column iot.sensor.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.sensor.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.actuador is 'Elemento que el sistema puede accionar (electroválvula, bomba, relé, sirena, reflector, cerradura, cortina, extractor).';
comment on column iot.actuador.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.actuador.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.actuador.dispositivo_id is 'Dispositivo';
comment on column iot.actuador.codigo is 'Código';
comment on column iot.actuador.tipo is 'Tipo (valores: electrovalvula, bomba, rele, motor, sirena, reflector, cerradura, cortina, extractor)';
comment on column iot.actuador.zona_seguridad_id is 'Zona de seguridad que protege (sirenas, cerraduras, reflectores)';
comment on column iot.actuador.modo_falla is 'Qué hace si se va la energía: una cerradura en un paso de personas debe abrir sin energía (valores: cierra_sin_energia, abre_sin_energia, mantiene)';
comment on column iot.actuador.estado_actual is 'Último estado reportado (valores: abierto, cerrado, encendido, apagado, desconocido)';
comment on column iot.actuador.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.actuador.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.lectura is 'Medición de un sensor, particionada por mes (o hipertabla si se usa TimescaleDB); sin columnas de auditoría por volumen. La pasarela guarda las lecturas mientras no hay internet y las sube después.';
comment on column iot.lectura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.lectura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.lectura.sensor_id is 'Sensor';
comment on column iot.lectura.medido_en is 'Momento de la medición (reloj de la pasarela)';
comment on column iot.lectura.recibido_en is 'Momento en que llegó a la nube; la diferencia muestra el tiempo sin conexión';
comment on column iot.lectura.valor is 'Valor medido';
comment on table iot.regla_automatizacion is 'Regla determinista que acciona un actuador (ej. abrir V-03 si humedad < 30 % y tanque > 40 %). Se ejecuta en la pasarela local, así funciona sin internet. La IA puede sugerir reglas pero no activarlas.';
comment on column iot.regla_automatizacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.regla_automatizacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.regla_automatizacion.nombre is 'Nombre';
comment on column iot.regla_automatizacion.condicion is 'Condición sobre sensores, horario y clima';
comment on column iot.regla_automatizacion.actuador_id is 'Actuador';
comment on column iot.regla_automatizacion.accion is 'Acción (valores: abrir, cerrar, encender, apagar)';
comment on column iot.regla_automatizacion.duracion_max_min is 'Tiempo máximo de seguridad; el nodo ESP32 también lo aplica por su cuenta';
comment on column iot.regla_automatizacion.ejecuta_en is 'Dónde corre la regla; la nube solo para reglas no críticas (valores: pasarela_local, nodo, nube)';
comment on column iot.regla_automatizacion.version is 'Versión; sube con cada cambio';
comment on column iot.regla_automatizacion.desplegada_version is 'Versión que confirmó tener la pasarela; distinta de version = cambio pendiente de bajar';
comment on column iot.regla_automatizacion.activa is 'Las reglas nacen inactivas hasta que un humano las activa';
comment on column iot.regla_automatizacion.aprobado_por is 'Quién la activó';
comment on column iot.regla_automatizacion.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.regla_automatizacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.comando_actuador is 'Orden manual o automática a un actuador (abrir o cerrar una válvula), con su resultado. Funciona desde la red local aunque no haya internet.';
comment on column iot.comando_actuador.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.comando_actuador.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.comando_actuador.actuador_id is 'Actuador';
comment on column iot.comando_actuador.accion is 'Acción (valores: abrir, cerrar, encender, apagar)';
comment on column iot.comando_actuador.origen is 'De dónde salió la orden (valores: app_nube, app_red_local, regla, boton_fisico)';
comment on column iot.comando_actuador.regla_id is 'Regla que la emitió, si aplica';
comment on column iot.comando_actuador.solicitado_por is 'Persona que la pidió, si aplica';
comment on column iot.comando_actuador.duracion_max_min is 'Tiempo máximo antes de cerrar solo';
comment on column iot.comando_actuador.estado is 'Resultado (valores: pendiente, enviado, ejecutado, fallido, expirado)';
comment on column iot.comando_actuador.expira_en is 'Si no se ejecuta antes, se descarta (evita que una orden vieja se ejecute al volver la conexión)';
comment on column iot.comando_actuador.ejecutado_en is 'Confirmación del nodo';
comment on column iot.comando_actuador.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column iot.comando_actuador.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column iot.comando_actuador.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column iot.comando_actuador.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.comando_actuador.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.dispositivo_captura is 'Equipo con el que se capturan datos: celulares con la app, lectores de código de barras, básculas e impresoras de etiquetas.';
comment on column nucleo.dispositivo_captura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.dispositivo_captura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.dispositivo_captura.codigo is 'Código, ej. CEL-SAMID, BAS-01, LEC-01';
comment on column nucleo.dispositivo_captura.tipo is 'Tipo de equipo (valores: celular, tableta, lector_codigo, bascula, impresora_etiquetas)';
comment on column nucleo.dispositivo_captura.conexion is 'Cómo se conecta: teclado_hid = el lector escribe como un teclado; red_local = a través de la pasarela de la finca (valores: camara, teclado_hid, bluetooth_ble, bluetooth_serial, usb, red_local)';
comment on column nucleo.dispositivo_captura.marca_modelo is 'Marca y modelo';
comment on column nucleo.dispositivo_captura.numero_serie is 'Serie del fabricante';
comment on column nucleo.dispositivo_captura.capacidad_max_kg is 'Báscula: peso máximo';
comment on column nucleo.dispositivo_captura.division_g is 'Báscula: resolución en gramos';
comment on column nucleo.dispositivo_captura.uso_comercial is 'Báscula usada para vender por peso: sujeta a verificación metrológica de la SIC';
comment on column nucleo.dispositivo_captura.ultima_verificacion is 'Fecha de la última verificación o calibración';
comment on column nucleo.dispositivo_captura.proxima_verificacion is 'Fecha en que vence la verificación';
comment on column nucleo.dispositivo_captura.certificado_url is 'Certificado de verificación o calibración';
comment on column nucleo.dispositivo_captura.usuario_asignado_id is 'Persona a cargo (celulares)';
comment on column nucleo.dispositivo_captura.activo is 'En uso';
comment on column nucleo.dispositivo_captura.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.dispositivo_captura.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.sincronizacion is 'Cada sincronización de la app sin conexión: cuántos registros subió, cuántos se rechazaron y por qué.';
comment on column nucleo.sincronizacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.sincronizacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.sincronizacion.dispositivo_captura_id is 'Celular o tableta que sincroniza';
comment on column nucleo.sincronizacion.usuario_id is 'Usuario que tenía la sesión';
comment on column nucleo.sincronizacion.version_app is 'Versión de la app';
comment on column nucleo.sincronizacion.iniciada_en is 'Inicio';
comment on column nucleo.sincronizacion.terminada_en is 'Fin';
comment on column nucleo.sincronizacion.registros_recibidos is 'Registros que llegaron';
comment on column nucleo.sincronizacion.registros_duplicados is 'Ya existían (mismo id_cliente); se ignoran sin error';
comment on column nucleo.sincronizacion.registros_rechazados is 'No pasaron una regla (ej. dos personas registraron la postura del mismo lote y día)';
comment on column nucleo.sincronizacion.detalle_rechazos is 'Qué se rechazó y por qué, para resolverlo en la app';
comment on column nucleo.sincronizacion.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.sincronizacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.etiqueta is 'Código de barras o QR impreso para un lote. Interno (Code 128 o QR) o GS1-128 si la finca obtiene códigos GS1.';
comment on column inventario.etiqueta.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.etiqueta.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.etiqueta.lote_inventario_id is 'Lote identificado';
comment on column inventario.etiqueta.codigo is 'Texto que contiene el código, ej. GY-HUE-20261025-GAL01 o (01)…(10)…(17)…';
comment on column inventario.etiqueta.simbologia is 'Tipo de código impreso (valores: code128, qr, gs1_128, gs1_datamatrix, ean13)';
comment on column inventario.etiqueta.impresora_id is 'Impresora usada';
comment on column inventario.etiqueta.impresa_en is 'Cuándo se imprimió';
comment on column inventario.etiqueta.anulada is 'Etiqueta dañada o reemplazada; si se escanea, se rechaza';
comment on column inventario.etiqueta.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.etiqueta.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.lectura_codigo is 'Cada escaneo de un código: qué se leyó, con qué equipo, para qué y qué resultado tuvo.';
comment on column inventario.lectura_codigo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.lectura_codigo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.lectura_codigo.codigo_leido is 'Texto leído';
comment on column inventario.lectura_codigo.simbologia is 'Tipo detectado';
comment on column inventario.lectura_codigo.etiqueta_id is 'Etiqueta encontrada, si existe';
comment on column inventario.lectura_codigo.accion is 'Para qué se escaneó (valores: consulta, entrada, salida, conteo, traslado, despacho)';
comment on column inventario.lectura_codigo.resultado is 'Resultado de la validación (valores: ok, desconocido, anulado, vencido, duplicado, rechazado)';
comment on column inventario.lectura_codigo.usuario_id is 'Quién escaneó';
comment on column inventario.lectura_codigo.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column inventario.lectura_codigo.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column inventario.lectura_codigo.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column inventario.lectura_codigo.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.lectura_codigo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.pesaje is 'Lectura de una báscula digital, automática o digitada, con tara y estabilidad.';
comment on column inventario.pesaje.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.pesaje.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.pesaje.peso_bruto_kg is 'Peso total en la báscula';
comment on column inventario.pesaje.tara_kg is 'Peso del recipiente (canastilla, bulto, nevera)';
comment on column inventario.pesaje.peso_neto_kg is 'Bruto menos tara';
comment on column inventario.pesaje.estable is 'La báscula indicó lectura estable; si es falso, no se acepta para vender';
comment on column inventario.pesaje.origen is 'Leído del equipo o escrito a mano (el digitado queda marcado en informes) (valores: bascula_automatica, digitado)';
comment on column inventario.pesaje.referencia_tabla is 'Para qué se pesó, ej. cosecha, registro_pesaje, pedido_detalle';
comment on column inventario.pesaje.referencia_id is 'Id del registro relacionado';
comment on column inventario.pesaje.usuario_id is 'Quién pesó';
comment on column inventario.pesaje.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column inventario.pesaje.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column inventario.pesaje.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column inventario.pesaje.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.pesaje.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.conteo_fisico is 'Inventario físico de una bodega: se escanea lo que hay y se compara con el sistema.';
comment on column inventario.conteo_fisico.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.conteo_fisico.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.conteo_fisico.bodega_id is 'Bodega contada';
comment on column inventario.conteo_fisico.fecha is 'Día del conteo';
comment on column inventario.conteo_fisico.estado is 'Ajustado = las diferencias ya generaron movimientos de ajuste (valores: en_curso, cerrado, ajustado)';
comment on column inventario.conteo_fisico.responsable_id is 'Responsable';
comment on column inventario.conteo_fisico.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.conteo_fisico.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.conteo_detalle is 'Resultado del conteo por lote.';
comment on column inventario.conteo_detalle.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.conteo_detalle.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.conteo_detalle.conteo_fisico_id is 'Conteo';
comment on column inventario.conteo_detalle.lote_inventario_id is 'Lote contado';
comment on column inventario.conteo_detalle.cantidad_sistema is 'Lo que decía el sistema al contar';
comment on column inventario.conteo_detalle.cantidad_contada is 'Lo encontrado';
comment on column inventario.conteo_detalle.movimiento_ajuste_id is 'Ajuste generado por la diferencia';
comment on column inventario.conteo_detalle.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column inventario.conteo_detalle.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column inventario.conteo_detalle.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column inventario.conteo_detalle.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.conteo_detalle.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.reserva_lote is 'Qué lotes se reservaron para cada línea de pedido, escogidos en orden FEFO; una línea puede tomar de varios lotes.';
comment on column comercial.reserva_lote.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.reserva_lote.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.reserva_lote.pedido_detalle_id is 'Línea del pedido';
comment on column comercial.reserva_lote.lote_inventario_id is 'Lote reservado';
comment on column comercial.reserva_lote.cantidad is 'Cantidad tomada de ese lote';
comment on column comercial.reserva_lote.estado is 'Situación (valores: reservada, despachada, liberada)';
comment on column comercial.reserva_lote.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.reserva_lote.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.periodo_contable is 'Mes contable; un comprobante solo se contabiliza o anula si su mes está abierto.';
comment on column finanzas.periodo_contable.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.periodo_contable.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.periodo_contable.anio is 'Año';
comment on column finanzas.periodo_contable.mes is 'Mes (1 a 12)';
comment on column finanzas.periodo_contable.estado is 'Estado (valores: abierto, cerrado)';
comment on column finanzas.periodo_contable.cerrado_por is 'Quién lo cerró';
comment on column finanzas.periodo_contable.cerrado_en is 'Cuándo';
comment on column finanzas.periodo_contable.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.periodo_contable.actualizado_en is 'Fecha y hora de la última modificación';
comment on table redes.politica_canal is 'Reglas de cada canal según su proveedor (Meta, TikTok): ventana para responder, quién inicia, límites y cobro. Se actualiza cuando cambian las políticas.';
comment on column redes.politica_canal.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column redes.politica_canal.plataforma is 'Código del canal: whatsapp, instagram, messenger, tiktok, web_chat, facebook_pagina';
comment on column redes.politica_canal.ventana_horas is 'Horas para responder después del último mensaje del cliente; vacío = sin límite (web propia)';
comment on column redes.politica_canal.ventana_agente_humano_horas is 'Horas extra solo para respuestas de una persona (etiqueta de agente humano de Meta)';
comment on column redes.politica_canal.ventana_anuncio_horas is 'Ventana ampliada si el cliente llegó por un anuncio que abre chat';
comment on column redes.politica_canal.max_mensajes_por_ventana is 'Tope de mensajes de la empresa por ventana (TikTok: 10)';
comment on column redes.politica_canal.empresa_puede_iniciar is 'Si la empresa puede escribir primero (WhatsApp solo con plantilla aprobada)';
comment on column redes.politica_canal.requiere_plantilla_fuera_ventana is 'Fuera de la ventana solo se envían plantillas aprobadas';
comment on column redes.politica_canal.cobra_por_mensaje is 'El proveedor cobra por mensaje enviado';
comment on column redes.politica_canal.mensajes_servicio_gratis_mes is 'Mensajes de servicio sin costo al mes (WhatsApp: 1.000 por número)';
comment on column redes.politica_canal.solo_bot_del_negocio is 'El bot debe limitarse a temas de la finca; no puede ser un asistente general';
comment on column redes.politica_canal.disponible is 'Si el canal está disponible para cuentas registradas en Colombia';
comment on column redes.politica_canal.fuente_url is 'Documento donde se verificó la regla';
comment on column redes.politica_canal.verificado_en is 'Cuándo se verificó';
comment on column redes.politica_canal.creado_en is 'Fecha y hora de creación del registro';
comment on column redes.politica_canal.actualizado_en is 'Fecha y hora de la última modificación';
comment on table redes.plantilla_mensaje is 'Plantilla aprobada por Meta para escribir fuera de la ventana de 24 horas de WhatsApp (confirmaciones, recordatorios, promociones).';
comment on column redes.plantilla_mensaje.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column redes.plantilla_mensaje.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column redes.plantilla_mensaje.cuenta_red_id is 'Cuenta de WhatsApp';
comment on column redes.plantilla_mensaje.nombre is 'Nombre técnico, ej. pedido_confirmado';
comment on column redes.plantilla_mensaje.categoria is 'Categoría de Meta; define el precio y si exige consentimiento de publicidad (valores: marketing, utility, authentication)';
comment on column redes.plantilla_mensaje.idioma is 'Idioma';
comment on column redes.plantilla_mensaje.cuerpo is 'Texto con variables {{1}}, {{2}}';
comment on column redes.plantilla_mensaje.variables is 'Qué dato va en cada variable';
comment on column redes.plantilla_mensaje.estado_meta is 'Estado de revisión en Meta (valores: borrador, enviada, aprobada, rechazada, pausada)';
comment on column redes.plantilla_mensaje.id_externo is 'Id en Meta';
comment on column redes.plantilla_mensaje.finalidad_requerida is 'Consentimiento que debe tener el cliente para recibirla (valores: atencion_pedidos, publicidad)';
comment on column redes.plantilla_mensaje.creado_en is 'Fecha y hora de creación del registro';
comment on column redes.plantilla_mensaje.actualizado_en is 'Fecha y hora de la última modificación';
comment on table redes.mensaje_saliente is 'Registro de control de cada mensaje que la finca envía por un canal: si estaba dentro de la ventana, qué plantilla usó, qué consentimiento lo permitió y cuánto costó.';
comment on column redes.mensaje_saliente.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column redes.mensaje_saliente.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column redes.mensaje_saliente.cuenta_red_id is 'Canal';
comment on column redes.mensaje_saliente.tercero_id is 'Destinatario, si está identificado';
comment on column redes.mensaje_saliente.conversacion_ref is 'Conversación en MongoDB';
comment on column redes.mensaje_saliente.tipo is 'Servicio = respuesta normal dentro de la ventana (valores: servicio, plantilla, respuesta_privada_comentario)';
comment on column redes.mensaje_saliente.plantilla_id is 'Plantilla usada';
comment on column redes.mensaje_saliente.autor is 'Quién lo generó (valores: agente, humano, sistema)';
comment on column redes.mensaje_saliente.dentro_ventana is 'Si se envió dentro de la ventana del canal';
comment on column redes.mensaje_saliente.consentimiento_id is 'Consentimiento que lo autoriza (obligatorio para publicidad)';
comment on column redes.mensaje_saliente.costo_estimado_usd is 'Costo según la tarifa del canal';
comment on column redes.mensaje_saliente.estado_entrega is 'Resultado; bloqueado_por_regla = el sistema lo detuvo (fuera de ventana, sin consentimiento) (valores: enviado, entregado, leido, fallido, bloqueado_por_regla)';
comment on column redes.mensaje_saliente.enviado_en is 'Momento';
comment on column redes.mensaje_saliente.creado_en is 'Fecha y hora de creación del registro';
comment on column redes.mensaje_saliente.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.regla_conversacion is 'Guardia del orquestador: temas permitidos, temas que se rechazan con cortesía y casos que pasan a una persona.';
comment on column ia.regla_conversacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.regla_conversacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.regla_conversacion.tipo is 'Clase de regla (valores: tema_permitido, tema_fuera_de_alcance, escalar_a_humano, dato_prohibido)';
comment on column ia.regla_conversacion.descripcion is 'Qué cubre, en lenguaje claro';
comment on column ia.regla_conversacion.ejemplos is 'Frases de ejemplo para el clasificador';
comment on column ia.regla_conversacion.respuesta_plantilla is 'Texto de respuesta (ej. cortesía al rechazar un tema ajeno a la finca)';
comment on column ia.regla_conversacion.prioridad_escalamiento is 'Si escala, con qué prioridad (valores: alta, media, baja)';
comment on column ia.regla_conversacion.activa is 'En uso';
comment on column ia.regla_conversacion.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.regla_conversacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.escalamiento is 'Conversación pasada a una persona: motivo, quién la atiende y hasta cuándo se puede responder según la ventana del canal.';
comment on column ia.escalamiento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.escalamiento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.escalamiento.conversacion_ref is 'Conversación en MongoDB';
comment on column ia.escalamiento.canal is 'Canal (whatsapp, instagram, ...)';
comment on column ia.escalamiento.motivo is 'Por qué escaló (valores: solicitud_cliente, queja, fuera_de_alcance, sin_respuesta_conocimiento, pedido_grande, pago, error_agente)';
comment on column ia.escalamiento.prioridad is 'Prioridad (valores: alta, media, baja)';
comment on column ia.escalamiento.asignado_a is 'Persona que atiende';
comment on column ia.escalamiento.estado is 'Situación; vencido = se cerró la ventana sin respuesta (valores: pendiente, en_atencion, resuelto, vencido)';
comment on column ia.escalamiento.responder_antes_de is 'Límite según la ventana del canal (incluye la extensión de agente humano cuando aplica)';
comment on column ia.escalamiento.atendido_en is 'Primera respuesta de la persona';
comment on column ia.escalamiento.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.escalamiento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.funcionalidad is 'Interruptor de funciones por finca (feature flag): lo que aún no tiene equipo o decisión queda construido y apagado, y se enciende sin desplegar otra versión.';
comment on column nucleo.funcionalidad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.funcionalidad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.funcionalidad.codigo is 'Código, ej. venta_credito, permuta, camara_termica, reconocimiento_facial';
comment on column nucleo.funcionalidad.descripcion is 'Qué habilita';
comment on column nucleo.funcionalidad.fase is 'Fase del plan en que se prevé';
comment on column nucleo.funcionalidad.requiere_equipo is 'Equipo que hay que comprar antes de activarla, si aplica';
comment on column nucleo.funcionalidad.activa is 'Encendida en esta finca';
comment on column nucleo.funcionalidad.activada_por is 'Quién la encendió';
comment on column nucleo.funcionalidad.activada_en is 'Cuándo';
comment on column nucleo.funcionalidad.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.funcionalidad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.nota_voz is 'Nota de voz grabada en campo sin conexión; se transcribe al sincronizar y el operario confirma lo interpretado antes de crear el registro.';
comment on column nucleo.nota_voz.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.nota_voz.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.nota_voz.usuario_id is 'Quién grabó';
comment on column nucleo.nota_voz.audio_url is 'Audio en el almacén de archivos';
comment on column nucleo.nota_voz.duracion_seg is 'Duración en segundos';
comment on column nucleo.nota_voz.transcripcion is 'Texto obtenido por el servicio de voz a texto';
comment on column nucleo.nota_voz.proveedor_voz_texto is 'Servicio usado (intercambiable)';
comment on column nucleo.nota_voz.interpretacion is 'Registro propuesto, ej. {"tabla":"registro_postura","lote":"AV-2026-01","huevos":87}';
comment on column nucleo.nota_voz.estado is 'Solo una nota confirmada por la persona crea el registro (valores: pendiente, interpretada, confirmada, descartada)';
comment on column nucleo.nota_voz.registro_tabla is 'Tabla del registro creado';
comment on column nucleo.nota_voz.registro_id is 'Id del registro creado';
comment on column nucleo.nota_voz.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column nucleo.nota_voz.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column nucleo.nota_voz.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column nucleo.nota_voz.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.nota_voz.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.categoria_huevo is 'Categorías comerciales del huevo por rango de peso, con la norma de la que salen (verificar NTC 1240 vigente).';
comment on column produccion.categoria_huevo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.categoria_huevo.codigo is 'Código, ej. jumbo, aaa, aa, a, b, c';
comment on column produccion.categoria_huevo.peso_min_g is 'Peso mínimo en gramos (incluido)';
comment on column produccion.categoria_huevo.peso_max_g is 'Peso máximo en gramos (excluido); vacío = sin tope';
comment on column produccion.categoria_huevo.norma is 'Norma o fuente de los rangos';
comment on column produccion.categoria_huevo.vigente_desde is 'Desde cuándo aplica';
comment on column produccion.categoria_huevo.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.categoria_huevo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.clasificacion_postura is 'Huevos de un registro de postura por categoría; el método dice si se clasificó con báscula, a mano o con visión artificial.';
comment on column produccion.clasificacion_postura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.clasificacion_postura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.clasificacion_postura.registro_postura_id is 'Registro de postura';
comment on column produccion.clasificacion_postura.categoria_huevo_id is 'Categoría';
comment on column produccion.clasificacion_postura.cantidad is 'Huevos de esa categoría';
comment on column produccion.clasificacion_postura.metodo is 'Cómo se clasificó (vision = piloto de fase 4) (valores: peso_bascula, manual, vision)';
comment on column produccion.clasificacion_postura.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.clasificacion_postura.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.clasificacion_postura.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.clasificacion_postura.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.clasificacion_postura.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.registro_bioseguridad is 'Registros de bioseguridad e inocuidad que pide el ICA: limpieza, desinfección, plagas, visitas, cambio de cama y agua.';
comment on column produccion.registro_bioseguridad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.registro_bioseguridad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.registro_bioseguridad.zona_id is 'Galpón, bodega o zona';
comment on column produccion.registro_bioseguridad.fecha is 'Día';
comment on column produccion.registro_bioseguridad.tipo is 'Tipo de registro (valores: limpieza, desinfeccion, control_plagas, visita, cambio_cama, calidad_agua, vacio_sanitario)';
comment on column produccion.registro_bioseguridad.producto_id is 'Desinfectante o insumo usado';
comment on column produccion.registro_bioseguridad.responsable is 'Quién lo hizo o quién visitó';
comment on column produccion.registro_bioseguridad.observaciones is 'Notas';
comment on column produccion.registro_bioseguridad.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.registro_bioseguridad.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.registro_bioseguridad.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.registro_bioseguridad.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.registro_bioseguridad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table produccion.produccion_abono is 'Humus y compost producidos por el lombricultivo o la compostera; al entrar a bodega crean un lote vendible.';
comment on column produccion.produccion_abono.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column produccion.produccion_abono.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column produccion.produccion_abono.origen is 'De dónde sale (valores: lombricultivo, compostera, biodigestor)';
comment on column produccion.produccion_abono.zona_id is 'Zona';
comment on column produccion.produccion_abono.fecha is 'Día de cosecha del abono';
comment on column produccion.produccion_abono.kg is 'Kilogramos';
comment on column produccion.produccion_abono.lote_inventario_id is 'Lote creado en inventario';
comment on column produccion.produccion_abono.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column produccion.produccion_abono.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column produccion.produccion_abono.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column produccion.produccion_abono.creado_en is 'Fecha y hora de creación del registro';
comment on column produccion.produccion_abono.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.vehiculo is 'Vehículo de entregas (camioneta, motocarro) y su registrador de temperatura.';
comment on column inventario.vehiculo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.vehiculo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.vehiculo.codigo is 'Código, ej. CAM-01';
comment on column inventario.vehiculo.tipo is 'Tipo (valores: camioneta, motocarro, moto, otro)';
comment on column inventario.vehiculo.placa is 'Placa';
comment on column inventario.vehiculo.capacidad_kg is 'Carga máxima';
comment on column inventario.vehiculo.refrigerado is 'Tiene nevera o caja térmica';
comment on column inventario.vehiculo.sensor_temperatura_id is 'Registrador de temperatura (guarda sin señal)';
comment on column inventario.vehiculo.temperatura_max_c is 'Temperatura máxima aceptada';
comment on column inventario.vehiculo.minutos_tolerancia is 'Minutos fuera de rango antes de bloquear lo que transporta';
comment on column inventario.vehiculo.activo is 'En uso';
comment on column inventario.vehiculo.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.vehiculo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.excursion_temperatura is 'Periodo en que una nevera o un vehículo estuvo fuera de su rango de temperatura; si supera la tolerancia, bloquea los lotes perecederos.';
comment on column inventario.excursion_temperatura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.excursion_temperatura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.excursion_temperatura.sensor_id is 'Sensor que la detectó';
comment on column inventario.excursion_temperatura.bodega_id is 'Bodega afectada';
comment on column inventario.excursion_temperatura.vehiculo_id is 'Vehículo afectado';
comment on column inventario.excursion_temperatura.inicio is 'Inicio';
comment on column inventario.excursion_temperatura.fin is 'Fin; vacío = sigue fuera de rango';
comment on column inventario.excursion_temperatura.temperatura_extrema_c is 'Peor temperatura registrada';
comment on column inventario.excursion_temperatura.minutos_fuera is 'Minutos fuera de rango';
comment on column inventario.excursion_temperatura.lotes_bloqueados is 'Lotes que bloqueó (lo calcula la regla)';
comment on column inventario.excursion_temperatura.estado is 'Situación (valores: abierta, cerrada)';
comment on column inventario.excursion_temperatura.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.excursion_temperatura.actualizado_en is 'Fecha y hora de la última modificación';
comment on table inventario.bloqueo_lote is 'Bloqueo de un lote y su decisión: lo pone una regla o una persona; liberarlo o descartarlo siempre lo decide una persona.';
comment on column inventario.bloqueo_lote.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column inventario.bloqueo_lote.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column inventario.bloqueo_lote.lote_inventario_id is 'Lote bloqueado';
comment on column inventario.bloqueo_lote.motivo is 'Por qué (valores: cadena_frio, sanitario, calidad, retiro)';
comment on column inventario.bloqueo_lote.origen_tabla is 'Qué lo causó, ej. excursion_temperatura, retiro_lote';
comment on column inventario.bloqueo_lote.origen_id is 'Id del origen';
comment on column inventario.bloqueo_lote.decision is 'Liberado vuelve a disponible; descartado registra la merma (valores: pendiente, liberado, descartado)';
comment on column inventario.bloqueo_lote.decidido_por is 'Persona que decidió';
comment on column inventario.bloqueo_lote.decidido_en is 'Cuándo';
comment on column inventario.bloqueo_lote.observacion is 'Motivo de la decisión';
comment on column inventario.bloqueo_lote.creado_en is 'Fecha y hora de creación del registro';
comment on column inventario.bloqueo_lote.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.retiro_lote is 'Retiro de un lote del mercado (recall): se bloquea el lote y se avisa a cada cliente que lo recibió.';
comment on column comercial.retiro_lote.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.retiro_lote.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.retiro_lote.lote_inventario_id is 'Lote retirado';
comment on column comercial.retiro_lote.motivo is 'Problema sanitario o de calidad';
comment on column comercial.retiro_lote.estado is 'Situación (valores: abierto, clientes_avisados, cerrado)';
comment on column comercial.retiro_lote.abierto_por is 'Quién lo abrió';
comment on column comercial.retiro_lote.cerrado_en is 'Cuándo se cerró';
comment on column comercial.retiro_lote.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.retiro_lote.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.retiro_aviso is 'Cliente que recibió un lote retirado: cuánto recibió, cuándo se le avisó y cuánto devolvió.';
comment on column comercial.retiro_aviso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.retiro_aviso.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.retiro_aviso.retiro_lote_id is 'Retiro';
comment on column comercial.retiro_aviso.cliente_id is 'Cliente';
comment on column comercial.retiro_aviso.pedido_id is 'Pedido en que lo recibió';
comment on column comercial.retiro_aviso.cantidad is 'Cantidad recibida de ese lote';
comment on column comercial.retiro_aviso.avisado_en is 'Cuándo se le avisó';
comment on column comercial.retiro_aviso.medio_aviso is 'Cómo (valores: whatsapp, llamada, visita, correo)';
comment on column comercial.retiro_aviso.cantidad_devuelta is 'Lo que devolvió';
comment on column comercial.retiro_aviso.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.retiro_aviso.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.pedido_recurrente is 'Pedido que se repite (tienda, restaurante, hotel); cada día la tarea crea en borrador los que tocan para que un vendedor los confirme.';
comment on column comercial.pedido_recurrente.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.pedido_recurrente.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.pedido_recurrente.cliente_id is 'Cliente';
comment on column comercial.pedido_recurrente.frecuencia is 'Cada cuánto (valores: semanal, quincenal, mensual)';
comment on column comercial.pedido_recurrente.proxima_fecha is 'Próxima entrega';
comment on column comercial.pedido_recurrente.canal is 'Canal con que se registra el pedido (valores: whatsapp, web, redes, telefono, finca, mercado_campesino)';
comment on column comercial.pedido_recurrente.forma_pago is 'Forma de pago de los pedidos generados (valores: contado, credito)';
comment on column comercial.pedido_recurrente.activo is 'En uso';
comment on column comercial.pedido_recurrente.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.pedido_recurrente.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.pedido_recurrente_detalle is 'Productos y cantidades del pedido recurrente.';
comment on column comercial.pedido_recurrente_detalle.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.pedido_recurrente_detalle.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.pedido_recurrente_detalle.pedido_recurrente_id is 'Pedido recurrente';
comment on column comercial.pedido_recurrente_detalle.producto_id is 'Producto';
comment on column comercial.pedido_recurrente_detalle.cantidad is 'Cantidad';
comment on column comercial.pedido_recurrente_detalle.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.pedido_recurrente_detalle.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.permuta is 'Trueque formal: una venta (factura) y una compra (documento soporte) que se compensan; requiere la función permuta activa. El pago con mano de obra no se admite.';
comment on column comercial.permuta.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.permuta.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.permuta.factura_id is 'Venta';
comment on column comercial.permuta.documento_soporte_id is 'Compra';
comment on column comercial.permuta.valor_compensado is 'Valor que se cruza';
comment on column comercial.permuta.acuerdo is 'Qué se intercambió y cómo se valoró';
comment on column comercial.permuta.registrado_por is 'Quién la registró';
comment on column comercial.permuta.creado_en is 'Fecha y hora de creación del registro';
comment on column comercial.permuta.actualizado_en is 'Fecha y hora de la última modificación';
comment on table comercial.huella_trazabilidad is 'Cadena de huellas SHA-256 de los hechos de trazabilidad de los lotes: cada huella incluye la anterior, así cualquier alteración se detecta. Lista para anclarse en una red blockchain si un comprador lo exige.';
comment on column comercial.huella_trazabilidad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column comercial.huella_trazabilidad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column comercial.huella_trazabilidad.lote_inventario_id is 'Lote';
comment on column comercial.huella_trazabilidad.hecho is 'Hecho registrado (valores: lote_creado, despachado, bloqueado, liberado, descartado, retirado)';
comment on column comercial.huella_trazabilidad.contenido is 'Datos del hecho (lote, fechas, cliente, pedido)';
comment on column comercial.huella_trazabilidad.hash_anterior is 'Huella anterior de la cadena de la finca';
comment on column comercial.huella_trazabilidad.hash is 'SHA-256 de la huella anterior más el contenido';
comment on column comercial.huella_trazabilidad.anclaje_red is 'Red externa donde se ancló (vacío = no anclada)';
comment on column comercial.huella_trazabilidad.anclaje_transaccion is 'Id de la transacción de anclaje';
comment on column comercial.huella_trazabilidad.anclado_en is 'Cuándo';
comment on table compras.documento_soporte is 'Documento soporte electrónico de la DIAN para compras a quien no factura (campesinos, permutas).';
comment on column compras.documento_soporte.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column compras.documento_soporte.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column compras.documento_soporte.proveedor_id is 'Vendedor';
comment on column compras.documento_soporte.orden_compra_id is 'Orden de compra, si existe';
comment on column compras.documento_soporte.prefijo is 'Prefijo autorizado';
comment on column compras.documento_soporte.numero is 'Número';
comment on column compras.documento_soporte.fecha is 'Fecha';
comment on column compras.documento_soporte.descripcion is 'Qué se compró';
comment on column compras.documento_soporte.total is 'Valor';
comment on column compras.documento_soporte.cuds is 'Código único del documento soporte';
comment on column compras.documento_soporte.estado_dian is 'Respuesta de la DIAN (valores: pendiente, aceptado, rechazado)';
comment on column compras.documento_soporte.creado_en is 'Fecha y hora de creación del registro';
comment on column compras.documento_soporte.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.modelo_pronostico is 'Modelo de pronóstico de demanda entrenado; gana el de menor error (necesita al menos 12 meses de ventas).';
comment on column ia.modelo_pronostico.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.modelo_pronostico.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.modelo_pronostico.producto_id is 'Producto';
comment on column ia.modelo_pronostico.algoritmo is 'Algoritmo (valores: base_estacional, promedio_movil, ets, prophet, otro)';
comment on column ia.modelo_pronostico.version is 'Versión';
comment on column ia.modelo_pronostico.entrenado_en is 'Cuándo se entrenó';
comment on column ia.modelo_pronostico.meses_historia is 'Meses de ventas usados';
comment on column ia.modelo_pronostico.error_mape is 'Error porcentual medio en la validación';
comment on column ia.modelo_pronostico.activo is 'Modelo en uso para ese producto';
comment on column ia.modelo_pronostico.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.modelo_pronostico.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.pronostico_demanda is 'Cantidad esperada de venta por producto y periodo, con su rango.';
comment on column ia.pronostico_demanda.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.pronostico_demanda.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.pronostico_demanda.modelo_pronostico_id is 'Modelo';
comment on column ia.pronostico_demanda.producto_id is 'Producto';
comment on column ia.pronostico_demanda.periodo_inicio is 'Inicio';
comment on column ia.pronostico_demanda.periodo_fin is 'Fin';
comment on column ia.pronostico_demanda.cantidad is 'Cantidad esperada';
comment on column ia.pronostico_demanda.limite_inferior is 'Rango bajo';
comment on column ia.pronostico_demanda.limite_superior is 'Rango alto';
comment on column ia.pronostico_demanda.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.pronostico_demanda.actualizado_en is 'Fecha y hora de la última modificación';
comment on table redes.pieza_audiovisual is 'Video, time-lapse o foto preparada para redes: la IA propone guion y texto, FFmpeg arma el archivo y una persona aprueba. Si aparecen personas, todas deben tener consentimiento de imagen.';
comment on column redes.pieza_audiovisual.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column redes.pieza_audiovisual.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column redes.pieza_audiovisual.tipo is 'Tipo (valores: video_promocional, timelapse, reel, foto)';
comment on column redes.pieza_audiovisual.clips is 'Clips de origen (ids de iot.clip_video o archivos subidos)';
comment on column redes.pieza_audiovisual.guion is 'Guion propuesto';
comment on column redes.pieza_audiovisual.texto_publicacion is 'Texto para la red';
comment on column redes.pieza_audiovisual.musica_ref is 'Pista con licencia de uso';
comment on column redes.pieza_audiovisual.archivo_url is 'MP4 o imagen final';
comment on column redes.pieza_audiovisual.personas_identificables is 'Si aparecen personas reconocibles';
comment on column redes.pieza_audiovisual.estado is 'Situación (valores: borrador, propuesta, aprobada, rechazada, publicada)';
comment on column redes.pieza_audiovisual.agente_id is 'Agente que la propuso';
comment on column redes.pieza_audiovisual.aprobado_por is 'Quién la aprobó';
comment on column redes.pieza_audiovisual.publicacion_id is 'Publicación en la que se usó';
comment on column redes.pieza_audiovisual.creado_en is 'Fecha y hora de creación del registro';
comment on column redes.pieza_audiovisual.actualizado_en is 'Fecha y hora de la última modificación';
comment on table redes.pieza_persona is 'Persona que aparece en una pieza audiovisual y su consentimiento de imagen.';
comment on column redes.pieza_persona.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column redes.pieza_persona.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column redes.pieza_persona.pieza_audiovisual_id is 'Pieza';
comment on column redes.pieza_persona.tercero_id is 'Persona';
comment on table turismo.bloqueo_calendario is 'Fechas en que un alojamiento o un plan no está disponible (mantenimiento, uso familiar).';
comment on column turismo.bloqueo_calendario.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column turismo.bloqueo_calendario.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column turismo.bloqueo_calendario.alojamiento_id is 'Alojamiento';
comment on column turismo.bloqueo_calendario.plan_turistico_id is 'Plan';
comment on column turismo.bloqueo_calendario.desde is 'Desde';
comment on column turismo.bloqueo_calendario.hasta is 'Hasta';
comment on column turismo.bloqueo_calendario.motivo is 'Motivo';
comment on column turismo.bloqueo_calendario.creado_en is 'Fecha y hora de creación del registro';
comment on column turismo.bloqueo_calendario.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.zona_seguridad is 'Área vigilada (perímetro, galpón, bodega, acceso) con su estado de alarma; las reglas corren en la pasarela local.';
comment on column iot.zona_seguridad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.zona_seguridad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.zona_seguridad.zona_id is 'Zona del predio';
comment on column iot.zona_seguridad.codigo is 'Código, ej. SEG-BOD-01';
comment on column iot.zona_seguridad.nombre is 'Nombre';
comment on column iot.zona_seguridad.tipo is 'Tipo (valores: perimetro, acceso, galpon, bodega, vivienda, otra)';
comment on column iot.zona_seguridad.paso_personas is 'Si por sus puertas salen personas: sus cerraduras deben abrir sin energía';
comment on column iot.zona_seguridad.bioseguridad is 'Exige registro de visita y desinfección para entrar (galpones)';
comment on column iot.zona_seguridad.estado_alarma is 'Estado actual; solo cambia con iot.cambiar_estado_alarma (valores: desarmado, armado, noche, mantenimiento)';
comment on column iot.zona_seguridad.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.zona_seguridad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.cambio_estado_alarma is 'Historial de cambios de estado de la alarma (solo inserción).';
comment on column iot.cambio_estado_alarma.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.cambio_estado_alarma.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.cambio_estado_alarma.zona_seguridad_id is 'Zona';
comment on column iot.cambio_estado_alarma.estado_anterior is 'Estado antes';
comment on column iot.cambio_estado_alarma.estado_nuevo is 'Estado después';
comment on column iot.cambio_estado_alarma.origen is 'De dónde salió el cambio (valores: app_nube, app_red_local, teclado, horario, regla)';
comment on column iot.cambio_estado_alarma.usuario_id is 'Persona, si aplica';
comment on column iot.cambio_estado_alarma.ocurrido_en is 'Momento';
comment on table iot.credencial_acceso is 'Credencial para abrir una puerta: PIN, tarjeta RFID o rostro. El rostro exige autorización expresa de biometría y su plantilla solo vive cifrada en la pasarela local, nunca en la nube.';
comment on column iot.credencial_acceso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.credencial_acceso.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.credencial_acceso.tercero_id is 'Persona autorizada';
comment on column iot.credencial_acceso.zona_seguridad_id is 'Zona a la que da acceso; vacío = todas';
comment on column iot.credencial_acceso.metodo is 'Método (valores: pin, rfid, facial)';
comment on column iot.credencial_acceso.referencia_hash is 'Hash del PIN o del número de tarjeta (nunca el valor en claro)';
comment on column iot.credencial_acceso.consentimiento_id is 'Autorización de biometría (obligatoria si el método es facial)';
comment on column iot.credencial_acceso.vigente_desde is 'Desde';
comment on column iot.credencial_acceso.vigente_hasta is 'Hasta';
comment on column iot.credencial_acceso.activa is 'En uso';
comment on column iot.credencial_acceso.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.credencial_acceso.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.camara is 'Cámara de la finca: graba en la pasarela local por movimiento y sube solo clips elegidos.';
comment on column iot.camara.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.camara.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.camara.dispositivo_id is 'Dispositivo';
comment on column iot.camara.zona_id is 'Ubicación';
comment on column iot.camara.zona_seguridad_id is 'Zona de seguridad que vigila';
comment on column iot.camara.tipo is 'Tipo (valores: ip_rtsp, termica, timelapse)';
comment on column iot.camara.graba_por_movimiento is 'Graba solo cuando hay movimiento (ahorra energía y almacenamiento)';
comment on column iot.camara.intervalo_timelapse_min is 'Minutos entre fotos de time-lapse';
comment on column iot.camara.retencion_dias is 'Días que se guardan los clips de seguridad antes de borrarse';
comment on column iot.camara.aviso_visible is 'Hay aviso de zona vigilada (Ley 1581)';
comment on column iot.camara.stream_secreto_ref is 'Nombre del secreto con la URL y la clave del video';
comment on column iot.camara.activa is 'En uso';
comment on column iot.camara.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.camara.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.evento_seguridad is 'Hecho de seguridad detectado (intrusión, puerta, humo, gas, acceso): lo publica la pasarela, aunque no haya internet, y queda para su atención (solo inserción salvo la atención).';
comment on column iot.evento_seguridad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.evento_seguridad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.evento_seguridad.zona_seguridad_id is 'Zona';
comment on column iot.evento_seguridad.tipo is 'Qué pasó (valores: intrusion, puerta_abierta, humo, gas, amoniaco, temperatura, sabotaje, falla_energia, acceso_concedido, acceso_denegado)';
comment on column iot.evento_seguridad.detector is 'Qué lo detectó: las reglas usan el hecho, no el tipo de sensor (así una cámara térmica entra sin cambiar reglas) (valores: pir, magnetico, vidrio, camara, camara_termica, sensor_gas, lector_acceso, manual)';
comment on column iot.evento_seguridad.sensor_id is 'Sensor';
comment on column iot.evento_seguridad.camara_id is 'Cámara';
comment on column iot.evento_seguridad.credencial_id is 'Credencial usada (accesos)';
comment on column iot.evento_seguridad.severidad is 'Severidad (valores: informativa, media, alta, critica)';
comment on column iot.evento_seguridad.estado_alarma is 'Estado de la alarma cuando ocurrió';
comment on column iot.evento_seguridad.acciones is 'Lo que hizo la pasarela: sirena, reflectores, extractor, aviso push o SMS';
comment on column iot.evento_seguridad.ocurrido_en is 'Momento (reloj de la pasarela)';
comment on column iot.evento_seguridad.atendido_por is 'Quién lo atendió';
comment on column iot.evento_seguridad.atendido_en is 'Cuándo';
comment on column iot.evento_seguridad.nota_atencion is 'Qué se encontró';
comment on column iot.evento_seguridad.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.evento_seguridad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.clip_video is 'Clip grabado por una cámara: los de seguridad se borran al vencer su retención; los marcados para redes pasan a una pieza audiovisual.';
comment on column iot.clip_video.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.clip_video.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.clip_video.camara_id is 'Cámara';
comment on column iot.clip_video.inicio is 'Inicio';
comment on column iot.clip_video.fin is 'Fin';
comment on column iot.clip_video.motivo is 'Por qué se grabó (valores: movimiento, evento_seguridad, timelapse, manual)';
comment on column iot.clip_video.evento_seguridad_id is 'Evento asociado';
comment on column iot.clip_video.ubicacion is 'Dónde está guardado (valores: pasarela, nube)';
comment on column iot.clip_video.archivo_url is 'Ruta del archivo';
comment on column iot.clip_video.para_redes is 'Elegido para contenido de redes (se conserva)';
comment on column iot.clip_video.retener_hasta is 'Fecha de borrado automático';
comment on column iot.clip_video.borrado_en is 'Cuándo se borró el archivo';
comment on column iot.clip_video.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.clip_video.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ambiental.factor_emision is 'Factor para convertir una medición en CO₂ equivalente, con su fuente; sin fuente no se publica ninguna cifra.';
comment on column ambiental.factor_emision.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ambiental.factor_emision.magnitud is 'Magnitud, ej. kwh_solar';
comment on column ambiental.factor_emision.factor_kgco2e is 'kg de CO₂ equivalente evitados por unidad';
comment on column ambiental.factor_emision.fuente is 'Documento oficial del que sale el factor';
comment on column ambiental.factor_emision.vigente_desde is 'Desde';
comment on column ambiental.factor_emision.creado_en is 'Fecha y hora de creación del registro';
comment on column ambiental.factor_emision.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ambiental.registro_ambiental is 'Medición ambiental de la finca (energía solar, biogás, compost, humus, agua).';
comment on column ambiental.registro_ambiental.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ambiental.registro_ambiental.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ambiental.registro_ambiental.magnitud is 'Qué se midió (valores: kwh_solar, m3_biogas, kg_compost, kg_humus, litros_agua_reutilizada, litros_agua_consumida)';
comment on column ambiental.registro_ambiental.cantidad is 'Cantidad';
comment on column ambiental.registro_ambiental.fecha is 'Día';
comment on column ambiental.registro_ambiental.origen is 'Cómo se obtuvo (valores: sensor, manual)';
comment on column ambiental.registro_ambiental.sensor_id is 'Sensor, si aplica';
comment on column ambiental.registro_ambiental.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column ambiental.registro_ambiental.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column ambiental.registro_ambiental.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column ambiental.registro_ambiental.creado_en is 'Fecha y hora de creación del registro';
comment on column ambiental.registro_ambiental.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.cuadrilla is 'Grupo de trabajadores que recibe tareas juntos (ej. cuadrilla de cosecha).';
comment on column personal.cuadrilla.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.cuadrilla.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.cuadrilla.codigo is 'Código, ej. CUA-COSECHA';
comment on column personal.cuadrilla.nombre is 'Nombre';
comment on column personal.cuadrilla.lider_id is 'Trabajador que coordina la cuadrilla';
comment on column personal.cuadrilla.activa is 'En uso';
comment on column personal.cuadrilla.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.cuadrilla.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.cuadrilla_miembro is 'Trabajadores de cada cuadrilla, con fechas.';
comment on column personal.cuadrilla_miembro.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.cuadrilla_miembro.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.cuadrilla_miembro.cuadrilla_id is 'Cuadrilla';
comment on column personal.cuadrilla_miembro.empleado_id is 'Trabajador';
comment on column personal.cuadrilla_miembro.desde is 'Desde';
comment on column personal.cuadrilla_miembro.hasta is 'Hasta; vacío = sigue';
comment on column personal.cuadrilla_miembro.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.cuadrilla_miembro.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.turno is 'Horario de trabajo programado de una persona en un día.';
comment on column personal.turno.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.turno.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.turno.empleado_id is 'Trabajador';
comment on column personal.turno.fecha is 'Día';
comment on column personal.turno.hora_inicio is 'Hora de entrada';
comment on column personal.turno.hora_fin is 'Hora de salida';
comment on column personal.turno.tipo is 'Tipo de turno (define recargos) (valores: diurno, nocturno, mixto, descanso, festivo)';
comment on column personal.turno.area_id is 'Área en la que trabaja ese turno';
comment on column personal.turno.cronograma_id is 'Cronograma del que salió';
comment on column personal.turno.horas is 'Horas del turno (las calcula la base; si la salida es menor que la entrada, cruza la medianoche)';
comment on column personal.turno.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.turno.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.ausencia is 'Vacaciones, permisos, incapacidades y licencias. Guarda solo el tipo y las fechas, nunca el diagnóstico médico.';
comment on column personal.ausencia.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.ausencia.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.ausencia.empleado_id is 'Trabajador';
comment on column personal.ausencia.tipo is 'Tipo (valores: vacaciones, permiso, incapacidad_general, incapacidad_laboral, licencia_maternidad, licencia_paternidad, luto, calamidad, suspension)';
comment on column personal.ausencia.desde is 'Primer día';
comment on column personal.ausencia.hasta is 'Último día';
comment on column personal.ausencia.remunerada is 'Si se paga';
comment on column personal.ausencia.soporte_documento_id is 'Soporte (sin diagnóstico)';
comment on column personal.ausencia.aprobada_por is 'Quién la aprobó';
comment on column personal.ausencia.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.ausencia.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.plantilla_tarea is 'Labor que se repite (recoger huevos dos veces al día, revisar bebederos, deshierbe semanal) y genera las tareas del día.';
comment on column personal.plantilla_tarea.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.plantilla_tarea.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.plantilla_tarea.codigo is 'Código, ej. REC-HUEVO-AM';
comment on column personal.plantilla_tarea.nombre is 'Nombre';
comment on column personal.plantilla_tarea.proceso is 'Proceso al que pertenece (une con la matriz de responsabilidades), ej. postura';
comment on column personal.plantilla_tarea.recurrencia is 'Cada cuánto se repite (valores: diaria, semanal, mensual, unica)';
comment on column personal.plantilla_tarea.dias_semana is 'Días (1 lunes … 7 domingo) para las semanales';
comment on column personal.plantilla_tarea.hora_limite is 'Hora máxima para terminarla';
comment on column personal.plantilla_tarea.zona_id is 'Zona';
comment on column personal.plantilla_tarea.duracion_estimada_min is 'Minutos estimados (estándar para productividad)';
comment on column personal.plantilla_tarea.competencia_id is 'Habilitación que exige; sin ella no se asigna';
comment on column personal.plantilla_tarea.forma_pago is 'Si la tarea aprobada paga jornal o destajo (nunca afecta el salario fijo) (valores: ninguna, jornal, destajo)';
comment on column personal.plantilla_tarea.valor_unitario is 'Valor del jornal o de cada unidad a destajo';
comment on column personal.plantilla_tarea.unidad_destajo is 'Unidad que se paga a destajo, ej. kg, racimo, planta';
comment on column personal.plantilla_tarea.registro_que_crea is 'Registro que nace de la tarea aprobada (valores: ninguno, postura, alimentacion, labor_cultural, bioseguridad, riego, cosecha)';
comment on column personal.plantilla_tarea.pasos is 'Lista de chequeo';
comment on column personal.plantilla_tarea.area_id is 'Área de responsabilidad';
comment on column personal.plantilla_tarea.prioridad is 'Prioridad (valores: baja, media, alta, critica)';
comment on column personal.plantilla_tarea.activa is 'En uso';
comment on column personal.plantilla_tarea.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.plantilla_tarea.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.tarea is 'Trabajo concreto con responsable, lugar, plazo y evidencia. Solo se asigna a quien está disponible y habilitado; aprobada no se edita.';
comment on column personal.tarea.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.tarea.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.tarea.plantilla_tarea_id is 'Plantilla de la que salió';
comment on column personal.tarea.titulo is 'Qué hay que hacer';
comment on column personal.tarea.proceso is 'Proceso';
comment on column personal.tarea.fecha is 'Día';
comment on column personal.tarea.hora_limite is 'Plazo';
comment on column personal.tarea.prioridad is 'Prioridad (valores: baja, media, alta, critica)';
comment on column personal.tarea.zona_id is 'Zona';
comment on column personal.tarea.area_id is 'Área de responsabilidad (su responsable puede aprobarla)';
comment on column personal.tarea.lote_animal_id is 'Lote de animales';
comment on column personal.tarea.siembra_id is 'Siembra';
comment on column personal.tarea.activo_id is 'Equipo que se usa o se mantiene';
comment on column personal.tarea.empleado_id is 'Responsable';
comment on column personal.tarea.cuadrilla_id is 'Cuadrilla responsable';
comment on column personal.tarea.origen is 'De dónde salió (valores: plan, manual, agente, orden_trabajo, accion_correctiva, mision_robot, proyecto, agenda)';
comment on column personal.tarea.agente_id is 'Agente que la propuso (no asigna por su cuenta)';
comment on column personal.tarea.estado is 'Estado (valores: pendiente, en_curso, terminada, aprobada, devuelta, cancelada)';
comment on column personal.tarea.iniciada_en is 'Inicio (escaneo del carné)';
comment on column personal.tarea.terminada_en is 'Fin';
comment on column personal.tarea.cantidad is 'Cantidad lograda (kg, aves, plantas) para destajo y productividad';
comment on column personal.tarea.unidad is 'Unidad de la cantidad';
comment on column personal.tarea.aprobado_por is 'Quién la aprobó o devolvió';
comment on column personal.tarea.aprobado_en is 'Cuándo';
comment on column personal.tarea.comentario_revision is 'Comentario al aprobar o devolver';
comment on column personal.tarea.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column personal.tarea.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column personal.tarea.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column personal.tarea.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.tarea.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.paso_tarea is 'Paso de la lista de chequeo de una tarea.';
comment on column personal.paso_tarea.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.paso_tarea.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.paso_tarea.tarea_id is 'Tarea';
comment on column personal.paso_tarea.orden is 'Orden';
comment on column personal.paso_tarea.descripcion is 'Paso';
comment on column personal.paso_tarea.hecho is 'Marcado';
comment on column personal.paso_tarea.hecho_en is 'Cuándo';
comment on column personal.paso_tarea.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column personal.paso_tarea.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column personal.paso_tarea.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column personal.paso_tarea.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.paso_tarea.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.evidencia_tarea is 'Prueba de una tarea: foto, lectura del carné o del lote, nota de voz o el registro que creó.';
comment on column personal.evidencia_tarea.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.evidencia_tarea.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.evidencia_tarea.tarea_id is 'Tarea';
comment on column personal.evidencia_tarea.tipo is 'Tipo (valores: foto, lectura_qr, lectura_nfc, nota_voz, documento, registro)';
comment on column personal.evidencia_tarea.archivo_url is 'Archivo';
comment on column personal.evidencia_tarea.registro_tabla is 'Tabla del registro creado, ej. produccion.registro_postura';
comment on column personal.evidencia_tarea.registro_id is 'Id del registro';
comment on column personal.evidencia_tarea.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column personal.evidencia_tarea.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column personal.evidencia_tarea.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column personal.evidencia_tarea.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.evidencia_tarea.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.matriz_responsabilidad is 'Matriz RACI: para cada proceso, qué rol lo hace, lo aprueba, es consultado o informado.';
comment on column personal.matriz_responsabilidad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.matriz_responsabilidad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.matriz_responsabilidad.proceso is 'Proceso, ej. postura, venta, nomina';
comment on column personal.matriz_responsabilidad.rol_id is 'Rol';
comment on column personal.matriz_responsabilidad.responsabilidad is 'R, A, C o I (valores: responsable, aprueba, consultado, informado)';
comment on column personal.matriz_responsabilidad.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.matriz_responsabilidad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.asignacion_equipo is 'Quién tiene cada herramienta o equipo, desde cuándo y en qué estado lo recibió y lo devolvió.';
comment on column personal.asignacion_equipo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.asignacion_equipo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.asignacion_equipo.activo_id is 'Equipo';
comment on column personal.asignacion_equipo.empleado_id is 'Trabajador';
comment on column personal.asignacion_equipo.entregado_en is 'Entrega';
comment on column personal.asignacion_equipo.estado_entrega is 'Estado al entregar (valores: bueno, regular, malo)';
comment on column personal.asignacion_equipo.devuelto_en is 'Devolución';
comment on column personal.asignacion_equipo.estado_devolucion is 'Estado al devolver (valores: bueno, regular, malo, perdido)';
comment on column personal.asignacion_equipo.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.asignacion_equipo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.credencial_trabajo is 'Carné del trabajador con QR o etiqueta NFC para registrar quién hizo qué, sin biometría.';
comment on column personal.credencial_trabajo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.credencial_trabajo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.credencial_trabajo.empleado_id is 'Trabajador';
comment on column personal.credencial_trabajo.tipo is 'Tipo (nunca biométrico) (valores: qr, nfc)';
comment on column personal.credencial_trabajo.codigo_hash is 'Huella SHA-256 del código impreso o grabado';
comment on column personal.credencial_trabajo.emitida_en is 'Emisión';
comment on column personal.credencial_trabajo.revocada_en is 'Revocación (pérdida o retiro)';
comment on column personal.credencial_trabajo.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.credencial_trabajo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.jornada is 'Registro de jornada (entrada, salida, horas y labor) para jornaleros sin tarea asignada ese día.';
comment on column personal.jornada.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.jornada.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.jornada.empleado_id is 'Trabajador';
comment on column personal.jornada.fecha is 'Día';
comment on column personal.jornada.entrada is 'Entrada';
comment on column personal.jornada.salida is 'Salida';
comment on column personal.jornada.horas is 'Horas trabajadas';
comment on column personal.jornada.labor is 'Labor hecha';
comment on column personal.jornada.zona_id is 'Zona';
comment on column personal.jornada.metodo_registro is 'Cómo se registró (valores: qr, nfc, manual)';
comment on column personal.jornada.aprobada_por is 'Quién la aprobó';
comment on column personal.jornada.aprobada_en is 'Cuándo';
comment on column personal.jornada.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column personal.jornada.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column personal.jornada.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column personal.jornada.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.jornada.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.concepto_nomina is 'Concepto de la nómina (salario, auxilio, horas extra, recargos, jornal, destajo, deducciones, aportes). La tarifa vive en nucleo.parametro, nunca en el código.';
comment on column nomina.concepto_nomina.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.concepto_nomina.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.concepto_nomina.codigo is 'Código, ej. SALARIO, AUX_TRANSPORTE, JORNAL, DESTAJO, SALUD_EMP';
comment on column nomina.concepto_nomina.nombre is 'Nombre';
comment on column nomina.concepto_nomina.tipo is 'Tipo (valores: devengado, deduccion, aporte_empleador, provision)';
comment on column nomina.concepto_nomina.base is 'Cómo se calcula (valores: salario, jornal, destajo, horas, valor_fijo, porcentaje)';
comment on column nomina.concepto_nomina.parametro_clave is 'Clave de nucleo.parametro con la tarifa vigente';
comment on column nomina.concepto_nomina.constitutivo_salario is 'Hace parte de la base para prestaciones';
comment on column nomina.concepto_nomina.cuenta_contable_id is 'Cuenta de causación';
comment on column nomina.concepto_nomina.codigo_dian is 'Elemento del documento soporte de nómina electrónica';
comment on column nomina.concepto_nomina.activo is 'En uso';
comment on column nomina.concepto_nomina.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.concepto_nomina.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.periodo_nomina is 'Periodo de pago. Cerrado no se edita; las correcciones van como nota de ajuste. Cierre con doble aprobación y nunca por un agente.';
comment on column nomina.periodo_nomina.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.periodo_nomina.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.periodo_nomina.codigo is 'Código, ej. 2026-11';
comment on column nomina.periodo_nomina.tipo is 'Frecuencia (valores: mensual, quincenal, semanal)';
comment on column nomina.periodo_nomina.desde is 'Primer día';
comment on column nomina.periodo_nomina.hasta is 'Último día';
comment on column nomina.periodo_nomina.estado is 'Estado (valores: abierto, prenomina, cerrado, anulado)';
comment on column nomina.periodo_nomina.preparado_por is 'Quién armó la prenómina';
comment on column nomina.periodo_nomina.cerrado_por is 'Primera aprobación del cierre';
comment on column nomina.periodo_nomina.aprobado_por is 'Segunda aprobación (persona distinta)';
comment on column nomina.periodo_nomina.cerrado_en is 'Cuándo';
comment on column nomina.periodo_nomina.comprobante_id is 'Comprobante de causación';
comment on column nomina.periodo_nomina.ajusta_periodo_id is 'Si es nota de ajuste, periodo que corrige';
comment on column nomina.periodo_nomina.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.periodo_nomina.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.novedad is 'Hecho que se paga o descuenta en el periodo: salario fijo, jornales y destajo de tareas aprobadas, horas extra, ausencias, préstamos.';
comment on column nomina.novedad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.novedad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.novedad.periodo_id is 'Periodo';
comment on column nomina.novedad.empleado_id is 'Trabajador';
comment on column nomina.novedad.concepto_id is 'Concepto';
comment on column nomina.novedad.cantidad is 'Días, horas, jornales o unidades';
comment on column nomina.novedad.valor_unitario is 'Valor por unidad';
comment on column nomina.novedad.valor is 'Valor total';
comment on column nomina.novedad.origen is 'De dónde sale (valores: contrato, tarea, jornada, ausencia, manual)';
comment on column nomina.novedad.tarea_id is 'Tarea aprobada que la origina';
comment on column nomina.novedad.jornada_id is 'Jornada que la origina';
comment on column nomina.novedad.ausencia_id is 'Ausencia que la origina';
comment on column nomina.novedad.observacion is 'Nota';
comment on column nomina.novedad.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.novedad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.liquidacion is 'Resultado del periodo para un trabajador: devengado, deducciones y neto.';
comment on column nomina.liquidacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.liquidacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.liquidacion.periodo_id is 'Periodo';
comment on column nomina.liquidacion.empleado_id is 'Trabajador';
comment on column nomina.liquidacion.total_devengado is 'Devengado';
comment on column nomina.liquidacion.total_deducciones is 'Deducciones';
comment on column nomina.liquidacion.neto is 'Neto a pagar';
comment on column nomina.liquidacion.estado is 'Estado (valores: borrador, aprobada, pagada)';
comment on column nomina.liquidacion.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.liquidacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.liquidacion_detalle is 'Línea de la liquidación por concepto.';
comment on column nomina.liquidacion_detalle.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.liquidacion_detalle.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.liquidacion_detalle.liquidacion_id is 'Liquidación';
comment on column nomina.liquidacion_detalle.concepto_id is 'Concepto';
comment on column nomina.liquidacion_detalle.cantidad is 'Cantidad';
comment on column nomina.liquidacion_detalle.valor is 'Valor';
comment on column nomina.liquidacion_detalle.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.liquidacion_detalle.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.provision_prestacion is 'Provisión mensual de cesantías, intereses, prima y vacaciones.';
comment on column nomina.provision_prestacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.provision_prestacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.provision_prestacion.periodo_id is 'Periodo';
comment on column nomina.provision_prestacion.empleado_id is 'Trabajador';
comment on column nomina.provision_prestacion.tipo is 'Prestación (valores: cesantias, intereses_cesantias, prima, vacaciones)';
comment on column nomina.provision_prestacion.base is 'Base';
comment on column nomina.provision_prestacion.valor is 'Valor provisionado';
comment on column nomina.provision_prestacion.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.provision_prestacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.documento_nomina_electronica is 'Documento soporte de pago de nómina electrónica (uno por trabajador al mes). Se transmite por el servicio gratuito de la DIAN o un proveedor autorizado; se enciende con nomina_electronica.';
comment on column nomina.documento_nomina_electronica.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.documento_nomina_electronica.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.documento_nomina_electronica.liquidacion_id is 'Liquidación';
comment on column nomina.documento_nomina_electronica.tipo is 'Tipo (valores: individual, ajuste)';
comment on column nomina.documento_nomina_electronica.proveedor is 'Por dónde se transmite (valores: dian_gratuito, proveedor_tecnologico)';
comment on column nomina.documento_nomina_electronica.cune is 'Código único devuelto por la DIAN';
comment on column nomina.documento_nomina_electronica.estado is 'Estado (valores: pendiente, enviado, aceptado, rechazado)';
comment on column nomina.documento_nomina_electronica.enviado_en is 'Envío';
comment on column nomina.documento_nomina_electronica.respuesta is 'Respuesta del proveedor';
comment on column nomina.documento_nomina_electronica.xml_url is 'XML firmado por el proveedor (nunca se firma a mano)';
comment on column nomina.documento_nomina_electronica.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.documento_nomina_electronica.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.planilla_pila is 'Archivo de la planilla de seguridad social para el operador de la PILA; el pago lo hace una persona.';
comment on column nomina.planilla_pila.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.planilla_pila.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.planilla_pila.periodo_id is 'Periodo';
comment on column nomina.planilla_pila.tipo_planilla is 'Tipo de planilla (E = empleados)';
comment on column nomina.planilla_pila.archivo_url is 'Archivo generado';
comment on column nomina.planilla_pila.operador is 'Operador de información';
comment on column nomina.planilla_pila.numero_planilla is 'Número asignado por el operador';
comment on column nomina.planilla_pila.pagada_por is 'Quién la pagó';
comment on column nomina.planilla_pila.pagada_en is 'Cuándo';
comment on column nomina.planilla_pila.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.planilla_pila.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.pago_nomina is 'Pago de una liquidación (transferencia, Bre-B o efectivo). Lo prepara una persona y lo aprueba otra; nadie aprueba su propio pago.';
comment on column nomina.pago_nomina.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.pago_nomina.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.pago_nomina.liquidacion_id is 'Liquidación';
comment on column nomina.pago_nomina.medio is 'Medio (valores: transferencia, bre_b, efectivo)';
comment on column nomina.pago_nomina.valor is 'Valor';
comment on column nomina.pago_nomina.preparado_por is 'Quién lo preparó';
comment on column nomina.pago_nomina.aprobado_por is 'Primera aprobación';
comment on column nomina.pago_nomina.segunda_aprobacion_por is 'Segunda aprobación (pagos sobre el monto del parámetro monto_doble_aprobacion)';
comment on column nomina.pago_nomina.pagado_en is 'Cuándo se pagó';
comment on column nomina.pago_nomina.referencia is 'Referencia bancaria';
comment on column nomina.pago_nomina.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.pago_nomina.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nomina.exportacion_nomina is 'Archivo para el contador cuando lleva la nómina en su propio programa.';
comment on column nomina.exportacion_nomina.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nomina.exportacion_nomina.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nomina.exportacion_nomina.periodo_id is 'Periodo';
comment on column nomina.exportacion_nomina.formato is 'Formato (valores: csv, excel, siigo, world_office, helisa, otro)';
comment on column nomina.exportacion_nomina.archivo_url is 'Archivo';
comment on column nomina.exportacion_nomina.generado_por is 'Quién lo generó';
comment on column nomina.exportacion_nomina.creado_en is 'Fecha y hora de creación del registro';
comment on column nomina.exportacion_nomina.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.competencia is 'Habilidad que habilita tareas (registrar vacunas, aplicar insumos, liberar lotes, operar motosierra), con su vigencia.';
comment on column formacion.competencia.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.competencia.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.competencia.codigo is 'Código, ej. aplicar_vacunas';
comment on column formacion.competencia.nombre is 'Nombre';
comment on column formacion.competencia.vigencia_meses is 'Meses que dura el certificado; vacío = no vence';
comment on column formacion.competencia.descripcion is 'Qué permite hacer';
comment on column formacion.competencia.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.competencia.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.curso is 'Curso virtual, presencial o mixto para operarios o estudiantes; los externos (SENA, FAO, Moodle) se enlazan.';
comment on column formacion.curso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.curso.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.curso.codigo is 'Código';
comment on column formacion.curso.nombre is 'Nombre';
comment on column formacion.curso.descripcion is 'Contenido';
comment on column formacion.curso.publico is 'A quién va (valores: operarios, estudiantes, ambos)';
comment on column formacion.curso.modalidad is 'Modalidad (valores: virtual, presencial, mixto)';
comment on column formacion.curso.competencia_id is 'Habilitación que otorga al aprobar';
comment on column formacion.curso.nota_minima is 'Nota mínima para aprobar (escala 0 a 5)';
comment on column formacion.curso.duracion_horas is 'Horas';
comment on column formacion.curso.origen is 'De dónde viene (valores: propio, sena, fao, moodle, otro)';
comment on column formacion.curso.url_externa is 'Enlace, si es externo';
comment on column formacion.curso.ruta_cargo is 'Ruta de aprendizaje, ej. operario_galpon, vendedor';
comment on column formacion.curso.activo is 'Publicado';
comment on column formacion.curso.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.curso.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.leccion is 'Lección de un curso (texto, video corto, práctica guiada); se descarga para verla sin señal.';
comment on column formacion.leccion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.leccion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.leccion.curso_id is 'Curso';
comment on column formacion.leccion.orden is 'Orden';
comment on column formacion.leccion.titulo is 'Título';
comment on column formacion.leccion.tipo is 'Tipo (valores: texto, video, practica, tutorial_pantalla)';
comment on column formacion.leccion.contenido_url is 'Archivo';
comment on column formacion.leccion.pantalla is 'Pantalla de la app que explica (tutoriales dentro de la app)';
comment on column formacion.leccion.documento_id is 'Protocolo o manual de base';
comment on column formacion.leccion.descargable is 'Se puede ver sin conexión';
comment on column formacion.leccion.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.leccion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.evaluacion is 'Examen de un curso.';
comment on column formacion.evaluacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.evaluacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.evaluacion.curso_id is 'Curso';
comment on column formacion.evaluacion.titulo is 'Título';
comment on column formacion.evaluacion.intentos_max is 'Intentos';
comment on column formacion.evaluacion.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.evaluacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.pregunta is 'Pregunta de una evaluación.';
comment on column formacion.pregunta.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.pregunta.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.pregunta.evaluacion_id is 'Evaluación';
comment on column formacion.pregunta.orden is 'Orden';
comment on column formacion.pregunta.enunciado is 'Pregunta';
comment on column formacion.pregunta.tipo is 'Tipo (valores: unica, multiple, verdadero_falso, practica)';
comment on column formacion.pregunta.opciones is 'Opciones';
comment on column formacion.pregunta.respuesta_correcta is 'Respuesta';
comment on column formacion.pregunta.puntos is 'Puntos';
comment on column formacion.pregunta.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.pregunta.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.inscripcion is 'Persona (operario o estudiante) inscrita en un curso, con su nota.';
comment on column formacion.inscripcion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.inscripcion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.inscripcion.curso_id is 'Curso';
comment on column formacion.inscripcion.tercero_id is 'Persona';
comment on column formacion.inscripcion.inscrito_en is 'Inscripción';
comment on column formacion.inscripcion.estado is 'Estado (valores: inscrito, en_curso, aprobado, reprobado, retirado)';
comment on column formacion.inscripcion.nota is 'Nota final';
comment on column formacion.inscripcion.aprobado_en is 'Fecha de aprobación';
comment on column formacion.inscripcion.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.inscripcion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.progreso is 'Lecciones vistas por cada inscrito.';
comment on column formacion.progreso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.progreso.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.progreso.inscripcion_id is 'Inscripción';
comment on column formacion.progreso.leccion_id is 'Lección';
comment on column formacion.progreso.completada_en is 'Cuándo';
comment on column formacion.progreso.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column formacion.progreso.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column formacion.progreso.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column formacion.progreso.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.progreso.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.sesion_presencial is 'Sesión dictada por el veterinario, el agrónomo o el encargado; su asistencia cuenta igual que un curso virtual.';
comment on column formacion.sesion_presencial.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.sesion_presencial.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.sesion_presencial.curso_id is 'Curso';
comment on column formacion.sesion_presencial.instructor_id is 'Quién la dicta';
comment on column formacion.sesion_presencial.fecha is 'Día';
comment on column formacion.sesion_presencial.lugar is 'Lugar';
comment on column formacion.sesion_presencial.duracion_horas is 'Horas';
comment on column formacion.sesion_presencial.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.sesion_presencial.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.asistencia is 'Asistencia y nota de cada persona en una sesión presencial.';
comment on column formacion.asistencia.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.asistencia.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.asistencia.sesion_id is 'Sesión';
comment on column formacion.asistencia.tercero_id is 'Persona';
comment on column formacion.asistencia.asistio is 'Asistió';
comment on column formacion.asistencia.nota is 'Nota práctica';
comment on column formacion.asistencia.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column formacion.asistencia.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column formacion.asistencia.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column formacion.asistencia.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.asistencia.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.certificado is 'Certificado interno con fecha, nota y vencimiento; al emitirse crea la habilitación.';
comment on column formacion.certificado.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.certificado.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.certificado.tercero_id is 'Persona';
comment on column formacion.certificado.competencia_id is 'Competencia';
comment on column formacion.certificado.inscripcion_id is 'Curso virtual aprobado';
comment on column formacion.certificado.sesion_id is 'Sesión presencial';
comment on column formacion.certificado.emitido_en is 'Emisión';
comment on column formacion.certificado.vence_en is 'Vencimiento';
comment on column formacion.certificado.nota is 'Nota';
comment on column formacion.certificado.codigo_verificacion is 'Código para verificarlo';
comment on column formacion.certificado.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.certificado.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.habilitacion is 'Permiso para hacer una tarea, nacido de un certificado. Al vencer el certificado se retira sola.';
comment on column formacion.habilitacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.habilitacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.habilitacion.tercero_id is 'Persona';
comment on column formacion.habilitacion.competencia_id is 'Competencia';
comment on column formacion.habilitacion.certificado_id is 'Certificado que la sustenta';
comment on column formacion.habilitacion.desde is 'Desde';
comment on column formacion.habilitacion.hasta is 'Hasta';
comment on column formacion.habilitacion.activa is 'Vigente';
comment on column formacion.habilitacion.retirada_en is 'Cuándo se retiró';
comment on column formacion.habilitacion.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.habilitacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table activos.activo is 'Hoja de vida de cada equipo de la finca (camioneta, motocultor, guadañas, bombas, paneles, dron, robot).';
comment on column activos.activo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column activos.activo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column activos.activo.codigo is 'Código, ej. ACT-GUA-01';
comment on column activos.activo.nombre is 'Nombre';
comment on column activos.activo.tipo is 'Tipo (valores: vehiculo, maquinaria, herramienta, bomba, panel_solar, bateria, equipo_electronico, dron, robot, infraestructura, otro)';
comment on column activos.activo.marca is 'Marca';
comment on column activos.activo.modelo is 'Modelo';
comment on column activos.activo.serie is 'Número de serie';
comment on column activos.activo.fecha_compra is 'Compra';
comment on column activos.activo.valor_compra is 'Costo de adquisición';
comment on column activos.activo.valor_residual is 'Valor de salvamento';
comment on column activos.activo.vida_util_meses is 'Vida útil';
comment on column activos.activo.metodo_depreciacion is 'Método (valores: linea_recta, ninguno)';
comment on column activos.activo.zona_id is 'Ubicación';
comment on column activos.activo.responsable_id is 'Responsable';
comment on column activos.activo.centro_costo_id is 'Centro de costo que lo usa';
comment on column activos.activo.garantia_hasta is 'Garantía';
comment on column activos.activo.horometro is 'Horas de uso acumuladas';
comment on column activos.activo.odometro is 'Kilómetros acumulados';
comment on column activos.activo.vehiculo_id is 'Vehículo de entregas, si es el mismo';
comment on column activos.activo.dispositivo_id is 'Dispositivo IoT, si lo tiene';
comment on column activos.activo.registro_aerocivil is 'Registro del dron ante la Aerocivil (RAC 100)';
comment on column activos.activo.estado is 'Estado (valores: operativo, en_mantenimiento, danado, dado_de_baja)';
comment on column activos.activo.creado_en is 'Fecha y hora de creación del registro';
comment on column activos.activo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table activos.plan_mantenimiento is 'Mantenimiento por horas de uso, kilómetros o días (cambio de aceite, afilado, revisión de la bomba).';
comment on column activos.plan_mantenimiento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column activos.plan_mantenimiento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column activos.plan_mantenimiento.activo_id is 'Equipo';
comment on column activos.plan_mantenimiento.nombre is 'Qué se hace';
comment on column activos.plan_mantenimiento.tipo is 'Tipo (predictivo cuando hay sensores) (valores: preventivo, predictivo)';
comment on column activos.plan_mantenimiento.frecuencia_tipo is 'Base de la frecuencia (valores: horas, km, dias)';
comment on column activos.plan_mantenimiento.frecuencia_valor is 'Cada cuánto';
comment on column activos.plan_mantenimiento.ultima_lectura is 'Horómetro u odómetro en la última ejecución';
comment on column activos.plan_mantenimiento.ultima_fecha is 'Fecha de la última ejecución';
comment on column activos.plan_mantenimiento.activo is 'En uso';
comment on column activos.plan_mantenimiento.creado_en is 'Fecha y hora de creación del registro';
comment on column activos.plan_mantenimiento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table activos.orden_trabajo is 'Orden de mantenimiento: la crea sola la regla al vencer el plan y se asigna como tarea; descuenta repuestos del inventario.';
comment on column activos.orden_trabajo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column activos.orden_trabajo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column activos.orden_trabajo.activo_id is 'Equipo';
comment on column activos.orden_trabajo.plan_id is 'Plan que la originó';
comment on column activos.orden_trabajo.tipo is 'Tipo (valores: preventivo, correctivo, predictivo)';
comment on column activos.orden_trabajo.descripcion is 'Qué hacer';
comment on column activos.orden_trabajo.estado is 'Estado (valores: abierta, en_curso, cerrada, cancelada)';
comment on column activos.orden_trabajo.tarea_id is 'Tarea asignada';
comment on column activos.orden_trabajo.lectura_cierre is 'Horómetro u odómetro al cerrar';
comment on column activos.orden_trabajo.costo_mano_obra is 'Mano de obra';
comment on column activos.orden_trabajo.costo_repuestos is 'Repuestos';
comment on column activos.orden_trabajo.cerrada_en is 'Cierre';
comment on column activos.orden_trabajo.creado_en is 'Fecha y hora de creación del registro';
comment on column activos.orden_trabajo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table activos.repuesto_orden is 'Repuesto usado en una orden de trabajo (sale del kardex).';
comment on column activos.repuesto_orden.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column activos.repuesto_orden.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column activos.repuesto_orden.orden_id is 'Orden';
comment on column activos.repuesto_orden.producto_id is 'Repuesto';
comment on column activos.repuesto_orden.cantidad is 'Cantidad';
comment on column activos.repuesto_orden.movimiento_id is 'Salida en el kardex';
comment on column activos.repuesto_orden.creado_en is 'Fecha y hora de creación del registro';
comment on column activos.repuesto_orden.actualizado_en is 'Fecha y hora de la última modificación';
comment on table activos.uso_activo is 'Uso de un equipo: horas, kilómetros y combustible, cargados al centro de costo que lo usó.';
comment on column activos.uso_activo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column activos.uso_activo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column activos.uso_activo.activo_id is 'Equipo';
comment on column activos.uso_activo.fecha is 'Día';
comment on column activos.uso_activo.empleado_id is 'Quién lo usó';
comment on column activos.uso_activo.horas is 'Horas';
comment on column activos.uso_activo.km is 'Kilómetros';
comment on column activos.uso_activo.combustible_litros is 'Combustible';
comment on column activos.uso_activo.costo_combustible is 'Costo del combustible';
comment on column activos.uso_activo.centro_costo_id is 'Centro de costo';
comment on column activos.uso_activo.tarea_id is 'Tarea';
comment on column activos.uso_activo.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column activos.uso_activo.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column activos.uso_activo.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column activos.uso_activo.creado_en is 'Fecha y hora de creación del registro';
comment on column activos.uso_activo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table activos.depreciacion is 'Depreciación mensual de cada activo (alimenta la contabilidad y el costo por línea).';
comment on column activos.depreciacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column activos.depreciacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column activos.depreciacion.activo_id is 'Equipo';
comment on column activos.depreciacion.mes is 'Primer día del mes';
comment on column activos.depreciacion.valor is 'Depreciación del mes';
comment on column activos.depreciacion.acumulada is 'Depreciación acumulada';
comment on column activos.depreciacion.comprobante_id is 'Comprobante';
comment on column activos.depreciacion.creado_en is 'Fecha y hora de creación del registro';
comment on column activos.depreciacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table documental.documento is 'Papel que la finca no puede perder: permisos, registros ICA, RUT, contratos, protocolos, manuales, evidencias. Con datos personales sigue la Ley 1581.';
comment on column documental.documento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column documental.documento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column documental.documento.codigo is 'Código, ej. PRT-BIO-01';
comment on column documental.documento.titulo is 'Título';
comment on column documental.documento.tipo is 'Tipo (valores: permiso, registro, contrato, protocolo, manual, ficha_tecnica, evidencia, acta, resultado_laboratorio, poliza, certificado, plan, otro)';
comment on column documental.documento.entidad_emisora is 'Quién lo expide, ej. ICA, CAR, DIAN';
comment on column documental.documento.numero is 'Número oficial';
comment on column documental.documento.responsable_id is 'Responsable';
comment on column documental.documento.nivel_acceso is 'Quién lo ve (valores: finca, rol, restringido)';
comment on column documental.documento.rol_id is 'Rol que lo ve, si es por rol';
comment on column documental.documento.contiene_datos_personales is 'Tiene datos personales (Ley 1581)';
comment on column documental.documento.finalidad is 'Para qué se guarda';
comment on column documental.documento.conservar_hasta is 'Hasta cuándo se conserva';
comment on column documental.documento.uso_agentes is 'Lo pueden leer los agentes (solo la versión aprobada y vigente)';
comment on column documental.documento.creado_en is 'Fecha y hora de creación del registro';
comment on column documental.documento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table documental.version_documento is 'Versión de un documento con su archivo, huella, aprobación y vigencia; solo una aprobada vigente a la vez.';
comment on column documental.version_documento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column documental.version_documento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column documental.version_documento.documento_id is 'Documento';
comment on column documental.version_documento.version is 'Número de versión';
comment on column documental.version_documento.archivo_url is 'Archivo en el almacén de objetos';
comment on column documental.version_documento.hash_sha256 is 'Huella del archivo';
comment on column documental.version_documento.estado is 'Estado (valores: borrador, en_revision, aprobada, obsoleta)';
comment on column documental.version_documento.aprobada_por is 'Quién la aprobó';
comment on column documental.version_documento.aprobada_en is 'Cuándo';
comment on column documental.version_documento.vigente_desde is 'Desde';
comment on column documental.version_documento.vence_en is 'Vencimiento (permisos, registros, pólizas)';
comment on column documental.version_documento.avisar_dias is 'Días de aviso antes de vencer';
comment on column documental.version_documento.cambios is 'Qué cambió';
comment on column documental.version_documento.creado_en is 'Fecha y hora de creación del registro';
comment on column documental.version_documento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table documental.vinculo_documento is 'Une un documento con cualquier registro (un lote, una póliza, un activo, una no conformidad).';
comment on column documental.vinculo_documento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column documental.vinculo_documento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column documental.vinculo_documento.documento_id is 'Documento';
comment on column documental.vinculo_documento.registro_tabla is 'Tabla';
comment on column documental.vinculo_documento.registro_id is 'Id';
comment on column documental.vinculo_documento.creado_en is 'Fecha y hora de creación del registro';
comment on column documental.vinculo_documento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.norma is 'Norma o certificación (granja avícola biosegura ICA 3651/2014, BPA ICA 30021/2017, GLOBALG.A.P. IFA v6). Catálogo compartido.';
comment on column cumplimiento.norma.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.norma.codigo is 'Código, ej. ICA_GAB, ICA_BPA, GLOBALGAP_IFA6';
comment on column cumplimiento.norma.nombre is 'Nombre';
comment on column cumplimiento.norma.entidad is 'Entidad';
comment on column cumplimiento.norma.referencia is 'Norma, ej. Resolución ICA 3651 de 2014';
comment on column cumplimiento.norma.obligatoria is 'Obligatoria por ley';
comment on column cumplimiento.norma.condicion_obligatoria is 'Cuándo aplica, ej. postura o levante desde 200 aves';
comment on column cumplimiento.norma.funcion_codigo is 'Función por finca que la enciende; vacío = siempre activa';
comment on column cumplimiento.norma.vigencia_certificado_meses is 'Duración del certificado';
comment on column cumplimiento.norma.url_fuente is 'Texto oficial';
comment on column cumplimiento.norma.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.norma.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.requisito is 'Requisito de una norma con el tipo de evidencia y, si aplica, la regla que la revisa sola.';
comment on column cumplimiento.requisito.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.requisito.norma_id is 'Norma';
comment on column cumplimiento.requisito.codigo is 'Código';
comment on column cumplimiento.requisito.descripcion is 'Qué pide';
comment on column cumplimiento.requisito.tipo_evidencia is 'Evidencia esperada (valores: documento, registro, certificado_formacion, analisis, inspeccion)';
comment on column cumplimiento.requisito.regla_evidencia is 'Revisión automática, ej. documento:protocolo, competencia:bioseguridad, registro:produccion.registro_bioseguridad';
comment on column cumplimiento.requisito.vigencia_dias is 'Días que vale la evidencia';
comment on column cumplimiento.requisito.critico is 'Sin él no se certifica';
comment on column cumplimiento.requisito.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.requisito.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.expediente is 'Expediente de la finca ante una norma (incluye el registro sanitario de predio avícola, RSPA).';
comment on column cumplimiento.expediente.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.expediente.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column cumplimiento.expediente.norma_id is 'Norma';
comment on column cumplimiento.expediente.estado is 'Estado (valores: en_preparacion, solicitado, certificado, suspendido, vencido)';
comment on column cumplimiento.expediente.rspa_numero is 'Registro sanitario de predio avícola (RSPA) del ICA, si aplica';
comment on column cumplimiento.expediente.numero_certificado is 'Número del certificado';
comment on column cumplimiento.expediente.organismo is 'Entidad u organismo certificador';
comment on column cumplimiento.expediente.solicitado_en is 'Solicitud';
comment on column cumplimiento.expediente.certificado_en is 'Certificación';
comment on column cumplimiento.expediente.vence_en is 'Vencimiento';
comment on column cumplimiento.expediente.responsable_id is 'Responsable';
comment on column cumplimiento.expediente.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.expediente.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.evaluacion_requisito is 'Estado de cada requisito en el expediente. Con evidencia vencida pasa solo a no cumple.';
comment on column cumplimiento.evaluacion_requisito.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.evaluacion_requisito.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column cumplimiento.evaluacion_requisito.expediente_id is 'Expediente';
comment on column cumplimiento.evaluacion_requisito.requisito_id is 'Requisito';
comment on column cumplimiento.evaluacion_requisito.estado is 'Estado (valores: cumple, no_cumple, en_proceso, no_aplica)';
comment on column cumplimiento.evaluacion_requisito.origen is 'Cómo se evaluó (valores: automatica, autoevaluacion, auditoria)';
comment on column cumplimiento.evaluacion_requisito.evaluado_por is 'Quién';
comment on column cumplimiento.evaluacion_requisito.evaluado_en is 'Cuándo';
comment on column cumplimiento.evaluacion_requisito.vence_en is 'Vencimiento de la evidencia que lo sostiene';
comment on column cumplimiento.evaluacion_requisito.observacion is 'Nota';
comment on column cumplimiento.evaluacion_requisito.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column cumplimiento.evaluacion_requisito.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column cumplimiento.evaluacion_requisito.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column cumplimiento.evaluacion_requisito.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.evaluacion_requisito.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.evidencia_requisito is 'Prueba de un requisito: un documento o un registro del sistema, con su vencimiento.';
comment on column cumplimiento.evidencia_requisito.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.evidencia_requisito.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column cumplimiento.evidencia_requisito.evaluacion_id is 'Evaluación';
comment on column cumplimiento.evidencia_requisito.documento_id is 'Documento';
comment on column cumplimiento.evidencia_requisito.registro_tabla is 'Tabla del registro';
comment on column cumplimiento.evidencia_requisito.registro_id is 'Id';
comment on column cumplimiento.evidencia_requisito.descripcion is 'Qué prueba';
comment on column cumplimiento.evidencia_requisito.vence_en is 'Vence';
comment on column cumplimiento.evidencia_requisito.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.evidencia_requisito.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.auditoria_externa is 'Auditoría interna o externa programada, con aviso previo y resultado.';
comment on column cumplimiento.auditoria_externa.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.auditoria_externa.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column cumplimiento.auditoria_externa.expediente_id is 'Expediente';
comment on column cumplimiento.auditoria_externa.tipo is 'Tipo (valores: interna, externa, seguimiento)';
comment on column cumplimiento.auditoria_externa.organismo is 'Quién audita';
comment on column cumplimiento.auditoria_externa.fecha_programada is 'Fecha';
comment on column cumplimiento.auditoria_externa.fecha_realizada is 'Realizada';
comment on column cumplimiento.auditoria_externa.resultado is 'Resultado (valores: pendiente, aprobada, con_hallazgos, rechazada)';
comment on column cumplimiento.auditoria_externa.informe_documento_id is 'Informe';
comment on column cumplimiento.auditoria_externa.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.auditoria_externa.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.no_conformidad is 'Hallazgo; no se cierra sin acciones verificadas y sin quien verifique.';
comment on column cumplimiento.no_conformidad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.no_conformidad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column cumplimiento.no_conformidad.expediente_id is 'Expediente';
comment on column cumplimiento.no_conformidad.auditoria_id is 'Auditoría que la encontró';
comment on column cumplimiento.no_conformidad.requisito_id is 'Requisito';
comment on column cumplimiento.no_conformidad.descripcion is 'Hallazgo';
comment on column cumplimiento.no_conformidad.severidad is 'Severidad (valores: menor, mayor, critica)';
comment on column cumplimiento.no_conformidad.detectada_en is 'Fecha';
comment on column cumplimiento.no_conformidad.estado is 'Estado (valores: abierta, en_tratamiento, cerrada)';
comment on column cumplimiento.no_conformidad.verificacion is 'Cómo se verificó el cierre';
comment on column cumplimiento.no_conformidad.cerrada_por is 'Quién la cerró';
comment on column cumplimiento.no_conformidad.cerrada_en is 'Cuándo';
comment on column cumplimiento.no_conformidad.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.no_conformidad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table cumplimiento.accion_correctiva is 'Acción para corregir una no conformidad, con responsable, plazo y verificación; se asigna como tarea.';
comment on column cumplimiento.accion_correctiva.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column cumplimiento.accion_correctiva.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column cumplimiento.accion_correctiva.no_conformidad_id is 'No conformidad';
comment on column cumplimiento.accion_correctiva.descripcion is 'Qué hacer';
comment on column cumplimiento.accion_correctiva.responsable_id is 'Responsable';
comment on column cumplimiento.accion_correctiva.plazo is 'Plazo';
comment on column cumplimiento.accion_correctiva.tarea_id is 'Tarea';
comment on column cumplimiento.accion_correctiva.estado is 'Estado (valores: pendiente, hecha, verificada, ineficaz)';
comment on column cumplimiento.accion_correctiva.verificada_por is 'Quién verificó';
comment on column cumplimiento.accion_correctiva.verificada_en is 'Cuándo';
comment on column cumplimiento.accion_correctiva.creado_en is 'Fecha y hora de creación del registro';
comment on column cumplimiento.accion_correctiva.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguros.poliza is 'Póliza (cultivo, animales, equipos, responsabilidad civil del dron, paramétrico) con vigencia, prima, suma asegurada e incentivo de Finagro.';
comment on column seguros.poliza.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguros.poliza.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column seguros.poliza.numero is 'Número';
comment on column seguros.poliza.aseguradora_id is 'Aseguradora';
comment on column seguros.poliza.corredor_id is 'Corredor';
comment on column seguros.poliza.tipo is 'Tipo (valores: cultivo, animales, equipos, vehiculo, responsabilidad_civil, dron, parametrico, vida, otro)';
comment on column seguros.poliza.desde is 'Inicio';
comment on column seguros.poliza.hasta is 'Fin';
comment on column seguros.poliza.prima is 'Prima total';
comment on column seguros.poliza.incentivo_pct is 'Porcentaje de la prima subsidiado (Incentivo al Seguro Agropecuario)';
comment on column seguros.poliza.valor_subsidiado is 'Valor subsidiado';
comment on column seguros.poliza.suma_asegurada is 'Suma asegurada';
comment on column seguros.poliza.deducible is 'Deducible';
comment on column seguros.poliza.estado is 'Estado (valores: en_tramite, vigente, vencida, cancelada)';
comment on column seguros.poliza.avisar_dias is 'Aviso antes de vencer';
comment on column seguros.poliza.documento_id is 'Póliza firmada';
comment on column seguros.poliza.creado_en is 'Fecha y hora de creación del registro';
comment on column seguros.poliza.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguros.bien_asegurado is 'Lo que cubre la póliza: un activo, una siembra, un lote de animales o una zona.';
comment on column seguros.bien_asegurado.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguros.bien_asegurado.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column seguros.bien_asegurado.poliza_id is 'Póliza';
comment on column seguros.bien_asegurado.activo_id is 'Equipo';
comment on column seguros.bien_asegurado.siembra_id is 'Siembra';
comment on column seguros.bien_asegurado.lote_animal_id is 'Lote';
comment on column seguros.bien_asegurado.zona_id is 'Zona';
comment on column seguros.bien_asegurado.descripcion is 'Descripción';
comment on column seguros.bien_asegurado.valor_asegurado is 'Valor';
comment on column seguros.bien_asegurado.creado_en is 'Fecha y hora de creación del registro';
comment on column seguros.bien_asegurado.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguros.indice_poliza is 'Regla del índice de un seguro paramétrico; la decide la aseguradora con su fuente, no los sensores de la finca.';
comment on column seguros.indice_poliza.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguros.indice_poliza.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column seguros.indice_poliza.poliza_id is 'Póliza';
comment on column seguros.indice_poliza.variable is 'Variable (valores: lluvia_mm, temperatura_c, dias_secos, viento_kmh, otro)';
comment on column seguros.indice_poliza.fuente_oficial is 'Fuente que usa la aseguradora, ej. satélite CHIRPS';
comment on column seguros.indice_poliza.comparador is 'Se cumple si el valor es mayor o menor que el umbral (valores: mayor, menor)';
comment on column seguros.indice_poliza.umbral is 'Umbral';
comment on column seguros.indice_poliza.ventana_dias is 'Días acumulados';
comment on column seguros.indice_poliza.sensor_id is 'Sensor propio con que se compara';
comment on column seguros.indice_poliza.creado_en is 'Fecha y hora de creación del registro';
comment on column seguros.indice_poliza.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguros.aviso_siniestro is 'Aviso de posible siniestro con la serie de datos como evidencia. No hay reclamación automática: una persona lo revisa y lo envía.';
comment on column seguros.aviso_siniestro.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguros.aviso_siniestro.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column seguros.aviso_siniestro.poliza_id is 'Póliza';
comment on column seguros.aviso_siniestro.indice_id is 'Índice, si es paramétrico';
comment on column seguros.aviso_siniestro.detectado_en is 'Cuándo';
comment on column seguros.aviso_siniestro.descripcion is 'Qué pasó';
comment on column seguros.aviso_siniestro.serie_datos is 'Datos usados como evidencia';
comment on column seguros.aviso_siniestro.estado is 'Estado (valores: borrador, revisado, enviado, pagado, rechazado, descartado)';
comment on column seguros.aviso_siniestro.revisado_por is 'Quién lo revisó';
comment on column seguros.aviso_siniestro.enviado_en is 'Envío al corredor';
comment on column seguros.aviso_siniestro.valor_reclamado is 'Reclamado';
comment on column seguros.aviso_siniestro.valor_pagado is 'Pagado';
comment on column seguros.aviso_siniestro.creado_en is 'Fecha y hora de creación del registro';
comment on column seguros.aviso_siniestro.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.diagnostico_imagen is 'Foto de hoja, fruto o animal analizada por el agente Agrónomo. Es una propuesta: no crea compras ni aplicaciones; la confirma una persona.';
comment on column ia.diagnostico_imagen.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.diagnostico_imagen.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.diagnostico_imagen.agente_id is 'Agente';
comment on column ia.diagnostico_imagen.foto_url is 'Foto';
comment on column ia.diagnostico_imagen.objetivo is 'Qué se fotografió (valores: hoja, fruto, tallo, animal, huevo, otro)';
comment on column ia.diagnostico_imagen.siembra_id is 'Siembra';
comment on column ia.diagnostico_imagen.lote_animal_id is 'Lote';
comment on column ia.diagnostico_imagen.tomada_por is 'Quién la tomó';
comment on column ia.diagnostico_imagen.diagnostico_propuesto is 'Plaga o enfermedad probable';
comment on column ia.diagnostico_imagen.confianza is 'Confianza del modelo (0 a 1)';
comment on column ia.diagnostico_imagen.resultado is 'Alternativas y fotos parecidas';
comment on column ia.diagnostico_imagen.estado is 'Revisión humana (valores: pendiente, confirmado, corregido, descartado)';
comment on column ia.diagnostico_imagen.diagnostico_final is 'Lo que decidió el agrónomo o el veterinario';
comment on column ia.diagnostico_imagen.revisado_por is 'Quién revisó';
comment on column ia.diagnostico_imagen.revisado_en is 'Cuándo';
comment on column ia.diagnostico_imagen.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column ia.diagnostico_imagen.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column ia.diagnostico_imagen.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column ia.diagnostico_imagen.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.diagnostico_imagen.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.escenario is 'Simulación "qué pasa si" (sube el concentrado 10 %, se pasa de 100 a 500 gallinas, cae la postura).';
comment on column ia.escenario.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.escenario.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.escenario.nombre is 'Nombre';
comment on column ia.escenario.supuestos is 'Variables y valores supuestos';
comment on column ia.escenario.resultado is 'Resultado (margen, caja, punto de equilibrio)';
comment on column ia.escenario.creado_por is 'Quién';
comment on column ia.escenario.agente_id is 'Agente que lo preparó';
comment on column ia.escenario.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.escenario.actualizado_en is 'Fecha y hora de la última modificación';
comment on table ia.decision is 'Registro de decisiones: contexto, opciones, evidencia, quién decidió y, después, el resultado. Memoria de la finca.';
comment on column ia.decision.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column ia.decision.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column ia.decision.titulo is 'Decisión';
comment on column ia.decision.contexto is 'Situación';
comment on column ia.decision.opciones is 'Opciones evaluadas';
comment on column ia.decision.evidencia is 'Cifras y documentos';
comment on column ia.decision.opcion_elegida is 'Lo que se decidió';
comment on column ia.decision.decidido_por is 'Quién decidió (persona)';
comment on column ia.decision.decidido_en is 'Cuándo';
comment on column ia.decision.resultado_esperado is 'Qué se espera';
comment on column ia.decision.revisar_en is 'Cuándo revisar el resultado';
comment on column ia.decision.resultado_real is 'Qué pasó';
comment on column ia.decision.recomendacion_id is 'Recomendación que la originó';
comment on column ia.decision.escenario_id is 'Escenario usado';
comment on column ia.decision.iniciativa_id is 'Iniciativa de negocio decidida';
comment on column ia.decision.creado_en is 'Fecha y hora de creación del registro';
comment on column ia.decision.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.clasificacion_costo is 'Cómo se comporta cada cuenta de costo o gasto: elemento (MD, MOD, CIF, administración, ventas, financiero) y comportamiento (fijo, variable, semivariable, escalonado). Base del costeo variable y de las palancas.';
comment on column finanzas.clasificacion_costo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.clasificacion_costo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.clasificacion_costo.cuenta_id is 'Cuenta';
comment on column finanzas.clasificacion_costo.elemento is 'Elemento del costo (valores: material_directo, mano_obra_directa, cif, gasto_administracion, gasto_ventas, gasto_financiero, otro)';
comment on column finanzas.clasificacion_costo.comportamiento is 'Comportamiento frente al volumen (valores: fijo, variable, semivariable, escalonado)';
comment on column finanzas.clasificacion_costo.parte_fija_pct is 'Porcentaje fijo de un costo semivariable';
comment on column finanzas.clasificacion_costo.controlable is 'Lo controla el responsable del centro';
comment on column finanzas.clasificacion_costo.es_costo_producto is 'Costo del producto (va al inventario) o costo del periodo';
comment on column finanzas.clasificacion_costo.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.clasificacion_costo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.actividad_costo is 'Actividad para costeo basado en actividades (ABC) con su inductor: horas de máquina, aves-día, jornales, m² regados.';
comment on column finanzas.actividad_costo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.actividad_costo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.actividad_costo.codigo is 'Código, ej. ALIMENTAR_AVES';
comment on column finanzas.actividad_costo.nombre is 'Actividad';
comment on column finanzas.actividad_costo.inductor is 'Inductor de costo, ej. aves_dia, horas_maquina, jornales';
comment on column finanzas.actividad_costo.centro_costo_id is 'Centro de servicio que la presta';
comment on column finanzas.actividad_costo.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.actividad_costo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.asignacion_costo is 'Reparto mensual de costos indirectos a los centros según el inductor consumido.';
comment on column finanzas.asignacion_costo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.asignacion_costo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.asignacion_costo.mes is 'Mes';
comment on column finanzas.asignacion_costo.actividad_id is 'Actividad';
comment on column finanzas.asignacion_costo.centro_costo_id is 'Centro que la consume';
comment on column finanzas.asignacion_costo.cantidad_inductor is 'Cantidad del inductor consumida';
comment on column finanzas.asignacion_costo.valor_asignado is 'Valor asignado (lo calcula la regla)';
comment on column finanzas.asignacion_costo.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.asignacion_costo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.costo_estandar is 'Costo estándar por unidad de producto (materiales, mano de obra y CIF) para comparar contra el real.';
comment on column finanzas.costo_estandar.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.costo_estandar.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.costo_estandar.producto_id is 'Producto';
comment on column finanzas.costo_estandar.vigente_desde is 'Desde';
comment on column finanzas.costo_estandar.material_directo is 'MD por unidad';
comment on column finanzas.costo_estandar.mano_obra_directa is 'MOD por unidad';
comment on column finanzas.costo_estandar.cif is 'CIF por unidad';
comment on column finanzas.costo_estandar.costo_variable_unitario is 'Parte variable del costo unitario';
comment on column finanzas.costo_estandar.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.costo_estandar.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.presupuesto is 'Presupuesto maestro del año (operación y financiero), con versión y aprobación; puede ser base cero. Base para el informe al Fondo Emprender.';
comment on column finanzas.presupuesto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.presupuesto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.presupuesto.nombre is 'Nombre';
comment on column finanzas.presupuesto.anio is 'Año';
comment on column finanzas.presupuesto.version is 'Versión';
comment on column finanzas.presupuesto.base_cero is 'Cada rubro se justifica desde cero';
comment on column finanzas.presupuesto.fuente is 'Fuente de los recursos (valores: propio, fondo_emprender, credito, mixto)';
comment on column finanzas.presupuesto.estado is 'Estado (valores: borrador, aprobado, cerrado)';
comment on column finanzas.presupuesto.aprobado_por is 'Quién lo aprobó';
comment on column finanzas.presupuesto.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.presupuesto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.premisa_presupuesto is 'Premisas del presupuesto: inflación, salario mínimo, precio del concentrado, crecimiento del mercado, política de cartera.';
comment on column finanzas.premisa_presupuesto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.premisa_presupuesto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.premisa_presupuesto.presupuesto_id is 'Presupuesto';
comment on column finanzas.premisa_presupuesto.tipo is 'Tipo de premisa (valores: macroeconomica, microeconomica)';
comment on column finanzas.premisa_presupuesto.variable is 'Variable, ej. inflacion, precio_concentrado, pct_ventas_contado';
comment on column finanzas.premisa_presupuesto.valor is 'Valor';
comment on column finanzas.premisa_presupuesto.fuente is 'Fuente (DANE, Banco de la República, cotización)';
comment on column finanzas.premisa_presupuesto.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.premisa_presupuesto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.presupuesto_detalle is 'Rubro del presupuesto por mes, centro de costo y cuenta, en la secuencia del presupuesto maestro (ventas, producción, materias primas, mano de obra, CIF, gastos, inversión, financiación, caja).';
comment on column finanzas.presupuesto_detalle.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.presupuesto_detalle.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.presupuesto_detalle.presupuesto_id is 'Presupuesto';
comment on column finanzas.presupuesto_detalle.componente is 'Componente del presupuesto maestro (valores: ventas, produccion, materia_prima, mano_obra, cif, gastos_operacion, inversion, financiacion, flujo_caja)';
comment on column finanzas.presupuesto_detalle.mes is 'Mes (1 a 12)';
comment on column finanzas.presupuesto_detalle.centro_costo_id is 'Centro de costo';
comment on column finanzas.presupuesto_detalle.cuenta_id is 'Cuenta';
comment on column finanzas.presupuesto_detalle.producto_id is 'Producto (ventas y producción)';
comment on column finanzas.presupuesto_detalle.cantidad is 'Unidades';
comment on column finanzas.presupuesto_detalle.valor is 'Valor';
comment on column finanzas.presupuesto_detalle.justificacion is 'Justificación (obligatoria en base cero)';
comment on column finanzas.presupuesto_detalle.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.presupuesto_detalle.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.estado_financiero is 'Estado financiero generado y congelado (balance, resultados por costeo variable o absorbente, flujo de efectivo directo o indirecto), real o presupuestado.';
comment on column finanzas.estado_financiero.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.estado_financiero.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.estado_financiero.tipo is 'Estado (valores: balance_general, resultados_absorbente, resultados_variable, flujo_efectivo_directo, flujo_efectivo_indirecto, cambios_patrimonio)';
comment on column finanzas.estado_financiero.desde is 'Desde';
comment on column finanzas.estado_financiero.hasta is 'Hasta';
comment on column finanzas.estado_financiero.presupuestado is 'Es proforma (del presupuesto)';
comment on column finanzas.estado_financiero.datos is 'Partidas y totales';
comment on column finanzas.estado_financiero.generado_por is 'Quién lo generó';
comment on column finanzas.estado_financiero.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.estado_financiero.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.indicador is 'Catálogo de indicadores financieros y de gestión con su fórmula, meta y semáforo (liquidez, endeudamiento, rentabilidad, rotación, EBITDA, EVA, Altman, palancas, postura por ave…).';
comment on column finanzas.indicador.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.indicador.codigo is 'Código, ej. razon_corriente, rsp, gpo';
comment on column finanzas.indicador.nombre is 'Nombre';
comment on column finanzas.indicador.grupo is 'Grupo (valores: liquidez, endeudamiento, rentabilidad, actividad, valor, riesgo, palanca, produccion, comercial, personal, proyecto)';
comment on column finanzas.indicador.formula is 'Fórmula';
comment on column finanzas.indicador.interpretacion is 'Cómo leerlo';
comment on column finanzas.indicador.unidad is 'Unidad (valores: veces, porcentaje, pesos, dias, unidades)';
comment on column finanzas.indicador.sentido is 'Qué es mejor (valores: mayor_mejor, menor_mejor, rango)';
comment on column finanzas.indicador.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.indicador.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.valor_indicador is 'Valor calculado de un indicador en un periodo, con meta y semáforo para el tablero del administrador.';
comment on column finanzas.valor_indicador.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.valor_indicador.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.valor_indicador.indicador_id is 'Indicador';
comment on column finanzas.valor_indicador.desde is 'Desde';
comment on column finanzas.valor_indicador.hasta is 'Hasta';
comment on column finanzas.valor_indicador.centro_costo_id is 'Línea, si es por línea';
comment on column finanzas.valor_indicador.valor is 'Valor';
comment on column finanzas.valor_indicador.meta is 'Meta';
comment on column finanzas.valor_indicador.semaforo is 'Semáforo (sin_meta: hay valor pero no hay meta fijada) (valores: verde, amarillo, rojo, sin_meta, sin_dato)';
comment on column finanzas.valor_indicador.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.valor_indicador.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.anticipo_proveedor is 'Pago adelantado a un proveedor: queda como saldo a favor y se descuenta en las compras siguientes; nunca queda negativo. No se reciben recargas de clientes.';
comment on column finanzas.anticipo_proveedor.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.anticipo_proveedor.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.anticipo_proveedor.proveedor_id is 'Proveedor';
comment on column finanzas.anticipo_proveedor.fecha is 'Fecha';
comment on column finanzas.anticipo_proveedor.valor is 'Valor';
comment on column finanzas.anticipo_proveedor.saldo is 'Saldo por descontar';
comment on column finanzas.anticipo_proveedor.comprobante_id is 'Comprobante';
comment on column finanzas.anticipo_proveedor.estado is 'Estado (valores: abierto, aplicado, devuelto)';
comment on column finanzas.anticipo_proveedor.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.anticipo_proveedor.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.aplicacion_anticipo is 'Descuento de un anticipo en una orden de compra.';
comment on column finanzas.aplicacion_anticipo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.aplicacion_anticipo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.aplicacion_anticipo.anticipo_id is 'Anticipo';
comment on column finanzas.aplicacion_anticipo.orden_compra_id is 'Compra';
comment on column finanzas.aplicacion_anticipo.valor is 'Valor descontado';
comment on column finanzas.aplicacion_anticipo.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.aplicacion_anticipo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table finanzas.reporte_indicadores is 'Informe de indicadores verificables para Finagro, bancos, gremios o certificadores, con autorización del titular y sin costos ni datos personales.';
comment on column finanzas.reporte_indicadores.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column finanzas.reporte_indicadores.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column finanzas.reporte_indicadores.destinatario is 'A quién va (valores: finagro, banco, gremio, certificador, fondo_emprender, otro)';
comment on column finanzas.reporte_indicadores.tercero_id is 'Entidad';
comment on column finanzas.reporte_indicadores.desde is 'Desde';
comment on column finanzas.reporte_indicadores.hasta is 'Hasta';
comment on column finanzas.reporte_indicadores.contenido is 'Indicadores (producción, ventas, cumplimiento)';
comment on column finanzas.reporte_indicadores.hash_sha256 is 'Huella del contenido (verificable)';
comment on column finanzas.reporte_indicadores.autorizado_por is 'Titular que autorizó compartirlo';
comment on column finanzas.reporte_indicadores.enviado_en is 'Envío';
comment on column finanzas.reporte_indicadores.creado_en is 'Fecha y hora de creación del registro';
comment on column finanzas.reporte_indicadores.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.mision_robot is 'Misión de un dron de monitoreo o de un robot de campo en piloto: una persona la aprueba; el robot opera solo en zonas sin personas y con parada de emergencia probada.';
comment on column iot.mision_robot.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.mision_robot.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.mision_robot.activo_id is 'Dron o robot';
comment on column iot.mision_robot.tipo is 'Tipo (valores: dron_monitoreo, robot_deshierbe, robot_monitoreo)';
comment on column iot.mision_robot.zona_id is 'Zona';
comment on column iot.mision_robot.estado is 'Estado (valores: propuesta, aprobada, en_curso, terminada, abortada)';
comment on column iot.mision_robot.aprobada_por is 'Quién la aprobó';
comment on column iot.mision_robot.piloto_id is 'Piloto certificado (dron)';
comment on column iot.mision_robot.poliza_id is 'Póliza de responsabilidad civil (dron)';
comment on column iot.mision_robot.altura_max_m is 'Altura máxima (RAC 100: hasta 122 m)';
comment on column iot.mision_robot.zona_sin_personas is 'Se confirmó que no hay personas en la zona';
comment on column iot.mision_robot.parada_emergencia_probada is 'Se probó la parada de emergencia';
comment on column iot.mision_robot.inicio is 'Inicio';
comment on column iot.mision_robot.fin is 'Fin';
comment on column iot.mision_robot.resultado is 'Fotos, conteos y lecturas devueltas';
comment on column iot.mision_robot.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.mision_robot.actualizado_en is 'Fecha y hora de la última modificación';
comment on table iot.prioridad_carga is 'Prioridad de cada carga eléctrica: con batería baja se cortan primero las no esenciales; alarma, nevera y agua de animales van primero.';
comment on column iot.prioridad_carga.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column iot.prioridad_carga.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column iot.prioridad_carga.actuador_id is 'Carga (relé)';
comment on column iot.prioridad_carga.prioridad is '1 = crítica … 5 = prescindible';
comment on column iot.prioridad_carga.esencial is 'Nunca se corta automáticamente';
comment on column iot.prioridad_carga.corte_bateria_pct is 'Porcentaje de batería bajo el cual se corta';
comment on column iot.prioridad_carga.creado_en is 'Fecha y hora de creación del registro';
comment on column iot.prioridad_carga.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.llave_api is 'Llave de un cliente B2B (HORECA) para la API: guarda solo su huella, con alcances, límite de peticiones y vencimiento. Se enciende con api_b2b.';
comment on column nucleo.llave_api.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.llave_api.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.llave_api.tercero_id is 'Cliente dueño de la llave';
comment on column nucleo.llave_api.nombre is 'Nombre';
comment on column nucleo.llave_api.prefijo is 'Prefijo visible para identificarla';
comment on column nucleo.llave_api.hash_llave is 'Huella SHA-256 de la llave (la llave nunca se guarda)';
comment on column nucleo.llave_api.alcances is 'Permisos: catalogo:leer, pedidos:leer, pedidos:crear';
comment on column nucleo.llave_api.limite_por_minuto is 'Límite de peticiones';
comment on column nucleo.llave_api.activa is 'Encendida';
comment on column nucleo.llave_api.vence_en is 'Vencimiento';
comment on column nucleo.llave_api.ultimo_uso is 'Último uso';
comment on column nucleo.llave_api.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.llave_api.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.webhook_suscripcion is 'Sistema externo (comprador, logística) que recibe eventos firmados del outbox: pedido confirmado, lote despachado, factura emitida.';
comment on column nucleo.webhook_suscripcion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.webhook_suscripcion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.webhook_suscripcion.nombre is 'Nombre';
comment on column nucleo.webhook_suscripcion.tercero_id is 'Dueño';
comment on column nucleo.webhook_suscripcion.url is 'URL https de destino';
comment on column nucleo.webhook_suscripcion.eventos is 'Tipos de evento';
comment on column nucleo.webhook_suscripcion.secreto_ref is 'Nombre del secreto para firmar (HMAC); nunca el secreto';
comment on column nucleo.webhook_suscripcion.activa is 'Encendida';
comment on column nucleo.webhook_suscripcion.fallos_seguidos is 'Fallos seguidos (al llegar a 10 se apaga)';
comment on column nucleo.webhook_suscripcion.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.webhook_suscripcion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table nucleo.webhook_entrega is 'Intento de entrega de un evento a un webhook, con reintentos.';
comment on column nucleo.webhook_entrega.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column nucleo.webhook_entrega.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column nucleo.webhook_entrega.suscripcion_id is 'Suscripción';
comment on column nucleo.webhook_entrega.evento_salida_id is 'Evento del outbox';
comment on column nucleo.webhook_entrega.estado is 'Estado (valores: pendiente, entregado, fallido)';
comment on column nucleo.webhook_entrega.intentos is 'Intentos';
comment on column nucleo.webhook_entrega.codigo_respuesta is 'Código HTTP';
comment on column nucleo.webhook_entrega.proximo_intento is 'Próximo intento';
comment on column nucleo.webhook_entrega.creado_en is 'Fecha y hora de creación del registro';
comment on column nucleo.webhook_entrega.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.factor_autenticacion is 'Segundo factor del usuario: app TOTP o llave de acceso (passkey/WebAuthn). Obligatorio para administrador y contador. El secreto vive en el gestor de secretos.';
comment on column seguridad.factor_autenticacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.factor_autenticacion.usuario_id is 'Usuario';
comment on column seguridad.factor_autenticacion.tipo is 'Tipo (sin biometría guardada en el servidor) (valores: totp, webauthn, codigo_respaldo)';
comment on column seguridad.factor_autenticacion.nombre is 'Nombre del dispositivo';
comment on column seguridad.factor_autenticacion.secreto_ref is 'Referencia al secreto o a la llave pública';
comment on column seguridad.factor_autenticacion.activo is 'En uso';
comment on column seguridad.factor_autenticacion.ultimo_uso is 'Último uso';
comment on column seguridad.factor_autenticacion.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.factor_autenticacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.sesion_usuario is 'Sesión iniciada: método, IP, dispositivo y vencimiento; se puede revocar en bloque ante un incidente.';
comment on column seguridad.sesion_usuario.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.sesion_usuario.usuario_id is 'Usuario';
comment on column seguridad.sesion_usuario.metodo is 'Cómo se autenticó (valores: contrasena, doble_factor, llave_acceso, token_dispositivo)';
comment on column seguridad.sesion_usuario.ip is 'IP';
comment on column seguridad.sesion_usuario.agente_usuario is 'Navegador o app';
comment on column seguridad.sesion_usuario.dispositivo_captura_id is 'Celular de campo registrado';
comment on column seguridad.sesion_usuario.iniciada_en is 'Inicio';
comment on column seguridad.sesion_usuario.vence_en is 'Vencimiento';
comment on column seguridad.sesion_usuario.revocada_en is 'Revocación';
comment on column seguridad.sesion_usuario.motivo_revocacion is 'Motivo';
comment on column seguridad.sesion_usuario.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.sesion_usuario.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.intento_acceso is 'Cada intento de inicio de sesión, exitoso o no (solo inserción). Alimenta el detector de ataques.';
comment on column seguridad.intento_acceso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.intento_acceso.correo is 'Correo intentado';
comment on column seguridad.intento_acceso.usuario_id is 'Usuario, si existe';
comment on column seguridad.intento_acceso.ip is 'IP';
comment on column seguridad.intento_acceso.exito is 'Entró';
comment on column seguridad.intento_acceso.motivo_fallo is 'Motivo del fallo (valores: contrasena, usuario_inexistente, cuenta_bloqueada, ip_bloqueada, segundo_factor, cuenta_inactiva, senuelo)';
comment on column seguridad.intento_acceso.agente_usuario is 'Navegador o app';
comment on column seguridad.intento_acceso.ocurrido_en is 'Momento';
comment on table seguridad.regla_deteccion is 'Regla del detector de ataques: cuántos hechos en cuánto tiempo, severidad y respuesta automática.';
comment on column seguridad.regla_deteccion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.regla_deteccion.codigo is 'Código, ej. fuerza_bruta_cuenta';
comment on column seguridad.regla_deteccion.descripcion is 'Qué detecta';
comment on column seguridad.regla_deteccion.umbral is 'Número de hechos';
comment on column seguridad.regla_deteccion.ventana_min is 'Minutos';
comment on column seguridad.regla_deteccion.severidad is 'Severidad (valores: baja, media, alta, critica)';
comment on column seguridad.regla_deteccion.respuesta is 'Qué hace sola (valores: alertar, bloquear_ip, bloquear_cuenta, revocar_sesiones)';
comment on column seguridad.regla_deteccion.bloqueo_min is 'Minutos de bloqueo';
comment on column seguridad.regla_deteccion.activa is 'Encendida';
comment on column seguridad.regla_deteccion.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.regla_deteccion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.bloqueo is 'Bloqueo temporal de una cuenta o una IP por una regla o una persona.';
comment on column seguridad.bloqueo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.bloqueo.tipo is 'Qué se bloquea (valores: cuenta, ip)';
comment on column seguridad.bloqueo.usuario_id is 'Cuenta';
comment on column seguridad.bloqueo.ip is 'IP o red';
comment on column seguridad.bloqueo.regla_id is 'Regla que lo puso';
comment on column seguridad.bloqueo.motivo is 'Motivo';
comment on column seguridad.bloqueo.desde is 'Desde';
comment on column seguridad.bloqueo.hasta is 'Hasta; vacío = indefinido';
comment on column seguridad.bloqueo.levantado_por is 'Quién lo levantó';
comment on column seguridad.bloqueo.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.bloqueo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.senuelo is 'Señuelo para intrusos (cuenta, llave de API o URL que nadie legítimo usa): tocarlo dispara una alerta crítica y bloquea la IP.';
comment on column seguridad.senuelo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.senuelo.tipo is 'Tipo (valores: cuenta, llave_api, url, registro)';
comment on column seguridad.senuelo.valor is 'Correo, prefijo o ruta del señuelo';
comment on column seguridad.senuelo.descripcion is 'Para qué está';
comment on column seguridad.senuelo.activo is 'Encendido';
comment on column seguridad.senuelo.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.senuelo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.alerta_seguridad is 'Hecho sospechoso detectado por las reglas, el WAF, la pasarela o la base (fuerza bruta, escalada de permisos, exportación masiva, señuelo). Solo inserción salvo su atención.';
comment on column seguridad.alerta_seguridad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.alerta_seguridad.tipo is 'Qué pasó (valores: fuerza_bruta, relleno_credenciales, senuelo, escalada_privilegios, cambio_permisos, exportacion_masiva, acceso_ip_nueva, sesion_sin_doble_factor, inyeccion, abuso_api, dispositivo_desconocido, firmware_no_firmado, copia_fallida, otro)';
comment on column seguridad.alerta_seguridad.severidad is 'Severidad (valores: baja, media, alta, critica)';
comment on column seguridad.alerta_seguridad.fuente is 'Quién lo detectó (valores: app, base_datos, waf, api, pasarela, agente_ia, monitoreo)';
comment on column seguridad.alerta_seguridad.regla_id is 'Regla';
comment on column seguridad.alerta_seguridad.usuario_id is 'Usuario implicado';
comment on column seguridad.alerta_seguridad.ip is 'IP';
comment on column seguridad.alerta_seguridad.predio_id is 'Finca afectada, si aplica';
comment on column seguridad.alerta_seguridad.detalle is 'Datos del hecho';
comment on column seguridad.alerta_seguridad.ocurrido_en is 'Momento';
comment on column seguridad.alerta_seguridad.estado is 'Atención (valores: nueva, en_analisis, contenida, falso_positivo, cerrada)';
comment on column seguridad.alerta_seguridad.atendida_por is 'Quién la atendió';
comment on column seguridad.alerta_seguridad.incidente_id is 'Incidente al que pertenece';
comment on column seguridad.alerta_seguridad.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.alerta_seguridad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.incidente is 'Incidente de seguridad con su atención; si compromete datos personales se reporta a la SIC (Ley 1581).';
comment on column seguridad.incidente.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.incidente.titulo is 'Título';
comment on column seguridad.incidente.severidad is 'Severidad (valores: baja, media, alta, critica)';
comment on column seguridad.incidente.estado is 'Estado (valores: abierto, contenido, erradicado, cerrado)';
comment on column seguridad.incidente.responsable_id is 'Responsable';
comment on column seguridad.incidente.datos_personales_afectados is 'Hubo datos personales comprometidos';
comment on column seguridad.incidente.reportado_sic_en is 'Reporte a la Superintendencia de Industria y Comercio';
comment on column seguridad.incidente.abierto_en is 'Apertura';
comment on column seguridad.incidente.cerrado_en is 'Cierre';
comment on column seguridad.incidente.lecciones is 'Lecciones aprendidas';
comment on column seguridad.incidente.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.incidente.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.ejecucion_prueba is 'Módulo de pruebas: cada corrida de pruebas (unitarias, de reglas de la base, extremo a extremo, carga, dependencias, SAST, DAST, pentest, restauración de copias) con su resultado.';
comment on column seguridad.ejecucion_prueba.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.ejecucion_prueba.tipo is 'Tipo de prueba (valores: unitaria, integracion, reglas_bd, extremo_a_extremo, carga, dependencias, sast, dast, pentest, restauracion_copia, simulacro_incidente)';
comment on column seguridad.ejecucion_prueba.suite is 'Suite, ej. pruebas_reglas_v5';
comment on column seguridad.ejecucion_prueba.version_sistema is 'Versión probada';
comment on column seguridad.ejecucion_prueba.entorno is 'Dónde corrió (nunca pentest en producción sin aprobación) (valores: desarrollo, pruebas, practica, produccion)';
comment on column seguridad.ejecucion_prueba.total is 'Casos';
comment on column seguridad.ejecucion_prueba.aprobadas is 'Aprobados';
comment on column seguridad.ejecucion_prueba.fallidas is 'Fallidos';
comment on column seguridad.ejecucion_prueba.hallazgos_criticos is 'Hallazgos críticos (seguridad)';
comment on column seguridad.ejecucion_prueba.herramienta is 'Herramienta, ej. pytest, pgTAP, OWASP ZAP, pip-audit';
comment on column seguridad.ejecucion_prueba.informe_url is 'Informe';
comment on column seguridad.ejecucion_prueba.ejecutada_en is 'Cuándo';
comment on column seguridad.ejecucion_prueba.ejecutada_por is 'Quién';
comment on column seguridad.ejecucion_prueba.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.ejecucion_prueba.actualizado_en is 'Fecha y hora de la última modificación';
comment on table seguridad.copia_seguridad is 'Copia cifrada de la base o los archivos (regla 3-2-1) y su prueba mensual de restauración.';
comment on column seguridad.copia_seguridad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column seguridad.copia_seguridad.alcance is 'Qué se copió (valores: postgresql, mongodb, archivos, configuracion)';
comment on column seguridad.copia_seguridad.destino is 'Dónde (valores: local, nube, disco_externo)';
comment on column seguridad.copia_seguridad.inicio is 'Inicio';
comment on column seguridad.copia_seguridad.fin is 'Fin';
comment on column seguridad.copia_seguridad.tamano_mb is 'Tamaño';
comment on column seguridad.copia_seguridad.hash_sha256 is 'Huella';
comment on column seguridad.copia_seguridad.cifrada is 'Cifrada';
comment on column seguridad.copia_seguridad.exitosa is 'Terminó bien';
comment on column seguridad.copia_seguridad.restauracion_probada_en is 'Última prueba de restauración';
comment on column seguridad.copia_seguridad.creado_en is 'Fecha y hora de creación del registro';
comment on column seguridad.copia_seguridad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table crm.segmento is 'Segmento de mercado (hogares, tiendas, restaurantes, hoteles, colegios, exportadores) con sus criterios: base de la palanca de mercadeo.';
comment on column crm.segmento.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column crm.segmento.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column crm.segmento.codigo is 'Código';
comment on column crm.segmento.nombre is 'Nombre';
comment on column crm.segmento.criterios is 'Criterios (municipio, tipo de negocio, volumen)';
comment on column crm.segmento.propuesta_valor is 'Qué se le ofrece y por qué paga más';
comment on column crm.segmento.creado_en is 'Fecha y hora de creación del registro';
comment on column crm.segmento.actualizado_en is 'Fecha y hora de la última modificación';
comment on table crm.campana is 'Campaña para captar clientes: canal, segmento, presupuesto, costo real y conversiones (costo por cliente nuevo).';
comment on column crm.campana.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column crm.campana.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column crm.campana.nombre is 'Nombre';
comment on column crm.campana.canal is 'Canal (valores: whatsapp, instagram, facebook, tiktok, feria, mercado_campesino, visita_finca, referidos, web, volanteo, otro)';
comment on column crm.campana.segmento_id is 'Segmento';
comment on column crm.campana.objetivo is 'Objetivo';
comment on column crm.campana.desde is 'Inicio';
comment on column crm.campana.hasta is 'Fin';
comment on column crm.campana.presupuesto is 'Presupuesto';
comment on column crm.campana.costo_real is 'Costo real';
comment on column crm.campana.publicacion_id is 'Publicación de redes asociada';
comment on column crm.campana.creado_en is 'Fecha y hora de creación del registro';
comment on column crm.campana.actualizado_en is 'Fecha y hora de la última modificación';
comment on table crm.formulario_captura is 'Formulario para registrar posibles clientes (web, QR en ferias, WhatsApp) con su texto de autorización de datos y finalidad.';
comment on column crm.formulario_captura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column crm.formulario_captura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column crm.formulario_captura.codigo is 'Código';
comment on column crm.formulario_captura.nombre is 'Nombre';
comment on column crm.formulario_captura.canal is 'Dónde se usa (valores: web, qr_feria, whatsapp, tablet_finca, otro)';
comment on column crm.formulario_captura.campos is 'Campos que pide (mínimos necesarios)';
comment on column crm.formulario_captura.texto_autorizacion is 'Texto de autorización de tratamiento de datos (Ley 1581)';
comment on column crm.formulario_captura.finalidad is 'Para qué se usarán los datos';
comment on column crm.formulario_captura.campana_id is 'Campaña';
comment on column crm.formulario_captura.activo is 'Publicado';
comment on column crm.formulario_captura.creado_en is 'Fecha y hora de creación del registro';
comment on column crm.formulario_captura.actualizado_en is 'Fecha y hora de la última modificación';
comment on table crm.prospecto is 'Posible cliente, persona o empresa. No se le escribe sin autorización; al comprar se convierte en tercero y cliente.';
comment on column crm.prospecto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column crm.prospecto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column crm.prospecto.tipo is 'Tipo (valores: persona, empresa)';
comment on column crm.prospecto.nombre is 'Nombre o razón social';
comment on column crm.prospecto.nit is 'NIT de la empresa (las personas no necesitan documento para ser prospecto)';
comment on column crm.prospecto.sector is 'Sector (valores: hogar, tienda, restaurante, hotel, colegio, casino, supermercado, distribuidor, exportador, agencia_turismo, institucion, otro)';
comment on column crm.prospecto.municipio is 'Municipio';
comment on column crm.prospecto.telefono is 'Celular';
comment on column crm.prospecto.correo is 'Correo';
comment on column crm.prospecto.canal_origen is 'Cómo llegó (valores: whatsapp, instagram, facebook, tiktok, feria, mercado_campesino, visita_finca, referido, web, llamada, base_publica, otro)';
comment on column crm.prospecto.formulario_id is 'Formulario por el que se registró';
comment on column crm.prospecto.campana_id is 'Campaña';
comment on column crm.prospecto.segmento_id is 'Segmento';
comment on column crm.prospecto.intereses is 'Productos o servicios de interés';
comment on column crm.prospecto.volumen_estimado_mes is 'Compra mensual estimada';
comment on column crm.prospecto.etapa is 'Etapa del embudo (valores: nuevo, contactado, calificado, propuesta, negociacion, ganado, perdido, descartado)';
comment on column crm.prospecto.puntaje is 'Puntaje de calificación (0 a 100)';
comment on column crm.prospecto.responsable_id is 'Vendedor responsable';
comment on column crm.prospecto.consentimiento_id is 'Autorización de datos; sin ella solo se guarda la empresa (datos públicos), no se contacta';
comment on column crm.prospecto.tercero_id is 'Tercero al convertirse en cliente';
comment on column crm.prospecto.motivo_perdida is 'Por qué se perdió';
comment on column crm.prospecto.proximo_contacto is 'Próximo contacto';
comment on column crm.prospecto.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column crm.prospecto.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column crm.prospecto.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column crm.prospecto.creado_en is 'Fecha y hora de creación del registro';
comment on column crm.prospecto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table crm.contacto_empresa is 'Persona de contacto dentro de una empresa prospecto (compras, chef, administrador), con su propia autorización.';
comment on column crm.contacto_empresa.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column crm.contacto_empresa.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column crm.contacto_empresa.prospecto_id is 'Empresa';
comment on column crm.contacto_empresa.nombre is 'Nombre';
comment on column crm.contacto_empresa.cargo is 'Cargo';
comment on column crm.contacto_empresa.telefono is 'Celular';
comment on column crm.contacto_empresa.correo is 'Correo';
comment on column crm.contacto_empresa.consentimiento_id is 'Autorización';
comment on column crm.contacto_empresa.creado_en is 'Fecha y hora de creación del registro';
comment on column crm.contacto_empresa.actualizado_en is 'Fecha y hora de la última modificación';
comment on table crm.interaccion is 'Contacto con un prospecto o cliente (llamada, WhatsApp, visita, degustación, feria) y su próximo paso.';
comment on column crm.interaccion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column crm.interaccion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column crm.interaccion.prospecto_id is 'Prospecto';
comment on column crm.interaccion.tercero_id is 'Cliente existente';
comment on column crm.interaccion.tipo is 'Tipo (valores: llamada, whatsapp, visita, correo, reunion, degustacion, feria, visita_finca)';
comment on column crm.interaccion.fecha is 'Cuándo';
comment on column crm.interaccion.resumen is 'Qué se habló';
comment on column crm.interaccion.proximo_paso is 'Próximo paso';
comment on column crm.interaccion.usuario_id is 'Quién';
comment on column crm.interaccion.agente_id is 'Agente, si la atendió uno';
comment on column crm.interaccion.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column crm.interaccion.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column crm.interaccion.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column crm.interaccion.creado_en is 'Fecha y hora de creación del registro';
comment on column crm.interaccion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table crm.oportunidad is 'Negocio posible con un prospecto o cliente: productos, valor, probabilidad y fecha de cierre (proyección del embudo).';
comment on column crm.oportunidad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column crm.oportunidad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column crm.oportunidad.prospecto_id is 'Prospecto';
comment on column crm.oportunidad.tercero_id is 'Cliente';
comment on column crm.oportunidad.titulo is 'Título';
comment on column crm.oportunidad.productos is 'Productos y cantidades';
comment on column crm.oportunidad.valor_estimado is 'Valor estimado';
comment on column crm.oportunidad.probabilidad_pct is 'Probabilidad de cierre';
comment on column crm.oportunidad.cierre_estimado is 'Fecha estimada';
comment on column crm.oportunidad.estado is 'Estado (valores: abierta, ganada, perdida)';
comment on column crm.oportunidad.pedido_id is 'Pedido que la cerró';
comment on column crm.oportunidad.linea_negocio_id is 'Línea de negocio';
comment on column crm.oportunidad.creado_en is 'Fecha y hora de creación del registro';
comment on column crm.oportunidad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.linea_negocio is 'Línea de negocio de la finca (avícola, piscícola, perennes, turismo…) o una nueva en estudio, unida a su centro de costo.';
comment on column estrategia.linea_negocio.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.linea_negocio.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.linea_negocio.codigo is 'Código';
comment on column estrategia.linea_negocio.nombre is 'Nombre';
comment on column estrategia.linea_negocio.centro_costo_id is 'Centro de costo';
comment on column estrategia.linea_negocio.estado is 'Estado (valores: actual, en_estudio, piloto, descartada, cerrada)';
comment on column estrategia.linea_negocio.palanca_dominante is 'Palanca con la que genera recursos (valores: mercadeo, produccion, operacional, financiera)';
comment on column estrategia.linea_negocio.descripcion is 'Descripción';
comment on column estrategia.linea_negocio.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.linea_negocio.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.factor_dofa is 'Debilidad, oportunidad, fortaleza o amenaza de la finca o de una línea, con su fuente.';
comment on column estrategia.factor_dofa.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.factor_dofa.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.factor_dofa.tipo is 'Tipo (valores: debilidad, oportunidad, fortaleza, amenaza)';
comment on column estrategia.factor_dofa.linea_negocio_id is 'Línea (vacío = toda la finca)';
comment on column estrategia.factor_dofa.descripcion is 'Descripción';
comment on column estrategia.factor_dofa.impacto is 'Impacto 1 a 5';
comment on column estrategia.factor_dofa.fuente is 'Fuente';
comment on column estrategia.factor_dofa.vigente is 'Vigente';
comment on column estrategia.factor_dofa.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.factor_dofa.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.estudio_mercado is 'Dato de un mercado posible: tamaño, precio de referencia, competidores y fuente (SIPSA, DANE, gremios, visitas).';
comment on column estrategia.estudio_mercado.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.estudio_mercado.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.estudio_mercado.mercado is 'Mercado, ej. huevo campesino en hoteles de Girardot';
comment on column estrategia.estudio_mercado.segmento_id is 'Segmento';
comment on column estrategia.estudio_mercado.tamano_estimado is 'Ventas anuales estimadas del mercado';
comment on column estrategia.estudio_mercado.precio_referencia is 'Precio de referencia';
comment on column estrategia.estudio_mercado.competidores is 'Competidores';
comment on column estrategia.estudio_mercado.barreras is 'Barreras de entrada (registros, certificaciones, frío)';
comment on column estrategia.estudio_mercado.fuente is 'Fuente';
comment on column estrategia.estudio_mercado.fecha is 'Fecha del dato';
comment on column estrategia.estudio_mercado.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.estudio_mercado.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.iniciativa is 'Idea de crecimiento: nuevo mercado, producto, canal o negocio, clasificada por la matriz de Ansoff y por la palanca que usa. La IA puede proponerla; decide la familia.';
comment on column estrategia.iniciativa.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.iniciativa.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.iniciativa.titulo is 'Título';
comment on column estrategia.iniciativa.descripcion is 'Descripción';
comment on column estrategia.iniciativa.ansoff is 'Cuadrante de la matriz de Ansoff (valores: penetracion_mercado, desarrollo_mercado, desarrollo_producto, diversificacion)';
comment on column estrategia.iniciativa.tipo is 'Tipo (valores: nuevo_mercado, nuevo_producto, nuevo_canal, nueva_linea, valor_agregado, integracion_vertical, mejora_proceso)';
comment on column estrategia.iniciativa.palanca is 'Palanca principal (valores: mercadeo, produccion, operacional, financiera)';
comment on column estrategia.iniciativa.linea_negocio_id is 'Línea existente o nueva';
comment on column estrategia.iniciativa.segmento_id is 'Segmento al que apunta';
comment on column estrategia.iniciativa.hipotesis is 'Qué se cree y cómo se probará';
comment on column estrategia.iniciativa.estado is 'Estado (valores: idea, en_evaluacion, aprobada, piloto, escalada, descartada)';
comment on column estrategia.iniciativa.propuesta_por is 'Quién la propuso';
comment on column estrategia.iniciativa.agente_id is 'Agente que la propuso';
comment on column estrategia.iniciativa.aprobada_por is 'Quién la aprobó (persona)';
comment on column estrategia.iniciativa.aprobada_en is 'Cuándo';
comment on column estrategia.iniciativa.puntaje is 'Puntaje de priorización';
comment on column estrategia.iniciativa.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.iniciativa.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.evaluacion_proyecto is 'Evaluación financiera de una iniciativa: inversión, flujos, VPN, TIR, ROI, recuperación, punto de equilibrio, margen de seguridad y grados de palanca. La calcula la base.';
comment on column estrategia.evaluacion_proyecto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.evaluacion_proyecto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.evaluacion_proyecto.iniciativa_id is 'Iniciativa';
comment on column estrategia.evaluacion_proyecto.version is 'Versión';
comment on column estrategia.evaluacion_proyecto.inversion_inicial is 'Inversión inicial';
comment on column estrategia.evaluacion_proyecto.horizonte_meses is 'Horizonte';
comment on column estrategia.evaluacion_proyecto.tasa_descuento_anual is 'Costo de capital (tasa de oportunidad) anual';
comment on column estrategia.evaluacion_proyecto.precio_unitario is 'Precio de venta por unidad';
comment on column estrategia.evaluacion_proyecto.costo_variable_unitario is 'Costo variable por unidad';
comment on column estrategia.evaluacion_proyecto.costos_fijos_mes is 'Costos fijos operacionales del mes';
comment on column estrategia.evaluacion_proyecto.intereses_mes is 'Intereses del mes si se financia con deuda';
comment on column estrategia.evaluacion_proyecto.unidades_mes is 'Unidades esperadas por mes';
comment on column estrategia.evaluacion_proyecto.fuente_fondos is 'De dónde sale la plata (valores: utilidades_retenidas, credito, fondo_emprender, aporte_familia, mixto)';
comment on column estrategia.evaluacion_proyecto.vpn is 'Valor presente neto';
comment on column estrategia.evaluacion_proyecto.tir_anual is 'Tasa interna de retorno anual';
comment on column estrategia.evaluacion_proyecto.roi_pct is 'Retorno sobre la inversión en el horizonte';
comment on column estrategia.evaluacion_proyecto.recuperacion_meses is 'Meses para recuperar la inversión';
comment on column estrategia.evaluacion_proyecto.punto_equilibrio_unidades is 'Unidades por mes para no perder';
comment on column estrategia.evaluacion_proyecto.margen_seguridad_pct is 'Cuánto pueden caer las ventas sin pérdida';
comment on column estrategia.evaluacion_proyecto.gpo is 'Grado de palanca operativa';
comment on column estrategia.evaluacion_proyecto.gpf is 'Grado de palanca financiera';
comment on column estrategia.evaluacion_proyecto.gpt is 'Grado de palanca total';
comment on column estrategia.evaluacion_proyecto.riesgos is 'Riesgos (costos fijos, deuda, precio)';
comment on column estrategia.evaluacion_proyecto.calculado_en is 'Cuándo se calculó';
comment on column estrategia.evaluacion_proyecto.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.evaluacion_proyecto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.flujo_proyecto is 'Flujo de caja proyectado de una evaluación por mes (mes 0 = inversión).';
comment on column estrategia.flujo_proyecto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.flujo_proyecto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.flujo_proyecto.evaluacion_id is 'Evaluación';
comment on column estrategia.flujo_proyecto.mes is 'Mes (0 = inversión)';
comment on column estrategia.flujo_proyecto.ingresos is 'Ingresos';
comment on column estrategia.flujo_proyecto.egresos is 'Egresos';
comment on column estrategia.flujo_proyecto.inversion is 'Inversión';
comment on column estrategia.flujo_proyecto.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.flujo_proyecto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.reinversion is 'Parte de la utilidad de una línea que se destina a una iniciativa (apalancarse con lo ganado). Nunca de una línea con pérdida ni por encima del tope de reinversión.';
comment on column estrategia.reinversion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.reinversion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.reinversion.anio is 'Año de la utilidad';
comment on column estrategia.reinversion.mes is 'Mes de la utilidad';
comment on column estrategia.reinversion.linea_origen_id is 'Línea que generó la utilidad';
comment on column estrategia.reinversion.utilidad_linea is 'Utilidad neta de la línea en el mes (de la contabilidad)';
comment on column estrategia.reinversion.valor is 'Valor reinvertido';
comment on column estrategia.reinversion.iniciativa_id is 'Iniciativa destino';
comment on column estrategia.reinversion.estado is 'Estado (valores: propuesta, aprobada, ejecutada, cancelada)';
comment on column estrategia.reinversion.aprobada_por is 'Quién la aprobó';
comment on column estrategia.reinversion.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.reinversion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.seguimiento_iniciativa is 'Resultado real mes a mes de una iniciativa en piloto o escalada, contra lo proyectado: así se mide el retorno de verdad.';
comment on column estrategia.seguimiento_iniciativa.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.seguimiento_iniciativa.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.seguimiento_iniciativa.iniciativa_id is 'Iniciativa';
comment on column estrategia.seguimiento_iniciativa.mes is 'Mes';
comment on column estrategia.seguimiento_iniciativa.ingresos_reales is 'Ingresos';
comment on column estrategia.seguimiento_iniciativa.egresos_reales is 'Egresos';
comment on column estrategia.seguimiento_iniciativa.unidades_reales is 'Unidades';
comment on column estrategia.seguimiento_iniciativa.nota is 'Aprendizajes';
comment on column estrategia.seguimiento_iniciativa.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.seguimiento_iniciativa.actualizado_en is 'Fecha y hora de la última modificación';
comment on table estrategia.objetivo is 'Objetivo estratégico por perspectiva del cuadro de mando (financiera, clientes, procesos, aprendizaje), con indicador y meta.';
comment on column estrategia.objetivo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column estrategia.objetivo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column estrategia.objetivo.perspectiva is 'Perspectiva (valores: financiera, clientes, procesos, aprendizaje)';
comment on column estrategia.objetivo.descripcion is 'Objetivo';
comment on column estrategia.objetivo.indicador_id is 'Indicador';
comment on column estrategia.objetivo.meta is 'Meta';
comment on column estrategia.objetivo.fecha_meta is 'Para cuándo';
comment on column estrategia.objetivo.responsable_id is 'Responsable';
comment on column estrategia.objetivo.creado_en is 'Fecha y hora de creación del registro';
comment on column estrategia.objetivo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.area_responsabilidad is 'Área de responsabilidad (galpón, cultivos, turismo y cabañas, bodega y despachos, mantenimiento, vigilancia): agrupa zonas, personas y tareas, con un responsable.';
comment on column personal.area_responsabilidad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.area_responsabilidad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.area_responsabilidad.codigo is 'Código, ej. AR-GALPON';
comment on column personal.area_responsabilidad.nombre is 'Nombre';
comment on column personal.area_responsabilidad.descripcion is 'Qué cubre';
comment on column personal.area_responsabilidad.zonas is 'Zonas que abarca';
comment on column personal.area_responsabilidad.centro_costo_id is 'Centro de costo';
comment on column personal.area_responsabilidad.opera_24_7 is 'Necesita cobertura las 24 horas, todos los días (vigilancia, galpón)';
comment on column personal.area_responsabilidad.activa is 'En uso';
comment on column personal.area_responsabilidad.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.area_responsabilidad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.miembro_area is 'Personas de cada área, con quién es el responsable (puede aprobar las tareas del área).';
comment on column personal.miembro_area.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.miembro_area.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.miembro_area.area_id is 'Área';
comment on column personal.miembro_area.empleado_id is 'Trabajador';
comment on column personal.miembro_area.es_responsable is 'Responsable del área';
comment on column personal.miembro_area.desde is 'Desde';
comment on column personal.miembro_area.hasta is 'Hasta';
comment on column personal.miembro_area.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.miembro_area.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.patron_turno is 'Patrón de turnos reutilizable: semanal (se eligen días y horas), cíclico (ej. 2 días, 2 noches, 2 de descanso para 24/7) o flexible (se arma a mano).';
comment on column personal.patron_turno.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.patron_turno.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.patron_turno.codigo is 'Código, ej. SEM-LV-6-14, CIC-2D2N2L';
comment on column personal.patron_turno.nombre is 'Nombre';
comment on column personal.patron_turno.tipo is 'Semanal: día 1 = lunes … 7 = domingo; cíclico: día 1 … N del ciclo (valores: semanal, ciclico, flexible)';
comment on column personal.patron_turno.ciclo_dias is 'Días del ciclo';
comment on column personal.patron_turno.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.patron_turno.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.patron_turno_detalle is 'Día del patrón con su horario (puede cruzar la medianoche) o descanso.';
comment on column personal.patron_turno_detalle.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.patron_turno_detalle.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.patron_turno_detalle.patron_id is 'Patrón';
comment on column personal.patron_turno_detalle.dia_ciclo is 'Día del ciclo (semanal: 1 lunes … 7 domingo)';
comment on column personal.patron_turno_detalle.hora_inicio is 'Entrada (vacío = descanso)';
comment on column personal.patron_turno_detalle.hora_fin is 'Salida; si es menor o igual a la entrada, termina al día siguiente';
comment on column personal.patron_turno_detalle.tipo is 'Tipo (valores: diurno, nocturno, mixto, descanso)';
comment on column personal.patron_turno_detalle.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.patron_turno_detalle.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.cronograma is 'Cronograma de trabajo de un área por un periodo: se genera desde patrones, se ajusta a mano y se publica cuando cumple jornada máxima, descanso semanal y cobertura.';
comment on column personal.cronograma.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.cronograma.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.cronograma.nombre is 'Nombre, ej. Galpón · noviembre 2026';
comment on column personal.cronograma.area_id is 'Área';
comment on column personal.cronograma.desde is 'Primer día';
comment on column personal.cronograma.hasta is 'Último día';
comment on column personal.cronograma.estado is 'Estado (valores: borrador, publicado, cerrado)';
comment on column personal.cronograma.permitir_huecos is 'Publicar aunque falte cobertura (queda la advertencia)';
comment on column personal.cronograma.publicado_por is 'Quién lo publicó';
comment on column personal.cronograma.publicado_en is 'Cuándo';
comment on column personal.cronograma.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.cronograma.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.asignacion_patron is 'Qué patrón sigue cada persona dentro del cronograma (con desfase para rotar entre varias personas).';
comment on column personal.asignacion_patron.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.asignacion_patron.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.asignacion_patron.cronograma_id is 'Cronograma';
comment on column personal.asignacion_patron.empleado_id is 'Trabajador';
comment on column personal.asignacion_patron.patron_id is 'Patrón';
comment on column personal.asignacion_patron.desfase_dias is 'En qué día del ciclo empieza (rotación)';
comment on column personal.asignacion_patron.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.asignacion_patron.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.requerimiento_cobertura is 'Cuántas personas necesita un área por franja horaria y día (ej. galpón: 1 persona las 24 horas; cabañas: 2 de 8 a 18 los fines de semana).';
comment on column personal.requerimiento_cobertura.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.requerimiento_cobertura.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.requerimiento_cobertura.area_id is 'Área';
comment on column personal.requerimiento_cobertura.dia_semana is '1 lunes … 7 domingo; vacío = todos los días';
comment on column personal.requerimiento_cobertura.hora_inicio is 'Desde';
comment on column personal.requerimiento_cobertura.hora_fin is 'Hasta (24:00 se escribe 23:59:59)';
comment on column personal.requerimiento_cobertura.personas_min is 'Personas mínimas';
comment on column personal.requerimiento_cobertura.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.requerimiento_cobertura.actualizado_en is 'Fecha y hora de la última modificación';
comment on table personal.disponibilidad is 'Días y horas en que cada persona puede o prefiere trabajar (para armar el cronograma flexible).';
comment on column personal.disponibilidad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column personal.disponibilidad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column personal.disponibilidad.empleado_id is 'Trabajador';
comment on column personal.disponibilidad.dia_semana is '1 lunes … 7 domingo';
comment on column personal.disponibilidad.hora_inicio is 'Desde';
comment on column personal.disponibilidad.hora_fin is 'Hasta';
comment on column personal.disponibilidad.preferencia is 'Preferencia (valores: disponible, preferido, no_disponible)';
comment on column personal.disponibilidad.creado_en is 'Fecha y hora de creación del registro';
comment on column personal.disponibilidad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table agenda.recurso is 'Lo que se agenda: cabañas, salón, zona de camping, vehículo, equipo, punto de cargue. Cada recurso tiene su calendario sin cruces.';
comment on column agenda.recurso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column agenda.recurso.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column agenda.recurso.codigo is 'Código';
comment on column agenda.recurso.nombre is 'Nombre';
comment on column agenda.recurso.tipo is 'Tipo (valores: cabana, salon, zona_camping, vehiculo, equipo, punto_cargue, sala, otro)';
comment on column agenda.recurso.alojamiento_id is 'Cabaña de turismo que representa';
comment on column agenda.recurso.activo_id is 'Equipo o vehículo que representa';
comment on column agenda.recurso.zona_id is 'Ubicación';
comment on column agenda.recurso.capacidad is 'Capacidad';
comment on column agenda.recurso.minutos_preparacion is 'Tiempo de alistamiento o limpieza que se bloquea después de cada uso';
comment on column agenda.recurso.activo is 'En uso';
comment on column agenda.recurso.creado_en is 'Fecha y hora de creación del registro';
comment on column agenda.recurso.actualizado_en is 'Fecha y hora de la última modificación';
comment on table agenda.cita is 'Bloque del calendario de un recurso (reserva, limpieza, mantenimiento, uso familiar, entrega). La base impide cruces, contando el alistamiento.';
comment on column agenda.cita.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column agenda.cita.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column agenda.cita.recurso_id is 'Recurso';
comment on column agenda.cita.titulo is 'Título';
comment on column agenda.cita.tipo is 'Tipo (valores: reserva_turistica, limpieza, mantenimiento, uso_familiar, bloqueo, entrega_proveedor, recogida_cliente, capacitacion, auditoria, reunion, otro)';
comment on column agenda.cita.inicio is 'Inicio';
comment on column agenda.cita.fin is 'Fin';
comment on column agenda.cita.fin_con_preparacion is 'Fin más el alistamiento del recurso (lo calcula la base)';
comment on column agenda.cita.estado is 'Estado (valores: tentativa, confirmada, cumplida, cancelada)';
comment on column agenda.cita.reserva_id is 'Reserva de turismo';
comment on column agenda.cita.bloqueo_id is 'Bloqueo del calendario';
comment on column agenda.cita.tarea_id is 'Tarea asociada (limpieza, mantenimiento)';
comment on column agenda.cita.responsable_id is 'Responsable';
comment on column agenda.cita.notas is 'Notas';
comment on column agenda.cita.creado_en is 'Fecha y hora de creación del registro';
comment on column agenda.cita.actualizado_en is 'Fecha y hora de la última modificación';
comment on table agenda.visita is 'Ingreso programado de una persona o un vehículo (proveedor, cliente, turista, técnico, autoridad): se aprueba antes, entrega un pase QR y exige bioseguridad si va al galpón.';
comment on column agenda.visita.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column agenda.visita.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column agenda.visita.tipo is 'Tipo de visitante (valores: proveedor, cliente, turista, contratista, tecnico, autoridad, visitante, transportador)';
comment on column agenda.visita.nombre is 'Nombre de la persona o empresa';
comment on column agenda.visita.tercero_id is 'Tercero, si está registrado';
comment on column agenda.visita.personas is 'Número de personas';
comment on column agenda.visita.vehiculo_placa is 'Placa del vehículo';
comment on column agenda.visita.vehiculo_tipo is 'Tipo de vehículo (valores: carro, camioneta, camion, moto, tractor, bicicleta)';
comment on column agenda.visita.motivo is 'Motivo';
comment on column agenda.visita.zona_destino_id is 'Zona a la que va';
comment on column agenda.visita.ingreso_programado is 'Hora de llegada';
comment on column agenda.visita.salida_programada is 'Hora de salida';
comment on column agenda.visita.anfitrion_id is 'Quién lo recibe';
comment on column agenda.visita.requiere_bioseguridad is 'Entra a una zona de bioseguridad (galpón)';
comment on column agenda.visita.contacto_aves_reciente is 'Declaró contacto con otras aves en las últimas horas del parámetro cuarentena_aves_horas';
comment on column agenda.visita.pase_hash is 'Huella del código QR del pase';
comment on column agenda.visita.estado is 'Estado (valores: solicitada, aprobada, rechazada, en_sitio, salio, no_llego, cancelada)';
comment on column agenda.visita.aprobada_por is 'Quién la aprobó';
comment on column agenda.visita.motivo_rechazo is 'Motivo del rechazo';
comment on column agenda.visita.cita_id is 'Cita de cargue o descargue, si aplica';
comment on column agenda.visita.creado_en is 'Fecha y hora de creación del registro';
comment on column agenda.visita.actualizado_en is 'Fecha y hora de la última modificación';
comment on table agenda.registro_acceso is 'Cada entrada o salida real por la portería (persona o vehículo): con pase, carné QR o NFC, a mano o por lectura de placa. Funciona sin internet y alimenta la jornada.';
comment on column agenda.registro_acceso.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column agenda.registro_acceso.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column agenda.registro_acceso.sentido is 'Entrada o salida (valores: entrada, salida)';
comment on column agenda.registro_acceso.tipo is 'Qué pasa (valores: persona, vehiculo)';
comment on column agenda.registro_acceso.visita_id is 'Visita programada';
comment on column agenda.registro_acceso.empleado_id is 'Trabajador';
comment on column agenda.registro_acceso.nombre is 'Nombre (si no es visita ni trabajador)';
comment on column agenda.registro_acceso.placa is 'Placa';
comment on column agenda.registro_acceso.punto is 'Punto de control';
comment on column agenda.registro_acceso.metodo is 'Cómo se identificó (valores: pase_qr, carne_qr, carne_nfc, manual, lectura_placa)';
comment on column agenda.registro_acceso.desinfeccion is 'Pasó por desinfección (personas y vehículos que van al galpón)';
comment on column agenda.registro_acceso.ocurrido_en is 'Momento';
comment on column agenda.registro_acceso.registrado_por is 'Portero o encargado';
comment on column agenda.registro_acceso.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column agenda.registro_acceso.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column agenda.registro_acceso.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column agenda.registro_acceso.creado_en is 'Fecha y hora de creación del registro';
comment on column agenda.registro_acceso.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.necesidad_formacion is 'Necesidad de formación detectada (por cargo, por una no conformidad, por un cambio o pedida por la persona).';
comment on column formacion.necesidad_formacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.necesidad_formacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.necesidad_formacion.origen is 'De dónde sale (valores: cargo, no_conformidad, cambio, solicitud, evaluacion_desempeno, norma)';
comment on column formacion.necesidad_formacion.descripcion is 'Qué se necesita aprender';
comment on column formacion.necesidad_formacion.tercero_id is 'Persona, si es individual';
comment on column formacion.necesidad_formacion.competencia_id is 'Competencia';
comment on column formacion.necesidad_formacion.curso_id is 'Curso que la atiende';
comment on column formacion.necesidad_formacion.estado is 'Estado (valores: abierta, planificada, atendida, descartada)';
comment on column formacion.necesidad_formacion.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.necesidad_formacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.encuesta is 'Encuesta de satisfacción y de resultados de un curso o sesión (seguimiento y medición de la formación).';
comment on column formacion.encuesta.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.encuesta.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.encuesta.curso_id is 'Curso';
comment on column formacion.encuesta.sesion_id is 'Sesión';
comment on column formacion.encuesta.tercero_id is 'Quién responde (vacío = anónima)';
comment on column formacion.encuesta.satisfaccion is 'Satisfacción general 1 a 5';
comment on column formacion.encuesta.utilidad is 'Utilidad para el trabajo 1 a 5';
comment on column formacion.encuesta.instructor is 'Desempeño del instructor 1 a 5';
comment on column formacion.encuesta.comentario is 'Comentario';
comment on column formacion.encuesta.id_cliente is 'Identificador UUIDv7 que genera el celular al capturar sin conexión; si llega dos veces, la segunda se ignora (sincronización idempotente)';
comment on column formacion.encuesta.capturado_en is 'Momento en que se registró en el celular (puede ser horas antes de llegar al servidor)';
comment on column formacion.encuesta.dispositivo_captura_id is 'Celular, lector o báscula con que se capturó';
comment on column formacion.encuesta.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.encuesta.actualizado_en is 'Fecha y hora de la última modificación';
comment on table formacion.queja_apelacion is 'Queja sobre la formación o apelación de una nota o certificado; se responde en plazo y la resuelve alguien distinto del instructor.';
comment on column formacion.queja_apelacion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column formacion.queja_apelacion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column formacion.queja_apelacion.tipo is 'Tipo (valores: queja, apelacion)';
comment on column formacion.queja_apelacion.tercero_id is 'Quién la presenta';
comment on column formacion.queja_apelacion.curso_id is 'Curso';
comment on column formacion.queja_apelacion.certificado_id is 'Certificado apelado';
comment on column formacion.queja_apelacion.descripcion is 'Qué pasó';
comment on column formacion.queja_apelacion.presentada_en is 'Fecha';
comment on column formacion.queja_apelacion.responder_antes is 'Plazo de respuesta';
comment on column formacion.queja_apelacion.estado is 'Estado (valores: recibida, en_estudio, resuelta, rechazada)';
comment on column formacion.queja_apelacion.respuesta is 'Respuesta';
comment on column formacion.queja_apelacion.resuelta_por is 'Quién resolvió';
comment on column formacion.queja_apelacion.creado_en is 'Fecha y hora de creación del registro';
comment on column formacion.queja_apelacion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.proyecto is 'Proyecto de la finca (nuevo galpón, sistema solar, cabañas, certificación, piloto de robot) con acta de constitución, enfoque predictivo, adaptativo o híbrido y área de enfoque actual.';
comment on column proyectos.proyecto.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.proyecto.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.proyecto.codigo is 'Código, ej. PRY-GAL-500';
comment on column proyectos.proyecto.nombre is 'Nombre';
comment on column proyectos.proyecto.objetivo is 'Objetivo (resultado y valor esperado)';
comment on column proyectos.proyecto.justificacion is 'Por qué (caso de negocio)';
comment on column proyectos.proyecto.criterios_exito is 'Cómo se sabrá que salió bien';
comment on column proyectos.proyecto.iniciativa_id is 'Iniciativa de negocio que lo origina';
comment on column proyectos.proyecto.linea_negocio_id is 'Línea';
comment on column proyectos.proyecto.enfoque is 'Enfoque de desarrollo (valores: predictivo, adaptativo, hibrido)';
comment on column proyectos.proyecto.area_enfoque is 'Área de enfoque en que está (valores: inicio, planificacion, ejecucion, monitoreo_control, cierre)';
comment on column proyectos.proyecto.estado is 'Estado (valores: propuesto, aprobado, en_curso, suspendido, cerrado, cancelado)';
comment on column proyectos.proyecto.patrocinador_id is 'Patrocinador (quien aprueba y responde por el valor)';
comment on column proyectos.proyecto.director_id is 'Director del proyecto';
comment on column proyectos.proyecto.presupuesto is 'Presupuesto al concluir (BAC) de la línea base vigente';
comment on column proyectos.proyecto.fuente_fondos is 'Financiación (valores: utilidades_retenidas, credito, fondo_emprender, aporte_familia, convenio, mixto)';
comment on column proyectos.proyecto.inicio_plan is 'Inicio planeado';
comment on column proyectos.proyecto.fin_plan is 'Fin planeado';
comment on column proyectos.proyecto.inicio_real is 'Inicio real';
comment on column proyectos.proyecto.fin_real is 'Fin real';
comment on column proyectos.proyecto.acta_documento_id is 'Acta de constitución firmada';
comment on column proyectos.proyecto.aprobado_por is 'Quién lo aprobó';
comment on column proyectos.proyecto.aprobado_en is 'Cuándo';
comment on column proyectos.proyecto.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.proyecto.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.interesado is 'Interesado del proyecto con su interés, influencia y estrategia de relación (dominio de interesados).';
comment on column proyectos.interesado.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.interesado.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.interesado.proyecto_id is 'Proyecto';
comment on column proyectos.interesado.tercero_id is 'Persona o entidad';
comment on column proyectos.interesado.usuario_id is 'Usuario interno';
comment on column proyectos.interesado.nombre is 'Nombre o rol';
comment on column proyectos.interesado.rol is 'Rol en el proyecto';
comment on column proyectos.interesado.interes is 'Interés 1 a 5';
comment on column proyectos.interesado.influencia is 'Influencia 1 a 5';
comment on column proyectos.interesado.estrategia is 'gestionar_de_cerca, mantener_satisfecho, mantener_informado o monitorear (la calcula la base)';
comment on column proyectos.interesado.expectativas is 'Qué espera';
comment on column proyectos.interesado.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.interesado.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.elemento_edt is 'Estructura de desglose del trabajo (EDT): entregables y paquetes de trabajo con su criterio de aceptación.';
comment on column proyectos.elemento_edt.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.elemento_edt.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.elemento_edt.proyecto_id is 'Proyecto';
comment on column proyectos.elemento_edt.padre_id is 'Elemento superior';
comment on column proyectos.elemento_edt.codigo is 'Código EDT, ej. 1.2.3';
comment on column proyectos.elemento_edt.nombre is 'Nombre';
comment on column proyectos.elemento_edt.es_entregable is 'Es un entregable que se acepta';
comment on column proyectos.elemento_edt.criterio_aceptacion is 'Cómo se acepta';
comment on column proyectos.elemento_edt.estado is 'Estado (valores: pendiente, en_curso, terminado, aceptado, rechazado)';
comment on column proyectos.elemento_edt.aceptado_por is 'Quién lo aceptó';
comment on column proyectos.elemento_edt.aceptado_en is 'Cuándo';
comment on column proyectos.elemento_edt.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.elemento_edt.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.iteracion is 'Iteración o sprint para la parte adaptativa del proyecto.';
comment on column proyectos.iteracion.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.iteracion.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.iteracion.proyecto_id is 'Proyecto';
comment on column proyectos.iteracion.numero is 'Número';
comment on column proyectos.iteracion.objetivo is 'Objetivo de la iteración';
comment on column proyectos.iteracion.inicio is 'Inicio';
comment on column proyectos.iteracion.fin is 'Fin';
comment on column proyectos.iteracion.estado is 'Estado (valores: planeada, en_curso, cerrada)';
comment on column proyectos.iteracion.retrospectiva is 'Qué se aprendió';
comment on column proyectos.iteracion.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.iteracion.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.actividad is 'Actividad del cronograma (o historia de la iteración) con duración, fechas, avance, costo y responsable; la ruta crítica la calcula la base.';
comment on column proyectos.actividad.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.actividad.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.actividad.proyecto_id is 'Proyecto';
comment on column proyectos.actividad.elemento_edt_id is 'Paquete de trabajo';
comment on column proyectos.actividad.iteracion_id is 'Iteración';
comment on column proyectos.actividad.codigo is 'Código';
comment on column proyectos.actividad.nombre is 'Nombre';
comment on column proyectos.actividad.es_hito is 'Hito (duración 0)';
comment on column proyectos.actividad.duracion_dias is 'Duración en días';
comment on column proyectos.actividad.inicio_temprano is 'Día de inicio temprano (CPM, desde el día 0)';
comment on column proyectos.actividad.fin_temprano is 'Día de fin temprano';
comment on column proyectos.actividad.inicio_tardio is 'Día de inicio tardío';
comment on column proyectos.actividad.fin_tardio is 'Día de fin tardío';
comment on column proyectos.actividad.holgura is 'Holgura total en días';
comment on column proyectos.actividad.critica is 'Está en la ruta crítica';
comment on column proyectos.actividad.inicio_plan is 'Inicio planeado';
comment on column proyectos.actividad.fin_plan is 'Fin planeado';
comment on column proyectos.actividad.inicio_real is 'Inicio real';
comment on column proyectos.actividad.fin_real is 'Fin real';
comment on column proyectos.actividad.avance_pct is 'Avance físico';
comment on column proyectos.actividad.costo_plan is 'Costo planeado';
comment on column proyectos.actividad.costo_real is 'Costo real';
comment on column proyectos.actividad.responsable_id is 'Responsable';
comment on column proyectos.actividad.area_id is 'Área de responsabilidad';
comment on column proyectos.actividad.tarea_id is 'Tarea de campo que la ejecuta';
comment on column proyectos.actividad.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.actividad.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.dependencia is 'Relación entre actividades (fin a comienzo, comienzo a comienzo, fin a fin, comienzo a fin) con adelanto o retraso.';
comment on column proyectos.dependencia.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.dependencia.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.dependencia.predecesora_id is 'Actividad predecesora';
comment on column proyectos.dependencia.sucesora_id is 'Actividad sucesora';
comment on column proyectos.dependencia.tipo is 'Tipo de relación (valores: FC, CC, FF, CF)';
comment on column proyectos.dependencia.desfase_dias is 'Adelanto (negativo) o retraso (positivo)';
comment on column proyectos.dependencia.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.dependencia.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.riesgo is 'Riesgo del proyecto (amenaza u oportunidad) con probabilidad, impacto, respuesta y responsable.';
comment on column proyectos.riesgo.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.riesgo.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.riesgo.proyecto_id is 'Proyecto';
comment on column proyectos.riesgo.descripcion is 'Causa, riesgo y efecto';
comment on column proyectos.riesgo.tipo is 'Tipo (valores: amenaza, oportunidad)';
comment on column proyectos.riesgo.categoria is 'Categoría (valores: tecnico, clima, sanitario, mercado, financiero, legal, personas, proveedor, seguridad)';
comment on column proyectos.riesgo.probabilidad is '1 a 5';
comment on column proyectos.riesgo.impacto is '1 a 5';
comment on column proyectos.riesgo.severidad is 'Probabilidad × impacto (1 a 25)';
comment on column proyectos.riesgo.respuesta is 'Estrategia de respuesta (valores: evitar, mitigar, transferir, aceptar, escalar, explotar, mejorar, compartir)';
comment on column proyectos.riesgo.plan_respuesta is 'Qué se hará';
comment on column proyectos.riesgo.disparador is 'Señal de que se está materializando';
comment on column proyectos.riesgo.responsable_id is 'Dueño del riesgo';
comment on column proyectos.riesgo.estado is 'Estado (valores: identificado, en_respuesta, materializado, cerrado)';
comment on column proyectos.riesgo.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.riesgo.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.registro is 'Registro de incidentes, supuestos, restricciones, decisiones y lecciones aprendidas del proyecto.';
comment on column proyectos.registro.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.registro.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.registro.proyecto_id is 'Proyecto';
comment on column proyectos.registro.tipo is 'Tipo (valores: incidente, supuesto, restriccion, decision, leccion_aprendida)';
comment on column proyectos.registro.descripcion is 'Descripción';
comment on column proyectos.registro.responsable_id is 'Responsable';
comment on column proyectos.registro.estado is 'Estado (valores: abierto, cerrado)';
comment on column proyectos.registro.fecha is 'Fecha';
comment on column proyectos.registro.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.registro.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.solicitud_cambio is 'Solicitud de cambio al alcance, cronograma o costo; la aprueba una persona distinta de quien la pide y, si se aprueba, crea una nueva línea base.';
comment on column proyectos.solicitud_cambio.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.solicitud_cambio.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.solicitud_cambio.proyecto_id is 'Proyecto';
comment on column proyectos.solicitud_cambio.descripcion is 'Qué cambia y por qué';
comment on column proyectos.solicitud_cambio.solicitada_por is 'Quién la pide';
comment on column proyectos.solicitud_cambio.impacto_alcance is 'Impacto en el alcance';
comment on column proyectos.solicitud_cambio.impacto_dias is 'Días que agrega o quita';
comment on column proyectos.solicitud_cambio.impacto_costo is 'Costo que agrega o quita';
comment on column proyectos.solicitud_cambio.estado is 'Estado (valores: propuesta, aprobada, rechazada)';
comment on column proyectos.solicitud_cambio.decidida_por is 'Quién decidió';
comment on column proyectos.solicitud_cambio.decidida_en is 'Cuándo';
comment on column proyectos.solicitud_cambio.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.solicitud_cambio.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.linea_base is 'Línea base aprobada de alcance, cronograma y costo; no se edita: cada cambio aprobado crea una versión nueva.';
comment on column proyectos.linea_base.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.linea_base.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.linea_base.proyecto_id is 'Proyecto';
comment on column proyectos.linea_base.version is 'Versión';
comment on column proyectos.linea_base.presupuesto is 'BAC';
comment on column proyectos.linea_base.fin_plan is 'Fecha de fin';
comment on column proyectos.linea_base.alcance is 'Resumen del alcance';
comment on column proyectos.linea_base.solicitud_cambio_id is 'Cambio que la originó';
comment on column proyectos.linea_base.aprobada_por is 'Quién la aprobó';
comment on column proyectos.linea_base.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.linea_base.actualizado_en is 'Fecha y hora de la última modificación';
comment on table proyectos.medicion_valor_ganado is 'Medición del desempeño en una fecha de corte por valor ganado: PV, EV, AC, CPI, SPI, EAC, ETC y VAC.';
comment on column proyectos.medicion_valor_ganado.id is 'Identificador interno (número consecutivo generado por la base de datos)';
comment on column proyectos.medicion_valor_ganado.predio_id is 'Finca a la que pertenece el registro; lo pone la base según la sesión y la seguridad por filas impide ver otras fincas';
comment on column proyectos.medicion_valor_ganado.proyecto_id is 'Proyecto';
comment on column proyectos.medicion_valor_ganado.fecha_corte is 'Fecha de corte';
comment on column proyectos.medicion_valor_ganado.pv is 'Valor planificado';
comment on column proyectos.medicion_valor_ganado.ev is 'Valor ganado';
comment on column proyectos.medicion_valor_ganado.ac is 'Costo real';
comment on column proyectos.medicion_valor_ganado.cpi is 'Índice de desempeño del costo (EV/AC)';
comment on column proyectos.medicion_valor_ganado.spi is 'Índice de desempeño del cronograma (EV/PV)';
comment on column proyectos.medicion_valor_ganado.eac is 'Estimación a la conclusión (BAC/CPI)';
comment on column proyectos.medicion_valor_ganado.etc is 'Estimación hasta concluir (EAC − AC)';
comment on column proyectos.medicion_valor_ganado.vac is 'Variación a la conclusión (BAC − EAC)';
comment on column proyectos.medicion_valor_ganado.creado_en is 'Fecha y hora de creación del registro';
comment on column proyectos.medicion_valor_ganado.actualizado_en is 'Fecha y hora de la última modificación';
