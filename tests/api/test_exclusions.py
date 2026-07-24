import pytest
from httpx import AsyncClient, ASGITransport
from services.api.main import app

@pytest.mark.anyio
async def test_category_exclusions_lifecycle():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # A. Create exclusion
        mute_payload = {"category": "politics"}
        res_post = await ac.post("/users/9998/exclusions", json=mute_payload)
        assert res_post.status_code == 200
        data_post = res_post.json()
        assert data_post["user_id"] == 9998
        assert data_post["category"] == "politics"
        assert "id" in data_post
        
        # B. Get exclusions
        res_get = await ac.get("/users/9998/exclusions")
        assert res_get.status_code == 200
        data_get = res_get.json()
        assert "politics" in data_get
        
        # C. Delete exclusion
        res_delete = await ac.delete("/users/9998/exclusions/politics")
        assert res_delete.status_code == 200
        
        # D. Get exclusions (verify empty)
        res_get_after = await ac.get("/users/9998/exclusions")
        assert res_get_after.status_code == 200
        assert "politics" not in res_get_after.json()
