from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.db.database import get_db
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository
from services.api.db.services import AnalyticsService
from services.api.schemas.analytics import AnalyticsSummaryResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """Returns aggregated CTR metrics, total counts, and per-category click distributions."""
    user_repo = UserRepository(db)
    article_repo = ArticleRepository(db)
    event_repo = EventRepository(db)

    analytics_service = AnalyticsService(
        user_repo=user_repo,
        article_repo=article_repo,
        event_repo=event_repo
    )

    data = await analytics_service.get_summary_analytics()
    return AnalyticsSummaryResponse.model_validate(data)
