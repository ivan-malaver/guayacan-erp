"""Servicio de agentes (FastAPI): recibe los mensajes de los canales, los pasa al orquestador y expone utilidades.

QUÉ HACE
- Recibe los webhooks de WhatsApp, Instagram, Messenger y TikTok (los mensajes que escriben los clientes).
- Verifica que el aviso venga de verdad de Meta (firma HMAC) antes de leerlo.
- Deja el trabajo en una cola para responder rápido (Meta exige respuesta en pocos segundos).

QUÉ NO HACE (por diseño)
Nunca escribe en PostgreSQL. Lee y propone a través de las herramientas MCP del ERP con el token del agente
(app.agente_id), y la base impide que un agente apruebe, pague o publique. Las conversaciones se guardan en MongoDB.

Arranque en su PC (desde servicios/agentes, con su venv activo):  uvicorn app.main:app --reload --port 8100
Documentación interactiva: http://localhost:8100/docs
"""
from fastapi import FastAPI, Header, HTTPException, Request, Response

from .config import ajustes
from .firmas import firma_meta_valida
from .orquestador import Orquestador

# La aplicación web; FastAPI genera sola la documentación en /docs
app = FastAPI(title='GuayacanERP · Agentes', version='0.1.0')
orquestador = Orquestador()


@app.get('/salud')
def salud():
    """Comprobación de vida: Docker y el monitoreo llaman aquí para saber si el servicio responde."""
    return {'estado': 'ok'}


@app.get('/canales/{canal}/webhook')
def verificar_webhook(canal: str, request: Request):
    """Verificación inicial de Meta (WhatsApp, Instagram, Messenger).

    Al configurar el webhook, Meta llama con hub.mode=subscribe, hub.verify_token y hub.challenge. Si el token
    coincide con META_TOKEN_VERIFICACION del .env, se devuelve hub.challenge tal cual y Meta da por buena la URL.
    """
    p = request.query_params
    if p.get('hub.mode') == 'subscribe' and p.get('hub.verify_token') == ajustes.meta_token_verificacion:
        return Response(content=p.get('hub.challenge', ''), media_type='text/plain')
    raise HTTPException(status_code=403, detail='Token de verificación inválido')


@app.post('/canales/{canal}/webhook', status_code=200)
async def recibir_webhook(canal: str, request: Request, x_hub_signature_256: str | None = Header(default=None)):
    """RED-01: llega un mensaje de un cliente.

    1. Lee el cuerpo crudo (bytes): la firma se calcula sobre los bytes exactos, no sobre el JSON ya convertido.
    2. Si el canal es de Meta, verifica la firma X-Hub-Signature-256; si no coincide, responde 401.
    3. Lo deja en la cola del orquestador y responde de inmediato.
    """
    cuerpo = await request.body()
    if canal in ('whatsapp', 'instagram', 'messenger') and not firma_meta_valida(cuerpo, x_hub_signature_256, ajustes.meta_secreto_app):
        raise HTTPException(status_code=401, detail='Firma inválida')
    await orquestador.encolar(canal, cuerpo)
    return {'recibido': True}


@app.post('/agentes/instructor/preguntar', status_code=501)
def instructor_preguntar():
    """FOR-09: el agente Instructor responde preguntas de un curso citando la base de conocimiento. Por construir."""
    return {'codigo': 'por_construir', 'caso_de_uso': 'FOR-09'}
