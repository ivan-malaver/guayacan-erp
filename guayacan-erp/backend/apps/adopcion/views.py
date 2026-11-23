"""Vistas (endpoints CRUD) del esquema adopcion.

QUÉ HACE UNA VISTA
Recibe la petición HTTP, usa el serializer para validar o convertir los datos y responde. Cada clase de abajo
es un «ViewSet»: una sola clase atiende varias rutas de la misma tabla.

QUÉ OPERACIONES OFRECE (heredadas de guayacan.vistas.VistaModelo)
  GET    /recurso/        lista paginada (50 por página; ?pagina=2&tamano=100)
  GET    /recurso/{id}/   detalle de un registro
  POST   /recurso/        crear
  PUT o PATCH /recurso/{id}/   modificar todo o una parte
  No hay DELETE: en GuayacanERP los registros se desactivan, se anulan o se cierran, no se borran.

La seguridad no se programa aquí: el middleware fija la finca y el usuario, y PostgreSQL solo deja ver y
cambiar lo de esa finca. Las acciones de los casos de uso (aprobar, confirmar, liquidar...) están en urls.py.
Generado por docs/uml/fuentes/gen_apps.py."""
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from guayacan.contexto import Contexto, fijar
from guayacan.pasarela import pasarela
from guayacan.permisos import SoloPersonas
from guayacan.vistas import VistaModelo

from . import models, serializers, services


class AltaPorAdo01:
    """ADO-01: crear un plan, un sitio o un bien pasa por el servicio, que exige la función «adopcion» en la finca.

    Solo cambia el POST; listar, ver y modificar siguen siendo el CRUD de VistaModelo.
    lista_ado_01 es el nombre de la lista que recibe el servicio: 'planes', 'sitios' o 'bienes'.
    """

    lista_ado_01 = None

    def perform_create(self, serializer):
        creados = services.ado_01_configurar_catalogo_sitios(usuario=self.request.user,
                                                             **{self.lista_ado_01: [serializer.validated_data]})
        # Lo mismo que haría serializer.save(): la respuesta 201 se arma con este objeto
        serializer.instance = creados[self.lista_ado_01][0]


# CRUD de adopcion.plan en /api/v1/adopcion/planes/  (el alta es ADO-01)
class PlanViewSet(AltaPorAdo01, VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Plan.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PlanSerializer
    lista_ado_01 = 'planes'


# CRUD de adopcion.sitio en /api/v1/adopcion/sitios/  (el alta es ADO-01)
class SitioViewSet(AltaPorAdo01, VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Sitio.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SitioSerializer
    lista_ado_01 = 'sitios'


# CRUD de adopcion.bien en /api/v1/adopcion/bienes/  (el alta es ADO-01)
class BienViewSet(AltaPorAdo01, VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Bien.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.BienSerializer
    lista_ado_01 = 'bienes'


# CRUD de adopcion.contrato en /api/v1/adopcion/contratos/
class ContratoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Contrato.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ContratoSerializer


# CRUD de adopcion.cuota en /api/v1/adopcion/cuotas/
class CuotaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cuota.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.CuotaSerializer


# CRUD de adopcion.seguimiento en /api/v1/adopcion/seguimientos/
class SeguimientoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Seguimiento.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SeguimientoSerializer


# CRUD de adopcion.liquidacion en /api/v1/adopcion/liquidaciones/
class LiquidacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Liquidacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LiquidacionSerializer


# CRUD de adopcion.movimiento_saldo en /api/v1/adopcion/movimientos-saldo/
class MovimientoSaldoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.MovimientoSaldo.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.MovimientoSaldoSerializer


class Compra(APIView):
    """ADO-02 · POST /api/v1/adopcion/contratos/compra/: un vendedor (o el agente) inicia la compra para el adoptante.

    Responde 201 con el contrato pendiente_pago y el enlace de pago; el adoptante no necesita cuenta.
    """

    # TODO(roles): exigir un permiso de adopción (p. ej. requiere('adopcion.vender')) cuando se definan los roles;
    # hoy basta la sesión en la finca (IsAuthenticated por defecto)

    def post(self, request):
        datos = serializers.CompraSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        contrato, cobro = services.ado_02_comprar_arbol_animal(usuario=request.user, **datos.validated_data)
        return Response({**serializers.ContratoSerializer(contrato).data, 'cobro': cobro}, status=status.HTTP_201_CREATED)


class Readopcion(APIView):
    """ADO-08 · POST /api/v1/adopcion/contratos/readopcion/: un bien en readopción pasa a otro adoptante.

    Responde 201 con el contrato pendiente_pago y el enlace de pago, igual que la compra.
    """

    # TODO(roles): el mismo permiso de adopción que la compra

    def post(self, request):
        datos = serializers.ReadopcionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        contrato, cobro = services.ado_08_readoptar(usuario=request.user, **datos.validated_data)
        return Response({**serializers.ContratoSerializer(contrato).data, 'cobro': cobro}, status=status.HTTP_201_CREATED)


class Decision(APIView):
    """ADO-11 · POST /api/v1/adopcion/contratos/{id}/decision/ {decision}: mantener o liquidar el bien maduro."""

    permission_classes = [IsAuthenticated, SoloPersonas]  # la decisión del dueño la registra una persona, no un agente

    def post(self, request, id):
        datos = serializers.DecisionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        contrato = services.ado_11_decidir_madurez_mantener_liquidar(usuario=request.user, contrato_id=id, **datos.validated_data)
        return Response(serializers.ContratoSerializer(contrato).data)


class Muerte(APIView):
    """ADO-13 · POST /api/v1/adopcion/bienes/{id}/muerte/ {fecha, causa}: se repone en garantía o termina el contrato."""

    permission_classes = [IsAuthenticated, SoloPersonas]  # la muerte la registra quien la vio, no un agente

    def post(self, request, id):
        datos = serializers.MuerteSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        return Response(services.ado_13_reponer_bien_muerto_garantia(usuario=request.user, bien_id=id, **datos.validated_data))


class PagarCuota(APIView):
    """ADO-05 · POST /api/v1/adopcion/cuotas/{id}/pagar/: devuelve el enlace de cobro de la cuota pendiente."""

    def post(self, request, id):
        return Response({'cuota': id, 'cobro': services.ado_05_cobrar_pagar_cuota_mensual(usuario=request.user, cuota_id=id)})


class AvisoPago(APIView):
    """ADO-02 y ADO-05 · POST /api/v1/pagos/webhook/: la pasarela avisa si el pago se aprobó o se rechazó.

    Llega sin sesión. Primero se verifica la firma (cabecera X-Pasarela-Firma) y solo entonces se fija la finca
    de la referencia para que la seguridad por filas deje ver el contrato.
    """

    permission_classes = []      # la pasarela no tiene usuario: la firma es la autenticación
    authentication_classes = []

    def post(self, request):
        aviso = pasarela().leer_aviso(request.data, request.headers.get('X-Pasarela-Firma'))
        datos = serializers.AvisoPagoSerializer(data=aviso)
        datos.is_valid(raise_exception=True)
        # TODO(VTA-07): las referencias de pedidos de venta llegarán aquí también; hoy solo hay contratos de adopción
        fijar(Contexto(predio_id=int(datos.validated_data['referencia'].split(':', 1)[0])))
        documento, estado = services.confirmar_pago(**datos.validated_data)  # contrato (ADO-02) o cuota (ADO-05)
        return Response({'recibido': True, 'documento': documento, 'estado': estado})


class Siembra(APIView):
    """POST /api/v1/adopcion/bienes/{id}/siembra/ según la modalidad del contrato:
      ADO-03 (propia)      {fecha, visita}: el adoptante sembró en persona
      ADO-04 (trabajador)  {fecha, tarea, video_url}: lo sembró un trabajador y el video va al adoptante
    """

    permission_classes = [IsAuthenticated, SoloPersonas]  # una siembra la registra quien la vio, no un agente

    def post(self, request, id):
        if models.Contrato.objects.filter(bien_id=id, estado='activo', modalidad_siembra='trabajador').exists():
            datos = serializers.SiembraTrabajadorSerializer(data=request.data)
            datos.is_valid(raise_exception=True)
            bien = services.ado_04_sembrar_trabajador_enviar_video(usuario=request.user, bien_id=id, **datos.validated_data)
        else:
            datos = serializers.SiembraPersonaSerializer(data=request.data)
            datos.is_valid(raise_exception=True)
            bien = services.ado_03_sembrar_persona(usuario=request.user, bien_id=id, **datos.validated_data)
        return Response(serializers.BienSerializer(bien).data)


class MarcarEnviado(APIView):
    """ADO-07 · POST /api/v1/adopcion/seguimientos/{id}/marcar-enviado/: el Gestor de redes confirma la entrega al adoptante."""

    def post(self, request, id):
        seguimiento = services.ado_07_marcar_enviado(usuario=request.user, seguimiento_id=id)
        return Response(serializers.SeguimientoSerializer(seguimiento).data)


class EmitirEnlace(APIView):
    """ADO-06 · POST /api/v1/adopcion/contratos/{id}/enlace/: enlace personal del adoptante (se muestra una sola vez)."""

    # TODO(roles): exigir un permiso de adopción cuando se definan los roles (igual que la compra)

    def post(self, request, id):
        return Response(services.ado_06_emitir_enlace(usuario=request.user, contrato_id=id), status=status.HTTP_201_CREATED)


class RevocarEnlace(APIView):
    """ADO-06 · POST /api/v1/adopcion/enlaces/{id}/revocar/."""

    def post(self, request, id):
        services.ado_06_revocar_enlace(usuario=request.user, enlace_id=id)
        return Response({'enlace': id, 'revocado': True})


class LimitePublico(AnonRateThrottle):
    rate = '60/min'  # nadie prueba códigos a ciegas (y protege el servidor)


class FichaPorEnlace(APIView):
    """ADO-06 · GET /api/v1/publico/adopcion/<finca>.<código>/: el adoptante sin cuenta ve su árbol o animal.

    Llega sin sesión: con la finca del enlace se fija la seguridad por filas y el código decide qué contrato se ve.
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = [LimitePublico]

    def get(self, request, enlace):
        finca, _, codigo = enlace.partition('.')
        if not finca.isdigit() or not codigo:
            raise NotFound('El enlace no existe o ya no está vigente')
        fijar(Contexto(predio_id=int(finca)))
        contrato = services.ado_06_contrato_por_enlace(codigo)
        return Response(services.ado_06_seguir_mi_arbol_mi_animal(contrato=contrato))


def _mis_contratos(usuario):
    """Contratos activos del adoptante que sí tiene cuenta (su usuario apunta a su tercero)."""
    return models.Contrato.objects.filter(adoptante_id=usuario.tercero_id, estado='activo') if usuario.tercero_id else models.Contrato.objects.none()


class MisBienes(APIView):
    """ADO-06 · GET /api/v1/adopcion/mis-bienes/: los bienes del adoptante con cuenta (sin el seguimiento completo)."""

    def get(self, request):
        fichas = [services.ado_06_seguir_mi_arbol_mi_animal(contrato=c) for c in _mis_contratos(request.user).order_by('id')]
        return Response([{k: f[k] for k in ('contrato', 'estado', 'bien', 'saldo_a_favor')} for f in fichas])


class SeguimientoMiBien(APIView):
    """ADO-06 · GET /api/v1/adopcion/mis-bienes/{id}/seguimiento/: la ficha completa de uno de sus bienes."""

    def get(self, request, id):
        contrato = _mis_contratos(request.user).filter(bien_id=id).first()
        if not contrato:
            raise NotFound('No es uno de sus bienes')
        return Response(services.ado_06_seguir_mi_arbol_mi_animal(contrato=contrato))
