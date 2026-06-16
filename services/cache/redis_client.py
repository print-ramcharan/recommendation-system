import json
import redis

REDIS_HOST = "127.0.0.1"  # Using explicit loopback to prevent macOS resolution lag
REDIS_PORT = 6379

# Initialize a thread-safe Redis client instance
# decode_responses=True automatically handles string conversion from raw bytes
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

def get_cached_user_embedding(user_id: int) -> list[float] | None:
    """Retrieves a user profile vector from the feature store cache in O(1) time."""
    key = f"user_embedding:{user_id}"
    try:
        cached_data = redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        print(f"⚠️ Redis Feature Store read error: {e}")
    return None

def set_cached_user_embedding(user_id: int, vector: list[float], ttl: int = 3600):
    """Caches a pre-computed user vector profile inside the feature store."""
    key = f"user_embedding:{user_id}"
    try:
        redis_client.set(
            name=key,
            value=json.dumps(vector),
            ex=ttl  # Default cache expiration time window set to 1 hour
        )
    except Exception as e:
        print(f"⚠️ Redis Feature Store write error: {e}")