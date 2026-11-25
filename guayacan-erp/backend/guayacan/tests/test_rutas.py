"""Pruebas de las rutas: las direcciones declaradas existen y las acciones sin construir usan PorConstruir (501).
resolve() pregunta a Django qué vista atendería una dirección, sin hacer la petición."""
from django.urls import resolve

from guayacan.vistas import PorConstruir


# CRUD, acción por construir, ruta anidada y rutas transversales se resuelven como se espera
def test_resuelve_crud_y_acciones():
    assert resolve('/api/v1/comercial/pedidos/').url_name.startswith('comercial-pedidos')
    vista = resolve('/api/v1/comercial/pedidos/5/despachar/').func.view_class  # VTA-05
    assert issubclass(vista, PorConstruir)
    assert resolve('/api/v1/comercial/pedidos/5/lineas/').url_name == 'comercial-lineas-lista'
    assert resolve('/api/v1/nucleo/mis-fincas/').url_name == 'nuc-03-mis-fincas'
    assert resolve('/api/v1/sincronizacion/lote/').url_name == 'nuc-05-sincronizar'
    # Apéndice A: la app de adopción también tiene CRUD y acciones
    assert resolve('/api/v1/adopcion/contratos/').url_name.startswith('adopcion-contratos')
    assert issubclass(resolve('/api/v1/adopcion/adoptantes/3/pagar-saldo/').func.view_class, PorConstruir)  # ADO-10
    # Una acción ya construida (ADO-03) deja de ser PorConstruir
    assert not issubclass(resolve('/api/v1/adopcion/bienes/3/siembra/').func.view_class, PorConstruir)


# Cada app de settings.ESQUEMAS tiene un urls.py que se puede importar sin errores
def test_todas_las_apps_tienen_rutas():
    from django.conf import settings
    for esquema in settings.ESQUEMAS:
        __import__(f'apps.{esquema}.urls')
