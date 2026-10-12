from typing import Literal
from uuid import UUID

from msgspec import Struct


class MovieRatingEvent(Struct):
    movie_id: UUID
    user_id: UUID
    rating: int
    type: Literal['movie-rating'] = 'movie-rating'
