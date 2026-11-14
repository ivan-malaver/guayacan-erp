# App `produccion` (PRO)

Producción animal (aves, ovinos, caprinos, peces, abejas, lombrices) y agrícola (siembras, labores, cosechas, suelo).

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| PRO-01 | Registrar el ingreso de un lote de animales | 1 | Encargado de finca, Operario de campo | CRUD |
| PRO-02 | Registrar la postura diaria y clasificar el huevo | 1 | Operario de campo | CRUD |
| PRO-03 | Registrar alimentación, pesajes y eventos sanitarios | 1 | Operario de campo | CRUD |
| PRO-04 | Registrar eventos reproductivos de ovinos y caprinos | 1 | Operario de campo | CRUD |
| PRO-05 | Registrar una siembra y sus labores culturales | 1 | Operario de campo, Encargado de finca | CRUD |
| PRO-06 | Registrar una cosecha y su destino | 1 | Operario de campo | CRUD |
| PRO-07 | Registrar un análisis de suelo y su recomendación | 1 | Encargado de finca | CRUD |
| PRO-08 | Registrar bioseguridad e inocuidad | 1 | Operario de campo | CRUD |
| PRO-09 | Producir abono en lombricultivo o compostera | 1 | Operario de campo | CRUD |
| PRO-10 | Medir la calidad del agua de los estanques | 1 | Operario de campo | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `produccion.especie` | `Especie` | `/api/v1/produccion/especies/` | Catálogo de especies animales que maneja la finca. |
| `produccion.lote_animal` | `LoteAnimal` | `/api/v1/produccion/lotes-animal/` | Grupo de animales que entra junto y se maneja junto (un lote de 100 gallinas, un ciclo de 1.000 alevinos, un rebaño). |
| `produccion.animal` | `Animal` | `/api/v1/produccion/animales/` | Animal identificado individualmente (ovinos y caprinos), con su genealogía. |
| `produccion.registro_postura` | `RegistroPostura` | `/api/v1/produccion/registros-postura/` | Huevos recogidos por día y por lote; las categorías por peso se registran en clasificacion_postura. |
| `produccion.registro_alimentacion` | `RegistroAlimentacion` | `/api/v1/produccion/registros-alimentacion/` | Alimento suministrado a un lote, distinguiendo lo comprado de lo producido en la finca (base para medir el ahorro). |
| `produccion.evento_sanitario` | `EventoSanitario` | `/api/v1/produccion/eventos-sanitario/` | Vacunas, desparasitaciones, tratamientos, revisiones y muertes. |
| `produccion.registro_pesaje` | `RegistroPesaje` | `/api/v1/produccion/registros-pesaje/` | Pesos de animales o muestras de un lote (corderos, cabritos, tilapia). |
| `produccion.evento_reproductivo` | `EventoReproductivo` | `/api/v1/produccion/eventos-reproductivo/` | Montas, partos, abortos y destetes de ovinos y caprinos. |
| `produccion.calidad_agua_estanque` | `CalidadAguaEstanque` | `/api/v1/produccion/calidad-agua/` | Mediciones del agua de los estanques de peces. |
| `produccion.cultivo` | `Cultivo` | `/api/v1/produccion/cultivos/` | Catálogo de cultivos (plátano, cacao, aguacate papelillo, maíz, frijol, calabacín, forrajes). |
| `produccion.siembra` | `Siembra` | `/api/v1/produccion/siembras/` | Una siembra en una zona: cuántas plantas se sembraron y cuántas siguen vivas (ej. 5.000 plátanos previstos, 600 vivos). |
| `produccion.labor_cultural` | `LaborCultural` | `/api/v1/produccion/labores-cultural/` | Trabajo hecho a una siembra: encalado, fertilización, deshierbe, control de plagas, poda, resiembra. |
| `produccion.cosecha` | `Cosecha` | `/api/v1/produccion/cosechas/` | Producto cosechado y a dónde se fue (venta, alimento para los animales, semilla o pérdida). |
| `produccion.analisis_suelo` | `AnalisisSuelo` | `/api/v1/produccion/analisis-suelo/` | Resultados de laboratorio del suelo de una zona y la recomendación de encalado. |
| `produccion.categoria_huevo` | `CategoriaHuevo` | `/api/v1/produccion/categorias-huevo/` | Categorías comerciales del huevo por rango de peso, con la norma de la que salen (verificar NTC 1240 vigente). |
| `produccion.clasificacion_postura` | `ClasificacionPostura` | `/api/v1/produccion/clasificaciones-postura/` | Huevos de un registro de postura por categoría; el método dice si se clasificó con báscula, a mano o con visión artificial. |
| `produccion.registro_bioseguridad` | `RegistroBioseguridad` | `/api/v1/produccion/registros-bioseguridad/` | Registros de bioseguridad e inocuidad que pide el ICA: limpieza, desinfección, plagas, visitas, cambio de cama y agua. |
| `produccion.produccion_abono` | `ProduccionAbono` | `/api/v1/produccion/producciones-abono/` | Humus y compost producidos por el lombricultivo o la compostera; al entrar a bodega crean un lote vendible. |

## Reglas de la base que protegen esta app

- `ck labor por robot exige misión`
- `comercial.registrar_huella()`
- `cumplimiento.evaluar_expediente()`
- `cumplimiento.v_granja_biosegura`
- `inventario.entrada_inicial()`
- `produccion.validar_clasificacion()`

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
