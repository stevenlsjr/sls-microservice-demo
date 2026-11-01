from logging import getLogger
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import dotenv
import sqlalchemy as sa
from litestar import Litestar, Request, get, put
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.di import NamedDependency
from litestar.exceptions import HTTPException
from litestar.params import QueryParameter
from litestar.plugins.opentelemetry import OpenTelemetryPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.template.config import TemplateConfig
from litestar_htmx import HTMXPlugin, HTMXRequest, HTMXTemplate
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.response import Template

from . import db, producer_service, rest_models
from .auth import jwt_auth

basedir = Path(__file__).parent.resolve()

dotenv.load_dotenv()

log = getLogger(__name__)


@get("/movies")
async def list_movies(
    request: Request,
    db_session: NamedDependency[AsyncSession],
    limit: Annotated[int, QueryParameter(gt=1, le=1000)] = 10,
    offset: Annotated[int, QueryParameter(ge=0)] = 0,
    search_text: str=''
) -> list[rest_models.MovieDetail]:
    return [rest_models.MovieDetail(id=uuid4(), title=f'searching for {search_text}', released_year='2024', director_name='eee')]


@get("/movies/{id:uuid}")
async def get_movie(id: UUID) -> db.Movie:
    raise NotImplementedError()

@put("/movies/{id:uuid}/rate")
async def rate_movie(
    request: Request,
    kafka_ratings_service: NamedDependency[producer_service.KafkaRatingsPublisher],
    id: UUID,
    data: rest_models.MovieRatingBody,
) -> None:
    raise NotImplementedError()
     
    # if movie_exists  != 1:
    #     raise HTTPException(status_code=404, detail="not found")
    # data.movie_id = id
    # user_id = request.user.id
    # await kafka_ratings_service.send_rating(user_id=user_id, rating=data)

@get('/')
def index(request: HTMXRequest) ->Template:
    return HTMXTemplate(template_name="index.html", context={})


app = Litestar(
    [list_movies, get_movie, rate_movie, index],
    plugins=[
        SQLAlchemyPlugin(config=db.sqlalchemy_config),
        producer_service.KafkaInitPlugin(),
        OpenTelemetryPlugin(),
        HTMXPlugin()
    ],
    on_app_init=[jwt_auth.on_app_init],
    middleware=[jwt_auth.middleware],
    template_config=TemplateConfig(
        directory=basedir / 'templates',
        engine=JinjaTemplateEngine,
    ),
)
