from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.database import Base, GUID


class AIReview(Base):
    """AIReview entity holding LLM-assisted analysis and suggested fixes for a finding."""
    __tablename__ = "ai_reviews"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    finding_id = Column(
        GUID(),
        ForeignKey("findings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    explanation = Column(Text, nullable=False)
    impact = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=False)
    fixed_code = Column(Text, nullable=False)

    # Relationships
    finding = relationship("Finding", back_populates="ai_review")

    def __repr__(self) -> str:
        return f"<AIReview id={self.id} finding_id={self.finding_id}>"
