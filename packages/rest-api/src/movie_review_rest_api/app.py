from litestar import Litestar, get
from . import rest_models

@get('/moview')
def list_moview() -> list[rest_models.MovieDetail]:
    return []


app = Litestar([list_moview])