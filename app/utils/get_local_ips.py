import socket
import psutil


def get_local_ips():
  ips = []
  try:
    for interface, addrs in psutil.net_if_addrs().items():
      for addr in addrs:
        if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
          ips.append(addr.address)
    # 对获取到的 IP 地址列表进行排序
    ips.sort()
  except Exception as e:
    print(f"获取 IP 地址时出错：{e}")
  return ips

