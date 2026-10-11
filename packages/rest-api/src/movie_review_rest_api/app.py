from logging import getLogger
from uuid import UUID

from litestar import Litestar, get
from litestar.di import NamedDependency
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
import sqlalchemy as sa

from . import rest_models, db
from .auth import jwt_auth
from litestar.params import QueryParameter
import dotenv
from typing import Annotated

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

@get('/movies/{id}')
async def get_movie(
    db_session: NamedDependency[AsyncSession],
    id: UUID
) -> db.Movie:
    query = sa.select(db.Movie).where(db.Movie.id == id)
    movie = await db_session.scalar(query)
    if movie is None:
        raise NotImplementedError()
    return movie

    


app = Litestar(
    [list_movies, get_movie],
    plugins=[SQLAlchemyPlugin(config=db.sqlalchemy_config)],
    on_app_init=[jwt_auth.on_app_init],
)
