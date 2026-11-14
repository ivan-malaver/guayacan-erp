# Cómo construir un caso de uso (ejemplo: VTA-03 · Tomar y confirmar un pedido)

La especificación está en `docs/casos-de-uso/cu_4_ventas_clientes_y_turismo.md` y su secuencia en
`docs/uml/secuencia/SQ04_confirmar_pedido_fefo.png`.

## 1. Rama

```
git switch -c cu/VTA-03-confirmar-pedido
```

## 2. Prueba de aceptación primero

En `backend/apps/comercial/tests/test_casos_de_uso.py` quite el `skip` de VTA-03 y escriba el flujo principal y cada
flujo alterno (pedido que no está en borrador, cliente bloqueado por mora, cupo insuficiente, precio cambiado):

```python
@pytest.mark.django_db
def test_vta_03_confirma_y_reserva_fefo(api_admin, pedido_borrador):
    r = api_admin.post(f'/api/v1/comercial/pedidos/{pedido_borrador.id}/confirmar/')
    assert r.status_code == 200
    assert r.data['estado'] == 'confirmado'


@pytest.mark.django_db
def test_vta_03_sin_existencias_responde_422(api_admin, pedido_sin_stock):
    r = api_admin.post(f'/api/v1/comercial/pedidos/{pedido_sin_stock.id}/confirmar/')
    assert r.status_code == 422           # P0001 lanzado por la regla de la base
    assert r.data['codigo'] == 'regla_negocio'
```

## 3. Servicio

`backend/apps/comercial/services.py` ya trae el método vacío con su ficha. La regla vive en la base:

```python
def vta_03_tomar_confirmar_pedido(*, usuario, pedido_id, **datos):
    with transaction.atomic(), connection.cursor() as cur:
        # La función bloquea el pedido, revisa mora y cartera, reserva FEFO y lo pasa a confirmado
        cur.execute('select comercial.confirmar_pedido(%s)', [pedido_id])
        # y escribe el evento en nucleo.evento_salida: aquí no se publica otra vez
        return models.Pedido.objects.get(pk=pedido_id)
```

No valide en Python lo que la base ya valida (estado, mora, cupo, precios, existencias): si falla, la base lanza `P0001` y
`guayacan/errores.py` responde 422 con el mensaje de la regla.

## 4. Vista y ruta

Reemplace en `apps/comercial/urls.py` la línea `PorConstruir` de `pedidos/<int:id>/confirmar/` por la vista real:

```python
class ConfirmarPedido(APIView):
    def post(self, request, id):
        pedido = services.vta_03_tomar_confirmar_pedido(usuario=request.user, pedido_id=id)
        return Response(serializers.PedidoSerializer(pedido).data)
```

## 5. Pantalla

En `frontend/src/app/features/comercial/` agregue el componente y su ruta en `comercial.routes.ts`. Muestre los
botones según el estado (diagrama `ST01_pedido`).

## 6. Terminar

Corra `ruff check .`, `pytest` y `npm test`; abra el pull request `VTA-03: confirmar pedido con reserva FEFO` y
verifique la definición de terminado (sección 10.6 del documento técnico).
