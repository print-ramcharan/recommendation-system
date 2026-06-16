from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    article_id: int
    title: str
    category: str

    class Config:
        from_attributes = True