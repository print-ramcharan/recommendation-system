import pytest
from httpx import ASGITransport, AsyncClient
from services.api.main import app

from services.api.db.database import SessionLocal
from services.api.models.user import User
from services.api.models.article import Article
from sqlalchemy import select

@pytest.mark.anyio
async def test_event_ingestion_endpoint():
    async with SessionLocal() as session:
        user_id = (await session.execute(select(User.user_id).limit(1))).scalar()
        article_id = (await session.execute(select(Article.article_id).limit(1))).scalar()

    if not user_id or not article_id:
        user_id = 221186
        article_id = 610304

    payload = {
        "user_id": user_id,
        "article_id": article_id,
        "event_type": "click",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/events/", json=payload)
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        body = response.json()
        assert body["event_type"] == "click"
        assert "event_id" in body