import pytest
from datetime import timedelta
import asyncio

from app.auth.crypt_utils import crypt_utils


@pytest.mark.asyncio
class TestCryptUtilsAsync:

  # --- 密码哈希测试 ---

  async def test_password_operations(self):
    """测试密码加密与验证的异步兼容性"""
    password = "secure_password_2026"
    hashed = crypt_utils.hash_password(password)

    assert hashed != password
    assert crypt_utils.verify_password(password, hashed) is True
    assert crypt_utils.verify_password("wrong_pass", hashed) is False

  # --- JWT 核心功能测试 ---

  async def test_jwt_flow(self):
    """测试完整的 JWT 生成与解码流程"""
    data = {"sub": "user123", "role": "admin"}
    expires = timedelta(minutes=15)

    token = crypt_utils.jwt_encode(data, expires)
    assert isinstance(token, str)

    decoded = crypt_utils.jwt_decode(token)
    assert decoded["sub"] == "user123"
    assert decoded["role"] == "admin"

  # --- 异常场景测试 ---

  async def test_jwt_expired(self):
    """测试过期 Token 的捕获"""
    # 创建一个已经过期的 Token
    expired_delta = timedelta(seconds=-10)
    token = crypt_utils.jwt_encode({"user": "expired"}, expired_delta)

    decoded = crypt_utils.jwt_decode(token)
    assert decoded is None  # 根据你的代码，过期返回 None

  async def test_jwt_invalid_signature(self):
    """测试无效签名的 Token"""
    token = crypt_utils.jwt_encode({"data": "test"}, timedelta(hours=1))
    # 修改 Token 字符串模拟篡改
    invalid_token = token[:-5] + "fake"

    decoded = crypt_utils.jwt_decode(invalid_token)
    assert decoded is None

  # --- 并发压力测试 (异步优势) ---

  async def test_concurrent_token_generation(self):
    """测试在高并发异步场景下生成 Token 是否正常"""
    tasks = [
      asyncio.to_thread(crypt_utils.jwt_encode, {"id": i}, timedelta(seconds=10))
      for i in range(10)
    ]
    tokens = await asyncio.gather(*tasks)
    assert len(tokens) == 10
    assert len(set(tokens)) == 10  # 确保生成的 Token 都是唯一的
