import re
from typing import Optional


def path_join(*args: Optional[str]) -> str:
  # 过滤掉 null、undefined 和空字符串/只有斜杠的项
  filtered_args = []
  for i in args:
    if i is None:
      continue
    if i.strip() == '/':
      continue
    filtered_args.append(i)

  # 拼接路径
  val = ''
  for item in filtered_args:
    if not val:
      val = item
    else:
      val += '/' + item

  # 检查是否以 http:// 或 https:// 开头
  prepend_string_list = ['http://', 'https://']
  prepend_string = None
  for prefix in prepend_string_list:
    if val.startswith(prefix):
      prepend_string = prefix
      break

  if not prepend_string:
    # 非 http/https 开头，替换多个斜杠为单个斜杠
    ret = re.sub(r'/{2,}', '/', val)
  else:
    # http/https 开头，处理后面的部分
    left_string = val[len(prepend_string):]
    ret = prepend_string + re.sub(r'/{2,}', '/', left_string)

  # 如果结果是 '/'，返回空字符串
  if ret == '/':
    return ''

  return ret
