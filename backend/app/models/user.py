from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.database import Base, GUID


class User(Base):
    """User account model for authentication and project ownership."""
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} email={self.email}>"
