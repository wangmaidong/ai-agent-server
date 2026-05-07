from app.config.env import env


def _parse_whitelist(raw_list: list) -> tuple[set, list]:
  """
  解析白名单列表，分离出精确匹配路径和通配符匹配路径
  """
  exact_paths = set()
  wildcard_prefixes = []

  for path in raw_list:
    # 去除首尾空格
    path = path.strip()

    # 过滤掉空行
    if not path:
      continue

    if path.endswith("/*"):
      # 通配符路径，去除 /* 后缀
      prefix = path[:-2]
      wildcard_prefixes.append(prefix)
    else:
      # 精确匹配路径
      exact_paths.add(path)

  return exact_paths, wildcard_prefixes


def load_whitelist_from_file(file_path: str) -> list:
  """
  从文件中读取并清洗数据：去掉注释、空行、换行符
  """
  cleaned_paths = []
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      for line in f:
        # 1. 去掉注释部分（#号之后的内容）
        content = line.split('#')[0]
        # 2. 去掉首尾空白字符（换行符、空格等）
        content = content.strip()
        # 3. 如果内容不为空，则加入列表
        if content:
          cleaned_paths.append(content)
  except FileNotFoundError:
    print(f"警告: 找不到白名单文件 {file_path}")
  return cleaned_paths


# --- 执行流程 ---

# 1. 加载并清洗数据
_raw_whitelist = load_whitelist_from_file(env.jwt_white_list)

# 2. 调用你的解析函数
_exact_paths, _wildcard_prefixes = _parse_whitelist(_raw_whitelist)


def is_white_listed(path: str) -> bool:
  """
  校验当前请求路径是否在白名单内
  """
  # 1. 精确匹配
  if path in _exact_paths:
    return True

  # 2. 通配符匹配
  for prefix in _wildcard_prefixes:
    if path.startswith(prefix):
      return True

  return False


print(f"[extract]\twhitelist: {_exact_paths}")
print(f"[wildcard]\twhitelist: {_wildcard_prefixes}")

# 测试用例
if __name__ == "__main__":
  print("-" * 30)
  print("/login ->", is_white_listed("/login"))  # True
  print("/sys_conf ->", is_white_listed("/sys_conf"))  # True
  print("/docs ->", is_white_listed("/docs"))  # True
  print("/general/test/list ->", is_white_listed("/general/test/list"))  # True
  print("/general/test/insert ->", is_white_listed("/general/test/insert"))  # True
  print("/general/demo/list ->", is_white_listed("/general/demo/list"))  # False
  print("/unknown ->", is_white_listed("/unknown"))  # False
