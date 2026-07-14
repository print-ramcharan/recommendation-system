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
    return EventResponse.model_validate(saved_event)