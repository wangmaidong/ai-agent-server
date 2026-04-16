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

from app.utils.PER_REQ_CONFIG_MODIFIER import PER_REQ_CONFIG_MODIFIER


def add_graph_proxy_route(app: FastAPI):
  """
  将自定义工作流注册为 FastAPI 的流式接口
  """

  add_routes(
    app=app,
    runnable=create_graph(),
    path="/graph_proxy",
    per_req_config_modifier=PER_REQ_CONFIG_MODIFIER,
    enabled_endpoints=["invoke", "batch", "config_hashes"]
  )


def create_graph(checkpointer=InMemorySaver()):
  """
  创建 LangGraph 工作流图

  Args:
    checkpointer: 状态检查点保存器，默认为内存保存器
                   支持分布式部署时可替换为 Redis、PostgreSQL 等持久化存储

  Returns:
    编译后的工作流图实例
  """

  # 定义工作流状态 schema
  class StateSchema(TypedDict):
    # name_list: 使用 Annotated 类型注解，指定 add 为归约函数
    # 每次节点返回的 name_list 会自动累加到全局状态中
    name_list: Annotated[List[str], add]

  builder = StateGraph(StateSchema)

  def node_1(state, config: RunnableConfig):
    """
    工作流第一个节点：生成 0-100 的随机数
    返回格式必须匹配 StateSchema，name_list 会被自动累加到状态中
    """
    random_int = str(random.randint(0, 100)) + "-->>id:" + config.get('configurable').get('thread_id')
    print(["🧠节点执行", "node_1", random_int])
    return {"name_list": [f"node_1:{random_int}"]}

  def node_2(state):
    """
    工作流第二个节点：生成 100-200 的随机数
    state 参数包含当前累积的状态（可通过 state['name_list'] 访问）
    """
    random_int = random.randint(100, 200)
    print(["🧠节点执行", "node_2", random_int])
    return {"name_list": [f"node_2:{random_int}"]}

  def node_3(state):
    """
    工作流第三个节点：生成 300-400 的随机数
    节点执行完成后，所有 name_list 会通过 add 归约函数合并
    """
    random_int = random.randint(300, 400)
    print(["🧠节点执行", "node_3", random_int])
    return {"name_list": [f"node_3:{random_int}"]}

  # 注册三个节点到工作流
  builder.add_node(node_1)
  builder.add_node(node_2)
  builder.add_node(node_3)

  # 定义节点执行顺序：START -> node_1 -> node_2 -> node_3 -> END
  builder.add_edge(START, 'node_1')
  builder.add_edge('node_1', 'node_2')
  builder.add_edge('node_2', 'node_3')
  builder.add_edge('node_3', END)

  # 编译工作流图，注入检查点保存器
  # checkpointer 支持：
  # 1. 断点续传：工作流中断后可从最近检查点恢复
  # 2. 人机交互：在 interrupt 处暂停等待用户输入
  # 3. 状态持久化：跨请求保持工作流状态
  graph = builder.compile(checkpointer=checkpointer)

  return graph
