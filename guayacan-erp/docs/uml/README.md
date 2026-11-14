# Diagramas UML de GuayacanERP v5.2

105 diagramas (101 de la v5 y 4 del Apéndice A), cada uno con su fuente (`.dot` para Graphviz o `.mmd` para Mermaid), su `.svg` y su `.png`.

| Carpeta | Diagramas | Tipo UML |
| --- | --- | --- |
| `casos-uso/` | 27: actores humanos, agentes de IA y uno por módulo (25) | Casos de uso |
| `clases/` | 34: modelo de dominio por módulo (los grandes en dos partes) | Clases |
| `paquetes/` | 1: dependencias entre los 25 módulos de la v5 (el módulo 26, adopción, tiene sus diagramas en `adopcion/`) | Paquetes |
| `arquitectura/` | 3: componentes, despliegue y capas de una app | Componentes y despliegue |
| `secuencia/` | 15: SQ01 a SQ15, las interacciones clave | Secuencia |
| `estados/` | 17: ST01 a ST17, ciclo de vida de las entidades con estado | Máquina de estados |
| `actividad/` | 4: AC01 a AC04, procesos programados y de mejora | Actividad |
| `adopcion/` | 4 del Apéndice A: casos de uso ADO, clases, secuencia de compra y estados del bien adoptado | Varios |
| `fuentes/` | Catálogo de casos de uso y generadores (diagramas, apps de Django, rutas de Angular) | — |

Los diagramas de clases muestran las tablas como clases con sus atributos y relaciones; las relaciones con
`nucleo.usuario` se omiten fuera de núcleo y seguridad para que se lean. El modelo físico completo está en
`docs/diagramas/er_*.mmd` y en el diccionario de datos.
