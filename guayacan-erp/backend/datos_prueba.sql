-- Desactivar RLS temporalmente para poder insertar desde consola
SET session_replication_role = 'replica';

-- 1. Crear un Predio (Finca)
INSERT INTO nucleo.predio (nombre, municipio, departamento, area_hectareas, tipo_explotacion) 
VALUES ('Finca La Esperanza', 'Bogotá', 'Cundinamarca', 10.5, 'AGRICOLA') 
ON CONFLICT DO NOTHING;

-- 2. Fijar el predio en la sesión actual (para que nucleo.predio_actual() devuelva este ID)
SELECT set_config('guayacan.predio_id', (SELECT id::text FROM nucleo.predio LIMIT 1), false);

-- 3. Insertar los 5 Clientes
INSERT INTO terceros.tercero (tipo_persona, tipo_documento, numero_documento, digito_verificacion, nombres, apellidos) 
VALUES 
('JURIDICA', 'NIT', '900123456', '1', 'Distribuidora El Sol', NULL), 
('NATURAL', 'CC', '10203040', NULL, 'Juan', 'Pérez'), 
('JURIDICA', 'NIT', '800987654', '2', 'AgroInsumos del Valle', NULL), 
('NATURAL', 'CC', '79887766', NULL, 'María', 'Gómez'), 
('JURIDICA', 'NIT', '901234567', '0', 'Transportes Rápidos', NULL);

-- 4. Insertar los 5 Productos (si la tabla existe)
INSERT INTO inventario.producto (codigo, nombre, precio_venta, costo_promedio, unidad_medida) 
VALUES 
('PROD001', 'Fertilizante NPK', 120000, 80000, 'Bulto 50kg'), 
('PROD002', 'Semilla de Maíz', 45000, 25000, 'Bulto 20kg'), 
('PROD003', 'Herbicida Glifosato', 35000, 18000, 'Galón'), 
('PROD004', 'Manguera de Riego', 15000, 9000, 'Rollo 100m'), 
('PROD005', 'Guantes de Trabajo', 8500, 4500, 'Par');

-- Reactivar RLS
SET session_replication_role = 'origin';