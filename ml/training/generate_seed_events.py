import asyncio
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.api.db.database import SessionLocal
from services.api.models.user import User
from services.api.models.article import Article
from services.api.models.event import Event

async def seed_events():
    print("🌱 Generating mock click events for NCF training...")
    async with SessionLocal() as db:
        users = (await db.execute(select(User.user_id))).scalars().all()
        articles = (await db.execute(select(Article.article_id))).scalars().all()
        
        if not users or not articles:
            print("⚠️ Users or articles not found in database. Run generate_embeddings first!")
            return
            
        clicks = []
        for _ in range(2000):
            uid = random.choice(users)
            aid = random.choice(articles)
            event = Event(
                user_id=uid,
                article_id=aid,
                event_type="click"
            )
            clicks.append(event)
            
        db.add_all(clicks)
        await db.commit()
        print(f"✨ Successfully seeded {len(clicks)} mock click events in PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(seed_events())
