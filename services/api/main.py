from fastapi import FastAPI
from services.api.routers.recommendations import router as recommendation_router
from services.api.routers.events import router as event_router
from services.api.routers.articles import router as article_router
from prometheus_fastapi_instrumentator import Instrumentator

# Mount right alongside your recommendation and event routes

app = FastAPI(
    title="Recommendation System",
    version="0.1.0",
)

Instrumentator().instrument(app).expose(app)

app.include_router(recommendation_router)
app.include_router(event_router)
app.include_router(article_router)

@app.get("/health")
async def health():
    return {"status": "ok"}