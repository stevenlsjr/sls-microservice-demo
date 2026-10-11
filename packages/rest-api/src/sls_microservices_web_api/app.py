from litestar import Litestar, get

@get('/')
def index() -> str:
    return 'hello'

app = Litestar([index])