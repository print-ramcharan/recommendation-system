import pytest
from services.streaming.consumer import handle_user_event
from services.cache.redis_client import get_cached_user_embedding, redis_client
from services.api.db.database import SessionLocal
from services.api.models.user import User
from services.api.models.article import Article
from services.api.models.event import Event
import uuid
import datetime

@pytest.mark.anyio
async def test_realtime_embedding_updates():
    user_id = 999999
    article_id = 888888
    
    # 1. Ensure user and article exist in database
    async with SessionLocal() as session:
        # Check and clean user
        existing_user = await session.get(User, user_id)
        if existing_user:
            await session.delete(existing_user)
        
        # Check and clean article
        existing_article = await session.get(Article, article_id)
        if existing_article:
            await session.delete(existing_article)
            
        await session.commit()
        
        # Insert user and article
        user = User(
            user_id=user_id,
            age=30,
            country="US",
            interests={"preferred_topics": ["tech"]},
            device_type="desktop",
            subscription="free",
            created_at=datetime.datetime.utcnow()
        )
        article = Article(
            article_id=article_id,
            title="Tech Future article",
            category="tech",
            tags={"keywords": ["tech"]},
            publish_time=datetime.datetime.utcnow(),
            author_id=1234
        )
        session.add(user)
        session.add(article)
        await session.commit()

        # Insert click event
        event = Event(
            event_id=uuid.uuid4(),
            user_id=user_id,
            article_id=article_id,
            event_type="click",
            timestamp=datetime.datetime.utcnow()
        )
        session.add(event)
        await session.commit()

    # 2. Invalidate cache if exists
    cache_key = f"user_embedding:{user_id}"
    redis_client.delete(cache_key)
    assert get_cached_user_embedding(user_id) is None
    
    # 3. Simulate consumer handling event
    event_payload = {
        "user_id": user_id,
        "article_id": article_id,
        "event_type": "click",
    }
    handle_user_event(event_payload)
    import asyncio
    await asyncio.sleep(0.5)
    
    # 4. Check Redis cache - embedding should now be cached
    cached_vector = get_cached_user_embedding(user_id)
    assert cached_vector is not None
    assert isinstance(cached_vector, list)
    assert len(cached_vector) == 384  # MiniLM dimension
    
    # Cleanup
    async with SessionLocal() as session:
        # Remove any events generated for this test user
        from sqlalchemy import delete
        await session.execute(delete(Event).where(Event.user_id == user_id))
        
        # Delete user and article
        u = await session.get(User, user_id)
        if u:
            await session.delete(u)
        a = await session.get(Article, article_id)
        if a:
            await session.delete(a)
        await session.commit()
    redis_client.delete(cache_key)
