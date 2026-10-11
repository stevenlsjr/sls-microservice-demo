"""OIDC resource-server auth: verify keycloak-issued JWTs against its JWKS."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient, PyJWKClientConnectionError, PyJWKClientError
from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTAuth, Token

from . import config

# PyJWKClient caches the fetched key set (default 5 min) and re-fetches when it
# sees an unknown `kid`, so key rotation is picked up automatically.
_jwks_client = PyJWKClient(config.oidc_jwks_url)


class OIDCToken(Token):
    """Token whose signature is verified with keys from the provider's JWKS."""

    @classmethod
    def decode_payload(
        cls,
        encoded_token: str,
        secret: str,  # unused: keys come from the JWKS endpoint
        algorithms: list[str],
        issuer: str | Sequence[str] | None = None,
        audience: str | Sequence[str] | None = None,
        options: Any = None,
    ) -> Any:
        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(encoded_token)
        except PyJWKClientConnectionError:
            raise  # provider unreachable: a server problem, not a bad token
        except PyJWKClientError as e:  # e.g. unknown kid
            raise jwt.InvalidTokenError(str(e)) from e
        return jwt.decode(
            encoded_token,
            signing_key.key,
            algorithms=algorithms,
            issuer=issuer,  # type: ignore[arg-type]
            audience=audience,
            options=options,
        )


@dataclass
class User:
    id: str  # OIDC `sub` claim
    username: str | None = None


async def retrieve_user(token: Token, connection: ASGIConnection) -> User:
    return User(id=token.sub, username=token.extras.get("preferred_username"))


jwt_auth = JWTAuth[User](
    retrieve_user_handler=retrieve_user,
    token_secret="unused",  # required by litestar; verification uses the JWKS
    algorithm="RS256",
    token_cls=OIDCToken,
    accepted_issuers=[config.oidc_issuer],
    # Reads are public for now; anything else (writes) requires a bearer token
    # and exposes the caller as `request.user`.
    exclude_http_methods=["GET", "HEAD", "OPTIONS"],
)
