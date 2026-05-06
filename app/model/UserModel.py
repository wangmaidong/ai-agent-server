import asyncio
from enum import Enum

from sqlmodel import Field

from app.model.BasicModel import BasicModel

# 引入redis缓存
from app.utils.redis_cache import RedisCache

# 用户账号状态，为Y表示账号已经激活，为N表示账号未激活
class UserValidStatus(str, Enum):
  Y = "Y"
  N = "N"


class PublicUser(BasicModel):
  """
  返回给前端的用户信息类型
  """
  username: str = Field(..., description="用户名")
  full_name: str = Field(..., description="用户昵称")
  email: str = Field(..., description="用户邮箱地址")
  valid: UserValidStatus = Field(default=UserValidStatus.N, description="用户账号是否已经激活生效")


class PrivateUserModel(PublicUser, table=True):
  """
  用来对数据库进行读写的用户对象类型
  """
  __tablename__ = "pl_user"
  hash_password: str = Field(..., description="经过哈希转换的密码")


class RegistryUserSchema(PublicUser):
  """
  用户注册的请求参数类型
  """
  password: str = Field(..., description="明文密码")

user_cache = RedisCache(
  cache_key="user",
  clazz=PrivateUserModel,
  clazz_attr=PrivateUserModel.username
)

if __name__ == "__main__":
  async def main():
    result = await asyncio.gather(
      asyncio.create_task(user_cache.get_cache("zhangsan")),
      asyncio.create_task(user_cache.get_cache("zhangsan")),
      asyncio.create_task(user_cache.get_cache("zhangsan")),
    )
    for item in result:
      print(item)

  asyncio.run(main())
