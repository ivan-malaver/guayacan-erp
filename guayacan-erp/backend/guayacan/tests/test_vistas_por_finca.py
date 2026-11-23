"""Las vistas de negocio respetan la finca de la sesión (migraciones 010 y 012).

Una vista sin security_invoker corre con los permisos de su dueño (postgres), que se salta la seguridad por filas, y
mezcla los datos de todas las fincas. Esta prueba falla si alguien crea una vista nueva sin esa opción.
"""
import pytest
from django.db import connection

# Esquemas propios de PostgreSQL y de Django: sus vistas no tienen datos de las fincas
AJENOS = ('pg_catalog', 'information_schema', 'django', 'public', 'topology', 'tiger')


def _vistas():
    with connection.cursor() as cur:
        cur.execute("select n.nspname || '.' || c.relname, coalesce('security_invoker=true' = any(c.reloptions), false) "
                    "from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                    "where c.relkind = 'v' and n.nspname <> all(%s) and n.nspname not like 'pg\\_%%' order by 1", [list(AJENOS)])
        return cur.fetchall()


@pytest.fixture
def finca(en_finca):
    with connection.cursor() as cur:
        cur.execute('select u.id, f.predio_id from nucleo.usuario u cross join lateral nucleo.predios_del_usuario(u.id) f order by 2, 1 limit 1')
        usuario_id, predio_id = cur.fetchone()
    en_finca(predio=predio_id, usuario=usuario_id)


def test_todas_las_vistas_de_negocio_usan_security_invoker(finca):
    """Ninguna vista de negocio corre con los permisos de su dueño"""
    vistas = _vistas()
    assert len(vistas) >= 21  # las 5 de la v4, adopcion.v_tablero y las 15 de la migración 012
    assert [v for v, invoker in vistas if not invoker] == []


def test_el_usuario_de_la_api_puede_leer_cada_vista(finca):
    """Con security_invoker, quien consulta necesita permiso sobre las tablas de la vista: ninguna responde «permiso denegado»"""
    for vista, _ in _vistas():
        with connection.cursor() as cur:
            cur.execute(f'select 1 from {vista} limit 1')  # noqa: S608  el nombre sale del catálogo, no del usuario
