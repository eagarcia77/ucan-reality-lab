from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .main import User, clean, normalized_email, password_hash, require_roles, require_university_email
from .models import ProjectModel, UserModel

router = APIRouter(prefix="/api/admin/users", tags=["User administration"])
projects_router = APIRouter(prefix="/api/admin/projects", tags=["Project administration"])


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=160)
    password: str = Field(min_length=10, max_length=128)
    role: str = Field(default="professor", pattern="^(admin|professor|reviewer)$")


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=160)
    role: str | None = Field(default=None, pattern="^(admin|professor|reviewer)$")
    is_active: bool | None = None


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)


class AdminProject(BaseModel):
    id: UUID
    owner_id: UUID
    owner_name: str
    owner_email: EmailStr
    title: str
    course: str
    description: str
    academic_level: str
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


@router.get("", response_model=list[User])
def list_all(_: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[UserModel]:
    return list(db.scalars(select(UserModel).order_by(UserModel.created_at.desc())).all())


@router.post("", response_model=User, status_code=201)
def create_user(payload: AdminUserCreate, _: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> UserModel:
    email = require_university_email(str(payload.email))
    if db.scalar(select(UserModel).where(UserModel.email == email)):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    user = UserModel(email=email, full_name=clean(payload.full_name), password_hash=password_hash.hash(payload.password), role=payload.role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=User)
def update_user(user_id: UUID, payload: AdminUserUpdate, admin: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> UserModel:
    user = db.get(UserModel, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    changes = payload.model_dump(exclude_unset=True)
    if str(user.id) == str(admin.id) and changes.get("is_active") is False:
        raise HTTPException(status_code=400, detail="No puede desactivar su propia cuenta")
    for key, value in changes.items():
        setattr(user, key, clean(value) if key == "full_name" else value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/reset-password")
def reset_password(user_id: UUID, payload: AdminPasswordReset, _: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.get(UserModel, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.password_hash = password_hash.hash(payload.new_password)
    user.is_active = True
    db.commit()
    return {"message": "Contraseña actualizada correctamente"}


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: UUID, admin: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> Response:
    user = db.get(UserModel, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if str(user.id) == str(admin.id):
        raise HTTPException(status_code=400, detail="No puede eliminar su propia cuenta")
    db.delete(user)
    db.commit()
    return Response(status_code=204)


@projects_router.get("", response_model=list[AdminProject])
def list_all_projects(_: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[AdminProject]:
    rows = db.execute(
        select(ProjectModel, UserModel)
        .join(UserModel, ProjectModel.owner_id == UserModel.id)
        .order_by(ProjectModel.updated_at.desc())
    ).all()
    return [
        AdminProject(
            id=UUID(project.id),
            owner_id=UUID(project.owner_id),
            owner_name=owner.full_name,
            owner_email=owner.email,
            title=project.title,
            course=project.course,
            description=project.description,
            academic_level=project.academic_level,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
            version=project.version,
        )
        for project, owner in rows
    ]
