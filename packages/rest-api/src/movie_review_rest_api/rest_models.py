from msgspec import Struct
from uuid import UUID
from datetime import datetime

##
# Read-optimizated data model


class MovieDetail(Struct):
    id: UUID
    title: str
    publish_date: datetime
    rating: int

