# Modelo de datos de GuayacanERP (v5 · operación integral de la finca)

| Archivo | Qué es |
| --- | --- |
| `esquema_postgresql.sql` | 25 esquemas, 246 tablas (el Apéndice A suma el esquema 26, `adopcion`, con 8 tablas: total 254), seguridad por filas, llaves compuestas, auditoría particionada, kardex, FEFO, cadena de frío, retiro de lotes, cartera, permuta, seguridad perimetral, cámaras, funciones por finca y, desde la v5, personal y cronogramas 24/7, nómina, formación, activos, documental, cumplimiento, seguros, seguridad informática, CRM, estrategia, agenda, proyectos y finanzas ampliadas. Para PostgreSQL 18 con PostGIS, pgvector y btree_gist |
| `datos_iniciales.sql` | Roles, parámetros, finca real y finca de práctica, zonas, siembras, riego instalado, productos con vida útil, precios, periodos, agentes, herramientas, políticas de canal, funciones por finca, categorías del huevo, nevera prevista y zonas de seguridad |
| `colecciones_mongodb.js` / `.json` | 8 colecciones con validación, `predio_id`, índices y borrado automático (mensajes con audio y transcripción) |
| `diccionario_postgresql.csv` / `.md` | Diccionario campo por campo |
| `diccionario_mongodb.csv` / `.md` | Diccionario de las colecciones |
| `generador/` | `modelo.py` (tablas), `reglas_negocio.sql` (funciones y disparadores), `generar.py`, `mongo.py`, `excel_diccionario.py`, `excel_apis.py` |
| `apendice_a_adopcion.sql` | Apéndice A: esquema `adopcion` (8 tablas), reglas y datos iniciales. Se carga después de `datos_iniciales.sql`; sus 48 pruebas están en `../casos-prueba/pruebas_adopcion.sql` |
| `../casos-prueba/pruebas_reglas_v4.sql` y `pruebas_reglas_v5.sql` | 90 + 215 pruebas de las reglas, ejecutadas con el rol de la API; resultado en `resultado_pruebas_v5.log` |

## Cargar y probar (Windows con Docker)

Copie `.env.ejemplo` como `.env` y cambie las claves. Los comandos son para el Símbolo del sistema (cmd); en PowerShell
cambie `comando < archivo` por `Get-Content archivo | comando`.

```
docker compose up -d --build postgres mongodb
docker compose exec -T postgres psql -U postgres -d guayacan -v ON_ERROR_STOP=1 < specs\modelo-datos\esquema_postgresql.sql
docker compose exec -T postgres psql -U postgres -d guayacan -v ON_ERROR_STOP=1 < specs\modelo-datos\datos_iniciales.sql
docker compose exec -T postgres psql -U postgres -d guayacan < specs\casos-prueba\pruebas_reglas_v5.sql
rem Para la regresión de la v4, borre y cree otra vez la base, cargue esquema y datos, y corra pruebas_reglas_v4.sql
docker compose exec -T mongodb sh -c "mongosh -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin guayacan" < specs\modelo-datos\colecciones_mongodb.js
```

La última línea de las pruebas debe decir `TODAS LAS PRUEBAS PASARON`. Las pruebas se corren sobre una base recién creada.

La API se conecta con un usuario miembro de `guayacan_app` (nunca superusuario) y fija al inicio de cada transacción
`app.predio_id`, `app.usuario_id` y, si actúa un agente, `app.agente_id`.

## Vistas y seguridad por filas

Toda vista se crea `with (security_invoker = true)`. Sin esa opción la vista corre con los permisos de su dueño
(`postgres`, que se salta la seguridad por filas) y mezcla los datos de todas las fincas. La prueba
`backend/guayacan/tests/test_vistas_por_finca.py` falla si una vista nueva no la tiene.

| Vista | security_invoker | Desde |
| --- | --- | --- |
| `inventario.v_alertas_vencimiento`, `comercial.v_catalogo_disponible`, `comercial.v_trazabilidad_lote`, `comercial.v_cartera`, `ambiental.v_indicadores` | Sí | v4 |
| `adopcion.v_tablero` | Sí | Migración 010 |
| `agenda.v_agenda_dia`, `agenda.v_en_sitio` | Sí | Migración 012 |
| `crm.v_campanas`, `crm.v_embudo`, `crm.v_proyeccion_ventas` | Sí | Migración 012 |
| `cumplimiento.v_granja_biosegura` (la consulta PRO-01 al ingresar cada lote) | Sí | Migración 012 |
| `documental.v_vigentes` | Sí | Migración 012 |
| `estrategia.v_matriz_lineas`, `estrategia.v_retorno_iniciativas` | Sí | Migración 012 |
| `formacion.v_satisfaccion` | Sí | Migración 012 |
| `personal.v_carga_semanal`, `personal.v_productividad` | Sí | Migración 012 |
| `proyectos.v_tablero`, `seguridad.v_tablero`, `seguros.v_por_vencer` | Sí | Migración 012 |

## Migraciones

Una base nueva se carga con los archivos de arriba, que ya traen todos los cambios. Una base cargada antes recibe los
cambios con los archivos de `migraciones/`, en orden (`001` a `012`); cada uno se puede correr más de una vez. En
Windows, con PowerShell, fije `PGCLIENTENCODING=UTF8` antes de correrlos: si no, psql guarda mal las tildes.

## Tareas programadas que necesita la base (Celery Beat)

| Tarea | Frecuencia | Función |
| --- | --- | --- |
| Marcar vencidos | Diaria | `inventario.marcar_vencidos()` |
| Mora de clientes | Diaria | `comercial.actualizar_mora()` |
| Pedidos recurrentes | Diaria | `comercial.generar_pedidos_recurrentes()` |
| Borrar clips vencidos | Diaria | `iot.depurar_clips()` |
| Particiones | Mensual | `nucleo.mantener_particiones()` |
| Tareas del día | Diaria | `personal.generar_tareas_del_dia()` |
| Habilitaciones vencidas | Diaria | `formacion.actualizar_habilitaciones()` |
| Órdenes de mantenimiento | Diaria | `activos.generar_ordenes_trabajo()` |
| Expedientes de cumplimiento | Diaria | `cumplimiento.evaluar_expediente(id)` |
| Revisión de copias | Diaria | `seguridad.revisar_copias()` |
| Índice de seguros paramétricos | Diaria (si está encendido) | `seguros.vigilar_indice(id)` |
| Depreciación | Mensual | `activos.depreciar_mes(mes)` |
| Indicadores financieros | Mensual | `finanzas.calcular_indicadores(desde, hasta)` |
| Valor ganado | Semanal por proyecto | `proyectos.calcular_valor_ganado(id)` |
| Abandono de adopciones (Apéndice A) | Diaria | `adopcion.marcar_abandono()` |
| Cuotas y madurez de adopciones (Apéndice A) | Mensual, día 1 | `adopcion.generar_cuotas()`, `adopcion.marcar_madurez()` |

## Cambiar el modelo

Edita `generador/modelo.py` o `generador/reglas_negocio.sql` y ejecuta desde `specs/modelo-datos/generador`:

```
python generar.py ..\..\..
python mongo.py ..\..\..
python excel_diccionario.py
python excel_apis.py
```
