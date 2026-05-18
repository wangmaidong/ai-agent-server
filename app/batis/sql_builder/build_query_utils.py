import re


def query_format(query: str, value_type: str):
  if value_type == "string" or value_type == "number":
    return query
  elif value_type == "date":
    return date_format_sql(query)
  elif value_type == "datetime":
    return datetime_format_sql(query)
  elif value_type == "time":
    return time_format_sql(query)
  raise ValueError(f"Can't recognise value type:{value_type}")


def date_format_sql(query: str):
  return f"date_format({query}, '%%Y-%%m-%%d')"


def datetime_format_sql(query: str):
  return f"date_format({query}, '%%Y-%%m-%%d %%H:%%i:%%s')"


def time_format_sql(query: str):
  return f"date_format({query}, '%%H:%%i:%%s')"


def format_in(value, query, not_in, value_list):
  # value_list.append(query)
  # 如果 value 不是列表，将其按逗号分割成列表
  if not isinstance(value, list):
    list_ = value.split(',')
  else:
    list_ = value

  # 将 list_ 中的元素添加到 valueList 中
  value_list.extend(list_)

  # 生成格式化字符串
  result = f"{query} {'not ' if not_in else ''}in ({','.join('?' for _ in list_)})"
  return result


def format_in_like(value, query, not_like, value_list):
  # 如果 value 不是列表，将其按逗号分割成列表
  if not isinstance(value, list):
    list_ = value.split(',')
  else:
    list_ = value

  if not_like:
    result_list = []
    for item in list_:
      value_list.append(f"%{item}%")
      result_list.append(f"{query} not like ?")
    return f"({' and '.join(result_list)})"
  else:
    result_list = []
    for item in list_:
      value_list.append(f"%{item}%")
      result_list.append(f"{query} like ?")
    return f"({' or '.join(result_list)})"


def format_string2array(val):
  return val if isinstance(val, list) else val.split(',')

def validate_filter_expression(expression: str, valid_ids: set) -> bool:
  """验证过滤表达式的合法性"""
  # 检查括号匹配
  if expression.count('(') != expression.count(')'):
    return False

  # 提取所有标识符
  tokens = re.findall(r'[a-zA-Z0-9_-]+', expression)

  # 检查每个标识符是否合法
  allowed_keywords = {'and', 'or', 'not'}
  for token in tokens:
    if token.lower() not in allowed_keywords and token not in valid_ids:
      return False

  return True
