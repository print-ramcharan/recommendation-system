from datetime import datetime
from typing import Optional, Any
from sqlalchemy import BigInteger, Text, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.api.models.base import Base

class Article(Base):
    __tablename__ = "articles"

    article_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    tags: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    events: Mapped[list["Event"]] = relationship(
        "Event",
        back_populates="article",
        cascade="all, delete-orphan"
    )