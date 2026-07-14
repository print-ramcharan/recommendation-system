import asyncio
from services.api.db.database import SessionLocal
from services.api.db.repository import EventRepository, UserRepository
from ml.embeddings.user_embeddings import compute_user_embedding
from services.cache.redis_client import set_cached_user_embedding

async def warm_cache():
    print("🔥 Starting Feature Store cache warming utility...")
    async with SessionLocal() as db:
        user_repo = UserRepository(db)
        event_repo = EventRepository(db)
        
        # Get up to 50 active users who have interactions
        users = await user_repo.list_users(limit=50)
        
        warmed_count = 0
        for user in users:
            clicked_ids = await event_repo.get_user_clicked_articles(user.user_id)
            if clicked_ids:
                vector = compute_user_embedding(clicked_ids, fallback_interests=user.interests)
                set_cached_user_embedding(user.user_id, vector, ttl=3600)
                warmed_count += 1
                
        print(f"✨ Successfully warmed embeddings for {warmed_count} active users in the Redis feature store.")

if __name__ == "__main__":
    asyncio.run(warm_cache())
