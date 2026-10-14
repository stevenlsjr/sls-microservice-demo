from datetime import UTC, datetime
from logging import getLogger
from uuid import UUID
import sqlalchemy as sa

import msgspec
from confluent_kafka.aio import AIOConsumer
from confluent_kafka.admin import AdminClient
from shared_utils.schemas import MovieRatingEvent

from review_service.config import sqlalchemy_config
from review_service.db_models import MovieRating
import contextlib

from .config import cfg

log = getLogger(__name__)


def setup_topics():
    options = cfg.kafka_options.copy()
    del options["group.id"]

    kadmin = AdminClient(options, logger=log)
    topics_to_create = [f"{cfg.kafka_topic_prefix}.{i}" for i in ["ratings", "foo"]]
    for topic_name in topics_to_create:
        topic = kadmin.list_topics(topic_name)


@contextlib.asynccontextmanager
async def services():
    async with AIOConsumer(
        cfg.kafka_options
        | {"enable.auto.commit": "false", "enable.auto.offset.store": "false"}
    ) as consumer:
        yield (consumer,)


async def run_consumer():
    log.info("starting consumer service")
    topics = [f"{cfg.kafka_topic_prefix}.ratings"]
    async with services() as (consumer,):
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

                timestamp = datetime.fromtimestamp(ts_epoch / 1000, tz=UTC)
                value = msg.value()
                if value is None:
                    log.debug("no message")
                    await consumer.commit(msg)
                    continue
                try:
                    payload = msgspec.json.decode(value, type=MovieRatingEvent)
                    await process_movie_rating(payload, ts=timestamp)
                    await consumer.commit(msg)
                except msgspec.ValidationError:
                    log.exception("")
                    await consumer.commit(msg)
                    # todo: pass to DLQ
        finally:
            await consumer.unsubscribe()


async def process_movie_rating(event: MovieRatingEvent, ts: datetime):
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
        # materialize rating count for movie

        await session.commit()


async def materialize_movie_ratings(movie_id: UUID):
    async with sqlalchemy_config.get_session() as session:
        res = await session.execute(
            sa.text("""
        with ratings AS (
        select 
            *,
            last_value(id) OVER (partition by user_id order by event_ts) as latest_rating_id
         from movie_rating where movie_id=:movie_id
        )
        select * from ratings
        """),
            params={"movie_id": movie_id},
        )
        for row in res.all():
            print(row._asdict())
