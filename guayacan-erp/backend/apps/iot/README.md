# App `iot` (IOT)

Red local de la finca: dispositivos, sensores, actuadores, reglas, seguridad perimetral y cámaras (fase 4, con diseño listo desde ya).

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| IOT-01 | Registrar dispositivos, sensores y actuadores | 4 | Administrador | CRUD |
| IOT-02 | Recibir lecturas de sensores | 4 | Pasarela IoT local | `MQTT finca/<dispositivo>/<sensor>` |
| IOT-03 | Accionar un actuador a mano | 4 | Encargado de finca | `POST /api/v1/iot/comandos/` |
| IOT-04 | Armar y desarmar la alarma por zonas | 4 · `seguridad_perimetral` | Encargado de finca, Portería | `POST /api/v1/iot/zonas-seguridad/{id}/estado/` |
| IOT-05 | Atender un evento de seguridad perimetral | 4 · `seguridad_perimetral` | Encargado de finca, Portería | CRUD |
| IOT-06 | Gestionar credenciales de acceso a puertas | 4 | Administrador | CRUD |
| IOT-07 | Conservar o depurar clips de cámaras | 4 · `camaras` | Tareas programadas, Administrador | CRUD |
| IOT-08 | Planear y ejecutar una misión de dron o robot | 4 · `dron_monitoreo` | Encargado de finca, Administrador | `POST /api/v1/iot/misiones-robot/{id}/aprobar/` |
| IOT-09 | Cortar cargas con batería baja | 4 | Pasarela IoT local | CRUD |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `iot.dispositivo` | `Dispositivo` | `/api/v1/iot/dispositivos/` | Equipo físico de la red local de la finca (ESP32, PLC, estación meteorológica) o la pasarela que la coordina. Los nodos hablan con la pasarela por MQTT local; la pasarela sincroniza con la nube cuando hay internet. |
| `iot.sensor` | `Sensor` | `/api/v1/iot/sensores/` | Sensor de un dispositivo (humedad de suelo, nivel de tanque, caudal, temperatura, movimiento, puerta, humo, gas). |
| `iot.actuador` | `Actuador` | `/api/v1/iot/actuadores/` | Elemento que el sistema puede accionar (electroválvula, bomba, relé, sirena, reflector, cerradura, cortina, extractor). |
| `iot.lectura` | `Lectura` | `/api/v1/iot/lecturas/` | Medición de un sensor, particionada por mes (o hipertabla si se usa TimescaleDB); sin columnas de auditoría por volumen. La pasarela guarda las lecturas mientras no hay internet y las sube después. |
| `iot.regla_automatizacion` | `ReglaAutomatizacion` | `/api/v1/iot/reglas/` | Regla determinista que acciona un actuador (ej. abrir V-03 si humedad < 30 % y tanque > 40 %). Se ejecuta en la pasarela local, así funciona sin internet. La IA puede sugerir reglas pero no activarlas. |
| `iot.comando_actuador` | `ComandoActuador` | `/api/v1/iot/comandos/` | Orden manual o automática a un actuador (abrir o cerrar una válvula), con su resultado. Funciona desde la red local aunque no haya internet. |
| `iot.zona_seguridad` | `ZonaSeguridad` | `/api/v1/iot/zonas-seguridad/` | Área vigilada (perímetro, galpón, bodega, acceso) con su estado de alarma; las reglas corren en la pasarela local. |
| `iot.cambio_estado_alarma` | `CambioEstadoAlarma` | `/api/v1/iot/cambios-estado-alarma/` | Historial de cambios de estado de la alarma (solo inserción). |
| `iot.credencial_acceso` | `CredencialAcceso` | `/api/v1/iot/credenciales-acceso/` | Credencial para abrir una puerta: PIN, tarjeta RFID o rostro. El rostro exige autorización expresa de biometría y su plantilla solo vive cifrada en la pasarela local, nunca en la nube. |
| `iot.camara` | `Camara` | `/api/v1/iot/camaras/` | Cámara de la finca: graba en la pasarela local por movimiento y sube solo clips elegidos. |
| `iot.evento_seguridad` | `EventoSeguridad` | `/api/v1/iot/eventos-seguridad/` | Hecho de seguridad detectado (intrusión, puerta, humo, gas, acceso): lo publica la pasarela, aunque no haya internet, y queda para su atención (solo inserción salvo la atención). |
| `iot.clip_video` | `ClipVideo` | `/api/v1/iot/clipes-video/` | Clip grabado por una cámara: los de seguridad se borran al vencer su retención; los marcados para redes pasan a una pieza audiovisual. |
| `iot.mision_robot` | `MisionRobot` | `/api/v1/iot/misiones-robot/` | Misión de un dron de monitoreo o de un robot de campo en piloto: una persona la aprueba; el robot opera solo en zonas sin personas y con parada de emergencia probada. |
| `iot.prioridad_carga` | `PrioridadCarga` | `/api/v1/iot/prioridades-carga/` | Prioridad de cada carga eléctrica: con batería baja se cortan primero las no esenciales; alarma, nevera y agua de animales van primero. |

## Reglas de la base que protegen esta app

- `biometría exige autorización expresa`
- `ck modo_falla`
- `inventario.evaluar_excursion()`
- `iot.cambiar_estado_alarma()`
- `iot.cargas_a_cortar()`
- `iot.depurar_clips()`
- `iot.validar_mision()`
- `solo se registra la atención`

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
