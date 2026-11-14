# Servicios FastAPI

Servicios aparte del monolito. **Nunca escriben directo en PostgreSQL**: hablan con el ERP por su API o sus
herramientas MCP, con su propio token (ADR 0002).

| Servicio | Puerto | Para qué | Casos de uso |
| --- | --- | --- | --- |
| `agentes/` | 8100 | Webhooks de WhatsApp, Instagram, Messenger y TikTok; orquestador de los 14 agentes; cliente MCP; conversaciones en MongoDB | RED-01 a RED-06, IA-01 a IA-09, FOR-09 |
| `iot/` | 8200 | Puente entre la pasarela MQTT de la finca y el ERP (fase 4) | RIE-03, IOT-01 a IOT-09 |

```
cd servicios/agentes
python -m venv .venv && .venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload --port 8100
pytest
```

Lo que ya está: salud, verificación y recepción de webhooks con la firma HMAC de Meta, reenvío de lecturas por
lote. Lo que falta está descrito en `app/orquestador.py` y `app/cliente_mcp.py`.
