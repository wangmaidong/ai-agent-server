import logging
from typing import List, Union

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

from app.config.env import env

app = FastAPI(
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

# @app.get("/chat")
# async def chat():
model = init_chat_model(
    model="doubao-1-5-pro-32k-250115",  # 你的模型名
    model_provider="openai",  # 必须填 openai（兼容协议）
    base_url="https://ark.cn-beijing.volces.com/api/v3/",  # 你的自定义 API URL
    api_key="e65b2b55-a28e-40cd-9b32-493cef36e248",  # 本地模型随便填
    temperature=0.7,
    streaming=False
)

add_routes(app=app, runnable=model, path="/doubao")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=env.server_port)
