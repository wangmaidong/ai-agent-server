import pytest
import asyncio

# 存储第一个测试的事件循环引用
_loop_ref = None


@pytest.mark.asyncio
async def test_event_loop_01():
  global _loop_ref

  # 获取当前事件循环
  loop = asyncio.get_running_loop()
  _loop_ref = loop  # 保存引用

  print(f"\nTest 1: 事件循环ID = {id(loop)}")
  print(f"Test 1: 事件循环是否存活 = {loop.is_running()}")

  # 做一些异步操作
  await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_event_loop_02():
  global _loop_ref

  # 获取当前事件循环
  current_loop = asyncio.get_running_loop()

  print(f"\nTest 2: 事件循环ID = {id(current_loop)}")
  print(f"Test 2: 事件循环是否存活 = {current_loop.is_running()}")

  # ✅ 验证：当前循环和上一个测试的循环是不同的对象
  assert current_loop is not _loop_ref, "事件循环没有被重建！"

  # ✅ 验证：上一个测试的循环已被关闭
  assert _loop_ref.is_closed() == True, "上一个事件循环没有被关闭！"

  print(f"\n✅ 验证成功！")
  print(f"   - 两个测试使用不同的事件循环")
  print(f"   - 第一个测试的事件循环已关闭")
