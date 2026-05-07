import traceback

from fastapi import FastAPI, HTTPException
from fastapi.logger import logger
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse


def add_error_middlewares(app: FastAPI):
  """
  异常中间件，用于捕获请求处理函数中raise的异常对象
  返回格式化的JsonResponse
  """

  @app.middleware("http")
  async def errors_handling(request: Request, call_next):
    try:
      return await call_next(request)

    except HTTPException as exc:
      # 对于主动抛出的 401/403 等，通常不需要打印长堆栈，只需记录简单日志
      logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
      return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
      )

    except Exception as e:
      # --- 关键部分：打印异常堆栈 ---
      # 方法 A：使用 traceback 直接打印到控制台
      traceback.print_exc()

      # 方法 B：使用 logger 记录（推荐，会自动包含堆栈信息）
      # logger.error(f"Internal Server Error: {str(e)}", exc_info=True)

      return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
          "success": False,
          "error": f"Internal Server Error: {e}",
        },
      )
