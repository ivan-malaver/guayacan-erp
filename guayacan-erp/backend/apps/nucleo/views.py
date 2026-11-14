"""Vistas (endpoints CRUD) del esquema nucleo.

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
from guayacan.vistas import VistaModelo

from . import models, serializers


# CRUD de nucleo.usuario en /api/v1/nucleo/usuarios/
class UsuarioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Usuario.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.UsuarioSerializer


# CRUD de nucleo.rol en /api/v1/nucleo/roles/
class RolViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Rol.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RolSerializer


# CRUD de nucleo.permiso en /api/v1/nucleo/permisos/
class PermisoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Permiso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PermisoSerializer


# CRUD de nucleo.rol_permiso en /api/v1/nucleo/roles/{id}/permisos/
class RolPermisoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.RolPermiso.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.RolPermisoSerializer


# CRUD de nucleo.usuario_rol en /api/v1/nucleo/usuarios/{id}/roles/
class UsuarioRolViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.UsuarioRol.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.UsuarioRolSerializer


# CRUD de nucleo.parametro en /api/v1/nucleo/parametros/
class ParametroViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Parametro.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ParametroSerializer


# CRUD de nucleo.auditoria en /api/v1/nucleo/auditoria/
class AuditoriaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Auditoria.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.AuditoriaSerializer


# CRUD de nucleo.evento_salida en /api/v1/nucleo/eventos-salida/
class EventoSalidaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.EventoSalida.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EventoSalidaSerializer


# CRUD de nucleo.predio en /api/v1/nucleo/predios/
class PredioViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Predio.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.PredioSerializer


# CRUD de nucleo.zona en /api/v1/nucleo/zonas/
class ZonaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Zona.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ZonaSerializer


# CRUD de nucleo.dispositivo_captura en /api/v1/nucleo/dispositivos-captura/
class DispositivoCapturaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.DispositivoCaptura.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.DispositivoCapturaSerializer


# CRUD de nucleo.sincronizacion en /api/v1/nucleo/sincronizaciones/
class SincronizacionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Sincronizacion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.SincronizacionSerializer


# CRUD de nucleo.funcionalidad en /api/v1/nucleo/funcionalidades/
class FuncionalidadViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Funcionalidad.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.FuncionalidadSerializer


# CRUD de nucleo.nota_voz en /api/v1/nucleo/notas-voz/
class NotaVozViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.NotaVoz.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.NotaVozSerializer


# CRUD de nucleo.llave_api en /api/v1/nucleo/llaves-api/
class LlaveApiViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.LlaveApi.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.LlaveApiSerializer


# CRUD de nucleo.webhook_suscripcion en /api/v1/nucleo/webhooks-suscripcion/
class WebhookSuscripcionViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.WebhookSuscripcion.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.WebhookSuscripcionSerializer


# CRUD de nucleo.webhook_entrega en /api/v1/nucleo/webhooks-entrega/
class WebhookEntregaViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.WebhookEntrega.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.WebhookEntregaSerializer
