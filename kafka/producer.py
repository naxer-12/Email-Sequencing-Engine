import json
import logging

from confluent_kafka import Producer

from config import settings

logger = logging.getLogger(__name__)

# Singleton producer instance
_producer = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer(
            {
                "bootstrap.servers": settings.kafka_broker,
                "client.id": "email-engine-producer",
                "acks": "all",  # wait for all replicas to acknowledge
            }
        )
    return _producer


def produce_event(topic: str, enrollment_id: int, step_id: int, extra: dict = None):
    """
    Emit an event to Kafka.

    Args:
        topic: e.g., "email.sent", "email.opened", "email.clicked"
        enrollment_id: partition key (ensures all events for one recipient go to same partition)
        step_id: the sequence step that was sent
        extra: any additional data to include
    """
    producer = get_producer()

    payload = {"enrollment_id": enrollment_id, "step_id": step_id, **(extra or {})}

    def delivery_callback(err, msg):
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(
                f"Message delivered to {msg.topic()} partition {msg.partition()}"
            )

    producer.produce(
        topic=topic,
        key=str(enrollment_id),  # partition key — same recipient goes to same partition
        value=json.dumps(payload),
        callback=delivery_callback,
    )
    print(producer)
    # Trigger callbacks without blocking
    producer.poll(0)


def flush_producer():
    """Ensure all messages are sent (call before shutdown)"""
    get_producer().flush()
