from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import ProjectModel

APP_VERSION = "7.0.0-phase1.1"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ucan_enterprise.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="UCAN Reality Lab Enterprise API",
    version=APP_VERSION,
    description="API persistente para gestión de proyectos de UCAN Reality Lab Enterprise.",
    lifespan=lifespan,
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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    course: str
    description: str
    academic_level: str
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


def clean(value: str) -> str:
    return " ".join(value.split())


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict:
    database_ok = False
    database_error = None
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    except SQLAlchemyError as exc:
        database_error = str(exc)

    return {
        "ok": database_ok,
        "service": "ucan-reality-lab-enterprise-api",
        "version": APP_VERSION,
        "database": "connected" if database_ok else "unavailable",
        "database_error": database_error,
        "redis_url_configured": bool(REDIS_URL),
        "phase": 1,
        "increment": "persistence",
    }


@app.get("/api/projects", response_model=list[Project])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectModel]:
    statement = select(ProjectModel).order_by(ProjectModel.updated_at.desc())
    return list(db.scalars(statement).all())


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectModel:
    project = ProjectModel(
        title=clean(payload.title),
        course=clean(payload.course),
        description=payload.description.strip(),
        academic_level=clean(payload.academic_level),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> ProjectModel:
    project = db.get(ProjectModel, str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@app.patch("/api/projects/{project_id}", response_model=Project)
def update_project(project_id: UUID, payload: ProjectUpdate, db: Session = Depends(get_db)) -> ProjectModel:
    project = db.get(ProjectModel, str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if isinstance(value, str):
            value = clean(value) if key != "description" else value.strip()
        setattr(project, key, value)

    project.updated_at = datetime.now(timezone.utc)
    project.version += 1
    db.commit()
    db.refresh(project)
    return project


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: UUID, db: Session = Depends(get_db)) -> Response:
    project = db.get(ProjectModel, str(project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    db.delete(project)
    db.commit()
    return Response(status_code=204)
