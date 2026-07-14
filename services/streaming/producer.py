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

def on_success(record_metadata):
    """Callback fired on successful Kafka broker commit acknowledgment."""
    print(f"📡 Broadcast confirmed! Partition: {record_metadata.partition} | Offset: {record_metadata.offset}")


def on_error(excp):
    """Callback triggered if event dispatch fails."""
    print(f"❌ Failed to dispatch message to Kafka topic: {excp}")


def publish_event(event_data: dict):
    """Dispatches an ingestion payload over the user-events cluster topic asynchronously."""
    producer_instance = get_producer()
    if producer_instance is None:
        print("⚠️ Event omitted. Kafka broker is currently unreachable.")
        return

    try:
        producer_instance.send(TOPIC_NAME, value=event_data).add_callback(on_success).add_errback(on_error)
    except Exception as e:
        print(f"❌ Failed to dispatch message to Kafka topic: {e}")