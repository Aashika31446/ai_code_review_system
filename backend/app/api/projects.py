from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import (
    get_user_projects,
    create_project,
    get_project_by_id,
    delete_project
)
from app.utils.security import get_current_user

router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
@router.get("/", response_model=List[ProjectResponse], include_in_schema=False)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all projects belonging to the authenticated user."""
    projects = await get_user_projects(db, current_user.id)
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_new_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new code review project."""
    project = await create_project(db, current_user.id, project_in)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single project by ID along with its associated scan history."""
    project = await get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
async def delete_existing_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a project owned by the authenticated user."""
    await delete_project(db, project_id, current_user.id)
    return {"detail": "Project successfully deleted"}
