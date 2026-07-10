# UCAN Reality Lab Enterprise v7.0 — Fase 1

Esta carpeta contiene la base ejecutable de la arquitectura Enterprise. La versión 6.0 del directorio principal permanece intacta.

## Servicios

- `frontend`: panel accesible con inicio de sesión y gestión de proyectos.
- `backend`: API FastAPI con PostgreSQL, autenticación JWT y control por roles.
- `db`: PostgreSQL para usuarios y proyectos persistentes.
- `redis`: cola y caché para análisis futuros.
- `minio`: almacenamiento de recursos, modelos y paquetes exportados.

## Configuración inicial

Desde la carpeta `enterprise`, copie el archivo de ejemplo:

```bash
cp .env.example .env
```

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edite `.env` y cambie, como mínimo:

```text
JWT_SECRET
ADMIN_EMAIL
ADMIN_PASSWORD
POSTGRES_PASSWORD
MINIO_ROOT_PASSWORD
```

No publique el archivo `.env` en GitHub.

## Ejecutar

```bash
docker compose up --build -d
```

Abra:

```text
http://localhost:8170
```

Verifique la API:

```text
http://localhost:8170/api/health
```

Consola de MinIO:

```text
http://localhost:8171
```

## Primer acceso

Use el correo y la contraseña definidos en:

```text
ADMIN_EMAIL
ADMIN_PASSWORD
```

El sistema crea automáticamente la primera cuenta administradora si todavía no existe.

## Roles

- `admin`: ve todos los proyectos y administra usuarios.
- `professor`: crea, edita y elimina sus propios proyectos.
- `reviewer`: revisa proyectos autorizados y puede actualizar su estado; en este incremento todavía no existe asignación cruzada de proyectos.

## Cambio de esquema durante desarrollo

Este incremento añade tablas de usuarios y propiedad de proyectos. Si utilizó una versión anterior de la rama, reinicie la base de desarrollo:

```bash
docker compose down -v
docker compose up --build -d
```

Este comando elimina únicamente los volúmenes de esta instalación de desarrollo.

## Pruebas del backend

```bash
cd backend
python -m pip install -r requirements.txt
pytest -q
```

## Funciones verificables

1. Inicio de sesión mediante JWT.
2. Cuenta administradora inicial configurable.
3. Creación de usuarios por el administrador.
4. Roles `admin`, `professor` y `reviewer`.
5. Proyectos persistentes en PostgreSQL.
6. Cada profesor visualiza sus propios proyectos.
7. El administrador puede consultar todos los proyectos.
8. API protegida: las rutas de proyectos requieren autenticación.
9. Interfaz accesible con sesión persistente en el navegador.
10. Pruebas automatizadas del flujo de autenticación y proyectos.

## Próximo incremento

- Alembic para migraciones controladas.
- Asignación de revisores a proyectos.
- Historial completo de versiones.
- Carga segura de archivos a MinIO.
- Registro de auditoría de acciones.
