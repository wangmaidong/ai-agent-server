from app.middlewares.add_auth_middlewares import add_auth_middlewares
from app.middlewares.add_error_middlewares import add_error_middlewares

middlewares = [
  add_auth_middlewares,
  add_error_middlewares,
]
