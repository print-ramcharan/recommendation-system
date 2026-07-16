import pytest
from httpx import ASGITransport, AsyncClient
from services.api.main import app

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code in [200, 503]
    json_data = response.json()
    if response.status_code == 200:
        assert json_data["status"] == "ok"
        assert "services" in json_data
    else:
        assert json_data["detail"]["status"] == "unhealthy"