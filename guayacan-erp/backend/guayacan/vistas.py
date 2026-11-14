"""Vistas base que usan todas las apps.

Una «vista» es la clase o función que recibe una petición HTTP (GET, POST, PATCH...) y devuelve la respuesta.
Aquí hay tres piezas reutilizables:
  VistaModelo          CRUD estándar de una tabla, sin borrado.
  PorConstruir         respuesta 501 para las acciones de los casos de uso que aún no se programan.
  PorConstruirPublico  lo mismo, para rutas que no exigen sesión (códigos QR, webhooks, formularios públicos).
"""
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView


class VistaModelo(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                  mixins.ListModelMixin, viewsets.GenericViewSet):
    """CRUD sin borrado.

    Qué hace: une las piezas («mixins») de Django REST Framework para crear (POST), ver uno (GET /id/),
    modificar (PUT/PATCH) y listar (GET). No incluye DestroyModelMixin, así que no existe DELETE.

    Por qué no se borra: en un ERP los registros son evidencia (contable, sanitaria, legal). Se desactivan, se
    anulan o se cierran. Si una app de verdad necesita borrar, agrega mixins.DestroyModelMixin en su vista.

    campo_padre: para rutas anidadas, p. ej. /pedidos/{padre}/lineas/. Si se indica (p. ej. 'pedido'), la lista
    muestra solo los hijos de ese padre y, al crear, el hijo queda ligado al padre de la ruta automáticamente.
    """

    # Nombre del campo que apunta al padre (sin el sufijo _id). None = ruta normal, no anidada.
    campo_padre = None

    def get_queryset(self):
        """Filas que puede ver esta vista. La base ya filtra por finca; aquí solo se filtra por el padre."""
        qs = super().get_queryset()
        if self.campo_padre and 'padre' in self.kwargs:
            # self.kwargs trae las partes variables de la ruta; 'padre' es el <int:padre> de urls.py
            qs = qs.filter(**{f'{self.campo_padre}_id': self.kwargs['padre']})
        return qs

    def perform_create(self, serializer):
        """Guarda el registro nuevo. En rutas anidadas, fija el padre con el id que viene en la ruta."""
        if self.campo_padre and 'padre' in self.kwargs:
            serializer.save(**{f'{self.campo_padre}_id': self.kwargs['padre']})
        else:
            serializer.save()


class PorConstruir(APIView):
    """Acción de un caso de uso declarada en la API pero aún sin programar.

    Para qué: así la ruta existe desde el primer día (aparece en la documentación OpenAPI y el frontend puede
    llamarla); responde 501 «Not Implemented» con el código del caso de uso para saber qué falta.
    Cómo se usa (en urls.py):  PorConstruir.as_view(caso_de_uso='VTA-03', metodo='POST')
    Al construir el caso de uso, se reemplaza esta vista por la real en el urls.py de la app.
    """

    caso_de_uso = None  # código del caso de uso, p. ej. 'VTA-03'
    metodo = 'POST'     # método HTTP que tendrá la acción cuando exista

    def _responder(self, request, *args, **kwargs):
        # Si llaman con otro método (p. ej. GET a una acción POST), se responde 405 como haría la vista real
        if request.method != self.metodo:
            return Response({'codigo': 'metodo_no_permitido'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return Response({'codigo': 'por_construir', 'caso_de_uso': self.caso_de_uso,
                         'detalle': f'El caso de uso {self.caso_de_uso} está especificado pero aún no se ha construido'},
                        status=status.HTTP_501_NOT_IMPLEMENTED)

    # Todos los métodos HTTP usan la misma respuesta
    get = post = put = patch = delete = _responder


class PorConstruirPublico(PorConstruir):
    """Igual que PorConstruir, pero para rutas que no exigen iniciar sesión.

    Ejemplos: consultar la trazabilidad de un lote con su código QR, validar un certificado o recibir el aviso
    (webhook) de la pasarela de pagos. Esas vistas, al construirse, deben validar el código o la firma.
    """

    permission_classes = []      # nadie necesita permisos para llegar aquí
    authentication_classes = []  # no se lee ningún token
