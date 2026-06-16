from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Database dependency
from services.api.db.database import get_db

# Repositories & Services
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository
from services.api.db.services import RecommendationService

# Schemas
from services.api.schemas.recommendation import RecommendationResponse

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)

@router.get("/{user_id}", response_model=list[RecommendationResponse])
async def get_recommendations(
    user_id: int,
    k: int = 10,
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    article_repo = ArticleRepository(db)
    event_repo = EventRepository(db)

    service = RecommendationService(
        user_repo=user_repo,
        article_repo=article_repo,
        event_repo=event_repo,
    )

    articles = await service.get_recommendations(
        user_id=user_id,
        k=k,
    )

    return [
        RecommendationResponse.model_validate(a)
        for a in articles
    ]