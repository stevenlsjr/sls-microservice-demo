# AGENTS.md

Kafka CQRS study (movie reviews). Python 3.12+, `uv` workspace (single root `.venv` / `uv.lock`). No CI, no lint config; `ruff` is the only dev tool.

This is a personal prototype for learning distributed application patterns, and it is and will stay messy: stubs, WIP code, and inconsistencies are expected, and nearly everything is subject to change. The owner writes most application code themselves. Don't refactor, "clean up", or fill in stubs unprompted; keep changes minimal and scoped to what was asked. Treat the notes below as a snapshot, not a contract.

## Layout (`packages/`)
- `rest-api` (`movie_review_rest_api`): Litestar app, entry `movie_review_rest_api.app:app`. GET `/movies*` read from Postgres `movie_review` DB; `PUT /movies/{id}/rate` publishes a `MovieRatingEvent` to Kafka topic `<prefix>.ratings`. Reads are public; non-GET requires a Keycloak JWT (`auth.py`, verified via JWKS).
- `review-service`: Typer CLI (`uv run review-service worker`) consuming `<prefix>.ratings` and writing `movie_rating` rows to its own DB `review_service`. `setup_topics` is a stub (creates nothing). Offsets are committed manually after processing.
- `shared-utils`: Kafka event schema (`schemas.py`, msgspec) and `get_kafka_options` env parser, shared by both services.
- `data-prep`: one-off script that loads the Kaggle IMDB top-1000 via DuckDB into the `movie_review.movie` table (needs the rest-api to have created the table first).

## Running
- Infra: `podman compose up` from root (postgres on host port **15432**, kafka, apicurio, kafka-ui :8084, keycloak :18080). Observability compose is commented out in `docker-compose.yaml`, but the `.env` files still point OTLP at `localhost:4317`.
- Run each service from its own package dir; code relies on that package's gitignored `.env` (rest-api uses `dotenv.load_dotenv()`, litestar CLI reads `LITESTAR_APP`):
  - `cd packages/rest-api && uv run litestar run`
  - `cd packages/review-service && uv run review-service worker`
  - `cd packages/data-prep && uv run --env-file .env -- src/data_prep/download_movie_set.py`
- Kafka's advertised listener is `kafka:9092`, so host-run services need `kafka` resolving to localhost (e.g. `/etc/hosts`).
- Get a dev token: `compose/scripts/admin-token.sh` (password grant, client `movie-review-rest-client`, realm `master`).
- Lint: `uv run ruff check` / `ruff format` (no config; defaults).

## Gotchas
- All `.env` files are gitignored; don't commit them. Root `.env` only feeds the postgres container.
- `compose/configs/psql-init.sql` creates only `movie_review` and `keycloak`. The `review_service` DB used by review-service does not exist on a fresh stack; create it manually (init script doesn't re-run on an existing volume).
- Kafka client config comes from env vars `KAFKA__A__B` -> `a.b` (double underscore = dot), e.g. `KAFKA__BOOTSTRAP__SERVERS`. Consumer code also reads `group.id` from this, so `KAFKA__GROUP__ID` is required (`setup_topics` does `del options["group.id"]`).
- Topic prefix defaults differ: rest-api `movie_review`, review-service `movie-review` (dataclass default; overridden to `movie_review` by `KAFKA_TOPIC_PREFIX` in its `.env`, and it passes `None` if unset). Keep them identical.
- rest-api config parsing reads some env keys lowercase (`kafka_bootstrap_url`, `kafka_topic_prefix`) but `DB_URL`, `OIDC_ISSUER`, `OIDC_JWKS_URL` uppercase.
- Migrations: rest-api uses `create_all=True` at startup (its `alembic/env.py` has `target_metadata=None`, so no autogenerate); review-service has real migrations in `packages/review-service/migrations` (advanced-alchemy async env).
- `review_service/cli.py` sets root logging to DEBUG on import, intentionally (workaround for OTel log level).
- Only placeholder tests exist (`rest-api/.../tests/__init__.py`); `pytest` is in dev groups of rest-api, review-service and shared-utils.
