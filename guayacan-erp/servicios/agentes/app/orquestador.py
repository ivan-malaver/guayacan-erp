"""Orquestador de agentes (por construir con LangGraph y LiteLLM; decisión en docs/adr/0002).

QUÉ HARÁ (casos de uso RED-01, RED-02, IA-02)
1. encolar(): guarda el mensaje crudo en MongoDB (colección mensajes) y lo pone en Redis Streams.
2. Un trabajador lo toma, identifica al cliente (o crea el prospecto con su autorización, CRM-01) y elige
   el agente adecuado (asesor, vendedor, guía...).
3. El agente consulta el ERP solo con herramientas MCP (cliente_mcp.py). Lo que exige una decisión va a la
   bandeja de aprobaciones (ia.solicitud_aprobacion) y nunca se ejecuta directo.
4. Si no sabe responder o el cliente lo pide, escala a una persona (ia.escalamiento).
5. Registra el consumo (ia.consumo_ia) y respeta el límite diario de gasto del agente (IA-06).

POR QUÉ UNA COLA
Meta exige responder el webhook en segundos; pensar la respuesta con IA puede tardar más. Por eso el webhook
solo encola y otro proceso hace el trabajo pesado.
"""


class Orquestador:
    async def encolar(self, canal: str, cuerpo: bytes) -> None:
        """Recibe un mensaje entrante del canal indicado. Por construir."""
        # Por construir: guardar en MongoDB y publicar en Redis Streams ('guayacan.mensajes_entrantes').
        return None
