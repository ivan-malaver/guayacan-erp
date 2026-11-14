"""Pruebas de los modelos de datos del puente IoT (app/main.py). Se corren con pytest desde servicios/iot."""
import pytest

# Si pydantic no está instalado, la prueba se salta en vez de fallar
pydantic = pytest.importorskip('pydantic')


def test_lote_limita_tamano():
    from app.main import Lote
    lectura = {'id_cliente': '0190f0f0-0000-7000-8000-000000000000', 'sensor_codigo': 'HUM-01', 'valor': 41.5,
               'medido_en': '2026-10-28T06:00:00-05:00'}
    # Un lote normal se acepta
    assert len(Lote(lecturas=[lectura]).lecturas) == 1
    # Más de 500 lecturas se rechaza con un error de validación
    with pytest.raises(pydantic.ValidationError):
        Lote(lecturas=[lectura] * 501)
