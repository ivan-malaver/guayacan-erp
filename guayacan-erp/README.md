# GuayacanERP · Paquete v5.2 final

Plataforma ERP + CRM + IA de la finca El Guayacán de los Malaver (Pueblo Nuevo, Nilo, Cundinamarca).
La v5.2 (31 de octubre de 2026) es el paquete definitivo para trabajar en VS Code: une la v5 (diseño y base de datos),
la v5.1 (esqueleto del código y UML) y el Apéndice A (adopción de árboles y animales), con todas las correcciones y
**todo el código comentado en español** (qué hace, cómo lo hace y para qué).

## Por dónde empezar

1. **`INSTALAR.md`**: programas, librerías, base de datos, backend, frontend, servicios y primer envío a GitHub.
2. `docs/desarrollo/01_primer_dia.md`: comprobar que todo funciona y en qué orden leer el código.
3. `docs/desarrollo/02_construir_un_caso_de_uso.md`: el flujo de trabajo con un ejemplo completo.
4. `docs/desarrollo/04_archivos_de_configuracion.md`: para qué sirve cada archivo de configuración.
5. `docs/desarrollo/05_informe_de_verificacion.md`: qué se comprobó y qué falta comprobar en su PC.

## Cifras

| Elemento | Cantidad |
| --- | --- |
| Esquemas de PostgreSQL | 26 (25 de la v5 + `adopcion`) |
| Tablas | 254 (246 + 8 del Apéndice A) |
| Pruebas de reglas en la base | 339 (215 v5, 90 de regresión v4, 34 de adopción) |
| Apps de Django | 26, con modelos `managed=False`, serializers, vistas, rutas, servicios y pruebas |
| Casos de uso | 192 (177 + ADO-01 a ADO-15) |
| Acciones de API por construir | 102 (responden 501 con su caso de uso) |
| Módulos de la PWA (Angular) | 26, carga perezosa |
| Diagramas UML | 105 |

## Qué cambió en la v5.2

| Cambio | Detalle |
| --- | --- |
| Apéndice A integrado | Esquema `adopcion` (SQL y pruebas), app de Django `apps/adopcion`, módulo de Angular, casos de uso ADO en el catálogo, diagramas y documentos |
| Correcciones | Archivos dañados (`comercial/models.py`, `personal/models.py`, `proyectos/models.py`); `adopcion.seguimiento` con `dispositivo_captura_id`; valores permitidos del diccionario (Excel y Word); Django ahora lee el `.env` (python-dotenv) |
| Código comentado | Backend, apps generadas (por plantilla), servicios FastAPI, frontend, generadores, Docker, CI y scripts |
| Para VS Code y GitHub | `.gitignore` completo (entornos virtuales, `.env`, bases locales, `node_modules`, `entregables/`), `.gitattributes`, `.vscode/`, `scripts/cargar_base.ps1` y `.sh` |
| CI | Corre también las pruebas del Apéndice A y carga el apéndice antes de las pruebas del backend |
| Integridad | `huellas.json` + `verificar.py` para comprobar que nada se dañó al copiar |

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `backend/` | Django 5.2 + DRF (núcleo `guayacan/`, configuración `config/`, 26 apps en `apps/`) |
| `servicios/agentes/`, `servicios/iot/` | FastAPI: canales y agentes de IA; puente IoT |
| `frontend/` | Angular 20 PWA |
| `specs/` | Esquema SQL, datos iniciales, Apéndice A, MongoDB, diccionarios, generador y pruebas |
| `docs/` | Documento técnico en Markdown, ADR, UML, diagramas y guías de desarrollo |
| `scripts/` | Carga de la base y pruebas |
| `entregables/` | Manuales en Word, PDF y Excel (ignorada por Git: no se sube al repositorio) |

Lo que no se pudo verificar al armar el paquete: instalar las librerías (sin acceso a PyPI ni npm) y, por tanto,
`manage.py check`, pytest con Django y `ng build`. Sí se verificó: todo el Python compila, el TypeScript no tiene
errores de sintaxis, el JSON y el YAML son válidos, las 339 pruebas de la base pasan y el script de carga funciona.
La primera ejecución en su PC (o en la CI de GitHub) es la prueba que falta.

---

## Historial: paquete v5.1 · Inicio del desarrollo

Plataforma ERP + CRM + IA de la finca El Guayacán de los Malaver (Pueblo Nuevo, Nilo, Cundinamarca).
La v5.1 (29 de octubre de 2026) agrega a la v5 lo que el equipo necesita para empezar a construir: el documento
técnico con 101 diagramas UML y la especificación de los 177 casos de uso, y un esqueleto de repositorio sin lógica de
negocio para Django, FastAPI y Angular, con Docker y GitHub Actions.

## Por dónde empezar

1. `docs/desarrollo/01_primer_dia.md`: levantar la base, el backend y la PWA.
2. `docs/casos-de-uso/00_documento_tecnico.md` (o el Word y el PDF entregados aparte): arquitectura, modelo, convenciones y plan por sprints.
3. `docs/desarrollo/02_construir_un_caso_de_uso.md`: el flujo de trabajo con un ejemplo completo.

## Qué agrega la v5.1

| Carpeta | Contenido |
| --- | --- |
| `backend/` | Django + DRF: 25 apps (una por esquema) con 246 modelos `managed=False` generados, serializers, CRUD sin borrado, 92 acciones declaradas que responden 501 con su caso de uso, un método de servicio y una prueba pendiente por caso de uso; contexto de finca, errores de la base a HTTP, sincronización sin conexión, outbox, Celery Beat e ingreso con el detector de ataques |
| `servicios/agentes/`, `servicios/iot/` | FastAPI: webhooks firmados de Meta, orquestador y cliente MCP por construir; puente de lecturas IoT por lote |
| `frontend/` | Angular PWA: sesión, finca (X-Predio), cola sin conexión con UUIDv7 en IndexedDB, 25 módulos perezosos generados desde el catálogo |
| `.github/workflows/ci.yml` | Reglas de la base (las dos baterías), backend, servicios y frontend |
| `docs/uml/` | Los 101 diagramas (fuente, SVG y PNG) y sus generadores |
| `docs/casos-de-uso/` | El documento técnico y las 7 pestañas de casos de uso en Markdown |
| `docs/desarrollo/` | Primer día, cómo construir un caso de uso, cómo regenerar |
| `docs/manuales/GuayacanERP_Trazabilidad_v5.1.xlsx` | Casos de uso con actores, requerimientos, tablas, reglas, endpoints y pruebas; matrices de trazabilidad |

Lo que no se pudo verificar aquí: instalar las dependencias (sin acceso a PyPI ni npm) y, por tanto, correr
`manage.py check`, pytest con Django, `ng build` y la CI. Sí se verificó: el código compila y pasa ruff, el JSON y
YAML son válidos, y el SQL del contexto de finca, el ingreso y las 14 tareas programadas corrió como `guayacan_api`
sobre la base v5 en PostgreSQL 16. La primera ejecución de la CI es la prueba que falta.

---

## Historial: paquete v5 · Operación integral de la finca

Plataforma ERP + CRM + IA de la finca El Guayacán de los Malaver (Pueblo Nuevo, Nilo, Cundinamarca).
Versión 5 del diseño, 27 de octubre de 2026. Todo lo de aquí está verificado: el esquema (25 esquemas, 246 tablas) y los
datos iniciales cargan sin errores y pasan 305 pruebas de reglas de negocio (90 de regresión de la v4 y 215 nuevas).

## Qué trae

| Carpeta o archivo | Contenido |
| --- | --- |
| `docker-compose.yml`, `docker/postgres/Dockerfile`, `.env.ejemplo` | Entorno local: PostgreSQL 18 con PostGIS, pgvector y btree_gist, MongoDB 8 y Redis |
| `specs/modelo-datos/` | Esquema SQL v5, datos iniciales, colecciones MongoDB, diccionarios y el generador (ver su `LEEME.md`) |
| `specs/casos-prueba/` | `pruebas_reglas_v4.sql` (regresión), `pruebas_reglas_v5.sql` y el resultado de la última ejecución |
| `docs/adr/` | Decisiones de arquitectura 0002 a 0006 |
| `docs/arquitectura/patrones-de-diseno.md` | Qué patrón se usa dónde y por qué (sección 9: v5) |
| `docs/diagramas/` | Diagramas 01 a 20 y diagramas entidad-relación por esquema (Mermaid) |
| `docs/manuales/` | Diccionario de datos v5 y mapa de APIs v5 en Excel; arquitectura v5 con diccionario en Word y PDF; arquitectura v4 como base |

## Qué agrega la v5

| Módulo (esquema) | Para qué |
| --- | --- |
| `personal` | Tareas con evidencia, áreas de responsabilidad, matriz RACI, carné QR o NFC, jornada, cronogramas 24/7 con patrones, cobertura y disponibilidad |
| `nomina` | Prenómina desde contratos, tareas y jornadas; liquidación, prestaciones, PILA, exportación al contador, pagos con doble aprobación; nómina electrónica apagada |
| `formacion` | Cursos, evaluaciones, certificados y habilitaciones que permiten asignar tareas; necesidades, encuestas, quejas y apelaciones (ISO 21001) |
| `activos`, `documental` | Hoja de vida y mantenimiento de equipos, depreciación; documentos con versión aprobada y vencimiento |
| `cumplimiento`, `seguros` | Granja avícola biosegura (obligatoria), BPA, GLOBALG.A.P. e ISO 21001 apagadas; pólizas y avisos de siniestro |
| `seguridad` | Doble factor, detector de ataques, señuelos, bloqueos, alertas, incidentes, módulo de pruebas y copias |
| `crm`, `estrategia` | Captura de posibles clientes con autorización; nuevos mercados y productos evaluados con VPN, TIR, ROI y palancas; reinversión de utilidades |
| `agenda` | Cabañas y recursos sin cruces, visitas con pase QR y portería de personas y vehículos |
| `proyectos` | PMBOK 8: acta, interesados, EDT, ruta crítica, riesgos, cambios, líneas base y valor ganado |
| `finanzas` (ampliado) | Clasificación de costos, costeo variable y ABC, presupuesto maestro, estados, 30 indicadores, análisis vertical y horizontal |

## Cómo empezar (BLOQUE 1)

1. Copie `.env.ejemplo` como `.env` y cambie las claves.
2. Levante la base: `docker compose up -d --build postgres mongodb`.
3. Cargue el esquema, los datos iniciales y corra las dos baterías de pruebas, cada una sobre una base nueva
   (comandos en `specs/modelo-datos/LEEME.md`). La última línea debe decir `TODAS LAS PRUEBAS PASARON`.
4. Siga la hoja "Ruta manual" del mapa de APIs v5: proyecto Django, apps `nucleo` y `seguridad`, finca de práctica.

## Bloque sugerido para agregar al CLAUDE.md del proyecto

```
## Arquitectura (ADR 0002 a 0006)
- Django + DRF es el monolito: dueño de todas las tablas de PostgreSQL, una app por esquema (25 apps).
- FastAPI son servicios aparte: agentes y canales (MongoDB) e IoT (fase 4). Nunca escriben directo en PostgreSQL.
- La API se conecta con un usuario del rol guayacan_app y fija app.predio_id, app.usuario_id y app.agente_id en cada transacción.
- Las reglas críticas viven en la base (specs/modelo-datos/generador/reglas_negocio.sql); no se duplican en Python.
- Funciones que esperan decisión o equipo se encienden con nucleo.funcionalidad; no se borran ni se comentan.
- Ningún agente aprueba, paga, cierra nómina, publica cronogramas ni asigna tareas: la base lo impide con app.agente_id.
- Antes de cada commit: correr pruebas_reglas_v4.sql y pruebas_reglas_v5.sql, cada una sobre una base nueva.
```

## Decisiones vigentes

| Tema | Decisión |
| --- | --- |
| Base de datos | PostgreSQL 18 |
| Cadena de frío, crédito, permuta, cámaras térmicas, rostro, gemelo 3D, blockchain | Listos y apagados (v4) |
| Empleador, régimen, nómina electrónica | Régimen "por definir"; nómina electrónica apagada hasta confirmar con el contador |
| Pago de trabajadores | Salario, jornal, destajo y mixto conviven; el ERP calcula y exporta para el contador |
| Aprobación de tareas | Encargado y familia por permiso, y el responsable de cada área |
| Formación | Operarios y estudiantes; ISO 21001 apagada |
| Robot y dron | Interfaz lista, apagada |
| BPA y GLOBALG.A.P. | Normas cargadas, apagadas; granja avícola biosegura obligatoria y activa |
| Seguros | Módulo construido; paramétrico apagado |

## Pendiente de validar con la familia y el contador

- Monto que exige doble aprobación de pagos (supuesto 3.000.000), tasa de oportunidad para VPN y EVA (15 % anual) y tope de reinversión (30 %).
- Tarifas de nómina, jornada máxima, recargos y hora nocturna (cargados según Ley 2101 de 2021 y Ley 2466 de 2025).
- Cuarentena de aves para visitantes del galpón (supuesto 72 horas) con el veterinario.
- Lo pendiente de la v4: NTC 1240, temperaturas de la nevera, vida útil de productos y factores de emisión.
