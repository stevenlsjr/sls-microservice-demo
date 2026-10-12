import os
import logging
# super ugly, but can't get otel to configure proper log level
# otherwise
logging.root.setLevel(logging.DEBUG)

import typer as ty
from review_service import consumer
import asyncio
import os
log = logging.getLogger(__name__)


app = ty.Typer()


@app.command()
def main():
    asyncio.run(consumer.run_consumer())

if __name__=='__main__':
    app()