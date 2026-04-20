from app.controller.add_custom_stream_route import add_custom_stream_route
from app.controller.add_docs_route import add_docs_route
from app.controller.add_graph_proxy_route import add_graph_proxy_route
from app.controller.add_test_route import add_test_route
from app.model.LlmDemoModel import add_llm_demo_route
from app.controller.add_file_route import add_file_route
from app.utils.next_id import add_next_id_route
# /*@formatter:off*/
routes = [
  add_docs_route,               # 代理文档静态资源
  add_test_route,               # 测试接口
  add_graph_proxy_route,        # 代理自定义工作流
  add_custom_stream_route,      # 自定义流式接口
  add_llm_demo_route,           # 测试用户模块
  add_next_id_route,            # 生成ID接口
  add_file_route,               # 文件上传接口
]
# /*@formatter:on*/
