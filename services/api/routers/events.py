from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Database dependency
from services.api.db.database import get_db

# Models, Repositories, and Services
from services.api.models.event import Event
from services.api.db.repository import EventRepository
from services.api.db.services import EventService

# Schemas
from services.api.schemas.event import EventCreate, EventResponse

router = APIRouter(
    prefix="/events",
    tags=["events"],
)

@router.post("/", response_model=EventResponse)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
):
    event_repo = EventRepository(db)
    service = EventService(event_repo=event_repo)

    saved_event = await service.ingest_user_event(payload)
    
    # Broadcast to Server-Sent Events subscribers
    from services.api.routers.notifications import sse_manager
    sse_manager.broadcast({
        "event_type": saved_event.event_type,
        "user_id": saved_event.user_id,
        "article_id": saved_event.article_id,
        "timestamp": str(saved_event.timestamp)
    })
    
    return EventResponse.model_validate(saved_event)