import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html, get_redoc_html, get_swagger_ui_html
from fastapi.responses import RedirectResponse
from langchain.chat_models import init_chat_model
from langserve import add_routes
from starlette.staticfiles import StaticFiles

from app.config.env import env
from app.controller.add_custom_stream_route import add_custom_stream_route
from app.controller.add_graph_proxy_route import add_graph_proxy_route
from app.routes import routes
from app.utils.get_local_ips import get_local_ips
from app.utils.llm_utils import create_llm


@asynccontextmanager
async def lifespan(app: FastAPI):
  print(f"应用启动：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  yield
  print(f"应用销毁：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


app = FastAPI(
  lifespan=lifespan,
  docs_url=None,  # 禁用默认 Swagger
  redoc_url=None,  # 禁用默认 ReDoc
)

for add_route_func in routes:
  add_route_func(app)

print("/*---------------------------------------main-------------------------------------------*/")
