import httpx
from fastapi import APIRouter, Request, HTTPException, FastAPI
from fastapi.responses import StreamingResponse

from app.config.ai_configs import ai_configs


async def proxy_openai_request(request: Request, config_key: str):
  """
  通用代理函数：将请求转发至指定的上游模型服务
  """
  if config_key not in ai_configs:
    raise HTTPException(status_code=404, detail=f"Config {config_key} not found")

  config = ai_configs[config_key]
  target_url = config["url"]
  api_key = config["key"]
  real_model_name = config["model"]

  # 1. 获取原始请求体并修改模型名称
  body = await request.json()
  body["model"] = real_model_name  # 强制替换为上游真正识别的模型名

  # 2. 准备请求头
  headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
  }

  client = httpx.AsyncClient()

  # 3. 处理流式响应 (OpenAI 协议的关键)
  if body.get("stream", False):
    async def stream_generator():
      async with client.stream("POST", target_url, json=body, headers=headers, timeout=60.0) as response:
        async for chunk in response.aiter_bytes():
          yield chunk
      await client.aclose()

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

  # 4. 处理非流式响应
  else:
    response = await client.post(target_url, json=body, headers=headers, timeout=60.0)
    await client.aclose()
    return response.json()


def add_proxy_routes(app: FastAPI, config_name: str):
  """
  动态生成路由的辅助函数
  """
  # 自动根据配置判断是 chat 还是 embeddings 路径
  is_embedding = "embedding" in config_name or "embeddings" in ai_configs[config_name]["url"]
  path = "/v1/embeddings" if is_embedding else "/v1/chat/completions"

  @app.post(f"/{config_name}{path}")
  async def dynamic_proxy(request: Request):
    return await proxy_openai_request(request, config_name)

  print(f"🚀 Proxy LLM route: /{config_name}{path}")
