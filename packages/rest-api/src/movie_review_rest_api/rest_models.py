from datetime import datetime
from uuid import UUID

from msgspec import Struct

##
# Read-optimizated data model


class MovieDetail(Struct):
    id: UUID
    title: str
    released_year: datetime
    director_name: str
    description: str
    poster_link: str
    imdb_score: float
    stars: list[str]


class MovieRatingBody(Struct):
    movie_id: UUID
    rating: int

