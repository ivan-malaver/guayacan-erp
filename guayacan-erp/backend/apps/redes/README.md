# App `redes` (RED)

Cuentas de redes sociales y publicaciones con su flujo de aprobación.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| RED-01 | Atender el mensaje de un cliente por un canal | 1 | Cliente | `POST /canales/whatsapp/webhook` |
| RED-02 | Escalar una conversación a una persona | 1 | Vendedor | CRUD |
| RED-03 | Enviar un mensaje saliente dentro de las reglas del canal | 1 | Vendedor | CRUD |
| RED-04 | Proponer y aprobar una publicación | 2 | Administrador | CRUD |
| RED-05 | Producir una pieza audiovisual con autorización de imagen | 2 · `videos_promocionales` | Administrador | CRUD |
| RED-06 | Mantener plantillas y políticas de canal | 1 | Administrador | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `redes.cuenta_red` | `CuentaRed` | `/api/v1/redes/cuentas-red/` | Cuenta de la finca en un canal de mensajería o red social; las credenciales van en el gestor de secretos, no aquí. |
| `redes.publicacion` | `Publicacion` | `/api/v1/redes/publicaciones/` | Contenido para redes: lo redacta el agente de redes y se publica solo con aprobación. |
| `redes.politica_canal` | `PoliticaCanal` | `/api/v1/redes/politicas-canal/` | Reglas de cada canal según su proveedor (Meta, TikTok): ventana para responder, quién inicia, límites y cobro. Se actualiza cuando cambian las políticas. |
| `redes.plantilla_mensaje` | `PlantillaMensaje` | `/api/v1/redes/plantillas-mensaje/` | Plantilla aprobada por Meta para escribir fuera de la ventana de 24 horas de WhatsApp (confirmaciones, recordatorios, promociones). |
| `redes.mensaje_saliente` | `MensajeSaliente` | `/api/v1/redes/mensajes-salientes/` | Registro de control de cada mensaje que la finca envía por un canal: si estaba dentro de la ventana, qué plantilla usó, qué consentimiento lo permitió y cuánto costó. |
| `redes.pieza_audiovisual` | `PiezaAudiovisual` | `/api/v1/redes/piezas-audiovisual/` | Video, time-lapse o foto preparada para redes: la IA propone guion y texto, FFmpeg arma el archivo y una persona aprueba. Si aparecen personas, todas deben tener consentimiento de imagen. |
| `redes.pieza_persona` | `PiezaPersona` | `/api/v1/redes/piezas-persona/` | Persona que aparece en una pieza audiovisual y su consentimiento de imagen. |

## Reglas de la base que protegen esta app

- `herramientas MCP de solo lectura y borrador`
- `redes.validar_pieza()`
- `redes.verificar_envio()`
- `solo una persona aprueba contenido`
- `ventana del canal`

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
