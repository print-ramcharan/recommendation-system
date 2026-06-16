import json
from kafka import KafkaConsumer

KAFKA_BROKER = "127.0.0.1:9092"
TOPIC_NAME = "user-events"


def start_event_consumer():
    """Initializes and spins up the live asynchronous message processing engine loop."""
    print(f"Connecting to Kafka Broker tracking topic: '{TOPIC_NAME}' at {KAFKA_BROKER}...")

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
    except Exception as e:
        print(f"❌ Failed to spin up streaming consumer engine: {e}")
        return

    try:
        for message in consumer:
            event_payload = message.value
            print("--- [ Incoming Real-Time Streaming Event Captured ] ---")
            print(f"Message Offset: {message.offset} | Partition: {message.partition}")
            print(json.dumps(event_payload, indent=2))
            print("--------------------------------------------------------\n")
    except KeyboardInterrupt:
        print("\nStopping streaming consumer engines cleanly...")
    finally:
        consumer.close()


if __name__ == "__main__":
    start_event_consumer()