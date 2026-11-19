from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from app.schemas.ai_review import AIReviewResponse


class FindingCreate(BaseModel):
    """Schema for recording a detected issue."""
    scan_id: UUID
    file: str
    line: int
    category: str
    severity: str
    rule: str
    message: str


class FindingResponse(BaseModel):
    """Schema for returning finding details."""
    id: UUID
    scan_id: UUID
    file: str
    line: int
    category: str
    severity: str
    rule: str
    message: str
    ai_review: Optional[AIReviewResponse] = None

    model_config = ConfigDict(from_attributes=True)
