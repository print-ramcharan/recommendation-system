from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# Database dependency
from services.api.db.database import get_db

# Repositories & Services
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository
from services.api.db.services import RecommendationService

# Schemas
from services.api.schemas.recommendation import RecommendationResponse
from services.api.schemas.article import SimilarArticleResponse

# ML Elements
from ml.embeddings.user_embeddings import compute_user_embedding
from ml.embeddings.qdrant_client import search_by_vector

# Cache Layer Elements
from services.cache.redis_client import get_cached_user_embedding, set_cached_user_embedding

# Prometheus Custom Metrics Trackers
from services.api.metrics import RECOMMENDATION_LATENCY, CACHE_HITS, CACHE_MISSES


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
    # Wrap the tracking block context to track real-time retrieval duration execution
    with RECOMMENDATION_LATENCY.time():
        user_repo = UserRepository(db)
        event_repo = EventRepository(db)
        article_repo = ArticleRepository(db)
        
        # Verify user profile exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User profile records not found.")
            
        # STAGE 0: Feature Store Read Look-up (O(1))
        user_vector = get_cached_user_embedding(user_id)
        
        if user_vector is not None:
            CACHE_HITS.inc()
            print(f"⚡ [Cache Hit] Retrieved user_embedding:{user_id} instantly from Redis Feature Store.")
        else:
            CACHE_MISSES.inc()
            print(f"🐢 [Cache Miss] Computing dynamic user vector profile on demand for user {user_id}.")
            clicked_ids = await event_repo.get_user_clicked_articles(user_id)
            user_vector = compute_user_embedding(clicked_ids, fallback_interests=user.interests)
            set_cached_user_embedding(user_id, user_vector, ttl=3600)

        # Re-fetch interaction history to guarantee deduplication slicing
        clicked_ids = await event_repo.get_user_clicked_articles(user_id)
        
        # STAGE 1: Vector Search (Fetch k + length of history to guarantee enough clean options)
        search_limit = k + len(clicked_ids) + 10
        raw_matches = search_by_vector(query_vector=user_vector, limit=search_limit)
        
        # STAGE 2: Post-Retrieval Heuristic Filtering
        seen_set = set(clicked_ids)
        filtered_candidate_ids = [point.id for point in raw_matches if point.id not in seen_set][:k]
        
        # Metadata Hydration from PostgreSQL
        recommended_articles = await article_repo.get_articles_by_ids(filtered_candidate_ids)
        return recommended_articles