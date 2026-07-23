import time
import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.api.db.database import get_db
from services.cache.redis_client import redis_client
from ml.embeddings.qdrant_client import get_qdrant_client
from services.api.routers.recommendations import router as recommendation_router
from services.api.routers.events import router as event_router
from services.api.routers.articles import router as article_router
from services.api.routers.ml import router as ml_router
from services.api.routers.users import router as users_router
from services.api.routers.analytics import router as analytics_router
from services.api.routers.notifications import router as notifications_router
from services.api.routers.profiling import router as profiling_router
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title="Recommendation System",
    version="0.1.0",
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}ms"
    logger.info(
        f"📡 [API Request] method={request.method} path={request.url.path} status={response.status_code} duration={formatted_process_time}"
    )
    return response

Instrumentator().instrument(app).expose(app)

app.include_router(recommendation_router)
app.include_router(event_router)
app.include_router(article_router)
app.include_router(ml_router)
app.include_router(users_router)
app.include_router(analytics_router)
app.include_router(notifications_router)
app.include_router(profiling_router)

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

app.mount("/static", StaticFiles(directory="services/api/static"), name="static")

@app.get("/dashboard", response_class=FileResponse)
async def dashboard():
    return FileResponse("services/api/static/index.html")