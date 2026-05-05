import logging
from datetime import timedelta, datetime, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from app.config.env import env


class CryptUtils:
  """
  加密解密工具类
  """

  def __init__(
    self,
    # JWT加密秘钥
    jwt_secret_key: str,
    # JWT加密算法
    jwt_algorithm: str,
  ):
    self.jwt_secret_key = jwt_secret_key
    self.jwt_algorithm = jwt_algorithm
    # 用于密码加密的上下文对象
    self.crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def hash_password(self, password: str) -> str:
    """
    对密码进行加密
    """
    return self.crypt_context.hash(password)

  def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    """
    return self.crypt_context.verify(plain_password, hashed_password)

  def jwt_encode(self, payload: dict, expires_delta: timedelta) -> str:
    """
    JWT加密
    """
    payload['exp'] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)

  def jwt_decode(self, token: str) -> Optional[dict]:
    """
    JWT解密
    """
    try:
      return jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])
    except jwt.ExpiredSignatureError as e:
      logging.warning(f"JWT Token已过期：{e}")
      return None
    except jwt.InvalidTokenError as e:
      logging.warning(f"JWT Token无效：{e}")
      return None
    except Exception as e:
      logging.error(f"JWT解密失败：{e}")
      return None


crypt_utils = CryptUtils(
  jwt_secret_key=env.jwt_secret_key,
  jwt_algorithm=env.jwt_algorithm,
)

if __name__ == '__main__':
  plain_password = "123456"
  hashed_password = '$2b$12$OowYmTuHiED06FQ6ymc7.O0HeItHMd47sLL.C0fVjT.yIz/MfC3XG'

  print(f"plain_password 类型: {type(plain_password)}")
  print(f"plain_password 值: {repr(plain_password)}")
  print(f"plain_password 长度: {len(plain_password)}")
  print(f"plain_password 字节长度: {len(plain_password.encode('utf-8'))}")
  print(f"hashed_password 类型: {type(hashed_password)}")
  print(f"hashed_password 值: {repr(hashed_password)}")
  print(f"hashed_password 长度: {len(hashed_password)}")

  try:
    result = crypt_utils.verify_password(plain_password, hashed_password)
    print(f"验证结果: {result}")
  except Exception as e:
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {e}")
