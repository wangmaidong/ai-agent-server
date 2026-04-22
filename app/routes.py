from app.controller.add_custom_stream_route import add_custom_stream_route
from app.controller.add_docs_route import add_docs_route
from app.controller.add_graph_proxy_route import add_graph_proxy_route
from app.controller.add_test_route import add_test_route
# from app.model.LlmDemoModel import add_llm_demo_route
from app.controller.add_file_route import add_file_route
from app.utils.next_id import add_next_id_route
from app.utils.add_model_routes import add_model_routes

from app.model.LlmDemoModel import LlmDemoModel
from app.model.ResumeTemplateModel import ResumeTemplateModel
from app.model.ResumeUserModel import ResumeUserModel
from app.utils.add_proxy_routes import add_proxy_routes
# /*@formatter:off*/
routes = [
  add_docs_route,               # 代理文档静态资源
  add_test_route,               # 测试接口
  add_graph_proxy_route,        # 代理自定义工作流
  add_custom_stream_route,      # 自定义流式接口
  add_next_id_route,            # 生成ID接口
  add_file_route,               # 文件上传接口
  lambda app: add_model_routes(app,LlmDemoModel,'/llm_demo'),                     # LlmDemo 测试用户模块,
  lambda app: add_model_routes(app,ResumeTemplateModel,'/llm_resume_template'),   # 简历模板
  lambda app: add_model_routes(app,ResumeUserModel,'/llm_resume_user'),           # 用户简历
  lambda app: add_proxy_routes(app, 'huoshan-doubao'),
  lambda app: add_proxy_routes(app, 'huoshan-doubao-vision'),
  lambda app: add_proxy_routes(app, 'bailian-qwen3.6-plus'),
]
# /*@formatter:on*/
