import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app

@pytest.mark.anyio
async def test_analytics_summary_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_clicks" in data
        assert "total_users" in data
        assert "total_articles" in data
        assert "category_breakdown" in data
        assert isinstance(data["category_breakdown"], list)
        assert data["total_clicks"] >= 0
        assert data["total_users"] >= 0
        assert data["total_articles"] >= 0
