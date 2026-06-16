import asyncio
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

from services.api.db.database import SessionLocal
from services.api.models.user import User
from services.api.models.article import Article
from services.api.models.event import Event

fake = Faker()

# Data Matrix Constraints
NUM_USERS = 1000
NUM_ARTICLES = 200
NUM_EVENTS = 12000

COUNTRIES = ["IN", "US", "UK", "CA", "DE", "FR", "AU", "SG"]
SUBSCRIPTIONS = ["free", "premium"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
CATEGORIES = ["tech", "sports", "finance", "lifestyle", "entertainment"]
EVENT_TYPES = ["view", "click", "bookmark", "share"]

async def seed_data():
    async with SessionLocal() as session:
        print("🚀 Initiating data pipeline seeding engine...")

        # 1. Generate Unique User Entities
        print(f"👥 Populating {NUM_USERS} user records...")
        user_ids = list({random.randint(100000, 999999) for _ in range(NUM_USERS * 2)})[:NUM_USERS]
        
        users = []
        for uid in user_ids:
            user = User(
                user_id=uid,
                age=random.randint(18, 70),
                country=random.choice(COUNTRIES),
                interests={"preferred_topics": random.sample(CATEGORIES, k=random.randint(1, 3))},
                device_type=random.choice(DEVICE_TYPES),
                subscription=random.choice(SUBSCRIPTIONS),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 180))
            )
            users.append(user)
        
        session.add_all(users)
        await session.flush()

        # 2. Generate Unique Article Records
        print(f"📰 Populating {NUM_ARTICLES} article catalog items...")
        article_ids = list({random.randint(100000, 999999) for _ in range(NUM_ARTICLES * 2)})[:NUM_ARTICLES]
        
        articles = []
        for aid in article_ids:
            article = Article(
                article_id=aid,
                title=fake.sentence(nb_words=random.randint(5, 10)),
                category=random.choice(CATEGORIES),
                tags={"keywords": [fake.word() for _ in range(random.randint(2, 5))]},
                publish_time=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                author_id=random.randint(1000, 9999)
            )
            articles.append(article)
            
        session.add_all(articles)
        await session.flush()

        # 3. Generate Correlated High-Volume Event Streams
        print(f"📊 Logging {NUM_EVENTS} user-content relational interaction logs...")
        events = []
        for _ in range(NUM_EVENTS):
            event_timestamp = datetime.utcnow() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            event = Event(
                event_id=uuid.uuid4(),
                user_id=random.choice(user_ids),
                article_id=random.choice(article_ids),
                event_type=random.choice(EVENT_TYPES),
                timestamp=event_timestamp
            )
            events.append(event)
            
        # Batch inserting massive array arrays optimizes database write performance
        session.add_all(events)
        
        print("💾 Flushing transactional payload directly to PostgreSQL backend...")
        await session.commit()
        print("✨ Database population complete! Real-world simulated ecology active.")

if __name__ == "__main__":
    asyncio.run(seed_data())