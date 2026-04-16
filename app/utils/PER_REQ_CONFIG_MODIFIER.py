import uuid

def next_thread_id():
  return str(uuid.uuid4())

# 用于配置LangServe的add_routes函数的per_req_config_modifier参数
# 将请求中的config参数传递给Graph
async def PER_REQ_CONFIG_MODIFIER(config, request):
  body = await request.json()
  return {
    "configurable": {
      "thread_id":
        body
        .get("config", {})
        .get("configurable", {})
        .get("thread_id", None) or next_thread_id()
    }
  }
