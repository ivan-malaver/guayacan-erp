"""Paginación de las listas de la API.

Para qué: una tabla puede tener miles de filas; enviarlas todas haría lenta la app de campo. Las listas se
entregan por páginas. Se registra en settings: REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'].

Uso desde el frontend:  GET /api/v1/inventario/productos/?pagina=2&tamano=100
La respuesta trae: count (total de filas), next y previous (enlaces) y results (las filas de la página).
"""
from rest_framework.pagination import PageNumberPagination


class Paginacion(PageNumberPagination):
    page_size = 50                    # filas por página si no se indica otra cosa
    page_size_query_param = 'tamano'  # el cliente puede pedir otro tamaño con ?tamano=
    max_page_size = 500               # límite para que nadie pida la tabla entera de una vez
    page_query_param = 'pagina'       # número de página: ?pagina=
