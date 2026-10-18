# syntax=docker/dockerfile:1
#
# One-off job that loads the IMDB top-1000 set into the movie_review.movie table.
# The rest-api must have created the table first.
#
# Build from the repo root (the uv workspace root):
#   podman build -f packages/data-prep/Dockerfile -t data-prep .
# Run (needs DB_USERNAME, DB_PASSWORD, DB_CONNSTRING and outbound network):
#   podman run --rm --env-file packages/data-prep/.env data-prep

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.12.15
ARG PACKAGE=data-prep

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------------------------------------------------------------- builder-base
FROM python:${PYTHON_VERSION}-slim AS builder-base
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# ------------------------------------------------------------------- manifests
# uv validates the whole workspace, so every member's pyproject.toml is needed
# even though only one package is installed.
FROM builder-base AS manifests
COPY pyproject.toml uv.lock ./
COPY packages/rest-api/pyproject.toml packages/rest-api/pyproject.toml
COPY packages/review-service/pyproject.toml packages/review-service/pyproject.toml
COPY packages/data-prep/pyproject.toml packages/data-prep/pyproject.toml
COPY packages/shared-utils/pyproject.toml packages/shared-utils/pyproject.toml

# ------------------------------------------------------------------------ deps
# Third-party dependencies of this package only (no workspace members).
# data-prep does not depend on shared-utils, so there is no "shared" stage.
FROM manifests AS deps
ARG PACKAGE
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --no-install-workspace --package ${PACKAGE}

# ------------------------------------------------------------------------- app
FROM deps AS app
ARG PACKAGE
COPY packages/data-prep/ packages/data-prep/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package ${PACKAGE}

# --------------------------------------------------------------------- runtime
FROM python:${PYTHON_VERSION}-slim AS runtime
# psycopg (pure python build) loads libpq at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 app
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1
# Writable cwd: the script creates prep.db here. $HOME holds the kagglehub
# cache and DuckDB's downloaded postgres extension.
WORKDIR /work
RUN chown app:app /work
COPY --from=app --chown=app:app /app/.venv /app/.venv
USER app
CMD ["python"]
