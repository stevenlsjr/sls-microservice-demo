from uuid import UUID

from litestar import Request
from litestar.app import Litestar
from logging import getLogger
from opensearchpy import AsyncOpenSearch
from .config import cfg
from .rest_models import MovieDetail

log = getLogger(__name__)


async def on_startup(app: Litestar):
    client = AsyncOpenSearch(
        hosts=cfg.opensearch_hosts,
        verify_certs=cfg.opensearch_verify_certs,
        http_auth=cfg.opensearch_http_auth,
    )
    app.state["opensearch_client"] = client


async def on_shutdown(app: Litestar):
    client: AsyncOpenSearch = app.state["opensearch_client"]
    if client:
        await client.close()
    log.info(client)


async def provide_opensearch(request: Request) -> AsyncOpenSearch:
    app = request.app
    client: None | AsyncOpenSearch = app.state.get("opensearch_client", None)
    if not client:
        client = AsyncOpenSearch(
            hosts=cfg.opensearch_hosts,
            verify_certs=cfg.opensearch_verify_certs,
            auth=cfg.opensearch_http_auth,
        )
        app.state["opensearch_client"] = client
    return client


_MOVIES_INDEX = "imdb-movies-*"


async def search_movies(
    client: AsyncOpenSearch, search_text: str, limit: int, offset
):
    if search_text.strip() == "":
        search = {"query": {"match_all": {}}}
    else:
        search = {"query": {"match": {"title": search_text}}}

    search["from"] = offset
    search["size"] = limit
    print(search)
    res = await client.search(index=_MOVIES_INDEX, body=search)
    hits = res["hits"]["hits"]
    records = [
        MovieDetail(
            id=h["_id"],
            title=h["_source"]["title"],
            released_year=h["_source"]["released_year"],
            director_name=h["_source"]["director"],
            description=h["_source"]["description"],
            poster_link=h["_source"]["poster_link"],
            imdb_score=h["_source"]["imdb_score"],
            stars=h["_source"]["stars"],
        )
        for h in hits
    ]
    return records

async def get_by_id(client: AsyncOpenSearch, id: UUID):
    pass