import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app

@pytest.mark.anyio
async def test_profiling_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # A. Record a latency sample
        record_payload = {"route": "/recommendations/personalized", "duration_ms": 12.34}
        res_post = await ac.post("/profiling/record", json=record_payload)
        assert res_post.status_code == 200
        data_post = res_post.json()
        assert data_post["route"] == "/recommendations/personalized"
        assert data_post["duration_ms"] == 12.34
        assert "id" in data_post
        
        # B. Get route latency stats
        res_get = await ac.get("/profiling/stats", params={"route": "/recommendations/personalized"})
        assert res_get.status_code == 200
        data_get = res_get.json()
        assert data_get["route"] == "/recommendations/personalized"
        assert "avg_ms" in data_get
        assert "min_ms" in data_get
        assert "max_ms" in data_get
        assert "p95_ms" in data_get
        assert "p99_ms" in data_get
        assert data_get["total_samples"] >= 1
