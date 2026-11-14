"""Pruebas de la verificación de firmas de Meta (app/firmas.py). Se corren con pytest desde servicios/agentes."""
import hashlib
import hmac

from app.firmas import firma_meta_valida


def test_firma_correcta():
    # Se calcula la firma igual que lo haría Meta y debe aceptarse
    cuerpo = b'{"entry": []}'
    firma = 'sha256=' + hmac.new(b'secreto', cuerpo, hashlib.sha256).hexdigest()
    assert firma_meta_valida(cuerpo, firma, 'secreto')


def test_firma_alterada_o_ausente():
    # Firma falsa, firma ausente o secreto sin configurar: siempre se rechaza
    assert not firma_meta_valida(b'x', 'sha256=00', 'secreto')
    assert not firma_meta_valida(b'x', None, 'secreto')
    assert not firma_meta_valida(b'x', 'sha256=00', '')
