import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.db.database import SessionLocal
from services.api.models.user import User
from sqlalchemy import select

@pytest.mark.anyio
async def test_category_exclusions_lifecycle():
    async with SessionLocal() as session:
        user_id = (await session.execute(select(User.user_id).limit(1))).scalar()

    if not user_id:
        user_id = 9998
        # Create user if not exists to avoid FK error
        async with SessionLocal() as session:
            user = User(user_id=user_id, age=30, country="US")
            session.add(user)
            await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # A. Create exclusion
        mute_payload = {"category": "politics"}
        res_post = await ac.post(f"/users/{user_id}/exclusions", json=mute_payload)
        assert res_post.status_code == 200
        data_post = res_post.json()
        assert data_post["user_id"] == user_id
        assert data_post["category"] == "politics"
        assert "id" in data_post
        
        # B. Get exclusions
        res_get = await ac.get(f"/users/{user_id}/exclusions")
        assert res_get.status_code == 200
        data_get = res_get.json()
        assert "politics" in data_get
        
        # C. Delete exclusion
        res_delete = await ac.delete(f"/users/{user_id}/exclusions/politics")
        assert res_delete.status_code == 200
        
        # D. Get exclusions (verify empty)
        res_get_after = await ac.get(f"/users/{user_id}/exclusions")
        assert res_get_after.status_code == 200
        assert "politics" not in res_get_after.json()
