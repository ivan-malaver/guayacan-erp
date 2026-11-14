"""Cliente de las herramientas MCP del ERP (por construir).

QUÉ ES MCP
Model Context Protocol: una forma estándar de que un agente de IA pida acciones a un sistema. El ERP publica
una lista de «herramientas» (funciones) y el agente solo puede usar esas.

SEGURIDAD
Cada agente tiene su usuario técnico y su token. Con ese token el ERP fija app.agente_id y solo expone las
herramientas ligadas al agente en ia.agente_herramienta (mínimo privilegio, IA-01). Las herramientas son de
lectura o de propuesta: consultar_disponibilidad, consultar_precio, crear_pedido_borrador, proponer_precio,
buscar_conocimiento, escalar_a_persona. Ninguna aprueba, paga ni publica.
"""


class ClienteMCP:
    def __init__(self, url: str, token_agente: str):
        # url: dirección del servidor MCP del ERP; token_agente: token del usuario técnico del agente
        self.url, self.token = url, token_agente

    async def llamar(self, herramienta: str, argumentos: dict) -> dict:
        """Llama una herramienta del ERP y devuelve su resultado. Por construir."""
        raise NotImplementedError(f'Herramienta MCP {herramienta}: por construir')
