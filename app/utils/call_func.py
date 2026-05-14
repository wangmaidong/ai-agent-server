import inspect


async def call_func(func, context):
  """
  自适应执行同步或异步函数，并根据参数名自动注入变量
  """
  # 1. 获取函数签名并筛选参数
  sig = inspect.signature(func)
  kwargs = {
    name: context[name]
    for name in sig.parameters
    if name in context
  }

  # 2. 判断函数类型并执行
  if inspect.iscoroutinefunction(func):
    # 如果是异步函数，必须 await
    return await func(**kwargs)
  else:
    # 如果是同步函数，直接调用
    return func(**kwargs)
