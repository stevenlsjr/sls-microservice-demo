from logging import getLogger
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import dotenv
from litestar import Litestar, MediaType, Request, get, put
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.di import NamedDependency, Provide
from litestar.exceptions import HTTPException
from litestar.params import QueryParameter
from litestar.plugins.opentelemetry import OpenTelemetryPlugin
from litestar.response import Template
from litestar.template.config import TemplateConfig
from litestar_htmx import HTMXPlugin, HTMXRequest, HTMXTemplate
from opensearchpy import AsyncOpenSearch
from sqlalchemy.ext.asyncio import AsyncSession

from . import db, opensearch_api, producer_service, rest_models
from .auth import jwt_auth

basedir = Path(__file__).parent.resolve()

dotenv.load_dotenv()

log = getLogger(__name__)


@get("/movies")
async def list_movies(
    *,
    request: Request,
    limit: Annotated[int, QueryParameter(gt=1, le=1000)] = 10,
    offset: Annotated[int, QueryParameter(ge=0)] = 0,
    search_text: str = "",
    opensearch: NamedDependency[AsyncOpenSearch],
) -> list[rest_models.MovieDetail]:
    query_result = await opensearch_api.search_movies(
        opensearch, search_text, limit=limit, offset=offset
    )
    preferred_type = request.accept.best_match(
        [MediaType.JSON, MediaType.HTML], default=MediaType.TEXT
    )
    if preferred_type == MediaType.HTML:
        return Template(
            template_name="partials/movies-list.html",
            context={"movies": query_result},
            media_type=MediaType.HTML,
        )
    else:
        return query_result


@get("/movies/{id:uuid}")
async def get_movie(
    id: UUID,
    opensearch: NamedDependency[AsyncOpenSearch],
) -> rest_models.MovieDetail:
    return opensearch_api.get_by_id(opensearch, id)


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


@get("/")
def index(request: HTMXRequest) -> Template:
    return HTMXTemplate(template_name="index.html", context={})


app = Litestar(
    [list_movies, get_movie, rate_movie, index],
    plugins=[producer_service.KafkaInitPlugin(), OpenTelemetryPlugin(), HTMXPlugin()],
    on_app_init=[jwt_auth.on_app_init],
    middleware=[jwt_auth.middleware],
    template_config=TemplateConfig(
        directory=basedir / "templates",
        engine=JinjaTemplateEngine,
    ),
    dependencies={"opensearch": Provide(opensearch_api.provide_opensearch)},
    on_startup=[opensearch_api.on_startup],
    on_shutdown=[opensearch_api.on_shutdown],
)
