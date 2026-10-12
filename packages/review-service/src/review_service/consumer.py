from datetime import datetime
from logging import getLogger

import msgspec
from confluent_kafka.aio import AIOConsumer
from shared_utils.schemas import MovieRatingEvent

from review_service.config import sqlalchemy_config
from review_service.db_models import MovieRating

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
                _ts_type, ts_epoch = msg.timestamp()

                timestamp = datetime.fromtimestamp(ts_epoch / 1000)
                if msg.value() is None:
                    log.debug("no message")
                    await consumer.commit(msg)
                    continue
                try:
                    payload = msgspec.json.decode(msg.value(), type=MovieRatingEvent)
                    await process_movie_rating(payload, ts=timestamp)
                    await consumer.commit(msg)
                except msgspec.ValidationError:
                    log.exception("")
                    await consumer.commit(msg)
                    # todo: pass to DLQ
        finally:
            await consumer.unsubscribe()


async def process_movie_rating(event: MovieRatingEvent, ts: datetime):
    sqlalchemy_config.get_engine()
    log.debug(
        "[%s] process_movie_rating %s ",
        ts.isoformat(),
        event,
    )
    async with sqlalchemy_config.get_session() as session:
        model = MovieRating(
            movie_id=event.movie_id,
            user_id=event.user_id,
            rating=event.rating,
            event_ts=ts,
        )
        session.add(model)
