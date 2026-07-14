from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .cloud import masked_database_target, wait_for_database
from .database import Base, DATABASE_URL, engine, get_db
from .models import ProjectModel, UserModel

APP_VERSION = "7.2.1-university-registration"
REDIS_URL = os.getenv("REDIS_URL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-development-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@ucan.local").lower().strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
ALLOWED_EMAIL_DOMAINS = tuple(
    domain.strip().lower().lstrip("@")
    for domain in os.getenv("ALLOWED_EMAIL_DOMAINS", "sangerman.inter.edu,inter.edu").split(",")
    if domain.strip()
)

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
ALLOWED_ROLES = {"admin", "professor", "reviewer"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    wait_for_database(engine)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        existing = db.scalar(select(UserModel).where(UserModel.email == ADMIN_EMAIL))
        if not existing:
            db.add(
                UserModel(
                    email=ADMIN_EMAIL,
                    full_name="Administrador UCAN",
                    password_hash=password_hash.hash(ADMIN_PASSWORD),
                    role="admin",
                )
            )
            db.commit()
    yield


app = FastAPI(
    title="UCAN Reality Lab Enterprise API",
    version=APP_VERSION,
    description="API persistente, autenticada y preparada para despliegue en la nube.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:8170").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegistrationRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=10, max_length=128)


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="professor", pattern="^(admin|professor|reviewer)$")


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class RegistrationConfig(BaseModel):
    enabled: bool = True
    allowed_domains: list[str]
    default_role: str = "professor"


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
    owner_id: UUID
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


def normalized_email(value: str) -> str:
    return value.lower().strip()


def email_domain(value: str) -> str:
    return normalized_email(value).rsplit("@", 1)[-1]


def require_university_email(value: str) -> str:
    email = normalized_email(value)
    domain = email_domain(email)
    if domain not in ALLOWED_EMAIL_DOMAINS:
        allowed = ", ".join(f"@{item}" for item in ALLOWED_EMAIL_DOMAINS)
        raise HTTPException(
            status_code=422,
            detail=f"Utilice un correo electrónico institucional autorizado: {allowed}",
        )
    return email


def create_access_token(user: UserModel) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user.id,
            "role": user.role,
            "email": user.email,
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión inválida o expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_error
    except jwt.PyJWTError as exc:
        raise credentials_error from exc
    user = db.get(UserModel, user_id)
    if not user or not user.is_active:
        raise credentials_error
    return user


def require_roles(*roles: str):
    def dependency(user: UserModel = Depends(current_user)) -> UserModel:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="No tiene permisos para realizar esta acción")
        return user
    return dependency


def accessible_project(db: Session, project_id: UUID, user: UserModel) -> ProjectModel:
    project = db.get(ProjectModel, str(project_id))
    if not project or (user.role != "admin" and project.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        database_ok, database_error = True, None
    except SQLAlchemyError as exc:
        database_ok, database_error = False, exc.__class__.__name__
    return {
        "ok": database_ok,
        "service": "ucan-reality-lab-enterprise-api",
        "version": APP_VERSION,
        "database": "connected" if database_ok else "unavailable",
        "database_target": masked_database_target(DATABASE_URL),
        "database_error": database_error,
        "redis_url_configured": bool(REDIS_URL),
        "port": int(os.getenv("PORT", "8000")),
        "registration_enabled": True,
        "allowed_email_domains": list(ALLOWED_EMAIL_DOMAINS),
        "phase": 1,
        "increment": "university-email-registration",
    }


@app.get("/api/auth/registration-config", response_model=RegistrationConfig)
def registration_config() -> RegistrationConfig:
    return RegistrationConfig(allowed_domains=list(ALLOWED_EMAIL_DOMAINS))


@app.post("/api/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: RegistrationRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = require_university_email(str(payload.email))
    if db.scalar(select(UserModel).where(UserModel.email == email)):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo electrónico")
    user = UserModel(
        email=email,
        full_name=clean(payload.full_name),
        password_hash=password_hash.hash(payload.password),
        role="professor",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user), user=User.model_validate(user))


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(UserModel).where(UserModel.email == normalized_email(str(payload.email))))
    if not user or not password_hash.verify(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Correo electrónico o contraseña incorrectos")
    return TokenResponse(access_token=create_access_token(user), user=User.model_validate(user))


@app.get("/api/auth/me", response_model=User)
def me(user: UserModel = Depends(current_user)) -> UserModel:
    return user


@app.get("/api/users", response_model=list[User])
def list_users(_: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[UserModel]:
    return list(db.scalars(select(UserModel).order_by(UserModel.created_at.desc())).all())


@app.post("/api/users", response_model=User, status_code=201)
def create_user(payload: UserCreate, _: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> UserModel:
    email = normalized_email(str(payload.email))
    if db.scalar(select(UserModel).where(UserModel.email == email)):
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese correo electrónico")
    user = UserModel(
        email=email,
        full_name=clean(payload.full_name),
        password_hash=password_hash.hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/projects", response_model=list[Project])
def list_projects(user: UserModel = Depends(current_user), db: Session = Depends(get_db)) -> list[ProjectModel]:
    statement = select(ProjectModel).order_by(ProjectModel.updated_at.desc())
    if user.role != "admin":
        statement = statement.where(ProjectModel.owner_id == user.id)
    return list(db.scalars(statement).all())


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate, user: UserModel = Depends(require_roles("admin", "professor")), db: Session = Depends(get_db)) -> ProjectModel:
    project = ProjectModel(
        owner_id=user.id,
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
def get_project(project_id: UUID, user: UserModel = Depends(current_user), db: Session = Depends(get_db)) -> ProjectModel:
    return accessible_project(db, project_id, user)


@app.patch("/api/projects/{project_id}", response_model=Project)
def update_project(project_id: UUID, payload: ProjectUpdate, user: UserModel = Depends(require_roles("admin", "professor", "reviewer")), db: Session = Depends(get_db)) -> ProjectModel:
    project = accessible_project(db, project_id, user)
    changes = payload.model_dump(exclude_unset=True)
    if user.role == "reviewer" and set(changes) - {"status"}:
        raise HTTPException(status_code=403, detail="El revisor solo puede actualizar el estado")
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
def delete_project(project_id: UUID, user: UserModel = Depends(require_roles("admin", "professor")), db: Session = Depends(get_db)) -> Response:
    project = accessible_project(db, project_id, user)
    db.delete(project)
    db.commit()
    return Response(status_code=204)
