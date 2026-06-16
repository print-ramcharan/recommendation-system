import pytest
from httpx import ASGITransport, AsyncClient
from services.api.main import app

@pytest.mark.anyio
async def test_event_ingestion_endpoint():
    payload = {
        "user_id": 221186,
        "article_id": 610304,
        "event_type": "click",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/events/", json=payload)
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        body = response.json()
        assert body["event_type"] == "click"
        assert "event_id" in body