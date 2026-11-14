# App `finanzas` (FIN)

Plan de cuentas (PUC), centros de costo, comprobantes y movimientos contables.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| FIN-01 | Configurar el plan de cuentas y los centros de costo | 1 | Contador | CRUD |
| FIN-02 | Contabilizar un comprobante | 1 | Contador | CRUD |
| FIN-03 | Anular un comprobante o registrar una nota | 1 | Contador | CRUD |
| FIN-04 | Cerrar el periodo contable | 1 | Contador | `POST /api/v1/finanzas/periodos-contable/{id}/cerrar/` |
| FIN-05 | Clasificar costos y distribuirlos por actividades | 2 | Contador | CRUD |
| FIN-06 | Elaborar y aprobar el presupuesto maestro | 2 | Contador, Familia | CRUD |
| FIN-07 | Generar los estados financieros | 2 | Contador, Familia | `GET /api/v1/finanzas/estado-resultados/?desde=&hasta=&centro=`<br>`GET /api/v1/finanzas/balance/?hasta=` |
| FIN-08 | Calcular indicadores y consultar el tablero | 2 | Familia, Tareas programadas | `POST /api/v1/finanzas/indicadores/calcular/` |
| FIN-09 | Analizar estados: vertical, horizontal, fuentes y usos | 2 | Contador, Familia | `GET /api/v1/finanzas/analisis/?a=&b=`<br>`GET /api/v1/finanzas/fuentes-usos/?a=&b=` |
| FIN-10 | Calcular punto de equilibrio y palancas | 2 | Familia | `GET /api/v1/finanzas/palancas/?q=&p=&cv=&cf=&i=` |
| FIN-11 | Gestionar anticipos a proveedores | 2 | Contador | CRUD |
| FIN-12 | Emitir un informe de indicadores para crédito | 3 · `indicadores_credito` | Familia | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `finanzas.cuenta_contable` | `CuentaContable` | `/api/v1/finanzas/cuentas-contable/` | Plan Único de Cuentas (PUC) adaptado a la finca. |
| `finanzas.centro_costo` | `CentroCosto` | `/api/v1/finanzas/centros-costo/` | Unidad de negocio para medir rentabilidad (avícola, ovino-caprino, piscícola, ciclo corto, perennes, turismo, administración). |
| `finanzas.comprobante` | `Comprobante` | `/api/v1/finanzas/comprobantes/` | Documento contable (ingreso, egreso, nota, causación). Lo generan reglas a partir de ventas, compras y nómina; el agente contador solo sugiere. |
| `finanzas.movimiento_contable` | `MovimientoContable` | `/api/v1/finanzas/comprobantes/{id}/movimientos/` | Línea débito o crédito de un comprobante. |
| `finanzas.periodo_contable` | `PeriodoContable` | `/api/v1/finanzas/periodos-contable/` | Mes contable; un comprobante solo se contabiliza o anula si su mes está abierto. |
| `finanzas.clasificacion_costo` | `ClasificacionCosto` | `/api/v1/finanzas/clasificaciones-costo/` | Cómo se comporta cada cuenta de costo o gasto: elemento (MD, MOD, CIF, administración, ventas, financiero) y comportamiento (fijo, variable, semivariable, escalonado). Base del costeo variable y de las palancas. |
| `finanzas.actividad_costo` | `ActividadCosto` | `/api/v1/finanzas/actividades-costo/` | Actividad para costeo basado en actividades (ABC) con su inductor: horas de máquina, aves-día, jornales, m² regados. |
| `finanzas.asignacion_costo` | `AsignacionCosto` | `/api/v1/finanzas/asignaciones-costo/` | Reparto mensual de costos indirectos a los centros según el inductor consumido. |
| `finanzas.costo_estandar` | `CostoEstandar` | `/api/v1/finanzas/costos-estandar/` | Costo estándar por unidad de producto (materiales, mano de obra y CIF) para comparar contra el real. |
| `finanzas.presupuesto` | `Presupuesto` | `/api/v1/finanzas/presupuestos/` | Presupuesto maestro del año (operación y financiero), con versión y aprobación; puede ser base cero. Base para el informe al Fondo Emprender. |
| `finanzas.premisa_presupuesto` | `PremisaPresupuesto` | `/api/v1/finanzas/premisas-presupuesto/` | Premisas del presupuesto: inflación, salario mínimo, precio del concentrado, crecimiento del mercado, política de cartera. |
| `finanzas.presupuesto_detalle` | `PresupuestoDetalle` | `/api/v1/finanzas/presupuestos/{id}/detalles/` | Rubro del presupuesto por mes, centro de costo y cuenta, en la secuencia del presupuesto maestro (ventas, producción, materias primas, mano de obra, CIF, gastos, inversión, financiación, caja). |
| `finanzas.estado_financiero` | `EstadoFinanciero` | `/api/v1/finanzas/estados-financiero/` | Estado financiero generado y congelado (balance, resultados por costeo variable o absorbente, flujo de efectivo directo o indirecto), real o presupuestado. |
| `finanzas.indicador` | `Indicador` | `/api/v1/finanzas/indicadores/` | Catálogo de indicadores financieros y de gestión con su fórmula, meta y semáforo (liquidez, endeudamiento, rentabilidad, rotación, EBITDA, EVA, Altman, palancas, postura por ave…). |
| `finanzas.valor_indicador` | `ValorIndicador` | `/api/v1/finanzas/valores-indicador/` | Valor calculado de un indicador en un periodo, con meta y semáforo para el tablero del administrador. |
| `finanzas.anticipo_proveedor` | `AnticipoProveedor` | `/api/v1/finanzas/anticipos-proveedor/` | Pago adelantado a un proveedor: queda como saldo a favor y se descuenta en las compras siguientes; nunca queda negativo. No se reciben recargas de clientes. |
| `finanzas.aplicacion_anticipo` | `AplicacionAnticipo` | `/api/v1/finanzas/aplicaciones-anticipo/` | Descuento de un anticipo en una orden de compra. |
| `finanzas.reporte_indicadores` | `ReporteIndicadores` | `/api/v1/finanzas/reportes-indicadores/` | Informe de indicadores verificables para Finagro, bancos, gremios o certificadores, con autorización del titular y sin costos ni datos personales. |

## Reglas de la base que protegen esta app

- `finanzas.analisis_vertical_horizontal()`
- `finanzas.aplicar_anticipo()`
- `finanzas.balance_general()`
- `finanzas.calcular_indicadores()`
- `finanzas.distribuir_costos()`
- `finanzas.estado_resultados()`
- `finanzas.fuentes_usos()`
- `finanzas.palancas()`
- `finanzas.preparar_anticipo()`
- `finanzas.proteger_comprobante()`
- `finanzas.proteger_movimiento()`
- `finanzas.saldo()`
- `finanzas.validar_clasificacion()`
- `finanzas.validar_cuadre()`
- `finanzas.validar_presupuesto_detalle()`
- `finanzas.validar_reporte_indicadores()`

## Archivos de esta carpeta

| Archivo | Qué hace |
| --- | --- |
| `apps.py` | Registra la app en Django |
| `models.py` | Una clase por tabla (generado; no editar) |
| `serializers.py` | Convierte filas en JSON y valida el JSON recibido |
| `views.py` | Endpoints CRUD de cada tabla |
| `urls.py` | Rutas: acciones de los casos de uso (501 mientras se construyen) y CRUD |
| `services.py` | Una función por caso de uso, vacía, con los pasos para construirla |
| `tests/test_casos_de_uso.py` | Una prueba por caso de uso, marcada como pendiente |

## Cómo trabajar aquí

1. Lea la especificación del caso de uso en el documento técnico (pestaña de su grupo) o en `docs/casos-de-uso/`.
2. Quite el `skip` de su prueba en `tests/test_casos_de_uso.py` y escriba el flujo principal y los alternos.
3. Implemente la función de `services.py`; no repita en Python las reglas que ya están en la base.
4. Reemplace la ruta `PorConstruir` de `urls.py` por la vista real.
