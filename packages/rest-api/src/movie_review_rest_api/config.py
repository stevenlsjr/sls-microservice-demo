import os
from typing import Self

from msgspec import Struct


def get_kafka_options(env=os.environ, strip_blank: bool =False):
    options = {}
    for k in env:
        transformed_key = k.lower()
        if not transformed_key.startswith('kafka__'):
            continue
        option_path = transformed_key.split('__')[1:] # remove kafka
        option_key = '.'.join(option_path)
        value = env[k]
        if value or not strip_blank:
            options[option_key] = env[k]

    return options

class ConfigSchema(Struct):
    db_url: str
    kafka_options: dict

    oidc_issuer: str = "http://localhost:18080/realms/master"
    oidc_jwks_url: str = (
        "http://localhost:18080/realms/master/protocol/openid-connect/certs"
    )

    kafka_bootstrap_url: str = ('http://kafka:9092')

    @classmethod
    def parse(cls, env=os.environ) -> Self:
        fields = {
            "db_url": env.get("DB_URL", None),
            "oidc_issuer": env.get("OIDC_ISSUER", None) or None,
            "oidc_jwks_url": env.get("OIDC_JWKS_URL", None) or None,
            'kafka_options': get_kafka_options(env)
        }

        return cls(**{k: v for k,v in fields.items() if v is not None})


cfg = ConfigSchema.parse(os.environ)
