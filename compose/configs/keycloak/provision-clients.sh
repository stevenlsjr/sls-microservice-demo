#!/usr/bin/env bash
# Idempotently provision OIDC clients in the keycloak master realm.
# Safe to re-run: existing clients are updated in place.
set -euo pipefail

REALM=master
KCADM=/opt/keycloak/bin/kcadm.sh

$KCADM config credentials \
  --server "$KC_URL" --realm master \
  --user "$KEYCLOAK_ADMIN" --password "$KEYCLOAK_ADMIN_PASSWORD"

# upsert_client <clientId> <kcadm -s settings...>
upsert_client() {
  local client_id=$1
  shift
  local id
  id=$($KCADM get clients -r "$REALM" -q "clientId=$client_id" --fields id --format csv --noquotes)
  if [[ -z "$id" ]]; then
    echo "creating client $client_id"
    $KCADM create clients -r "$REALM" -s "clientId=$client_id" "$@"
  else
    echo "updating client $client_id ($id)"
    $KCADM update "clients/$id" -r "$REALM" "$@"
  fi
}

# Rest client: public client (no secret). Supports the auth-code flow for
# browser apps and the password grant so tokens are easy to mint with curl in dev.
upsert_client movie-review-rest-client \
  -s enabled=true \
  -s protocol=openid-connect \
  -s publicClient=true \
  -s standardFlowEnabled=true \
  -s directAccessGrantsEnabled=true \
  -s 'redirectUris=["http://localhost:*"]' \
  -s 'webOrigins=["+"]'

echo "keycloak provisioning complete"
