from logging import getLogger
from typing import Annotated
from uuid import UUID

import dotenv
import sqlalchemy as sa
from litestar import Litestar, Request, get, put
from litestar.di import NamedDependency
from litestar.exceptions import HTTPException
from litestar.params import QueryParameter
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from sqlalchemy.ext.asyncio import AsyncSession
from confluent_kafka.aio.producer import AIOProducer
from litestar.plugins.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin

from . import db, producer_service, rest_models
from .auth import jwt_auth

dotenv.load_dotenv()

log = getLogger(__name__)


@get("/movies")
async def list_movies(
    db_session: NamedDependency[AsyncSession],
    limit: Annotated[int, QueryParameter(gt=1, le=1000)] = 10,
    offset: Annotated[int, QueryParameter(ge=0)] = 0,
) -> list[db.Movie]:
    query = (
        sa.select(db.Movie)
        .limit(limit)
        .offset(offset)
        .order_by(
            sa.desc(db.Movie.meta_score),
        )
    )
    movies = await db_session.scalars(query)

    return list(movies)


@get("/movies/{id:uuid}")
async def get_movie(db_session: NamedDependency[AsyncSession], id: UUID) -> db.Movie:
    query = sa.select(db.Movie).where(db.Movie.id == id)
    movie = await db_session.scalar(query)

    if movie is None:
        raise HTTPException(status_code=404, detail="not found")
    return movie


@put("/movies/{id:uuid}/rate")
async def rate_movie(
    request: Request,
    db_session: NamedDependency[AsyncSession],
    kafka_ratings_service: NamedDependency[producer_service.KafkaRatingsPublisher],
    id: UUID,
    data: rest_models.MovieRatingBody,
) -> None:
    movie_exists = await db_session.scalar(
        sa.select(sa.func.count()).select_from(db.Movie).where(db.Movie.id == id)
    )
    if movie_exists  != 1:
        raise HTTPException(status_code=404, detail="not found")
    data.movie_id = id
    user_id = request.user.id
    await kafka_ratings_service.send_rating(user_id=user_id, rating=data)


app = Litestar(
    [list_movies, get_movie, rate_movie],
    plugins=[
        SQLAlchemyPlugin(config=db.sqlalchemy_config),
        producer_service.KafkaInitPlugin(),
        OpenTelemetryPlugin(OpenTelemetryConfig()),
    ],
    on_app_init=[jwt_auth.on_app_init],
    middleware=[jwt_auth.middleware],
)
