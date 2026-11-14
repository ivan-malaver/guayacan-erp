"""Vistas (endpoints CRUD) del esquema terceros.

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


# CRUD de terceros.tercero en /api/v1/terceros/terceros/
class TerceroViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Tercero.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.TerceroSerializer


# CRUD de terceros.consentimiento_datos en /api/v1/terceros/consentimientos/
class ConsentimientoDatosViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.ConsentimientoDatos.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ConsentimientoDatosSerializer


# CRUD de terceros.cliente en /api/v1/terceros/clientes/
class ClienteViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Cliente.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ClienteSerializer


# CRUD de terceros.proveedor en /api/v1/terceros/proveedores/
class ProveedorViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Proveedor.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.ProveedorSerializer


# CRUD de terceros.empleado en /api/v1/terceros/empleados/
class EmpleadoViewSet(VistaModelo):
    # Filas que puede ver la vista (la base ya filtra por la finca de la sesión)
    queryset = models.Empleado.objects.all()
    # Cómo se convierten y validan los datos
    serializer_class = serializers.EmpleadoSerializer
