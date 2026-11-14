"""Ayudas de base de datos que usan los modelos generados y algunas vistas.

  SQLCrudo / sql()   valor por defecto calculado por PostgreSQL (db_default)
  Geometria          columna de mapas PostGIS sin instalar GeoDjango
  RutaAdmin          decide qué tablas puede migrar Django y con qué conexión
  consultar()        ejecuta SQL y devuelve filas como diccionarios
"""
from django.db import connection, models


class SQLCrudo(models.Func):
    """Expresión SQL literal usada como valor por defecto, p. ej. nucleo.predio_actual() o current_date.

    Con db_default=sql('...') Django NO envía la columna en el INSERT y la base pone el valor. Así la finca de
    cada registro la decide siempre la base según la sesión, nunca el usuario.
    """

    def __init__(self, expresion, output_field=None):
        # En las plantillas SQL de Django el % es especial; se duplica para que llegue literal a la base
        self.template = expresion.replace('%', '%%')
        super().__init__(output_field=output_field or models.TextField())


def sql(expresion):
    """Atajo para escribir db_default=sql('nucleo.predio_actual()') en los modelos."""
    return SQLCrudo(expresion)


class Geometria(models.TextField):
    """Columna PostGIS (puntos, polígonos) sin GeoDjango.

    Por qué: GeoDjango exige instalar GDAL, que en Windows es difícil. Esta clase solo le dice a Django el tipo
    de la columna; los datos viajan como texto:
      - Se escribe en EWKT, p. ej. 'SRID=9377;POLYGON((...))'  (SRID 9377 = origen nacional de Colombia)
      - Se lee como EWKB en hexadecimal.
    Para devolver GeoJSON a un mapa use ST_AsGeoJSON en la consulta (ver la acción zonas?formato=geojson).
    """

    def __init__(self, *args, tipo='Geometry', srid=9377, **kwargs):
        self.tipo, self.srid = tipo, srid
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        """Django lo usa para copiar el campo; se agregan tipo y srid para no perderlos."""
        nombre, ruta, args, kwargs = super().deconstruct()
        kwargs.update(tipo=self.tipo, srid=self.srid)
        return nombre, ruta, args, kwargs

    def db_type(self, connection):
        """Tipo real de la columna en PostgreSQL."""
        return f'geometry({self.tipo}, {self.srid})'


class RutaAdmin:
    """Enrutador de base de datos (settings.DATABASE_ROUTERS).

    Regla: las tablas internas de Django (contenttypes y auth) se migran SOLO con la conexión 'admin' (usuario
    dueño de la base). Las tablas de negocio nunca se migran: las crea el SQL de specs/modelo-datos.
    Por eso el comando correcto es:  python manage.py migrate --database=admin
    (con «migrate» a secas no se crea nada, porque la conexión 'default' no tiene permiso para migrar).
    """

    internas = {'contenttypes', 'auth'}

    def allow_migrate(self, db, app_label, **hints):
        if app_label in self.internas:
            return db == 'admin'
        return False


def consultar(sql_texto, parametros=None):
    """Ejecuta una consulta dentro de la transacción de la petición y devuelve las filas como diccionarios.

    Ejemplo:  consultar('select * from adopcion.v_tablero where tipo = %s', ['frutal'])
    Use siempre %s y la lista de parámetros; nunca arme el SQL pegando textos (riesgo de inyección de SQL).
    """
    with connection.cursor() as cur:
        cur.execute(sql_texto, parametros or [])
        if cur.description is None:   # la sentencia no devuelve filas (p. ej. un UPDATE)
            return []
        columnas = [c.name for c in cur.description]
        return [dict(zip(columnas, fila, strict=True)) for fila in cur.fetchall()]
