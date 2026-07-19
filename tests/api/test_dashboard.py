import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app

@pytest.mark.anyio
async def test_dashboard_endpoint_serves_html():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/dashboard")
        assert response.status_code == 200
        assert "Recommendation Engine Simulator" in response.text

@pytest.mark.anyio
async def test_semantic_search_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/articles/search?query=sports&k=2")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
