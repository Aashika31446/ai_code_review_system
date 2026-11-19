from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ScanStatus(str, Enum):
    """Scan status lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanCreate(BaseModel):
    """Schema for initiating a scan."""
    project_id: UUID


class ScanResponse(BaseModel):
    """Schema for scan summary details."""
    id: UUID
    project_id: UUID
    status: str
    total_files: int
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics for code reviews."""
    total_scans: int
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    recent_scans: List[ScanResponse] = []

    model_config = ConfigDict(from_attributes=True)
