# Primer día en GuayacanERP

Meta del día: tener la base cargada con sus 339 pruebas en verde (215 v5, 90 de regresión v4 y 34 del Apéndice A),
la API respondiendo y la PWA abierta en el navegador.

## 1. Instalar y levantar todo

Siga `INSTALAR.md` en la raíz del repositorio: programas, `.env`, base de datos con `scripts/cargar_base.ps1 -Pruebas`,
backend, frontend y servicios, con los comandos para PowerShell y VS Code.

## 2. Comprobar que funciona

1. `http://localhost:8000/api/docs/`: la documentación de la API. Ingrese con `POST /api/v1/auth/token/` usando un
   usuario de los datos iniciales (el administrador necesita doble factor en producción; en desarrollo se omite).
2. `http://localhost:4200`: la PWA. Desconecte el wifi: la barra dice «Sin conexión» y lo capturado queda en la cola.
3. Abra un módulo cualquiera (por ejemplo Adopción): verá la lista de sus casos de uso por construir.
4. Llame a una acción por construir, por ejemplo `POST /api/v1/adopcion/bienes/1/siembra/`: responde 501 con su
   caso de uso (ADO-03). Así se reconoce lo que falta.

## 3. Cómo leer el código

Todo el código está comentado en español. Cada archivo empieza diciendo **qué hace, cómo y para qué**, y las líneas
que no son obvias tienen su explicación. Orden sugerido:

1. `backend/guayacan/contexto.py` y `backend/guayacan/db.py`: cómo cada petición fija la finca y el usuario en
   PostgreSQL (seguridad por filas).
2. `backend/guayacan/errores.py`: cómo una regla de la base se convierte en un mensaje para la persona.
3. `backend/apps/<su_modulo>/`: `models.py` (tablas), `serializers.py`, `views.py`, `urls.py`, `services.py`
   (donde va la lógica) y `tests/`.
4. `frontend/src/app/core/`: sesión, finca y la cola sin conexión.
5. `docs/desarrollo/04_archivos_de_configuracion.md`: para qué sirve cada archivo de configuración (los JSON no
   admiten comentarios, por eso se explican allí).

## 4. Lectura obligatoria

1. Documento técnico: Cómo usar, Arquitectura, Modelo de dominio, Convenciones (sección 10) y Apéndice A.
2. ADR 0002 a 0007 en `docs/adr/`.
3. La pestaña de casos de uso de su módulo y el `README.md` de su app en `backend/apps/<esquema>/`.
