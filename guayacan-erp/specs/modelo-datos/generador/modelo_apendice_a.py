"""Apéndice A · Tablas del esquema adopcion, en el mismo formato que modelo.py.

Para qué sirve: gen_apps.py (docs/uml/fuentes) lee este archivo además de modelo.py y genera la app Django
apps/adopcion (modelos, serializers, vistas, rutas, servicios y pruebas). La estructura real de la base la crea
specs/modelo-datos/apendice_a_adopcion.sql; si cambia una tabla allá, cámbiela también aquí y regenere la app.

Formato de cada columna: (nombre, tipo, restricciones, significado)
  tipo: 'fk:esquema.tabla' = llave foránea; 'enum:a,b,c' = lista cerrada (CHECK); o el tipo de PostgreSQL
  restricciones: 'not null' = obligatorio; 'default X' = valor por defecto que pone la base; 'unique' = no se repite
"""

ESQUEMAS_A = {'adopcion': 'Adopción de árboles y animales: catálogo, sitios, bienes, contratos de compra y cuidado, cuotas, seguimiento, liquidaciones y saldo del adoptante'}

# Tabla que se captura sin conexión en la app de campo (recibe id_cliente, capturado_en y dispositivo_captura_id)
CAPTURA_A = {'adopcion.seguimiento'}

# Cada tabla: (esquema, tabla, fase, descripción, columnas, extras, tiene creado_en y actualizado_en)
T_A = []

T_A.append(('adopcion', 'plan', 3, 'Catálogo de lo que se puede adoptar, con precio de compra y de readopción, cuota mensual, costos estimados (para el margen), meses de madurez, garantía y permiso que exige su liquidación.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código del plan (ej. FRU-CACAO)'),
    ('nombre', 'varchar(120)', 'not null', 'Nombre comercial del plan'),
    ('tipo', 'enum:frutal,maderable,ovino,caprino,ave', 'not null', 'Grupo de especie'),
    ('cultivo_id', 'fk:produccion.cultivo', '', 'Cultivo, si es frutal o maderable'),
    ('especie_id', 'fk:produccion.especie', '', 'Especie animal, si es ovino, caprino o ave'),
    ('precio_compra', 'numeric(14,2)', 'not null', 'Precio de compra (incluye el bien, la siembra o instalación y el primer mes de cuidado)'),
    ('precio_readopcion', 'numeric(14,2)', 'not null', 'Precio para un nuevo adoptante de un bien abandonado'),
    ('cuota_mensual', 'numeric(14,2)', 'not null', 'Cuota mensual de cuidado que se ofrece'),
    ('costo_bien', 'numeric(14,2)', 'not null', 'Costo estimado del bien para la finca (plántula o animal, siembra)'),
    ('costo_cuidado_mensual', 'numeric(14,2)', 'not null', 'Costo estimado del cuidado mensual (insumos y mano de obra)'),
    ('meses_madurez', 'smallint', 'not null', 'Meses hasta la madurez (producción, tala o sacrificio)'),
    ('garantia_meses', 'smallint', 'not null default 12', 'Meses de garantía de reposición si el bien muere'),
    ('requiere_permiso', 'enum:ninguno,tala_car,remision_ica,planta_beneficio', "not null default 'ninguno'", 'Soporte legal que exige la liquidación final'),
    ('descripcion', 'text', '', 'Descripción para el sitio público'),
    ('activo', 'boolean', 'not null default true', 'Se ofrece a la venta'),
], [], True))

T_A.append(('adopcion', 'sitio', 3, 'Lugar asignado por la administración: hoyo de siembra en un lote o cupo en corral o galpón, con coordenadas.', [
    ('zona_id', 'fk:nucleo.zona', 'not null', 'Zona o lote de la finca'),
    ('codigo', 'varchar(20)', 'not null unique', 'Código del sitio (letrero en campo)'),
    ('tipo', 'enum:hoyo_siembra,corral,galpon', 'not null', 'Clase de sitio'),
    ('latitud', 'numeric(9,6)', '', 'Latitud del sitio'),
    ('longitud', 'numeric(9,6)', '', 'Longitud del sitio'),
    ('estado', 'enum:libre,reservado,ocupado,inhabilitado', "not null default 'libre'", 'Disponibilidad del sitio'),
], [], True))

T_A.append(('adopcion', 'bien', 3, 'El árbol o el animal concreto que se vende, con su código, sitio, estado de vida y el bien al que reemplaza si fue repuesto en garantía.', [
    ('codigo', 'varchar(20)', 'not null unique', 'Código del bien (va en el letrero y el QR)'),
    ('plan_id', 'fk:adopcion.plan', 'not null', 'Plan al que pertenece'),
    ('sitio_id', 'fk:adopcion.sitio', '', 'Sitio donde está'),
    ('animal_id', 'fk:produccion.animal', '', 'Animal registrado en producción, si es animal'),
    ('fecha_inicio', 'date', '', 'Fecha de siembra o de inicio del cuidado'),
    ('estado', 'enum:disponible,reservado,activo,en_readopcion,maduro,liquidado,muerto', "not null default 'disponible'", 'Estado de vida y de venta del bien'),
    ('nombre_dado', 'varchar(60)', '', 'Nombre que le da el adoptante'),
    ('reemplaza_id', 'fk:adopcion.bien', '', 'Bien muerto al que repone en garantía'),
], [], True))

T_A.append(('adopcion', 'contrato', 3, 'Compraventa del bien más servicio de cuidado mensual. Un bien vivo tiene a lo sumo un contrato activo; guarda la modalidad de siembra y la decisión en la madurez.', [
    ('numero', 'varchar(20)', 'not null unique', 'Número del contrato'),
    ('bien_id', 'fk:adopcion.bien', 'not null', 'Bien vendido'),
    ('adoptante_id', 'fk:terceros.tercero', 'not null', 'Adoptante (tercero)'),
    ('tipo', 'enum:compra,readopcion,cesion', 'not null', 'Origen del contrato'),
    ('fecha', 'date', 'not null default CURRENT_DATE', 'Fecha del contrato'),
    ('precio', 'numeric(14,2)', 'not null', 'Precio pagado'),
    ('cuota_mensual', 'numeric(14,2)', 'not null', 'Cuota mensual pactada (no cambia si cambia el plan)'),
    ('modalidad_siembra', 'enum:propia,trabajador,no_aplica', "not null default 'no_aplica'", 'Quién siembra el árbol'),
    ('consentimiento_id', 'fk:terceros.consentimiento_datos', '', 'Autorización de datos con finalidad seguimiento_adopcion'),
    ('estado', 'enum:activo,terminado_abandono,terminado_liquidacion,cedido,terminado_muerte', "not null default 'activo'", 'Estado del contrato'),
    ('decision_madurez', 'enum:mantener,liquidar', '', 'Decisión del dueño en la madurez'),
    ('decidido_en', 'timestamptz', '', 'Cuándo se registró la decisión'),
    ('terminado_en', 'timestamptz', '', 'Cuándo terminó el contrato'),
], [], True))

T_A.append(('adopcion', 'cuota', 3, 'Cuota mensual de cuidado; vence el día 10, se paga por la pasarela o se compensa con el saldo a favor del adoptante.', [
    ('contrato_id', 'fk:adopcion.contrato', 'not null', 'Contrato al que pertenece'),
    ('periodo', 'date', 'not null', 'Mes cobrado (primer día del mes)'),
    ('valor', 'numeric(14,2)', 'not null', 'Valor de la cuota'),
    ('vence_en', 'date', 'not null', 'Fecha de vencimiento (día 10)'),
    ('estado', 'enum:pendiente,pagada,compensada,anulada', "not null default 'pendiente'", 'Estado de la cuota'),
    ('pago_id', 'fk:comercial.pago', '', 'Pago que la canceló'),
    ('pagada_en', 'timestamptz', '', 'Cuándo se pagó o compensó'),
], [], True))

T_A.append(('adopcion', 'seguimiento', 3, 'Bitácora que ve el adoptante: siembra, video, fotos, visitas, sanidad, mediciones, muerte, reposición y avisos de mora. Se captura sin conexión.', [
    ('bien_id', 'fk:adopcion.bien', 'not null', 'Bien seguido'),
    ('tipo', 'enum:siembra,video_siembra,foto,visita,sanidad,medicion,muerte,reposicion,aviso_mora', 'not null', 'Clase de registro'),
    ('fecha', 'timestamptz', 'not null default now()', 'Fecha y hora del registro'),
    ('descripcion', 'text', '', 'Descripción'),
    ('evidencia_url', 'varchar(300)', '', 'Foto o video en el almacén de objetos'),
    ('tarea_id', 'fk:personal.tarea', '', 'Tarea de campo que lo originó'),
    ('enviado_al_adoptante', 'boolean', 'not null default false', 'Ya se envió al adoptante'),
], [], True))

T_A.append(('adopcion', 'liquidacion', 3, 'Venta de productos o liquidación final (tala, sacrificio, venta en pie): ingresos menos gastos = utilidad neta; la finca cobra el % de administración solo si hay utilidad.', [
    ('contrato_id', 'fk:adopcion.contrato', 'not null', 'Contrato liquidado'),
    ('tipo', 'enum:productos,tala,sacrificio,venta_en_pie', 'not null', 'Clase de liquidación'),
    ('periodo_desde', 'date', '', 'Inicio del periodo liquidado (productos)'),
    ('periodo_hasta', 'date', '', 'Fin del periodo liquidado (productos)'),
    ('ingresos', 'numeric(14,2)', 'not null default 0', 'Ingresos de la venta'),
    ('gastos', 'numeric(14,2)', 'not null default 0', 'Gastos directos atribuibles'),
    ('utilidad_neta', 'numeric(14,2)', '', 'Ingresos menos gastos (la calcula la base)'),
    ('comision_pct', 'numeric(5,2)', '', 'Porcentaje de administración vigente (parámetro comision_adopcion_pct)'),
    ('comision', 'numeric(14,2)', '', 'Comisión de la finca: % de la utilidad positiva'),
    ('abono_adoptante', 'numeric(14,2)', '', 'Lo que se abona al adoptante'),
    ('soporte_documento_id', 'fk:documental.documento', '', 'Permiso de tala, remisión ICA o acta de beneficio'),
    ('estado', 'enum:borrador,aprobada,anulada', "not null default 'borrador'", 'Estado de la liquidación'),
    ('aprobada_por', 'bigint', '', 'Persona que la aprobó'),
    ('aprobada_en', 'timestamptz', '', 'Cuándo se aprobó'),
    ('detalle', 'jsonb', "not null default '[]'::jsonb", 'Líneas de ingresos y gastos (JSON)'),
], [], True))

T_A.append(('adopcion', 'movimiento_saldo', 3, 'Cuenta del adoptante, solo inserción: abonos de liquidaciones, cuotas compensadas y pagos al adoptante. No genera intereses ni se invierte.', [
    ('adoptante_id', 'fk:terceros.tercero', 'not null', 'Adoptante dueño del saldo'),
    ('tipo', 'enum:abono_liquidacion,compensacion_cuota,pago_al_adoptante', 'not null', 'Clase de movimiento'),
    ('valor', 'numeric(14,2)', 'not null', 'Valor (siempre positivo; el tipo da el signo)'),
    ('liquidacion_id', 'fk:adopcion.liquidacion', '', 'Liquidación que lo originó'),
    ('cuota_id', 'fk:adopcion.cuota', '', 'Cuota compensada'),
    ('referencia', 'varchar(80)', '', 'Referencia del pago al adoptante'),
    ('fecha', 'timestamptz', 'not null default now()', 'Fecha y hora del movimiento'),
    ('creado_en', 'timestamptz', 'not null default now()', 'Fecha y hora de creación del registro'),
], [], False))
