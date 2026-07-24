from pydantic import BaseModel, Field
from datetime import datetime

class ExclusionCreate(BaseModel):
    category: str = Field(..., max_length=100, description="Article category name to exclude")

class ExclusionResponse(BaseModel):
    id: int
    user_id: int
    category: str
    created_at: datetime

    class Config:
        from_attributes = True
