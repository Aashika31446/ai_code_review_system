from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.project import Project
from app.schemas.project import ProjectCreate


async def get_user_projects(db: AsyncSession, user_id: UUID) -> List[Project]:
    """Retrieves all projects belonging to the given user, ordered by creation date descending."""
    query = (
        select(Project)
        .where(Project.user_id == user_id)
        .options(selectinload(Project.scans))
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_project(db: AsyncSession, user_id: UUID, project_in: ProjectCreate) -> Project:
    """Creates a new project for the given user."""
    project = Project(
        user_id=user_id,
        name=project_in.name.strip(),
        description=project_in.description.strip() if project_in.description else None
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Reload with empty scans relation
    query = (
        select(Project)
        .where(Project.id == project.id)
        .options(selectinload(Project.scans))
    )
    result = await db.execute(query)
    return result.scalar_one()


async def get_project_by_id(db: AsyncSession, project_id: UUID, user_id: UUID) -> Optional[Project]:
    """Retrieves a single project by ID, verifying that the user owns it."""
    query = (
        select(Project)
        .where(Project.id == project_id, Project.user_id == user_id)
        .options(selectinload(Project.scans))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def delete_project(db: AsyncSession, project_id: UUID, user_id: UUID) -> bool:
    """Deletes a project owned by the user. Returns True if deleted, False if not found."""
    project = await get_project_by_id(db, project_id=project_id, user_id=user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not owned by user"
        )

    await db.delete(project)
    await db.commit()
    return True
