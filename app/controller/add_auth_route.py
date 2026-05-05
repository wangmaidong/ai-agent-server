import logging
from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import select
from starlette import status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.auth.auth_utils import auth_utils
from app.auth.crypt_utils import crypt_utils
from app.auth.token_utils import token_utils, TokenInfo
from app.config.env import env
from app.model.UserModel import RegistryUserSchema, PrivateUserModel, PublicUser, UserValidStatus
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.next_id import next_id


def add_auth_route(app: FastAPI):
  @app.post("/registry")
  async def registry(registry_user: RegistryUserSchema, session: AsyncSessionDep):
    """
    通过用户名、密码、邮箱、用户昵称注册账号
    """
    is_valid, error_msg = validate_password_strength(registry_user.password)
    if not is_valid:
      raise HTTPException(detail=error_msg, status_code=status.HTTP_400_BAD_REQUEST)
    # /*---------------------------------------用户名或者邮箱是否已经存在-------------------------------------------*/
    query = select(PrivateUserModel).where(
      (PrivateUserModel.username == registry_user.username) | (PrivateUserModel.email == registry_user.email)
    )
    result = await session.execute(query)
    user_obj = result.scalars().first()

    if user_obj:
      logging.warning(f"用户名或者邮箱已经存在！{registry_user}")
      raise HTTPException(detail=f"用户名或者邮箱已经存在！", status_code=status.HTTP_400_BAD_REQUEST)

    # /*---------------------------------------注册用户信息-------------------------------------------*/
    user = PrivateUserModel(
      username=registry_user.username,
      full_name=registry_user.full_name,
      email=registry_user.email,
      hash_password=crypt_utils.hash_password(registry_user.password),
      valid='N'
    )
    user.id = await next_id(1)

    session.add(user)
    # 提交事务（保存到数据库）
    await session.commit()
    # 刷新实例，获取数据库生成的最新数据（如自动更新的时间字段）
    await session.refresh(user)

    # /*---------------------------------------返回用户信息以及激活账号访问地址-------------------------------------------*/
    public_user = PublicUser.to_obj(user.to_dict())

    # 验证用户账号的token 7天内有效
    verify_token = token_utils.create_token(user.username, "verify", expires_delta=timedelta(days=7 * 3))

    return {
      # 返回用户信息
      "result": public_user,
      # 访问这个url地址就可以激活账号，实际上这里我们应该把这个激活账号访问地址，通过邮件发送给用户
      # 但是因为我们没有条件配置邮件服务，所以这里我们将这个激活账号的url返回前端，让用户去浏览器中访问激活账号
      "valid_url": f"{env.server_verify_path}?token={verify_token}"
    }

  @app.get("/verify")
  async def verify(session: AsyncSessionDep, token: str = Query(..., description="激活用户账号的token")):
    """激活账号"""
    token_info = token_utils.decode_token(token)
    if not token_info:
      raise HTTPException(
        detail="token无效或已过期",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )
    username = token_info['username']

    # 使用行级锁防止并发激活
    query = select(PrivateUserModel).where(PrivateUserModel.username == username).with_for_update()
    result = await session.execute(query)
    user_obj: PrivateUserModel | None = result.scalars().first()
    if not user_obj:
      raise HTTPException(
        detail="用户名不存在",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )
    if user_obj.valid == UserValidStatus.Y:
      return {"result": f"账号'{username}'已经激活"}

    print("激活账号：", username)
    user_obj.valid = UserValidStatus.Y
    session.add(user_obj)
    await session.commit()
    await session.refresh(user_obj)
    return RedirectResponse(url=env.server_login_path)

  @app.post("/login")  # 习惯性的登录地址
  @app.post("/token")  # 兼容swagger
  async def _token(request: Request, session: AsyncSessionDep, form_data: OAuth2PasswordRequestForm = Depends()):
    logging.info(f"login with: {form_data}")

    if not form_data.password:
      raise HTTPException(detail="密码不能为空", status_code=status.HTTP_401_UNAUTHORIZED)

    user = await auth_utils.authenticate_user(form_data.username, form_data.password, session)

    if not user:
      raise HTTPException(detail="用户名或者密码不正确", status_code=status.HTTP_401_UNAUTHORIZED)

    return await auth_utils.create_login_token(user, request)

  @app.post("/refresh")
  async def refresh_token(data: dict, session: AsyncSessionDep):
    """
    刷新token接口，通过refresh_token获取新的access_token
    """
    refresh_token: str | None = data.get('refresh_token', None)
    if not refresh_token:
      raise HTTPException(
        detail="refresh_token不能为空",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )
    token_info: TokenInfo | None = crypt_utils.jwt_decode(refresh_token)
    if not token_info:
      raise HTTPException(
        detail="refresh_token无效或已过期",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )
    if token_info.get('token_type') != 'refresh':
      raise HTTPException(
        detail="token类型不正确",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )

    # /*---------------------------------------验证用户信息-------------------------------------------*/
    query = select(PrivateUserModel).where(PrivateUserModel.username == token_info.get('username'))
    result = await session.execute(query)
    user_obj: PrivateUserModel | None = result.scalars().first()

    # 用户名username不存在
    if not user_obj or user_obj.valid != 'Y':
      raise HTTPException(
        detail="用户已经失效",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )

    # /*---------------------------------------创建新的访问token-------------------------------------------*/

    access_token, access_expires = await auth_utils.create_access_token(user_obj)
    return {
      "access_token": access_token,
      "access_expires": access_expires,
    }

  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

  # 获取用户信息接口
  @app.get("/users/me")
  async def _me(request: Request, token: Annotated[str, Depends(oauth2_scheme)], session: AsyncSessionDep):
    token_info: TokenInfo | None = crypt_utils.jwt_decode(token)
    if not token_info:
      raise HTTPException(
        detail="token无效或已过期",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )
    username = token_info.get('username')
    query = select(PrivateUserModel).where(PrivateUserModel.username == username)
    result = await session.execute(query)
    user_obj: PrivateUserModel | None = result.scalars().first()
    if not user_obj:
      raise HTTPException(
        detail="用户不存在",
        status_code=status.HTTP_401_UNAUTHORIZED,
      )
    return PublicUser.to_obj(user_obj.to_dict())


def validate_password_strength(password: str) -> tuple[bool, str]:
  """验证密码强度"""
  if len(password) < 8:
    return False, "密码长度至少为8位"
  if not any(c.isupper() for c in password):
    return False, "密码必须包含至少一个大写字母"
  if not any(c.islower() for c in password):
    return False, "密码必须包含至少一个小写字母"
  if not any(c.isdigit() for c in password):
    return False, "密码必须包含至少一个数字"
  return True, ""
