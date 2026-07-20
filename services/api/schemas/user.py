from pydantic import BaseModel, Field

class UserInterestsUpdate(BaseModel):
    preferred_topics: list[str] = Field(..., min_items=1, description="List of preferred category topics")
