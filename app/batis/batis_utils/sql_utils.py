import json
import re

from fastapi import HTTPException

MAX_FILTERS_COUNT = 50  # 最大筛选条件数
MAX_EXPRESSION_LENGTH = 1000  # 最大筛选表达式长度
MAX_BATCH_DELETE_SIZE = 100  # 批量删除最大数量


# 将json字符串中的 \u00A0 全部去掉，\u00A0 表示 &nbsp，当这个字符存在的时候会导致无法将json字符串合法地解析为对象/字典
def format_json_string(json_str: str):
  json_str = re.sub(r'\u00A0', '', json_str)
  return json_str


# 将驼峰命名转换为下划线命名
def to_line(hump_name: str) -> str:
  return re.sub(r'([A-Z])', r'_\1', hump_name).lower()


# 通用的获取属性值的方法
def get_value(obj, attr_name, default=None):
  if isinstance(obj, dict):
    return obj.get(attr_name, default)
  else:
    return getattr(obj, attr_name, default)


# 获取值的sql查询语句
def get_value_sql(value, value_type, sql_values):
  if value_type == 'string' or value_type == 'number':
    sql_values.append(value)
    return '?'
  elif value_type == 'date':
    sql_values.append(value)
    return "str_to_date(?, '%%Y-%%m-%%d')"
  elif value_type == 'datetime':
    sql_values.append(value)
    return "str_to_date(?, '%%Y-%%m-%%d %%H:%%i:%%s')"
  elif value_type == 'time':
    sql_values.append(value)
    return "str_to_date(?, '%%H:%%i:%%s')";

  raise HTTPException(status_code=500, detail=f"column value_type: {value_type} is not supported")


def parse_env_content(env_content):
  """
  将.env文件内容解析为字典格式

  Args:
      env_content (str): .env文件的内容字符串

  Returns:
      dict: 包含所有环境变量的字典
  """
  config_dict = {}

  # 按行分割内容
  lines = env_content.strip().split('\n')

  # 定义注释和值的正则表达式
  pattern = r'^([^=#]+)=([^#]*)(?:#.*)?$'

  for line in lines:
    line = line.strip()
    if line and not line.startswith('#'):  # 忽略空行和纯注释行
      match = re.match(pattern, line)
      if match:
        key = match.group(1).strip()
        value = match.group(2).strip()
        # 移除可能存在的引号
        if value.startswith('"') and value.endswith('"'):
          value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
          value = value[1:-1]
        config_dict[key] = value

  return config_dict


show_sql = True


# 一个用于打印sql的工具函数
def log_sql(sql, values):
  if show_sql:
    print("\n/*---------------------------------------log sql-------------------------------------------*/\n")
    print("\nsource sql-->>\n")
    print(sql)
    print("\nsql params-->>\n")
    print(values)
    count = 0

    def replace_callback(match):
      nonlocal count
      val = values[count]
      count = count + 1
      if isinstance(val, str):
        return f"'{val}'"
      if isinstance(val, list):
        return ', '.join(map(str, val))
      # formatDebugData 要加上''，不然有些关键词没有''当做字符串的话会报错
      return f"'{str(val)}'"

    import re
    target_sql = re.sub(r'\?+', replace_callback, sql)
    print("\ntarget sql-->>\n")
    print(target_sql)
    print("\n")
