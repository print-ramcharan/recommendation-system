from datetime import datetime, UTC
import math
from services.api.models.article import Article

def rerank_candidates(
    articles: list[Article],
    similarity_scores: dict[int, float],
    preferred_topics: list[str],
    decay_lambda: float = 0.005,
    category_boost: float = 0.15
) -> list[Article]:
    """
    Applies heuristic re-ranking (Learning-to-Rank baseline) to candidate articles.
    Scores are adjusted based on:
    1. Semantic similarity score from Qdrant
    2. Time-decay freshness penalty
    3. Category alignment boost matching user's preferred topics
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    scored_articles = []
    
    for article in articles:
        sim_score = similarity_scores.get(article.article_id, 0.0)
        
        # 1. Compute time decay (freshness)
        # hours since publication
        time_diff = now - article.publish_time
        hours = max(0, time_diff.total_seconds() / 3600.0)
        decay = math.exp(-decay_lambda * hours)
        
        # 2. Compute category boost
        boost = 1.0
        if article.category in preferred_topics:
            boost += category_boost
            
        # 3. Final heuristic score
        final_score = (sim_score * decay) * boost
        scored_articles.append((article, final_score))
        
    # Sort articles descending by their final heuristic score
    scored_articles.sort(key=lambda x: x[1], reverse=True)
    
    # Return sorted list of Article objects
    return [item[0] for item in scored_articles]
