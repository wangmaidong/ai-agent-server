import json
from typing import Any

from sqlalchemy.orm import InstrumentedAttribute
from sqlmodel import select

from app.model.BasicModel import BasicModel
from app.utils.mysql_utils import async_session
from app.utils.redis_utils import redis_utils


class RedisCache:
  def __init__(
    self,
    # 缓存的关键词前缀，会使用 cache_key + item_Key 生成最终的缓存key
    cache_key: str,
    # 缓存数据的实体类型，会使用这个实体类型来查数据库表
    clazz: type[BasicModel],
    # 缓存数据的实体属性，会用这个属性来生成查询条件
    clazz_attr: InstrumentedAttribute,
  ):
    self.cache_key = cache_key
    self.clazz = clazz
    self.clazz_attr = clazz_attr

  async def get_default_value(self, item_key: str) -> dict:
    """item_key没有缓存时的默认值"""
    async with async_session() as session:
      query = select(self.clazz).where(self.clazz_attr == item_key)
      result = await session.execute(query)
      obj = result.scalars().first()
    return obj.to_dict() if obj else None

  async def save_cache(self, key: str, redis_client, value: Any):
    """保存缓存"""
    value = {k: v for k, v in value.items() if v is not None}
    await redis_client.set(key, json.dumps(value, ensure_ascii=False))
    return value

  async def get_cache(self, item_key: str):
    """
      从redis中获取key的缓存，如果没有值则执行默认值获取函数，并保存到redis中
      @param  key                         缓存的key
      @param  default_value_getter        如果缓存值不存在的情况下则调用异步函数 default_value_getter 来获取默认值，这个函数的返回值必须是一个字典 dict
      """
    async with redis_utils.get_redis_connection() as redis_client:
      # default_value_getter返回的字段可能嵌套多层对象，这里改成用json字符串缓存
      key = self.cache_key + ":" + item_key
      json_string = await redis_client.get(key)
      exists = False if json_string == "{}" else bool(json_string)
      # print("exists", exists)
      if exists:
        return json.loads(json_string)
      else:
        value = await self.get_default_value(item_key)
        # print("value", value)
        if value is not None:
          value = await self.save_cache(key, redis_client, value)
        return value

  async def refresh_cache(self, item_key: str):
    key = self.cache_key + ":" + item_key
    async with redis_utils.get_redis_connection() as redis_client:
      value = await self.get_default_value(item_key)
      # print("value", value)
      if value is not None:
        value = await self.save_cache(key, redis_client, value)
      return value
