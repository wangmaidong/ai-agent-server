import time
from datetime import datetime, timedelta, timezone
from typing import TypeAlias, Literal, TypedDict

from app.auth.crypt_utils import crypt_utils, CryptUtils

# token的类型：
# access用于接口认证；
# refresh用于刷新access token；
# verify用于激活用户账号；
# api用于API接口认证
AccessTokenType: TypeAlias = Literal["access", "refresh", "verify", "api"]


# /*@formatter:off*/
class TokenInfo(TypedDict):
  username: str                   # 用户名信息
  exp: datetime                   # token过期时间
  token_type: AccessTokenType     # token的类型
# /*@formatter:on*/

class TokenUtils:
  def __init__(self, crypt_utils: CryptUtils):
    self.crypt_utils = crypt_utils

  def create_token(
    self,
    username: str,
    token_type: AccessTokenType,
    expires_delta: timedelta
  ):
    return self.crypt_utils.jwt_encode({
      "username": username,
      "token_type": token_type
    }, expires_delta)

  def decode_token(self, token: str) -> TokenInfo | None:
    return self.crypt_utils.jwt_decode(token)


token_utils = TokenUtils(crypt_utils)

# token = token_utils.create_token("admin", "access", timedelta(seconds=3))

# print(f"token: {token}")
# print('1 ==>> ', token_utils.decode_token(token))
# time.sleep(2)
# print('2 ==>> ', token_utils.decode_token(token))
# time.sleep(1)
# print('3 ==>> ', token_utils.decode_token(token))
