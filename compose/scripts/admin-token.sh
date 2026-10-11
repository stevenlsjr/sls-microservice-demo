KEYCLOAK_REALM=${KEYCLOAK_REALM:-http://localhost:18080/realms/master}
curl -s $KEYCLOAK_REALM/protocol/openid-connect/token \
  -d grant_type=password -d client_id=movie-review-rest-client \
  -d username=admin -d password=admin