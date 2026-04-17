import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html, get_redoc_html, get_swagger_ui_html
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import init_chat_model
from langserve import add_routes
from starlette.staticfiles import StaticFiles

# 引入环境变量配置
from app.config.env import env
# 批量注册多个路由接口
from app.routes import routes
# 测试mysql链接服务是否正常
from app.utils.mysql_utils import check_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
  print(f"应用启动：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  async_engine = await check_database_connection()
  yield
  print(f"应用销毁：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
  await async_engine.dispose()


app = FastAPI(
  lifespan=lifespan,
  docs_url=None,  # 禁用默认 Swagger
  redoc_url=None,  # 禁用默认 ReDoc
)

for add_route_func in routes:
  add_route_func(app)

if env.server_enable_cors:
  app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
  )

print("/*---------------------------------------main-------------------------------------------*/")
