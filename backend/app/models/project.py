from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.database import Base, GUID


class Project(Base):
    """Project entity representing a codebase under review."""
    __tablename__ = "projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="projects")
    scans = relationship("Scan", back_populates="project", cascade="all, delete-orphan", order_by="desc(Scan.created_at)")

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name} user_id={self.user_id}>"
