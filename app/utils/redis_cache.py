import asyncio
import json
from typing import Any, Optional

import redis.asyncio as redis
from sqlalchemy.orm import InstrumentedAttribute
from sqlmodel import select

from app.model.BasicModel import BasicModel
from app.utils.mysql_utils import async_session
from app.utils.redis_lock import get_redis_lock
from app.utils.redis_utils import redis_utils

# 用于表示缓存不存在（Redis中没有这个key）
CACHE_KEY_NOT_EXIST = "__CACHE_KEY_NOT_EXIST__"
# 用于表示缓存存在但值为空（数据库中也没有数据）
CACHE_VALUE_NULL = "__CACHE_VALUE_NULL__"


class RedisCache:
  def __init__(
    self,
    cache_key: str,
    clazz: type[BasicModel],
    clazz_attr: InstrumentedAttribute,
    ttl: int = 3600,
    null_ttl: int = 60,
  ):
    """
    Redis 缓存管理器初始化

    :param cache_key: 缓存的关键词前缀，会使用 cache_key + item_key 生成最终的缓存 key
    :param clazz: 缓存数据的实体类型，会使用这个实体类型来查数据库表
    :param clazz_attr: 缓存数据的实体属性，会用这个属性来生成查询条件
    :param ttl: 缓存过期时间（秒），默认 3600 秒（1小时）
    :param null_ttl: 空值缓存过期时间（秒），防止缓存击穿，默认 60 秒
    """
    self.cache_key = cache_key
    self.clazz = clazz
    self.clazz_attr = clazz_attr
    self.ttl = ttl
    self.null_ttl = null_ttl

  async def get_from_mysql(self, item_key: str) -> Optional[dict]:
    """
    从 MySQL 数据库中获取数据

    :param item_key: 查询条件的值（与 clazz_attr 对应）
    :return: 实体对象的字典形式，如果不存在则返回 None
    """
    # await asyncio.sleep(5)
    async with async_session() as session:
      query = select(self.clazz).where(self.clazz_attr == item_key)
      result = await session.execute(query)
      obj = result.scalars().first()
    return obj.to_dict() if obj else None

  async def get_from_redis(self, key: str, redis_client: redis.Redis) -> str:
    """
    从 Redis 中获取缓存数据

    :param key: Redis 缓存 key
    :param redis_client: Redis 客户端连接
    :return:
      - CACHE_KEY_NOT_EXIST: 缓存不存在
      - CACHE_VALUE_NULL: 缓存存在但值为空（数据库中也没有数据）
      - 其他: JSON 字符串形式的缓存数据
    """
    json_string = await redis_client.get(key)
    if json_string is None:
      return CACHE_KEY_NOT_EXIST
    if json_string == CACHE_VALUE_NULL:
      return CACHE_VALUE_NULL
    return json_string

  def _parse_redis_result(self, result) -> dict | None:
    """
    解析 Redis 返回的结果

    :param result: Redis 返回的结果
    :return: 解析后的数据：
      - None: 表示数据库中没有对应数据
      - dict: 解析后的 JSON 数据
    """
    if result == CACHE_VALUE_NULL:
      return None
    return json.loads(result)

  async def save_cache(self, key: str, redis_client: redis.Redis, value: Any) -> Any:
    """
    保存数据到 Redis 缓存

    :param key: Redis 缓存 key
    :param redis_client: Redis 客户端连接
    :param value: 要缓存的数据（字典或 None）
    :return: 保存后的数据
    """
    if value is None:
      await redis_client.set(key, CACHE_VALUE_NULL, ex=self.null_ttl)
      return None

    value = {k: v for k, v in value.items() if v is not None}
    await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=self.ttl)
    return value

  async def get_cache(self, item_key: str):
    """
    获取缓存数据（优先从 Redis 获取，不存在则查数据库并缓存）

    :param item_key: 查询条件的值
    :return: 缓存的数据（字典），如果不存在则返回 None
    """
    key = self.cache_key + ":" + item_key
    lock_key = f"lock:{key}"

    async with redis_utils.get_redis_connection() as redis_client:
      result = await self.get_from_redis(key, redis_client)
      if result != CACHE_KEY_NOT_EXIST:
        return self._parse_redis_result(result)

      async with get_redis_lock(
        lock_key=lock_key,
        redis_client=redis_client,
        timeout=10,
        retry_interval=0.1
      ):
        result = await self.get_from_redis(key, redis_client)
        if result != CACHE_KEY_NOT_EXIST:
          return self._parse_redis_result(result)

        value = await self.get_from_mysql(item_key)
        return await self.save_cache(key, redis_client, value)

  async def refresh_cache(self, item_key: str):
    """
    刷新缓存（强制从数据库重新获取并更新缓存）

    :param item_key: 查询条件的值
    :return: 刷新后的数据（字典），如果不存在则返回 None
    """
    key = self.cache_key + ":" + item_key
    async with redis_utils.get_redis_connection() as redis_client:
      value = await self.get_from_mysql(item_key)
      return await self.save_cache(key, redis_client, value)
