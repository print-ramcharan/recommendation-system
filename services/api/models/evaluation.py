import datetime
from sqlalchemy import Column, Integer, BigInteger, Float, DateTime, ForeignKey
from services.api.models.base import Base

class RecommendationMetric(Base):
    __tablename__ = "recommendation_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    precision_at_k = Column(Float, nullable=False)
    recall_at_k = Column(Float, nullable=False)
    ndcg_at_k = Column(Float, nullable=False)
    k = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
