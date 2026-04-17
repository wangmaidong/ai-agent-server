from app.config.env import env
from app.utils.get_local_ips import get_local_ips

if __name__ == "__main__":
  import uvicorn

  # 获取环境变量中的端口号
  port = int(env.server_port)

  # 打印所有可用的访问地址
  print("\n服务已启动，以下是可用的访问地址：")
  print(f" - 本地访问: http://127.0.0.1:{port}")

  for ip in get_local_ips():
    print(f" - 网络访问: http://{ip}:{port}")

  print("\n")  # 空行美化输出

  """
uvicorn.run() 启动了一个异步事件循环来处理 HTTP 请求，
这个循环会一直运行直到服务器被手动停止（比如按下 Ctrl+C）。
因此，uvicorn.run() 之后的代码不会被执行，直到服务器关闭。
  """
  # 启动Uvicorn服务器
  uvicorn.run("app.main:app", host="0.0.0.0", port=port)

  # uvicorn.run之后的代码永远都不会执行
  # 使用FastAPI的 @app.on_event("startup")装饰器可以在服务器成功启动后执行代码
  print('App is running...(Never Callable)')
