import uuid
from datetime import date, datetime
from uuid import UUID

from litestar import Litestar, get
from litestar.di import NamedDependency
from litestar.plugins.sqlalchemy import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
    base,
)
from sqlalchemy import ForeignKey, func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..config import cfg


class Movie(base.UUIDBase):
    __tablename__ = "movie"
    title: Mapped[str]
    poster_link: Mapped[str]
    released_year: Mapped[datetime]
    certificate: Mapped[str | None] = None
    genre: Mapped[str | None] = None
    imdb_rating: Mapped[float | None] = None
    overview: Mapped[str | None] = None
    meta_score: Mapped[int]
    director_name: Mapped[str]
    gross: Mapped[str]
    user_rating: Mapped[int | None]=None
    user_rating_count: Mapped[int]=0


session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=cfg.db_url, session_config=session_config, create_all=True

)  # Create 'async_session' dependency.

