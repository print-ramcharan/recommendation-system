from pydantic import BaseModel
from uuid import UUID

class EventCreate(BaseModel):
    user_id: int
    article_id: int
    event_type: str

class EventResponse(BaseModel):
    event_id: UUID  # Kept as UUID to perfectly map the incoming SQLAlchemy attribute
    user_id: int
    article_id: int
    event_type: str

    class Config:
        from_attributes = True