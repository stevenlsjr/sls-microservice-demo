import logging

# super ugly, but can't get otel to configure proper log level
# otherwise
logging.root.setLevel(logging.DEBUG)

import asyncio

import typer as ty

from review_service import consumer

log = logging.getLogger(__name__)


app = ty.Typer()


@app.command()
def main():
    asyncio.run(consumer.run_consumer())

if __name__=='__main__':
    logging.basicConfig()
    app()