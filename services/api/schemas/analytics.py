from pydantic import BaseModel, Field

class CategoryCTR(BaseModel):
    category: str = Field(..., description="Article category topic name")
    click_count: int = Field(..., ge=0, description="Total number of recorded click interactions")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Share percentage of total interactions")

class AnalyticsSummaryResponse(BaseModel):
    total_clicks: int = Field(..., ge=0, description="Total count of click interactions across system")
    total_users: int = Field(..., ge=0, description="Total registered user profiles")
    total_articles: int = Field(..., ge=0, description="Total published articles indexed")
    category_breakdown: list[CategoryCTR] = Field(default_factory=list, description="Per-category click breakdown")
