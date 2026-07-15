import pytest
from datetime import datetime, timedelta
from ml.embeddings.reranking import rerank_candidates
from services.api.models.article import Article

def test_rerank_candidates_freshness_and_boost():
    now = datetime.utcnow()
    
    art_old = Article(
        article_id=1,
        title="Old Tech Article",
        category="tech",
        publish_time=now - timedelta(days=5),
        author_id=1234
    )
    
    art_new = Article(
        article_id=2,
        title="New Sports Article",
        category="sports",
        publish_time=now - timedelta(minutes=15),
        author_id=1234
    )
    
    similarity_scores = {
        1: 0.8,
        2: 0.7
    }
    
    # Rerank with "tech" interest
    ranked = rerank_candidates(
        articles=[art_old, art_new],
        similarity_scores=similarity_scores,
        preferred_topics=["tech"]
    )
    
    # Article 2 (new) should rank first because Article 1 (old) has decayed significantly
    assert ranked[0].article_id == 2
