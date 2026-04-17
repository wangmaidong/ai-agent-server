import json
import random
import time
import uuid
from typing import Annotated, List
from operator import add

from langchain_core.runnables import RunnableConfig
from typing_extensions import TypedDict
from fastapi import FastAPI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.func import task, entrypoint
from langgraph.graph import StateGraph
from langgraph.types import interrupt
from langserve import add_routes
from starlette.responses import StreamingResponse

from app.controller.add_graph_proxy_route import create_graph
from app.utils.PER_REQ_CONFIG_MODIFIER import PER_REQ_CONFIG_MODIFIER, next_thread_id


def add_custom_stream_route(app: FastAPI):
  @app.post('/custom_stream')
  async def custom_stream():
    # 生成唯一的线程 ID，用于追踪和持久化工作流执行状态

    config = {"configurable": {"thread_id": next_thread_id()}}

    # 创建工作流图实例
    graph = create_graph()

    async def generator_function():
      """
      异步生成器函数，实现流式响应
      使用 astream 方法流式执行工作流，实时返回每个节点的执行结果
      """
      async for chunk in graph.astream(
        input={},  # 空输入，工作流从 START 节点自动开始
        config=config,  # 配置线程 ID，支持状态持久化和恢复
        stream_mode=['messages', 'updates']  # 同时流式消息和状态更新
      ):
        # 将每个执行块格式化为 SSE (Server-Sent Events) 格式
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    # 返回流式响应，客户端可以实时接收工作流执行进度
    return StreamingResponse(generator_function(), media_type="text/event-stream")
