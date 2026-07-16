from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.api.db.database import get_db
from services.cache.redis_client import redis_client
from ml.embeddings.qdrant_client import get_qdrant_client
from services.api.routers.recommendations import router as recommendation_router
from services.api.routers.events import router as event_router
from services.api.routers.articles import router as article_router
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="Recommendation System",
    version="0.1.0",
)

Instrumentator().instrument(app).expose(app)

app.include_router(recommendation_router)
app.include_router(event_router)
app.include_router(article_router)

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    services_status = {}
    
    # 1. Check PostgreSQL Connection
    try:
        await db.execute(text("SELECT 1"))
        services_status["database"] = "online"
    except Exception as e:
        services_status["database"] = f"offline: {e}"
        
    # 2. Check Redis Connection
    try:
        redis_client.ping()
        services_status["redis"] = "online"
    except Exception as e:
        services_status["redis"] = f"offline: {e}"
        
    # 3. Check Qdrant Connection
    try:
        qdrant_client = get_qdrant_client()
        qdrant_client.get_collections()
        services_status["qdrant"] = "online"
    except Exception as e:
        services_status["qdrant"] = f"offline: {e}"
        
    # If any dependency is down, return HTTP 503
    is_healthy = all(status == "online" for status in services_status.values())
    if not is_healthy:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "services": services_status})
        
    return {"status": "ok", "services": services_status}