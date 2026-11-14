<#
  cargar_base.ps1 · Carga la base de datos de GuayacanERP en el contenedor «postgres» de docker-compose (Windows).

  QUÉ HACE, EN ORDEN
    1. Lee POSTGRES_API_CLAVE del archivo .env.
    2. (Opcional, -Pruebas) Corre las tres baterías de reglas (v5, v4 y Apéndice A), cada una en una base
       temporal «guayacan_prueba» recién cargada, y la borra al final. Así su base de trabajo no se ensucia.
    3. Carga en la base «guayacan»: esquema v5, datos iniciales, Apéndice A (adopción) y preparar_api.sql
       (usuario de la API y esquema django).

  POR QUÉ COPIA LOS ARCHIVOS AL CONTENEDOR
    En PowerShell el símbolo «<» no sirve para pasar un archivo a un programa, y canalizar con Get-Content puede
    dañar las tildes. Copiar el .sql al contenedor y leerlo con psql -f evita los dos problemas.

  USO (desde la raíz del repositorio, con «docker compose up -d postgres» ya corriendo):
    .\scripts\cargar_base.ps1                 # carga la base guayacan (debe estar vacía)
    .\scripts\cargar_base.ps1 -Pruebas        # primero corre las 339 pruebas y luego carga
    .\scripts\cargar_base.ps1 -Reiniciar      # BORRA la base guayacan y la vuelve a cargar (pide confirmación)

  Si Windows no deja ejecutar scripts:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>
param(
  [switch]$Pruebas,
  [switch]$Reiniciar
)
$ErrorActionPreference = 'Stop'  # detenerse ante el primer error

# --- 1. Leer .env (líneas NOMBRE=valor; se ignoran las que empiezan con #) ---
if (-not (Test-Path .env)) { throw 'No existe .env. Copie .env.ejemplo como .env y cambie las claves.' }
$entorno = @{}
foreach ($linea in Get-Content .env -Encoding UTF8) {
  if ($linea -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') { $entorno[$Matches[1]] = $Matches[2].Trim() }
}
$claveApi = $entorno['POSTGRES_API_CLAVE']
if (-not $claveApi) { throw 'Falta POSTGRES_API_CLAVE en .env' }

# Ejecuta un comando de psql dentro del contenedor como el usuario postgres
function Psql([string]$Base, [string[]]$Argumentos) {
  docker compose exec -T postgres psql -U postgres -d $Base @Argumentos
  if ($LASTEXITCODE -ne 0) { throw "psql falló en la base $Base" }
}

# Copia un archivo .sql al contenedor y lo ejecuta en la base indicada
function Ejecutar([string]$Base, [string]$Archivo, [string[]]$Extra = @()) {
  Write-Host "  -> $Archivo" -ForegroundColor DarkGray
  docker compose cp $Archivo postgres:/tmp/carga.sql | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "No se pudo copiar $Archivo al contenedor" }
  Psql $Base (@('-v', 'ON_ERROR_STOP=1', '-q') + $Extra + @('-f', '/tmp/carga.sql'))
}

# Carga esquema + datos + apéndice en una base
function CargarModelo([string]$Base) {
  Ejecutar $Base 'specs/modelo-datos/esquema_postgresql.sql'
  Ejecutar $Base 'specs/modelo-datos/datos_iniciales.sql'
  Ejecutar $Base 'specs/modelo-datos/apendice_a_adopcion.sql'
}

# --- 2. Pruebas (opcional) ---
if ($Pruebas) {
  $baterias = @(
    @{ archivo = 'specs/casos-prueba/pruebas_reglas_v5.sql'; apendice = $false },
    @{ archivo = 'specs/casos-prueba/pruebas_reglas_v4.sql'; apendice = $false },
    @{ archivo = 'specs/casos-prueba/pruebas_adopcion.sql';  apendice = $true  }
  )
  foreach ($b in $baterias) {
    Write-Host "Prueba: $($b.archivo)" -ForegroundColor Cyan
    Psql 'postgres' @('-q', '-c', 'drop database if exists guayacan_prueba', '-c', 'create database guayacan_prueba')
    Ejecutar 'guayacan_prueba' 'specs/modelo-datos/esquema_postgresql.sql'
    Ejecutar 'guayacan_prueba' 'specs/modelo-datos/datos_iniciales.sql'
    if ($b.apendice) { Ejecutar 'guayacan_prueba' 'specs/modelo-datos/apendice_a_adopcion.sql' }
    docker compose cp $b.archivo postgres:/tmp/prueba.sql | Out-Null
    $salida = docker compose exec -T postgres psql -U postgres -d guayacan_prueba -f /tmp/prueba.sql 2>&1 | Out-String
    if ($salida -notmatch 'TODAS LAS PRUEBAS PASARON') {
      Write-Host $salida
      throw "Falló la batería $($b.archivo) (vea arriba la línea FALLA o ERROR)"
    }
    Write-Host '  TODAS LAS PRUEBAS PASARON' -ForegroundColor Green
  }
  Psql 'postgres' @('-q', '-c', 'drop database if exists guayacan_prueba')
}

# --- 3. Base de trabajo ---
if ($Reiniciar) {
  $r = Read-Host 'Esto BORRA la base guayacan y todo lo que tenga. Escriba SI para continuar'
  if ($r -ne 'SI') { Write-Host 'Cancelado.'; exit 1 }
  # Cierra las conexiones abiertas (Django, VS Code) para poder borrar
  Psql 'postgres' @('-q', '-c', "select pg_terminate_backend(pid) from pg_stat_activity where datname='guayacan' and pid<>pg_backend_pid()")
  Psql 'postgres' @('-q', '-c', 'drop database if exists guayacan', '-c', 'create database guayacan')
}
Write-Host 'Cargando la base guayacan' -ForegroundColor Cyan
CargarModelo 'guayacan'
Ejecutar 'guayacan' 'backend/sql/preparar_api.sql' @('-v', "clave_api=$claveApi")
Write-Host 'Base lista. Siguiente paso: cd backend; python manage.py migrate --database=admin' -ForegroundColor Green
