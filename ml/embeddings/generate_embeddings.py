import asyncio
import json
import os
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from services.api.models.user import User      
from services.api.models.event import Event  
from services.api.models.article import Article
from services.api.db.database import DATABASE_URL

print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
model = SentenceTransformer("all-MiniLM-L6-v2")


async def generate_article_embeddings():
    # 1. Initialize Async Engine to fetch data
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("Fetching articles from recommendation_db...")
    async with async_session() as session:
        stmt = select(Article)
        result = await session.execute(stmt)
        articles = result.scalars().all()

    if not articles:
        print("No articles found in the database. Run your seed pipeline first!")
        await engine.dispose()
        return

    print(f"Loaded {len(articles)} articles. Generating dense vector spaces...")

    embedding_payload = []

    for article in articles:
        # Construct dense feature document combining Title + Category + Space-separated tags
        metadata_text = f"{article.title} {article.category} {' '.join(article.tags)}"

        # Compute embedding matrix locally (Inference runs on CPU/Apple Silicon smoothly)
        vector = model.encode(metadata_text)

        # Verify exact structural dimensionality contract
        assert vector.shape == (384,), f"Expected shape (384,), got {vector.shape}"

        embedding_payload.append({
            "article_id": article.article_id,
            "vector": vector.tolist()
        })

    # 2. Save vectors to a temporary disk checkpoint
    output_dir = "data/embeddings"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "articles.json")

    with open(output_path, "w") as f:
        json.dump(embedding_payload, f, indent=2)

    print(f"\nSuccess! Verified embedding vector length: {len(embedding_payload[0]['vector'])}")
    print(f"Serialized {len(embedding_payload)} article vectors directly to: {output_path}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(generate_article_embeddings())