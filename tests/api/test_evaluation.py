import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.db.database import SessionLocal
from services.api.models.user import User
from services.api.models.event import Event
from sqlalchemy import select

@pytest.mark.anyio
async def test_offline_metrics_evaluation_lifecycle():
    async with SessionLocal() as session:
        user_id = (await session.execute(select(User.user_id).limit(1))).scalar()

    if not user_id:
        user_id = 9999
        async with SessionLocal() as session:
            user = User(user_id=user_id, age=25, country="CA", interests=["tech", "science"])
            session.add(user)
            await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # A. Trigger metrics calculation
        payload = {"user_id": user_id, "k": 5}
        res_post = await ac.post("/evaluation/metrics", json=payload)
        assert res_post.status_code == 200
        data_post = res_post.json()
        assert data_post["user_id"] == user_id
        assert data_post["k"] == 5
        assert "precision_at_k" in data_post
        assert "recall_at_k" in data_post
        assert "ndcg_at_k" in data_post
        
        # B. Get evaluation history
        res_get = await ac.get(f"/evaluation/metrics/{user_id}")
        assert res_get.status_code == 200
        data_get = res_get.json()
        assert len(data_get) >= 1
        assert data_get[0]["user_id"] == user_id
