from pydantic import BaseModel, Field
from datetime import datetime

class EvaluationRequest(BaseModel):
    user_id: int = Field(..., description="Target User ID for quality metrics evaluation")
    k: int = Field(default=10, ge=1, le=100, description="Recommendation cutoff limit (k)")

class EvaluationResponse(BaseModel):
    id: int
    user_id: int
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float
    k: int
    timestamp: datetime

    class Config:
        from_attributes = True
