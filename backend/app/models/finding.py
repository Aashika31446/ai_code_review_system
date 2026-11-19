from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.database import Base, GUID


class Finding(Base):
    """Finding entity recording a specific code issue or vulnerability."""
    __tablename__ = "findings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    scan_id = Column(GUID(), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    file = Column(String(500), nullable=False)
    line = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)  # security, bug_risk, performance, style, etc.
    severity = Column(String(50), nullable=False)  # critical, high, medium, low
    rule = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)

    # Relationships
    scan = relationship("Scan", back_populates="findings")
    ai_review = relationship("AIReview", back_populates="finding", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Finding id={self.id} file={self.file} line={self.line} severity={self.severity}>"
