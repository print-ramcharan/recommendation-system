from fastapi import FastAPI
from services.api.routers.recommendations import router as recommendation_router
from services.api.routers.events import router as event_router

app = FastAPI(
    title="Recommendation System",
    version="0.1.0",
)

app.include_router(recommendation_router)
app.include_router(event_router)

@app.get("/health")
async def health():
    return {"status": "ok"}