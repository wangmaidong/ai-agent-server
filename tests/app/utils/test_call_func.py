import asyncio

import pytest

from app.utils.call_func import call_func


@pytest.mark.asyncio
async def test_call_sync_function():
  """测试调用同步函数，参数从context中自动注入"""
  data_context = {
    "user": "Leo",
    "row": "Order_001",
  }

  def sync_handler(user, row):
    return f"同步处理: {user} 修改了 {row}"

  result = await call_func(sync_handler, data_context)
  assert result == "同步处理: Leo 修改了 Order_001"


@pytest.mark.asyncio
async def test_call_async_function():
  """测试调用异步函数，参数从context中自动注入"""
  data_context = {
    "user": "Leo",
    "row": "Order_001",
    "session": "SSN_999",
  }

  async def async_handler(user, row, session):
    await asyncio.sleep(0.01)
    return f"异步处理: {user} 在会话 {session} 中操作"

  result = await call_func(async_handler, data_context)
  assert result == "异步处理: Leo 在会话 SSN_999 中操作"


@pytest.mark.asyncio
async def test_ignore_extra_context():
  """测试context中多余的参数不会被注入到函数中"""
  data_context = {
    "user": "Leo",
    "extra_stuff": "ignored",
  }

  def handler(user):
    return user

  result = await call_func(handler, data_context)
  assert result == "Leo"


@pytest.mark.asyncio
async def test_missing_context_params():
  """测试函数参数在context中不存在时会报错"""
  data_context = {
    "name": "Leo",
  }

  def handler(user):
    return user

  with pytest.raises(TypeError):
    await call_func(handler, data_context)


@pytest.mark.asyncio
async def test_empty_context():
  """测试空context调用无参数函数"""
  data_context = {}

  def handler():
    return "no params"

  result = await call_func(handler, data_context)
  assert result == "no params"


@pytest.mark.asyncio
async def test_partial_params_match():
  """测试函数参数部分匹配context"""
  data_context = {
    "a": 1,
    "b": 2,
    "c": 3,
  }

  def handler(a, c):
    return a + c

  result = await call_func(handler, data_context)
  assert result == 4


@pytest.mark.asyncio
async def test_sync_function_returns_none():
  """测试同步函数返回None的情况"""
  data_context = {
    "value": 10,
  }

  def handler(value):
    if value > 5:
      return None
    return value

  result = await call_func(handler, data_context)
  assert result is None


@pytest.mark.asyncio
async def test_async_function_returns_none():
  """测试异步函数返回None的情况"""
  data_context = {
    "value": 10,
  }

  async def handler(value):
    await asyncio.sleep(0.01)
    if value > 5:
      return None
    return value

  result = await call_func(handler, data_context)
  assert result is None
