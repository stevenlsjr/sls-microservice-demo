import os
from typing import Self

from msgspec import Struct
from shared_utils.config import get_kafka_options


class ConfigSchema(Struct):
    db_url: str
    kafka_options: dict

    oidc_issuer: str = "http://localhost:18080/realms/master"
    oidc_jwks_url: str = (
        "http://localhost:18080/realms/master/protocol/openid-connect/certs"
    )

    kafka_bootstrap_url: str = "http://kafka:9092"
    kafka_topic_prefix: str = "movie_review"

    @classmethod
    def parse(cls, env=os.environ) -> Self:
        fields = {
            "db_url": env.get("DB_URL", None),
            "oidc_issuer": env.get("OIDC_ISSUER", None),
            "oidc_jwks_url": env.get("OIDC_JWKS_URL", None),
            "kafka_bootstrap_url": env.get("kafka_bootstrap_url", None),
            "kafka_options": get_kafka_options(env),
            "kafka_topic_prefix": env.get("kafka_topic_prefix", None),
        }

        return cls(**{k: v for k, v in fields.items() if v is not None})


cfg = ConfigSchema.parse(os.environ)
