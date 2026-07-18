import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from ml.training.dataset import RecommendationDataset, build_training_tensors
from services.api.models.user import User
from services.api.models.article import Article
from services.api.models.event import Event

from services.api.db.database import SessionLocal

@pytest.mark.anyio
async def test_empty_dataset_handling():
    async with SessionLocal() as session:
        # Clear clicks to make sure it's empty
        from sqlalchemy import delete
        await session.execute(delete(Event))
        await session.commit()
        
        dataset, user_map, item_map = await build_training_tensors(session)
        assert len(dataset) == 0
        assert user_map == {}
        assert item_map == {}

@pytest.mark.anyio
async def test_dataset_generation_and_negative_sampling():
    async with SessionLocal() as session:
        # Seed mock data for verification
        user = User(user_id=8888, age=25, interests={})
        art1 = Article(article_id=101, title="Art 1", category="tech", author_id=99)
        art2 = Article(article_id=102, title="Art 2", category="sports", author_id=99)
        art3 = Article(article_id=103, title="Art 3", category="music", author_id=99)
        
        session.add_all([user, art1, art2, art3])
        await session.flush()

        event = Event(user_id=8888, article_id=101, event_type="click")
        session.add(event)
        await session.flush()

        dataset, user_map, item_map = await build_training_tensors(session, negative_ratio=2)
        
        # 1 positive click + negative sampling
        assert 8888 in user_map
        assert 101 in item_map
        assert len(dataset) > 1
        
        # Check that labels contain 1.0 (click) and 0.0 (sampled negative)
        labels = [dataset[i][2].item() for i in range(len(dataset))]
        assert 1.0 in labels
        assert 0.0 in labels
        
        # Clean up seeded mock records
        await session.delete(event)
        await session.delete(user)
        await session.delete(art1)
        await session.delete(art2)
        await session.delete(art3)
        await session.commit()
