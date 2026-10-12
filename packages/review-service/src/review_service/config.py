from dataclasses import dataclass
import os
from shared_utils.config import get_kafka_options
from advanced_alchemy.config import SQLAlchemyAsyncConfig


@dataclass(kw_only=True)
class Config:
    kafka_options: dict
    kafka_topic_prefix: str = "movie-review"
    db_url: str


cfg = Config(
    kafka_options=get_kafka_options(os.environ),
    kafka_topic_prefix=os.getenv("KAFKA_TOPIC_PREFIX"),
    db_url=os.getenv("DB_URL")
)

sqlalchemy_config = SQLAlchemyAsyncConfig(connection_string=cfg.db_url)