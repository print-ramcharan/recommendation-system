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

@pytest.mark.anyio
async def test_ml_training_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Check GET status is functional
        status_res = await ac.get("/ml/status")
        assert status_res.status_code == 200
        assert "status" in status_res.json()
        
        # Check POST train trigger does not raise exception
        train_res = await ac.post("/ml/train")
        assert train_res.status_code in (200, 409)
