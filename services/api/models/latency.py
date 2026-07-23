import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from services.api.models.base import Base

class LatencyProfile(Base):
    __tablename__ = "latency_profiles"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String, index=True, nullable=False)
    duration_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
