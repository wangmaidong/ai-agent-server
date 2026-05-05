import logging
from datetime import timedelta
from typing import Optional

from sqlmodel import select
from starlette.requests import Request

from app.auth.crypt_utils import crypt_utils
from app.auth.token_utils import token_utils
from app.config.env import env
from app.model.UserLoginLogsModel import UserLoginLogsModel
from app.model.UserModel import PrivateUserModel, PublicUser
from app.utils.mysql_utils import AsyncSessionDep, async_session
from app.utils.next_id import next_id


class AuthUtils:
  async def authenticate_user(self, username: str, password: str, session: AsyncSessionDep) -> PublicUser | None:
    """
     验证登录用户名以及密码
     """
    query = select(PrivateUserModel).where(PrivateUserModel.username == username)
    result = await session.execute(query)
    user_obj: PrivateUserModel | None = result.scalars().first()

    # 用户名username不存在
    if not user_obj:
      return None

    # 用户账号未激活
    if user_obj.valid != 'Y':
      return None

    # 环境变量启用了登陆密码验证
    if env.server_verify_pwd:
      if not crypt_utils.verify_password(password, user_obj.hash_password):
        return None

    # 验证通过，返回用户信息
    public_user = PublicUser.to_obj(user_obj.to_dict())

    return public_user

  async def create_login_logs(self, public_user: PublicUser, request: Request):
    """
    创建登录日志
    """
    try:
      async with async_session() as session:
        login_logs_cls = UserLoginLogsModel(
          id=await next_id(),
          created_by=public_user.id,
          updated_by=public_user.id,
          host=request.client.host,
          address="",  # 登录的地址，需要调用付费API将ip地址转化成真实地址
        )
        session.add(login_logs_cls)
        await session.commit()
    except Exception as e:
      logging.error(f"用户 [{public_user.username}@{request.client.host}] 创建登录日志失败:{e}")

  async def create_access_token(self, public_user: PublicUser):
    """
    创建访问token
    """
    access_token = token_utils.create_token(
      username=public_user.username,
      token_type="access",
      expires_delta=timedelta(seconds=env.jwt_access_token_expire_seconds),
    )
    # 加一个提前量，让用户早点更新token，避免用户在token即将过期时使用这个token
    access_expires = (env.jwt_access_token_expire_seconds - 3) * 1000
    return access_token, access_expires

  async def create_refresh_token(self, public_user: PublicUser):
    """
    创建refresh_token
    """
    refresh_token = token_utils.create_token(
      username=public_user.username,
      token_type="refresh",
      expires_delta=timedelta(seconds=env.jwt_refresh_token_expire_seconds),
    )
    # 加一个提前量，让用户早点更新token，避免用户在token即将过期时使用这个token
    refresh_expires = (env.jwt_refresh_token_expire_seconds - 5) * 1000
    return refresh_token, refresh_expires

  async def create_login_token(self, public_user: PublicUser, request: Request):
    """
    用户登录之后创建访问token以及刷新token
    """
    # 记录登录日志
    await self.create_login_logs(public_user, request)
    # 创建access_token
    access_token, access_expires = await self.create_access_token(public_user)
    # 创建refresh_token
    refresh_token, refresh_expires = await self.create_refresh_token(public_user)
    return {
      "result": public_user,
      "access_token": access_token,
      "access_expires": access_expires,
      "refresh_token": refresh_token,
      "refresh_expires": refresh_expires,
    }


auth_utils = AuthUtils()
