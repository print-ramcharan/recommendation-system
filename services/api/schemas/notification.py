from pydantic import BaseModel, Field
from datetime import datetime

class NotificationPayload(BaseModel):
    event_type: str = Field(..., description="Type of user interaction event (e.g. click)")
    user_id: int = Field(..., description="Registered user ID initiating the interaction")
    article_id: int = Field(..., description="Target article ID interacted with")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC event recording timestamp")
