from logging import getLogger

import msgspec
from confluent_kafka.aio import AIOProducer
from litestar.config.app import AppConfig
from litestar.di import NamedDependency, Provide
from litestar.plugins import InitPlugin
from shared_utils.schemas import MovieRatingEvent

from . import rest_models
from .config import cfg

log = getLogger(__name__)
kafka_log = getLogger('kafka')

class KafkaRatingsPublisher:
    topic_name: str
    producer: AIOProducer
    def __init__(self,
                 kafka_ratings_producer: NamedDependency[AIOProducer]):
        self.producer = kafka_ratings_producer
        self.topic_name = cfg.kafka_topic_prefix + '.ratings'
    async def send_rating(self, user_id: str, rating: rest_models.MovieRatingBody):
        key = f'uid-{user_id}'
        val = MovieRatingEvent(movie_id=rating.movie_id, rating=rating.rating, user_id=user_id)
        future=await self.producer.produce(self.topic_name, key=key, value=msgspec.json.encode(val))
        res = await future
        log.info("delivered message %s", res)


class KafkaInitPlugin(InitPlugin):
    _producer: AIOProducer = None
    
    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        async def setup():
            await self.setup_producer()
        async def shutdown(app):
            await self.on_shutdown(app)

        async def kafka_ratings_producer() -> AIOProducer:
            return self._producer

        app_config.on_startup.append(setup)
        app_config.on_shutdown.append(shutdown)
        app_config.dependencies['kafka_ratings_producer'] = Provide(kafka_ratings_producer)
        app_config.dependencies['kafka_ratings_service'] = Provide(KafkaRatingsPublisher, sync_to_thread=True)
        return app_config
    
    async def setup_producer(self):
        from .config import cfg
        config = cfg.kafka_options | {
            'logger': kafka_log
        }
        self._producer = AIOProducer(config)

    async def on_shutdown(self, app):
        if self._producer is not None:
            log.info("shutting down producer")
            await self._producer.close()
        else:
            log.error("producer doesn't exist")

