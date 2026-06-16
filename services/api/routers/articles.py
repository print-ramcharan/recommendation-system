from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ml.embeddings.generate_embeddings import model as embedding_model
from ml.embeddings.qdrant_client import search_similar_articles
from services.api.db.database import get_db
from services.api.db.repository import ArticleRepository
from services.api.schemas.article import SimilarArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])

@router.get("/{article_id}/similar", response_model=list[SimilarArticleResponse])
async def get_similar_articles(
    article_id: int, 
    k: int = 5, 
    db: AsyncSession = Depends(get_db)
):
    repo = ArticleRepository(db)
    
    # 1. Gather baseline text payload details out of Postgres
    source_article = await repo.get_by_id(article_id)
    if not source_article:
        raise HTTPException(status_code=404, detail="Target article metadata records not found.")

    # 2. Reconstruct matching raw context text string
    metadata_text = f"{source_article.title} {source_article.category} {' '.join(source_article.tags)}"
    query_vector = embedding_model.encode(metadata_text).tolist()

    # 3. Pull matches out of the vector engine space
    raw_matches = search_similar_articles(query_vector=query_vector, limit=k)

    # 4. Discard self-referential ids from the output stream
    match_ids = [point.id for point in raw_matches if point.id != article_id][:k]

    # 5. Build full records from PostgreSQL
    matched_articles = await repo.get_articles_by_ids(match_ids)
    return matched_articles