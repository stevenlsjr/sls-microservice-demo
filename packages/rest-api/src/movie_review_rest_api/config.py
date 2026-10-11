import os

db_url = os.getenv("DB_URL")

# OIDC provider (keycloak master realm in the dev stack). `oidc_issuer` must
# match the `iss` claim of issued tokens exactly.
oidc_issuer = os.getenv("OIDC_ISSUER", "http://localhost:18080/realms/master")
oidc_jwks_url = os.getenv(
    "OIDC_JWKS_URL", f"{oidc_issuer.rstrip('/')}/protocol/openid-connect/certs"
)
