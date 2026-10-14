# syntax=docker/dockerfile:1
#
# Build from the repo root (the uv workspace root):
#   podman build -f packages/rest-api/Dockerfile -t movie-review-rest-api .
#
# Stages are ordered from least to most frequently changing so that
# third-party deps and shared-utils stay cached when only service code changes.

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.12.15
ARG PACKAGE=movie-review-rest-api

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
FROM manifests AS deps
ARG PACKAGE
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --no-install-workspace --package ${PACKAGE}

# ---------------------------------------------------------------------- shared
# Workspace libraries (shared-utils), built as a wheel and installed non-editable.
FROM deps AS shared
ARG PACKAGE
COPY packages/shared-utils/ packages/shared-utils/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable --package ${PACKAGE} --no-install-package ${PACKAGE}

# ------------------------------------------------------------------------- app
FROM shared AS app
ARG PACKAGE
COPY packages/rest-api/ packages/rest-api/
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
WORKDIR /app
COPY --from=app --chown=app:app /app/.venv /app/.venv
USER app
EXPOSE 8000
CMD ["litestar", "--app", "movie_review_rest_api.app:app", "run", "--host", "0.0.0.0", "--port", "8000"]
