from datetime import datetime

from advanced_alchemy.base import UUIDBase
from uuid import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy import Column, Integer, UniqueConstraint, Index


class Base(DeclarativeBase): ...


class MovieRating(UUIDBase):
    __tablename__ = "movie_rating"
    movie_id: Mapped[UUID]
    user_id: Mapped[UUID]
    rating: Mapped[int]
    event_ts: Mapped[datetime]
    __table_args__ = (
        UniqueConstraint(
            "movie_id", "user_id", "event_ts", name="movie_rating_unique_events"
        ),
        Index("movie_rating_user_index", 'movie_id'),
    )
