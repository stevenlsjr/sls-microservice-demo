import os
import uuid
from pathlib import Path

import dotenv
import duckdb
import kagglehub

dotenv.load_dotenv()

uuid5_ns = uuid.UUID("a82d9361-5e1f-44c1-b6e8-b58ee0c1d869")


def get_movie_uuid5(title: str) -> str:
    return str(uuid.uuid5(uuid5_ns, title))


db = duckdb.connect("prep.db")
db.create_function("get_movie_uuid5", get_movie_uuid5)

path = Path(kagglehub.dataset_download("debanganghosh/imdb-dataset"))
db.sql(f"""
drop table if exists imdb_dataset;
create table if not exists imdb_dataset AS 
WITH src AS (
    select * from '{path / "imdb_top_1000.csv"}'
)
select
    get_movie_uuid5(src.Series_Title || src.Released_Year || src.Director) as id,
    src.Poster_Link                     as poster_link,
    src.Series_title                    as title,
    coalesce(TRY(src.Released_Year::timestamptz),
            TRY((src.Released_Year || '-01-01')::timestamptz)
            )
                as released_year,
    src.Certificate                     as certificate,
    runtime,
    genre,
    imdb_rating,
    overview,
    meta_score,
    director,
    [Star1, Star2, Star3, Star4]        as stars,
    replace(gross, ',', '')::int        as gross

   from src
""")

db.sql(f"""
create secret pg_secret (
    type POSTGRES,
    user '{os.environ["DB_USERNAME"]}',
    password '{os.environ["DB_PASSWORD"]}'
);
attach '{os.environ["DB_CONNSTRING"]}' as runtime_db (TYPE POSTGRES, secret 'pg_secret');
""")

db.sql("""
INSERT or replace into runtime_db.movie
(
    id,
    title,
    poster_link,
    released_year,
    certificate,
    genre,
    imdb_rating,
    overview,
    meta_score,
    director_name,
    gross
    )
(
select
    id,
    title,
    poster_link,
    coalesce(released_year, '1990-01-01'),
    certificate,
    genre,
    imdb_rating,
    overview,
    coalesce(meta_score, 0),
    director,
    coalesce(gross, 0)

from imdb_dataset
);
call postgres_execute('runtime_db', $$
update movie
set _search_index = to_tsvector(title || ' ' || overview);
$$);
""")
