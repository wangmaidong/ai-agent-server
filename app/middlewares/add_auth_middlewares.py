from fastapi import FastAPI, HTTPException
from starlette import status
from starlette.requests import Request

from app.auth.crypt_utils import crypt_utils
from app.auth.token_utils import TokenInfo
from app.config.env import env
from app.model.UserModel import user_cache, PublicUser
from app.utils.whitelist import is_white_listed


def add_auth_middlewares(app: FastAPI):
  @app.middleware("http")
  async def add_oauth_middleware(request: Request, call_next):

    # 初始化 request.state 属性，确保在整个请求生命周期内（如后续路由或依赖注入中）
    # 访问 user 和 token 属性时不会因属性未定义而抛出 AttributeError。
    # request.state 不可以JSON序列化
    request.state.user = None
    request.state.token = None

    path = request.url.path
    # 1. 处理 OPTIONS 请求 (CORS 预检)
    if request.method == "OPTIONS":
      return await call_next(request)

    # 2. 接口白名单校验
    if is_white_listed(path):
      return await call_next(request)

    is_api_route = path.startswith("/api")
    auth_header = request.headers.get("Authorization", None)
    token = auth_header.strip() if auth_header else None

    if token and token.startswith("Bearer "):
      token = token[7:]

    # 认证token，无效或者过期都会得到None
    token_info: TokenInfo | None = crypt_utils.jwt_decode(token) if token else None

    if not token_info:
      # token不存在
      if not env.jwt_global_enable:
        # 没有开启认证，直接放行
        return await call_next(request)
      else:
        raise HTTPException(
          detail="The token in the request header is missing",
          status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # api token只能用于/api开头的接口（这是设计约束）
    if is_api_route:
      if token_info['token_type'] != 'api':
        raise HTTPException(
          detail="invalid token type!",
          status_code=status.HTTP_401_UNAUTHORIZED,
        )
    # 普通认证接口仅允许用access令牌
    elif token_info['token_type'] != 'access':
        raise HTTPException(
          detail="invalid token type!",
          status_code=status.HTTP_401_UNAUTHORIZED,
        )

    private_user_dict: dict | None = await user_cache.get_cache(token_info['username'])
    if not private_user_dict or private_user_dict.get('valid') != 'Y':
      raise HTTPException(
        detail="用户已经失效",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )
    public_user = PublicUser.to_obj(private_user_dict)

    request.state.user = public_user
    request.state.token = token
    return await call_next(request)
