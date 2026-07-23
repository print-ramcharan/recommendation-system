from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.db.database import get_db
from services.api.db.repository import LatencyRepository
from services.api.db.services import ProfilingService
from services.api.schemas.latency import LatencyRecordCreate, LatencyRecordResponse, LatencyStatsResponse

router = APIRouter(prefix="/profiling", tags=["profiling"])

@router.post("/record", response_model=LatencyRecordResponse)
async def record_latency_sample(
    payload: LatencyRecordCreate,
    db: AsyncSession = Depends(get_db)
):
    """Records an execution latency sample to the database."""
    latency_repo = LatencyRepository(db)
    service = ProfilingService(latency_repo)
    saved = await service.record_sample(route=payload.route, duration_ms=payload.duration_ms)
    return LatencyRecordResponse.model_validate(saved)

@router.get("/stats", response_model=LatencyStatsResponse)
async def get_route_latency_stats(
    route: str = Query(..., description="Target API route path to aggregate"),
    db: AsyncSession = Depends(get_db)
):
    """Aggregates min, max, avg, p95, and p99 percentile latencies for a target route."""
    latency_repo = LatencyRepository(db)
    service = ProfilingService(latency_repo)
    data = await service.get_percentile_latencies(route=route)
    return LatencyStatsResponse.model_validate(data)
