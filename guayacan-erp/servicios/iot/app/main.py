"""Puente IoT (fase 4, funciones iot_*): recibe lecturas de la pasarela de la finca y las entrega al ERP por lotes.

CONTEXTO
En la finca hay una «pasarela» local (un computador pequeño con Mosquitto, el servidor MQTT) a la que los sensores
envían sus datos. La pasarela sigue funcionando sin internet: guarda las lecturas y las reenvía cuando vuelve
la conexión. Este servicio las recibe y las pasa al ERP.

SIN DUPLICADOS
Cada lectura trae un id_cliente (UUIDv7) generado por la pasarela. El ERP las inserta en iot.lectura
(particionada por mes) usando ese id, así un reenvío no duplica (IOT-02). Los comandos a actuadores (válvulas,
bombas) salen del ERP (IOT-03) y pasarán por aquí hacia MQTT.

Arranque en su PC (desde servicios/iot, con su venv activo):  uvicorn app.main:app --reload --port 8200
"""
import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

# Configuración desde el entorno (.env)
ERP_URL = os.environ.get('ERP_URL', 'http://localhost:8000')
TOKEN_PASARELA = os.environ.get('TOKEN_PASARELA', '')  # secreto compartido con la pasarela de la finca

app = FastAPI(title='GuayacanERP · Puente IoT', version='0.1.0')


class Lectura(BaseModel):
    """Una medición de un sensor. Pydantic valida los tipos automáticamente al recibir el JSON."""
    id_cliente: str = Field(description='UUIDv7 generado por la pasarela')
    sensor_codigo: str  # p. ej. 'HUM-01' (humedad del suelo, lote 1)
    valor: float
    medido_en: str      # fecha y hora ISO 8601 con zona horaria


class Lote(BaseModel):
    """Un envío de la pasarela: máximo 500 lecturas."""
    lecturas: list[Lectura] = Field(max_length=500)


@app.get('/salud')
def salud():
    """Comprobación de vida para Docker y el monitoreo."""
    return {'estado': 'ok'}


@app.post('/lecturas/lote')
async def lecturas_lote(lote: Lote, authorization: str | None = Header(default=None)):
    """Reenvía el lote al ERP (POST /api/v1/iot/lecturas/lote/) con el token de la pasarela."""
    if not TOKEN_PASARELA:
        raise HTTPException(status_code=503, detail='Falta TOKEN_PASARELA en el entorno')
    # Solo la pasarela, que conoce el token, puede enviar lecturas
    if authorization != f'Bearer {TOKEN_PASARELA}':
        raise HTTPException(status_code=401, detail='Token de pasarela inválido')
    # httpx.AsyncClient hace la petición HTTP sin bloquear el servidor; timeout de 15 segundos
    async with httpx.AsyncClient(base_url=ERP_URL, timeout=15) as cliente:
        r = await cliente.post('/api/v1/iot/lecturas/lote/', json=lote.model_dump(),
                               headers={'Authorization': f'Bearer {TOKEN_PASARELA}'})
    es_json = r.headers.get('content-type', '').startswith('application/json')
    # Se devuelve lo que respondió el ERP (hoy 501 «por construir»)
    return {'estado_erp': r.status_code, 'respuesta': r.json() if es_json else None}
