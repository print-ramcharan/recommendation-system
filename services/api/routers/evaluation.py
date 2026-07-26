from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.db.database import get_db
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository, EvaluationRepository
from services.api.db.services import RecommendationService, EvaluationService
from services.api.schemas.evaluation import EvaluationRequest, EvaluationResponse

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.post("/metrics", response_model=EvaluationResponse)
async def evaluate_metrics(
    payload: EvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Computes offline Precision@K, Recall@K, and NDCG@K recommendation quality metrics."""
    user_repo = UserRepository(db)
    article_repo = ArticleRepository(db)
    event_repo = EventRepository(db)
    evaluation_repo = EvaluationRepository(db)

    # 1. Fetch user to verify profile
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    # 2. Get recommendations
    rec_service = RecommendationService(user_repo, article_repo, event_repo)
    recommended_articles = await rec_service.get_recommendations(user_id=payload.user_id, k=payload.k)
    recommended_ids = [art.article_id for art in recommended_articles]

    # 3. Evaluate quality metrics
    eval_service = EvaluationService(evaluation_repo, event_repo)
    record = await eval_service.evaluate_user_recommendations(
        user_id=payload.user_id,
        recommended_ids=recommended_ids,
        k=payload.k
    )
    return EvaluationResponse.model_validate(record)

@router.get("/metrics/{user_id}", response_model=list[EvaluationResponse])
async def get_user_evaluation_history(
    user_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves historical offline evaluation quality scores for a given user."""
    evaluation_repo = EvaluationRepository(db)
    records = await evaluation_repo.get_user_metrics(user_id=user_id, limit=limit)
    return [EvaluationResponse.model_validate(r) for r in records]
