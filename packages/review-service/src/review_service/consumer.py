from logging import getLogger

from confluent_kafka.aio import AIOConsumer

from .config import cfg

log = getLogger(__name__)


async def run_consumer():
    log.info("starting consumer service")
    topics = [f"{cfg.kafka_topic_prefix}.ratings"]
    async with AIOConsumer(
        cfg.kafka_options
        | {"enable.auto.commit": "false", "enable.auto.offset.store": "false"}
    ) as consumer:
        await consumer.subscribe(topics)
        try:
            while True:
                # Poll without blocking the event loop
                msg = await consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    print(f"Consumer error: {msg.error()}")
                    continue

                # Process the message
                print(f"Received: {msg.value().decode('utf-8')}")
        finally:
            await consumer.unsubscribe()
