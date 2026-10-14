import logging
from uuid import UUID

# super ugly, but can't get otel to configure proper log level
# otherwise
logging.root.setLevel(logging.DEBUG)

import asyncio

import typer as ty

from review_service import consumer

log = logging.getLogger(__name__)


app = ty.Typer()

@app.command()
def setup_topics():
    consumer.setup_topics()


@app.command()
def worker():
    asyncio.run(consumer.run_consumer())

@app.command()
def get_materialized_rating(movie_id: UUID):
    asyncio.run(consumer.materialize_movie_ratings(movie_id))

if __name__=='__main__':
    logging.basicConfig()
    app()