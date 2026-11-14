"""Rutas principales de GuayacanERP: el «mapa» que une cada dirección web con su archivo de rutas.

  /api/v1/                 rutas transversales (autenticación, sincronización, público): guayacan/urls.py
  /api/v1/<esquema>/       una entrada por app (26): apps/<esquema>/urls.py
  /api/b2b/v1/             API para clientes empresariales: guayacan/urls_b2b.py
  /api/esquema/            descripción OpenAPI de toda la API (la genera drf-spectacular)
  /api/docs/               documentación interactiva (Swagger): abra http://localhost:8000/api/docs/
"""
from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Primero las transversales, para que /api/v1/nucleo/mis-fincas/ se resuelva en guayacan/urls.py
    path('api/v1/', include('guayacan.urls')),
    # Una línea por cada esquema de settings.ESQUEMAS, p. ej. /api/v1/comercial/ -> apps/comercial/urls.py
    *[path(f'api/v1/{esquema}/', include(f'apps.{esquema}.urls')) for esquema in settings.ESQUEMAS],
    path('api/b2b/v1/', include('guayacan.urls_b2b')),
    path('api/esquema/', SpectacularAPIView.as_view(), name='openapi'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='openapi'), name='docs'),
]
