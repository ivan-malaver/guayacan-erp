# App `crm` (CRM)

Posibles clientes (personas y empresas), formularios de captura con autorización de datos, campañas, interacciones y oportunidades.

## Casos de uso

| ID | Caso de uso | Fase | Actores | Endpoints de acción |
| --- | --- | --- | --- | --- |
| CRM-01 | Capturar un posible cliente con autorización | 2 | Posible cliente, Vendedor | `POST /api/v1/crm/captura/{formulario}/` |
| CRM-02 | Gestionar segmentos y campañas | 2 | Vendedor, Administrador | CRUD |
| CRM-03 | Registrar interacciones y avanzar el embudo | 2 | Vendedor | CRUD |
| CRM-04 | Calificar los prospectos | 2 | Tareas programadas, Vendedor | `POST /api/v1/crm/prospectos/{id}/calificar/` |
| CRM-05 | Convertir un prospecto en cliente | 2 | Vendedor | `POST /api/v1/crm/prospectos/{id}/convertir/` |
| CRM-06 | Gestionar oportunidades y proyectar ventas | 2 | Vendedor, Familia | `GET /api/v1/crm/embudo/` |

## Tablas

| Tabla | Modelo | Ruta CRUD | Qué guarda |
| --- | --- | --- | --- |
| `crm.segmento` | `Segmento` | `/api/v1/crm/segmentos/` | Segmento de mercado (hogares, tiendas, restaurantes, hoteles, colegios, exportadores) con sus criterios: base de la palanca de mercadeo. |
| `crm.campana` | `Campana` | `/api/v1/crm/campanas/` | Campaña para captar clientes: canal, segmento, presupuesto, costo real y conversiones (costo por cliente nuevo). |
| `crm.formulario_captura` | `FormularioCaptura` | `/api/v1/crm/formularios-captura/` | Formulario para registrar posibles clientes (web, QR en ferias, WhatsApp) con su texto de autorización de datos y finalidad. |
| `crm.prospecto` | `Prospecto` | `/api/v1/crm/prospectos/` | Posible cliente, persona o empresa. No se le escribe sin autorización; al comprar se convierte en tercero y cliente. |
| `crm.contacto_empresa` | `ContactoEmpresa` | `/api/v1/crm/contactos-empresa/` | Persona de contacto dentro de una empresa prospecto (compras, chef, administrador), con su propia autorización. |
| `crm.interaccion` | `Interaccion` | `/api/v1/crm/interacciones/` | Contacto con un prospecto o cliente (llamada, WhatsApp, visita, degustación, feria) y su próximo paso. |
| `crm.oportunidad` | `Oportunidad` | `/api/v1/crm/oportunidades/` | Negocio posible con un prospecto o cliente: productos, valor, probabilidad y fecha de cierre (proyección del embudo). |

## Reglas de la base que protegen esta app

- `crm.calificar()`
- `crm.convertir_prospecto()`
- `crm.v_campanas`
- `crm.v_embudo`
- `crm.v_proyeccion_ventas`
- `crm.validar_interaccion()`
- `crm.validar_prospecto()`

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
