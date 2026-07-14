import json
import time
import asyncio
from kafka import KafkaConsumer
from services.cache.redis_client import set_cached_user_embedding, redis_client
from services.api.db.database import SessionLocal
from services.api.db.repository import EventRepository, UserRepository
from ml.embeddings.user_embeddings import compute_user_embedding

KAFKA_BROKER = "127.0.0.1:9092"
TOPIC_NAME = "user-events"


async def async_update_user_embedding(user_id: int):
    """
    Asynchronously queries the database for user clicked history,
    computes the user embedding semantic profile, and writes it back to Redis.
    """
    async with SessionLocal() as db:
        user_repo = UserRepository(db)
        event_repo = EventRepository(db)
        
        user = await user_repo.get_by_id(user_id)
        if not user:
            print(f"⚠️ [Consumer] User {user_id} not found in database. Cannot compute embedding.")
            return
            
        clicked_ids = await event_repo.get_user_clicked_articles(user_id)
        user_vector = compute_user_embedding(clicked_ids, fallback_interests=user.interests)
        
        set_cached_user_embedding(user_id, user_vector, ttl=3600)
        print(f"✨ [Consumer] Real-time embedding updated successfully in Redis feature store for user {user_id}.")


def handle_user_event(event_payload: dict):
    """Processes user events and triggers real-time updates."""
    user_id = event_payload.get("user_id")
    event_type = event_payload.get("event_type")
    
    if not user_id:
        return
        
    print(f"Processing event for user {user_id} ({event_type})...")
    
    # Invalidate existing cache first to guarantee fresh reads
    cache_key = f"user_embedding:{user_id}"
    try:
        redis_client.delete(cache_key)
        print(f"🧹 Cache invalidated for key: {cache_key}")
    except Exception as e:
        print(f"⚠️ Failed to invalidate cache: {e}")
        
    # Recompute and update embedding in real-time
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            loop.create_task(async_update_user_embedding(user_id))
        else:
            asyncio.run(async_update_user_embedding(user_id))
    except Exception as e:
        print(f"⚠️ Failed to compute real-time embedding: {e}")


def start_event_consumer():
    """Initializes and spins up the live asynchronous message processing engine loop."""
    print(f"Connecting to Kafka Broker tracking topic: '{TOPIC_NAME}' at {KAFKA_BROKER}...")

    retries = 5
    delay = 2
    consumer = None
    
    for attempt in range(1, retries + 1):
        try:
            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset="latest",
                enable_auto_commit=True,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                request_timeout_ms=10000,
            )
            print("🚀 Kafka Event Consumer online and polling. Listening for real-time user clicks...\n")
            break
        except Exception as e:
            print(f"❌ Failed to spin up streaming consumer engine (Attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
            else:
                return

    try:
        for message in consumer:
            event_payload = message.value
            print("--- [ Incoming Real-Time Streaming Event Captured ] ---")
            print(f"Message Offset: {message.offset} | Partition: {message.partition}")
            print(json.dumps(event_payload, indent=2))
            print("--------------------------------------------------------\n")
            
            handle_user_event(event_payload)
            
    except KeyboardInterrupt:
        print("\nStopping streaming consumer engines cleanly...")
    finally:
        if consumer:
            consumer.close()


if __name__ == "__main__":
    start_event_consumer()