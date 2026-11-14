#!/usr/bin/env bash
# cargar_base.sh · Igual que cargar_base.ps1, para Linux, macOS o Git Bash en Windows.
#
# QUÉ HACE: (opcional) corre las tres baterías de pruebas en una base temporal y luego carga en «guayacan» el
# esquema v5, los datos iniciales, el Apéndice A (adopción) y preparar_api.sql.
#
# USO (desde la raíz del repositorio, con «docker compose up -d postgres» corriendo):
#   ./scripts/cargar_base.sh              # carga la base guayacan (debe estar vacía)
#   ./scripts/cargar_base.sh --pruebas    # primero corre las 339 pruebas y luego carga
#   ./scripts/cargar_base.sh --reiniciar  # BORRA la base guayacan y la vuelve a cargar (pide confirmación)
set -euo pipefail  # detenerse ante cualquier error o variable sin definir

PRUEBAS=0; REINICIAR=0
for a in "$@"; do
  case "$a" in
    --pruebas) PRUEBAS=1 ;;
    --reiniciar) REINICIAR=1 ;;
    *) echo "Opción desconocida: $a"; exit 2 ;;
  esac
done

[ -f .env ] || { echo 'No existe .env. Copie .env.ejemplo como .env y cambie las claves.'; exit 1; }
# Toma POSTGRES_API_CLAVE del .env sin ejecutar el archivo
CLAVE_API=$(grep -E '^\s*POSTGRES_API_CLAVE\s*=' .env | tail -1 | cut -d= -f2- | xargs)
[ -n "$CLAVE_API" ] || { echo 'Falta POSTGRES_API_CLAVE en .env'; exit 1; }

psql_en() { local base=$1; shift; docker compose exec -T postgres psql -U postgres -d "$base" "$@"; }
# Ejecuta un .sql leyéndolo por la entrada estándar (en bash «<» sí funciona)
ejecutar() { local base=$1 archivo=$2; shift 2; echo "  -> $archivo"; psql_en "$base" -v ON_ERROR_STOP=1 -q "$@" < "$archivo"; }
cargar_modelo() {
  ejecutar "$1" specs/modelo-datos/esquema_postgresql.sql
  ejecutar "$1" specs/modelo-datos/datos_iniciales.sql
  ejecutar "$1" specs/modelo-datos/apendice_a_adopcion.sql
}

if [ "$PRUEBAS" = 1 ]; then
  for prueba in pruebas_reglas_v5 pruebas_reglas_v4 pruebas_adopcion; do
    echo "Prueba: $prueba"
    psql_en postgres -q -c 'drop database if exists guayacan_prueba' -c 'create database guayacan_prueba'
    ejecutar guayacan_prueba specs/modelo-datos/esquema_postgresql.sql
    ejecutar guayacan_prueba specs/modelo-datos/datos_iniciales.sql
    [ "$prueba" = pruebas_adopcion ] && ejecutar guayacan_prueba specs/modelo-datos/apendice_a_adopcion.sql
    salida=$(psql_en guayacan_prueba < "specs/casos-prueba/$prueba.sql" 2>&1 || true)
    if ! grep -q 'TODAS LAS PRUEBAS PASARON' <<<"$salida"; then
      echo "$salida"; echo "Falló la batería $prueba"; exit 1
    fi
    echo '  TODAS LAS PRUEBAS PASARON'
  done
  psql_en postgres -q -c 'drop database if exists guayacan_prueba'
fi

if [ "$REINICIAR" = 1 ]; then
  read -r -p 'Esto BORRA la base guayacan. Escriba SI para continuar: ' r
  [ "$r" = SI ] || { echo 'Cancelado.'; exit 1; }
  psql_en postgres -q -c "select pg_terminate_backend(pid) from pg_stat_activity where datname='guayacan' and pid<>pg_backend_pid()"
  psql_en postgres -q -c 'drop database if exists guayacan' -c 'create database guayacan'
fi

echo 'Cargando la base guayacan'
cargar_modelo guayacan
ejecutar guayacan backend/sql/preparar_api.sql -v "clave_api=$CLAVE_API"
echo 'Base lista. Siguiente paso: cd backend && python manage.py migrate --database=admin'
