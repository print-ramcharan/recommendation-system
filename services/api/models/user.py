from datetime import datetime
from typing import Optional, Any
from sqlalchemy import BigInteger, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.api.models.base import Base

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    interests: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    subscription: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    events: Mapped[list["Event"]] = relationship(
        "Event",
        back_populates="user",
        cascade="all, delete-orphan"
    )