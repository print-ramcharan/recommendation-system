from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

# Database dependency
from services.api.db.database import get_db

# Repositories & Services
from services.api.db.repository import UserRepository, ArticleRepository, EventRepository, ExclusionRepository
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
    exclusion_repo = ExclusionRepository(db)

    service = RecommendationService(
        user_repo=user_repo,
        article_repo=article_repo,
        event_repo=event_repo,
        exclusion_repo=exclusion_repo
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
    response: Response,
    k: int = 10,
    db: AsyncSession = Depends(get_db)
):
    # Wrap the tracking block context to track real-time retrieval duration execution
    import time
    start_time = time.perf_counter()
    with RECOMMENDATION_LATENCY.time():
        user_repo = UserRepository(db)
        event_repo = EventRepository(db)
        article_repo = ArticleRepository(db)
        
        # Verify user profile exists
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User profile records not found.")
            
        # A/B Experiment Traffic Split Allocation (3-way split: Group A, B, and C)
        bucket = user_id % 3
        if bucket == 0:
            experiment_group = "group-a"
        elif bucket == 1:
            experiment_group = "group-b"
        else:
            experiment_group = "group-c"
            
        response.headers["X-Experiment-Group"] = experiment_group
        
        if experiment_group == "group-b":
            print(f"📊 [A/B Test] Routing user {user_id} to Group B (Heuristic Popularity Baseline).")
            # Fetch popular clicked articles from Postgres
            popular_ids = await event_repo.get_popular_articles(limit=k * 2)
            # Filter out seen articles
            clicked_ids = await event_repo.get_user_clicked_articles(user_id)
            seen_set = set(clicked_ids)
            filtered_ids = [aid for aid in popular_ids if aid not in seen_set][:k]
            
            # Fallback to category list if not enough popular clicked articles
            if len(filtered_ids) < k:
                # Fetch baseline articles matching first interest
                interests_dict = user.interests or {}
                topics = interests_dict.get("preferred_topics", ["tech"]) if isinstance(interests_dict, dict) else ["tech"]
                interest = topics[0] if topics else "tech"
                category_articles = await article_repo.get_by_category(interest, limit=k * 2)
                for art in category_articles:
                    if art.article_id not in seen_set and art.article_id not in filtered_ids:
                        filtered_ids.append(art.article_id)
                        if len(filtered_ids) == k:
                            break
                            
            result_articles = await article_repo.get_articles_by_ids(filtered_ids[:k])
        else:
            # STAGE 0: Feature Store Read Look-up (O(1)) for Group A and Group C
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
            
            # STAGE 1: Vector Search (Fetch larger pool for re-ranking)
            search_limit = max(50, k * 3)
            raw_matches = search_by_vector(query_vector=user_vector, limit=search_limit)
            
            # STAGE 2: Post-Retrieval Heuristic Filtering
            seen_set = set(clicked_ids)
            filtered_candidate_ids = [point.id for point in raw_matches if point.id not in seen_set]
            
            # Metadata Hydration from PostgreSQL
            candidate_articles = await article_repo.get_articles_by_ids(filtered_candidate_ids)

            if experiment_group == "group-c":
                print(f"📊 [A/B Test] Routing user {user_id} to Group C (NCF Neural Re-ranking).")
                # STAGE 3: NCF model predictor scoring
                from ml.training.model_loader import NeuralCollaborativeFilteringPredictor
                predictor = NeuralCollaborativeFilteringPredictor()
                scores = predictor.predict_score(user_id, [art.article_id for art in candidate_articles])
                
                # Sort candidate articles descending by their neural scores
                candidate_articles.sort(key=lambda art: scores.get(art.article_id, 0.0), reverse=True)
                result_articles = candidate_articles[:k]
            else:
                print(f"📊 [A/B Test] Routing user {user_id} to Group A (Personalized Vector Search with Heuristic decay).")
                # Map Qdrant similarity scores
                similarity_scores = {point.id: point.score for point in raw_matches}
                
                # STAGE 3: Heuristic Re-ranking (freshness decay & category boost)
                interests_dict = user.interests or {}
                preferred_topics = interests_dict.get("preferred_topics", []) if isinstance(interests_dict, dict) else []
                
                from ml.embeddings.reranking import rerank_candidates
                recommended_articles = rerank_candidates(
                    articles=candidate_articles,
                    similarity_scores=similarity_scores,
                    preferred_topics=preferred_topics
                )[:k]
                result_articles = recommended_articles
                
        # Record SLA profiling duration sample
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        from services.api.db.repository import LatencyRepository
        from services.api.db.services import ProfilingService
        latency_repo = LatencyRepository(db)
        profiling_service = ProfilingService(latency_repo)
        await profiling_service.record_sample(route="/recommendations/personalized", duration_ms=duration_ms)
        
        return result_articles