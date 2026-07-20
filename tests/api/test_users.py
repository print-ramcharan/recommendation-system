import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.db.database import SessionLocal
from services.api.models.user import User
from sqlalchemy import select

@pytest.mark.anyio
async def test_user_interests_get_and_put():
    async with SessionLocal() as session:
        # Seed a test user
        user = User(user_id=7777, age=30, interests={"preferred_topics": ["tech", "sports"]})
        session.add(user)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Verify GET interests
        get_res = await ac.get("/users/7777/interests")
        assert get_res.status_code == 200
        assert get_res.json()["preferred_topics"] == ["tech", "sports"]

        # 2. Verify PUT interests
        put_res = await ac.put(
            "/users/7777/interests",
            json={"preferred_topics": ["music", "finance"]}
        )
        assert put_res.status_code == 200
        assert put_res.json()["interests"]["preferred_topics"] == ["music", "finance"]

        # 3. Clean up test user
        async with SessionLocal() as session:
            await session.delete(await session.get(User, 7777))
            await session.commit()

def test_user_interests_update_validation():
    from services.api.schemas.user import UserInterestsUpdate
    from pydantic import ValidationError
    
    # Test valid preferred_topics
    update = UserInterestsUpdate(preferred_topics=["tech"])
    assert update.preferred_topics == ["tech"]
    
    # Test empty topics raises validation error
    with pytest.raises(ValidationError):
        UserInterestsUpdate(preferred_topics=[])
