"""Verifica que los archivos del paquete llegaron completos y sin daños a su PC.

QUÉ HACE
Calcula la huella SHA-256 de cada archivo y la compara con la guardada en huellas.json al armar el paquete.
Una huella es como una «firma» del contenido: si cambia un solo byte (un archivo cortado al copiar, bytes nulos,
basura de otro archivo), la huella es totalmente distinta.

PARA QUÉ
Detecta archivos dañados antes de perder tiempo con errores raros de Python o Angular (como los de models.py que
traían restos de un PDF o bytes nulos).

USO (desde la raíz del repositorio, con cualquier Python 3):
    python verificar.py

NOTA: después de que usted edite archivos, esos saldrán como DIFERENTE; es normal. La verificación sirve para el
paquete recién descomprimido. Los finales de línea se comparan normalizados (LF), así Git en Windows no da falsos avisos.
"""
import hashlib
import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent
# Extensiones binarias: se comparan byte a byte (no tienen finales de línea que normalizar)
BINARIOS = {'.png', '.jpg', '.ico', '.pdf', '.docx', '.xlsx', '.zip'}


def huella(ruta: pathlib.Path) -> str:
    """SHA-256 del archivo. En los de texto, convierte CRLF (Windows) a LF antes de calcular."""
    datos = ruta.read_bytes()
    if ruta.suffix.lower() not in BINARIOS:
        datos = datos.replace(b'\r\n', b'\n')
    return hashlib.sha256(datos).hexdigest()


def main() -> None:
    huellas = json.loads((RAIZ / 'huellas.json').read_text(encoding='utf-8'))
    distintos, faltan = [], []
    for nombre, esperada in huellas.items():
        ruta = RAIZ / nombre
        if not ruta.exists():
            faltan.append(nombre)
        elif huella(ruta) != esperada:
            distintos.append(nombre)
    for n in distintos:
        print('DIFERENTE:', n)
    for n in faltan:
        print('FALTA:    ', n)
    bien = len(huellas) - len(distintos) - len(faltan)
    print(f'{bien} de {len(huellas)} archivos idénticos al paquete original')
    if not distintos and not faltan:
        print('Todo en orden.')


if __name__ == '__main__':
    main()
