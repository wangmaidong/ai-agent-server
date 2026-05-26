from app.batis.batis_interceptors.BatisInterceptor import BatisInterceptor
from app.utils.call_func import call_func

VALID_ACTIONS = {
  "before_list", "after_list",
  "before_insert", "after_insert",
  "before_update", "after_update",
  "before_batch_insert", "after_batch_insert",
  "before_batch_update", "after_batch_update",
  "before_delete", "after_delete",
}


def batis_aop(module: str, action: list[str]):
  invalid_actions = set(action) - VALID_ACTIONS
  if invalid_actions:
    raise ValueError(f"Invalid action(s): {invalid_actions}. Valid actions are: {VALID_ACTIONS}")

  def decorator(func):
    interceptor_kwargs = {"module": module}
    for act in action:
      interceptor_kwargs[act] = func
    batis_interceptor_manager.add(BatisInterceptor(**interceptor_kwargs))
    return func

  return decorator


class BatisInterceptorManager:
  def __init__(self):
    interceptors: dict[str, list[BatisInterceptor]] = {}
    self.interceptors = interceptors

  def add(self, target: BatisInterceptor):
    target_interceptor_list = self.interceptors.get(target.module, [])
    target_interceptor_list.append(target)
    self.interceptors[target.module] = target_interceptor_list

  async def call(self, module: str, batis_type: str, **kwargs):
    if module.startswith('/'):
      module = module[1:]
    if module.endswith('/'):
      module = module[:-1]
    match_interceptors = self.interceptors.get(module, [])
    for item in match_interceptors:
      interceptor_method = getattr(item, batis_type, None)  # 使用 getattr 获取方法
      if interceptor_method and callable(interceptor_method):
        await call_func(interceptor_method, kwargs)


batis_interceptor_manager = BatisInterceptorManager()
