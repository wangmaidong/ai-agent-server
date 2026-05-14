import uuid
from contextlib import asynccontextmanager
from typing import AsyncContextManager

import redis.asyncio as redis
from fastapi.logger import logger

from app.config.env import env
from app.utils.is_pytesting import is_pytesting


class RedisUtils():
  def __init__(
    self,
    redis_host: str,
    redis_port: int,
    redis_password: str,
    redis_db: int
  ):
    self.redis_config = {
      "host": redis_host,
      "port": redis_port,
      "password": redis_password,
      "db": redis_db,
      "encoding": "utf-8",
      # /*@formatter:off*/
      "decode_responses": True,    # 自动解码响应结果
      "health_check_interval": 5,  # 每5秒自动发送PING，保持连接活跃
      "socket_keepalive": True,    # 启用TCP层面的保活探测
      "socket_connect_timeout": 3, # 连接超时设置
      "retry_on_timeout": True,    # 遇到超时自动重试一次
      # /*@formatter:on*/
    }
    self.redis_pool = None if is_pytesting() else redis.ConnectionPool(**self.redis_config)

  @asynccontextmanager
  async def get_redis_connection(self) -> AsyncContextManager[redis.Redis]:
    # 异步连接池中，Redis 实例创建很轻量
    # 上下文管理器结束后，它会自动将连接归还给 pool，而不是物理断开
    if not is_pytesting():
      redis_client = redis.Redis(connection_pool=self.redis_pool)
    else:
      redis_client = redis.Redis(**self.redis_config, single_connection_client=True)

    try:
      yield redis_client
    except Exception as e:
      logger.error(f"Redis Connection Error: {e}")
      raise e
    finally:
      # 测试环境下：由于是单连接，aclose 会彻底关闭它，不留隐患
      # 生产环境下：aclose 仅将连接还回 pool，不关闭 pool
      await redis_client.close()

  async def check_redis_connection(self):
    # 立即对redis做一次读写测试
    async with self.get_redis_connection() as redis_client:
      try:
        if not await redis_client.ping():
          raise Exception("Redis ping failed!")
        random_id = str(uuid.uuid4())
        await redis_client.set("__init__setup__", random_id, ex=30)  # 设置30秒过期
        cache_random_id = await redis_client.get("__init__setup__")

        if cache_random_id != random_id:
          raise Exception("Redis 读写测试一致性校验失败")

        print("✅ Redis connection successful：", f"redis://{env.redis_password}@{env.redis_host}:{env.redis_port}/{env.redis_db}")
      except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise e

  # 3. 清理连接池
  async def close_redis_connection(self):
    if self.redis_pool:
      await self.redis_pool.disconnect()
      print("🚀 Redis connection pool closed.")


redis_utils = RedisUtils(
  redis_host=env.redis_host,
  redis_port=env.redis_port,
  redis_password=env.redis_password,
  redis_db=env.redis_db
)
