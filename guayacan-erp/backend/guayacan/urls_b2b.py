"""API B2B (empresa a empresa) bajo /api/b2b/v1/  ·  caso de uso NUC-10, fase 3, función por finca api_b2b.

Para qué: hoteles y restaurantes con sistema propio consultan el catálogo y hacen pedidos automáticamente,
con una llave de API (nucleo.llave_api) en vez de usuario y contraseña. Ambas rutas están por construir (501).
"""
from django.urls import path

from .vistas import PorConstruir

urlpatterns = [
    # Catálogo con precios del cliente
    path('catalogo/', PorConstruir.as_view(caso_de_uso='NUC-10', metodo='GET'), name='nuc-10-catalogo'),
    # Crear un pedido desde el sistema del cliente
    path('pedidos/', PorConstruir.as_view(caso_de_uso='NUC-10', metodo='POST'), name='nuc-10-pedidos'),
]
