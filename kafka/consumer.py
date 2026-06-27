import json
import logging

from confluent_kafka import Consumer, KafkaException

from config import settings
from database import SessionLocal
from models import EmailEvent

logger = logging.getLogger(__name__)


def create_consumer():
    """Create a Kafka consumer for tracking events"""
    return Consumer(
        {
            "bootstrap.servers": settings.kafka_broker,
            "group.id": "email-engine-consumers",
            "auto.offset.reset": "earliest",  # start from beginning if no offset exists
            "enable.auto.commit": False,  # manual commit — only after successful processing
            "session.timeout.ms": 6000,
        }
    )


def start_consumer():
    """Run the Kafka consumer (blocking loop)"""
    consumer = create_consumer()
    print(f"Consumer created: {consumer}")
    if consumer is None:
        print("Error: Consumer failed to initialize. Check broker connection.")
        return
    consumer.subscribe(["email.sent", "email.opened", "email.clicked"])

    logger.info("Consumer started, listening for events...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            print(f"Polled message: {msg}")
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == -191:  # PARTITION_EOF
                    logger.debug("Reached end of partition")
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                continue

            # Process the message
            try:
                process_event(msg)
                consumer.commit(
                    asynchronous=False
                )  # commit only after successful write
                logger.info(f"Successfully processed {msg.topic()} event")
            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                # Don't commit — will retry on next run

    except KeyboardInterrupt:
        logger.info("Consumer shutting down...")

    finally:
        consumer.close()


def process_event(msg):
    """
    Process a single Kafka event.
    This is where idempotency happens.
    """
    event_data = json.loads(msg.value())
    topic = msg.topic()

    # Determine event type from topic
    event_type = topic.split(".")[-1]  # "email.opened" -> "opened"

    # Create idempotency key: unique identifier for this event
    # If we receive the same event twice, we won't insert it twice
    idempotency_key = (
        f"{event_data['enrollment_id']}-{event_data['step_id']}-{event_type}"
    )

    db = SessionLocal()
    try:
        # Check if this event already exists (fast path)
        existing = (
            db.query(EmailEvent).filter_by(idempotency_key=idempotency_key).first()
        )

        if existing:
            logger.debug(f"Event already processed: {idempotency_key}")
            return  # duplicate — skip silently

        # Insert new event
        email_event = EmailEvent(
            enrollment_id=event_data["enrollment_id"],
            step_id=event_data["step_id"],
            event_type=event_type,
            idempotency_key=idempotency_key,
        )
        db.add(email_event)
        db.commit()
        logger.debug(f"Event inserted: {idempotency_key}")

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_consumer()
