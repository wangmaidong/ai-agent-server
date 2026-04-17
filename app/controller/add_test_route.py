from fastapi import FastAPI
from langchain.chat_models import init_chat_model
from langserve import add_routes

from app.utils.llm_utils import create_llm


def add_test_route(app: FastAPI):
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

  # Edit this to add the chain you want to add
  # add_routes(app, NotImplemented)

  model = init_chat_model(
    model="doubao-1-5-pro-32k-250115",  # 你的模型名
    model_provider="openai",  # 必须填 openai（兼容协议）
    base_url="https://ark.cn-beijing.volces.com/api/v3/",  # 你的自定义 API URL
    api_key="b1e7c7e0-33af-480e-b0a8-2812ba97f7b1",  # 本地模型随便填
    temperature=0.7,
    streaming=False
  )

  add_routes(app=app, runnable=model, path="/doubao")
