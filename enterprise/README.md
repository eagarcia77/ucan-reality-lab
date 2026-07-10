# UCAN Reality Lab Enterprise v7.0 — Fase 1

Esta carpeta contiene la primera base ejecutable de la arquitectura Enterprise. La versión 6.0 del directorio principal permanece intacta.

## Servicios

- `frontend`: panel accesible para crear y listar proyectos.
- `backend`: API FastAPI con ciclo de vida básico de proyectos.
- `db`: PostgreSQL preparado para persistencia.
- `redis`: cola y caché para análisis futuros.
- `minio`: almacenamiento de recursos, modelos y paquetes exportados.

> En este incremento, el repositorio de proyectos del backend todavía es temporal en memoria. PostgreSQL está incluido y se conectará mediante SQLAlchemy/Alembic en el siguiente incremento de la Fase 1.

## Ejecutar

Desde la carpeta `enterprise`:

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

## Cambiar puertos

Cree un archivo `.env` dentro de `enterprise`:

```text
UCAN_ENTERPRISE_PORT=8175
MINIO_CONSOLE_PORT=8176
POSTGRES_PASSWORD=cambie-esta-clave
MINIO_ROOT_USER=ucanadmin
MINIO_ROOT_PASSWORD=cambie-esta-clave-de-almacenamiento
```

## Pruebas del backend

```bash
cd backend
python -m pip install -r requirements.txt
pytest -q
```

## Funciones verificables de este incremento

1. El stack inicia con Docker Compose.
2. `/api/health` identifica la versión y la fase.
3. El profesor puede crear un proyecto.
4. Los proyectos aparecen en el panel.
5. La API permite consultar, actualizar y eliminar proyectos.
6. El frontend incluye navegación por teclado, estados accesibles y diseño adaptable.

## Próximo incremento

- Persistencia real en PostgreSQL.
- Migraciones con Alembic.
- Usuarios, autenticación y roles.
- Historial de versiones del proyecto.
- Carga segura de archivos a MinIO.
