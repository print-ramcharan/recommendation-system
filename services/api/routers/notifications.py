import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from services.api.schemas.notification import NotificationPayload

router = APIRouter(prefix="/notifications", tags=["notifications"])

class SSEConnectionManager:
    def __init__(self):
        self.active_connections: set[asyncio.Queue] = set()

    def connect(self, queue: asyncio.Queue):
        self.active_connections.add(queue)

    def disconnect(self, queue: asyncio.Queue):
        self.active_connections.remove(queue)

    def broadcast(self, payload: dict):
        # Format as Server-Sent Event data format
        sse_message = f"data: {json.dumps(payload)}\n\n"
        for queue in self.active_connections:
            queue.put_nowait(sse_message)

sse_manager = SSEConnectionManager()

async def event_generator(request: Request, queue: asyncio.Queue):
    sse_manager.connect(queue)
    try:
        while True:
            # Yield streamed messages to the client
            if await request.is_disconnected():
                break
            message = await queue.get()
            yield message
    except asyncio.CancelledError:
        pass
    finally:
        sse_manager.disconnect(queue)

@router.get("/stream")
async def get_live_notification_stream(request: Request):
    """Establishes persistent Server-Sent Events (SSE) stream for live clicks."""
    queue = asyncio.Queue()
    return StreamingResponse(
        event_generator(request, queue),
        media_type="text/event-stream"
    )
