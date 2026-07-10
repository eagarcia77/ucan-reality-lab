from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_VERSION = "7.0.0-phase1"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ucan:ucan@db:5432/ucan")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(
    title="UCAN Reality Lab Enterprise API",
    version=APP_VERSION,
    description="API inicial para gestión de proyectos de UCAN Reality Lab Enterprise.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:8170").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    course: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=2000)
    academic_level: str = Field(default="Subgraduado", max_length=60)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    course: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    academic_level: str | None = Field(default=None, max_length=60)
    status: str | None = Field(default=None, pattern="^(draft|in_review|published|archived)$")


class Project(BaseModel):
    id: UUID
    title: str
    course: str
    description: str
    academic_level: str
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


# Repositorio temporal para validar el flujo de la Fase 1.
# En el siguiente incremento se sustituirá por PostgreSQL/SQLAlchemy.
PROJECTS: dict[UUID, Project] = {}


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "ucan-reality-lab-enterprise-api",
        "version": APP_VERSION,
        "database_url_configured": bool(DATABASE_URL),
        "redis_url_configured": bool(REDIS_URL),
        "phase": 1,
    }


@app.get("/api/projects", response_model=list[Project])
def list_projects() -> list[Project]:
    return sorted(PROJECTS.values(), key=lambda project: project.updated_at, reverse=True)


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    now = datetime.now(timezone.utc)
    project = Project(
        id=uuid4(),
        title=payload.title.strip(),
        course=payload.course.strip(),
        description=payload.description.strip(),
        academic_level=payload.academic_level.strip(),
        status="draft",
        created_at=now,
        updated_at=now,
        version=1,
    )
    PROJECTS[project.id] = project
    return project


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: UUID) -> Project:
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@app.patch("/api/projects/{project_id}", response_model=Project)
def update_project(project_id: UUID, payload: ProjectUpdate) -> Project:
    current = PROJECTS.get(project_id)
    if not current:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if isinstance(value, str):
            changes[key] = value.strip()

    updated = current.model_copy(
        update={
            **changes,
            "updated_at": datetime.now(timezone.utc),
            "version": current.version + 1,
        }
    )
    PROJECTS[project_id] = updated
    return updated


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: UUID) -> None:
    if project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    del PROJECTS[project_id]
