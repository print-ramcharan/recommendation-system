from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Database dependency
from services.api.db.database import get_db

# Repositories & Services
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository
from services.api.db.services import RecommendationService

# Schemas
from services.api.schemas.recommendation import RecommendationResponse


from fastapi import HTTPException
from services.api.schemas.article import SimilarArticleResponse # Reusing our lean metadata schema
from ml.embeddings.user_embeddings import compute_user_embedding
from ml.embeddings.qdrant_client import search_by_vector


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

@router.get("/personalized/{user_id}", response_model=list[SimilarArticleResponse])
async def get_personalized_recommendations(
    user_id: int,
    k: int = 10,
    db: AsyncSession = Depends(get_db)
):
    user_repo = UserRepository(db)
    event_repo = EventRepository(db)
    article_repo = ArticleRepository(db)
    
    # 1. Fetch user context record
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User profile records not found.")
        
    # 2. Extract past history using your existing repository tracker
    clicked_ids = await event_repo.get_user_clicked_articles(user_id)
    
    # 3. Compute dynamic user profile embedding vector
    user_vector = compute_user_embedding(clicked_ids, fallback_interests=user.interests)
    
    # 4. STAGE 1: Vector Search (Fetch k + length of history to guarantee enough clean options)
    search_limit = k + len(clicked_ids) + 10
    raw_matches = search_by_vector(query_vector=user_vector, limit=search_limit)
    
    # 5. STAGE 2: Post-Retrieval Heuristic Filtering
    seen_set = set(clicked_ids)
    filtered_candidate_ids = [point.id for point in raw_matches if point.id not in seen_set][:k]
    
    # 6. Metadata Hydration from PostgreSQL
    recommended_articles = await article_repo.get_articles_by_ids(filtered_candidate_ids)
    return recommended_articles