import json
from kafka import KafkaProducer

# Force explicit IPv4 to bypass dual-stacking lookup lag on macOS
KAFKA_BROKER = "127.0.0.1:9092"
TOPIC_NAME = "user-events"

_producer = None

def get_producer():
    """Lazily initializes the thread-safe Kafka Producer instance."""
    global _producer
    if _producer is not None:
        return _producer
    try:
        _producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=3,
            request_timeout_ms=5000
        )
        print("✓ [Lazy Init] Kafka Event Producer connected successfully.")
        return _producer
    except Exception as e:
        print(f"⚠️ Lazy initialization failed to connect to Kafka Broker: {e}")
        return None

def publish_event(event_data: dict):
    """Dispatches an ingestion payload over the user-events cluster topic and blocks for confirmation."""
    producer_instance = get_producer()
    if producer_instance is None:
        print("⚠️ Event omitted. Kafka broker is currently unreachable.")
        return

    try:
        future = producer_instance.send(TOPIC_NAME, value=event_data)
        # Block up to 2 seconds to force metadata synchronization across partitions
        record_metadata = future.get(timeout=2)
        print(f"📡 Broadcast confirmed! Partition: {record_metadata.partition} | Offset: {record_metadata.offset}")
    except Exception as e:
        print(f"❌ Failed to dispatch message to Kafka topic: {e}")