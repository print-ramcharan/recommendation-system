import pytest
import asyncio
import json
from httpx import AsyncClient, ASGITransport
from services.api.main import app
from services.api.routers.notifications import sse_manager

@pytest.mark.anyio
async def test_sse_stream_response_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Verify text/event-stream content type is configured correctly
        async with ac.stream("GET", "/notifications/stream") as response:
            assert response.status_code == 200
            assert response.headers.get("content-type").startswith("text/event-stream")

@pytest.mark.anyio
async def test_sse_broadcast_message():
    queue = asyncio.Queue()
    sse_manager.connect(queue)
    
    try:
        # Trigger mock broadcast
        payload = {"event_type": "click", "user_id": 9999, "article_id": 1111}
        sse_manager.broadcast(payload)
        
        # Read from active client queue
        message = await asyncio.wait_for(queue.get(), timeout=2.0)
        assert "data: " in message
        data = json.loads(message.replace("data: ", "").strip())
        assert data["user_id"] == 9999
        assert data["article_id"] == 1111
    finally:
        sse_manager.disconnect(queue)
