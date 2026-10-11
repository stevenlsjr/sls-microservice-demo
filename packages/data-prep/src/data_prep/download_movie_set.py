import duckdb
import kagglehub
from pathlib import Path
import uuid

uuid5_ns = uuid.UUID("a82d9361-5e1f-44c1-b6e8-b58ee0c1d869")

def get_movie_uuid5(title: str) -> str:
    return str(uuid.uuid5(uuid5_ns, title))

duckdb.create_function('get_movie_uuid5', get_movie_uuid5)

path = Path(kagglehub.dataset_download("debanganghosh/imdb-dataset"))
duckdb.sql(f"""
create table imdb_dataset AS 
WITH src AS (
    select * from '{path / "imdb_top_1000.csv"}'
)
select 
    get_movie_uuid5(src.Series_Title) as id,
    src.Poster_Link                     as poster_link,
    src.Series_title                    as title,
    coalesce(TRY(src.Released_Year::timestamptz),
            TRY((src.Released_Year || '01-01')::timestamptz))
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

print(duckdb.sql("from imdb_dataset").dtypes)
