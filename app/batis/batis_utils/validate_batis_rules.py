import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

from app.batis.batis_utils.batis_scheme import BatisModuleColumn, BatisValidRule, BatisModuleConfig
from app.batis.batis_utils.sql_utils import get_value

MAX_REGEX_COMPLEXITY = 100


# validate_batis_rules.py
def validate_row(
  row: dict,
  module_config: BatisModuleConfig,
  is_partial: bool = False,  # 是否部分更新
):
  for hump_name, col_config in module_config.columns.items():
    if col_config.rules:
      # 部分更新时，只校验用户实际传了的字段
      if is_partial and hump_name not in row:
        continue
      is_valid, valid_msg = validate_batis_rules(hump_name=hump_name, col_config=col_config, value=get_value(row, hump_name))
      if not is_valid:
        return is_valid, valid_msg
  return True, ""


def validate_batis_rules(
  hump_name: str,
  col_config: BatisModuleColumn,
  value: Any,
) -> tuple[bool, str]:
  if not col_config.rules:
    return True, ""

  for rule in col_config.rules:
    is_valid, error_msg = _validate_single_rule(hump_name, rule, value)
    if not is_valid:
      return False, error_msg

  return True, ""


def _validate_single_rule(
  hump_name: str,
  rule: BatisValidRule,
  value: Any,
) -> tuple[bool, str]:
  if value is None or value == "" or (isinstance(value, (list, dict)) and len(value) == 0):
    if rule.required:
      return False, rule.message or f"{hump_name} 为必填项"
    return True, ""

  default_msg = rule.message or f"{hump_name} 校验失败"

  match rule.type:
    case "string":
      return _validate_string(value, rule, default_msg)
    case "number":
      return _validate_number(value, rule, default_msg)
    case "date":
      return _validate_date(value, rule, default_msg)
    case "datetime":
      return _validate_datetime(value, rule, default_msg)
    case "time":
      return _validate_time(value, rule, default_msg)
    case "email":
      return _validate_email(value, rule, default_msg)
    case "idcard":
      return _validate_idcard(value, rule, default_msg)
    case "phone":
      return _validate_phone(value, rule, default_msg)
    case "qq":
      return _validate_qq(value, rule, default_msg)
    case _:
      return True, ""


def _validate_string(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  try:
    value = str(value)
  except (TypeError, ValueError):
    return False, rule.message or default_msg

  if rule.pattern:
    is_safe, error = _is_safe_regex(rule.pattern)
    if not is_safe:
      return False, error
    try:
      if not re.match(rule.pattern, value):
        return False, rule.message or default_msg
    except re.error:
      return False, rule.message or "正则表达式格式错误"

  if rule.len is not None and len(value) != rule.len:
    return False, rule.message or f"{default_msg}，长度必须为{rule.len}"

  if rule.min is not None and len(value) < int(rule.min):
    return False, rule.message or f"{default_msg}，最小长度为{rule.min}"

  if rule.max is not None and len(value) > int(rule.max):
    return False, rule.message or f"{default_msg}，最大长度为{rule.max}"

  if rule.enum and value not in rule.enum:
    return False, rule.message or f"{default_msg}，必须是{rule.enum}之一"

  return True, ""


def _validate_number(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  try:
    num_value = Decimal(str(value))
  except (InvalidOperation, TypeError, ValueError):
    return False, rule.message or default_msg

  if rule.min is not None and num_value < Decimal(str(rule.min)):
    return False, rule.message or f"{default_msg}，最小值为{rule.min}"

  if rule.max is not None and num_value > Decimal(str(rule.max)):
    return False, rule.message or f"{default_msg}，最大值为{rule.max}"

  if rule.enum and str(value) not in rule.enum:
    return False, rule.message or f"{default_msg}，必须是{rule.enum}之一"

  return True, ""


def _validate_date(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  if isinstance(value, str):
    try:
      value = date.fromisoformat(value)
    except ValueError:
      return False, rule.message or default_msg

  if not isinstance(value, date):
    return False, rule.message or default_msg

  if rule.min is not None:
    try:
      min_date = date.fromisoformat(str(rule.min))
      if value < min_date:
        return False, rule.message or f"{default_msg}，最小日期为{rule.min}"
    except ValueError:
      pass

  if rule.max is not None:
    try:
      max_date = date.fromisoformat(str(rule.max))
      if value > max_date:
        return False, rule.message or f"{default_msg}，最大日期为{rule.max}"
    except ValueError:
      pass

  return True, ""


def _validate_datetime(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  if isinstance(value, str):
    try:
      value = datetime.fromisoformat(value)
    except ValueError:
      return False, rule.message or default_msg

  if not isinstance(value, datetime):
    return False, rule.message or default_msg

  if rule.min is not None:
    try:
      min_dt = datetime.fromisoformat(str(rule.min))
      if value < min_dt:
        return False, rule.message or f"{default_msg}，最小时间为{rule.min}"
    except ValueError:
      pass

  if rule.max is not None:
    try:
      max_dt = datetime.fromisoformat(str(rule.max))
      if value > max_dt:
        return False, rule.message or f"{default_msg}，最大时间为{rule.max}"
    except ValueError:
      pass

  return True, ""


def _validate_time(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  if isinstance(value, str):
    try:
      value = time.fromisoformat(value)
    except ValueError:
      return False, rule.message or default_msg

  if not isinstance(value, time):
    return False, rule.message or default_msg

  return True, ""


def _validate_email(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  if not isinstance(value, str):
    try:
      value = str(value)
    except (TypeError, ValueError):
      return False, rule.message or default_msg

  pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
  if not re.match(pattern, value):
    return False, rule.message or f"{default_msg}，邮箱格式不正确"

  return True, ""


def _validate_idcard(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  if not isinstance(value, str):
    try:
      value = str(value)
    except (TypeError, ValueError):
      return False, rule.message or default_msg

  pattern = r'^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
  if not re.match(pattern, value):
    return False, rule.message or f"{default_msg}，身份证格式不正确"

  return True, ""


def _validate_phone(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  if not isinstance(value, str):
    try:
      value = str(value)
    except (TypeError, ValueError):
      return False, rule.message or default_msg

  pattern = r'^1[3-9]\d{9}$'
  if not re.match(pattern, value):
    return False, rule.message or f"{default_msg}，手机号格式不正确"

  return True, ""


def _validate_qq(value: Any, rule: BatisValidRule, default_msg: str) -> tuple[bool, str]:
  if not isinstance(value, str):
    try:
      value = str(value)
    except (TypeError, ValueError):
      return False, rule.message or default_msg

  pattern = r'^[1-9]\d{4,10}$'
  if not re.match(pattern, value):
    return False, rule.message or f"{default_msg}，QQ号格式不正确"

  return True, ""


def _is_safe_regex(pattern: str) -> tuple[bool, str]:
  if len(pattern) > MAX_REGEX_COMPLEXITY:
    return False, "正则表达式过长"

  dangerous_patterns = [
    r'\([^)]*\+[^)]*\+[^)]*\)',  # 嵌套重复
    r'\(.*\)\*.*\(.*\)\*',  # 多重重叠通配符
    r'\.\*.*\.\*',  # 多个.*
    r'\(\.\*\+\)',  # possessive 量词
    r'(\[[^\]]*\])\*\{',  # 字符类重复带大括号
  ]

  for dp in dangerous_patterns:
    if re.search(dp, pattern):
      return False, "正则表达式可能存在性能问题"

  return True, ""
