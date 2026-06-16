from fastapi import FastAPI
from services.api.routers.recommendations import router

app = FastAPI(
    title="Recommendation System",
    version="0.1.0",
)

app.include_router(router)

@app.get("/health")
async def health():
    return {"status": "ok"}