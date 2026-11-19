from pydantic import BaseModel, ConfigDict
from uuid import UUID


class AIReviewCreate(BaseModel):
    """Schema for creating an AI review record."""
    finding_id: UUID
    explanation: str
    impact: str
    suggested_fix: str
    fixed_code: str


class AIReviewResponse(BaseModel):
    """Schema for returning AI-assisted review details."""
    id: UUID
    finding_id: UUID
    explanation: str
    impact: str
    suggested_fix: str
    fixed_code: str

    model_config = ConfigDict(from_attributes=True)
