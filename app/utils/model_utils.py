import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal, InvalidOperation
from typing import List, Annotated, Any

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, BeforeValidator
from sqlmodel import SQLModel, Field, select

from app.utils.mysql_utils import AsyncSessionDep

# 定义北京时区（UTC+8）
beijing_timezone = timezone(timedelta(hours=8))

# 定义获取当前北京时区时间的匿名函数，用于默认值生成
current_datetime = lambda: datetime.now(beijing_timezone)

# /*---------------------------------------datetime-------------------------------------------*/

# 日期时间格式
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# 辅助函数：将 datetime 格式化为字符串
def format_datetime_to_string(dt: datetime) -> str:
  if isinstance(dt, str):
    return dt
  if dt is None:
    return None
  # 确保 datetime 对象是带时区的，如果不是则假设为北京时间
  if dt.tzinfo is None:
    dt = dt.replace(tzinfo=beijing_timezone)
  return dt.astimezone(beijing_timezone).strftime(DATETIME_FORMAT)


# 辅助函数：将字符串解析为 datetime
def parse_datetime_from_string(dt_str: Any) -> datetime | None:
  if dt_str is None or dt_str == "":
    return None
  if isinstance(dt_str, datetime):  # 如果已经是datetime对象，直接返回
    return dt_str
  try:
    # 尝试解析，并明确设置为北京时区
    return datetime.strptime(str(dt_str), DATETIME_FORMAT).replace(tzinfo=beijing_timezone)
  except ValueError:
    # 如果解析失败，Pydantic 会处理验证错误
    raise ValueError(f"Invalid datetime format. Expected '{DATETIME_FORMAT}'")


# 定义一个 Annotated 类型，用于在 Pydantic 字段中应用解析器
# 当从输入数据（如JSON字符串）转换为 datetime 对象时，会先经过这个解析器
# 这里使用 BeforeValidator，因为它在 Pydantic 自己的验证之前运行
# 对于 SQLModel (基于Pydantic)，这在从数据库加载数据或从请求体解析数据时都适用
FormattedDatetime = Annotated[
  datetime,
  BeforeValidator(parse_datetime_from_string)
]

# /*---------------------------------------date-------------------------------------------*/

# 日期格式
DATE_FORMAT = "%Y-%m-%d"


# 辅助函数：将 date 格式化为字符串
def format_date_to_string(d: date) -> str:
  if isinstance(d, str):
    return d
  if d is None:
    return None
  return d.strftime(DATE_FORMAT)


# 辅助函数：将字符串解析为 date
def parse_date_from_string(d_str: Any) -> date | None:
  if d_str is None or d_str == "":
    return None
  if isinstance(d_str, date):  # 如果已经是 date 对象，直接返回
    return d_str
  try:
    # 尝试解析
    return datetime.strptime(str(d_str), DATE_FORMAT).date()
  except ValueError:
    # 如果解析失败，Pydantic 会处理验证错误
    raise ValueError(f"Invalid date format. Expected '{DATE_FORMAT}'")


# 定义一个 Annotated 类型，用于在 Pydantic 字段中应用解析器
# 当从输入数据（如 JSON 字符串）转换为 date 对象时，会先经过这个解析器
FormattedDate = Annotated[
  date,
  BeforeValidator(parse_date_from_string)
]


# /*---------------------------------------decimal-------------------------------------------*/

# 辅助函数：将 Decimal 格式化为字符串
def format_decimal_to_string(d: Decimal) -> str:
  if isinstance(d, str):
    return d
  if d is None:
    return None
  return str(d)


# 辅助函数：将字符串解析为 decimal
def parse_decimal_from_string(d_str: Any) -> Decimal | None:
  if d_str is None or d_str == "":
    return None
  if isinstance(d_str, Decimal):  # 如果已经是 Decimal 对象，直接返回
    return d_str
  try:
    # 尝试解析
    return Decimal(str(d_str))
  except InvalidOperation:
    # 如果解析失败，Pydantic 会处理验证错误
    raise ValueError(f"Invalid decimal format: {d_str}")


# 定义一个 Annotated 类型，用于在 Pydantic 字段中应用解析器
# 当从输入数据（如 JSON 字符串）转换为 Decimal 对象时，会先经过这个解析器
FormattedDecimal = Annotated[
  Decimal,
  BeforeValidator(parse_decimal_from_string)
]


# /*---------------------------------------other-------------------------------------------*/

def to_camel(snake_str: str) -> str:
  """Converts a snake_case string to camelCase."""
  components = snake_str.split('_')
  # We capitalize the first letter of each component except the first one
  # and join them to form the camelCase string.
  return components[0] + ''.join(x.title() for x in components[1:])

# 将SqlModel子类实例转化为 JSON 字符串
def to_dict(obj: BaseModel):
  return obj.model_dump_json(by_alias=True)

# 将字典转化为SqlModel子类实例对象
def to_obj(clazz: type[SQLModel], json_data: dict):
  return clazz.model_validate(json_data)
