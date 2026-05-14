import sys


def is_pytesting():
  return "pytest" in sys.modules


if __name__ == "__main__":
  assert not is_pytesting()
  print("当前不是自动化测试环境")
