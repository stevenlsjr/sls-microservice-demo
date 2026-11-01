import os
from typing import Self

from msgspec import Struct
from shared_utils.config import get_kafka_options
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigSchema(BaseSettings):
    model_config = SettingsConfigDict()
    db_url: str

    @property
    def kafka_options(self) -> dict[str, str]:
        return get_kafka_options(os.environ)

    oidc_issuer: str = "http://localhost:18080/realms/microservice-app"
    oidc_jwks_url: str = (
        "http://localhost:18080/realms/microservice-app/protocol/openid-connect/certs"
    )

    kafka_bootstrap_url: str = "http://kafka:9092"
    kafka_topic_prefix: str = "movie_review"
    opensearch_hosts: list[str] = ["https://localhost:9200"]
    opensearch_verify_certs: bool = True
    opensearch_auth: str | None

    @property
    def opensearch_http_auth(self) -> tuple[str, str] | None:
        if not self.opensearch_auth:
            return None
        auth_pair = self.opensearch_auth.split(':', 1)
        return auth_pair[0], auth_pair[1]


cfg = ConfigSchema.settings_cached()
