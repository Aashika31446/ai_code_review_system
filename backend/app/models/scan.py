from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.database import Base, GUID


class Scan(Base):
    """Scan entity recording an execution of code review analysis."""
    __tablename__ = "scans"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed
    total_files = Column(Integer, default=0, nullable=False)
    total_issues = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    medium_count = Column(Integer, default=0, nullable=False)
    low_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan", order_by="Finding.line")

    def __repr__(self) -> str:
        return f"<Scan id={self.id} project_id={self.project_id} status={self.status} issues={self.total_issues}>"
