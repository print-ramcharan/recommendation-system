from pydantic import BaseModel

class SimilarArticleResponse(BaseModel):
    article_id: int
    title: str
    category: str

    class Config:
        from_attributes = True