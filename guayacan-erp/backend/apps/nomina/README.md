# App `nomina` (NOM)

Conceptos, periodos, novedades, liquidación, prestaciones, PILA, nómina electrónica (apagada) y pagos con doble aprobación.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| NOM-01 | Configurar conceptos y tarifas de nómina | 2 | Contador | CRUD |
| NOM-02 | Preparar la prenómina | 2 | Contador, Encargado de finca | `POST /api/v1/nomina/periodos/{id}/prenomina/` |
| NOM-03 | Registrar novedades manuales | 2 | Contador | CRUD |
| NOM-04 | Liquidar la nómina | 2 | Contador | `POST /api/v1/nomina/periodos/{id}/liquidar/` |
| NOM-05 | Cerrar el periodo de nómina | 2 | Familia, Contador | `POST /api/v1/nomina/periodos/{id}/cerrar/` |
| NOM-06 | Preparar y aprobar los pagos de nómina | 2 | Contador, Familia | CRUD |
| NOM-07 | Generar la PILA y exportar al contador | 2 | Contador | `GET /api/v1/nomina/periodos/{id}/pila/`<br>`GET /api/v1/nomina/periodos/{id}/exportar/?formato=` |
| NOM-08 | Transmitir la nómina electrónica | 2 · `nomina_electronica` | Contador | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `nomina.concepto_nomina` | `ConceptoNomina` | `/api/v1/nomina/conceptos-nomina/` | Concepto de la nómina (salario, auxilio, horas extra, recargos, jornal, destajo, deducciones, aportes). La tarifa vive en nucleo.parametro, nunca en el código. |
| `nomina.periodo_nomina` | `PeriodoNomina` | `/api/v1/nomina/periodos-nomina/` | Periodo de pago. Cerrado no se edita; las correcciones van como nota de ajuste. Cierre con doble aprobación y nunca por un agente. |
| `nomina.novedad` | `Novedad` | `/api/v1/nomina/novedades/` | Hecho que se paga o descuenta en el periodo: salario fijo, jornales y destajo de tareas aprobadas, horas extra, ausencias, préstamos. |
| `nomina.liquidacion` | `Liquidacion` | `/api/v1/nomina/liquidaciones/` | Resultado del periodo para un trabajador: devengado, deducciones y neto. |
| `nomina.liquidacion_detalle` | `LiquidacionDetalle` | `/api/v1/nomina/liquidaciones/{id}/detalles/` | Línea de la liquidación por concepto. |
| `nomina.provision_prestacion` | `ProvisionPrestacion` | `/api/v1/nomina/provisiones-prestacion/` | Provisión mensual de cesantías, intereses, prima y vacaciones. |
| `nomina.documento_nomina_electronica` | `DocumentoNominaElectronica` | `/api/v1/nomina/documentos-nomina-electronica/` | Documento soporte de pago de nómina electrónica (uno por trabajador al mes). Se transmite por el servicio gratuito de la DIAN o un proveedor autorizado; se enciende con nomina_electronica. |
| `nomina.planilla_pila` | `PlanillaPila` | `/api/v1/nomina/planillas-pila/` | Archivo de la planilla de seguridad social para el operador de la PILA; el pago lo hace una persona. |
| `nomina.pago_nomina` | `PagoNomina` | `/api/v1/nomina/pagos-nomina/` | Pago de una liquidación (transferencia, Bre-B o efectivo). Lo prepara una persona y lo aprueba otra; nadie aprueba su propio pago. |
| `nomina.exportacion_nomina` | `ExportacionNomina` | `/api/v1/nomina/exportaciones-nomina/` | Archivo para el contador cuando lleva la nómina en su propio programa. |

## Reglas de la base que protegen esta app

- `nomina.concepto()`
- `nomina.liquidar()`
- `nomina.marcar_pagada()`
- `nomina.preparar_prenomina()`
- `nomina.proteger_detalle_periodo()`
- `nomina.proteger_periodo()`
- `nomina.validar_documento_electronico()`
- `nomina.validar_novedad()`
- `nomina.validar_pago()`

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
