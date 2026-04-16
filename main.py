import logging
from typing import List, Union
from contextlib import asynccontextmanager
import datetime

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html, get_redoc_html, get_swagger_ui_html
from fastapi.responses import RedirectResponse
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableGenerator
from langchain_openai import ChatOpenAI
from langserve import add_routes
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

# 引入环境配置文件
from app.config.env import env
# 引入获取本机ip的方法
from app.utils.get_local_ips import get_local_ips
# 引入大模型创建方法
from app.utils.llm_utils import create_llm
# 引入graph自定义工作流
from app.controller.add_graph_proxy_route import add_graph_proxy_route
from app.controller.add_custom_stream_route import add_custom_stream_route

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
app.mount("/static", StaticFiles(directory="static"), name="static")


# 自定义 Swagger 页面（使用本地资源）
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """
    提供自定义的 Swagger UI 文档页面

    Returns:
        Swagger UI HTML 页面，使用本地静态资源加载
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.min.js",
        swagger_css_url="/static/swagger-ui.min.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    """
    处理 Swagger UI 的 OAuth2 重定向回调

    Returns:
        OAuth2 重定向 HTML 响应
    """
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """
    提供自定义的 ReDoc 文档页面

    Returns:
        ReDoc HTML 页面，使用本地静态资源加载
    """
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get("/")
async def redirect_root_to_docs():
    """
    将根路径请求重定向到 Swagger 文档页面

    Returns:
        重定向响应到 /docs 路径
    """
    return RedirectResponse("/docs")

@app.get("/chat")
async def chat():
  model_qwen = create_llm(platform_code='bailian-qwen-turbo')
  model_qwen_output = model_qwen.invoke("你好，你是谁").content
  print(f"model_qwen output: {model_qwen_output}")

  model_doubao = create_llm(platform_code='huoshan-doubao')
  model_doubao_output = model_doubao.invoke("你好，你是谁").content
  print(f"model_doubao output: {model_doubao_output}")

  return {
    "model_qwen_output": model_qwen_output,
    "model_doubao_output": model_doubao_output
  }

add_graph_proxy_route(app)
add_custom_stream_route(app)

if __name__ == "__main__":
    import uvicorn

    # 获取环境变量中的端口号
    port = int(env.server_port)
    # 打印所有可用的访问地址
    print("\n服务已启动，以下是可用的访问地址：")
    print(f" - 本地访问: http://127.0.0.1:{port}")

    for ip in get_local_ips():
      print(f" - 网络访问: http://{ip}:{port}")

    print("\n")  # 空行美化输出
    # 启动Uvicorn服务器
    uvicorn.run("main:app", host="0.0.0.0", port=port)
    # uvicorn.run之后的代码永远都不会执行
    # 使用FastAPI的 @app.on_event("startup")装饰器可以在服务器成功启动后执行代码
    print('App is running...(Never Callable)')
