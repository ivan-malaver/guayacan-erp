SET session_replication_role = 'replica';

-- Los productos se insertan con el tipo correcto: 'insumo'
INSERT INTO inventario.producto (predio_id, sku, nombre, descripcion, tipo, categoria_id, unidad_id) VALUES 
(3, 'PROD001', 'Fertilizante NPK', 'Fertilizante granulado 15-15-15', 'insumo', (SELECT id FROM inventario.categoria_producto WHERE nombre = 'Insumos Agrícolas' LIMIT 1), (SELECT id FROM inventario.unidad_medida WHERE codigo = 'UND' LIMIT 1)),
(3, 'PROD002', 'Semilla de Maíz', 'Semilla híbrida certificada', 'insumo', (SELECT id FROM inventario.categoria_producto WHERE nombre = 'Insumos Agrícolas' LIMIT 1), (SELECT id FROM inventario.unidad_medida WHERE codigo = 'UND' LIMIT 1)),
(3, 'PROD003', 'Herbicida Glifosato', 'Herbicida de amplio espectro', 'insumo', (SELECT id FROM inventario.categoria_producto WHERE nombre = 'Insumos Agrícolas' LIMIT 1), (SELECT id FROM inventario.unidad_medida WHERE codigo = 'UND' LIMIT 1)),
(3, 'PROD004', 'Manguera de Riego', 'Manguera de polietileno 1/2 pulgada', 'insumo', (SELECT id FROM inventario.categoria_producto WHERE nombre = 'Insumos Agrícolas' LIMIT 1), (SELECT id FROM inventario.unidad_medida WHERE codigo = 'UND' LIMIT 1)),
(3, 'PROD005', 'Guantes de Trabajo', 'Guantes de nitrilo resistentes', 'insumo', (SELECT id FROM inventario.categoria_producto WHERE nombre = 'Insumos Agrícolas' LIMIT 1), (SELECT id FROM inventario.unidad_medida WHERE codigo = 'UND' LIMIT 1));

SET session_replication_role = 'origin';
