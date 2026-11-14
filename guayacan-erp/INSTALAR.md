# Instalar GuayacanERP en su PC (Windows + VS Code)

Guía paso a paso para dejar funcionando la base de datos, el backend (Django), el frontend (Angular) y los
servicios (FastAPI). Los comandos son para **PowerShell** en la terminal de VS Code (`Ctrl + ñ`). Al final hay
equivalentes para Linux o macOS.

> Regla de oro: los entornos virtuales (`.venv`), las dependencias (`node_modules`), las bases de datos y el
> archivo `.env` con sus claves **nunca** se suben a GitHub. El archivo `.gitignore` ya se encarga de eso.

---

## 0. Programas que necesita (una sola vez)

| Programa | Versión | Para qué | Comprobar |
| --- | --- | --- | --- |
| Git | 2.4x o superior | control de versiones | `git --version` |
| Python | **3.12** (recomendado; 3.13 también sirve) | backend y servicios | `py -3.12 --version` |
| Node.js | 22 LTS | frontend Angular | `node --version` |
| Docker Desktop | reciente, con WSL 2 | PostgreSQL, MongoDB, Redis | `docker compose version` |
| VS Code | reciente | editor | — |

Sobre Python: si tiene 3.14 instalado, puede funcionar, pero algunas librerías (psycopg, Celery) tardan en
publicar versiones para la última versión de Python. Instale 3.12 al lado (python.org) y use `py -3.12` para no
tener problemas; ambas versiones conviven sin estorbarse.

Sin Docker Desktop: instale PostgreSQL 18 con PostGIS (Stack Builder) y pgvector, MongoDB 8 y Redis (o Memurai en
Windows) directamente en su PC, y cargue los `.sql` con `psql -f` en lugar del script del paso 2.

## 1. Abrir el proyecto

1. Descomprima `GuayacanERP_v5.2_final.zip` en una carpeta sin espacios raros, por ejemplo `C:\proyectos\guayacan-erp`.
2. En VS Code: **Archivo > Abrir carpeta…** y elija `guayacan-erp`.
3. VS Code ofrecerá instalar las extensiones recomendadas (`.vscode/extensions.json`): acepte.
4. Cree su archivo de claves:

```powershell
Copy-Item .env.ejemplo .env
code .env      # cambie cada «cambiar…» por una clave propia y guarde
```

## 2. Base de datos (Docker)

```powershell
docker compose up -d --build postgres mongodb redis   # la primera vez tarda (descarga y construye)
docker compose ps                                     # los tres deben decir "running"
.\scripts\cargar_base.ps1 -Pruebas                    # 339 pruebas de reglas y luego carga la base
```

`-Pruebas` corre las tres baterías (215 de la v5, 90 de regresión v4 y 34 del Apéndice A de adopción), cada una en
una base temporal, y después carga la base de trabajo `guayacan` con el esquema, los datos iniciales, el Apéndice A
y el usuario de la API. Para empezar de cero más adelante: `.\scripts\cargar_base.ps1 -Reiniciar`.

Si PowerShell no deja ejecutar el script: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (una sola vez).

## 3. Backend (Django)

```powershell
cd backend
py -3.12 -m venv .venv                 # crea el entorno virtual (carpeta .venv, ignorada por Git)
.\.venv\Scripts\Activate.ps1           # actívelo: el indicador muestra (.venv)
python -m pip install --upgrade pip
pip install -e ".[dev]"                # instala Django, DRF, psycopg, Celery... y las de desarrollo (pytest, ruff)
pip freeze > requirements.lock         # opcional: foto exacta de versiones (también ignorada por Git)
python manage.py migrate --database=admin   # tablas internas de Django en el esquema django (SIEMPRE con --database=admin)
python manage.py check                 # debe decir "System check identified no issues"
pytest                                 # pruebas del backend
python manage.py runserver             # API en http://localhost:8000/api/docs/
```

Importante: `migrate` **sin** `--database=admin` no crea nada, porque el enrutador de bases (`guayacan/db.py`) solo
permite migrar con el usuario dueño. Los modelos del ERP son `managed=False`: sus tablas las crea el SQL, no Django.

Qué instala `pip install -e ".[dev]"` (definido y comentado en `backend/pyproject.toml`): Django 5.2, Django REST
Framework, SimpleJWT (tokens), drf-spectacular (documentación /api/docs), django-cors-headers, psycopg 3
(PostgreSQL), pgvector, argon2-cffi (contraseñas), pyotp (doble factor), Celery con Redis, gunicorn (solo
servidores Linux) y python-dotenv (lee el `.env`); para desarrollo, pytest, pytest-django y ruff.

### Tareas en segundo plano (Celery), en otras dos terminales con el `.venv` activo

```powershell
celery -A config worker -l info --pool=solo   # en Windows hace falta --pool=solo
celery -A config beat -l info                 # reloj de tareas programadas
```

## 4. Frontend (Angular)

En una terminal nueva:

```powershell
cd frontend
npm install        # descarga las dependencias en node_modules (ignorada por Git) y crea package-lock.json
npm start          # abre http://localhost:4200 ; las llamadas a /api van a Django por proxy.conf.json
npm test           # pruebas unitarias
npm run build      # versión de producción en dist/ (ignorada por Git)
```

Suba `package-lock.json` a Git: fija las versiones exactas para todo el equipo (después use `npm ci`).

## 5. Servicios FastAPI (cuando los necesite)

```powershell
cd servicios\agentes
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8100     # http://localhost:8100/docs

cd ..\iot
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8200
```

Cada servicio tiene su propio `.venv`: así sus librerías no se mezclan con las del backend.

## 6. Subir a GitHub por primera vez

```powershell
cd C:\proyectos\guayacan-erp
git init -b main
git add .
git status          # revise: NO deben aparecer .env, .venv, node_modules, dist ni *.sqlite3
git commit -m "GuayacanERP v5.2: paquete inicial"
git remote add origin https://github.com/<su-usuario>/guayacan-erp.git
git push -u origin main
```

Si `git status` muestra algo que no debería subir: `git check-ignore -v <archivo>` dice qué regla lo cubre; si
ya lo había agregado, `git rm --cached <archivo>` lo saca del repositorio sin borrarlo de su PC.

Los manuales (Word, PDF, Excel) vienen en la carpeta `entregables/` del paquete. Esa carpeta está en `.gitignore`:
guárdelos en Drive o adjúntelos a un *release* de GitHub en vez de subirlos al código.

## 7. Problemas frecuentes

| Síntoma | Causa y solución |
| --- | --- |
| `Falta la variable de entorno DJANGO_SECRET_KEY` | No existe `.env` en la raíz o no tiene esa línea |
| `connection refused` puerto 5432 | El contenedor no está corriendo: `docker compose up -d postgres` |
| `password authentication failed for user "guayacan_api"` | La clave de `.env` cambió después de cargar la base: `.\scripts\cargar_base.ps1 -Reiniciar` |
| `ValueError: source code string cannot contain null bytes` | Un archivo `.py` se dañó al copiarlo; vuelva a descomprimirlo y corra `python verificar.py` |
| `migrate` no hace nada | Falta `--database=admin` |
| Celery se queda quieto en Windows | Falta `--pool=solo` |
| `ng` no se reconoce | Use `npm start` (usa el Angular de `node_modules`), no `ng serve` directo |

## 8. Comprobar que nada se dañó al copiar

```powershell
python verificar.py    # compara cada archivo con huellas.json (SHA-256) e informa los distintos o faltantes
```

## Linux o macOS

Igual, cambiando: `cp .env.ejemplo .env`, `./scripts/cargar_base.sh --pruebas`, `python3.12 -m venv .venv`,
`source .venv/bin/activate` y Celery sin `--pool=solo`.
