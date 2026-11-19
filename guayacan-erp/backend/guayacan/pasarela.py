"""Adaptador de la pasarela de pagos: el resto del código no sabe qué pasarela cobra.

POR QUÉ UN ADAPTADOR
Igual que RegistroExterno en la base (huellas listas para anclarse en una red externa), la pasarela es una pieza
que cambia: hoy PasarelaSimulada, mañana Wompi. Los casos de uso llaman a pasarela() y usan solo dos métodos:
  crear_cobro(referencia, valor, descripcion)  -> {'id_transaccion', 'url_pago'}: el enlace que se envía al adoptante
  leer_aviso(datos, firma)                     -> el aviso (webhook) ya verificado, o PermissionDenied si la firma no cuadra

LA REFERENCIA
Lleva la finca y el documento: '<predio_id>:<número>' (p. ej. '3:ADO-12'). El webhook llega sin sesión; con la firma
válida, la finca de la referencia es confiable y fija la seguridad por filas (ver apps/adopcion/views.py).
"""
import hashlib
import hmac
import uuid

from django.conf import settings
from rest_framework.exceptions import PermissionDenied


class PasarelaSimulada:
    """Cobra de mentiras para desarrollo y pruebas: el aviso se firma con HMAC-SHA256 y settings.PASARELA_SECRETO."""

    proveedor = 'simulada'  # valor de comercial.pago.proveedor_pasarela

    def crear_cobro(self, *, referencia, valor, descripcion):
        return {'id_transaccion': f'SIM-{uuid.uuid4().hex[:12]}', 'url_pago': f'https://pagos.simulada.local/{referencia}',
                'descripcion': descripcion, 'valor': str(valor)}

    def firmar(self, datos):
        """Firma del aviso. La usa quien simula la pasarela (pruebas, consola) para enviar el webhook."""
        mensaje = '|'.join(str(datos.get(k, '')) for k in ('referencia', 'estado', 'id_transaccion', 'valor'))
        return hmac.new(settings.PASARELA_SECRETO.encode(), mensaje.encode(), hashlib.sha256).hexdigest()

    def leer_aviso(self, datos, firma):
        # Sin secreto configurado se rechaza todo: nunca se confirma un pago sin verificar
        if not settings.PASARELA_SECRETO or not firma or not hmac.compare_digest(self.firmar(datos), firma):
            raise PermissionDenied('Firma de la pasarela inválida')
        return datos


def pasarela():
    """La pasarela de la instalación."""
    # TODO(Wompi): con la cuenta y las llaves de la finca, crear PasarelaWompi (enlace de pago y verificación del
    # checksum del evento con el secreto de eventos) y elegirla aquí según settings.PASARELA
    return PasarelaSimulada()
