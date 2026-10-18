import contextlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Annotated

import typer as ty
from keycloak.keycloak_admin import KeycloakAdmin, KeycloakGetError

keycloak_admin_url = os.getenv("KEYCLOAK_ADMIN_URL", "http://localhost:18080")
keycloak_admin_username = os.getenv("KEYCLOAK_ADMIN_USERNAME", "admin")
keycloak_admin_password = os.getenv("KEYCLOAK_ADMIN_USERNAME", "admin")
log = logging.getLogger(__name__)
app = ty.Typer()


def initialize_realm(
    admin: KeycloakAdmin, realm_import_json: Path
) -> tuple[bool, dict]:
    with open(realm_import_json) as f:
        realm_payload: dict = json.load(f)

    realm_name = realm_payload["realm"]

    try:
        realm = admin.get_realm(realm_name)
        realm_exists = True
        created = False
    except KeycloakGetError as e:
        if e.response_code != 404:
            raise
        realm_exists = False
        realm = None

    if not realm_exists:
        log.info("realm does not exist, importing it")
        admin.import_realm(realm_payload)
        created = True
        realm = admin.get_realm(realm_name)
    return created, realm


def setup_clients(admin: KeycloakAdmin):
    api_user_id = "app-client"
    clients = admin.get_clients()
    searched = [i for i in clients if i["clientId"] == api_user_id]
    try:
        client = searched[0]
    except IndexError:
        raise RuntimeError("client not created")

    secrets = admin.get_client_secrets(client["id"])
    if secrets["value"].startswith("****"):
        # we need to regenerate secret
        secrets = admin.generate_client_secrets(client["id"])

    return (client["id"], secrets["value"])


@app.command()
def main(
    realm_import_json: Annotated[Path, ty.Option(dir_okay=False, exists=True)],
    client_secret_out: Annotated[
        Path | None, ty.Option("--client-secret-out", "-o", dir_okay=False, exists=False)
    ] = None,
):

    admin = KeycloakAdmin(
        keycloak_admin_url,
        username=keycloak_admin_username,
        password=keycloak_admin_password,
    )

    _realm_created, realm = initialize_realm(admin, realm_import_json)

    realm_admin = KeycloakAdmin(
        keycloak_admin_url,
        realm_name=realm["realm"],
        username=keycloak_admin_username,
        password=keycloak_admin_password,
        user_realm_name="master",
    )

    _client_id, secret = setup_clients(realm_admin)
    if client_secret_out:
        with contextlib.ExitStack() as stack:
            is_stdout = str(client_secret_out) == "-"
            if is_stdout:
                f = sys.stdout
            else:
                f = stack.push(
                    open( # noqa: SIM115 exitStack manages __close__
                        client_secret_out,
                        "w",
                    )
                )  
            f.write(secret)
            # f.flush()
            if not is_stdout:
                client_secret_out.chmod(0o640)


if __name__ == "__main__":
    logging.basicConfig()
    app()
