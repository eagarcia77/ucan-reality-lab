from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .main import accessible_project, current_user
from .models import AuthoringWorkspaceModel, UserModel

router = APIRouter(prefix="/api/projects", tags=["Authoring workspace"])


class WorkspacePayload(BaseModel):
    content: dict = Field(default_factory=dict)
    quality_score: int = Field(default=0, ge=0, le=100)


class WorkspaceResponse(BaseModel):
    project_id: UUID
    content: dict
    quality_score: int
    updated_at: datetime


def _response(workspace: AuthoringWorkspaceModel) -> WorkspaceResponse:
    try:
        content = json.loads(workspace.content_json or "{}")
    except json.JSONDecodeError:
        content = {}
    return WorkspaceResponse(
        project_id=UUID(workspace.project_id),
        content=content,
        quality_score=workspace.quality_score,
        updated_at=workspace.updated_at,
    )


@router.get("/{project_id}/workspace", response_model=WorkspaceResponse)
def get_workspace(
    project_id: UUID,
    user: UserModel = Depends(current_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    accessible_project(db, project_id, user)
    workspace = db.scalar(select(AuthoringWorkspaceModel).where(AuthoringWorkspaceModel.project_id == str(project_id)))
    if not workspace:
        now = datetime.now(timezone.utc)
        return WorkspaceResponse(project_id=project_id, content={}, quality_score=0, updated_at=now)
    return _response(workspace)


@router.put("/{project_id}/workspace", response_model=WorkspaceResponse)
def save_workspace(
    project_id: UUID,
    payload: WorkspacePayload,
    user: UserModel = Depends(current_user),
    db: Session = Depends(get_db),
) -> WorkspaceResponse:
    project = accessible_project(db, project_id, user)
    if user.role == "reviewer":
        raise HTTPException(status_code=403, detail="El revisor no puede modificar la actividad")
    workspace = db.scalar(select(AuthoringWorkspaceModel).where(AuthoringWorkspaceModel.project_id == str(project_id)))
    if not workspace:
        workspace = AuthoringWorkspaceModel(project_id=str(project_id))
        db.add(workspace)
    workspace.content_json = json.dumps(payload.content, ensure_ascii=False)
    workspace.quality_score = payload.quality_score
    workspace.updated_at = datetime.now(timezone.utc)
    project.updated_at = workspace.updated_at
    project.version += 1
    db.commit()
    db.refresh(workspace)
    return _response(workspace)
