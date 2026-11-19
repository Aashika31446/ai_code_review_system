from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.schemas.scan import ScanResponse


class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(default=None, description="Optional project description")


class ProjectResponse(BaseModel):
    """Schema for returning project information."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    scans: Optional[List[ScanResponse]] = []

    model_config = ConfigDict(from_attributes=True)
