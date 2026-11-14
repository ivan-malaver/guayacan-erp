SET session_replication_role = 'replica';
INSERT INTO terceros.tercero (predio_id, tipo_persona, tipo_documento, numero_documento, digito_verificacion, nombres, apellidos) VALUES 
(3, 'juridica', 'NIT', '900123456', '1', 'Distribuidora El Sol', NULL), 
(3, 'natural', 'CC', '10203040', NULL, 'Juan', 'Pérez'), 
(3, 'juridica', 'NIT', '800987654', '2', 'AgroInsumos del Valle', NULL), 
(3, 'natural', 'CC', '79887766', NULL, 'María', 'Gómez'), 
(3, 'juridica', 'NIT', '901234567', '0', 'Transportes Rápidos', NULL);
INSERT INTO inventario.producto (codigo, nombre, precio_venta, costo_promedio, unidad_medida) VALUES ('PROD001', 'Fertilizante NPK', 120000, 80000, 'Bulto 50kg'), ('PROD002', 'Semilla de Maíz', 45000, 25000, 'Bulto 20kg'), ('PROD003', 'Herbicida Glifosato', 35000, 18000, 'Galón'), ('PROD004', 'Manguera de Riego', 15000, 9000, 'Rollo 100m'), ('PROD005', 'Guantes de Trabajo', 8500, 4500, 'Par');
SET session_replication_role = 'origin';
