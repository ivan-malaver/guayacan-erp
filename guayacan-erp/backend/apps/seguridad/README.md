# App `seguridad` (SEG)

Doble factor, sesiones, intentos de acceso, detector de ataques, señuelos, bloqueos, alertas, incidentes, pruebas y copias de seguridad.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| SEG-01 | Iniciar sesión con doble factor | 1 | Usuario autenticado | `POST /api/v1/auth/token/`<br>`POST /api/v1/auth/doble-factor/verificar/` |
| SEG-02 | Inscribir el segundo factor y recuperar la contraseña | 1 | Usuario autenticado | `POST /api/v1/auth/doble-factor/inscribir/`<br>`POST /api/v1/auth/recuperar/` |
| SEG-03 | Detectar y bloquear ataques de acceso | 1 | Tareas programadas | CRUD |
| SEG-04 | Atender una alerta o un incidente de seguridad | 1 | Administrador | `GET /api/v1/seguridad/tablero/` |
| SEG-05 | Revocar sesiones y levantar bloqueos | 1 | Administrador | `POST /api/v1/seguridad/sesiones/{id}/revocar/`<br>`POST /api/v1/seguridad/bloqueos/{id}/levantar/` |
| SEG-06 | Registrar una corrida de pruebas | 1 | Integración continua | `POST /api/v1/seguridad/ejecuciones-prueba/` |
| SEG-07 | Verificar copias de seguridad y restauraciones | 1 | Tareas programadas, Administrador | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `seguridad.factor_autenticacion` | `FactorAutenticacion` | `/api/v1/seguridad/factores-autenticacion/` | Segundo factor del usuario: app TOTP o llave de acceso (passkey/WebAuthn). Obligatorio para administrador y contador. El secreto vive en el gestor de secretos. |
| `seguridad.sesion_usuario` | `SesionUsuario` | `/api/v1/seguridad/sesiones-usuario/` | Sesión iniciada: método, IP, dispositivo y vencimiento; se puede revocar en bloque ante un incidente. |
| `seguridad.intento_acceso` | `IntentoAcceso` | `/api/v1/seguridad/intentos-acceso/` | Cada intento de inicio de sesión, exitoso o no (solo inserción). Alimenta el detector de ataques. |
| `seguridad.regla_deteccion` | `ReglaDeteccion` | `/api/v1/seguridad/reglas-deteccion/` | Regla del detector de ataques: cuántos hechos en cuánto tiempo, severidad y respuesta automática. |
| `seguridad.bloqueo` | `Bloqueo` | `/api/v1/seguridad/bloqueos/` | Bloqueo temporal de una cuenta o una IP por una regla o una persona. |
| `seguridad.senuelo` | `Senuelo` | `/api/v1/seguridad/senuelos/` | Señuelo para intrusos (cuenta, llave de API o URL que nadie legítimo usa): tocarlo dispara una alerta crítica y bloquea la IP. |
| `seguridad.alerta_seguridad` | `AlertaSeguridad` | `/api/v1/seguridad/alertas-seguridad/` | Hecho sospechoso detectado por las reglas, el WAF, la pasarela o la base (fuerza bruta, escalada de permisos, exportación masiva, señuelo). Solo inserción salvo su atención. |
| `seguridad.incidente` | `Incidente` | `/api/v1/seguridad/incidentes/` | Incidente de seguridad con su atención; si compromete datos personales se reporta a la SIC (Ley 1581). |
| `seguridad.ejecucion_prueba` | `EjecucionPrueba` | `/api/v1/seguridad/ejecuciones-prueba/` | Módulo de pruebas: cada corrida de pruebas (unitarias, de reglas de la base, extremo a extremo, carga, dependencias, SAST, DAST, pentest, restauración de copias) con su resultado. |
| `seguridad.copia_seguridad` | `CopiaSeguridad` | `/api/v1/seguridad/copias-seguridad/` | Copia cifrada de la base o los archivos (regla 3-2-1) y su prueba mensual de restauración. |

## Reglas de la base que protegen esta app

- `seguridad.cuenta_bloqueada()`
- `seguridad.ip_bloqueada()`
- `seguridad.proteger_alerta()`
- `seguridad.registrar_intento()`
- `seguridad.requiere_doble_factor()`
- `seguridad.revisar_copias()`
- `seguridad.revocar_sesiones()`
- `seguridad.validar_sesion()`
- `seguridad.vigilar_exportaciones()`
- `solo inserción`

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
