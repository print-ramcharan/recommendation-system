import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

# Import your Base exactly how your other models do it
from services.api.models.base import Base 

class Event(Base):
    __tablename__ = "events"

    event_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(BigInteger, ForeignKey("articles.article_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Add these relationships to resolve the mapper property lookups
    user = relationship("User", back_populates="events")
    article = relationship("Article", back_populates="events")