from pydantic import BaseModel, Field
from datetime import datetime

class LatencyRecordCreate(BaseModel):
    route: str = Field(..., description="API request endpoint route path")
    duration_ms: float = Field(..., ge=0.0, description="Duration in milliseconds")

class LatencyRecordResponse(BaseModel):
    id: int
    route: str
    duration_ms: float
    timestamp: datetime

    class Config:
        from_attributes = True

class LatencyStatsResponse(BaseModel):
    route: str = Field(..., description="API endpoint path")
    avg_ms: float = Field(..., description="Average processing latency")
    min_ms: float = Field(..., description="Minimum processing latency")
    max_ms: float = Field(..., description="Maximum processing latency")
    p95_ms: float = Field(..., description="95th percentile SLA response time")
    p99_ms: float = Field(..., description="99th percentile SLA response time")
    total_samples: int = Field(..., description="Count of statistical sample elements")
