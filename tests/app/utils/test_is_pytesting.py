import pytest

from app.utils.is_pytesting import is_pytesting


@pytest.mark.asyncio
async def test_is_pytesting():
  assert is_pytesting()
  print("当前运行环境为自动化测试环境")
