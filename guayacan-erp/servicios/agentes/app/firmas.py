"""Verificación de firmas de webhooks: garantiza que un aviso viene de Meta y no de un impostor.

Cómo funciona HMAC-SHA256: Meta y nosotros compartimos un secreto. Meta calcula una «huella» del cuerpo del
mensaje con ese secreto y la envía en la cabecera. Nosotros calculamos la misma huella; si coinciden, el mensaje
es auténtico y no fue alterado. Quien no conoce el secreto no puede fabricar una huella válida.
"""
import hashlib
import hmac


def firma_meta_valida(cuerpo: bytes, cabecera: str | None, secreto: str) -> bool:
    """True si la cabecera X-Hub-Signature-256 ('sha256=<hex>') corresponde al cuerpo con el secreto dado."""
    # Sin cabecera, sin secreto configurado o con un formato distinto: se rechaza
    if not cabecera or not secreto or not cabecera.startswith('sha256='):
        return False
    esperado = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    # compare_digest compara en tiempo constante: no deja adivinar la firma midiendo cuánto tarda la comparación
    return hmac.compare_digest(esperado, cabecera.removeprefix('sha256='))
