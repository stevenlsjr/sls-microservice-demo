from itertools import islice
import logging
from pathlib import Path
from typing import Annotated
import pendulum
from opensearchpy import OpenSearch
import os
import typer
import duckdb

log = logging.getLogger()
app = typer.Typer()

OPENSEARCH_HOSTS = os.getenv("OPENSEARCH_HOSTS", "https://localhost:9200")
OPENSEARCH_AUTH = os.getenv("OPENSEARCH_AUTH", "")


def create_index_template(client: OpenSearch):
    client.indices.put_template(
        name="imdb-movies",
        body={
            "index_patterns": ["imdb-movies-*"],
            "template": {
                "settings": {"number_of_shards": 2, "number_of_replicas": 1},
                "mappings": {
                    "properties": {
                        "title": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "director": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "stars": {"type": "text"},
                        "genre": {
                            "type": "text",
                            "fields": {"raw": {"type": "keyword"}},
                        },
                        "imdb_score": {
                            "type": "double",
                        },
                        "meta_score": {"type": "long"},
                        "community_rating": {"type": "double"},
                    }
                },
            },
        },
    )


@app.command()
def main(
    verify_certs: bool = True,
    duckdb_path: Annotated[
        Path, typer.Option(dir_okay=False, exists=True)
    ] = "./prep.db",
    update_index_template: bool = True,
    index_postfix: str | None = None,
):
    if not index_postfix:
        index_postfix = pendulum.now().format("-YYYY-MM-DD")
    if OPENSEARCH_AUTH:
        auth = OPENSEARCH_AUTH.split(":", 1)
    else:
        auth = None
    client = OpenSearch(
        hosts=OPENSEARCH_HOSTS.split(","), verify_certs=verify_certs, http_auth=auth
    )
    if update_index_template:
        create_index_template(client)
    with duckdb.connect(duckdb_path, read_only=True) as conn:
        df = conn.sql(
            """
        
        with operation AS ( select
            to_json({
                "index": {
                    _index : 'imdb-movies'||$index_postfix,
                    _id : id
                }
            }) as header,
            to_json({
                title : title,
                director : director,
                stars : stars,
                genre : genre,
                imdb_score : imdb_rating
            }) as body

           from imdb_dataset
           order by title
           )
        select header || '\n' || body from operation
        """,
            params={"index_postfix": index_postfix},
        )

        body = '\n'.join(i[0] for i in df.fetchall())
        res = client.bulk(body=body)
        print(res)


if __name__ == "__main__":
    logging.basicConfig()
    app()
