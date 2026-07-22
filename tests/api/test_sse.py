import pytest
import asyncio
import json
from services.api.routers.notifications import sse_manager, event_generator

class MockRequest:
    def __init__(self):
        self.calls = 0
    async def is_disconnected(self):
        self.calls += 1
        # Disconnect after yielding the first queue message to prevent infinite loops in tests
        return self.calls > 1

@pytest.mark.anyio
async def test_event_generator_direct():
    queue = asyncio.Queue()
    queue.put_nowait("data: hello\n\n")
    
    gen = event_generator(MockRequest(), queue)
    msg = await gen.__anext__()
    assert msg == "data: hello\n\n"

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
